"""Crypto Carry Strategy Factor - PRD FR-2.2"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ..utils.logger import logger

class CryptoCarry:
    """
    Implements funding rate arbitrage (carry) logic for Crypto.
    Focuses on Spot-Futures arbitrage: Long Spot, Short Perpetual.
    """
    
    def __init__(self, funding_threshold: float = 0.0001, exit_threshold: float = -0.0001):
        """
        Initialize carry factor.
        
        Args:
            funding_threshold: 8h funding rate threshold to enter (default 0.01%)
            exit_threshold: 8h funding rate threshold to exit (default -0.01%)
        """
        self.funding_threshold = funding_threshold
        self.exit_threshold = exit_threshold
        logger.info(f"CryptoCarry initialized: entry={funding_threshold:.4%}, exit={exit_threshold:.4%}")

    def calculate_annualized_yield(self, funding_rate: float) -> float:
        """Convert 8-hour funding rate to annualized yield"""
        # 3 payments per day, 365 days per year
        return funding_rate * 3 * 365

    def generate_signals(self, funding_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Generate carry arbitrage signals based on funding rates.
        
        Args:
            funding_data: Dict mapping symbol -> funding rate history DataFrame
            
        Returns:
            Dict mapping symbol -> signal info
        """
        signals = {}
        
        for symbol, df in funding_data.items():
            if df is None or df.empty:
                continue
                
            # Get latest funding rate
            latest_rate = df['fundingRate'].iloc[-1]
            annual_yield = self.calculate_annualized_yield(latest_rate)
            
            signal = "HOLD"
            if latest_rate > self.funding_threshold:
                signal = "ARBITRAGE_OPEN"  # Long Spot, Short Perpetual
            elif latest_rate < self.exit_threshold:
                signal = "ARBITRAGE_CLOSE"
                
            signals[symbol] = {
                "signal": signal,
                "funding_rate_8h": latest_rate,
                "annualized_yield": annual_yield,
                "timestamp": df.index[-1]
            }
            
            if signal != "HOLD":
                logger.info(f"Carry Signal for {symbol}: {signal} (Rate: {latest_rate:.4%}, Yield: {annual_yield:.2%})")
                
        return signals

    def analyze_risk(self, funding_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Analyze risk metrics for carry strategy (PRD FR-2.2 Risk Control).
        
        - Funding rate volatility
        - Counterparty exposure (placeholder as we only use Binance for now)
        """
        risk_metrics = {}
        
        for symbol, df in funding_data.items():
            if df is None or df.empty or len(df) < 30:
                continue
                
            # Calculate funding rate volatility (standard deviation)
            vol = df['fundingRate'].std()
            latest_rate = df['fundingRate'].iloc[-1]
            mean_rate = df['fundingRate'].mean()
            
            # Check for extreme volatility (PRD: > 3x historical std dev)
            is_volatile = abs(latest_rate - mean_rate) > 3 * vol
            
            risk_metrics[symbol] = {
                "volatility_8h": vol,
                "z_score": (latest_rate - mean_rate) / vol if vol > 0 else 0,
                "is_volatile": bool(is_volatile)
            }
            
            if is_volatile:
                logger.warning(f"High Funding Volatility for {symbol}: Z-Score = {risk_metrics[symbol]['z_score']:.2f}")
                
        return risk_metrics
