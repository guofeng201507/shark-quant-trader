"""Compliance Checker - Tech Design v1.1 Section 6"""

from typing import List, Dict, Optional
from ..models.domain import Order, Portfolio
from ..utils.logger import logger


class ComplianceChecker:
    """Pre-trade and post-trade compliance checks"""
    
    # Compliance rules from Tech Design
    RULES = {
        "max_position_concentration": 0.50,  # Max 50% in single asset (GLD)
        "max_leverage": 1.5,                 # Max 1.5x leverage
        "min_cash_buffer": 0.05,             # Min 5% cash
        "max_daily_trades": 5,
        "max_daily_turnover": 0.30,
        "blacklist": [],                     # Can add restricted symbols
        "trading_hours_only": False          # Phase 1 allows 24/7 for BTC
    }
    
    def __init__(self):
        """Initialize compliance checker"""
        logger.info("ComplianceChecker initialized")
    
    def check_pre_trade(self, order: Order, portfolio: Portfolio,
                       prices: Dict[str, float]) -> tuple[bool, Optional[str]]:
        """
        Pre-trade compliance checks.
        
        Args:
            order: Order to check
            portfolio: Current portfolio state
            prices: Current market prices
            
        Returns:
            (is_compliant, violation_reason)
        """
        # Check if symbol is blacklisted
        if order.symbol in self.RULES["blacklist"]:
            return False, f"Symbol {order.symbol} is blacklisted"
        
        # Check position concentration after trade
        if order.side == "BUY":
            if not self._check_concentration_limit(order, portfolio, prices):
                return False, f"Position concentration would exceed {self.RULES['max_position_concentration']:.0%}"
        
        # Check leverage limit
        if not self._check_leverage_limit(order, portfolio, prices):
            return False, f"Leverage would exceed {self.RULES['max_leverage']:.1f}x"
        
        # Check cash buffer
        if order.side == "BUY":
            if not self._check_cash_buffer(order, portfolio, prices):
                return False, f"Insufficient cash buffer (min {self.RULES['min_cash_buffer']:.0%})"
        
        # All checks passed
        return True, None
    
    def check_post_trade(self, portfolio: Portfolio) -> List[str]:
        """
        Post-trade compliance checks.
        
        Args:
            portfolio: Portfolio state after trade execution
            
        Returns:
            List of violation messages (empty if compliant)
        """
        violations = []
        
        # Check leverage
        leverage = self._calculate_leverage(portfolio)
        if leverage > self.RULES["max_leverage"]:
            violations.append(f"Leverage {leverage:.2f}x exceeds limit {self.RULES['max_leverage']:.1f}x")
        
        # Check cash buffer
        cash_ratio = portfolio.cash / portfolio.nav if portfolio.nav > 0 else 0
        if cash_ratio < self.RULES["min_cash_buffer"]:
            violations.append(f"Cash buffer {cash_ratio:.1%} below minimum {self.RULES['min_cash_buffer']:.0%}")
        
        # Check position concentration
        for symbol, weight in portfolio.weights.items():
            if weight > self.RULES["max_position_concentration"]:
                violations.append(f"{symbol} weight {weight:.1%} exceeds {self.RULES['max_position_concentration']:.0%}")
        
        if violations:
            logger.warning(f"Post-trade violations: {violations}")
        else:
            logger.debug("Post-trade compliance: PASS")
        
        return violations
    
    def _check_concentration_limit(self, order: Order, portfolio: Portfolio,
                                   prices: Dict[str, float]) -> bool:
        """Check if order would violate position concentration limit"""
        
        if order.symbol not in prices:
            return True  # Can't check without price
        
        # Calculate position value after trade
        current_qty = portfolio.positions.get(order.symbol, 0.0)
        
        if order.side == "BUY":
            new_qty = current_qty + order.quantity
        else:
            new_qty = current_qty - order.quantity
        
        new_value = new_qty * prices[order.symbol]
        
        # Calculate new NAV (approximate)
        order_cost = order.quantity * prices[order.symbol]
        if order.side == "BUY":
            new_nav = portfolio.nav  # Buying doesn't change NAV (cash -> position)
        else:
            new_nav = portfolio.nav  # Selling doesn't change NAV (position -> cash)
        
        if new_nav == 0:
            return False
        
        new_weight = new_value / new_nav
        
        # Check against limit
        return new_weight <= self.RULES["max_position_concentration"]
    
    def _check_leverage_limit(self, order: Order, portfolio: Portfolio,
                             prices: Dict[str, float]) -> bool:
        """Check if order would violate leverage limit"""
        
        # Calculate total position value after trade
        total_position_value = sum(
            qty * prices.get(symbol, 0)
            for symbol, qty in portfolio.positions.items()
        )
        
        # Adjust for order
        if order.symbol in prices:
            order_value = order.quantity * prices[order.symbol]
            if order.side == "BUY":
                total_position_value += order_value
            else:
                total_position_value -= order_value
        
        # Calculate leverage
        if portfolio.nav > 0:
            leverage = total_position_value / portfolio.nav
            return leverage <= self.RULES["max_leverage"]
        
        return True
    
    def _check_cash_buffer(self, order: Order, portfolio: Portfolio,
                          prices: Dict[str, float]) -> bool:
        """Check if order would violate minimum cash buffer"""
        
        if order.side != "BUY":
            return True  # Selling increases cash
        
        if order.symbol not in prices:
            return True
        
        # Calculate cash after trade
        order_cost = order.quantity * prices[order.symbol]
        new_cash = portfolio.cash - order_cost
        
        if new_cash < 0:
            return False  # Not enough cash
        
        # Check cash buffer
        if portfolio.nav > 0:
            cash_ratio = new_cash / portfolio.nav
            return cash_ratio >= self.RULES["min_cash_buffer"]
        
        return True
    
    def _calculate_leverage(self, portfolio: Portfolio) -> float:
        """Calculate current portfolio leverage"""
        
        if portfolio.nav == 0:
            return 0.0
        
        # Total position value
        position_value = portfolio.nav - portfolio.cash
        
        # Leverage = position value / NAV
        leverage = position_value / portfolio.nav
        
        return leverage
    
    def check_daily_limits(self, num_trades: int, turnover: float) -> tuple[bool, Optional[str]]:
        """
        Check daily trading limits.
        
        Args:
            num_trades: Number of trades today
            turnover: Portfolio turnover today
            
        Returns:
            (is_compliant, violation_reason)
        """
        if num_trades > self.RULES["max_daily_trades"]:
            return False, f"Daily trade limit exceeded: {num_trades} > {self.RULES['max_daily_trades']}"
        
        if turnover > self.RULES["max_daily_turnover"]:
            return False, f"Daily turnover limit exceeded: {turnover:.1%} > {self.RULES['max_daily_turnover']:.0%}"
        
        return True, None