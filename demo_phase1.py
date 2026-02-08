#!/usr/bin/env python3
"""
Phase 1 Demo Script - Shark Quant Trader
Tests all major components with live data
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("SHARK QUANT TRADER - Phase 1 Demo")
print("=" * 60)
print()

# 1. Test Data Provider
print("[1/7] Testing Data Provider...")
print("-" * 40)
try:
    from src.data.provider import DataProvider
    
    provider = DataProvider()
    status = provider.get_source_status()
    print("   Data source status:")
    for source, state in status.items():
        print(f"   - {source}: {state}")
    
    # Fetch recent data for core assets
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
    
    symbols = ["GLD", "SPY", "QQQ", "BTC-USD"]
    print(f"\n   Fetching data for {symbols}...")
    print(f"   Period: {start_date} to {end_date}")
    
    data = provider.fetch(symbols, start_date, end_date)
    
    for symbol, df in data.items():
        print(f"   [OK] {symbol}: {len(df)} rows, latest close: ${df['close'].iloc[-1]:.2f}")
    
    print("   [PASS] Data Provider")
except Exception as e:
    print(f"   [FAIL] Data Provider - {e}")
    import traceback
    traceback.print_exc()
    data = {}

print()

# 2. Test Factor Calculator
print("[2/7] Testing Factor Calculator...")
print("-" * 40)
try:
    from src.factors.calculator import FactorCalculator
    import pandas as pd
    
    calculator = FactorCalculator()
    all_factors = {}
    
    if data:
        # Calculator expects dict of DataFrames
        factors_result = calculator.calculate(data)
        
        for symbol, factor_df in factors_result.items():
            all_factors[symbol] = factor_df
            if factor_df is not None and not factor_df.empty:
                print(f"   Factors for {symbol}: {list(factor_df.columns)}")
                # Show latest values
                latest = factor_df.iloc[-1]
                for col in factor_df.columns[:5]:  # Show first 5
                    val = latest[col]
                    if pd.notna(val):
                        print(f"      - {col}: {val:.4f}")
        
        print("   [PASS] Factor Calculator")
    else:
        print("   [SKIP] No data available")
except Exception as e:
    print(f"   [FAIL] Factor Calculator - {e}")
    import traceback
    traceback.print_exc()

print()

# 3. Test Signal Generator
print("[3/7] Testing Signal Generator...")
print("-" * 40)
try:
    from src.signals.generator import SignalGenerator
    
    generator = SignalGenerator()
    
    if data and all_factors:
        signals = generator.generate(all_factors, data)
        
        print(f"   Generated {len(signals)} signals:")
        for signal in signals:
            print(f"   - {signal.symbol}: {signal.signal.value} (confidence: {signal.confidence:.2f})")
        
        print("   [PASS] Signal Generator")
    else:
        print("   [SKIP] No data/factors available")
except Exception as e:
    print(f"   [FAIL] Signal Generator - {e}")
    import traceback
    traceback.print_exc()

print()

# 4. Test Risk Manager
print("[4/7] Testing Risk Manager...")
print("-" * 40)
try:
    from src.risk.manager import RiskManager
    from src.risk.correlation import CorrelationMonitor
    from src.models.domain import Portfolio
    
    risk_manager = RiskManager()
    correlation_monitor = CorrelationMonitor()
    
    # Create a test portfolio with 5% drawdown
    test_portfolio = Portfolio(
        positions={"GLD": 100, "SPY": 50, "QQQ": 30, "BTC-USD": 0.5},
        cash=20000,
        nav=100000,
        peak_nav=105000,
        weights={"GLD": 0.3, "SPY": 0.3, "QQQ": 0.2, "BTC-USD": 0.1, "CASH": 0.1},
        unrealized_pnl=-5000,
        cost_basis={"GLD": 400, "SPY": 600, "QQQ": 500, "BTC-USD": 80000}
    )
    
    # Check risk
    risk_assessment = risk_manager.check(test_portfolio)
    risk_level = risk_manager.get_risk_level()
    drawdown = (test_portfolio.peak_nav - test_portfolio.nav) / test_portfolio.peak_nav
    
    print(f"   Portfolio state:")
    print(f"   - NAV: ${test_portfolio.nav:,.2f}")
    print(f"   - Peak NAV: ${test_portfolio.peak_nav:,.2f}")
    print(f"   - Drawdown: {drawdown:.1%}")
    print(f"   - Risk Level: {risk_level}")
    
    # Calculate correlation matrix
    if data and len(data) >= 2:
        corr_matrix = correlation_monitor.calculate_rolling_correlation(data)
        if corr_matrix is not None and not corr_matrix.empty:
            print(f"\n   Correlation matrix:")
            print(corr_matrix.round(2).to_string().replace('\n', '\n   '))
            
            breaches = correlation_monitor.check_breaches(corr_matrix)
            if breaches:
                print(f"\n   [WARN] Correlation breaches: {breaches}")
            else:
                print(f"\n   [OK] No correlation breaches")
    
    print("   [PASS] Risk Manager")
except Exception as e:
    print(f"   [FAIL] Risk Manager - {e}")
    import traceback
    traceback.print_exc()

print()

# 5. Test Alert Manager
print("[5/7] Testing Alert Manager...")
print("-" * 40)
try:
    from src.alerts.manager import AlertManager, AlertLevel
    
    alert_manager = AlertManager()
    
    telegram_token = os.getenv("ALERT_TELEGRAM_TOKEN")
    telegram_chat = os.getenv("ALERT_TELEGRAM_CHAT_ID")
    
    if telegram_token and telegram_chat:
        print("   - Telegram: Configured")
        
        # Send test alert
        print("\n   Sending test alert to Telegram...")
        alert_manager.send_alert(
            level=AlertLevel.INFO,
            title="Shark Quant Trader - Test Alert",
            message=f"Phase 1 Demo running successfully!\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nAssets: GLD, SPY, QQQ, BTC-USD"
        )
        print("   [OK] Test alert sent!")
    else:
        print("   - Telegram: Not configured")
    
    print("   [PASS] Alert Manager")
except Exception as e:
    print(f"   [FAIL] Alert Manager - {e}")
    import traceback
    traceback.print_exc()

print()

# 6. Test State Manager
print("[6/7] Testing State Manager...")
print("-" * 40)
try:
    from src.state.manager import StateManager
    from src.models.domain import Portfolio
    
    state_manager = StateManager()
    
    # Create test portfolio
    test_portfolio = Portfolio(
        positions={"GLD": 100, "SPY": 50, "QQQ": 30, "BTC-USD": 0.5},
        cash=20000,
        nav=100000,
        peak_nav=100000,
        weights={"GLD": 0.3, "SPY": 0.3, "QQQ": 0.2, "BTC-USD": 0.1, "CASH": 0.1},
        unrealized_pnl=0,
        cost_basis={"GLD": 400, "SPY": 600, "QQQ": 500, "BTC-USD": 80000}
    )
    
    # Save state
    success = state_manager.save_portfolio_state(test_portfolio)
    print(f"   State saved: {success}")
    
    # Load state
    loaded = state_manager.load_latest_portfolio_state()
    if loaded:
        print(f"   State loaded:")
        print(f"   - NAV: ${loaded.nav:,.2f}")
        print(f"   - Positions: {loaded.positions}")
        print(f"   - Cash: ${loaded.cash:,.2f}")
    
    print("   [PASS] State Manager")
except Exception as e:
    print(f"   [FAIL] State Manager - {e}")
    import traceback
    traceback.print_exc()

print()

# 7. Test Backtest Engine
print("[7/7] Testing Backtest Engine...")
print("-" * 40)
try:
    from src.backtest.engine import Backtester
    
    backtester = Backtester(initial_capital=100000)
    
    symbols = ["GLD", "SPY", "QQQ", "BTC-USD"]
    print(f"   Running backtest...")
    print(f"   Period: {start_date} to {end_date}")
    
    result = backtester.run(symbols, start_date, end_date)
    
    if result:
        print(f"\n   Backtest Results:")
        print(f"   - Total Return: {result.total_return:.2%}")
        print(f"   - Annualized Return: {result.annualized_return:.2%}")
        print(f"   - Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   - Max Drawdown: {result.max_drawdown:.2%}")
        print(f"   - Win Rate: {result.win_rate:.1%}")
        print(f"   - Trades: {result.num_trades}")
        print("   [PASS] Backtest Engine")
    else:
        print("   [WARN] Backtest returned no results")
except Exception as e:
    print(f"   [FAIL] Backtest Engine - {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Phase 1 Demo Complete!")
print("=" * 60)
