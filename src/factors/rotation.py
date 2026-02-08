"""Asset Rotation Model - PRD FR-2.3"""

import pandas as pd
from typing import Dict, List, Optional
from .momentum import CrossSectionalMomentum
from ..portfolio.optimizer import PortfolioOptimizer
from ..utils.logger import logger

class AssetRotation:
    """
    Implements tactical asset allocation combining momentum and risk parity.
    Based on "Momentum and Markowitz: A Golden Combination" (Keller & Keuning).
    """
    
    def __init__(self, asset_universe: List[str], target_vol: float = 0.15):
        """
        Initialize rotation model.
        
        Args:
            asset_universe: List of all 15 symbols
            target_vol: Portfolio target volatility
        """
        self.asset_universe = asset_universe
        self.momentum = CrossSectionalMomentum()
        self.optimizer = PortfolioOptimizer(target_vol=target_vol)
        logger.info(f"AssetRotation initialized with {len(asset_universe)} assets")

    def calculate_rotation_weights(self, prices: Dict[str, pd.DataFrame], 
                                  sma_200_filter: Dict[str, bool]) -> Dict[str, float]:
        """
        Calculate tactical weights based on rotation logic.
        
        Step 1: Rank assets by 12-1 momentum.
        Step 2: Filter Top 30% assets that are above SMA_200.
        Step 3: Apply Risk Parity on the filtered group.
        Step 4: Scale by volatility target.
        
        Returns:
            Dict mapping symbol -> target weight
        """
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
        
        return final_weights
