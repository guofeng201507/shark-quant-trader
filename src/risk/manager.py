"""Risk Manager - 4-level hierarchical risk control - Tech Design v1.1 Section 4.3.3"""

import pandas as pd
from typing import Dict, List, Optional
from ..models.domain import Portfolio, RiskAssessment, Order
from ..utils.logger import logger


class RiskManager:
    """4-level hierarchical risk control system with correlation monitoring"""
    
    # Portfolio-level drawdown triggers (from Tech Design)
    LEVELS = {
        0: {"drawdown": 0.00, "actions": []},
        1: {"drawdown": 0.05, "actions": ["ALERT", "INCREASE_CONFIDENCE_THRESHOLD", "BLOCK_BTC_NEW"]},
        2: {"drawdown": 0.08, "actions": ["REDUCE_25%", "CLOSE_BTC", "SELL_ONLY"]},
        3: {"drawdown": 0.12, "actions": ["REDUCE_50%", "SAFE_HAVEN_ONLY", "MANUAL_REVIEW"]},
        4: {"drawdown": 0.15, "actions": ["EMERGENCY_LIQUIDATION", "REQUIRE_MANUAL_CONFIRM"]}
    }
    
    # Single asset stop loss
    ASSET_STOPS = {
        "drawdown_reduce": 0.12,  # Reduce to 50%
        "drawdown_exit": 0.18     # Full exit
    }
    
    # Correlation thresholds
    CORRELATION = {
        "pair_warning": 0.7,       # Single asset pair
        "portfolio_warning": 0.5,   # Portfolio average
        "extreme_threshold": 0.8    # All assets same direction
    }
    
    def __init__(self):
        """Initialize risk manager"""
        self.current_level = 0
        logger.info("RiskManager initialized")
    
    def check(self, portfolio: Portfolio) -> RiskAssessment:
        """
        Assess current risk state.
        
        Args:
            portfolio: Current portfolio state
            
        Returns:
            RiskAssessment with risk level and violations
        """
        # Calculate drawdown
        drawdown = portfolio.calculate_drawdown()
        
        # Determine risk level
        level = self.assess_risk_level(portfolio)
        
        # Check for violations
        violations = []
        
        # Check if level changed
        if level != self.current_level:
            logger.warning(f"Risk level changed: {self.current_level} -> {level}")
            violations.append(f"Risk level escalated to {level}")
            self.current_level = level
        
        # Check single asset stops
        for symbol, position in portfolio.positions.items():
            if position > 0:
                cost_basis = portfolio.cost_basis.get(symbol, 0)
                if cost_basis > 0:
                    # Calculate asset drawdown (would need current price)
                    # This is a placeholder - actual implementation needs price data
                    pass
        
        assessment = RiskAssessment(
            level=level,
            portfolio_drawdown=drawdown,
            violations=violations
        )
        
        logger.info(f"Risk assessment: Level {level}, Drawdown {drawdown:.2%}")
        return assessment
    
    def assess_risk_level(self, portfolio: Portfolio) -> int:
        """
        Determine current risk level based on drawdown from peak NAV.
        
        Args:
            portfolio: Current portfolio state
            
        Returns:
            Risk level (0-4)
        """
        drawdown = portfolio.calculate_drawdown()
        
        # Determine level based on drawdown thresholds
        for level in sorted(self.LEVELS.keys(), reverse=True):
            if drawdown >= self.LEVELS[level]["drawdown"]:
                return level
        
        return 0
    
    def apply_controls(self, level: int, portfolio: Portfolio) -> List[str]:
        """
        Apply risk controls for given level.
        
        Args:
            level: Risk level (0-4)
            portfolio: Current portfolio
            
        Returns:
            List of actions to take
        """
        if level not in self.LEVELS:
            logger.error(f"Invalid risk level: {level}")
            return []
        
        actions = self.LEVELS[level]["actions"]
        logger.warning(f"Applying Level {level} risk controls: {actions}")
        
        return actions
    
    def check_single_asset_stop(self, symbol: str, entry_price: float,
                                current_price: float) -> Optional[str]:
        """
        Check if single asset stop loss triggered.
        
        Args:
            symbol: Asset symbol
            entry_price: Entry/cost basis price
            current_price: Current market price
            
        Returns:
            Action to take: "EXIT", "REDUCE_50%", or None
        """
        if entry_price == 0:
            return None
        
        drawdown = (entry_price - current_price) / entry_price
        
        if drawdown > self.ASSET_STOPS["drawdown_exit"]:
            logger.critical(f"{symbol} stop loss triggered: {drawdown:.2%} > {self.ASSET_STOPS['drawdown_exit']:.2%}")
            return "EXIT"
        elif drawdown > self.ASSET_STOPS["drawdown_reduce"]:
            logger.warning(f"{symbol} partial stop loss: {drawdown:.2%} > {self.ASSET_STOPS['drawdown_reduce']:.2%}")
            return "REDUCE_50%"
        
        return None
    
    def get_risk_level(self) -> int:
        """Get current risk level"""
        return self.current_level
    
    def should_block_new_positions(self) -> bool:
        """Check if new positions should be blocked"""
        return self.current_level >= 2
    
    def should_sell_only(self) -> bool:
        """Check if only sell orders are allowed"""
        return self.current_level >= 2
    
    def get_position_reduction_factor(self) -> float:
        """
        Get position reduction factor based on current risk level.
        
        Returns:
            Factor to multiply positions by (0.0 to 1.0)
        """
        if self.current_level == 0 or self.current_level == 1:
            return 1.0
        elif self.current_level == 2:
            return 0.75  # Reduce by 25%
        elif self.current_level == 3:
            return 0.50  # Reduce by 50%
        else:  # Level 4
            return 0.0   # Emergency liquidation
    
    def is_safe_haven_asset(self, symbol: str) -> bool:
        """
        Check if asset is considered safe haven.
        Safe haven assets: GLD, TLT
        """
        return symbol in ["GLD", "TLT"]