"""Alert Manager - Multi-channel notifications - Tech Design v1.1 Section 7"""

import os
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime
from ..utils.logger import logger

# Optional: apprise for multi-channel alerts
try:
    import apprise
    APPRISE_AVAILABLE = True
except ImportError:
    APPRISE_AVAILABLE = False
    logger.warning("apprise not installed, alerts will be logged only")


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlertManager:
    """Multi-channel alert notifications"""
    
    def __init__(self):
        """Initialize alert manager"""
        self.apprise_obj = None
        
        if APPRISE_AVAILABLE:
            self.apprise_obj = apprise.Apprise()
            self._setup_channels()
        
        logger.info("AlertManager initialized")
    
    def _setup_channels(self):
        """Setup notification channels from environment variables"""
        
        # Email (SMTP)
        smtp_url = os.getenv("ALERT_SMTP_URL")
        if smtp_url:
            self.apprise_obj.add(smtp_url)
            logger.info("Email alerts configured")
        
        # Slack
        slack_webhook = os.getenv("ALERT_SLACK_WEBHOOK")
        if slack_webhook:
            self.apprise_obj.add(slack_webhook)
            logger.info("Slack alerts configured")
        
        # Telegram
        telegram_token = os.getenv("ALERT_TELEGRAM_TOKEN")
        telegram_chat_id = os.getenv("ALERT_TELEGRAM_CHAT_ID")
        if telegram_token and telegram_chat_id:
            telegram_url = f"tgram://{telegram_token}/{telegram_chat_id}"
            self.apprise_obj.add(telegram_url)
            logger.info("Telegram alerts configured")
        
        # Discord
        discord_webhook = os.getenv("ALERT_DISCORD_WEBHOOK")
        if discord_webhook:
            self.apprise_obj.add(discord_webhook)
            logger.info("Discord alerts configured")
        
        if len(self.apprise_obj) == 0:
            logger.warning("No alert channels configured")
    
    def send_alert(self, level: AlertLevel, title: str, message: str,
                   channels: Optional[List[str]] = None) -> bool:
        """
        Send alert notification.
        
        Args:
            level: Alert severity level
            title: Alert title
            message: Alert message body
            channels: Optional list of specific channels to use
            
        Returns:
            True if alert sent successfully
        """
        # Format message with timestamp and level
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {level.value}\n\n{message}"
        
        # Log alert
        if level == AlertLevel.EMERGENCY or level == AlertLevel.CRITICAL:
            logger.critical(f"{title}: {message}")
        elif level == AlertLevel.WARNING:
            logger.warning(f"{title}: {message}")
        else:
            logger.info(f"{title}: {message}")
        
        # Send via apprise if available
        if APPRISE_AVAILABLE and self.apprise_obj and len(self.apprise_obj) > 0:
            try:
                # Determine notification type based on level
                if level == AlertLevel.EMERGENCY or level == AlertLevel.CRITICAL:
                    notify_type = apprise.NotifyType.FAILURE
                elif level == AlertLevel.WARNING:
                    notify_type = apprise.NotifyType.WARNING
                else:
                    notify_type = apprise.NotifyType.INFO
                
                # Send notification
                success = self.apprise_obj.notify(
                    body=formatted_message,
                    title=title,
                    notify_type=notify_type
                )
                
                if success:
                    logger.debug(f"Alert sent successfully: {title}")
                else:
                    logger.error(f"Failed to send alert: {title}")
                
                return success
                
            except Exception as e:
                logger.error(f"Error sending alert: {e}")
                return False
        
        return True  # Return True if only logging
    
    def alert_risk_level_change(self, old_level: int, new_level: int,
                               drawdown: float) -> bool:
        """Send alert for risk level change"""
        
        if new_level > old_level:
            level = AlertLevel.CRITICAL if new_level >= 3 else AlertLevel.WARNING
        else:
            level = AlertLevel.INFO
        
        title = f"Risk Level Changed: {old_level} → {new_level}"
        message = f"Portfolio drawdown: {drawdown:.2%}\n"
        message += f"New risk level: {new_level}\n"
        message += f"Immediate action may be required."
        
        return self.send_alert(level, title, message)
    
    def alert_position_stop_loss(self, symbol: str, entry_price: float,
                                 current_price: float, action: str) -> bool:
        """Send alert for position stop loss"""
        
        drawdown = (entry_price - current_price) / entry_price
        
        title = f"Stop Loss Triggered: {symbol}"
        message = f"Symbol: {symbol}\n"
        message += f"Entry Price: ${entry_price:.2f}\n"
        message += f"Current Price: ${current_price:.2f}\n"
        message += f"Drawdown: {drawdown:.2%}\n"
        message += f"Action: {action}"
        
        return self.send_alert(AlertLevel.WARNING, title, message)
    
    def alert_correlation_breach(self, avg_correlation: float,
                                threshold: float, pairs: List = None) -> bool:
        """Send alert for correlation threshold breach"""
        
        title = "Correlation Threshold Breach"
        message = f"Portfolio average correlation: {avg_correlation:.2%}\n"
        message += f"Threshold: {threshold:.2%}\n"
        
        if pairs:
            message += f"\nHigh correlation pairs ({len(pairs)}):\n"
            for asset1, asset2, corr in pairs[:5]:  # Show top 5
                message += f"  {asset1} - {asset2}: {corr:.2%}\n"
        
        level = AlertLevel.CRITICAL if avg_correlation > 0.8 else AlertLevel.WARNING
        return self.send_alert(level, title, message)
    
    def alert_data_quality_issue(self, symbol: str, issues: Dict) -> bool:
        """Send alert for data quality problems"""
        
        title = f"Data Quality Issue: {symbol}"
        message = f"Symbol: {symbol}\n"
        
        if issues.get("missing_data_pct", 0) > 0:
            message += f"Missing data: {issues['missing_data_pct']:.1%}\n"
        
        if issues.get("price_jumps", 0) > 0:
            message += f"Price jumps detected: {issues['price_jumps']}\n"
        
        if issues.get("volume_issues", 0) > 0:
            message += f"Volume issues: {issues['volume_issues']}\n"
        
        return self.send_alert(AlertLevel.WARNING, title, message)
    
    def alert_execution_failure(self, order_details: str, error: str) -> bool:
        """Send alert for order execution failure"""
        
        title = "Order Execution Failed"
        message = f"Order: {order_details}\n"
        message += f"Error: {error}\n"
        message += f"Manual intervention may be required."
        
        return self.send_alert(AlertLevel.CRITICAL, title, message)
    
    def alert_compliance_violation(self, violations: List[str]) -> bool:
        """Send alert for compliance violations"""
        
        title = "Compliance Violation Detected"
        message = "The following violations were detected:\n\n"
        message += "\n".join(f"- {v}" for v in violations)
        message += "\n\nImmediate review required."
        
        return self.send_alert(AlertLevel.CRITICAL, title, message)
    
    def alert_daily_summary(self, portfolio_nav: float, daily_pnl: float,
                           num_trades: int, top_performers: List = None) -> bool:
        """Send daily performance summary"""
        
        title = "Daily Trading Summary"
        message = f"Portfolio NAV: ${portfolio_nav:,.2f}\n"
        message += f"Daily P&L: ${daily_pnl:,.2f} ({daily_pnl/portfolio_nav:.2%})\n"
        message += f"Trades executed: {num_trades}\n"
        
        if top_performers:
            message += f"\nTop performers:\n"
            for symbol, pnl in top_performers[:3]:
                message += f"  {symbol}: ${pnl:,.2f}\n"
        
        return self.send_alert(AlertLevel.INFO, title, message)
    
    def alert_emergency_liquidation(self, portfolio_nav: float,
                                   drawdown: float) -> bool:
        """Send emergency alert for Level 4 liquidation"""
        
        title = "🚨 EMERGENCY LIQUIDATION TRIGGERED"
        message = f"Level 4 risk control activated!\n\n"
        message += f"Portfolio NAV: ${portfolio_nav:,.2f}\n"
        message += f"Drawdown: {drawdown:.2%}\n"
        message += f"All positions being liquidated.\n"
        message += f"Manual confirmation required to resume trading."
        
        return self.send_alert(AlertLevel.EMERGENCY, title, message)