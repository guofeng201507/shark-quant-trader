"""Paper Trading System - Phase 5

Based on Tech Design v1.2 Section 4.11
Implements FR-5.1, FR-5.2, FR-5.3 from PRD

Components:
- PaperTradingEngine: Simulates realistic order execution with slippage/delay
- RealTimePerformanceMonitor: Tracks IC, KS, Sharpe, drawdown metrics
- GateValidationSystem: Validates paper trading gate requirements
"""

from .models import (
    PaperOrder,
    PaperExecutionResult,
    PaperPortfolio,
    DailyPerformanceReport,
    GateCheckResult,
    GateValidationResult,
    DeviationReport,
    ICPoint,
    KSDriftPoint
)

from .engine import (
    PaperTradingEngine,
    SlippageConfig,
    DelayConfig
)

from .monitor import (
    RealTimePerformanceMonitor,
    MonitorConfig
)

from .gates import (
    GateValidationSystem,
    Phase12Gates,
    Phase3Gates
)

__all__ = [
    # Models
    "PaperOrder",
    "PaperExecutionResult",
    "PaperPortfolio",
    "DailyPerformanceReport",
    "GateCheckResult",
    "GateValidationResult",
    "DeviationReport",
    "ICPoint",
    "KSDriftPoint",
    
    # Engine
    "PaperTradingEngine",
    "SlippageConfig",
    "DelayConfig",
    
    # Monitor
    "RealTimePerformanceMonitor",
    "MonitorConfig",
    
    # Gates
    "GateValidationSystem",
    "Phase12Gates",
    "Phase3Gates"
]
