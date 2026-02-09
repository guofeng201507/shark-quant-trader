"""ML Model Training Module - PRD FR-3.2

Implements XGBoost/LightGBM training with overfitting-resistant validation.
Supports Purged Walk-Forward and CPCV validation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
import pickle
from pathlib import Path
from datetime import datetime

from ..utils.logger import logger

# ML libraries
import xgboost as xgb
import lightgbm as lgb
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


@dataclass
class ModelConfig:
    """Configuration for ML model"""
    model_type: str = 'xgboost'  # 'xgboost', 'lightgbm', 'ridge'
    target_type: str = 'binary'  # 'binary', 'regression'
    
    # XGBoost params
    xgb_params: Dict = field(default_factory=lambda: {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 5,
        'learning_rate': 0.05,
        'n_estimators': 100,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'random_state': 42,
    })
    
    # LightGBM params
    lgb_params: Dict = field(default_factory=lambda: {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'random_state': 42,
    })
    
    # Ridge params
    ridge_params: Dict = field(default_factory=lambda: {
        'alpha': 1.0,
        'random_state': 42,
    })


@dataclass
class TrainingMetadata:
    """Metadata for trained model"""
    model_id: str
    model_type: str
    training_date: str
    data_start: str
    data_end: str
    n_samples: int
    n_features: int
    features: List[str]
    cv_method: str
    cv_scores: Dict[str, float]
    overfitting_detected: bool
    
    def to_dict(self) -> Dict:
        return {
            'model_id': self.model_id,
            'model_type': self.model_type,
            'training_date': self.training_date,
            'data_start': self.data_start,
            'data_end': self.data_end,
            'n_samples': self.n_samples,
            'n_features': self.n_features,
            'features': self.features,
            'cv_method': self.cv_method,
            'cv_scores': self.cv_scores,
            'overfitting_detected': self.overfitting_detected,
        }
    
    def save(self, path: str):
        """Save metadata to JSON"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class MLTrainer:
    """
    Overfitting-resistant model training framework.
    
    FR-3.2 Requirements:
    - Support XGBoost, LightGBM, Ridge
    - Purged Walk-Forward and CPCV validation
    - Overfitting detection (Sharpe diff > 0.5, IC < 0.03)
    - Model versioning with metadata
    """
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model = None
        self.scaler = StandardScaler()
        self.metadata: Optional[TrainingMetadata] = None
        
        logger.info(f"MLTrainer initialized: {self.config.model_type}")
    
    def train(self, 
             X: pd.DataFrame,
             y: pd.Series,
             feature_cols: List[str],
             cv_splitter=None) -> Tuple[Any, TrainingMetadata]:
        """
        Train model with cross-validation.
        
        Args:
            X: Feature matrix
            y: Target variable
            feature_cols: List of feature column names
            cv_splitter: Cross-validation splitter (CPCV or PurgedWalkForward)
            
        Returns:
            Tuple of (trained_model, metadata)
        """
        # Prepare data
        X_train = X[feature_cols].fillna(0)
        y_train = y
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_train)
        X_scaled = pd.DataFrame(X_scaled, index=X_train.index, columns=X_train.columns)
        
        # Cross-validation training
        if cv_splitter is not None:
            cv_scores = self._cross_validate(X_scaled, y_train, cv_splitter)
        else:
            cv_scores = {}
        
        # Train final model on all data
        self.model = self._create_model()
        self.model.fit(X_scaled, y_train)
        
        # Detect overfitting
        overfitting = self._detect_overfitting(cv_scores)
        
        # Create metadata
        model_id = f"{self.config.model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.metadata = TrainingMetadata(
            model_id=model_id,
            model_type=self.config.model_type,
            training_date=datetime.now().isoformat(),
            data_start=str(X.index.min()),
            data_end=str(X.index.max()),
            n_samples=len(X),
            n_features=len(feature_cols),
            features=feature_cols,
            cv_method=cv_splitter.__class__.__name__ if cv_splitter else 'none',
            cv_scores=cv_scores,
            overfitting_detected=overfitting,
        )
        
        logger.info(f"Model trained: {model_id}, overfitting={overfitting}")
        
        return self.model, self.metadata
    
    def _create_model(self):
        """Create model instance based on config"""
        if self.config.model_type == 'xgboost':
            if self.config.target_type == 'binary':
                params = self.config.xgb_params.copy()
                return xgb.XGBClassifier(**params)
            else:
                params = self.config.xgb_params.copy()
                params['objective'] = 'reg:squarederror'
                params['eval_metric'] = 'rmse'
                return xgb.XGBRegressor(**params)
        
        elif self.config.model_type == 'lightgbm':
            if self.config.target_type == 'binary':
                return lgb.LGBMClassifier(**self.config.lgb_params)
            else:
                params = self.config.lgb_params.copy()
                params['objective'] = 'regression'
                return lgb.LGBMRegressor(**params)
        
        elif self.config.model_type == 'ridge':
            return Ridge(**self.config.ridge_params)
        
        else:
            raise ValueError(f"Unknown model type: {self.config.model_type}")
    
    def _cross_validate(self, X: pd.DataFrame, y: pd.Series, cv_splitter) -> Dict[str, float]:
        """
        Perform cross-validation and return scores.
        
        FR-3.2: Calculate IC, AUC, and other metrics per fold
        """
        from sklearn.metrics import roc_auc_score, accuracy_score
        
        scores = {
            'ic': [],
            'auc': [],
            'accuracy': [],
        }
        
        for fold_idx, (train_idx, val_idx) in enumerate(cv_splitter.split(X, y)):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            if len(y_tr) < 100 or len(y_val) < 10:
                continue
            
            # Train fold model
            model = self._create_model()
            model.fit(X_tr, y_tr)
            
            # Predict
            if hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_val)[:, 1]
                y_pred = model.predict(X_val)
                
                # AUC
                try:
                    auc = roc_auc_score(y_val, y_pred_proba)
                    scores['auc'].append(auc)
                except:
                    pass
                
                # Accuracy
                acc = accuracy_score(y_val, y_pred)
                scores['accuracy'].append(acc)
            else:
                y_pred = model.predict(X_val)
            
            # Information Coefficient (IC)
            ic = np.corrcoef(y_val, y_pred)[0, 1] if len(y_val) > 1 else 0
            if not np.isnan(ic):
                scores['ic'].append(ic)
        
        # Aggregate scores
        result = {}
        for metric, values in scores.items():
            if values:
                result[f'{metric}_mean'] = np.mean(values)
                result[f'{metric}_std'] = np.std(values)
        
        return result
    
    def _detect_overfitting(self, cv_scores: Dict[str, float]) -> bool:
        """
        Detect overfitting based on CV scores.
        
        FR-3.2 Criteria:
        - Train vs Val Sharpe diff > 0.5
        - Val IC < 0.03
        """
        overfitting = False
        
        # Check IC threshold
        ic_mean = cv_scores.get('ic_mean', 0)
        if ic_mean < 0.03:
            logger.warning(f"Low IC detected: {ic_mean:.4f} < 0.03")
            overfitting = True
        
        # Check IC stability (high variance indicates instability)
        ic_std = cv_scores.get('ic_std', 0)
        if ic_std > 0.1:
            logger.warning(f"Unstable IC detected: std={ic_std:.4f}")
            overfitting = True
        
        return overfitting
    
    def predict(self, X: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        X_input = X[feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X_input)
        
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X_scaled)[:, 1]
        return self.model.predict(X_scaled)
    
    def save(self, path: str):
        """Save model and metadata"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = path / f"{self.metadata.model_id}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'config': self.config,
            }, f)
        
        # Save metadata
        meta_path = path / f"{self.metadata.model_id}.json"
        self.metadata.save(meta_path)
        
        logger.info(f"Model saved to {path}")
    
    def load(self, model_path: str):
        """Load model and metadata"""
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.scaler = data['scaler']
        self.config = data['config']
        
        # Load metadata
        meta_path = model_path.replace('.pkl', '.json')
        with open(meta_path, 'r') as f:
            meta_dict = json.load(f)
        
        self.metadata = TrainingMetadata(**meta_dict)
        
        logger.info(f"Model loaded: {self.metadata.model_id}")
