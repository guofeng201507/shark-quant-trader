"""Signal Fusion Module - PRD FR-3.4

Combines ML predictions with traditional signals using weighted averaging.
Ensures ML never fully overrides traditional signals (max 50% weight).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..utils.logger import logger


@dataclass
class FusionConfig:
    """Configuration for signal fusion"""
    ml_max_weight: float = 0.5       # ML weight cap (PRD: max 50%)
    traditional_min_weight: float = 0.5  # Traditional signal minimum (PRD: min 50%)
    ic_threshold_for_degradation: float = 0.02  # PRD: IC < 0.02 for 20 days -> weight 0
    disagreement_threshold: float = 0.3  # Reduce confidence when models disagree
    rolling_window: int = 20         # Window for rolling IC calculation


class SignalFusion:
    """
    Fusion of ML and traditional signals.
    
    FR-3.4 Requirements:
    - Weighted average by rolling IC
    - Voting mechanism for high disagreement
    - Dynamic weight: ML weight = min(0.5, rolling_IC / benchmark_IC)
    - ML never fully covers traditional (max 50%, min 50% traditional)
    - Auto-degradation: IC < 0.02 for 20 days -> ML weight to 0
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        self.ml_ic_history: List[float] = []
        self.fusion_history: List[Dict] = []
        
        logger.info(f"SignalFusion initialized: ml_max_weight={self.config.ml_max_weight}")
    
    def fuse(self,
            ml_signal: pd.Series,
            traditional_signal: pd.Series,
            ml_ic: Optional[float] = None,
            benchmark_ic: float = 0.05) -> pd.Series:
        """
        Fuse ML and traditional signals.
        
        Args:
            ml_signal: ML model predictions (normalized to [-1, 1] or [0, 1])
            traditional_signal: Traditional factor signals
            ml_ic: Current ML model IC (for dynamic weighting)
            benchmark_ic: Benchmark IC for weight calculation
            
        Returns:
            Fused signal series
        """
        # Store IC history
        if ml_ic is not None:
            self.ml_ic_history.append(ml_ic)
            self.ml_ic_history = self.ml_ic_history[-self.config.rolling_window:]
        
        # Calculate ML weight
        ml_weight = self._calculate_ml_weight(benchmark_ic)
        traditional_weight = 1 - ml_weight
        
        # Check for disagreement
        disagreement = self._calculate_disagreement(ml_signal, traditional_signal)
        confidence = 1.0 if disagreement < self.config.disagreement_threshold else 0.5
        
        # Normalize signals to same scale
        ml_norm = self._normalize_signal(ml_signal)
        trad_norm = self._normalize_signal(traditional_signal)
        
        # Weighted fusion
        fused = ml_weight * ml_norm + traditional_weight * trad_norm
        
        # Apply confidence adjustment for high disagreement
        if confidence < 1.0:
            # Reduce signal strength when models disagree
            fused = fused * confidence
            logger.warning(f"High signal disagreement ({disagreement:.2f}), reducing confidence")
        
        # Record fusion
        self.fusion_history.append({
            'ml_weight': ml_weight,
            'traditional_weight': traditional_weight,
            'disagreement': disagreement,
            'confidence': confidence,
        })
        
        logger.info(f"Signal fused: ML weight={ml_weight:.2%}, disagreement={disagreement:.2f}")
        
        return fused
    
    def _calculate_ml_weight(self, benchmark_ic: float) -> float:
        """
        Calculate ML weight based on rolling IC.
        
        FR-3.4: ML weight = min(0.5, rolling_IC / benchmark_IC)
        Auto-degradation: IC < 0.02 for 20 days -> weight 0
        """
        # Check for auto-degradation condition
        if len(self.ml_ic_history) >= self.config.rolling_window:
            recent_ics = self.ml_ic_history[-self.config.rolling_window:]
            avg_ic = np.mean(recent_ics)
            
            # Auto-degradation: IC < 0.02 for 20 consecutive days
            if all(ic < self.config.ic_threshold_for_degradation for ic in recent_ics):
                logger.warning(f"ML auto-degradation triggered: IC < {self.config.ic_threshold_for_degradation} for {self.config.rolling_window} days")
                return 0.0
        
        # Calculate dynamic weight
        if not self.ml_ic_history:
            # No history, use minimum weight
            return 0.2
        
        rolling_ic = np.mean(self.ml_ic_history[-self.config.rolling_window:])
        
        if benchmark_ic > 0:
            dynamic_weight = rolling_ic / benchmark_ic
        else:
            dynamic_weight = 0.0
        
        # Apply caps
        ml_weight = min(dynamic_weight, self.config.ml_max_weight)
        ml_weight = max(ml_weight, 0.0)  # No negative weight
        
        return ml_weight
    
    def _calculate_disagreement(self, 
                               ml_signal: pd.Series,
                               traditional_signal: pd.Series) -> float:
        """
        Calculate signal disagreement.
        
        Returns proportion of predictions where signs differ.
        """
        ml_sign = np.sign(ml_signal - ml_signal.median())
        trad_sign = np.sign(traditional_signal - traditional_signal.median())
        
        disagreement = (ml_sign != trad_sign).mean()
        return disagreement
    
    def _normalize_signal(self, signal: pd.Series) -> pd.Series:
        """Normalize signal to [-1, 1] range"""
        if signal.std() == 0:
            return pd.Series(0, index=signal.index)
        
        # Z-score then clip
        normalized = (signal - signal.mean()) / signal.std()
        normalized = normalized.clip(-3, 3) / 3  # Scale to [-1, 1]
        
        return normalized
    
    def get_fusion_stats(self) -> Dict:
        """Get fusion statistics"""
        if not self.fusion_history:
            return {}
        
        recent = self.fusion_history[-100:]  # Last 100 fusions
        
        return {
            'avg_ml_weight': np.mean([f['ml_weight'] for f in recent]),
            'avg_disagreement': np.mean([f['disagreement'] for f in recent]),
            'degradation_events': sum(1 for f in recent if f['ml_weight'] == 0),
            'current_ml_weight': recent[-1]['ml_weight'] if recent else 0,
        }
