"""Correlation Monitor - Tech Design v1.1 Section 4.3.5"""

import pandas as pd
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass
from ..utils.logger import logger


@dataclass
class CorrelationAlert:
    """Alert for correlation threshold breach"""
    level: str  # WARNING, LEVEL_1, LEVEL_2
    message: str
    pairs: List[Tuple[str, str, float]] = None  # List of (asset1, asset2, correlation)
    avg_correlation: float = None


class CorrelationMonitor:
    """Monitor cross-asset correlations for risk management"""
    
    THRESHOLDS = {
        "pair_warning": 0.7,       # Single asset pair
        "portfolio_warning": 0.5,   # Portfolio average
        "extreme_threshold": 0.8    # All assets same direction
    }
    
    def __init__(self):
        """Initialize correlation monitor"""
        logger.info("CorrelationMonitor initialized")
    
    def calculate_rolling_correlation(self, returns: pd.DataFrame,
                                     window: int = 60) -> pd.DataFrame:
        """
        Calculate 60-day rolling correlation matrix.
        
        Args:
            returns: DataFrame with assets as columns, dates as index
            window: Rolling window size (default 60 days)
            
        Returns:
            Correlation matrix
        """
        if returns.empty or len(returns) < window:
            logger.warning(f"Insufficient data for correlation calculation: {len(returns)} < {window}")
            return pd.DataFrame()
        
        # Calculate rolling correlation
        corr_matrix = returns.rolling(window=window).corr().iloc[-len(returns.columns):]
        
        return corr_matrix
    
    def check_correlation_breach(self, corr_matrix: pd.DataFrame) -> List[CorrelationAlert]:
        """
        Check for correlation threshold breaches.
        
        From Tech Design:
        - Any pair > 0.7: Reduce combined weight cap
        - Portfolio avg > 0.5: Level 1 alert
        - All assets > 0.8 same direction: Auto Level 2
        
        Args:
            corr_matrix: Correlation matrix
            
        Returns:
            List of CorrelationAlert objects
        """
        if corr_matrix.empty:
            return []
        
        alerts = []
        high_corr_pairs = []
        
        # Check pairwise correlations
        for i, asset1 in enumerate(corr_matrix.columns):
            for j, asset2 in enumerate(corr_matrix.columns[i+1:], i+1):
                corr_value = corr_matrix.loc[asset1, asset2]
                
                if pd.notna(corr_value) and abs(corr_value) > self.THRESHOLDS["pair_warning"]:
                    high_corr_pairs.append((asset1, asset2, corr_value))
        
        if high_corr_pairs:
            alert = CorrelationAlert(
                level="WARNING",
                message=f"Found {len(high_corr_pairs)} high correlation pairs (>{self.THRESHOLDS['pair_warning']})",
                pairs=high_corr_pairs
            )
            alerts.append(alert)
            logger.warning(alert.message)
        
        # Check portfolio average correlation
        # Get upper triangle of correlation matrix (excluding diagonal)
        upper_tri = np.triu_indices_from(corr_matrix, k=1)
        correlations = corr_matrix.values[upper_tri]
        
        # Filter out NaN values
        correlations = correlations[~np.isnan(correlations)]
        
        if len(correlations) > 0:
            avg_corr = np.mean(np.abs(correlations))
            
            if avg_corr > self.THRESHOLDS["portfolio_warning"]:
                alert = CorrelationAlert(
                    level="LEVEL_1",
                    message=f"Portfolio avg correlation: {avg_corr:.2f} > {self.THRESHOLDS['portfolio_warning']}",
                    avg_correlation=avg_corr
                )
                alerts.append(alert)
                logger.warning(alert.message)
            
            # Check for extreme correlation (all assets moving together)
            if avg_corr > self.THRESHOLDS["extreme_threshold"]:
                alert = CorrelationAlert(
                    level="LEVEL_2",
                    message=f"EXTREME: Portfolio avg correlation: {avg_corr:.2f} > {self.THRESHOLDS['extreme_threshold']}",
                    avg_correlation=avg_corr
                )
                alerts.append(alert)
                logger.critical(alert.message)
        
        return alerts
    
    def get_correlation_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Get current correlation matrix (last 60 days).
        
        Args:
            returns: DataFrame with assets as columns
            
        Returns:
            Correlation matrix
        """
        if returns.empty or len(returns) < 60:
            return pd.DataFrame()
        
        # Use last 60 days
        recent_returns = returns.tail(60)
        corr_matrix = recent_returns.corr()
        
        return corr_matrix