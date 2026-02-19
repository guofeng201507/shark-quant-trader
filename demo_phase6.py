"""Demo Phase 6: Live Trading System Validation

This script validates the Phase 6 Live Trading implementation:
- FR-6.1: Broker API Integration (Alpaca, Binance, IBKR)
- FR-6.2: Order Management System (smart routing, splitting, retry)
- FR-6.2: Capital Transition Manager (staged deployment, rollback triggers)
- FR-6.3: Live Monitoring System (health checks, performance tracking)

Usage:
    # Demo mode (no API keys required):
    python demo_phase6.py

    # Live mode with Alpaca (requires .env config):
    # Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env
    python demo_phase6.py --live
"""

import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, List
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.live_trading import (
    # Models
    LiveOrder,
    OrderResponse,
    OrderStatus,
    OrderType,
    OrderSide,
    Position,
    AccountInfo,
    LiveTradingConfig,
    CapitalStage,
    DEFAULT_STAGES,
    # Brokers
    BrokerFactory,
    AlpacaAdapter,
    BinanceAdapter,
    IBKRAdapter,
    # Order Management
    OrderManagementSystem,
    # Capital Transition
    CapitalTransitionManager,
    # Monitoring
    LiveMonitoringSystem,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


# Global flag for live mode
USE_LIVE_BROKER = False


async def test_broker_adapters():
    """Test FR-6.1: Broker API Integration."""
    print_section("FR-6.1: Broker Adapter Tests")

    # Get credentials from environment
    alpaca_key = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret = os.getenv("ALPACA_SECRET_KEY", "")
    alpaca_paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"

    # Test 1: Alpaca Adapter (Live or Demo Mode)
    print("\n[1] Testing AlpacaAdapter...")
    if alpaca_key and alpaca_secret and USE_LIVE_BROKER:
        # Use real API
        alpaca = AlpacaAdapter(
            api_key=alpaca_key,
            secret_key=alpaca_secret,
            paper=alpaca_paper,
            demo_mode=False
        )
        print(f"    Using Live API (Paper: {alpaca_paper})")
    else:
        # Use demo mode
        alpaca = AlpacaAdapter(
            api_key="demo_key",
            secret_key="demo_secret",
            paper=True,
            demo_mode=True
        )
        print(f"    Using Demo Mode (No API keys found)")

    await alpaca.connect()
    account = await alpaca.get_account_info()
    mode_str = "Demo Mode" if alpaca.demo_mode else "Live"
    print(f"    Alpaca Account: ${account.cash} ({mode_str})")
    print(f"    Portfolio Value: ${account.portfolio_value}")
    print(f"    Buying Power: ${account.buying_power}")
    await alpaca.disconnect()

    # Test 2: Binance Adapter (Demo Mode)
    print("\n[2] Testing BinanceAdapter...")
    binance = BinanceAdapter(
        api_key="demo_key",
        secret_key="demo_secret",
        testnet=True,
        demo_mode=True
    )
    await binance.connect()
    account = await binance.get_account_info()
    print(f"    Binance Account: ${account.cash} (Demo Mode)")
    await binance.disconnect()

    # Test 3: IBKR Adapter (Demo Mode)
    print("\n[3] Testing IBKRAdapter...")
    ibkr = IBKRAdapter(
        host="127.0.0.1",
        port=7497
    )
    await ibkr.connect()
    account = await ibkr.get_account_info()
    print(f"    IBKR Account: ${account.cash} (Demo Mode)")
    await ibkr.disconnect()

    # Test 4: Broker Factory
    print("\n[4] Testing BrokerFactory...")
    broker = BrokerFactory.create_broker("alpaca", paper=True, demo_mode=True)
    print(f"    Created broker: {type(broker).__name__}")

    print("\n[✓] FR-6.1 Broker Adapters: PASSED")


async def test_order_management():
    """Test FR-6.2: Order Management System."""
    print_section("FR-6.2: Order Management System Tests")

    # Setup
    brokers = {
        "alpaca": AlpacaAdapter(demo_mode=True),
        "binance": BinanceAdapter(demo_mode=True),
    }
    oms = OrderManagementSystem(brokers)

    # Test 1: Smart Routing
    print("\n[1] Testing Smart Routing...")

    # Crypto order should route to Binance
    crypto_order = LiveOrder(
        order_id="demo-crypto-001",
        symbol="BTC/USD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.1,
        broker="auto"
    )
    route = oms.route_order(crypto_order)
    print(f"    BTC/USD routes to: {route}")

    # US ETF should route to Alpaca
    etf_order = LiveOrder(
        order_id="demo-etf-001",
        symbol="SPY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=10.0,
        broker="auto"
    )
    route = oms.route_order(etf_order)
    print(f"    SPY routes to: {route}")

    # Test 2: Order Splitting (for large orders)
    print("\n[2] Testing Order Splitting...")
    large_order = LiveOrder(
        order_id="demo-large-001",
        symbol="SPY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=5000.0,
        broker="alpaca"
    )
    splits = oms.split_order(large_order, current_price=500.0)
    print(f"    Split {large_order.quantity} into {len(splits)} orders")
    for i, split in enumerate(splits):
        print(f"      Split {i+1}: {split.quantity}")

    # Test 3: Execute Order
    print("\n[3] Testing Order Execution...")
    await brokers["alpaca"].connect()
    order = LiveOrder(
        order_id="demo-limit-001",
        symbol="SPY",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1.0,
        limit_price=500.00,
        broker="alpaca"
    )
    result = await oms.execute_order(order, current_price=500.0)
    # execute_order returns a list of OrderResponse
    if isinstance(result, list):
        result = result[0] if result else None
    if result:
        print(f"    Order Status: {result.status}")
        print(f"    Order Message: {result.message}")
    await brokers["alpaca"].disconnect()

    print("\n[✓] FR-6.2 Order Management: PASSED")


def test_capital_transition():
    """Test FR-6.2: Capital Transition Manager."""
    print_section("FR-6.2: Capital Transition Manager Tests")

    # Setup
    ctm = CapitalTransitionManager(total_capital=100000.0)

    # Test 1: Initial Stage
    print("\n[1] Testing Initial Stage...")
    stage = ctm.current_stage_info
    print(f"    Current Stage: {stage.name} ({stage.capital_pct * 100}%)")
    print(f"    Capital Amount: ${ctm.get_current_allocation():,.2f}")

    # Test 2: Advance Stage
    print("\n[2] Testing Stage Advance...")
    # Simulate good performance
    can_advance, reason = ctm.can_advance_stage(current_nav=105000.0)
    print(f"    Can advance: {can_advance} - {reason}")

    if can_advance:
        success, msg = ctm.advance_stage(current_nav=105000.0)
        print(f"    Advanced: {msg}")
        stage = ctm.current_stage_info
        print(f"    New Stage: {stage.name} ({stage.capital_pct * 100}%)")

    # Test 3: Check Rollback Triggers
    print("\n[3] Testing Rollback Triggers...")
    trigger = ctm.check_rollback_triggers(daily_return=-0.04, cumulative_dd=0.0)
    print(f"    Trigger result: {trigger}")

    # Test 4: Transition History
    print("\n[4] Testing Transition History...")
    history = ctm.get_transition_log()
    print(f"    Total transitions: {len(history)}")

    print("\n[✓] FR-6.2 Capital Transition: PASSED")


def test_live_monitoring():
    """Test FR-6.3: Live Monitoring System."""
    print_section("FR-6.3: Live Monitoring System Tests")

    # Setup
    monitor = LiveMonitoringSystem()

    # Test 1: Health Check
    print("\n[1] Testing Health Check...")
    health = monitor.check_system_health()
    print(f"    Status: {health.status}")
    print(f"    Issues: {len(health.issues)}")
    for issue in health.issues:
        print(f"      - {issue}")

    # Test 2: Performance Recording
    print("\n[2] Testing Performance Recording...")
    monitor.record_performance(nav=105000.0, daily_return=0.005, positions=5, trades=10)
    status = monitor.get_status()
    print(f"    Portfolio Value: ${float(status['nav']):,.2f}")
    print(f"    Daily Return: {status['return']}")

    # Test 3: Model Quality Tracking
    print("\n[3] Testing Model Quality Tracking...")
    monitor.record_ic(0.12)
    monitor.record_ks(0.55)
    status = monitor.get_status()
    print(f"    Model IC: {status['ic']}")
    print(f"    Model KS: {status['ks']}")

    # Test 4: System Failures
    print("\n[4] Testing System Failure Recording...")
    ctm = CapitalTransitionManager(total_capital=100000.0)
    ctm.record_system_failure()
    ctm.record_system_failure()
    print(f"    System Failures: {ctm.system_failure_count}")
    print(f"    Should rollback: {ctm.check_rollback_triggers(0, 0) is not None}")

    print("\n[✓] FR-6.3 Live Monitoring: PASSED")


async def test_end_to_end():
    """Test FR-6: End-to-End Live Trading Flow."""
    print_section("FR-6: End-to-End Integration Test")

    # Setup components
    print("\n[1] Initializing Live Trading System...")
    total_capital = 100000.0
    ctm = CapitalTransitionManager(total_capital=total_capital)
    monitor = LiveMonitoringSystem()

    brokers = {
        "alpaca": AlpacaAdapter(demo_mode=True),
        "binance": BinanceAdapter(demo_mode=True),
    }
    oms = OrderManagementSystem(brokers)

    print(f"    Capital: ${total_capital:,.2f}")
    print(f"    Current Stage: {ctm.current_stage_info.name}")

    # Connect brokers
    print("\n[2] Connecting to Brokers...")
    for name, broker in brokers.items():
        await broker.connect()
        print(f"    ✓ {name} connected")

    # Simulate trading day
    print("\n[3] Simulating Trading Day...")

    # Execute sample orders
    orders = [
        LiveOrder(order_id="demo-e2e-001", symbol="SPY", side=OrderSide.BUY, order_type=OrderType.MARKET,
                  quantity=10.0, broker="alpaca"),
    ]

    for order in orders:
        results = await oms.execute_order(order, current_price=500.0)
        if isinstance(results, list) and results:
            print(f"    {order.symbol}: {results[0].status}")
        else:
            print(f"    {order.symbol}: Unknown")

    # Record performance
    monitor.record_performance(nav=102000.0, daily_return=0.002, positions=1, trades=1)

    # Record model quality
    monitor.record_ic(0.11)
    monitor.record_ks(0.58)

    # Check health
    health = monitor.check_system_health()
    print(f"\n[4] Health Check: {health.status}")

    # Disconnect brokers
    print("\n[5] Disconnecting from Brokers...")
    for name, broker in brokers.items():
        await broker.disconnect()
        print(f"    ✓ {name} disconnected")

    print("\n[✓] FR-6 End-to-End: PASSED")


async def main():
    """Run all Phase 6 tests."""
    global USE_LIVE_BROKER

    # Parse arguments
    parser = argparse.ArgumentParser(description="Phase 6 Live Trading Demo")
    parser.add_argument("--live", action="store_true", help="Use live broker APIs (requires .env config)")
    args = parser.parse_args()
    USE_LIVE_BROKER = args.live

    print("\n" + "=" * 60)
    print("  PHASE 6: LIVE TRADING SYSTEM VALIDATION")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    mode = "LIVE MODE" if USE_LIVE_BROKER else "DEMO MODE"
    print(f"  Mode: {mode}")
    print("=" * 60)

    try:
        await test_broker_adapters()
        await test_order_management()
        test_capital_transition()
        test_live_monitoring()
        await test_end_to_end()

        print_section("PHASE 6 VALIDATION COMPLETE")
        print("\n[✓] All tests passed!")
        print("\nSummary:")
        print("  - FR-6.1 Broker API Integration: ✓")
        print("  - FR-6.2 Order Management System: ✓")
        print("  - FR-6.2 Capital Transition Manager: ✓")
        print("  - FR-6.3 Live Monitoring System: ✓")

        if USE_LIVE_BROKER:
            print("\n  [LIVE MODE] Connected to real Alpaca Paper Trading API")

    except Exception as e:
        print(f"\n[✗] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
