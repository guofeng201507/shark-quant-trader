"""Stress Tester - Crisis scenarios - Tech Design v1.1 Section 4.10"""

import pandas as pd
import numpy as np
from typing import Dict, List
from ..models.domain import Portfolio, StressTestReport
from ..risk.manager import RiskManager
from ..utils.logger import logger


class StressTester:
    """Stress testing with historical crisis scenarios"""
    
    # Crisis scenarios from Tech Design Section 4.10
    SCENARIOS = {
        "covid_crash_2020": {
            "name": "COVID-19 Crash (Mar 2020)",
            "spy_shock": -0.34,      # S&P 500 down 34%
            "gld_shock": 0.05,       # Gold up 5%
            "btc_shock": -0.50,      # Bitcoin down 50%
            "vix_spike": 82.69       # VIX spike to 82.69
        },
        "gfc_2008": {
            "name": "Global Financial Crisis (2008)",
            "spy_shock": -0.57,      # S&P 500 down 57%
            "gld_shock": 0.25,       # Gold up 25%
            "btc_shock": 0.0,        # BTC didn't exist
            "vix_spike": 80.0        # VIX spike to 80
        },
        "tech_bubble_2000": {
            "name": "Dot-com Bubble Burst (2000-2002)",
            "spy_shock": -0.49,      # S&P 500 down 49%
            "qqq_shock": -0.83,      # NASDAQ down 83%
            "gld_shock": 0.12,       # Gold up 12%
            "vix_spike": 45.0
        },
        "flash_crash_2010": {
            "name": "Flash Crash (May 2010)",
            "spy_shock": -0.09,      # Intraday down 9%
            "gld_shock": 0.01,
            "vix_spike": 40.0
        },
        "crypto_winter_2022": {
            "name": "Crypto Winter (2022)",
            "spy_shock": -0.19,
            "btc_shock": -0.64,      # Bitcoin down 64%
            "vix_spike": 35.0
        }
    }
    
    def __init__(self):
        """Initialize stress tester"""
        self.risk_manager = RiskManager()
        logger.info("StressTester initialized")
    
    def run_scenario(self, portfolio: Portfolio, scenario_name: str,
                    current_prices: Dict[str, float]) -> StressTestReport:
        """
        Run single stress test scenario.
        
        Args:
            portfolio: Current portfolio state
            scenario_name: Name of scenario from SCENARIOS
            current_prices: Current market prices
            
        Returns:
            StressTestReport with results
        """
        if scenario_name not in self.SCENARIOS:
            logger.error(f"Unknown scenario: {scenario_name}")
            return None
        
        scenario = self.SCENARIOS[scenario_name]
        logger.info(f"Running stress test: {scenario['name']}")
        
        # Apply shocks to prices
        shocked_prices = self._apply_shocks(current_prices, scenario)
        
        # Calculate stressed portfolio value
        stressed_nav = self._calculate_stressed_nav(
            portfolio, shocked_prices
        )
        
        # Calculate drawdown
        drawdown = (portfolio.nav - stressed_nav) / portfolio.nav
        
        # Check risk level after shock
        stressed_portfolio = Portfolio(
            positions=portfolio.positions.copy(),
            cash=portfolio.cash,
            nav=stressed_nav,
            peak_nav=portfolio.peak_nav,
            weights=portfolio.weights.copy(),
            unrealized_pnl=stressed_nav - portfolio.nav,
            cost_basis=portfolio.cost_basis.copy()
        )
        
        risk_level = self.risk_manager.assess_risk_level(stressed_portfolio)
        
        # Determine survival
        survived = drawdown < 0.50  # Survive if drawdown < 50%
        
        report = StressTestReport(
            scenario=scenario['name'],
            stressed_nav=stressed_nav,
            drawdown=drawdown,
            risk_level=risk_level,
            survived=survived
        )
        
        logger.info(f"Stress test complete: Drawdown {drawdown:.2%}, "
                   f"Risk Level {risk_level}, Survived: {survived}")
        
        return report
    
    def run_all_scenarios(self, portfolio: Portfolio,
                         current_prices: Dict[str, float]) -> List[StressTestReport]:
        """
        Run all stress test scenarios.
        
        Args:
            portfolio: Current portfolio state
            current_prices: Current market prices
            
        Returns:
            List of StressTestReport objects
        """
        logger.info("Running all stress test scenarios")
        
        reports = []
        for scenario_name in self.SCENARIOS.keys():
            report = self.run_scenario(portfolio, scenario_name, current_prices)
            if report:
                reports.append(report)
        
        # Summary statistics
        avg_drawdown = np.mean([r.drawdown for r in reports])
        max_drawdown = max([r.drawdown for r in reports])
        survival_rate = sum([1 for r in reports if r.survived]) / len(reports)
        
        logger.info(f"Stress test summary: Avg DD {avg_drawdown:.2%}, "
                   f"Max DD {max_drawdown:.2%}, Survival Rate {survival_rate:.0%}")
        
        return reports
    
    def _apply_shocks(self, prices: Dict[str, float],
                     scenario: Dict) -> Dict[str, float]:
        """Apply scenario shocks to current prices"""
        
        shocked_prices = prices.copy()
        
        # Map shocks to symbols
        shock_mapping = {
            "SPY": scenario.get("spy_shock", 0),
            "QQQ": scenario.get("qqq_shock", scenario.get("spy_shock", 0)),  # Fallback to SPY
            "GLD": scenario.get("gld_shock", 0),
            "BTC-USD": scenario.get("btc_shock", 0),
            "SLV": scenario.get("gld_shock", 0) * 1.2,  # Silver amplifies gold moves
            "TLT": scenario.get("spy_shock", 0) * -0.3,  # Bonds inverse to stocks
            "XLK": scenario.get("qqq_shock", scenario.get("spy_shock", 0)) * 1.2,  # Tech amplifies
            "XLF": scenario.get("spy_shock", 0) * 1.3,  # Financials amplify
            "XLE": scenario.get("spy_shock", 0) * 1.5,  # Energy amplifies
            "XLV": scenario.get("spy_shock", 0) * 0.7,  # Healthcare defensive
            "EFA": scenario.get("spy_shock", 0) * 0.9,  # International follows US
            "EEM": scenario.get("spy_shock", 0) * 1.2,  # EM amplifies
        }
        
        # Apply shocks
        for symbol, price in prices.items():
            shock = shock_mapping.get(symbol, 0)
            shocked_prices[symbol] = price * (1 + shock)
        
        return shocked_prices
    
    def _calculate_stressed_nav(self, portfolio: Portfolio,
                                shocked_prices: Dict[str, float]) -> float:
        """Calculate portfolio NAV under stress scenario"""
        
        stressed_value = portfolio.cash
        
        for symbol, quantity in portfolio.positions.items():
            if symbol in shocked_prices:
                stressed_value += quantity * shocked_prices[symbol]
        
        return stressed_value
    
    def run_monte_carlo(self, portfolio: Portfolio,
                       current_prices: Dict[str, float],
                       num_simulations: int = 1000) -> Dict:
        """
        Run Monte Carlo stress simulation.
        
        Args:
            portfolio: Current portfolio state
            current_prices: Current market prices
            num_simulations: Number of random scenarios
            
        Returns:
            Dict with simulation statistics
        """
        logger.info(f"Running Monte Carlo simulation: {num_simulations} scenarios")
        
        # Historical volatilities (annualized)
        volatilities = {
            "SPY": 0.18,
            "QQQ": 0.22,
            "GLD": 0.15,
            "BTC-USD": 0.80,
            "SLV": 0.25,
            "TLT": 0.12,
            "XLK": 0.25,
            "XLF": 0.28,
            "XLE": 0.35,
            "XLV": 0.16
        }
        
        # Correlation matrix (simplified)
        # In production, use historical correlation matrix
        correlation = 0.6  # Assume 60% correlation across equities
        
        drawdowns = []
        
        for _ in range(num_simulations):
            # Generate random shocks
            shocked_prices = {}
            
            for symbol, price in current_prices.items():
                vol = volatilities.get(symbol, 0.20)
                # Daily shock (1-day 95% move)
                shock = np.random.normal(0, vol / np.sqrt(252) * 2)
                shocked_prices[symbol] = price * (1 + shock)
            
            # Calculate stressed NAV
            stressed_nav = self._calculate_stressed_nav(
                portfolio, shocked_prices
            )
            
            # Calculate drawdown
            drawdown = (portfolio.nav - stressed_nav) / portfolio.nav
            drawdowns.append(drawdown)
        
        # Calculate VaR and CVaR
        drawdowns_sorted = sorted(drawdowns, reverse=True)
        
        var_95 = np.percentile(drawdowns, 95)  # 95% VaR
        var_99 = np.percentile(drawdowns, 99)  # 99% VaR
        
        # CVaR (Expected Shortfall): average of worst 5%
        worst_5pct = drawdowns_sorted[:int(num_simulations * 0.05)]
        cvar_95 = np.mean(worst_5pct)
        
        results = {
            "num_simulations": num_simulations,
            "mean_drawdown": np.mean(drawdowns),
            "std_drawdown": np.std(drawdowns),
            "max_drawdown": max(drawdowns),
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95
        }
        
        logger.info(f"Monte Carlo complete: VaR 95% = {var_95:.2%}, "
                   f"CVaR 95% = {cvar_95:.2%}")
        
        return results