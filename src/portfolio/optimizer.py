"""Portfolio Optimization using riskfolio-lib - PRD FR-2.3"""

import pandas as pd
import numpy as np
import riskfolio as rp
from typing import Dict, List, Optional
from ..utils.logger import logger

class PortfolioOptimizer:
    """
    Implements advanced portfolio optimization techniques.
    Primary focus: Hierarchical Risk Parity (HRP) or Vanilla Risk Parity.
    """
    
    def __init__(self, target_vol: float = 0.15):
        """
        Initialize optimizer.
        
        Args:
            target_vol: Target annualized volatility (default 15%)
        """
        self.target_vol = target_vol
        logger.info(f"PortfolioOptimizer initialized with target_vol={target_vol:.1%}")

    def calculate_risk_parity_weights(self, returns: pd.DataFrame, 
                                     method: str = 'RP') -> Dict[str, float]:
        """
        Calculate risk parity weights for a given set of returns.
        
        Args:
            returns: DataFrame of asset returns (columns are symbols)
            method: Optimization method ('RP' for Risk Parity, 'HRP' for Hierarchical Risk Parity)
            
        Returns:
            Dict mapping symbol -> weight
        """
        if returns.empty:
            logger.warning("Empty returns DataFrame provided for optimization")
            return {}
            
        try:
            # Create Portfolio object
            port = rp.Portfolio(returns=returns)
            
            # Estimate mean and covariance
            method_mu = 'hist'
            method_cov = 'hist'
            port.assets_stats(method_mu=method_mu, method_cov=method_cov)
            
            # Optimization parameters
            model = 'Classic'  # Could be 'Classic', 'BL', 'FM'
            rm = 'MV'         # Risk measure: MV for Variance
            obj = 'MinRisk'    # Objective: MinRisk for Risk Parity
            hist = True       # Use historical returns
            rf = 0            # Risk free rate
            b = None          # Benchmarks
            
            # Calculate weights
            if method == 'RP':
                w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=0, hist=hist)
            elif method == 'HRP':
                w = port.rp_optimization(model=model, rm=rm, rf=rf, b=b, hist=hist)
            else:
                logger.warning(f"Unsupported method {method}, falling back to RP")
                w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=0, hist=hist)
                
            if w is not None and not w.empty:
                # w is a DataFrame with 'weights' column
                weights = w['weights'].to_dict()
                return weights
                
        except Exception as e:
            logger.error(f"Riskfolio optimization failed: {e}")
            
        # Fallback: Inverse Volatility weighting
        return self._calculate_inverse_vol_weights(returns)

    def _calculate_inverse_vol_weights(self, returns: pd.DataFrame) -> Dict[str, float]:
        """Simple inverse volatility weighting fallback"""
        vols = returns.std() * np.sqrt(252)
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()
        return weights.to_dict()

    def scale_by_vol_target(self, weights: Dict[str, float], 
                           returns: pd.DataFrame) -> Dict[str, float]:
        """
        Scale weights based on target volatility (Volatility Targeting).
        
        Args:
            weights: Optimized weights
            returns: Asset returns
            
        Returns:
            Scaled weights
        """
        if not weights or returns.empty:
            return weights
            
        try:
            # Calculate portfolio volatility
            w_series = pd.Series(weights)
            cov = returns.cov() * 252
            port_vol = np.sqrt(np.dot(w_series.T, np.dot(cov, w_series)))
            
            if port_vol > 0:
                scale = self.target_vol / port_vol
                # Limit leverage to 1.5x as per PRD
                scale = min(scale, 1.5)
                
                scaled_weights = {s: w * scale for s, w in weights.items()}
                return scaled_weights
        except Exception as e:
            logger.error(f"Volatility scaling failed: {e}")
            
        return weights
