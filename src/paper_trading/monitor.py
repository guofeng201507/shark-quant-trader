"""Real-Time Performance Monitor

Based on Tech Design v1.2 Section 4.11.2
Implements FR-5.2: Real-Time Performance Tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from .models import (
    PaperPortfolio,
    DailyPerformanceReport,
    ICPoint,
    KSDriftPoint
)


@dataclass
class MonitorConfig:
    """Performance monitoring configuration"""
    # Rolling windows
    sharpe_short_window: int = 20
    sharpe_medium_window: int = 60
    sharpe_long_window: int = 252
    ic_window: int = 20
    ks_window: int = 20
    
    # IC thresholds
    ic_warning_threshold: float = 0.02
    ic_critical_threshold: float = 0.0
    ic_retrain_consecutive_days: int = 10
    
    # KS thresholds
    ks_warning_threshold: float = 0.1
    ks_critical_threshold: float = 0.2
    
    # Performance thresholds
    max_drawdown_warning: float = 0.10
    max_drawdown_critical: float = 0.15
    min_sharpe_threshold: float = 0.5


class RealTimePerformanceMonitor:
    """
    Real-time tracking of portfolio performance metrics.
    
    Based on PRD FR-5.2 requirements:
    - Portfolio NAV and P&L (real-time)
    - Sharpe Ratio (rolling 20/60/252 days)
    - Maximum Drawdown (real-time)
    - IC monitoring: Rolling IC (20-day rolling)
    - KS monitoring: Feature distribution drift detection
    """
    
    DEFAULT_CONFIG = MonitorConfig()
    
    def __init__(
        self,
        portfolio: PaperPortfolio,
        config: Optional[MonitorConfig] = None
    ):
        """
        Initialize performance monitor.
        
        Args:
            portfolio: Paper portfolio to monitor
            config: Monitoring configuration
        """
        self.portfolio = portfolio
        self.config = config or self.DEFAULT_CONFIG
        
        # History tracking
        self.nav_history: pd.Series = pd.Series(dtype=float)
        self.returns_history: pd.Series = pd.Series(dtype=float)
        self.date_history: List[date] = []
        
        # IC tracking
        self.ic_history: List[ICPoint] = []
        self.predictions_history: pd.DataFrame = pd.DataFrame()
        self.actuals_history: pd.DataFrame = pd.DataFrame()
        
        # KS drift tracking
        self.ks_history: List[KSDriftPoint] = []
        self.feature_history: pd.DataFrame = pd.DataFrame()
        self.training_feature_distribution: Optional[pd.DataFrame] = None
        
        # Daily tracking
        self.daily_trades: List[int] = []
        self.daily_turnover: List[float] = []
        
        # Alert tracking
        self.alerts: List[Dict] = []
    
    def record_day(
        self,
        current_prices: Dict[str, float],
        daily_trades: int = 0,
        daily_turnover: float = 0.0
    ) -> DailyPerformanceReport:
        """
        Record end-of-day portfolio state.
        
        Args:
            current_prices: Current prices for all positions
            daily_trades: Number of trades executed today
            daily_turnover: Portfolio turnover today
        
        Returns:
            DailyPerformanceReport for the day
        """
        today = date.today()
        
        # Calculate NAV
        nav = self._calculate_nav(current_prices)
        
        # Update peak NAV
        if nav > self.portfolio.peak_nav:
            self.portfolio.peak_nav = nav
        
        # Calculate daily return
        prev_nav = self.nav_history.iloc[-1] if len(self.nav_history) > 0 else self.portfolio.initial_capital
        daily_return = (nav - prev_nav) / prev_nav if prev_nav > 0 else 0
        
        # Record history
        self.nav_history = pd.concat([
            self.nav_history,
            pd.Series({today: nav})
        ])
        self.returns_history = pd.concat([
            self.returns_history,
            pd.Series({today: daily_return})
        ])
        self.date_history.append(today)
        self.daily_trades.append(daily_trades)
        self.daily_turnover.append(daily_turnover)
        
        # Update portfolio
        self.portfolio.nav = nav
        self.portfolio.trading_days = len(self.date_history)
        
        # Calculate metrics
        sharpe_20d = self.calculate_rolling_sharpe(20)
        sharpe_60d = self.calculate_rolling_sharpe(60)
        sharpe_252d = self.calculate_rolling_sharpe(252)
        max_dd = self.calculate_max_drawdown()
        cumulative_return = (nav / self.portfolio.initial_capital - 1)
        
        # Get latest IC and KS if available
        latest_ic = self.ic_history[-1].ic if self.ic_history else np.nan
        latest_ks = self.ks_history[-1].ks_statistic if self.ks_history else 0.0
        
        # Check for alerts
        self._check_alerts(daily_return, max_dd, sharpe_20d, latest_ic, latest_ks)
        
        return DailyPerformanceReport(
            date=today,
            nav=nav,
            daily_return=daily_return,
            cumulative_return=cumulative_return,
            sharpe_20d=sharpe_20d,
            sharpe_60d=sharpe_60d,
            sharpe_252d=sharpe_252d,
            max_drawdown=max_dd,
            rolling_ic=latest_ic,
            ks_drift=latest_ks,
            daily_trades=daily_trades,
            daily_turnover=daily_turnover,
            positions_count=len(self.portfolio.positions)
        )
    
    def _calculate_nav(self, current_prices: Dict[str, float]) -> float:
        """Calculate current NAV from positions and prices"""
        position_value = 0.0
        for symbol, quantity in self.portfolio.positions.items():
            price = current_prices.get(symbol, 0)
            position_value += quantity * price
        
        return self.portfolio.cash + position_value
    
    def calculate_rolling_sharpe(self, window: int) -> float:
        """
        Calculate rolling Sharpe ratio.
        
        Uses annualized returns and volatility.
        Assumes risk-free rate of 0 for simplicity.
        """
        if len(self.returns_history) < window:
            return 0.0
        
        recent_returns = self.returns_history.tail(window)
        
        mean_return = recent_returns.mean()
        std_return = recent_returns.std()
        
        if std_return == 0 or np.isnan(std_return):
            return 0.0
        
        # Annualize
        annualized_return = mean_return * 252
        annualized_vol = std_return * np.sqrt(252)
        
        return annualized_return / annualized_vol
    
    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from peak NAV"""
        if len(self.nav_history) == 0:
            return 0.0
        
        nav_series = self.nav_history
        peak = nav_series.expanding().max()
        drawdown = (peak - nav_series) / peak
        
        return drawdown.max()
    
    def calculate_current_drawdown(self) -> float:
        """Calculate current drawdown from peak NAV"""
        if self.portfolio.peak_nav == 0:
            return 0.0
        return (self.portfolio.peak_nav - self.portfolio.nav) / self.portfolio.peak_nav
    
    def track_ic(
        self,
        predictions: pd.Series,
        actuals: pd.Series,
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Track Information Coefficient (IC).
        
        IC is the correlation between predictions and actual returns.
        Rolling IC is calculated for model quality monitoring.
        
        Args:
            predictions: Predicted returns or scores
            actuals: Actual returns
            timestamp: Optional timestamp for the measurement
        
        Returns:
            Rolling IC value
        """
        timestamp = timestamp or datetime.now()
        
        # Store predictions and actuals
        self.predictions_history = pd.concat([
            self.predictions_history,
            predictions.to_frame().T
        ], ignore_index=True)
        self.actuals_history = pd.concat([
            self.actuals_history,
            actuals.to_frame().T
        ], ignore_index=True)
        
        # Calculate IC for this point
        if len(predictions) > 1:
            point_ic = predictions.corr(actuals)
        else:
            point_ic = np.nan
        
        # Calculate rolling IC
        window = self.config.ic_window
        if len(self.predictions_history) >= window:
            # Get rolling predictions and actuals
            recent_pred = self.predictions_history.tail(window)
            recent_actual = self.actuals_history.tail(window)
            
            # Calculate IC for each column (asset) and average
            ic_values = []
            for col in recent_pred.columns:
                if col in recent_actual.columns:
                    ic = recent_pred[col].corr(recent_actual[col])
                    if not np.isnan(ic):
                        ic_values.append(ic)
            
            rolling_ic = np.mean(ic_values) if ic_values else np.nan
        else:
            rolling_ic = point_ic
        
        # Record IC point
        ic_point = ICPoint(
            timestamp=timestamp,
            ic=rolling_ic,
            num_predictions=len(predictions)
        )
        self.ic_history.append(ic_point)
        
        # Check IC thresholds
        if not np.isnan(rolling_ic):
            if rolling_ic < self.config.ic_critical_threshold:
                self._add_alert("CRITICAL", f"IC ({rolling_ic:.4f}) below critical threshold ({self.config.ic_critical_threshold})")
            elif rolling_ic < self.config.ic_warning_threshold:
                self._add_alert("WARNING", f"IC ({rolling_ic:.4f}) below warning threshold ({self.config.ic_warning_threshold})")
        
        return rolling_ic
    
    def track_ks_drift(
        self,
        current_features: pd.DataFrame,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Track Kolmogorov-Smirnov statistic for concept drift detection.
        
        Compares current feature distribution to training distribution.
        
        Args:
            current_features: Current feature values
            timestamp: Optional timestamp for measurement
        
        Returns:
            Dict mapping feature name to KS statistic
        """
        timestamp = timestamp or datetime.now()
        
        # Store feature history
        self.feature_history = pd.concat([
            self.feature_history,
            current_features.head(1)
        ], ignore_index=True)
        
        if self.training_feature_distribution is None:
            return {}
        
        ks_stats = {}
        for col in current_features.columns:
            if col in self.training_feature_distribution.columns:
                try:
                    ks_stat, _ = scipy_stats.ks_2samp(
                        self.training_feature_distribution[col].dropna(),
                        current_features[col].dropna()
                    )
                    ks_stats[col] = ks_stat
                    
                    # Record KS point
                    ks_point = KSDriftPoint(
                        timestamp=timestamp,
                        ks_statistic=ks_stat,
                        feature_name=col
                    )
                    self.ks_history.append(ks_point)
                    
                    # Check thresholds
                    if ks_stat > self.config.ks_critical_threshold:
                        self._add_alert("CRITICAL", f"KS drift for {col}: {ks_stat:.4f} > {self.config.ks_critical_threshold}")
                    elif ks_stat > self.config.ks_warning_threshold:
                        self._add_alert("WARNING", f"KS drift for {col}: {ks_stat:.4f} > {self.config.ks_warning_threshold}")
                        
                except Exception:
                    pass
        
        return ks_stats
    
    def set_training_distribution(self, features: pd.DataFrame) -> None:
        """Set the training feature distribution for KS drift comparison"""
        self.training_feature_distribution = features.copy()
    
    def _check_alerts(
        self,
        daily_return: float,
        max_dd: float,
        sharpe: float,
        ic: float,
        ks: float
    ) -> None:
        """Check thresholds and generate alerts"""
        # Max drawdown alerts
        if max_dd > self.config.max_drawdown_critical:
            self._add_alert("CRITICAL", f"Max drawdown ({max_dd:.2%}) exceeded critical threshold ({self.config.max_drawdown_critical:.2%})")
        elif max_dd > self.config.max_drawdown_warning:
            self._add_alert("WARNING", f"Max drawdown ({max_dd:.2%}) exceeded warning threshold ({self.config.max_drawdown_warning:.2%})")
        
        # Sharpe ratio alerts
        if sharpe < self.config.min_sharpe_threshold and len(self.returns_history) >= 20:
            self._add_alert("WARNING", f"Rolling Sharpe ({sharpe:.2f}) below minimum threshold ({self.config.min_sharpe_threshold})")
        
        # Large daily loss
        if daily_return < -0.03:  # 3% daily loss
            self._add_alert("WARNING", f"Large daily loss: {daily_return:.2%}")
    
    def _add_alert(self, level: str, message: str) -> None:
        """Add an alert"""
        self.alerts.append({
            "timestamp": datetime.now(),
            "level": level,
            "message": message
        })
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        if len(self.returns_history) == 0:
            return {"status": "No data recorded yet"}
        
        total_return = (self.portfolio.nav / self.portfolio.initial_capital - 1)
        annualized_return = self.returns_history.mean() * 252
        annualized_vol = self.returns_history.std() * np.sqrt(252)
        
        return {
            "trading_days": len(self.date_history),
            "total_return": f"{total_return:.2%}",
            "annualized_return": f"{annualized_return:.2%}",
            "annualized_volatility": f"{annualized_vol:.2%}",
            "sharpe_ratio": f"{annualized_return / annualized_vol:.2f}" if annualized_vol > 0 else "N/A",
            "sharpe_20d": f"{self.calculate_rolling_sharpe(20):.2f}",
            "sharpe_60d": f"{self.calculate_rolling_sharpe(60):.2f}",
            "max_drawdown": f"{self.calculate_max_drawdown():.2%}",
            "current_drawdown": f"{self.calculate_current_drawdown():.2%}",
            "nav": f"${self.portfolio.nav:,.2f}",
            "peak_nav": f"${self.portfolio.peak_nav:,.2f}",
            "realized_pnl": f"${self.portfolio.realized_pnl:,.2f}",
            "alerts_count": len([a for a in self.alerts if a["level"] in ["WARNING", "CRITICAL"]])
        }
    
    def get_ic_trend(self, days: int = 20) -> Dict:
        """Get IC trend over recent days"""
        if len(self.ic_history) == 0:
            return {"status": "No IC data recorded yet"}
        
        recent_ic = self.ic_history[-days:] if len(self.ic_history) >= days else self.ic_history
        
        ic_values = [p.ic for p in recent_ic if not np.isnan(p.ic)]
        
        if not ic_values:
            return {"status": "No valid IC values"}
        
        return {
            "mean_ic": np.mean(ic_values),
            "std_ic": np.std(ic_values),
            "min_ic": np.min(ic_values),
            "max_ic": np.max(ic_values),
            "current_ic": ic_values[-1] if ic_values else np.nan,
            "trend": "DECLINING" if len(ic_values) >= 5 and ic_values[-1] < np.mean(ic_values[:5]) else "STABLE"
        }
    
    def get_ks_drift_summary(self) -> Dict:
        """Get KS drift summary"""
        if len(self.ks_history) == 0:
            return {"status": "No KS drift data recorded yet"}
        
        # Group by feature
        feature_drifts = {}
        for ks_point in self.ks_history[-100:]:  # Last 100 measurements
            if ks_point.feature_name not in feature_drifts:
                feature_drifts[ks_point.feature_name] = []
            feature_drifts[ks_point.feature_name].append(ks_point.ks_statistic)
        
        summary = {}
        for feature, values in feature_drifts.items():
            summary[feature] = {
                "mean_ks": np.mean(values),
                "max_ks": np.max(values),
                "latest_ks": values[-1],
                "drift_level": "CRITICAL" if values[-1] > self.config.ks_critical_threshold else
                              "WARNING" if values[-1] > self.config.ks_warning_threshold else
                              "NORMAL"
            }
        
        return summary
    
    def get_recent_alerts(self, limit: int = 20) -> List[Dict]:
        """Get recent alerts"""
        return self.alerts[-limit:]
