"""Unit tests for Factor Calculator"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.factors.calculator import FactorCalculator


@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing"""
    dates = pd.date_range(start='2023-01-01', periods=200, freq='D')
    
    # Generate synthetic price data
    np.random.seed(42)
    spy_prices = 100 * np.exp(np.cumsum(np.random.randn(200) * 0.01))
    gld_prices = 50 * np.exp(np.cumsum(np.random.randn(200) * 0.008))
    
    spy_df = pd.DataFrame({
        'Open': spy_prices * 0.99,
        'High': spy_prices * 1.01,
        'Low': spy_prices * 0.98,
        'Close': spy_prices,
        'Volume': np.random.randint(1000000, 5000000, 200)
    }, index=dates)
    
    gld_df = pd.DataFrame({
        'Open': gld_prices * 0.99,
        'High': gld_prices * 1.01,
        'Low': gld_prices * 0.98,
        'Close': gld_prices,
        'Volume': np.random.randint(500000, 2000000, 200)
    }, index=dates)
    
    return {
        'SPY': spy_df,
        'GLD': gld_df
    }


def test_factor_calculator_initialization():
    """Test FactorCalculator initialization"""
    calc = FactorCalculator()
    assert calc is not None
    assert 'momentum' in calc.FACTOR_CONFIG
    assert 'volatility' in calc.FACTOR_CONFIG


def test_calculate_momentum(sample_price_data):
    """Test momentum calculation"""
    calc = FactorCalculator()
    factors = calc.calculate(sample_price_data)
    
    assert 'SPY' in factors
    assert 'Momentum_60' in factors['SPY'].columns
    assert 'Momentum_120' in factors['SPY'].columns
    
    # Check that momentum values are reasonable
    momentum_60 = factors['SPY']['Momentum_60'].dropna()
    assert len(momentum_60) > 0
    assert momentum_60.abs().max() < 2.0  # Reasonable range


def test_calculate_volatility(sample_price_data):
    """Test volatility calculation"""
    calc = FactorCalculator()
    factors = calc.calculate(sample_price_data)
    
    assert 'Volatility_20' in factors['SPY'].columns
    assert 'Volatility_60' in factors['SPY'].columns
    
    # Volatility should be positive
    vol_20 = factors['SPY']['Volatility_20'].dropna()
    assert (vol_20 > 0).all()


def test_calculate_moving_averages(sample_price_data):
    """Test SMA calculation"""
    calc = FactorCalculator()
    factors = calc.calculate(sample_price_data)
    
    assert 'SMA_20' in factors['SPY'].columns
    assert 'SMA_50' in factors['SPY'].columns
    assert 'SMA_200' in factors['SPY'].columns
    
    # SMA should be close to price
    prices = sample_price_data['SPY']['Close']
    sma_20 = factors['SPY']['SMA_20']
    
    # Check last value is reasonable
    assert abs(sma_20.iloc[-1] / prices.iloc[-1] - 1) < 0.1


def test_calculate_rsi(sample_price_data):
    """Test RSI calculation"""
    calc = FactorCalculator()
    factors = calc.calculate(sample_price_data)
    
    assert 'RSI_14' in factors['SPY'].columns
    
    # RSI should be between 0 and 100
    rsi = factors['SPY']['RSI_14'].dropna()
    assert (rsi >= 0).all()
    assert (rsi <= 100).all()


def test_calculate_atr(sample_price_data):
    """Test ATR calculation"""
    calc = FactorCalculator()
    factors = calc.calculate(sample_price_data)
    
    assert 'ATR_14' in factors['SPY'].columns
    assert 'ATR_14_pct' in factors['SPY'].columns
    
    # ATR should be positive
    atr = factors['SPY']['ATR_14'].dropna()
    assert (atr > 0).all()


def test_empty_data():
    """Test handling of empty data"""
    calc = FactorCalculator()
    empty_data = {'SPY': pd.DataFrame()}
    
    factors = calc.calculate(empty_data)
    assert 'SPY' in factors
    assert factors['SPY'].empty


def test_cross_sectional_rank(sample_price_data):
    """Test cross-sectional ranking"""
    calc = FactorCalculator()
    factors = calc.calculate(sample_price_data)
    
    ranks = calc.calculate_cross_sectional_rank(factors, 'Momentum_60')
    
    assert len(ranks) == 2  # Two symbols
    assert ranks.min() >= 0
    assert ranks.max() <= 1