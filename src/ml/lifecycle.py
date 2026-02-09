"""Model Lifecycle Management - PRD FR-3.5

Handles model retraining schedules, retirement criteria, and concept drift monitoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from ..utils.logger import logger


@dataclass
class LifecycleConfig:
    """Configuration for model lifecycle management"""
    # Retraining schedule
    retrain_monthly: bool = True          # Monthly retraining
    retrain_trigger_ic: float = 0.02      # Retrain if rolling IC < 0.02 for 10 days
    retrain_data_window: int = 756        # Use last 3 years of data
    
    # Retirement criteria
    retire_ic_threshold: float = 0.0      # Retire if IC < 0 for 30 days
    retire_ic_days: int = 30
    
    # Drift detection
    drift_ks_threshold_alert: float = 0.1  # KS > 0.1: alert
    drift_ks_threshold_retrain: float = 0.2  # KS > 0.2: trigger retrain
    
    # Performance comparison
    min_ic_improvement: float = 0.01      # New model must be better by 0.01
    p_value_threshold: float = 0.05       # Statistical significance


class ModelLifecycleManager:
    """
    Model lifecycle management.
    
    FR-3.5 Requirements:
    - Regular retraining: monthly with latest 3 years data
    - Triggered retraining: rolling IC < 0.02 for 10 consecutive days
    - Retirement: IC < 0 for 30 consecutive days
    - New model must significantly outperform old model (IC diff > 0.01, p < 0.05)
    - Concept drift: KS > 0.1 alert, KS > 0.2 trigger retrain
    """
    
    def __init__(self, config: Optional[LifecycleConfig] = None):
        self.config = config or LifecycleConfig()
        self.ic_history: List[Dict] = []
        self.drift_history: List[Dict] = []
        self.last_retrain_date: Optional[datetime] = None
        
        logger.info("ModelLifecycleManager initialized")
    
    def check_retrain_needed(self, 
                            current_ic: float,
                            current_date: datetime) -> Tuple[bool, str]:
        """
        Check if model retraining is needed.
        
        Returns:
            Tuple of (retrain_needed, reason)
        """
        # Record IC
        self.ic_history.append({
            'date': current_date,
            'ic': current_ic,
        })
        
        # 1. Monthly retraining
        if self.config.retrain_monthly:
            if self.last_retrain_date is None:
                return True, "Initial training needed"
            
            days_since_retrain = (current_date - self.last_retrain_date).days
            if days_since_retrain >= 30:
                return True, f"Monthly retraining ({days_since_retrain} days since last)"
        
        # 2. Triggered retraining: IC < 0.02 for 10 consecutive days
        if len(self.ic_history) >= 10:
            recent = self.ic_history[-10:]
            if all(h['ic'] < self.config.retrain_trigger_ic for h in recent):
                return True, f"IC < {self.config.retrain_trigger_ic} for 10 consecutive days"
        
        # 3. Concept drift triggered retrain
        if self.drift_history:
            latest_drift = self.drift_history[-1]
            if latest_drift.get('max_ks', 0) > self.config.drift_ks_threshold_retrain:
                return True, f"Concept drift detected (KS={latest_drift['max_ks']:.3f})"
        
        return False, "No retraining needed"
    
    def check_retirement_needed(self) -> Tuple[bool, str]:
        """
        Check if model should be retired.
        
        FR-3.5: IC < 0 for 30 consecutive days -> auto retire
        """
        if len(self.ic_history) < self.config.retire_ic_days:
            return False, "Insufficient history"
        
        recent = self.ic_history[-self.config.retire_ic_days:]
        
        if all(h['ic'] < self.config.retire_ic_threshold for h in recent):
            return True, f"IC < {self.config.retire_ic_threshold} for {self.config.retire_ic_days} consecutive days"
        
        return False, "Model performing adequately"
    
    def validate_new_model(self,
                          old_model_metrics: Dict,
                          new_model_metrics: Dict) -> Tuple[bool, str]:
        """
        Validate if new model should replace old model.
        
        FR-3.5: New model must significantly outperform old model
        - IC difference > 0.01
        - Statistical significance (p < 0.05)
        """
        old_ic = old_model_metrics.get('ic_mean', 0)
        new_ic = new_model_metrics.get('ic_mean', 0)
        
        ic_diff = new_ic - old_ic
        
        if ic_diff < self.config.min_ic_improvement:
            return False, f"IC improvement {ic_diff:.4f} < {self.config.min_ic_improvement} threshold"
        
        # Statistical significance test (simplified)
        # In practice, would use proper statistical test with IC variances
        old_std = old_model_metrics.get('ic_std', 0.1)
        new_std = new_model_metrics.get('ic_std', 0.1)
        
        # Approximate t-test
        n = 10  # Assuming 10 folds
        se = np.sqrt((old_std**2 + new_std**2) / n)
        if se > 0:
            t_stat = ic_diff / se
            # Simplified: require t > 2 (approx p < 0.05)
            if t_stat < 2:
                return False, f"Improvement not statistically significant (t={t_stat:.2f})"
        
        return True, f"New model validated: IC improved by {ic_diff:.4f}"
    
    def record_drift(self, 
                    drift_scores: Dict[str, float],
                    date: datetime):
        """Record concept drift detection results"""
        max_ks = max(drift_scores.values()) if drift_scores else 0
        
        self.drift_history.append({
            'date': date,
            'max_ks': max_ks,
            'drift_scores': drift_scores,
            'alert': max_ks > self.config.drift_ks_threshold_alert,
            'retrain_triggered': max_ks > self.config.drift_ks_threshold_retrain,
        })
        
        if max_ks > self.config.drift_ks_threshold_retrain:
            logger.warning(f"Severe drift detected (KS={max_ks:.3f}), retraining triggered")
        elif max_ks > self.config.drift_ks_threshold_alert:
            logger.warning(f"Moderate drift detected (KS={max_ks:.3f})")
    
    def update_retrain_date(self, date: datetime):
        """Update last retraining date"""
        self.last_retrain_date = date
        logger.info(f"Retraining date updated: {date}")
    
    def get_lifecycle_report(self) -> Dict:
        """Generate lifecycle status report"""
        report = {
            'last_retrain': self.last_retrain_date.isoformat() if self.last_retrain_date else None,
            'ic_history_length': len(self.ic_history),
            'current_ic': self.ic_history[-1]['ic'] if self.ic_history else None,
            'avg_ic_last_30': np.mean([h['ic'] for h in self.ic_history[-30:]]) if len(self.ic_history) >= 30 else None,
            'drift_events': len([d for d in self.drift_history if d['alert']]),
            'retrain_triggers': len([d for d in self.drift_history if d['retrain_triggered']]),
        }
        
        # Check current status
        retire_needed, retire_reason = self.check_retirement_needed()
        report['retire_needed'] = retire_needed
        report['retire_reason'] = retire_reason
        
        return report
