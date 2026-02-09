"""Demo script for Phase 3 functions: Machine Learning Enhancement"""

import os
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.data.provider import DataProvider
from src.factors.momentum import CrossSectionalMomentum
from src.ml.features import FeatureEngineer, FeatureConfig
from src.ml.cpcv import PurgedWalkForwardCV
from src.ml.trainer import MLTrainer, ModelConfig
from src.ml.evaluator import ModelEvaluator
from src.ml.fusion import SignalFusion, FusionConfig
from src.ml.lifecycle import ModelLifecycleManager
from src.utils.logger import logger


def run_phase3_demo():
    """Run Phase 3 ML pipeline demo"""
    load_dotenv()
    
    logger.info("=== Starting Shark Quant Trader Phase 3 Demo (ML Enhancement) ===")
    
    # 1. Load Configuration
    with open("config/strategy.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    ml_config = config['ml']
    
    core_symbols = list(config['core_assets'].keys())
    extended_symbols = [a['symbol'] for a in config['extended_assets']]
    all_symbols = core_symbols + extended_symbols
    
    logger.info(f"Asset universe: {len(all_symbols)} assets")
    
    # 2. Fetch Data
    dp = DataProvider()
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d")
    
    logger.info(f"Fetching data from {start_date} to {end_date}...")
    prices = dp.fetch(all_symbols, start_date, end_date)
    
    if not prices:
        logger.error("Failed to fetch price data")
        return
    
    logger.info(f"Fetched data for {len(prices)} assets")
    
    # 3. Feature Engineering (FR-3.1)
    logger.info("--- Step 1: Feature Engineering ---")
    feature_config = FeatureConfig(
        return_periods=ml_config['features']['return_periods'],
        volatility_periods=ml_config['features']['volatility_periods'],
        ma_periods=ml_config['features']['ma_periods'],
    )
    
    engineer = FeatureEngineer(feature_config)
    features = engineer.create_features(prices)
    
    logger.info(f"Created features: {features.shape}")
    logger.info(f"Feature columns: {list(features.columns)[:10]}...")
    
    # 4. Create Target
    target = engineer.create_target(prices, horizon=5, binary=True)
    
    # Align features and target
    common_idx = features.index.intersection(target.index)
    features = features.loc[common_idx]
    target = target.loc[common_idx]
    
    logger.info(f"Aligned data: {len(features)} samples")
    
    # 5. Feature Selection
    numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
    numeric_features = [c for c in numeric_features if c != 'symbol' and 'target' not in c]
    
    selected_features = engineer.select_features(
        features, target,
        method='ic',
        min_ic=ml_config['features']['min_ic_threshold'],
        max_features=ml_config['features']['max_features']
    )
    
    logger.info(f"Selected {len(selected_features)} features by IC")
    logger.info(f"Top features: {selected_features[:5]}")
    
    # 6. Model Training with Purged Walk-Forward CV (FR-3.2)
    logger.info("--- Step 2: Model Training with Purged Walk-Forward CV ---")
    
    # Create CV splitter
    cv_splitter = PurgedWalkForwardCV(
        train_size=ml_config['training']['train_window'],
        test_size=ml_config['training']['test_window'],
        purge_gap=ml_config['training']['purge_gap'],
        step_size=63
    )
    
    # Configure model
    model_config = ModelConfig(
        model_type=ml_config['training']['model_type'],
        target_type=ml_config['training']['target_type']
    )
    
    trainer = MLTrainer(model_config)
    
    # Train model
    model, metadata = trainer.train(
        features,
        target,
        selected_features,
        cv_splitter=cv_splitter
    )
    
    logger.info(f"Model trained: {metadata.model_id}")
    logger.info(f"CV Scores: {metadata.cv_scores}")
    logger.info(f"Overfitting detected: {metadata.overfitting_detected}")
    
    # 7. Model Evaluation (FR-3.3)
    logger.info("--- Step 3: Model Evaluation ---")
    evaluator = ModelEvaluator()
    
    # Make predictions
    predictions = trainer.predict(features, selected_features)
    predictions = pd.Series(predictions, index=target.index, name='predictions')
    
    # Calculate metrics
    metrics = evaluator.evaluate(target, predictions)
    logger.info(f"Evaluation metrics: {metrics}")
    
    # Rolling IC
    rolling_ic = evaluator.calculate_rolling_ic(target, predictions, window=63)
    last_valid_ic = rolling_ic.dropna().iloc[-1] if not rolling_ic.dropna().empty else 0.0
    logger.info(f"Current rolling IC (63d): {last_valid_ic:.4f}")
    
    # Feature importance
    importance = evaluator.get_feature_importance(model, selected_features)
    logger.info(f"Top 5 important features:")
    for _, row in importance.head(5).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    # SHAP explainability (if available)
    shap_summary = evaluator.explain_with_shap(model, features, selected_features)
    if shap_summary is not None:
        logger.info(f"SHAP analysis completed")
        logger.info(f"Top SHAP feature: {shap_summary.iloc[0]['feature']}")
    
    # 8. Signal Fusion (FR-3.4)
    logger.info("--- Step 4: Signal Fusion ---")
    
    # Generate traditional momentum signal
    cs_momentum = CrossSectionalMomentum()
    momentum_rets = cs_momentum.calculate_momentum_returns(prices)
    
    # Create traditional signal: map each row's symbol to its momentum return
    symbol_col = features['symbol'].values
    trad_signal = pd.Series(
        [momentum_rets.get(s, 0.0) for s in symbol_col],
        index=features.index
    )
    
    # Fuse signals
    fusion_config = FusionConfig(
        ml_max_weight=ml_config['fusion']['ml_max_weight'],
        ic_threshold_for_degradation=ml_config['fusion']['ic_threshold_degradation']
    )
    
    fusion = SignalFusion(fusion_config)
    fused_signal = fusion.fuse(
        predictions,
        trad_signal,
        ml_ic=metrics.get('ic', 0),
        benchmark_ic=0.05
    )
    
    logger.info(f"Signal fusion completed")
    logger.info(f"ML weight: {fusion.get_fusion_stats()['current_ml_weight']:.2%}")
    logger.info(f"Fused signal range: [{fused_signal.min():.3f}, {fused_signal.max():.3f}]")
    
    # 9. Model Lifecycle Management (FR-3.5)
    logger.info("--- Step 5: Model Lifecycle Management ---")
    
    lifecycle = ModelLifecycleManager()
    
    # Check retraining needs
    retrain_needed, reason = lifecycle.check_retrain_needed(
        metrics.get('ic', 0),
        datetime.now()
    )
    logger.info(f"Retrain needed: {retrain_needed} ({reason})")
    
    # Check retirement
    retire_needed, retire_reason = lifecycle.check_retirement_needed()
    logger.info(f"Retire needed: {retire_needed} ({retire_reason})")
    
    # Lifecycle report
    report = lifecycle.get_lifecycle_report()
    logger.info(f"Lifecycle report: {report}")
    
    logger.info("=== Phase 3 Demo Completed ===")
    
    # Summary
    logger.info("\n--- Phase 3 Implementation Summary ---")
    logger.info(f"FR-3.1 Feature Engineering: {len(selected_features)} features created")
    logger.info(f"FR-3.2 Model Training: {metadata.model_type} with Purged Walk-Forward CV")
    logger.info(f"FR-3.3 Model Evaluation: IC={metrics.get('ic', 0):.4f}, AUC={metrics.get('auc', 0):.4f}")
    logger.info(f"FR-3.4 Signal Fusion: ML weight capped at {ml_config['fusion']['ml_max_weight']:.0%}")
    logger.info(f"FR-3.5 Lifecycle: Retrain={retrain_needed}, Retire={retire_needed}")


if __name__ == "__main__":
    run_phase3_demo()
