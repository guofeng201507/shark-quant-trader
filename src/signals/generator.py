"""Signal Generator with market regime filtering - Tech Design v1.1 Section 4.3.2"""

import pandas as pd
from typing import Dict, List
from datetime import datetime
from ..models.domain import TradeSignal, SignalType, MarketRegime
from ..utils.logger import logger


class SignalGenerator:
    """Generate trading signals with VIX-based market regime filtering"""
    
    # Signal thresholds
    THRESHOLDS = {
        "momentum_high": 0.10,      # 10% for STRONG_BUY
        "momentum_low": 0.03,       # 3% for BUY
        "momentum_neg": -0.03,      # -3% for SELL
        "momentum_neg_high": -0.10  # -10% for STRONG_SELL
    }
    
    # VIX regime thresholds
    VIX_THRESHOLDS = {
        "normal": 20,
        "elevated": 30,
        "extreme": 40
    }
    
    def __init__(self):
        """Initialize signal generator"""
        logger.info("SignalGenerator initialized")
    
    def generate(self, factors: Dict[str, pd.DataFrame], 
                current_positions: Dict[str, float],
                vix: float = None) -> List[TradeSignal]:
        """
        Generate trading signals for all symbols.
        
        Signal Logic (from Tech Design):
        - STRONG_BUY: momentum > high_threshold AND price > SMA_50 AND price > SMA_200 AND VIX < 30
        - BUY: momentum > low_threshold AND price > SMA_20
        - SELL: momentum < neg_threshold OR price < SMA_50
        - STRONG_SELL: momentum < neg_high_threshold AND price < SMA_200
        - HOLD: all other cases
        
        Market Regime Filters:
        - High volatility (VIX > 30): Reduce all signal confidence by 50%
        - Extreme volatility (VIX > 40): Only allow reduce position signals
        
        Args:
            factors: Dict mapping symbol -> factors DataFrame
            current_positions: Dict mapping symbol -> current quantity
            vix: Current VIX level (optional)
            
        Returns:
            List of TradeSignal objects
        """
        signals = []
        regime = self._determine_regime(vix)
        
        logger.info(f"Generating signals for {len(factors)} symbols in {regime.value} regime")
        
        for symbol, factor_df in factors.items():
            try:
                signal = self._generate_single_signal(
                    symbol, 
                    factor_df, 
                    current_positions.get(symbol, 0.0),
                    regime
                )
                
                if signal:
                    # Apply regime filter
                    signal = self._apply_regime_filter(signal, vix or 0)
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Signal generation failed for {symbol}: {e}")
        
        logger.info(f"Generated {len(signals)} signals")
        return signals
    
    def _generate_single_signal(self, symbol: str, factors: pd.DataFrame,
                                current_position: float, regime: MarketRegime) -> TradeSignal:
        """Generate signal for a single symbol"""
        
        # Get latest factor values
        if factors.empty:
            return None
            
        latest = factors.iloc[-1]
        
        # Extract key factors
        momentum_60 = latest.get('Momentum_60', 0)
        price_vs_sma_20 = latest.get('Price_vs_SMA_20', 0)
        price_vs_sma_50 = latest.get('Price_vs_SMA_50', 0)
        price_vs_sma_200 = latest.get('Price_vs_SMA_200', 0)
        
        # Determine signal type
        signal_type, confidence, reason = self._determine_signal_type(
            momentum_60, price_vs_sma_20, price_vs_sma_50, 
            price_vs_sma_200, regime
        )
        
        # Calculate target weight based on signal
        target_weight = self._calculate_target_weight(signal_type, symbol)
        
        return TradeSignal(
            symbol=symbol,
            signal=signal_type,
            confidence=confidence,
            target_weight=target_weight,
            reason=reason,
            timestamp=datetime.now(),
            regime=regime
        )
    
    def _determine_signal_type(self, momentum: float, price_vs_sma_20: float,
                               price_vs_sma_50: float, price_vs_sma_200: float,
                               regime: MarketRegime) -> tuple:
        """
        Determine signal type based on momentum and price vs SMAs.
        
        Returns:
            tuple of (SignalType, confidence, reason)
        """
        
        # STRONG_BUY: High momentum + above SMA_50 and SMA_200 + Normal VIX
        if (momentum > self.THRESHOLDS["momentum_high"] and 
            price_vs_sma_50 > 0 and 
            price_vs_sma_200 > 0 and
            regime in [MarketRegime.NORMAL, MarketRegime.ELEVATED]):
            return (
                SignalType.STRONG_BUY, 
                0.9,
                f"Strong momentum {momentum:.2%}, above 50 & 200 SMA, regime={regime.value}"
            )
        
        # BUY: Positive momentum + above SMA_20
        if momentum > self.THRESHOLDS["momentum_low"] and price_vs_sma_20 > 0:
            return (
                SignalType.BUY,
                0.7,
                f"Positive momentum {momentum:.2%}, above 20 SMA"
            )
        
        # STRONG_SELL: Large negative momentum + below SMA_200
        if (momentum < self.THRESHOLDS["momentum_neg_high"] and 
            price_vs_sma_200 < 0):
            return (
                SignalType.STRONG_SELL,
                0.9,
                f"Strong negative momentum {momentum:.2%}, below 200 SMA"
            )
        
        # SELL: Negative momentum OR below SMA_50
        if momentum < self.THRESHOLDS["momentum_neg"] or price_vs_sma_50 < 0:
            return (
                SignalType.SELL,
                0.7,
                f"Negative momentum {momentum:.2%} or below 50 SMA"
            )
        
        # HOLD: Default case
        return (
            SignalType.HOLD,
            0.5,
            f"Neutral conditions, momentum {momentum:.2%}"
        )
    
    def _calculate_target_weight(self, signal_type: SignalType, symbol: str) -> float:
        """
        Calculate target portfolio weight based on signal type.
        Uses max weights from config (Tech Design Section 3.4.1).
        """
        # Maximum weights per asset from Tech Design
        MAX_WEIGHTS = {
            "GLD": 0.50,
            "SPY": 0.40,
            "QQQ": 0.30,
            "BTC-USD": 0.15,
            "SLV": 0.15,
            "XLK": 0.20,
            "XLF": 0.15,
            "XLE": 0.15,
            "XLV": 0.15,
            "TLT": 0.30,
            "TIP": 0.15,
            "EFA": 0.20,
            "EEM": 0.15,
            "DBC": 0.15,
            "VNQ": 0.15
        }
        
        max_weight = MAX_WEIGHTS.get(symbol, 0.20)  # Default 20% if not specified
        
        if signal_type == SignalType.STRONG_BUY:
            return max_weight
        elif signal_type == SignalType.BUY:
            return max_weight * 0.7
        elif signal_type == SignalType.SELL:
            return max_weight * 0.3
        elif signal_type == SignalType.STRONG_SELL:
            return 0.0
        else:  # HOLD
            return max_weight * 0.5
    
    def _determine_regime(self, vix: float = None) -> MarketRegime:
        """
        Determine market regime based on VIX level.
        
        Args:
            vix: VIX index level
            
        Returns:
            MarketRegime enum
        """
        if vix is None:
            return MarketRegime.NORMAL
        
        if vix >= self.VIX_THRESHOLDS["extreme"]:
            return MarketRegime.EXTREME
        elif vix >= self.VIX_THRESHOLDS["elevated"]:
            return MarketRegime.HIGH_VOL
        elif vix >= self.VIX_THRESHOLDS["normal"]:
            return MarketRegime.ELEVATED
        else:
            return MarketRegime.NORMAL
    
    def _apply_regime_filter(self, signal: TradeSignal, vix: float) -> TradeSignal:
        """
        Apply VIX-based regime filtering to signal.
        
        From Tech Design:
        - VIX > 40: Only allow reduce position signals
        - VIX > 30: Reduce confidence by 50%
        """
        if vix > self.VIX_THRESHOLDS["extreme"]:
            # Extreme volatility: Only allow SELL signals
            if signal.signal in [SignalType.BUY, SignalType.STRONG_BUY]:
                logger.warning(f"Blocking BUY signal for {signal.symbol} due to extreme VIX={vix:.1f}")
                return TradeSignal(
                    symbol=signal.symbol,
                    signal=SignalType.HOLD,
                    confidence=0.3,
                    target_weight=signal.target_weight * 0.5,
                    reason=f"Original signal blocked by extreme VIX={vix:.1f}",
                    timestamp=signal.timestamp,
                    regime=signal.regime
                )
        
        elif vix > self.VIX_THRESHOLDS["elevated"]:
            # High volatility: Reduce confidence by 50%
            return TradeSignal(
                symbol=signal.symbol,
                signal=signal.signal,
                confidence=signal.confidence * 0.5,
                target_weight=signal.target_weight,
                reason=f"{signal.reason} (confidence reduced due to VIX={vix:.1f})",
                timestamp=signal.timestamp,
                regime=signal.regime
            )
        
        return signal