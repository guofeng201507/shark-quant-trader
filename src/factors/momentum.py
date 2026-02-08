"""Cross-Sectional Momentum Factor - Based on Asness (2013)"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ..utils.logger import logger

class CrossSectionalMomentum:
    """
    Implements cross-sectional momentum ranking logic.
    Based on "Value and Momentum Everywhere" (Asness, 2013).
    """
    
    def __init__(self, lookback_months: int = 12, skip_months: int = 1):
        """
        Initialize momentum calculator.
        
        Args:
            lookback_months: Total months to look back (default 12)
            skip_months: Recent months to skip to avoid short-term reversal (default 1)
        """
        self.lookback_days = lookback_months * 21  # Approx 21 trading days per month
        self.skip_days = skip_months * 21
        logger.info(f"CrossSectionalMomentum initialized: {lookback_months}-1 month")

    def calculate_momentum_returns(self, prices: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        Calculate 12-1 month momentum returns for all assets.
        
        Args:
            prices: Dict mapping symbol -> OHLCV DataFrame
            
        Returns:
            Series mapping symbol -> momentum return
        """
        momentum_returns = {}
        
        for symbol, df in prices.items():
            if len(df) < self.lookback_days:
                logger.warning(f"Insufficient data for {symbol} momentum: {len(df)} < {self.lookback_days}")
                continue
                
            # Get prices at specific points
            try:
                price_now = df['close'].iloc[-self.skip_days - 1]
                price_then = df['close'].iloc[-self.lookback_days - 1]
                
                # Cumulative return: (P_t-skip / P_t-lookback) - 1
                ret = (price_now / price_then) - 1
                momentum_returns[symbol] = ret
            except Exception as e:
                logger.error(f"Error calculating momentum for {symbol}: {e}")
                
        return pd.Series(momentum_returns)

    def rank_assets(self, momentum_returns: pd.Series) -> pd.Series:
        """
        Rank assets by returns (percentile rank).
        
        Returns:
            Series mapping symbol -> rank (0.0 to 1.0)
        """
        if momentum_returns.empty:
            return pd.Series(dtype=float)
            
        return momentum_returns.rank(pct=True)

    def get_signals(self, ranks: pd.Series, 
                    sma_200_filter: Dict[str, bool]) -> Dict:
        """
        Generate signals based on ranks and filters.
        
        Args:
            ranks: Series of percentile ranks
            sma_200_filter: Dict mapping symbol -> is_above_sma_200
            
        Returns:
            Dict with keys:
                - 'signals': Dict mapping symbol -> signal ("LONG", "AVOID", "HOLD")
                - 'defense_mode': bool indicating if defense mode is triggered
        """
        signals = {}
        defense_mode = False
        
        for symbol, rank in ranks.items():
            is_above_sma = sma_200_filter.get(symbol, False)
            
            if rank >= 0.7:  # Top 30%
                if is_above_sma:
                    signals[symbol] = "LONG"
                else:
                    signals[symbol] = "AVOID"  # Trend filter failed
            elif rank <= 0.3:  # Bottom 30%
                signals[symbol] = "AVOID"
            else:
                signals[symbol] = "HOLD"
                
        # Check defense mode: If >50% of Top group below SMA_200 (PRD FR-2.1)
        top_group = [s for s, r in ranks.items() if r >= 0.7]
        if top_group:
            top_above_sma = [s for s in top_group if sma_200_filter.get(s, False)]
            if len(top_above_sma) / len(top_group) < 0.5:
                defense_mode = True
                logger.warning("Defense Mode Triggered: >50% of Top Momentum assets below SMA_200")
                # Override all signals to AVOID except safe havens (GLD, TLT)
                safe_havens = {"GLD", "TLT"}
                for symbol in signals:
                    if symbol not in safe_havens:
                        signals[symbol] = "AVOID"
                
        return {"signals": signals, "defense_mode": defense_mode}
