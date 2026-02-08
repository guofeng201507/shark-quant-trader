"""Demo script for Phase 2 functions: Enhanced Strategies"""

import os
import yaml
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.data.provider import DataProvider
from src.factors.momentum import CrossSectionalMomentum
from src.factors.carry import CryptoCarry
from src.factors.rotation import AssetRotation
from src.utils.logger import logger

def run_phase2_demo():
    load_dotenv()
    
    logger.info("=== Starting Shark Quant Trader Phase 2 Demo ===")
    
    # 1. Load Configuration
    with open("config/strategy.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    core_symbols = list(config['core_assets'].keys())
    extended_symbols = [a['symbol'] for a in config['extended_assets']]
    all_symbols = core_symbols + extended_symbols
    
    logger.info(f"Expanded asset universe: {len(all_symbols)} assets")
    
    # 2. Fetch Data
    dp = DataProvider()
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=500)).strftime("%Y-%m-%d")
    
    logger.info(f"Fetching data from {start_date} to {end_date}...")
    prices = dp.fetch(all_symbols, start_date, end_date)
    
    if not prices:
        logger.error("Failed to fetch price data")
        return
        
    # 3. Cross-Sectional Momentum Ranking
    logger.info("--- Step 1: Cross-Sectional Momentum ---")
    cs_momentum = CrossSectionalMomentum()
    momentum_rets = cs_momentum.calculate_momentum_returns(prices)
    ranks = cs_momentum.rank_assets(momentum_rets)
    
    logger.info("Asset Momentum Ranks (Top 30%):")
    top_30 = ranks[ranks >= 0.7].sort_values(ascending=False)
    for sym, rank in top_30.items():
        logger.info(f"  {sym: <8}: Rank {rank:.2f} (Ret: {momentum_rets[sym]:.2%})")
        
    # 4. Crypto Carry Strategy
    logger.info("--- Step 2: Crypto Carry Strategy ---")
    carry = CryptoCarry()
    # Fetch funding for BTC
    btc_funding = dp.fetch_funding_rate("BTC-USD", limit=50)
    if btc_funding is not None:
        carry_signals = carry.generate_signals({"BTC-USD": btc_funding})
        btc_info = carry_signals.get("BTC-USD")
        if btc_info:
            logger.info(f"BTC Funding Rate: {btc_info['funding_rate_8h']:.4%}")
            logger.info(f"Annualized Yield: {btc_info['annualized_yield']:.2%}")
            logger.info(f"Carry Signal: {btc_info['signal']}")
    
    # 5. Asset Rotation (Momentum + Risk Parity)
    logger.info("--- Step 3: Tactical Asset Rotation ---")
    rotation = AssetRotation(all_symbols, target_vol=config['portfolio']['target_volatility'])
    
    # Mock SMA_200 filter (in production, use FactorCalculator)
    # For demo, we'll assume everything is above SMA_200 except maybe a few
    sma_200_filter = {s: True for s in all_symbols}
    # Let's say BTC is below SMA_200 for demo purposes (if we want to see AVOID)
    # sma_200_filter['BTC-USD'] = False 
    
    rotation_weights = rotation.calculate_rotation_weights(prices, sma_200_filter)
    
    logger.info("Target Rotation Weights (Risk Parity Optimized):")
    for sym, weight in sorted(rotation_weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0:
            logger.info(f"  {sym: <8}: {weight:.2%}")

    logger.info("=== Phase 2 Demo Completed ===")

if __name__ == "__main__":
    run_phase2_demo()
