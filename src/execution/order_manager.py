"""Order Manager - Tech Design v1.1 Section 5"""

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from ..models.domain import Order, Portfolio
from ..utils.logger import logger


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderManager:
    """Manage order creation, submission, and tracking"""
    
    def __init__(self):
        """Initialize order manager"""
        self.pending_orders: List[Order] = []
        self.order_history: List[Order] = []
        logger.info("OrderManager initialized")
    
    def create_orders(self, current_positions: Dict[str, float],
                     target_positions: Dict[str, float],
                     prices: Dict[str, float],
                     portfolio: Portfolio) -> List[Order]:
        """
        Create orders to move from current to target positions.
        
        Args:
            current_positions: Current positions (symbol -> quantity)
            target_positions: Target positions (symbol -> quantity)
            prices: Current market prices
            portfolio: Current portfolio state
            
        Returns:
            List of Order objects
        """
        orders = []
        
        # Determine all symbols to consider
        all_symbols = set(list(current_positions.keys()) + list(target_positions.keys()))
        
        for symbol in all_symbols:
            current_qty = current_positions.get(symbol, 0.0)
            target_qty = target_positions.get(symbol, 0.0)
            
            # Calculate trade quantity
            trade_qty = target_qty - current_qty
            
            if abs(trade_qty) < 1e-6:  # Skip negligible trades
                continue
            
            # Determine order side
            side = "BUY" if trade_qty > 0 else "SELL"
            quantity = abs(trade_qty)
            
            # Get price
            price = prices.get(symbol, 0.0)
            if price <= 0:
                logger.warning(f"Invalid price for {symbol}, skipping order")
                continue
            
            # Create order
            order = Order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type="MARKET",  # Phase 1 uses market orders
                limit_price=None,
                timestamp=datetime.now(),
                status=OrderStatus.PENDING.value
            )
            
            orders.append(order)
            logger.info(f"Created order: {side} {quantity} {symbol} @ market")
        
        self.pending_orders.extend(orders)
        return orders
    
    def submit_order(self, order: Order) -> bool:
        """
        Submit order for execution (placeholder for broker integration).
        
        Args:
            order: Order to submit
            
        Returns:
            True if submission successful
        """
        # TODO: Integrate with actual broker API (Alpaca, IBKR, etc.)
        # For Phase 1, this is a simulation
        
        logger.info(f"Submitting order: {order.side} {order.quantity} {order.symbol}")
        
        # Simulate order submission
        order.status = OrderStatus.SUBMITTED.value
        
        # In production, this would return order ID from broker
        return True
    
    def check_order_status(self, order: Order) -> str:
        """
        Check order execution status (placeholder for broker integration).
        
        Args:
            order: Order to check
            
        Returns:
            Order status string
        """
        # TODO: Query broker API for order status
        # For Phase 1, simulate immediate fill
        
        if order.status == OrderStatus.SUBMITTED.value:
            order.status = OrderStatus.FILLED.value
            logger.info(f"Order filled: {order.side} {order.quantity} {order.symbol}")
        
        return order.status
    
    def cancel_order(self, order: Order) -> bool:
        """
        Cancel pending order.
        
        Args:
            order: Order to cancel
            
        Returns:
            True if cancellation successful
        """
        if order.status not in [OrderStatus.PENDING.value, OrderStatus.SUBMITTED.value]:
            logger.warning(f"Cannot cancel order with status {order.status}")
            return False
        
        # TODO: Send cancellation to broker API
        order.status = OrderStatus.CANCELLED.value
        logger.info(f"Order cancelled: {order.side} {order.quantity} {order.symbol}")
        
        return True
    
    def cancel_all_pending(self) -> int:
        """
        Cancel all pending orders.
        
        Returns:
            Number of orders cancelled
        """
        cancelled_count = 0
        
        for order in self.pending_orders:
            if order.status in [OrderStatus.PENDING.value, OrderStatus.SUBMITTED.value]:
                if self.cancel_order(order):
                    cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} pending orders")
        return cancelled_count
    
    def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        return [o for o in self.pending_orders 
                if o.status in [OrderStatus.PENDING.value, OrderStatus.SUBMITTED.value]]
    
    def get_filled_orders(self) -> List[Order]:
        """Get all filled orders"""
        return [o for o in self.pending_orders + self.order_history
                if o.status == OrderStatus.FILLED.value]
    
    def archive_completed_orders(self):
        """Move completed orders to history"""
        completed = [o for o in self.pending_orders
                    if o.status in [OrderStatus.FILLED.value, 
                                   OrderStatus.CANCELLED.value,
                                   OrderStatus.REJECTED.value]]
        
        self.order_history.extend(completed)
        self.pending_orders = [o for o in self.pending_orders
                              if o not in completed]
        
        if completed:
            logger.debug(f"Archived {len(completed)} completed orders")
    
    def calculate_cost(self, order: Order, filled_price: float) -> Dict:
        """
        Calculate order execution cost.
        
        From Tech Design Section 4.3.6:
        - Commission: $0/trade (Alpaca), 0.1% fallback
        - Slippage: 0.05% stocks, 0.1% BTC
        - Spread: Half-spread impact
        
        Args:
            order: Executed order
            filled_price: Actual fill price
            
        Returns:
            Dict with cost breakdown
        """
        notional = order.quantity * filled_price
        
        # Commission (assume Alpaca for Phase 1)
        commission = 0.0
        
        # Slippage estimate
        if order.symbol == "BTC-USD":
            slippage_rate = 0.001  # 0.1%
        else:
            slippage_rate = 0.0005  # 0.05%
        
        slippage = notional * slippage_rate
        
        # Total cost
        total_cost = commission + slippage
        
        return {
            "notional": notional,
            "commission": commission,
            "slippage": slippage,
            "total_cost": total_cost,
            "cost_bps": (total_cost / notional * 10000) if notional > 0 else 0
        }