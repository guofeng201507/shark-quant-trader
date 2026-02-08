"""Main trading system execution script"""

import os
import sys
import time
import argparse
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.provider import DataProvider
from src.factors.calculator import FactorCalculator
from src.signals.generator import SignalGenerator
from src.risk.manager import RiskManager
from src.risk.correlation import CorrelationMonitor
from src.risk.reentry import ReEntryManager
from src.portfolio.manager import PositionManager
from src.execution.order_manager import OrderManager
from src.execution.compliance import ComplianceChecker
from src.state.manager import StateManager
from src.alerts.manager import AlertManager, AlertLevel
from src.backtest.engine import Backtester
from src.stress.tester import StressTester
from src.models.domain import Portfolio
from src.utils.logger import logger
import yaml


class TradingSystem:
    """Main trading system orchestrator"""
    
    def __init__(self, config_path: str = "config/strategy.yaml"):
        """Initialize trading system"""
        logger.info("=" * 80)
        logger.info("SHARK QUANT TRADER - Intelligent Trading System v1.0")
        logger.info("=" * 80)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.data_provider = DataProvider()
        self.factor_calculator = FactorCalculator()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.correlation_monitor = CorrelationMonitor()
        self.reentry_manager = ReEntryManager()
        self.position_manager = PositionManager()
        self.order_manager = OrderManager()
        self.compliance_checker = ComplianceChecker()
        self.state_manager = StateManager()
        self.alert_manager = AlertManager()
        
        # Initialize portfolio
        self.portfolio = self._initialize_portfolio()
        
        logger.info("Trading system initialized successfully")
    
    def _load_config(self, config_path: str) -> dict:
        """Load strategy configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _initialize_portfolio(self) -> Portfolio:
        """Initialize or load portfolio state"""
        
        # Try to load from state manager
        portfolio = self.state_manager.load_latest_portfolio_state()
        
        if portfolio is None:
            # Initialize new portfolio
            initial_capital = float(os.getenv("INITIAL_CAPITAL", "100000"))
            symbols = list(self.config['core_assets'].keys())
            
            portfolio = Portfolio(
                positions={s: 0.0 for s in symbols},
                cash=initial_capital,
                nav=initial_capital,
                peak_nav=initial_capital,
                weights={},
                unrealized_pnl=0.0,
                cost_basis={},
                target_volatility=0.15
            )
            
            logger.info(f"New portfolio initialized: ${initial_capital:,.0f}")
        else:
            logger.info(f"Portfolio loaded from state: NAV ${portfolio.nav:,.0f}")
        
        return portfolio
    
    def run_trading_cycle(self):
        """Execute one trading cycle (daily)"""
        logger.info("Starting trading cycle")
        
        try:
            # 1. Fetch latest data
            symbols = list(self.config['core_assets'].keys())
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            logger.info(f"Fetching data for {len(symbols)} symbols")
            price_data = self.data_provider.fetch(symbols, start_date, end_date)
            
            if not price_data:
                logger.error("Failed to fetch market data")
                return False
            
            # Get current prices
            current_prices = {s: price_data[s].iloc[-1]['Close'] 
                            for s in symbols if not price_data[s].empty}
            
            # Get VIX (if available)
            vix_symbol = "^VIX"
            try:
                vix_data = self.data_provider.fetch([vix_symbol], start_date, end_date)
                vix = vix_data[vix_symbol].iloc[-1]['Close'] if vix_symbol in vix_data else 20.0
            except:
                vix = 20.0  # Default VIX
            
            logger.info(f"Current VIX: {vix:.2f}")
            
            # 2. Calculate factors
            logger.info("Calculating factors")
            factors = self.factor_calculator.calculate(price_data)
            
            # 3. Check correlation
            returns = {}
            for symbol, df in price_data.items():
                returns[symbol] = df['Close'].pct_change()
            
            returns_df = pd.DataFrame(returns).dropna()
            corr_matrix = self.correlation_monitor.get_correlation_matrix(returns_df)
            corr_alerts = self.correlation_monitor.check_correlation_breach(corr_matrix)
            
            for alert in corr_alerts:
                self.alert_manager.alert_correlation_breach(
                    alert.avg_correlation or 0, 
                    0.5, 
                    alert.pairs
                )
            
            # 4. Generate signals
            logger.info("Generating trading signals")
            signals = self.signal_generator.generate(factors, self.portfolio.positions, vix)
            
            logger.info(f"Generated {len(signals)} signals")
            for signal in signals:
                logger.info(f"  {signal.symbol}: {signal.signal.value} "
                          f"(confidence: {signal.confidence:.2f})")
            
            # 5. Risk assessment
            logger.info("Assessing portfolio risk")
            risk_assessment = self.risk_manager.check(self.portfolio)
            
            if risk_assessment.level > 0:
                logger.warning(f"Risk Level {risk_assessment.level}: {risk_assessment.violations}")
                self.alert_manager.alert_risk_level_change(
                    0, risk_assessment.level, risk_assessment.portfolio_drawdown
                )
            
            # 6. Calculate target positions
            logger.info("Calculating target positions")
            target_positions = self.position_manager.calculate_target_positions(
                signals, self.portfolio, current_prices
            )
            
            # 7. Check if rebalance needed
            current_weights = self.position_manager.calculate_weights(
                self.portfolio.positions, current_prices, self.portfolio.nav
            )
            target_weights = self.position_manager.calculate_weights(
                target_positions, current_prices, self.portfolio.nav
            )
            
            needs_rebalance = self.position_manager.needs_rebalance(
                current_weights, target_weights
            )
            
            if not needs_rebalance:
                logger.info("No rebalance needed")
                return True
            
            # 8. Create orders
            logger.info("Creating orders")
            orders = self.order_manager.create_orders(
                self.portfolio.positions, target_positions, current_prices, self.portfolio
            )
            
            logger.info(f"Created {len(orders)} orders")
            
            # 9. Pre-trade compliance checks
            compliant_orders = []
            for order in orders:
                is_compliant, reason = self.compliance_checker.check_pre_trade(
                    order, self.portfolio, current_prices
                )
                
                if is_compliant:
                    compliant_orders.append(order)
                else:
                    logger.warning(f"Order rejected by compliance: {reason}")
            
            # 10. Submit orders (simulated for Phase 1)
            logger.info(f"Submitting {len(compliant_orders)} compliant orders")
            for order in compliant_orders:
                success = self.order_manager.submit_order(order)
                if success:
                    # Simulate immediate fill
                    self.order_manager.check_order_status(order)
                    # Save order
                    self.state_manager.save_order(order)
            
            # 11. Update portfolio state
            self.portfolio.nav = self.position_manager.calculate_portfolio_nav(
                self.portfolio.positions, self.portfolio.cash, current_prices
            )
            
            # Update peak NAV
            if self.portfolio.nav > self.portfolio.peak_nav:
                self.portfolio.peak_nav = self.portfolio.nav
            
            # 12. Save state
            self.state_manager.save_portfolio_state(self.portfolio)
            
            logger.info(f"Trading cycle complete: NAV ${self.portfolio.nav:,.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Trading cycle failed: {e}", exc_info=True)
            self.alert_manager.send_alert(
                AlertLevel.CRITICAL,
                "Trading Cycle Error",
                f"An error occurred: {str(e)}"
            )
            return False
    
    def run_backtest(self, start_date: str, end_date: str):
        """Run backtest"""
        logger.info("=" * 80)
        logger.info("BACKTEST MODE")
        logger.info("=" * 80)
        
        symbols = list(self.config['core_assets'].keys())
        initial_capital = float(os.getenv("INITIAL_CAPITAL", "100000"))
        
        backtester = Backtester(initial_capital)
        result = backtester.run(symbols, start_date, end_date)
        
        if result:
            logger.info("=" * 80)
            logger.info("BACKTEST RESULTS")
            logger.info("=" * 80)
            logger.info(f"Period: {result.start_date} to {result.end_date}")
            logger.info(f"Total Return: {result.total_return:.2%}")
            logger.info(f"Annualized Return: {result.annualized_return:.2%}")
            logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
            logger.info(f"Max Drawdown: {result.max_drawdown:.2%}")
            logger.info(f"Calmar Ratio: {result.calmar_ratio:.2f}")
            logger.info(f"Win Rate: {result.win_rate:.2%}")
            logger.info(f"Number of Trades: {result.num_trades}")
            logger.info("=" * 80)
    
    def run_stress_test(self):
        """Run stress tests"""
        logger.info("=" * 80)
        logger.info("STRESS TEST MODE")
        logger.info("=" * 80)
        
        # Get current prices
        symbols = list(self.config['core_assets'].keys())
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        price_data = self.data_provider.fetch(symbols, start_date, end_date)
        current_prices = {s: price_data[s].iloc[-1]['Close'] 
                         for s in symbols if not price_data[s].empty}
        
        # Run stress tests
        tester = StressTester()
        reports = tester.run_all_scenarios(self.portfolio, current_prices)
        
        logger.info("=" * 80)
        logger.info("STRESS TEST RESULTS")
        logger.info("=" * 80)
        
        for report in reports:
            logger.info(f"\n{report.scenario}")
            logger.info(f"  Stressed NAV: ${report.stressed_nav:,.2f}")
            logger.info(f"  Drawdown: {report.drawdown:.2%}")
            logger.info(f"  Risk Level: {report.risk_level}")
            logger.info(f"  Survived: {report.survived}")
        
        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Shark Quant Trader")
    parser.add_argument("--mode", choices=["live", "backtest", "stress"], 
                       default="live", help="Execution mode")
    parser.add_argument("--start-date", help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--interval", type=int, default=86400,
                       help="Trading interval in seconds (default: 86400 = daily)")
    
    args = parser.parse_args()
    
    # Initialize system
    system = TradingSystem()
    
    if args.mode == "backtest":
        if not args.start_date or not args.end_date:
            logger.error("Backtest mode requires --start-date and --end-date")
            return
        
        system.run_backtest(args.start_date, args.end_date)
    
    elif args.mode == "stress":
        system.run_stress_test()
    
    else:  # live mode
        logger.info("Starting live trading mode")
        logger.info(f"Trading interval: {args.interval} seconds")
        
        while True:
            system.run_trading_cycle()
            
            logger.info(f"Waiting {args.interval} seconds until next cycle")
            time.sleep(args.interval)


if __name__ == "__main__":
    main()