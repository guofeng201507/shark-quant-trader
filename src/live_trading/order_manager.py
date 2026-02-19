"""Order Management System for Live Trading - Phase 6

Based on Tech Design v1.2 Section 4.12.2
Implements FR-6.2: Order Management System
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from .models import (
    LiveOrder,
    OrderResponse,
    OrderLogEntry
)
from .brokers import BrokerAdapter


class OrderManagementSystem:
    """Intelligent order management with routing and retry logic.
    
    Based on PRD FR-6.2 requirements:
    - Smart order routing
    - Order splitting (large orders)
    - Order retry logic
    - Order logging for audit trail
    """
    
    # Routing configuration
    ROUTING_CONFIG = {
        "US_ETF": "alpaca",
        "CRYPTO": "binance",
        "GLOBAL": "ibkr"
    }
    
    # Order splitting thresholds
    SPLIT_CONFIG = {
        "max_single_order_usd": 50000,
        "max_pct_of_volume": 0.01,
        "slice_count": 5,
        "slice_interval_minutes": 5
    }
    
    # Retry configuration
    RETRY_CONFIG = {
        "max_retries": 3,
        "retry_delay_seconds": 5,
        "exponential_backoff": True
    }
    
    def __init__(self, brokers: Dict[str, BrokerAdapter]):
        """Initialize order management system."""
        self.brokers = brokers
        self.pending_orders: Dict[str, LiveOrder] = {}
        self.executed_orders: List[LiveOrder] = []
        self.order_log: List[OrderLogEntry] = []
        self.order_counter = 0
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        self.order_counter += 1
        return f"LIVE-{datetime.now().strftime('%Y%m%d')}-{self.order_counter:06d}"
    
    def route_order(self, order: LiveOrder) -> str:
        """Determine which broker to use for the order."""
        symbol = order.symbol
        
        # Crypto routing - handle various symbol formats
        # BTC, BTC/USD, BTC-USD, BTCUSDT, etc.
        crypto_symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "USDT", "USDC", "DOGE", "ADA"]
        symbol_upper = symbol.upper()
        
        # Check if it's a crypto asset
        if any(crypto in symbol_upper for crypto in crypto_symbols):
            return "binance"
        
        # Check for common crypto pair formats
        if symbol_upper.endswith("-USD") or symbol_upper.endswith("/USD") or symbol_upper.endswith("USDT"):
            return "binance"
        
        # US ETF routing
        us_etfs = ["GLD", "SPY", "QQQ", "SLV", "XLK", "XLF", "XLE", "XLV", "TLT", "TIP", "EFA", "EEM", "DBC", "VNQ"]
        if symbol in us_etfs:
            return "alpaca"
        
        return "ibkr"
    
    def should_split_order(self, order: LiveOrder, current_price: float) -> bool:
        """Determine if order should be split."""
        if current_price <= 0:
            return False
        order_value = order.quantity * current_price
        return order_value > self.SPLIT_CONFIG["max_single_order_usd"]
    
    def split_order(self, order: LiveOrder, current_price: float) -> List[LiveOrder]:
        """Split large order into TWAP slices."""
        total_value = order.quantity * current_price
        slice_count = min(
            self.SPLIT_CONFIG["slice_count"],
            int(total_value / self.SPLIT_CONFIG["max_single_order_usd"]) + 1
        )
        
        slice_quantity = order.quantity / slice_count
        slices = []
        
        for i in range(slice_count):
            slice_order = LiveOrder(
                order_id=self._generate_order_id(),
                symbol=order.symbol,
                side=order.side,
                quantity=slice_quantity,
                order_type="LIMIT",
                limit_price=current_price * (1.001 if order.side == "BUY" else 0.999),
                reason=f"{order.reason} (slice {i+1}/{slice_count})"
            )
            slices.append(slice_order)
        
        return slices
    
    async def submit_order(self, order: LiveOrder) -> OrderResponse:
        """Submit a single order with retry logic."""
        broker_name = self.route_order(order)
        broker = self.brokers.get(broker_name)
        
        if not broker:
            return OrderResponse(
                broker_order_id="",
                status="REJECTED",
                message=f"Broker {broker_name} not available"
            )
        
        # Execute with retry
        for attempt in range(self.RETRY_CONFIG["max_retries"]):
            try:
                result = await broker.submit_order(order)
                self._log_order(order, result, broker_name, attempt + 1)
                
                if result.status in ["FILLED", "PARTIAL"]:
                    order.status = result.status
                    self.executed_orders.append(order)
                
                return result
            except Exception as e:
                if attempt < self.RETRY_CONFIG["max_retries"] - 1:
                    delay = self.RETRY_CONFIG["retry_delay_seconds"]
                    if self.RETRY_CONFIG["exponential_backoff"]:
                        delay *= (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    self._log_order(order, None, broker_name, attempt + 1, error=str(e))
                    return OrderResponse(
                        broker_order_id="",
                        status="REJECTED",
                        message=f"Failed after {attempt + 1} attempts: {str(e)}"
                    )
    
    async def execute_order(self, order: LiveOrder, current_price: float) -> List[OrderResponse]:
        """Execute order with automatic splitting if needed."""
        results = []
        
        if self.should_split_order(order, current_price):
            slices = self.split_order(order, current_price)
            for slice_order in slices:
                result = await self.submit_order(slice_order)
                results.append(result)
        else:
            result = await self.submit_order(order)
            results.append(result)
        
        return results
    
    def _log_order(self, order: LiveOrder, result: Optional[OrderResponse], broker: str, attempt: int, error: str = None) -> None:
        """Log all order activity for audit trail."""
        self.order_log.append(OrderLogEntry(
            timestamp=datetime.now(),
            order=order,
            broker=broker,
            attempt=attempt,
            result=result,
            error=error
        ))
    
    def get_order_summary(self) -> Dict:
        """Get summary of order management system."""
        total_orders = len(self.order_log)
        filled_orders = len([e for e in self.order_log if e.result and e.result.status == "FILLED"])
        return {
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "pending_orders": len(self.pending_orders),
            "success_rate": filled_orders / total_orders if total_orders > 0 else 0
        }
    
    async def get_all_account_info(self) -> Dict[str, Dict]:
        """Get account info from all brokers."""
        results = {}
        for name, broker in self.brokers.items():
            try:
                account_info = await broker.get_account_info()
                results[name] = {
                    "account_id": account_info.account_id,
                    "cash": account_info.cash,
                    "portfolio_value": account_info.portfolio_value,
                    "positions_count": len(account_info.positions)
                }
            except Exception as e:
                results[name] = {"error": str(e)}
        return results
