"""Re-Entry Manager - Tech Design v1.1 Section 4.3.4"""

import pandas as pd
from ..models.domain import Portfolio
from ..utils.logger import logger


class ReEntryManager:
    """Manage position recovery after risk events"""
    
    CONFIG = {
        "cooldown_days": 5,             # Consecutive days of low vol required
        "vol_threshold_multiplier": 1.0, # Vol must be < target vol
        "initial_position_pct": 0.25,   # Start with 25% of normal position
        "ramp_up_weekly_pct": 0.25,     # Add 25% each week
        "max_leverage_recovery": 1.0    # Lower leverage during recovery
    }
    
    def __init__(self):
        """Initialize re-entry manager"""
        self.in_recovery = False
        self.recovery_start_date = None
        self.weeks_in_recovery = 0
        logger.info("ReEntryManager initialized")
    
    def check_reentry_conditions(self, portfolio: Portfolio,
                                 volatility_history: pd.Series) -> bool:
        """
        Check if conditions met to resume trading after Level 4 exit.
        Requires 5 consecutive days where portfolio vol < target vol.
        
        Args:
            portfolio: Current portfolio state
            volatility_history: Series of recent portfolio volatility
            
        Returns:
            True if re-entry conditions are met
        """
        if len(volatility_history) < self.CONFIG["cooldown_days"]:
            logger.debug("Insufficient volatility history for re-entry check")
            return False
        
        # Get recent volatility
        recent_vol = volatility_history.tail(self.CONFIG["cooldown_days"])
        
        # Check if all recent vol < target vol
        target_vol = portfolio.target_volatility * self.CONFIG["vol_threshold_multiplier"]
        conditions_met = all(recent_vol < target_vol)
        
        if conditions_met:
            logger.info(f"Re-entry conditions met: {self.CONFIG['cooldown_days']} days vol < {target_vol:.2%}")
        else:
            logger.debug(f"Re-entry conditions not met: recent vol {recent_vol.mean():.2%} vs target {target_vol:.2%}")
        
        return conditions_met
    
    def calculate_recovery_position(self, target_weight: float,
                                   weeks_in_recovery: int) -> float:
        """
        Gradual position rebuild: 25% → 50% → 75% → 100% over 4 weeks.
        
        Args:
            target_weight: Normal target weight
            weeks_in_recovery: Number of weeks since recovery started
            
        Returns:
            Adjusted target weight for recovery period
        """
        recovery_pct = min(1.0, 
                          self.CONFIG["initial_position_pct"] + 
                          weeks_in_recovery * self.CONFIG["ramp_up_weekly_pct"])
        
        adjusted_weight = target_weight * recovery_pct
        
        logger.debug(f"Recovery position: week {weeks_in_recovery}, "
                    f"{recovery_pct:.0%} of target = {adjusted_weight:.2%}")
        
        return adjusted_weight
    
    def start_recovery(self) -> None:
        """Start recovery mode"""
        self.in_recovery = True
        self.recovery_start_date = pd.Timestamp.now()
        self.weeks_in_recovery = 0
        logger.info("Recovery mode STARTED")
    
    def end_recovery(self) -> None:
        """End recovery mode"""
        self.in_recovery = False
        self.recovery_start_date = None
        self.weeks_in_recovery = 0
        logger.info("Recovery mode ENDED")
    
    def update_recovery_week(self) -> None:
        """Increment recovery week counter"""
        if self.in_recovery:
            self.weeks_in_recovery += 1
            logger.info(f"Recovery week {self.weeks_in_recovery}")
    
    def is_recovery_complete(self) -> bool:
        """Check if recovery period is complete (4 weeks)"""
        return self.weeks_in_recovery >= 4
    
    def get_max_leverage(self) -> float:
        """Get maximum allowed leverage during recovery"""
        if self.in_recovery:
            return self.CONFIG["max_leverage_recovery"]
        return 1.5  # Normal max leverage from Tech Design