"""Backtest Engine - Tech Design v1.1 Section 10"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..models.domain import Portfolio, BacktestResult
from ..data.provider import DataProvider
from ..factors.calculator import FactorCalculator
from ..signals.generator import SignalGenerator
from ..risk.manager import RiskManager
from ..portfolio.manager import PositionManager
from ..utils.logger import logger


class Backtester:
    """Backtesting engine with performance metrics"""
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting portfolio value
        """
        self.initial_capital = initial_capital
        self.data_provider = DataProvider()
        self.factor_calculator = FactorCalculator()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.position_manager = PositionManager()
        
        logger.info(f"Backtester initialized with ${initial_capital:,.0f}")
    
    def run(self, symbols: List[str], start_date: str, end_date: str,
            vix_data: pd.Series = None) -> BacktestResult:
        """
        Run backtest simulation.
        
        Args:
            symbols: List of asset symbols to trade
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            vix_data: Optional VIX data series
            
        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Starting backtest: {start_date} to {end_date}")
        
        # Fetch historical data
        price_data = self.data_provider.fetch(symbols, start_date, end_date)
        
        if not price_data:
            logger.error("Failed to fetch historical data")
            return None
        
        # Calculate factors
        factors = self.factor_calculator.calculate(price_data)
        
        # Initialize portfolio
        portfolio = Portfolio(
            positions={s: 0.0 for s in symbols},
            cash=self.initial_capital,
            nav=self.initial_capital,
            peak_nav=self.initial_capital,
            weights={},
            unrealized_pnl=0.0,
            cost_basis={}
        )
        
        # Track history
        nav_history = []
        trades = []
        
        # Get date range from first symbol's data
        first_symbol = symbols[0]
        dates = price_data[first_symbol].index
        
        # Run simulation day by day
        for date in dates:
            # Get current prices
            prices = {s: price_data[s].loc[date, 'Close'] 
                     for s in symbols if date in price_data[s].index}
            
            # Get VIX value if available
            vix = vix_data.loc[date] if vix_data is not None and date in vix_data.index else None
            
            # Get factors up to current date
            current_factors = {
                s: factors[s].loc[:date] 
                for s in symbols if date in factors[s].index
            }
            
            # Generate signals
            signals = self.signal_generator.generate(
                current_factors, 
                portfolio.positions,
                vix
            )
            
            # Check risk
            risk_assessment = self.risk_manager.check(portfolio)
            
            # Calculate target positions
            target_positions = self.position_manager.calculate_target_positions(
                signals, portfolio, prices
            )
            
            # Execute trades (simplified for backtest)
            for symbol, target_qty in target_positions.items():
                current_qty = portfolio.positions.get(symbol, 0.0)
                trade_qty = target_qty - current_qty
                
                if abs(trade_qty) < 1e-6:
                    continue
                
                # Calculate trade cost
                price = prices.get(symbol, 0)
                if price == 0:
                    continue
                
                trade_value = abs(trade_qty) * price
                
                # Apply slippage
                slippage = 0.001 if symbol == "BTC-USD" else 0.0005
                cost = trade_value * slippage
                
                # Execute trade
                if trade_qty > 0:  # Buy
                    total_cost = trade_value + cost
                    if portfolio.cash >= total_cost:
                        portfolio.positions[symbol] = target_qty
                        portfolio.cash -= total_cost
                        portfolio.cost_basis[symbol] = price
                        trades.append({
                            'date': date,
                            'symbol': symbol,
                            'side': 'BUY',
                            'quantity': trade_qty,
                            'price': price
                        })
                else:  # Sell
                    portfolio.positions[symbol] = target_qty
                    portfolio.cash += trade_value - cost
                    trades.append({
                        'date': date,
                        'symbol': symbol,
                        'side': 'SELL',
                        'quantity': abs(trade_qty),
                        'price': price
                    })
            
            # Update portfolio NAV
            portfolio.nav = self.position_manager.calculate_portfolio_nav(
                portfolio.positions, portfolio.cash, prices
            )
            
            # Update peak NAV
            if portfolio.nav > portfolio.peak_nav:
                portfolio.peak_nav = portfolio.nav
            
            # Record NAV
            nav_history.append({
                'date': date,
                'nav': portfolio.nav,
                'cash': portfolio.cash
            })
        
        # Calculate performance metrics
        result = self._calculate_metrics(nav_history, trades)
        
        logger.info(f"Backtest complete: Total Return {result.total_return:.2%}, "
                   f"Sharpe {result.sharpe_ratio:.2f}, MaxDD {result.max_drawdown:.2%}")
        
        return result
    
    def _calculate_metrics(self, nav_history: List[Dict],
                          trades: List[Dict]) -> BacktestResult:
        """Calculate backtest performance metrics"""
        
        # Convert to DataFrame
        nav_df = pd.DataFrame(nav_history)
        nav_df.set_index('date', inplace=True)
        
        # Calculate returns
        nav_df['returns'] = nav_df['nav'].pct_change()
        
        # Total return
        total_return = (nav_df['nav'].iloc[-1] / nav_df['nav'].iloc[0]) - 1
        
        # Annualized return (assuming 252 trading days)
        days = len(nav_df)
        years = days / 252
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Volatility (annualized)
        daily_vol = nav_df['returns'].std()
        annualized_vol = daily_vol * np.sqrt(252)
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = annualized_return / annualized_vol if annualized_vol > 0 else 0
        
        # Maximum drawdown
        nav_df['cummax'] = nav_df['nav'].cummax()
        nav_df['drawdown'] = (nav_df['nav'] - nav_df['cummax']) / nav_df['cummax']
        max_drawdown = nav_df['drawdown'].min()
        
        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win rate
        if len(trades) > 0:
            # Group trades by round-trip (simplified)
            # For now, just count profitable days
            winning_days = (nav_df['returns'] > 0).sum()
            total_days = (nav_df['returns'] != 0).sum()
            win_rate = winning_days / total_days if total_days > 0 else 0
        else:
            win_rate = 0
        
        # Number of trades
        num_trades = len(trades)
        
        result = BacktestResult(
            start_date=nav_df.index[0].strftime('%Y-%m-%d'),
            end_date=nav_df.index[-1].strftime('%Y-%m-%d'),
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            num_trades=num_trades
        )
        
        return result