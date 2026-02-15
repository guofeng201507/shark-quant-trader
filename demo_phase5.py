#!/usr/bin/env python3
"""
Phase 5 Paper Trading System Demo

This demo validates the paper trading implementation:
1. PaperTradingEngine - Order execution with slippage/delay simulation
2. RealTimePerformanceMonitor - IC, KS, Sharpe, drawdown tracking
3. GateValidationSystem - Gate requirement validation

Based on Tech Design v1.2 Section 4.11
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd

from src.paper_trading import (
    PaperTradingEngine,
    SlippageConfig,
    DelayConfig,
    RealTimePerformanceMonitor,
    MonitorConfig,
    GateValidationSystem
)
from src.models import BacktestResult


def print_section(title: str) -> None:
    """Print section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)


def demo_paper_trading_engine():
    """Demo: Paper Trading Engine with slippage and delay simulation"""
    print_section("1. Paper Trading Engine Demo")
    
    # Configure with custom slippage/delay
    slippage_config = SlippageConfig(
        base_slippage_bps=5.0,
        volatility_multiplier=0.1,
        size_impact_threshold=10000,
        size_impact_bps_per_10k=2.0
    )
    
    delay_config = DelayConfig(
        market_order_delay=60,
        limit_order_delay=300,
        twap_interval_minutes=15
    )
    
    # Initialize engine with $100k
    engine = PaperTradingEngine(
        initial_capital=100000,
        slippage_config=slippage_config,
        delay_config=delay_config,
        commission_rate=0.001
    )
    
    print(f"\nInitial Capital: ${engine.portfolio.initial_capital:,.2f}")
    
    # Set up simulated prices and volatility
    assets = ["SPY", "GLD", "QQQ", "BTC-USD"]
    prices = {
        "SPY": 450.0,
        "GLD": 180.0,
        "QQQ": 380.0,
        "BTC-USD": 42000.0
    }
    volatilities = {
        "SPY": 0.15,
        "GLD": 0.12,
        "QQQ": 0.20,
        "BTC-USD": 0.60
    }
    
    for symbol, price in prices.items():
        engine.set_price(symbol, price)
    for symbol, vol in volatilities.items():
        engine.set_volatility(symbol, vol)
    
    # Submit orders
    print("\n--- Submitting Orders ---")
    
    order1 = engine.submit_order(
        symbol="SPY",
        side="BUY",
        quantity=100,  # ~$45,000
        order_type="MARKET",
        reason="Momentum signal"
    )
    print(f"Order 1: BUY 100 SPY @ Market")
    print(f"  Expected Slippage: {order1.expected_slippage*10000:.2f} bps")
    print(f"  Status: {order1.status}")
    
    order2 = engine.submit_order(
        symbol="GLD",
        side="BUY",
        quantity=50,  # ~$9,000
        order_type="MARKET",
        reason="Safe haven allocation"
    )
    print(f"\nOrder 2: BUY 50 GLD @ Market")
    print(f"  Expected Slippage: {order2.expected_slippage*10000:.2f} bps")
    
    order3 = engine.submit_order(
        symbol="BTC-USD",
        side="BUY",
        quantity=0.5,  # ~$21,000
        order_type="MARKET",
        reason="Crypto allocation"
    )
    print(f"\nOrder 3: BUY 0.5 BTC-USD @ Market")
    print(f"  Expected Slippage: {order3.expected_slippage*10000:.2f} bps")
    print(f"  (Higher slippage due to BTC volatility)")
    
    # Force execute all orders (for demo - normally would wait for delay)
    print("\n--- Executing Orders ---")
    results = engine.force_execute_all_pending()
    
    for result in results:
        print(f"\n{result.symbol} {result.side}:")
        print(f"  Fill Price: ${result.fill_price:,.2f}")
        print(f"  Fill Quantity: {result.fill_quantity}")
        print(f"  Slippage: {result.slippage_actual*10000:.2f} bps")
        print(f"  Commission: ${result.commission:.2f}")
        print(f"  Status: {result.status}")
    
    # Update NAV
    engine.update_portfolio_nav(prices)
    
    print(f"\n--- Portfolio Summary ---")
    summary = engine.get_portfolio_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    return engine, prices


def demo_performance_monitor(engine, prices):
    """Demo: Real-Time Performance Monitor with IC/KS tracking"""
    print_section("2. Real-Time Performance Monitor Demo")
    
    # Initialize monitor
    config = MonitorConfig(
        sharpe_short_window=20,
        ic_warning_threshold=0.02,
        ks_warning_threshold=0.1
    )
    
    monitor = RealTimePerformanceMonitor(
        portfolio=engine.portfolio,
        config=config
    )
    
    # Simulate trading days with price changes
    print("\n--- Simulating 25 Trading Days ---")
    
    np.random.seed(42)
    for day in range(25):
        # Simulate price changes
        for symbol in prices:
            # Generate random return based on volatility
            if symbol == "BTC-USD":
                daily_vol = 0.60 / np.sqrt(252)
            else:
                daily_vol = 0.15 / np.sqrt(252)
            
            daily_return = np.random.normal(0.0003, daily_vol)  # Small positive drift
            prices[symbol] *= (1 + daily_return)
            engine.set_price(symbol, prices[symbol])
        
        # Update NAV
        engine.update_portfolio_nav(prices)
        
        # Record day
        report = monitor.record_day(
            current_prices=prices,
            daily_trades=np.random.randint(1, 5),
            daily_turnover=np.random.uniform(0.01, 0.05)
        )
        
        if day % 5 == 4:  # Print every 5 days
            print(f"\nDay {day+1}:")
            print(f"  NAV: ${report.nav:,.2f}")
            print(f"  Daily Return: {report.daily_return*100:.2f}%")
            print(f"  Cumulative Return: {report.cumulative_return*100:.2f}%")
            print(f"  Sharpe (20d): {report.sharpe_20d:.3f}")
    
    # Simulate IC tracking
    print("\n--- IC (Information Coefficient) Tracking ---")
    
    for i in range(10):
        # Generate predictions and actuals for 4 assets
        predictions = pd.Series({
            "SPY": np.random.uniform(-0.02, 0.02),
            "GLD": np.random.uniform(-0.02, 0.02),
            "QQQ": np.random.uniform(-0.02, 0.02),
            "BTC-USD": np.random.uniform(-0.05, 0.05)
        })
        
        # Actuals have some correlation with predictions (IC ~ 0.03-0.05)
        actuals = predictions * 0.3 + pd.Series({
            "SPY": np.random.normal(0, 0.01),
            "GLD": np.random.normal(0, 0.01),
            "QQQ": np.random.normal(0, 0.015),
            "BTC-USD": np.random.normal(0, 0.03)
        })
        
        ic = monitor.track_ic(predictions, actuals)
        if not np.isnan(ic):
            print(f"  IC point {i+1}: {ic:.4f}")
    
    ic_trend = monitor.get_ic_trend(days=10)
    print(f"\nIC Trend Summary:")
    print(f"  Mean IC: {ic_trend.get('mean_ic', 'N/A'):.4f}")
    print(f"  Trend: {ic_trend.get('trend', 'N/A')}")
    
    # Simulate KS drift tracking
    print("\n--- KS (Kolmogorov-Smirnov) Drift Tracking ---")
    
    # Set training distribution
    training_features = pd.DataFrame({
        "Momentum_60": np.random.normal(0.05, 0.02, 100),
        "Volatility_20": np.random.normal(0.15, 0.05, 100),
        "RSI_14": np.random.normal(50, 15, 100)
    })
    monitor.set_training_distribution(training_features)
    
    # Track drift
    for i in range(5):
        current_features = pd.DataFrame({
            "Momentum_60": [np.random.normal(0.05, 0.02)],
            "Volatility_20": [np.random.normal(0.15 + i*0.01, 0.05)],  # Slight drift
            "RSI_14": [np.random.normal(50, 15)]
        })
        
        ks_stats = monitor.track_ks_drift(current_features)
        print(f"  KS Drift Check {i+1}: {ks_stats}")
    
    # Final performance summary
    print("\n--- Performance Summary ---")
    perf = monitor.get_performance_summary()
    for key, value in perf.items():
        print(f"  {key}: {value}")
    
    # Show alerts
    alerts = monitor.get_recent_alerts(limit=5)
    if alerts:
        print("\n--- Recent Alerts ---")
        for alert in alerts:
            print(f"  [{alert['level']}] {alert['message']}")
    
    return monitor


def demo_gate_validation(monitor):
    """Demo: Gate Validation System"""
    print_section("3. Gate Validation System Demo")
    
    gates = GateValidationSystem(monitor)
    
    # Simulate gate progress
    print("\n--- Simulating Gate Progress ---")
    
    # Record some trading days
    for _ in range(65):  # Exceed minimum 63 days
        gates.record_trading_day()
    
    # Simulate risk level triggers
    gates.record_risk_level_trigger(1)
    gates.record_risk_level_trigger(2)
    gates.record_risk_level_trigger(3)
    gates.record_risk_level_trigger(4)
    
    # Record uptime
    gates.record_uptime(86300, 86400)  # ~99.9% uptime
    
    # Get progress
    progress = gates.get_gate_progress()
    print("\nGate Progress:")
    print(f"  Trading Days: {progress['trading_days']['current']}/{progress['trading_days']['required']}")
    print(f"  Risk Levels: {progress['risk_levels_triggered']['current']}")
    print(f"  Availability: {progress['system_availability']['current']}")
    
    # Validate gates
    print("\n--- Validating Phase 1+2 Gates ---")
    result = gates.validate_phase_1_2_gates()
    
    print(f"\nOverall Passed: {result.overall_passed}")
    print(f"Pass Rate: {result.get_pass_rate()*100:.0f}%")
    
    print("\nGate Results:")
    for gate_name, gate_result in result.gates.items():
        status = "✓ PASS" if gate_result.get("passed") else "✗ FAIL"
        print(f"  {gate_name}: {status}")
        print(f"    Required: {gate_result.get('required')}")
        print(f"    Actual: {gate_result.get('actual')}")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
    
    # Test deviation report
    print("\n--- Deviation Report (Paper vs Backtest) ---")
    
    # Create mock backtest result
    backtest = BacktestResult(
        start_date="2023-01-01",
        end_date="2024-01-01",
        total_return=0.15,
        annualized_return=0.15,
        sharpe_ratio=1.2,
        max_drawdown=-0.12,
        calmar_ratio=1.25,
        win_rate=0.55,
        num_trades=150
    )
    
    deviation = gates.generate_deviation_report(backtest)
    print(deviation.to_summary())
    
    # Final summary
    print("\n--- Gate Validation Summary ---")
    print(gates.get_summary())
    
    return gates


def demo_integrated_workflow():
    """Demo: Complete integrated paper trading workflow"""
    print_section("4. Integrated Paper Trading Workflow")
    
    print("""
This demo shows how the three components work together:

1. PAPER TRADING ENGINE
   - Submits orders with realistic slippage simulation
   - Delays execution to simulate real market conditions
   - Tracks positions, NAV, and P&L

2. PERFORMANCE MONITOR
   - Records daily performance metrics
   - Tracks IC for model quality assessment
   - Monitors KS drift for concept detection
   - Generates alerts when thresholds breached

3. GATE VALIDATION
   - Tracks progress toward gate requirements
   - Validates each gate criterion
   - Compares paper vs backtest performance

WORKFLOW:
---------
1. Initialize PaperTradingEngine with capital
2. For each trading day:
   - Generate signals from strategy
   - Submit orders via engine
   - Execute pending orders
   - Update portfolio NAV
   - Record day in performance monitor
   - Track IC and KS metrics
3. Periodically:
   - Validate gates
   - Check deviation from backtest
   - Generate reports

GATE REQUIREMENTS (PRD FR-5.3):
-------------------------------
✓ Minimum 63 trading days
✓ Sharpe ratio > 0.5
✓ Max drawdown < 15%
✓ System availability > 99.9%
✓ All risk levels (1-4) triggered at least once
✓ Rolling IC > 0.02 (for ML phases)
""")


def main():
    """Run all Phase 5 demos"""
    print("\n" + "="*60)
    print(" PHASE 5: PAPER TRADING SYSTEM DEMO")
    print(" Based on Tech Design v1.2 Section 4.11")
    print("="*60)
    
    # Run demos
    engine, prices = demo_paper_trading_engine()
    monitor = demo_performance_monitor(engine, prices)
    gates = demo_gate_validation(monitor)
    demo_integrated_workflow()
    
    # Final summary
    print_section("Demo Complete")
    print("""
Phase 5 Paper Trading System Components:
  
  ✓ PaperTradingEngine
    - Order submission with slippage/delay
    - Portfolio tracking
    - Commission calculation
    
  ✓ RealTimePerformanceMonitor
    - Rolling Sharpe (20/60/252 day)
    - IC tracking for model quality
    - KS drift detection
    - Performance alerts
    
  ✓ GateValidationSystem
    - Gate requirement tracking
    - Automated validation
    - Deviation analysis
    
Ready for integration with:
  - Phase 1-4 strategy signals
  - Risk management system
  - Alert/notification channels
""")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
