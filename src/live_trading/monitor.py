"""Live Monitoring System for Phase 6

Based on Tech Design v1.2 Section 4.12.4
Implements FR-6.3: Live Monitoring System
"""

from typing import Dict, List, Optional
from datetime import datetime
import time
import numpy as np

from .models import HealthCheck, PerformanceSnapshot


class LiveMonitoringSystem:
    """Real-time monitoring for live trading operations.
    
    Based on PRD FR-6.3 requirements:
    - System health monitoring (API response, memory, CPU)
    - Strategy performance monitoring (Sharpe, drawdown)
    - Model quality monitoring (IC, KS drift)
    """
    
    def __init__(self):
        self.health_history: List[HealthCheck] = []
        self.performance_history: List[PerformanceSnapshot] = []
        self.ic_history: List[float] = []
        self.ks_history: List[float] = []
        self.alerts: List[Dict] = []
        self.last_data_update: Optional[datetime] = None
    
    def check_system_health(self) -> HealthCheck:
        """Check system health."""
        import psutil
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        data_freshness = 0
        if self.last_data_update:
            data_freshness = (datetime.now() - self.last_data_update).total_seconds() / 60
        
        issues = []
        if memory.percent > 80:
            issues.append(f"Memory {memory.percent:.1f}% > 80%")
        if cpu > 80:
            issues.append(f"CPU {cpu:.1f}% > 80%")
        
        health = HealthCheck(
            timestamp=datetime.now(),
            api_response_time_ms=0,
            data_freshness_minutes=int(data_freshness),
            memory_usage_pct=memory.percent,
            cpu_usage_pct=cpu,
            broker_connections={},
            issues=issues
        )
        self.health_history.append(health)
        return health
    
    def update_data_timestamp(self) -> None:
        self.last_data_update = datetime.now()
    
    def record_performance(self, nav: float, daily_return: float, positions: int = 0, trades: int = 0) -> PerformanceSnapshot:
        initial = self.performance_history[0].nav if self.performance_history else nav
        cumulative = (nav - initial) / initial if initial > 0 else 0
        sharpe = self._calc_sharpe()
        max_dd = self._calc_max_dd()
        
        snap = PerformanceSnapshot(
            timestamp=datetime.now(),
            nav=nav,
            daily_return=daily_return,
            cumulative_return=cumulative,
            sharpe_20d=sharpe,
            max_drawdown=max_dd,
            positions_count=positions,
            daily_trades=trades
        )
        self.performance_history.append(snap)
        
        if max_dd > 0.15:
            self._alert("CRITICAL", f"Max DD {max_dd:.2%} > 15%")
        elif max_dd > 0.10:
            self._alert("WARNING", f"Max DD {max_dd:.2%} > 10%")
        
        return snap
    
    def _calc_sharpe(self) -> float:
        if len(self.performance_history) < 2:
            return 0.0
        returns = [p.daily_return for p in self.performance_history[-20:]]
        if not returns or np.std(returns) == 0:
            return 0.0
        return (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252))
    
    def _calc_max_dd(self) -> float:
        if not self.performance_history:
            return 0.0
        navs = [p.nav for p in self.performance_history]
        peak = np.maximum.accumulate(navs)
        dd = (peak - navs) / peak
        return float(np.max(dd)) if len(dd) > 0 else 0.0
    
    def record_ic(self, ic: float) -> None:
        self.ic_history.append(ic)
        if ic < 0.02:
            self._alert("WARNING", f"IC {ic:.4f} < 0.02")
    
    def record_ks(self, ks: float) -> None:
        self.ks_history.append(ks)
        if ks > 0.2:
            self._alert("CRITICAL", f"KS {ks:.4f} > 0.2 - trigger retrain")
        elif ks > 0.1:
            self._alert("WARNING", f"KS {ks:.4f} > 0.1")
    
    def _alert(self, level: str, message: str) -> None:
        self.alerts.append({"timestamp": datetime.now(), "level": level, "message": message})
    
    def should_retrain(self) -> bool:
        if len(self.ic_history) >= 10:
            if all(ic < 0.02 for ic in self.ic_history[-10:]):
                return True
        if self.ks_history and self.ks_history[-1] > 0.2:
            return True
        return False
    
    def get_status(self) -> Dict:
        return {
            "nav": self.performance_history[-1].nav if self.performance_history else 0,
            "return": f"{self.performance_history[-1].cumulative_return:.2%}" if self.performance_history else "0%",
            "sharpe": f"{self.performance_history[-1].sharpe_20d:.2f}" if self.performance_history else "0",
            "max_dd": f"{self.performance_history[-1].max_drawdown:.2%}" if self.performance_history else "0%",
            "ic": f"{self.ic_history[-1]:.4f}" if self.ic_history else "N/A",
            "ks": f"{self.ks_history[-1]:.4f}" if self.ks_history else "N/A",
            "alerts": len(self.alerts)
        }
