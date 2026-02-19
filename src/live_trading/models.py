"""Live Trading data models based on Tech Design v1.2 Section 4.12"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, date
from enum import Enum
import numpy as np


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class LiveOrder:
    """Live trading order"""
    order_id: str
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    order_type: str  # MARKET/LIMIT/STOP/STOP_LIMIT
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str = "PENDING"
    submitted_time: datetime = field(default_factory=datetime.now)
    filled_time: Optional[datetime] = None
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    commission: float = 0.0
    broker: str = ""
    reason: str = ""


@dataclass
class OrderResponse:
    """Response from broker after order submission"""
    broker_order_id: str
    status: str
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    """Live trading position"""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class AccountInfo:
    """Broker account information"""
    account_id: str
    cash: float
    buying_power: float
    portfolio_value: float
    positions: Dict[str, Position] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OrderLogEntry:
    """Order activity log entry"""
    timestamp: datetime
    order: LiveOrder
    broker: str
    attempt: int
    result: Optional[OrderResponse]
    error: Optional[str] = None


@dataclass
class TransitionEvent:
    """Capital transition event"""
    timestamp: datetime
    action: str  # ADVANCE, ROLLBACK, EVALUATE, ROLLBACK_TO_PAPER
    from_stage: int
    to_stage: Optional[int] = None
    reason: str = ""


@dataclass
class HealthCheck:
    """System health check result"""
    timestamp: datetime
    api_response_time_ms: float
    data_freshness_minutes: int
    memory_usage_pct: float
    cpu_usage_pct: float
    broker_connections: Dict[str, bool] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Return health status based on issues"""
        if not self.issues:
            return "HEALTHY"
        critical_count = sum(1 for i in self.issues if "CRITICAL" in i.upper())
        if critical_count > 0:
            return "CRITICAL"
        return "WARNING"


@dataclass
class PerformanceSnapshot:
    """Performance snapshot for live trading"""
    timestamp: datetime
    nav: float
    daily_return: float
    cumulative_return: float
    sharpe_20d: float
    max_drawdown: float
    positions_count: int
    daily_trades: int


@dataclass
class LiveTradingConfig:
    """Live trading configuration"""
    # Broker settings
    alpaca_enabled: bool = True
    alpaca_paper: bool = True  # Use paper trading by default
    binance_enabled: bool = True
    binance_testnet: bool = True  # Use testnet by default
    ibkr_enabled: bool = False
    
    # Order settings
    max_single_order_usd: float = 50000.0
    max_pct_of_volume: float = 0.01
    slice_count: int = 5
    slice_interval_minutes: int = 5
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: int = 5
    exponential_backoff: bool = True
    
    # Transition settings
    total_capital: float = 100000.0
    stage_1_pct: float = 0.10
    stage_2_pct: float = 0.25
    stage_3_pct: float = 0.50
    stage_4_pct: float = 1.00
    
    # Rollback triggers
    daily_loss_threshold: float = 0.03
    cumulative_dd_threshold: float = 0.10
    system_failure_count_limit: int = 2
    
    # Health thresholds
    api_response_time_limit_ms: int = 1000
    data_freshness_limit_minutes: int = 30
    memory_usage_limit_pct: float = 80.0
    cpu_usage_limit_pct: float = 80.0


@dataclass
class CapitalStage:
    """Capital deployment stage"""
    name: str
    capital_pct: float
    duration_weeks: int
    loss_limit: float
    
    @property
    def capital_amount(self, total_capital: float) -> float:
        return total_capital * self.capital_pct


# Default stages from PRD
DEFAULT_STAGES = [
    CapitalStage("Stage 1", 0.10, 4, 0.05),
    CapitalStage("Stage 2", 0.25, 4, 0.05),
    CapitalStage("Stage 3", 0.50, 2, 0.05),
    CapitalStage("Stage 4", 1.00, 0, 0.10),
]
