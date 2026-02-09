"""Machine Learning Module - Phase 3

Implements ML-enhanced trading signals with overfitting-resistant validation.
"""

from .features import FeatureEngineer, FeatureConfig
from .cpcv import CombinatorialPurgedCV, PurgedWalkForwardCV, create_time_series_split
from .trainer import MLTrainer, ModelConfig, TrainingMetadata
from .evaluator import ModelEvaluator
from .fusion import SignalFusion, FusionConfig
from .lifecycle import ModelLifecycleManager, LifecycleConfig

__all__ = [
    # Feature Engineering (FR-3.1)
    "FeatureEngineer",
    "FeatureConfig",
    
    # Cross-Validation (FR-3.2)
    "CombinatorialPurgedCV",
    "PurgedWalkForwardCV",
    "create_time_series_split",
    
    # Model Training (FR-3.2)
    "MLTrainer",
    "ModelConfig",
    "TrainingMetadata",
    
    # Evaluation (FR-3.3)
    "ModelEvaluator",
    
    # Signal Fusion (FR-3.4)
    "SignalFusion",
    "FusionConfig",
    
    # Lifecycle Management (FR-3.5)
    "ModelLifecycleManager",
    "LifecycleConfig",
]
