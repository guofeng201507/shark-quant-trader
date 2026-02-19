"""Capital Transition Manager for Live Trading - Phase 6

Based on Tech Design v1.2 Section 4.12.3
Implements FR-6.2: Capital Transition Management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .models import TransitionEvent


@dataclass
class CapitalStage:
    """Capital deployment stage"""
    name: str
    capital_pct: float
    duration_weeks: int
    loss_limit: float


class CapitalTransitionManager:
    """Manages gradual capital deployment from paper to live trading.
    
    Based on PRD FR-6.2 capital transition requirements:
    
    Stages:
    - Stage 1: 10% capital (4 weeks, 5% loss limit)
    - Stage 2: 25% capital (4 weeks, 5% loss limit)
    - Stage 3: 50% capital (2 weeks, 5% loss limit)
    - Stage 4: 100% capital (ongoing, 10% loss limit)
    
    Rollback triggers:
    - Single day loss > 3% triggers evaluation
    - Cumulative drawdown > 10% rolls back
    - 2+ system failures rolls back to paper
    """
    
    # Default stages from PRD
    DEFAULT_STAGES = [
        CapitalStage("Stage 1", 0.10, 4, 0.05),
        CapitalStage("Stage 2", 0.25, 4, 0.05),
        CapitalStage("Stage 3", 0.50, 2, 0.05),
        CapitalStage("Stage 4", 1.00, 0, 0.10),
    ]
    
    # Rollback triggers
    ROLLBACK_TRIGGERS = {
        "daily_loss_threshold": 0.03,
        "cumulative_dd_threshold": 0.10,
        "system_failure_count": 2
    }
    
    def __init__(self, total_capital: float, stages: Optional[List[CapitalStage]] = None):
        """Initialize capital transition manager.
        
        Args:
            total_capital: Total capital available for trading
            stages: Optional custom stages (defaults to PRD stages)
        """
        self.total_capital = total_capital
        self.stages = stages or self.DEFAULT_STAGES
        
        self.current_stage = 0
        self.stage_start_date: Optional[datetime] = None
        self.stage_start_nav: float = total_capital
        self.system_failure_count = 0
        self.transition_log: List[TransitionEvent] = []
        
        # Initialize first stage
        self.stage_start_date = datetime.now()
    
    @property
    def current_stage_info(self) -> CapitalStage:
        """Get current stage info"""
        return self.stages[self.current_stage]
    
    def get_current_allocation(self) -> float:
        """Get current capital allocation amount.
        
        Returns:
            Current allocation in dollars
        """
        return self.total_capital * self.current_stage_info.capital_pct
    
    def get_current_allocation_pct(self) -> float:
        """Get current allocation percentage.
        
        Returns:
            Current allocation as decimal (e.g., 0.10 for 10%)
        """
        return self.current_stage_info.capital_pct
    
    def get_days_in_stage(self) -> int:
        """Get number of days in current stage.
        
        Returns:
            Days since current stage started
        """
        if not self.stage_start_date:
            return 0
        return (datetime.now() - self.stage_start_date).days
    
    def can_advance_stage(self, current_nav: float) -> Tuple[bool, str]:
        """Check if conditions are met to advance to next stage.
        
        Args:
            current_nav: Current portfolio NAV
            
        Returns:
            Tuple of (can_advance, reason)
        """
        stage = self.current_stage_info
        
        # Check if at final stage
        if self.current_stage >= len(self.stages) - 1:
            return False, "Already at final stage (100%)"
        
        # Check duration requirement
        required_days = stage.duration_weeks * 7 if stage.duration_weeks else 0
        days_in_stage = self.get_days_in_stage()
        
        if required_days > 0 and days_in_stage < required_days:
            return False, f"Need {required_days - days_in_stage} more days in current stage"
        
        # Check loss limit
        if self.stage_start_nav > 0:
            stage_return = (current_nav - self.stage_start_nav) / self.stage_start_nav
            if stage_return < -stage.loss_limit:
                return False, f"Stage loss {stage_return:.2%} exceeds limit {-stage.loss_limit:.2%}"
        
        return True, "All conditions met for advancement"
    
    def advance_stage(self, current_nav: float) -> Tuple[bool, str]:
        """Advance to next stage if conditions are met.
        
        Args:
            current_nav: Current portfolio NAV
            
        Returns:
            Tuple of (success, message)
        """
        can_advance, reason = self.can_advance_stage(current_nav)
        
        if not can_advance:
            return False, reason
        
        if self.current_stage < len(self.stages) - 1:
            self.current_stage += 1
            self.stage_start_date = datetime.now()
            self.stage_start_nav = current_nav
            
            self._log_transition(
                "ADVANCE",
                f"Advanced to {self.current_stage_info.name}: "
                f"{self.current_stage_info.capital_pct:.0%} capital"
            )
            return True, f"Advanced to {self.current_stage_info.name}"
        
        return False, "Already at final stage"
    
    def rollback_stage(self) -> Tuple[bool, str]:
        """Rollback to previous stage.
        
        Returns:
            Tuple of (success, message)
        """
        if self.current_stage > 0:
            old_stage = self.stages[self.current_stage].name
            self.current_stage -= 1
            self.stage_start_date = datetime.now()
            
            self._log_transition(
                "ROLLBACK",
                f"Rolled back to {self.current_stage_info.name}"
            )
            return True, f"Rolled back to {self.current_stage_info.name}"
        
        return False, "Already at Stage 1"
    
    def check_rollback_triggers(self, daily_return: float, cumulative_dd: float) -> Optional[str]:
        """Check if any rollback conditions are triggered.
        
        Args:
            daily_return: Today's return (negative for loss)
            cumulative_dd: Cumulative drawdown
            
        Returns:
            Rollback action or None
        """
        # Daily loss trigger
        if daily_return < -self.ROLLBACK_TRIGGERS["daily_loss_threshold"]:
            self._log_transition(
                "EVALUATE",
                f"Daily loss {daily_return:.2%} exceeded {self.ROLLBACK_TRIGGERS['daily_loss_threshold']:.2%} threshold"
            )
            return "EVALUATE"
        
        # Cumulative drawdown trigger
        if cumulative_dd > self.ROLLBACK_TRIGGERS["cumulative_dd_threshold"]:
            self._log_transition(
                "ROLLBACK_STAGE",
                f"Cumulative DD {cumulative_dd:.2%} exceeded {self.ROLLBACK_TRIGGERS['cumulative_dd_threshold']:.2%} threshold"
            )
            return "ROLLBACK_STAGE"
        
        # System failure trigger
        if self.system_failure_count >= self.ROLLBACK_TRIGGERS["system_failure_count"]:
            self._log_transition(
                "ROLLBACK_TO_PAPER",
                f"{self.system_failure_count} system failures exceeded limit"
            )
            return "ROLLBACK_TO_PAPER"
        
        return None
    
    def record_system_failure(self) -> None:
        """Record a system failure event."""
        self.system_failure_count += 1
    
    def reset_system_failures(self) -> None:
        """Reset system failure counter (e.g., after successful recovery)."""
        self.system_failure_count = 0
    
    def _log_transition(self, action: str, reason: str) -> None:
        """Log transition event for audit.
        
        Args:
            action: Action taken
            reason: Reason for action
        """
        self.transition_log.append(TransitionEvent(
            timestamp=datetime.now(),
            action=action,
            from_stage=self.current_stage,
            to_stage=self.current_stage if action == "ADVANCE" else self.current_stage,
            reason=reason
        ))
    
    def get_transition_log(self) -> List[TransitionEvent]:
        """Get transition event log.
        
        Returns:
            List of transition events
        """
        return self.transition_log
    
    def get_progress(self) -> Dict:
        """Get progress towards full deployment.
        
        Returns:
            Dict with progress information
        """
        stage = self.current_stage_info
        days_in_stage = self.get_days_in_stage()
        required_days = stage.duration_weeks * 7 if stage.duration_weeks else 0
        
        return {
            "current_stage": self.current_stage + 1,
            "total_stages": len(self.stages),
            "stage_name": stage.name,
            "capital_pct": f"{stage.capital_pct:.0%}",
            "capital_amount": f"${self.get_current_allocation():,.2f}",
            "days_in_stage": days_in_stage,
            "required_days": required_days,
            "system_failures": f"{self.system_failure_count}/{self.ROLLBACK_TRIGGERS['system_failure_count']}",
            "is_final_stage": self.current_stage >= len(self.stages) - 1
        }
    
    def get_summary(self) -> str:
        """Get human-readable summary.
        
        Returns:
            Summary string
        """
        progress = self.get_progress()
        
        lines = [
            "=== Capital Transition Status ===",
            f"Stage: {progress['stage_name']} ({progress['current_stage']}/{progress['total_stages']})",
            f"Capital: {progress['capital_pct']} ({progress['capital_amount']})",
            f"Days in Stage: {progress['days_in_stage']}/{progress['required_days']}",
            f"System Failures: {progress['system_failures']}",
        ]
        
        if self.transition_log:
            last_event = self.transition_log[-1]
            lines.append(f"Last Event: {last_event.action} - {last_event.reason}")
        
        return "\n".join(lines)
