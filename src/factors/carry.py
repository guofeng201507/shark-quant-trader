"""Crypto Carry Strategy Factor - PRD FR-2.2"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ..utils.logger import logger

class CryptoCarry:
    """
    Implements funding rate arbitrage (carry) logic for Crypto.
    Focuses on Spot-Futures arbitrage: Long Spot, Short Perpetual.
    
    PRD FR-2.2 Constraints:
    - Max arbitrage position: 10% of portfolio
    - Max single exchange exposure: 8% of portfolio (counterparty risk)
    - Funding rate volatility > 3x historical std: pause new positions
    - Basis deviation > 2%: trigger alert
    """
    
    # Thresholds per PRD FR-2.2 and Tech Design 4.5.2
    THRESHOLDS = {
        "entry_rate": 0.0001,          # 0.01% per 8h = ~10% annualized
        "exit_rate": -0.0001,          # Close when rate inverts
        "max_position": 0.10,          # Max 10% of portfolio
        "max_exchange_exposure": 0.08, # Max 8% per exchange (counterparty risk)
        "basis_deviation_alert": 0.02, # 2% basis deviation triggers alert
    }
    
    def __init__(self, funding_threshold: float = None, exit_threshold: float = None,
                 max_position: float = None, max_exchange_exposure: float = None):
        """
        Initialize carry factor.
        
        Args:
            funding_threshold: 8h funding rate threshold to enter (default 0.01%)
            exit_threshold: 8h funding rate threshold to exit (default -0.01%)
            max_position: Max arbitrage position as fraction of portfolio (default 10%)
            max_exchange_exposure: Max single exchange exposure (default 8%)
        """
        self.funding_threshold = funding_threshold or self.THRESHOLDS["entry_rate"]
        self.exit_threshold = exit_threshold or self.THRESHOLDS["exit_rate"]
        self.max_position = max_position or self.THRESHOLDS["max_position"]
        self.max_exchange_exposure = max_exchange_exposure or self.THRESHOLDS["max_exchange_exposure"]
        logger.info(f"CryptoCarry initialized: entry={self.funding_threshold:.4%}, "
                    f"exit={self.exit_threshold:.4%}, max_pos={self.max_position:.0%}, "
                    f"max_exchange={self.max_exchange_exposure:.0%}")

    def calculate_annualized_yield(self, funding_rate: float) -> float:
        """Convert 8-hour funding rate to annualized yield"""
        # 3 payments per day, 365 days per year
        return funding_rate * 3 * 365

    def generate_signals(self, funding_data: Dict[str, pd.DataFrame],
                         current_positions: Optional[Dict[str, float]] = None,
                         portfolio_value: float = 1.0) -> Dict[str, Dict]:
        """
        Generate carry arbitrage signals based on funding rates.
        
        Args:
            funding_data: Dict mapping symbol -> funding rate history DataFrame
            current_positions: Dict mapping symbol -> current position value (optional)
            portfolio_value: Total portfolio value for position limit checks
            
        Returns:
            Dict mapping symbol -> signal info
        """
        signals = {}
        current_positions = current_positions or {}
        
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
            
            # PRD FR-2.2: Check max position constraint (10% of portfolio)
            current_pos = current_positions.get(symbol, 0)
            position_pct = abs(current_pos) / portfolio_value if portfolio_value > 0 else 0
            if signal == "ARBITRAGE_OPEN" and position_pct >= self.max_position:
                signal = "HOLD"  # Block new position, already at limit
                logger.warning(f"Carry position limit reached for {symbol}: "
                              f"{position_pct:.1%} >= {self.max_position:.0%}")
            
            # PRD FR-2.2: Check max exchange exposure (8% per exchange)
            if signal == "ARBITRAGE_OPEN" and position_pct >= self.max_exchange_exposure:
                signal = "HOLD"
                logger.warning(f"Exchange exposure limit reached for {symbol}: "
                              f"{position_pct:.1%} >= {self.max_exchange_exposure:.0%}")
                
            signals[symbol] = {
                "signal": signal,
                "funding_rate_8h": latest_rate,
                "annualized_yield": annual_yield,
                "timestamp": df.index[-1],
                "position_pct": position_pct,
                "max_position": self.max_position,
                "max_exchange_exposure": self.max_exchange_exposure,
            }
            
            if signal != "HOLD":
                logger.info(f"Carry Signal for {symbol}: {signal} (Rate: {latest_rate:.4%}, Yield: {annual_yield:.2%})")
                
        return signals

    def analyze_risk(self, funding_data: Dict[str, pd.DataFrame],
                     basis_data: Optional[Dict[str, float]] = None) -> Dict[str, Dict]:
        """
        Analyze risk metrics for carry strategy (PRD FR-2.2 Risk Control).
        
        - Funding rate volatility > 3x historical std: pause new positions
        - Basis deviation > 2%: trigger alert
        - Counterparty exposure monitoring
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
            z_score = (latest_rate - mean_rate) / vol if vol > 0 else 0
            
            # Check basis deviation (PRD FR-2.2: > 2% triggers alert)
            basis_deviation = 0.0
            basis_alert = False
            if basis_data and symbol in basis_data:
                basis_deviation = abs(basis_data[symbol])
                basis_alert = basis_deviation > self.THRESHOLDS["basis_deviation_alert"]
            
            risk_metrics[symbol] = {
                "volatility_8h": vol,
                "z_score": z_score,
                "is_volatile": bool(is_volatile),
                "pause_new_positions": bool(is_volatile),
                "basis_deviation": basis_deviation,
                "basis_alert": basis_alert,
            }
            
            if is_volatile:
                logger.warning(f"High Funding Volatility for {symbol}: Z-Score = {z_score:.2f} — pausing new positions")
            if basis_alert:
                logger.warning(f"Basis Deviation Alert for {symbol}: {basis_deviation:.2%} > {self.THRESHOLDS['basis_deviation_alert']:.0%}")
                
        return risk_metrics
