"""Factor Calculator - Calculate all technical indicators"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, List
from ..utils.logger import logger


class FactorCalculator:
    """
    Calculate all technical factors for signal generation.
    Based on Tech Design v1.1 Section 4.2
    """
    
    FACTOR_CONFIG = {
        "momentum": {"periods": [60, 120]},
        "volatility": {"periods": [20, 60], "annualize": True},
        "sma": {"periods": [20, 50, 200]},
        "rsi": {"period": 14},
        "atr": {"period": 14}
    }
    
    TRADING_DAYS_PER_YEAR = 252
    
    def __init__(self):
        """Initialize factor calculator"""
        logger.info("FactorCalculator initialized")
    
    def calculate(self, prices: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Calculate all factors for given price data.
        
        Args:
            prices: Dict mapping symbol -> OHLCV DataFrame
            
        Returns:
            Dict mapping symbol -> factors DataFrame
        """
        factors = {}
        
        for symbol, df in prices.items():
            try:
                factor_df = self._calculate_single_symbol(df, symbol)
                factors[symbol] = factor_df
                logger.debug(f"Calculated {len(factor_df.columns)} factors for {symbol}")
            except Exception as e:
                logger.error(f"Factor calculation failed for {symbol}: {e}")
                
        return factors
    
    def _calculate_single_symbol(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Calculate all factors for a single symbol"""
        factors = pd.DataFrame(index=df.index)
        
        # Momentum factors
        factors = self._add_momentum(factors, df)
        
        # Volatility factors
        factors = self._add_volatility(factors, df)
        
        # Moving averages
        factors = self._add_moving_averages(factors, df)
        
        # RSI
        factors = self._add_rsi(factors, df)
        
        # ATR
        factors = self._add_atr(factors, df)
        
        return factors
    
    def _add_momentum(self, factors: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Add momentum factors: 60-day and 120-day cumulative returns
        """
        close = prices['close']
        
        for period in self.FACTOR_CONFIG["momentum"]["periods"]:
            # Cumulative return over period
            momentum = close.pct_change(period)
            factors[f'Momentum_{period}'] = momentum
            
        return factors
    
    def _add_volatility(self, factors: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Add volatility factors: 20-day and 60-day annualized volatility
        """
        close = prices['close']
        returns = close.pct_change()
        
        for period in self.FACTOR_CONFIG["volatility"]["periods"]:
            # Rolling volatility
            vol = returns.rolling(window=period).std()
            
            # Annualize if configured
            if self.FACTOR_CONFIG["volatility"]["annualize"]:
                vol = vol * np.sqrt(self.TRADING_DAYS_PER_YEAR)
                
            factors[f'Volatility_{period}'] = vol
            
        return factors
    
    def _add_moving_averages(self, factors: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Add simple moving averages: 20, 50, 200 days
        """
        close = prices['close']
        
        for period in self.FACTOR_CONFIG["sma"]["periods"]:
            sma = close.rolling(window=period).mean()
            factors[f'SMA_{period}'] = sma
            
            # Also calculate price relative to SMA (useful for signals)
            factors[f'Price_vs_SMA_{period}'] = (close - sma) / sma
            
        return factors
    
    def _add_rsi(self, factors: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Add RSI (Relative Strength Index) - 14 day
        """
        close = prices['close']
        period = self.FACTOR_CONFIG["rsi"]["period"]
        
        # Calculate RSI using pandas_ta
        rsi = ta.rsi(close, length=period)
        factors[f'RSI_{period}'] = rsi
        
        return factors
    
    def _add_atr(self, factors: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Add ATR (Average True Range) - 14 day
        Used for stop loss calculation
        """
        high = prices['high']
        low = prices['low']
        close = prices['close']
        period = self.FACTOR_CONFIG["atr"]["period"]
        
        # Calculate ATR using pandas_ta
        atr = ta.atr(high=high, low=low, close=close, length=period)
        factors[f'ATR_{period}'] = atr
        
        # Also calculate ATR as percentage of price (useful for stop loss)
        factors[f'ATR_{period}_pct'] = atr / close
        
        return factors
    
    def calculate_cross_sectional_rank(self, factors: Dict[str, pd.DataFrame], 
                                      factor_name: str,
                                      date: pd.Timestamp = None) -> pd.Series:
        """
        Rank assets cross-sectionally for momentum strategy.
        Used in Phase 2 for Top/Bottom 30% selection.
        
        Args:
            factors: Dict of factor DataFrames for each symbol
            factor_name: Name of factor to rank (e.g., 'Momentum_120')
            date: Date to rank at (defaults to last available date)
            
        Returns:
            Series with symbols as index and ranks as values (0-1 scale)
        """
        # Extract factor values for all symbols at specified date
        factor_values = {}
        
        for symbol, df in factors.items():
            if factor_name not in df.columns:
                logger.warning(f"Factor {factor_name} not found for {symbol}")
                continue
                
            if date is None:
                # Use most recent date
                value = df[factor_name].iloc[-1]
            else:
                if date in df.index:
                    value = df.loc[date, factor_name]
                else:
                    logger.warning(f"Date {date} not found for {symbol}")
                    continue
                    
            # Skip NaN values
            if pd.notna(value):
                factor_values[symbol] = value
        
        # Convert to Series and rank
        if not factor_values:
            logger.error("No valid factor values to rank")
            return pd.Series(dtype=float)
            
        series = pd.Series(factor_values)
        ranks = series.rank(pct=True)  # Percentile ranks (0-1)
        
        return ranks
    
    def get_latest_factors(self, factors: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        """
        Get the most recent factor values for all symbols.
        
        Args:
            factors: Dict of factor DataFrames
            
        Returns:
            Dict mapping symbol -> latest factor values as Series
        """
        latest = {}
        
        for symbol, df in factors.items():
            if not df.empty:
                latest[symbol] = df.iloc[-1]
                
        return latest