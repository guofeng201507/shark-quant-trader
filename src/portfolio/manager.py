"""Position Manager with risk parity optimization"""

import pandas as pd
import numpy as np
from typing import Dict, List
from ..models.domain import TradeSignal, Portfolio
from ..utils.logger import logger


class PositionManager:
    """Position sizing and portfolio optimization"""
    
    # Portfolio constraints from Tech Design Section 3.5
    CONSTRAINTS = {
        "min_trade_amount": 100.0,      # Minimum $100 per trade
        "min_rebalance_threshold": 0.02, # 2% weight change triggers rebalance
        "cash_buffer": 0.05,            # Always keep 5% cash
        "max_portfolio_leverage": 1.5,  # Maximum 1.5x leverage
        "max_daily_trades": 5,
        "max_daily_turnover": 0.30
    }
    
    def __init__(self):
        """Initialize position manager"""
        self.daily_trades = 0
        self.daily_turnover = 0.0
        logger.info("PositionManager initialized")
    
    def calculate_target_positions(self, signals: List[TradeSignal],
                                   portfolio: Portfolio,
                                   prices: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate target position quantities from signals.
        
        Args:
            signals: List of trade signals
            portfolio: Current portfolio state
            prices: Current prices for each symbol
            
        Returns:
            Dict mapping symbol -> target quantity
        """
        target_weights = self._calculate_target_weights(signals, portfolio)
        target_positions = self._weights_to_quantities(
            target_weights, portfolio.nav, prices
        )
        
        # Apply constraints
        target_positions = self._apply_constraints(
            target_positions, portfolio, prices
        )
        
        return target_positions
    
    def _calculate_target_weights(self, signals: List[TradeSignal],
                                  portfolio: Portfolio) -> Dict[str, float]:
        """
        Calculate target portfolio weights from signals.
        Implements risk parity principles.
        """
        target_weights = {}
        total_weight = 0.0
        
        # Extract weights from signals
        for signal in signals:
            weight = signal.target_weight * signal.confidence
            target_weights[signal.symbol] = weight
            total_weight += weight
        
        # Normalize weights to sum to (1 - cash_buffer)
        max_invested = 1.0 - self.CONSTRAINTS["cash_buffer"]
        
        if total_weight > 0:
            scale_factor = min(1.0, max_invested / total_weight)
            target_weights = {
                symbol: weight * scale_factor 
                for symbol, weight in target_weights.items()
            }
        
        logger.debug(f"Target weights: {target_weights}")
        return target_weights
    
    def _weights_to_quantities(self, weights: Dict[str, float],
                               nav: float,
                               prices: Dict[str, float]) -> Dict[str, int]:
        """
        Convert portfolio weights to share quantities.
        
        Args:
            weights: Target weights for each symbol
            nav: Portfolio net asset value
            prices: Current prices
            
        Returns:
            Dict mapping symbol -> quantity
        """
        quantities = {}
        
        for symbol, weight in weights.items():
            if symbol not in prices:
                logger.warning(f"No price available for {symbol}, skipping")
                continue
            
            target_value = weight * nav
            price = prices[symbol]
            
            if price <= 0:
                logger.warning(f"Invalid price for {symbol}: {price}")
                continue
            
            # Calculate quantity
            quantity = target_value / price
            
            # Round to appropriate precision
            if symbol == "BTC-USD":
                quantity = round(quantity, 4)  # 4 decimal places for BTC
            else:
                quantity = int(quantity)  # Whole shares for stocks/ETFs
            
            quantities[symbol] = quantity
        
        return quantities
    
    def _apply_constraints(self, target_positions: Dict[str, float],
                          current_portfolio: Portfolio,
                          prices: Dict[str, float]) -> Dict[str, float]:
        """Apply portfolio constraints"""
        
        # Check minimum trade amount
        filtered_positions = {}
        
        for symbol, quantity in target_positions.items():
            current_qty = current_portfolio.positions.get(symbol, 0.0)
            trade_qty = quantity - current_qty
            
            if trade_qty == 0:
                filtered_positions[symbol] = quantity
                continue
            
            # Check if trade meets minimum amount
            if symbol in prices:
                trade_value = abs(trade_qty * prices[symbol])
                if trade_value < self.CONSTRAINTS["min_trade_amount"]:
                    logger.debug(f"Trade too small for {symbol}: ${trade_value:.2f} < ${self.CONSTRAINTS['min_trade_amount']}")
                    # Keep current position
                    filtered_positions[symbol] = current_qty
                    continue
            
            filtered_positions[symbol] = quantity
        
        return filtered_positions
    
    def needs_rebalance(self, current_weights: Dict[str, float],
                       target_weights: Dict[str, float]) -> bool:
        """
        Check if portfolio needs rebalancing.
        Only rebalance if weight change > threshold.
        """
        max_change = 0.0
        
        for symbol in set(list(current_weights.keys()) + list(target_weights.keys())):
            current = current_weights.get(symbol, 0.0)
            target = target_weights.get(symbol, 0.0)
            change = abs(target - current)
            max_change = max(max_change, change)
        
        needs_rebal = max_change > self.CONSTRAINTS["min_rebalance_threshold"]
        
        if needs_rebal:
            logger.info(f"Rebalance needed: max weight change {max_change:.2%}")
        else:
            logger.debug(f"No rebalance needed: max change {max_change:.2%}")
        
        return needs_rebal
    
    def calculate_turnover(self, current_positions: Dict[str, float],
                          target_positions: Dict[str, float],
                          prices: Dict[str, float],
                          nav: float) -> float:
        """
        Calculate portfolio turnover rate.
        
        Returns:
            Turnover as fraction of NAV
        """
        total_trade_value = 0.0
        
        for symbol in set(list(current_positions.keys()) + list(target_positions.keys())):
            current_qty = current_positions.get(symbol, 0.0)
            target_qty = target_positions.get(symbol, 0.0)
            trade_qty = abs(target_qty - current_qty)
            
            if symbol in prices and trade_qty > 0:
                trade_value = trade_qty * prices[symbol]
                total_trade_value += trade_value
        
        if nav > 0:
            turnover = total_trade_value / nav
        else:
            turnover = 0.0
        
        logger.debug(f"Portfolio turnover: {turnover:.2%}")
        return turnover
    
    def check_daily_limits(self, num_trades: int, turnover: float) -> bool:
        """
        Check if daily trading limits would be exceeded.
        
        Returns:
            True if limits OK, False if would exceed
        """
        new_trades = self.daily_trades + num_trades
        new_turnover = self.daily_turnover + turnover
        
        if new_trades > self.CONSTRAINTS["max_daily_trades"]:
            logger.warning(f"Daily trade limit exceeded: {new_trades} > {self.CONSTRAINTS['max_daily_trades']}")
            return False
        
        if new_turnover > self.CONSTRAINTS["max_daily_turnover"]:
            logger.warning(f"Daily turnover limit exceeded: {new_turnover:.2%} > {self.CONSTRAINTS['max_daily_turnover']:.2%}")
            return False
        
        return True
    
    def update_daily_metrics(self, num_trades: int, turnover: float):
        """Update daily trade and turnover counters"""
        self.daily_trades += num_trades
        self.daily_turnover += turnover
        logger.debug(f"Daily metrics: {self.daily_trades} trades, {self.daily_turnover:.2%} turnover")
    
    def reset_daily_metrics(self):
        """Reset daily counters (call at start of each trading day)"""
        self.daily_trades = 0
        self.daily_turnover = 0.0
        logger.debug("Daily metrics reset")
    
    def calculate_portfolio_nav(self, positions: Dict[str, float],
                                cash: float,
                                prices: Dict[str, float]) -> float:
        """
        Calculate portfolio Net Asset Value.
        
        Args:
            positions: Current positions (symbol -> quantity)
            cash: Cash balance
            prices: Current prices
            
        Returns:
            Total NAV
        """
        position_value = 0.0
        
        for symbol, quantity in positions.items():
            if symbol in prices:
                value = quantity * prices[symbol]
                position_value += value
        
        nav = cash + position_value
        return nav
    
    def calculate_weights(self, positions: Dict[str, float],
                         prices: Dict[str, float],
                         nav: float) -> Dict[str, float]:
        """
        Calculate current portfolio weights.
        
        Returns:
            Dict mapping symbol -> weight (0-1)
        """
        if nav == 0:
            return {}
        
        weights = {}
        
        for symbol, quantity in positions.items():
            if symbol in prices:
                value = quantity * prices[symbol]
                weight = value / nav
                weights[symbol] = weight
        
        return weights