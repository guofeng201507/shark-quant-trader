"""Paper Trading Engine - Simulates realistic order execution

Based on Tech Design v1.2 Section 4.11.1
Implements FR-5.1: Paper Trading Engine
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import uuid
import numpy as np
import pandas as pd

from .models import PaperOrder, PaperExecutionResult, PaperPortfolio


@dataclass
class SlippageConfig:
    """Slippage model configuration"""
    base_slippage_bps: float = 5.0  # 5 bps base slippage
    volatility_multiplier: float = 0.1  # Additional slippage per 1% volatility
    size_impact_threshold: float = 10000.0  # Orders above this get extra slippage
    size_impact_bps_per_10k: float = 2.0  # Additional bps per $10k over threshold
    
    def to_dict(self) -> Dict:
        return {
            "base_slippage_bps": self.base_slippage_bps,
            "volatility_multiplier": self.volatility_multiplier,
            "size_impact_threshold": self.size_impact_threshold,
            "size_impact_bps_per_10k": self.size_impact_bps_per_10k
        }


@dataclass
class DelayConfig:
    """Execution delay model configuration"""
    min_delay_seconds: int = 60  # Minimum 1 minute
    max_delay_seconds: int = 1800  # Maximum 30 minutes
    market_order_delay: int = 60  # Market orders: 1 minute
    limit_order_delay: int = 300  # Limit orders: 5 minutes
    twap_interval_minutes: int = 15  # TWAP slice interval
    
    def to_dict(self) -> Dict:
        return {
            "min_delay_seconds": self.min_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "market_order_delay": self.market_order_delay,
            "limit_order_delay": self.limit_order_delay,
            "twap_interval_minutes": self.twap_interval_minutes
        }


class PaperTradingEngine:
    """
    Simulates real trading execution with realistic market conditions.
    
    Based on PRD FR-5.1 requirements:
    - Simulates order types: MARKET, LIMIT, TWAP
    - Simulates slippage based on volatility and order size
    - Simulates execution delays (1-30 minutes)
    - Simulates partial fills for large orders
    """
    
    DEFAULT_SLIPPAGE_CONFIG = SlippageConfig()
    DEFAULT_DELAY_CONFIG = DelayConfig()
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        slippage_config: Optional[SlippageConfig] = None,
        delay_config: Optional[DelayConfig] = None,
        commission_rate: float = 0.001,  # 10 bps
        price_provider: Optional[Callable[[str], float]] = None,
        volatility_provider: Optional[Callable[[str], float]] = None
    ):
        """
        Initialize paper trading engine.
        
        Args:
            initial_capital: Starting capital
            slippage_config: Slippage model parameters
            delay_config: Execution delay parameters
            commission_rate: Commission rate as decimal
            price_provider: Function to get current price for symbol
            volatility_provider: Function to get current volatility for symbol
        """
        self.slippage_config = slippage_config or self.DEFAULT_SLIPPAGE_CONFIG
        self.delay_config = delay_config or self.DEFAULT_DELAY_CONFIG
        self.commission_rate = commission_rate
        self.price_provider = price_provider
        self.volatility_provider = volatility_provider
        
        # Portfolio state
        self.portfolio = PaperPortfolio(
            initial_capital=initial_capital,
            cash=initial_capital,
            positions={},
            cost_basis={},
            nav=initial_capital,
            peak_nav=initial_capital,
            weights={}
        )
        
        # Order tracking
        self.pending_orders: Dict[str, PaperOrder] = {}
        self.executed_orders: List[PaperExecutionResult] = []
        self.order_counter = 0
        
        # Price cache for simulation
        self._price_cache: Dict[str, float] = {}
        self._volatility_cache: Dict[str, float] = {}
    
    def set_price(self, symbol: str, price: float) -> None:
        """Set current price for a symbol (for simulation)"""
        self._price_cache[symbol] = price
    
    def set_volatility(self, symbol: str, volatility: float) -> None:
        """Set current volatility for a symbol (for simulation)"""
        self._volatility_cache[symbol] = volatility
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        if self.price_provider:
            return self.price_provider(symbol)
        return self._price_cache.get(symbol, 0.0)
    
    def get_current_volatility(self, symbol: str) -> float:
        """Get current volatility for symbol"""
        if self.volatility_provider:
            return self.volatility_provider(symbol)
        return self._volatility_cache.get(symbol, 0.20)  # Default 20% annual vol
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        self.order_counter += 1
        return f"PAPER-{datetime.now().strftime('%Y%m%d')}-{self.order_counter:06d}"
    
    def _calculate_slippage(
        self,
        symbol: str,
        quantity: float,
        estimated_price: float
    ) -> float:
        """
        Calculate realistic slippage based on:
        - Base slippage
        - Current volatility
        - Order size relative to average volume
        
        Returns slippage as decimal (e.g., 0.0005 = 5 bps)
        """
        config = self.slippage_config
        
        # Base slippage
        base = config.base_slippage_bps / 10000
        
        # Volatility impact
        volatility = self.get_current_volatility(symbol)
        vol_impact = volatility * config.volatility_multiplier
        
        # Size impact for large orders
        order_value = abs(quantity * estimated_price)
        size_impact = 0.0
        if order_value > config.size_impact_threshold:
            excess = order_value - config.size_impact_threshold
            size_impact = (excess / 10000) * config.size_impact_bps_per_10k / 10000
        
        return base + vol_impact + size_impact
    
    def _calculate_delay(self, order_type: str) -> int:
        """
        Calculate execution delay in seconds based on order type.
        
        Returns delay in seconds
        """
        config = self.delay_config
        
        if order_type == "MARKET":
            return config.market_order_delay
        elif order_type == "LIMIT":
            return config.limit_order_delay
        elif order_type == "TWAP":
            return config.twap_interval_minutes * 60
        else:
            return config.min_delay_seconds
    
    def submit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        limit_price: Optional[float] = None,
        reason: str = ""
    ) -> PaperOrder:
        """
        Submit order for paper execution.
        
        Args:
            symbol: Asset symbol
            side: BUY or SELL
            quantity: Number of shares/units
            order_type: MARKET, LIMIT, or TWAP
            limit_price: Limit price (required for LIMIT orders)
            reason: Reason for the order
        
        Returns:
            PaperOrder with execution metadata
        """
        # Validate inputs
        if side not in ["BUY", "SELL"]:
            raise ValueError(f"Side must be BUY or SELL, got {side}")
        if order_type not in ["MARKET", "LIMIT", "TWAP"]:
            raise ValueError(f"Order type must be MARKET/LIMIT/TWAP, got {order_type}")
        if order_type == "LIMIT" and limit_price is None:
            raise ValueError("Limit price required for LIMIT orders")
        
        # Get current price for slippage calculation
        current_price = limit_price or self.get_current_price(symbol)
        
        # Calculate slippage and delay
        slippage = self._calculate_slippage(symbol, quantity, current_price)
        delay = self._calculate_delay(order_type)
        
        # Create order
        order = PaperOrder(
            order_id=self._generate_order_id(),
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            expected_slippage=slippage,
            expected_execution_time=datetime.now() + timedelta(seconds=delay),
            status="PENDING",
            reason=reason
        )
        
        self.pending_orders[order.order_id] = order
        return order
    
    def execute_pending_orders(self) -> List[PaperExecutionResult]:
        """
        Execute orders that have reached their execution time.
        
        Returns list of execution results for newly executed orders.
        """
        results = []
        current_time = datetime.now()
        orders_to_remove = []
        
        for order_id, order in self.pending_orders.items():
            if order.expected_execution_time <= current_time:
                result = self._execute_single_order(order)
                results.append(result)
                self.executed_orders.append(result)
                orders_to_remove.append(order_id)
        
        # Remove executed orders from pending
        for order_id in orders_to_remove:
            del self.pending_orders[order_id]
        
        return results
    
    def _execute_single_order(self, order: PaperOrder) -> PaperExecutionResult:
        """
        Execute a single order with slippage applied.
        
        Updates portfolio state and returns execution result.
        """
        # Get current price
        current_price = self.get_current_price(order.symbol)
        if current_price == 0:
            # If no price available, use limit price or reject
            if order.limit_price:
                current_price = order.limit_price
            else:
                return PaperExecutionResult(
                    order_id=order.order_id,
                    symbol=order.symbol,
                    side=order.side,
                    requested_quantity=order.quantity,
                    fill_quantity=0,
                    fill_price=0,
                    slippage_actual=0,
                    execution_time=datetime.now(),
                    status="REJECTED",
                    commission=0
                )
        
        # Apply slippage (positive for buys, negative for sells)
        if order.side == "BUY":
            fill_price = current_price * (1 + order.expected_slippage)
        else:
            fill_price = current_price * (1 - order.expected_slippage)
        
        # Calculate fill quantity and check cash/position constraints
        fill_quantity = order.quantity
        
        if order.side == "BUY":
            # Check if enough cash
            required_cash = fill_quantity * fill_price * (1 + self.commission_rate)
            if required_cash > self.portfolio.cash:
                fill_quantity = self.portfolio.cash / (fill_price * (1 + self.commission_rate))
        else:
            # Check if enough position
            current_position = self.portfolio.positions.get(order.symbol, 0)
            fill_quantity = min(order.quantity, current_position)
        
        # Calculate commission
        commission = fill_quantity * fill_price * self.commission_rate
        
        # Update portfolio
        if order.side == "BUY":
            # Update cash
            self.portfolio.cash -= (fill_quantity * fill_price + commission)
            
            # Update position
            current_position = self.portfolio.positions.get(order.symbol, 0)
            current_cost = self.portfolio.cost_basis.get(order.symbol, 0) * current_position
            new_cost = fill_quantity * fill_price
            new_position = current_position + fill_quantity
            
            self.portfolio.positions[order.symbol] = new_position
            self.portfolio.cost_basis[order.symbol] = (current_cost + new_cost) / new_position if new_position > 0 else 0
            
        else:  # SELL
            # Update cash
            self.portfolio.cash += (fill_quantity * fill_price - commission)
            
            # Calculate realized P&L
            cost_basis = self.portfolio.cost_basis.get(order.symbol, 0)
            realized_pnl = (fill_price - cost_basis) * fill_quantity
            self.portfolio.realized_pnl += realized_pnl
            
            # Update position
            current_position = self.portfolio.positions.get(order.symbol, 0)
            new_position = current_position - fill_quantity
            if new_position <= 0:
                self.portfolio.positions.pop(order.symbol, None)
                self.portfolio.cost_basis.pop(order.symbol, None)
            else:
                self.portfolio.positions[order.symbol] = new_position
        
        # Determine status
        status = "FILLED" if fill_quantity == order.quantity else "PARTIAL"
        
        return PaperExecutionResult(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            requested_quantity=order.quantity,
            fill_quantity=fill_quantity,
            fill_price=fill_price,
            slippage_actual=order.expected_slippage,
            execution_time=datetime.now(),
            status=status,
            commission=commission,
            market_impact=order.expected_slippage  # Simplified: use slippage as market impact
        )
    
    def update_portfolio_nav(self, prices: Dict[str, float]) -> float:
        """
        Update portfolio NAV based on current prices.
        
        Args:
            prices: Dict mapping symbol to current price
        
        Returns:
            Updated NAV
        """
        # Calculate position values
        position_value = 0.0
        unrealized_pnl = 0.0
        
        for symbol, quantity in self.portfolio.positions.items():
            price = prices.get(symbol, self.get_current_price(symbol))
            position_value += quantity * price
            
            # Calculate unrealized P&L
            cost = self.portfolio.cost_basis.get(symbol, 0)
            unrealized_pnl += (price - cost) * quantity
        
        self.portfolio.unrealized_pnl = unrealized_pnl
        self.portfolio.nav = self.portfolio.cash + position_value
        self.portfolio.update_peak_nav()
        
        # Update weights
        if self.portfolio.nav > 0:
            self.portfolio.weights = {
                symbol: (quantity * prices.get(symbol, 0)) / self.portfolio.nav
                for symbol, quantity in self.portfolio.positions.items()
            }
            self.portfolio.weights["CASH"] = self.portfolio.cash / self.portfolio.nav
        
        return self.portfolio.nav
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of current portfolio state"""
        return {
            "nav": self.portfolio.nav,
            "cash": self.portfolio.cash,
            "positions": dict(self.portfolio.positions),
            "weights": dict(self.portfolio.weights),
            "realized_pnl": self.portfolio.realized_pnl,
            "unrealized_pnl": self.portfolio.unrealized_pnl,
            "drawdown": self.portfolio.calculate_drawdown(),
            "trading_days": self.portfolio.trading_days,
            "pending_orders": len(self.pending_orders),
            "total_trades": len(self.executed_orders)
        }
    
    def force_execute_all_pending(self) -> List[PaperExecutionResult]:
        """Force execute all pending orders immediately (for testing)"""
        results = []
        for order_id in list(self.pending_orders.keys()):
            order = self.pending_orders[order_id]
            result = self._execute_single_order(order)
            results.append(result)
            self.executed_orders.append(result)
            del self.pending_orders[order_id]
        return results
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        if order_id in self.pending_orders:
            del self.pending_orders[order_id]
            return True
        return False
    
    def get_execution_history(self, limit: int = 100) -> List[PaperExecutionResult]:
        """Get recent execution history"""
        return self.executed_orders[-limit:]
