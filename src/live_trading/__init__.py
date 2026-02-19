"""Live Trading System - Phase 6

Based on Tech Design v1.2 Section 4.12
Implements FR-6.1, FR-6.2, FR-6.3 from PRD

Components:
- Broker Adapters: Alpaca, Binance, IBKR integration
- Order Management: Smart routing, splitting, retry logic
- Capital Transition: Staged deployment with rollback triggers
- Live Monitoring: Health, performance, model quality tracking
"""

from .models import (
    LiveOrder,
    OrderResponse,
    OrderStatus,
    OrderType,
    OrderSide,
    Position,
    AccountInfo,
    OrderLogEntry,
    TransitionEvent,
    HealthCheck,
    PerformanceSnapshot,
    LiveTradingConfig,
    CapitalStage,
    DEFAULT_STAGES
)

from .brokers import (
    BrokerAdapter,
    AlpacaAdapter,
    BinanceAdapter,
    IBKRAdapter,
    BrokerFactory
)

from .order_manager import OrderManagementSystem

from .transition import CapitalTransitionManager

from .monitor import LiveMonitoringSystem

__all__ = [
    # Models
    "LiveOrder",
    "OrderResponse",
    "OrderStatus",
    "OrderType",
    "OrderSide",
    "Position",
    "AccountInfo",
    "OrderLogEntry",
    "TransitionEvent",
    "HealthCheck",
    "PerformanceSnapshot",
    "LiveTradingConfig",
    "CapitalStage",
    "DEFAULT_STAGES",
    
    # Brokers
    "BrokerAdapter",
    "AlpacaAdapter",
    "BinanceAdapter",
    "IBKRAdapter",
    "BrokerFactory",
    
    # Order Management
    "OrderManagementSystem",
    
    # Capital Transition
    "CapitalTransitionManager",
    
    # Live Monitoring
    "LiveMonitoringSystem"
]
