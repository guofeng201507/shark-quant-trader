"""Sentiment Factor Integration Module - PRD FR-4.3

Integrates news sentiment and COT factors into the Phase 3 ML feature pipeline.
Validates sentiment feature contribution via SHAP analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..utils.logger import logger


@dataclass
class IntegrationConfig:
    """Configuration for sentiment factor integration"""
    # Feature names
    news_sentiment_col: str = "Sentiment_News_5d"
    cot_sentiment_col: str = "Sentiment_COT_Percentile"
    momentum_col: str = "Sentiment_Momentum"
    
    # Weighting
    news_weight: float = 0.6  # News sentiment weight
    cot_weight: float = 0.4    # COT sentiment weight
    
    # Feature contribution threshold
    min_shap_contribution: float = 0.05  # Remove if < 5% SHAP contribution
    
    # Merge settings
    forward_fill: bool = True  # Forward-fill missing sentiment data


class SentimentFactorIntegrator:
    """
    Integrate sentiment factors into Phase 3 ML feature pipeline.
    
    FR-4.3 Requirements:
    - Merge sentiment factors into Phase 3 feature set
    - Feature names: Sentiment_News_5d, Sentiment_COT_Percentile, Sentiment_Momentum
    - Validate via SHAP analysis, remove if contribution < 5%
    - Note: Sentiment is INPUT to ML model, not standalone signal
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        self.config = config or IntegrationConfig()
        self.sentiment_history = []
        
        logger.info("SentimentFactorIntegrator initialized")
    
    def integrate(self,
                  ml_features: pd.DataFrame,
                  news_sentiment: Optional[pd.DataFrame] = None,
                  cot_sentiment: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Integrate sentiment factors into ML feature set.
        
        Args:
            ml_features: Phase 3 feature DataFrame
            news_sentiment: News sentiment features
            cot_sentiment: COT sentiment features
            
        Returns:
            Combined feature DataFrame with sentiment factors
        """
        if ml_features.empty:
            return ml_features
        
        combined = ml_features.copy()
        
        # Add news sentiment if available
        if news_sentiment is not None and not news_sentiment.empty:
            combined = self._merge_sentiment(
                combined, 
                news_sentiment,
                self.config.news_sentiment_col
            )
        
        # Add COT sentiment if available
        if cot_sentiment is not None and not cot_sentiment.empty:
            combined = self._merge_sentiment(
                combined,
                cot_sentiment,
                self.config.cot_sentiment_col
            )
        
        # Create combined sentiment momentum
        combined = self._create_sentiment_momentum(combined)
        
        # Forward fill missing values
        if self.config.forward_fill:
            sentiment_cols = [c for c in combined.columns if 'sentiment' in c.lower()]
            combined[sentiment_cols] = combined[sentiment_cols].ffill()
            combined[sentiment_cols] = combined[sentiment_cols].fillna(0)
        
        logger.info(f"Integrated sentiment factors: {combined.shape}")
        
        return combined
    
    def _merge_sentiment(self,
                         features: pd.DataFrame,
                         sentiment: pd.DataFrame,
                         col_name: str) -> pd.DataFrame:
        """Merge sentiment data into features"""
        
        # Try to match on date index
        if 'date' in features.columns and 'date' in sentiment.columns:
            # Merge on date
            merged = features.merge(
                sentiment[['date', col_name]], 
                on='date', 
                how='left'
            )
        elif features.index.name == 'date' and 'date' in sentiment.columns:
            # Merge on index
            features_indexed = features.reset_index()
            merged = features_indexed.merge(
                sentiment[['date', col_name]],
                on='date',
                how='left'
            )
            merged = merged.set_index(features.index)
        else:
            # Use symbol-based merge
            if 'symbol' in features.columns and 'symbol' in sentiment.columns:
                merged = features.merge(
                    sentiment[['symbol', 'date', col_name]],
                    on=['symbol', 'date'],
                    how='left'
                )
            else:
                logger.warning("Cannot merge sentiment: no matching key")
                return features
        
        return merged
    
    def _create_sentiment_momentum(self, features: pd.DataFrame) -> pd.DataFrame:
        """Create combined sentiment momentum feature"""
        
        sentiment_cols = []
        if self.config.news_sentiment_col in features.columns:
            sentiment_cols.append(self.config.news_sentiment_col)
        if self.config.cot_sentiment_col in features.columns:
            sentiment_cols.append(self.config.cot_sentiment_col)
        
        if len(sentiment_cols) >= 2:
            # Weighted combination
            news_col = self.config.news_sentiment_col
            cot_col = self.config.cot_sentiment_col
            
            # Normalize if both exist
            if news_col in features.columns and cot_col in features.columns:
                features[self.config.momentum_col] = (
                    self.config.news_weight * features[news_col].fillna(0) +
                    self.config.cot_weight * features[cot_col].fillna(0)
                )
        elif len(sentiment_cols) == 1:
            # Use single sentiment
            features[self.config.momentum_col] = features[sentiment_cols[0]].fillna(0)
        
        return features
    
    def validate_sentiment_contribution(self,
                                       model,
                                       features: pd.DataFrame,
                                       feature_cols: List[str]) -> Dict[str, float]:
        """
        Validate sentiment feature contribution via SHAP.
        
        FR-4.3: Remove sentiment if SHAP contribution < 5%
        
        Args:
            model: Trained ML model
            features: Feature DataFrame
            feature_cols: List of feature column names
            
        Returns:
            Dict mapping feature -> SHAP contribution
        """
        try:
            import shap
            
            # Filter to sentiment columns
            sentiment_cols = [
                c for c in feature_cols 
                if 'sentiment' in c.lower()
            ]
            
            if not sentiment_cols:
                return {}
            
            # Calculate SHAP
            X_sample = features[feature_cols].fillna(0).sample(min(100, len(features)))
            
            if hasattr(model, 'predict_proba'):
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_sample)
                
                # Handle multi-class
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]  # Use positive class
                
                # Calculate mean absolute SHAP per feature
                contribution = pd.DataFrame({
                    'feature': feature_cols,
                    'shap_importance': np.abs(shap_values).mean(axis=0)
                })
            else:
                logger.warning("Model doesn't support SHAP")
                return {}
            
            # Filter to sentiment features
            sentiment_contrib = contribution[
                contribution['feature'].isin(sentiment_cols)
            ]
            
            # Calculate relative contribution
            total_importance = contribution['shap_importance'].sum()
            sentiment_contrib['relative_contribution'] = (
                sentiment_contrib['shap_importance'] / total_importance
            )
            
            # Create dict
            result = dict(zip(
                sentiment_contrib['feature'],
                sentiment_contrib['relative_contribution']
            ))
            
            # Log low-contribution features
            for feat, contrib in result.items():
                if contrib < self.config.min_shap_contribution:
                    logger.warning(
                        f"Sentiment feature '{feat}' has low SHAP contribution: "
                        f"{contrib:.2%} < {self.config.min_shap_contribution:.2%}"
                    )
            
            logger.info(f"Sentiment SHAP contributions: {result}")
            
            return result
            
        except Exception as e:
            logger.warning(f"SHAP validation failed: {e}")
            return {}
    
    def get_features_to_remove(self,
                                shap_contributions: Dict[str, float]) -> List[str]:
        """
        Get list of sentiment features to remove based on SHAP contribution.
        
        Args:
            shap_contributions: Dict from validate_sentiment_contribution
            
        Returns:
            List of feature names to remove
        """
        to_remove = [
            feat for feat, contrib in shap_contributions.items()
            if contrib < self.config.min_shap_contribution
        ]
        
        return to_remove
    
    def remove_low_contribution_features(self,
                                        features: pd.DataFrame,
                                        to_remove: List[str]) -> pd.DataFrame:
        """
        Remove low-contribution sentiment features.
        
        Args:
            features: Feature DataFrame
            to_remove: List of feature names to remove
            
        Returns:
            Cleaned feature DataFrame
        """
        if not to_remove:
            return features
        
        removed = features.drop(columns=to_remove, errors='ignore')
        
        logger.info(f"Removed {len(to_remove)} low-contribution features: {to_remove}")
        
        return removed
    
    def get_sentiment_summary(self, 
                              features: pd.DataFrame) -> Dict:
        """
        Get summary of sentiment features in the dataset.
        
        Args:
            features: Feature DataFrame
            
        Returns:
            Summary dict
        """
        sentiment_cols = [
            c for c in features.columns 
            if 'sentiment' in c.lower()
        ]
        
        summary = {
            'n_sentiment_features': len(sentiment_cols),
            'sentiment_features': sentiment_cols,
            'coverage': {}
        }
        
        for col in sentiment_cols:
            coverage = features[col].notna().mean()
            summary['coverage'][col] = coverage
        
        return summary
    
    def get_combined_sentiment(self,
                                news_sentiment: Dict[str, float],
                                cot_sentiment: Dict[str, float]) -> Dict[str, float]:
        """
        Get combined sentiment score for each symbol.
        
        FR-4.3: Combines news and COT into single factor
        
        Args:
            news_sentiment: Dict symbol -> news sentiment
            cot_sentiment: Dict symbol -> COT sentiment
            
        Returns:
            Dict symbol -> combined sentiment
        """
        all_symbols = set(news_sentiment.keys()) | set(cot_sentiment.keys())
        
        combined = {}
        
        for symbol in all_symbols:
            news = news_sentiment.get(symbol, 0.0)
            cot = cot_sentiment.get(symbol, 0.0)
            
            # Weight and combine
            combined[symbol] = (
                self.config.news_weight * news +
                self.config.cot_weight * cot
            )
        
        return combined
    
    def create_sentiment_signal(self,
                                sentiment_score: float,
                                threshold: float = 0.3) -> str:
        """
        Create trading signal from sentiment score.
        
        Note: Sentiment is primarily an ML input, but can also generate signals.
        
        Args:
            sentiment_score: Combined sentiment (-1 to +1)
            threshold: Threshold for signal generation
            
        Returns:
            Signal: 'buy', 'sell', or 'hold'
        """
        if sentiment_score > threshold:
            return 'buy'
        elif sentiment_score < -threshold:
            return 'sell'
        else:
            return 'hold'
