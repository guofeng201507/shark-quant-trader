"""Model Evaluation Module - PRD FR-3.3

Implements evaluation metrics: IC, IC_IR, AUC-ROC, risk-adjusted returns.
Provides SHAP-based explainability and model monitoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import stats
from ..utils.logger import logger


class ModelEvaluator:
    """
    Model evaluation with finance-specific metrics.
    
    FR-3.3 Requirements:
    - Information Coefficient (IC) and IC_IR
    - AUC-ROC
    - Risk-adjusted returns (Sharpe of signal-based portfolio)
    - SHAP values for explainability
    - Feature importance (global)
    - Model monitoring: rolling IC, feature drift, prediction drift
    """
    
    def __init__(self):
        self.metrics_history: List[Dict] = []
        logger.info("ModelEvaluator initialized")
    
    def calculate_ic(self, y_true: pd.Series, y_pred: pd.Series) -> float:
        """
        Calculate Information Coefficient (rank correlation).
        
        IC measures the correlation between predicted and actual returns.
        """
        # Use Spearman rank correlation
        ic, _ = stats.spearmanr(y_true, y_pred, nan_policy='omit')
        return ic if not np.isnan(ic) else 0.0
    
    def calculate_ic_ir(self, ic_series: pd.Series) -> float:
        """
        Calculate IC Information Ratio (IC mean / IC std).
        
        IC_IR measures consistency of predictions.
        """
        if len(ic_series) < 2 or ic_series.std() == 0:
            return 0.0
        return ic_series.mean() / ic_series.std()
    
    def calculate_rolling_ic(self,
                            y_true: pd.Series,
                            y_pred: pd.Series,
                            window: int = 63) -> pd.Series:
        """
        Calculate rolling IC for monitoring.
        
        FR-3.3: Rolling IC decay curve for model monitoring
        """
        df = pd.DataFrame({'true': y_true, 'pred': y_pred})
        
        # Calculate rolling rank correlation
        rolling_ic = df.rolling(window).apply(
            lambda x: stats.spearmanr(x['true'], x['pred'])[0] if len(x) > 1 else np.nan,
            raw=False
        )
        
        return rolling_ic['true']
    
    def evaluate(self,
                y_true: pd.Series,
                y_pred: pd.Series,
                returns: Optional[pd.Series] = None) -> Dict[str, float]:
        """
        Comprehensive model evaluation.
        
        Args:
            y_true: True target values
            y_pred: Predicted values
            returns: Actual returns (for portfolio metrics)
            
        Returns:
            Dictionary of evaluation metrics
        """
        metrics = {}
        
        # IC metrics
        metrics['ic'] = self.calculate_ic(y_true, y_pred)
        
        # AUC-ROC (if binary classification)
        if set(y_true.unique()).issubset({-1, 0, 1}):
            from sklearn.metrics import roc_auc_score
            try:
                # Convert to binary (0/1)
                y_true_binary = (y_true > 0).astype(int)
                metrics['auc'] = roc_auc_score(y_true_binary, y_pred)
            except:
                metrics['auc'] = 0.5
        
        # Portfolio metrics (if returns provided)
        if returns is not None:
            metrics.update(self._calculate_portfolio_metrics(y_pred, returns))
        
        # Store metrics history
        self.metrics_history.append(metrics)
        
        return metrics
    
    def _calculate_portfolio_metrics(self,
                                    y_pred: pd.Series,
                                    returns: pd.Series) -> Dict[str, float]:
        """Calculate portfolio-based metrics"""
        metrics = {}
        
        # Long-short portfolio based on predictions
        long_mask = y_pred > y_pred.quantile(0.8)
        short_mask = y_pred < y_pred.quantile(0.2)
        
        long_returns = returns[long_mask].mean() if long_mask.any() else 0
        short_returns = returns[short_mask].mean() if short_mask.any() else 0
        
        # Long-short spread
        metrics['long_short_return'] = long_returns - short_returns
        
        # Sharpe of signal-based portfolio
        portfolio_returns = returns * np.sign(y_pred - y_pred.median())
        if portfolio_returns.std() > 0:
            metrics['signal_sharpe'] = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)
        else:
            metrics['signal_sharpe'] = 0.0
        
        return metrics
    
    def explain_with_shap(self,
                         model,
                         X: pd.DataFrame,
                         feature_cols: List[str],
                         sample_size: int = 1000) -> Optional[pd.DataFrame]:
        """
        Generate SHAP values for model explainability.
        
        FR-3.3: SHAP values for each prediction
        """
        try:
            import shap
            
            # Sample data for SHAP calculation
            X_sample = X[feature_cols].fillna(0).sample(min(sample_size, len(X)))
            
            # Create explainer
            if hasattr(model, 'predict_proba'):
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_sample)
            else:
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_sample)
            
            # Create summary DataFrame
            shap_summary = pd.DataFrame({
                'feature': feature_cols,
                'mean_shap': np.abs(shap_values).mean(axis=0) if isinstance(shap_values, np.ndarray) else np.abs(shap_values[1]).mean(axis=0),
            })
            shap_summary = shap_summary.sort_values('mean_shap', ascending=False)
            
            logger.info(f"SHAP values calculated for {len(feature_cols)} features")
            return shap_summary
            
        except Exception as e:
            logger.warning(f"SHAP calculation failed: {e}")
            return None
    
    def get_feature_importance(self, model, feature_cols: List[str]) -> pd.DataFrame:
        """
        Get global feature importance from model.
        
        FR-3.3: Feature importance (global)
        """
        importance = {}
        
        if hasattr(model, 'feature_importances_'):
            importance = dict(zip(feature_cols, model.feature_importances_))
        elif hasattr(model, 'coef_'):
            importance = dict(zip(feature_cols, np.abs(model.coef_)))
        
        df = pd.DataFrame({
            'feature': list(importance.keys()),
            'importance': list(importance.values())
        })
        df = df.sort_values('importance', ascending=False)
        
        return df
    
    def detect_feature_drift(self,
                            X_current: pd.DataFrame,
                            X_reference: pd.DataFrame,
                            feature_cols: List[str],
                            threshold: float = 0.1) -> Dict[str, float]:
        """
        Detect feature distribution drift using KS test.
        
        FR-3.3: Feature importance drift detection
        FR-3.5: KS > 0.1 triggers alert, KS > 0.2 triggers retraining
        """
        drift_scores = {}
        
        for col in feature_cols:
            if col not in X_current.columns or col not in X_reference.columns:
                continue
            
            current = X_current[col].dropna()
            reference = X_reference[col].dropna()
            
            if len(current) < 10 or len(reference) < 10:
                continue
            
            # KS test
            ks_stat, p_value = stats.ks_2samp(current, reference)
            drift_scores[col] = ks_stat
            
            if ks_stat > 0.2:
                logger.warning(f"Severe drift detected in {col}: KS={ks_stat:.3f}")
            elif ks_stat > 0.1:
                logger.warning(f"Moderate drift detected in {col}: KS={ks_stat:.3f}")
        
        return drift_scores
    
    def detect_prediction_drift(self,
                               y_pred_current: pd.Series,
                               y_pred_reference: pd.Series,
                               threshold: float = 0.1) -> float:
        """
        Detect prediction distribution drift using KS test.
        
        FR-3.3: Prediction distribution offset detection
        """
        ks_stat, p_value = stats.ks_2samp(y_pred_current, y_pred_reference)
        
        if ks_stat > threshold:
            logger.warning(f"Prediction drift detected: KS={ks_stat:.3f}")
        
        return ks_stat
    
    def generate_report(self) -> Dict:
        """Generate evaluation report"""
        if not self.metrics_history:
            return {}
        
        report = {
            'n_evaluations': len(self.metrics_history),
            'latest_metrics': self.metrics_history[-1],
            'average_ic': np.mean([m.get('ic', 0) for m in self.metrics_history]),
            'ic_trend': 'improving' if len(self.metrics_history) > 1 and 
                        self.metrics_history[-1].get('ic', 0) > self.metrics_history[0].get('ic', 0)
                        else 'stable/declining',
        }
        
        return report
