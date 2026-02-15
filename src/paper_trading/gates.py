"""Gate Validation System

Based on Tech Design v1.2 Section 4.11.3
Implements FR-5.3: Gate Validation System
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime, date, timedelta
import numpy as np

from .models import (
    GateValidationResult,
    GateCheckResult,
    DeviationReport
)
from .monitor import RealTimePerformanceMonitor
from ..models import BacktestResult


@dataclass
class Phase12Gates:
    """Phase 1+2 Paper Trading Gate requirements from PRD FR-5.3"""
    min_trading_days: int = 63  # Minimum 3 months
    min_sharpe: float = 0.5
    max_drawdown: float = 0.15  # 15%
    min_availability: float = 0.999  # 99.9%
    required_risk_levels: List[int] = field(default_factory=lambda: [1, 2, 3, 4])
    min_rolling_ic: float = 0.02


@dataclass
class Phase3Gates:
    """Phase 3 (ML) Additional Gate requirements"""
    ml_outperformance: bool = True
    min_trading_days: int = 63
    max_drawdown: float = 0.15
    min_ic_sustained: float = 0.02


class GateValidationSystem:
    """
    Automated validation of paper trading gates.
    
    Based on PRD FR-5.3 requirements:
    - Validates minimum trading days (63)
    - Validates Sharpe ratio (> 0.5)
    - Validates max drawdown (< 15%)
    - Validates system availability (> 99.9%)
    - Validates risk level coverage (all levels triggered at least once)
    - Validates rolling IC (> 0.02)
    """
    
    PHASE_1_2_GATES = Phase12Gates()
    PHASE_3_GATES = Phase3Gates()
    
    def __init__(self, performance_monitor: RealTimePerformanceMonitor):
        """
        Initialize gate validation system.
        
        Args:
            performance_monitor: Real-time performance monitor instance
        """
        self.monitor = performance_monitor
        
        # Tracking state
        self.trading_days_count = 0
        self.risk_levels_triggered: Set[int] = set()
        self.system_uptime_seconds = 0
        self.total_seconds = 0
        self.start_time: datetime = datetime.now()
        
        # Gate history
        self.gate_history: List[GateValidationResult] = []
        self.daily_gate_checks: List[Dict] = []
    
    def record_trading_day(self) -> None:
        """Record a completed trading day"""
        self.trading_days_count += 1
    
    def record_risk_level_trigger(self, level: int) -> None:
        """
        Record when a risk level is triggered.
        
        Args:
            level: Risk level (1-4)
        """
        if 1 <= level <= 4:
            self.risk_levels_triggered.add(level)
    
    def record_uptime(self, uptime_seconds: float, total_seconds: float) -> None:
        """
        Record system uptime.
        
        Args:
            uptime_seconds: Seconds of system uptime
            total_seconds: Total seconds in measurement period
        """
        self.system_uptime_seconds += uptime_seconds
        self.total_seconds += total_seconds
    
    def validate_phase_1_2_gates(self) -> GateValidationResult:
        """
        Validate all Phase 1+2 paper trading gates.
        
        Returns detailed result with pass/fail for each gate.
        """
        gates = self.PHASE_1_2_GATES
        results = {}
        warnings = []
        
        # Gate 1: Minimum trading days
        trading_days_passed = self.trading_days_count >= gates.min_trading_days
        results["min_trading_days"] = {
            "required": gates.min_trading_days,
            "actual": self.trading_days_count,
            "passed": trading_days_passed,
            "gap": max(0, gates.min_trading_days - self.trading_days_count)
        }
        if not trading_days_passed:
            warnings.append(f"Need {gates.min_trading_days - self.trading_days_count} more trading days")
        
        # Gate 2: Sharpe ratio (use 252-day Sharpe if available, else longest available)
        sharpe_252 = self.monitor.calculate_rolling_sharpe(252)
        sharpe_60 = self.monitor.calculate_rolling_sharpe(60)
        sharpe_20 = self.monitor.calculate_rolling_sharpe(20)
        
        # Use the longest available Sharpe
        if sharpe_252 != 0:
            current_sharpe = sharpe_252
            sharpe_window = 252
        elif sharpe_60 != 0:
            current_sharpe = sharpe_60
            sharpe_window = 60
        else:
            current_sharpe = sharpe_20
            sharpe_window = 20
        
        sharpe_passed = current_sharpe > gates.min_sharpe
        results["sharpe_ratio"] = {
            "required": f"> {gates.min_sharpe}",
            "actual": f"{current_sharpe:.3f}",
            "actual_value": current_sharpe,
            "window_days": sharpe_window,
            "passed": sharpe_passed
        }
        if not sharpe_passed and current_sharpe != 0:
            warnings.append(f"Sharpe {current_sharpe:.3f} below threshold {gates.min_sharpe}")
        
        # Gate 3: Maximum drawdown
        current_dd = self.monitor.calculate_max_drawdown()
        dd_passed = current_dd < gates.max_drawdown
        results["max_drawdown"] = {
            "required": f"< {gates.max_drawdown * 100:.1f}%",
            "actual": f"{current_dd * 100:.2f}%",
            "actual_value": current_dd,
            "passed": dd_passed
        }
        if not dd_passed:
            warnings.append(f"Max drawdown {current_dd:.2%} exceeds limit {gates.max_drawdown:.0%}")
        
        # Gate 4: System availability
        if self.total_seconds > 0:
            availability = self.system_uptime_seconds / self.total_seconds
        else:
            availability = 1.0  # Assume 100% if not tracked
        
        availability_passed = availability >= gates.min_availability
        results["system_availability"] = {
            "required": f"> {gates.min_availability * 100:.1f}%",
            "actual": f"{availability * 100:.3f}%",
            "actual_value": availability,
            "passed": availability_passed
        }
        if not availability_passed:
            warnings.append(f"System availability {availability:.3%} below threshold {gates.min_availability:.1%}")
        
        # Gate 5: Risk level coverage
        required_levels = set(gates.required_risk_levels)
        risk_coverage_passed = self.risk_levels_triggered >= required_levels
        missing_levels = required_levels - self.risk_levels_triggered
        results["risk_level_coverage"] = {
            "required": sorted(list(required_levels)),
            "actual": sorted(list(self.risk_levels_triggered)),
            "passed": risk_coverage_passed,
            "missing_levels": sorted(list(missing_levels))
        }
        if not risk_coverage_passed:
            warnings.append(f"Missing risk level triggers: {missing_levels}")
        
        # Gate 6: Rolling IC (if ML model is used)
        ic_trend = self.monitor.get_ic_trend(days=20)
        if "mean_ic" in ic_trend:
            current_ic = ic_trend.get("current_ic", 0)
            ic_passed = current_ic > gates.min_rolling_ic
            results["rolling_ic"] = {
                "required": f"> {gates.min_rolling_ic}",
                "actual": f"{current_ic:.4f}",
                "actual_value": current_ic,
                "passed": ic_passed
            }
            if not ic_passed:
                warnings.append(f"Rolling IC {current_ic:.4f} below threshold {gates.min_rolling_ic}")
        
        # Determine overall pass
        all_passed = all(r.get("passed", True) for r in results.values())
        
        result = GateValidationResult(
            phase="Phase 1+2",
            gates=results,
            overall_passed=all_passed,
            validation_date=datetime.now(),
            warnings=warnings
        )
        
        self.gate_history.append(result)
        return result
    
    def validate_phase_3_gates(
        self,
        ml_sharpe: float,
        traditional_sharpe: float
    ) -> GateValidationResult:
        """
        Validate Phase 3 (ML) additional gates.
        
        Args:
            ml_sharpe: Sharpe ratio of ML-enhanced strategy
            traditional_sharpe: Sharpe ratio of traditional strategy
        
        Returns:
            GateValidationResult for Phase 3 gates
        """
        gates = self.PHASE_3_GATES
        results = {}
        warnings = []
        
        # Gate 1: ML outperformance
        outperformance = ml_sharpe > traditional_sharpe
        results["ml_outperformance"] = {
            "required": f"ML > Traditional",
            "actual": f"ML: {ml_sharpe:.3f}, Traditional: {traditional_sharpe:.3f}",
            "passed": outperformance
        }
        if not outperformance:
            warnings.append(f"ML strategy ({ml_sharpe:.3f}) does not outperform traditional ({traditional_sharpe:.3f})")
        
        # Gate 2: Minimum trading days
        trading_days_passed = self.trading_days_count >= gates.min_trading_days
        results["min_trading_days"] = {
            "required": gates.min_trading_days,
            "actual": self.trading_days_count,
            "passed": trading_days_passed
        }
        
        # Gate 3: Max drawdown
        current_dd = self.monitor.calculate_max_drawdown()
        dd_passed = current_dd < gates.max_drawdown
        results["max_drawdown"] = {
            "required": f"< {gates.max_drawdown * 100:.1f}%",
            "actual": f"{current_dd * 100:.2f}%",
            "passed": dd_passed
        }
        
        # Gate 4: Sustained IC
        ic_trend = self.monitor.get_ic_trend(days=20)
        current_ic = ic_trend.get("current_ic", 0) if "mean_ic" in ic_trend else 0
        ic_passed = current_ic > gates.min_ic_sustained
        results["sustained_ic"] = {
            "required": f"> {gates.min_ic_sustained}",
            "actual": f"{current_ic:.4f}",
            "passed": ic_passed
        }
        
        all_passed = all(r.get("passed", True) for r in results.values())
        
        return GateValidationResult(
            phase="Phase 3 (ML)",
            gates=results,
            overall_passed=all_passed,
            validation_date=datetime.now(),
            warnings=warnings
        )
    
    def generate_deviation_report(
        self,
        backtest_results: BacktestResult
    ) -> DeviationReport:
        """
        Compare paper trading results with backtest expectations.
        
        Identifies significant deviations for investigation.
        
        Args:
            backtest_results: Backtest performance metrics
        
        Returns:
            DeviationReport with comparisons
        """
        # Get paper trading metrics
        paper_sharpe = self.monitor.calculate_rolling_sharpe(252)
        if paper_sharpe == 0:
            paper_sharpe = self.monitor.calculate_rolling_sharpe(60)
        
        paper_dd = self.monitor.calculate_max_drawdown()
        paper_return = (self.monitor.portfolio.nav / self.monitor.portfolio.initial_capital - 1)
        
        # Calculate deviations
        sharpe_deviation = abs(paper_sharpe - backtest_results.sharpe_ratio)
        dd_deviation = abs(paper_dd - abs(backtest_results.max_drawdown))
        return_deviation = abs(paper_return - backtest_results.total_return)
        
        # Identify significant deviations
        significant_deviations = []
        
        # Threshold: Sharpe deviation > 0.3
        if sharpe_deviation > 0.3:
            significant_deviations.append(f"Sharpe deviation: {sharpe_deviation:.3f} > 0.3 threshold")
        
        # Threshold: Drawdown deviation > 5%
        if dd_deviation > 0.05:
            significant_deviations.append(f"Drawdown deviation: {dd_deviation:.2%} > 5% threshold")
        
        # Threshold: Return deviation > 5%
        if return_deviation > 0.05:
            significant_deviations.append(f"Return deviation: {return_deviation:.2%} > 5% threshold")
        
        return DeviationReport(
            metric_comparisons={
                "sharpe_ratio": {
                    "backtest": backtest_results.sharpe_ratio,
                    "paper": paper_sharpe,
                    "deviation": sharpe_deviation
                },
                "max_drawdown": {
                    "backtest": abs(backtest_results.max_drawdown),
                    "paper": paper_dd,
                    "deviation": dd_deviation
                },
                "total_return": {
                    "backtest": backtest_results.total_return,
                    "paper": paper_return,
                    "deviation": return_deviation
                }
            },
            significant_deviations=significant_deviations
        )
    
    def get_gate_progress(self) -> Dict:
        """
        Get progress towards gate completion.
        
        Returns:
            Dict with progress metrics
        """
        gates = self.PHASE_1_2_GATES
        
        # Calculate progress percentages
        trading_days_progress = min(1.0, self.trading_days_count / gates.min_trading_days)
        risk_coverage_progress = len(self.risk_levels_triggered) / len(gates.required_risk_levels)
        
        availability = self.system_uptime_seconds / self.total_seconds if self.total_seconds > 0 else 1.0
        
        return {
            "trading_days": {
                "current": self.trading_days_count,
                "required": gates.min_trading_days,
                "progress": f"{trading_days_progress * 100:.1f}%"
            },
            "risk_levels_triggered": {
                "current": sorted(list(self.risk_levels_triggered)),
                "required": gates.required_risk_levels,
                "progress": f"{risk_coverage_progress * 100:.0f}%"
            },
            "system_availability": {
                "current": f"{availability * 100:.3f}%",
                "required": f"{gates.min_availability * 100:.1f}%",
                "passing": availability >= gates.min_availability
            },
            "overall_progress": {
                "trading_days": trading_days_progress,
                "risk_coverage": risk_coverage_progress,
                "availability": availability
            }
        }
    
    def should_trigger_risk_test(self) -> bool:
        """
        Check if we should artificially trigger a risk event for testing.
        
        Returns True if no risk events have been recorded yet.
        """
        return len(self.risk_levels_triggered) == 0
    
    def get_summary(self) -> str:
        """Generate human-readable summary"""
        progress = self.get_gate_progress()
        
        lines = [
            "=== Paper Trading Gate Progress ===",
            "",
            f"Trading Days: {progress['trading_days']['current']}/{progress['trading_days']['required']} ({progress['trading_days']['progress']})",
            f"Risk Levels Triggered: {progress['risk_levels_triggered']['current']} (need: {progress['risk_levels_triggered']['required']})",
            f"System Availability: {progress['system_availability']['current']} (required: {progress['system_availability']['required']})",
            "",
            f"Running for: {self.trading_days_count} trading days",
            f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M')}"
        ]
        
        # Add latest validation result if available
        if self.gate_history:
            latest = self.gate_history[-1]
            status = "✓ PASSED" if latest.overall_passed else "✗ NOT PASSED"
            lines.append(f"Latest Validation: {status}")
        
        return "\n".join(lines)
