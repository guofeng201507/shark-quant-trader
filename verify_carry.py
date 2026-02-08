"""Verification script for Crypto Carry Strategy"""

import os
import pandas as pd
from dotenv import load_dotenv
from src.data.provider import DataProvider
from src.factors.carry import CryptoCarry
from src.utils.logger import logger

def verify_carry():
    load_dotenv()
    print("Starting Crypto Carry verification...")
    
    # 1. Fetch funding rates
    dp = DataProvider()
    symbol = "BTC-USD"
    funding_df = dp.fetch_funding_rate(symbol, limit=100)
    
    if funding_df is None or funding_df.empty:
        logger.error("Failed to fetch funding rates")
        return
        
    logger.info(f"Fetched {len(funding_df)} funding rate records for {symbol}")
    logger.info(f"Latest funding rate: {funding_df['fundingRate'].iloc[-1]:.4%}")
    
    # 2. Generate signals
    carry = CryptoCarry(funding_threshold=0.0001)  # 0.01%
    funding_data = {symbol: funding_df}
    signals = carry.generate_signals(funding_data)
    
    for sym, info in signals.items():
        logger.info(f"Signal for {sym}: {info['signal']}")
        logger.info(f"Annualized Yield: {info['annualized_yield']:.2%}")
    
    # 3. Analyze risk
    risk_metrics = carry.analyze_risk(funding_data)
    for sym, metrics in risk_metrics.items():
        logger.info(f"Risk for {sym}: Volatility={metrics['volatility_8h']:.6f}, Z-Score={metrics['z_score']:.2f}, Volatile={metrics['is_volatile']}")

if __name__ == "__main__":
    verify_carry()
