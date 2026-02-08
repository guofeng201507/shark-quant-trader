"""Asset Rotation Model - PRD FR-2.3"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from .momentum import CrossSectionalMomentum
from ..portfolio.optimizer import PortfolioOptimizer
from ..utils.logger import logger

# Cost model defaults (from config/strategy.yaml)
DEFAULT_ETF_COST = 0.0015   # commission + slippage per trade
DEFAULT_BTC_COST = 0.0025   # commission + slippage per trade

class AssetRotation:
    """
    Implements tactical asset allocation combining momentum and risk parity.
    Based on "Momentum and Markowitz: A Golden Combination" (Keller & Keuning).
    """
    
    def __init__(self, asset_universe: List[str], target_vol: float = 0.15,
                 max_monthly_turnover: float = 0.40,
                 max_monthly_cost: float = 0.002):
        """
        Initialize rotation model.
        
        Args:
            asset_universe: List of all 15 symbols
            target_vol: Portfolio target volatility
            max_monthly_turnover: Max monthly turnover ratio (PRD FR-2.3: 40%)
            max_monthly_cost: Max monthly transaction cost as portfolio fraction (PRD FR-2.3: 0.2%)
        """
        self.asset_universe = asset_universe
        self.momentum = CrossSectionalMomentum()
        self.optimizer = PortfolioOptimizer(target_vol=target_vol)
        self.max_monthly_turnover = max_monthly_turnover
        self.max_monthly_cost = max_monthly_cost
        logger.info(f"AssetRotation initialized with {len(asset_universe)} assets, "
                    f"max_turnover={max_monthly_turnover:.0%}, max_cost={max_monthly_cost:.2%}")

    def calculate_rotation_weights(self, prices: Dict[str, pd.DataFrame], 
                                  sma_200_filter: Dict[str, bool],
                                  current_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Calculate tactical weights based on rotation logic.
        
        Step 1: Rank assets by 12-1 momentum.
        Step 2: Filter Top 30% assets that are above SMA_200.
        Step 3: Apply Risk Parity on the filtered group.
        Step 4: Scale by volatility target.
        Step 5: Apply turnover and cost constraints (PRD FR-2.3).
        
        Returns:
            Dict mapping symbol -> target weight
        """
        current_weights = current_weights or {}
        # 1. Calculate Momentum and Ranks
        momentum_rets = self.momentum.calculate_momentum_returns(prices)
        ranks = self.momentum.rank_assets(momentum_rets)
        
        if ranks.empty:
            logger.warning("No ranks generated, cannot calculate rotation weights")
            return {}
            
        # 2. Filter Top 30% above SMA_200
        top_assets = [s for s, r in ranks.items() if r >= 0.7]
        selected_assets = [s for s in top_assets if sma_200_filter.get(s, False)]
        
        logger.info(f"Selected {len(selected_assets)} assets for rotation: {selected_assets}")
        
        if not selected_assets:
            logger.warning("No assets selected (Trend filter or momentum failed). Entering Safe Haven mode.")
            # Default to GLD and TLT if available, or just cash
            safe_havens = ["GLD", "TLT"]
            selected_assets = [s for s in safe_havens if s in prices]
            if not selected_assets:
                return {} # Cash only
                
        # 3. Prepare returns for selected assets
        returns_data = {}
        for symbol in selected_assets:
            returns_data[symbol] = prices[symbol]['close'].pct_change().dropna()
            
        returns_df = pd.DataFrame(returns_data).dropna()
        
        if returns_df.empty:
            logger.warning("Insufficient overlapping returns data for selected assets")
            return {}
            
        # 4. Optimize weights (Risk Parity)
        raw_weights = self.optimizer.calculate_risk_parity_weights(returns_df)
        
        # 5. Volatility Targeting
        final_weights = self.optimizer.scale_by_vol_target(raw_weights, returns_df)
        
        # 6. Apply turnover and cost constraints (PRD FR-2.3)
        final_weights = self._apply_turnover_constraint(final_weights, current_weights)
        
        return final_weights

    def _apply_turnover_constraint(self, new_weights: Dict[str, float],
                                   current_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Apply PRD FR-2.3 constraints:
        - Monthly turnover < 40%
        - Transaction cost estimate < 0.2%/month
        
        If constraints would be violated, blend old and new weights.
        """
        if not current_weights:
            return new_weights  # First allocation, no turnover
        
        # Calculate proposed turnover
        all_symbols = set(list(new_weights.keys()) + list(current_weights.keys()))
        turnover = sum(
            abs(new_weights.get(s, 0) - current_weights.get(s, 0))
            for s in all_symbols
        ) / 2  # Divide by 2 since buys and sells are symmetric
        
        # Estimate transaction costs
        estimated_cost = 0.0
        for s in all_symbols:
            trade_size = abs(new_weights.get(s, 0) - current_weights.get(s, 0))
            cost_rate = DEFAULT_BTC_COST if 'BTC' in s else DEFAULT_ETF_COST
            estimated_cost += trade_size * cost_rate
        
        logger.info(f"Rotation turnover: {turnover:.1%}, estimated cost: {estimated_cost:.4%}")
        
        # If turnover exceeds limit, blend weights to stay within constraint
        if turnover > self.max_monthly_turnover:
            blend_ratio = self.max_monthly_turnover / turnover
            blended = {}
            for s in all_symbols:
                old_w = current_weights.get(s, 0)
                new_w = new_weights.get(s, 0)
                blended[s] = old_w + blend_ratio * (new_w - old_w)
            logger.warning(f"Turnover {turnover:.1%} exceeds {self.max_monthly_turnover:.0%} limit. "
                          f"Blending weights (ratio={blend_ratio:.2f})")
            new_weights = {s: w for s, w in blended.items() if abs(w) > 1e-6}
            turnover = self.max_monthly_turnover
        
        # If cost exceeds limit, further reduce turnover
        if estimated_cost > self.max_monthly_cost:
            cost_blend = self.max_monthly_cost / estimated_cost
            blended = {}
            for s in all_symbols:
                old_w = current_weights.get(s, 0)
                new_w = new_weights.get(s, 0)
                blended[s] = old_w + cost_blend * (new_w - old_w)
            logger.warning(f"Estimated cost {estimated_cost:.4%} exceeds {self.max_monthly_cost:.2%} limit. "
                          f"Reducing turnover (ratio={cost_blend:.2f})")
            new_weights = {s: w for s, w in blended.items() if abs(w) > 1e-6}
        
        return new_weights
