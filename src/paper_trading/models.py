"""Paper Trading data models based on Tech Design v1.2 Section 4.11"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, date
import pandas as pd
import numpy as np


@dataclass
class PaperOrder:
    """Paper trading order with execution metadata"""
    order_id: str
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    order_type: str  # MARKET/LIMIT/TWAP
    limit_price: Optional[float]
    expected_slippage: float  # Expected slippage as decimal
    expected_execution_time: datetime
    status: str = "PENDING"  # PENDING/FILLED/CANCELLED/PARTIAL
    submitted_time: datetime = field(default_factory=datetime.now)
    reason: str = ""
    
    def __post_init__(self):
        """Validate order parameters"""
        if self.side not in ["BUY", "SELL"]:
            raise ValueError(f"Side must be BUY or SELL, got {self.side}")
        if self.order_type not in ["MARKET", "LIMIT", "TWAP"]:
            raise ValueError(f"Order type must be MARKET/LIMIT/TWAP, got {self.order_type}")


@dataclass
class PaperExecutionResult:
    """Result of paper order execution"""
    order_id: str
    symbol: str
    side: str
    requested_quantity: float
    fill_quantity: float
    fill_price: float
    slippage_actual: float
    execution_time: datetime
    status: str  # FILLED/PARTIAL/REJECTED
    commission: float = 0.0
    market_impact: float = 0.0
    
    @property
    def fill_value(self) -> float:
        """Total value of filled order"""
        return self.fill_quantity * self.fill_price


@dataclass
class PaperPortfolio:
    """Paper trading portfolio state"""
    initial_capital: float
    cash: float
    positions: Dict[str, float]  # symbol -> quantity
    cost_basis: Dict[str, float]  # symbol -> average cost
    nav: float
    peak_nav: float
    weights: Dict[str, float]
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    trading_days: int = 0
    start_date: date = field(default_factory=date.today)
    
    def calculate_drawdown(self) -> float:
        """Calculate current drawdown from peak NAV"""
        if self.peak_nav == 0:
            return 0.0
        return (self.peak_nav - self.nav) / self.peak_nav
    
    def update_peak_nav(self) -> None:
        """Update peak NAV if current NAV is higher"""
        if self.nav > self.peak_nav:
            self.peak_nav = self.nav


@dataclass
class DailyPerformanceReport:
    """Daily performance report for paper trading"""
    date: date
    nav: float
    daily_return: float
    cumulative_return: float
    sharpe_20d: float
    sharpe_60d: float
    sharpe_252d: float
    max_drawdown: float
    rolling_ic: float
    ks_drift: float
    daily_trades: int = 0
    daily_turnover: float = 0.0
    positions_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "date": str(self.date),
            "nav": self.nav,
            "daily_return": self.daily_return,
            "cumulative_return": self.cumulative_return,
            "sharpe_20d": self.sharpe_20d,
            "sharpe_60d": self.sharpe_60d,
            "sharpe_252d": self.sharpe_252d,
            "max_drawdown": self.max_drawdown,
            "rolling_ic": self.rolling_ic,
            "ks_drift": self.ks_drift,
            "daily_trades": self.daily_trades,
            "daily_turnover": self.daily_turnover,
            "positions_count": self.positions_count
        }


@dataclass
class GateCheckResult:
    """Result of individual gate check"""
    gate_name: str
    required: str
    actual: str
    passed: bool
    details: Dict = field(default_factory=dict)


@dataclass
class GateValidationResult:
    """Complete gate validation result"""
    phase: str
    gates: Dict[str, Dict]  # gate_name -> {required, actual, passed}
    overall_passed: bool
    validation_date: datetime
    warnings: List[str] = field(default_factory=list)
    
    def get_pass_rate(self) -> float:
        """Calculate percentage of gates passed"""
        if not self.gates:
            return 0.0
        passed = sum(1 for g in self.gates.values() if g.get("passed", False))
        return passed / len(self.gates)


@dataclass
class DeviationReport:
    """Paper vs backtest deviation analysis"""
    metric_comparisons: Dict[str, Dict[str, float]]  # metric -> {backtest, paper, deviation}
    significant_deviations: List[str]
    generated_at: datetime = field(default_factory=datetime.now)
    
    def has_significant_deviations(self) -> bool:
        """Check if any significant deviations exist"""
        return len(self.significant_deviations) > 0
    
    def to_summary(self) -> str:
        """Generate human-readable summary"""
        lines = ["=== Paper vs Backtest Deviation Report ===", ""]
        for metric, values in self.metric_comparisons.items():
            lines.append(f"{metric}:")
            lines.append(f"  Backtest: {values['backtest']:.4f}")
            lines.append(f"  Paper:    {values['paper']:.4f}")
            lines.append(f"  Deviation: {values['deviation']:.4f}")
        
        if self.significant_deviations:
            lines.append("")
            lines.append("Significant Deviations:")
            for dev in self.significant_deviations:
                lines.append(f"  - {dev}")
        return "\n".join(lines)


@dataclass
class ICPoint:
    """Single IC measurement point"""
    timestamp: datetime
    ic: float
    num_predictions: int
    
    @property
    def quality(self) -> str:
        """Assess IC quality"""
        if self.ic >= 0.05:
            return "EXCELLENT"
        elif self.ic >= 0.03:
            return "GOOD"
        elif self.ic >= 0.02:
            return "ACCEPTABLE"
        elif self.ic >= 0.0:
            return "WEAK"
        else:
            return "NEGATIVE"


@dataclass 
class KSDriftPoint:
    """Single KS drift measurement point"""
    timestamp: datetime
    ks_statistic: float
    feature_name: str
    
    @property
    def drift_level(self) -> str:
        """Assess drift level"""
        if self.ks_statistic >= 0.2:
            return "CRITICAL"
        elif self.ks_statistic >= 0.1:
            return "WARNING"
        else:
            return "NORMAL"
