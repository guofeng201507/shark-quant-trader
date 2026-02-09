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
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder


@dataclass
class ModelConfig:
    """Configuration for ML model"""
    model_type: str = 'xgboost'  # 'xgboost', 'lightgbm', 'ridge'
    target_type: str = 'binary'  # 'binary', 'regression'
    
    # XGBoost params
    xgb_params: Dict = field(default_factory=lambda: {
        'objective': 'multi:softprob',
        'eval_metric': 'mlogloss',
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
        'objective': 'multiclass',
        'metric': 'multi_logloss',
        'num_class': 3,
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'random_state': 42,
    })
    
    # Random Forest params (PRD FR-3.2)
    rf_params: Dict = field(default_factory=lambda: {
        'n_estimators': 100,
        'max_depth': 8,
        'min_samples_split': 10,
        'min_samples_leaf': 5,
        'max_features': 'sqrt',
        'random_state': 42,
        'n_jobs': -1,
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
        self.label_encoder: Optional[LabelEncoder] = None
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
        y_train = y.copy()
        
        # Encode labels for classification (XGBoost requires 0-indexed labels)
        if self.config.target_type == 'binary':
            self.label_encoder = LabelEncoder()
            y_train = pd.Series(
                self.label_encoder.fit_transform(y_train),
                index=y_train.index, name=y_train.name
            )
        
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
        
        elif self.config.model_type == 'random_forest':
            if self.config.target_type == 'binary':
                return RandomForestClassifier(**self.config.rf_params)
            else:
                return RandomForestRegressor(**self.config.rf_params)
        
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
            'train_ic': [],
        }
        
        for fold_idx, (train_idx, val_idx) in enumerate(cv_splitter.split(X, y)):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            if len(y_tr) < 100 or len(y_val) < 10:
                continue
            
            # Train fold model
            model = self._create_model()
            model.fit(X_tr, y_tr)
            
            # Predict on validation
            if hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_val)
                y_pred = model.predict(X_val)
                
                # AUC (handle multi-class)
                try:
                    if y_pred_proba.shape[1] == 2:
                        auc = roc_auc_score(y_val, y_pred_proba[:, 1])
                    else:
                        auc = roc_auc_score(y_val, y_pred_proba, multi_class='ovr', average='macro')
                    scores['auc'].append(auc)
                except:
                    pass
                
                # Accuracy
                acc = accuracy_score(y_val, y_pred)
                scores['accuracy'].append(acc)
            else:
                y_pred = model.predict(X_val)
            
            # Validation IC
            ic = np.corrcoef(y_val, y_pred)[0, 1] if len(y_val) > 1 else 0
            if not np.isnan(ic):
                scores['ic'].append(ic)
            
            # Train IC (for overfitting detection: Sharpe diff)
            y_train_pred = model.predict(X_tr)
            train_ic = np.corrcoef(y_tr, y_train_pred)[0, 1] if len(y_tr) > 1 else 0
            if not np.isnan(train_ic):
                scores['train_ic'].append(train_ic)
        
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
        - Train vs Val Sharpe diff > 0.5 (approximated via IC diff)
        - Val IC < 0.03
        - IC variance too high (instability)
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
        
        # FR-3.2: Train vs Val IC diff > 0.5 (Sharpe proxy)
        train_ic = cv_scores.get('train_ic_mean', 0)
        val_ic = cv_scores.get('ic_mean', 0)
        ic_diff = train_ic - val_ic
        if ic_diff > 0.5:
            logger.warning(f"Train-Val IC gap too large: {ic_diff:.4f} > 0.5 (overfitting)")
            overfitting = True
        
        return overfitting
    
    def predict(self, X: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        """Make predictions (returns probability of positive class or regression values)"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        X_input = X[feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X_input)
        
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(X_scaled)
            if proba.shape[1] == 2:
                return proba[:, 1]
            else:
                # Multi-class: return weighted sum as signal strength
                # For 3 classes (-1, 0, 1 encoded as 0, 1, 2):
                # Signal = P(up) - P(down)
                return proba[:, -1] - proba[:, 0]
        return self.model.predict(X_scaled)
    
    def optimize_hyperparameters(self,
                                X: pd.DataFrame,
                                y: pd.Series,
                                feature_cols: List[str],
                                cv_splitter=None,
                                max_trials: int = 100,
                                timeout: int = 3600) -> Dict:
        """
        Hyperparameter optimization using Optuna (FR-3.2).
        
        Uses Tree-structured Parzen Estimator (TPE) for search.
        Conservative search space to prevent overfitting optimization itself.
        
        Args:
            X: Feature matrix
            y: Target variable
            feature_cols: Feature columns
            cv_splitter: Cross-validation splitter
            max_trials: Maximum optimization trials (PRD: 100)
            timeout: Maximum time in seconds
            
        Returns:
            Best hyperparameters dictionary
        """
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
        except ImportError:
            logger.warning("Optuna not installed, skipping hyperparameter optimization")
            return {}
        
        X_train = X[feature_cols].fillna(0)
        scaler = StandardScaler()
        X_scaled = pd.DataFrame(
            scaler.fit_transform(X_train),
            index=X_train.index, columns=X_train.columns
        )
        
        def objective(trial):
            if self.config.model_type == 'xgboost':
                params = {
                    'max_depth': trial.suggest_int('max_depth', 3, 8),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0.01, 10.0, log=True),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0.01, 10.0, log=True),
                    'random_state': 42,
                }
                if self.config.target_type == 'binary':
                    params['objective'] = 'binary:logistic'
                    params['eval_metric'] = 'auc'
                    model = xgb.XGBClassifier(**params)
                else:
                    params['objective'] = 'reg:squarederror'
                    model = xgb.XGBRegressor(**params)
                    
            elif self.config.model_type == 'lightgbm':
                params = {
                    'num_leaves': trial.suggest_int('num_leaves', 15, 63),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                    'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0),
                    'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 1.0),
                    'bagging_freq': trial.suggest_int('bagging_freq', 1, 10),
                    'verbose': -1,
                    'random_state': 42,
                }
                if self.config.target_type == 'binary':
                    model = lgb.LGBMClassifier(**params)
                else:
                    model = lgb.LGBMRegressor(**params)
            else:
                return 0.0
            
            # Cross-validate
            ics = []
            if cv_splitter is not None:
                for train_idx, val_idx in cv_splitter.split(X_scaled, y):
                    X_tr, X_val = X_scaled.iloc[train_idx], X_scaled.iloc[val_idx]
                    y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
                    if len(y_tr) < 100 or len(y_val) < 10:
                        continue
                    model.fit(X_tr, y_tr)
                    y_pred = model.predict(X_val)
                    ic = np.corrcoef(y_val, y_pred)[0, 1] if len(y_val) > 1 else 0
                    if not np.isnan(ic):
                        ics.append(ic)
            
            return np.mean(ics) if ics else 0.0
        
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        study.optimize(objective, n_trials=max_trials, timeout=timeout)
        
        best_params = study.best_params
        logger.info(f"Optuna optimization complete: {len(study.trials)} trials, best IC={study.best_value:.4f}")
        logger.info(f"Best params: {best_params}")
        
        # Update config with best params
        if self.config.model_type == 'xgboost':
            self.config.xgb_params.update(best_params)
        elif self.config.model_type == 'lightgbm':
            self.config.lgb_params.update(best_params)
        
        return best_params
    
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
                'label_encoder': self.label_encoder,
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
        self.label_encoder = data.get('label_encoder', None)
        
        # Load metadata
        meta_path = model_path.replace('.pkl', '.json')
        with open(meta_path, 'r') as f:
            meta_dict = json.load(f)
        
        self.metadata = TrainingMetadata(**meta_dict)
        
        logger.info(f"Model loaded: {self.metadata.model_id}")
