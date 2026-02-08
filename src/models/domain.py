"""Core domain models based on Tech Design v1.1"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import pandas as pd


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class MarketRegime(Enum):
    """Market volatility regimes based on VIX levels"""
    NORMAL = "NORMAL"           # VIX < 20
    ELEVATED = "ELEVATED"       # 20 <= VIX < 30
    HIGH_VOL = "HIGH_VOL"       # 30 <= VIX < 40
    EXTREME = "EXTREME"         # VIX >= 40


@dataclass
class TradeSignal:
    """Trading signal with confidence and reasoning"""
    symbol: str
    signal: SignalType
    confidence: float  # 0.0 to 1.0
    target_weight: float
    reason: str
    timestamp: datetime
    regime: MarketRegime
    
    def __post_init__(self):
        """Validate signal parameters"""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
        if not 0 <= self.target_weight <= 1:
            raise ValueError(f"Target weight must be between 0 and 1, got {self.target_weight}")


@dataclass
class Portfolio:
    """Portfolio state representation"""
    positions: Dict[str, float]  # symbol -> quantity
    cash: float
    nav: float  # Net Asset Value
    peak_nav: float  # For drawdown calculation
    weights: Dict[str, float]
    unrealized_pnl: float
    cost_basis: Dict[str, float]  # symbol -> average cost
    target_volatility: float = 0.15
    
    def calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak"""
        if self.peak_nav == 0:
            return 0.0
        return (self.peak_nav - self.nav) / self.peak_nav


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    level: int  # 0-4
    portfolio_drawdown: float
    correlation_matrix: Optional[pd.DataFrame] = None
    violations: List[str] = field(default_factory=list)
    recovery_mode: bool = False
    weeks_in_recovery: int = 0
    
    def __post_init__(self):
        """Validate risk level"""
        if not 0 <= self.level <= 4:
            raise ValueError(f"Risk level must be between 0 and 4, got {self.level}")


@dataclass
class Order:
    """Order representation"""
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    order_type: str  # MARKET/LIMIT
    limit_price: Optional[float] = None
    timestamp: Optional[datetime] = None
    status: str = "PENDING"
    estimated_commission: float = 0.0
    reason: str = ""
    
    def __post_init__(self):
        """Validate order parameters"""
        if self.side not in ["BUY", "SELL"]:
            raise ValueError(f"Side must be BUY or SELL, got {self.side}")
        if self.order_type not in ["MARKET", "LIMIT"]:
            raise ValueError(f"Order type must be MARKET or LIMIT, got {self.order_type}")
        if self.order_type == "LIMIT" and self.limit_price is None:
            raise ValueError("Limit price required for LIMIT orders")


@dataclass
class DataQualityReport:
    """Data quality validation report"""
    symbol: str
    total_rows: int
    missing_values: Dict[str, float]  # column -> missing percentage
    price_jumps: int  # Number of extreme price jumps
    issues: List[str]
    passed: bool = True
    
    def __post_init__(self):
        """Determine if quality check passed"""
        self.passed = len(self.issues) == 0


@dataclass
class BacktestResult:
    """Backtest performance metrics"""
    start_date: str
    end_date: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    num_trades: int
    annualized_volatility: float = 0.0
    profit_factor: float = 0.0
    monthly_turnover: float = 0.0
    annual_cost_drag: float = 0.0
    equity_curve: Optional[pd.Series] = None
    
    def meets_criteria(self, min_sharpe: float = 0.7, max_dd: float = 0.20) -> bool:
        """Check if backtest meets minimum criteria from PRD"""
        return self.sharpe_ratio > min_sharpe and abs(self.max_drawdown) < max_dd


@dataclass
class StressTestReport:
    """Stress test results"""
    scenario: str
    stressed_nav: float
    drawdown: float
    risk_level: int
    survived: bool
    recovery_days: Optional[int] = None
    details: Optional[Dict] = None
    
    def __post_init__(self):
        """Validate stress test result"""
        if self.details is None:
            self.details = {}