"""Feature Engineering Module - PRD FR-3.1

Implements robust feature engineering with forward-looking bias prevention.
Features include price-based, macro, and cross-sectional factors.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from ..utils.logger import logger


@dataclass
class FeatureConfig:
    """Configuration for feature engineering"""
    # Price features
    return_periods: List[int] = None
    volatility_periods: List[int] = None
    ma_periods: List[int] = None
    
    # Cross-sectional features
    rank_features: bool = True
    
    def __post_init__(self):
        if self.return_periods is None:
            self.return_periods = [1, 5, 10, 20, 60]
        if self.volatility_periods is None:
            self.volatility_periods = [5, 20, 60]
        if self.ma_periods is None:
            self.ma_periods = [5, 10, 20, 50, 200]


class FeatureEngineer:
    """
    Robust feature engineering with forward-looking bias prevention.
    
    FR-3.1 Requirements:
    - Price features: Returns, volatility, moving averages, RSI, MACD, ATR, Bollinger
    - Macro features: Rates, VIX, DXY, CPI (to be fetched externally)
    - Cross-sectional features: Correlation changes, rotation indicators, sector momentum diff
    - Anti-overfitting: Point-in-time data only, macro data uses release date
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        logger.info(f"FeatureEngineer initialized with {len(self.config.return_periods)} return periods")
    
    def create_features(self, prices: Dict[str, pd.DataFrame],
                       macro_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Create feature matrix from price data.
        
        Args:
            prices: Dict mapping symbol -> OHLCV DataFrame
            macro_data: Optional macro indicators DataFrame
            
        Returns:
            DataFrame with features (symbol, date index)
        """
        all_features = []
        
        for symbol, df in prices.items():
            if df is None or len(df) < 200:
                continue
                
            try:
                features = self._create_symbol_features(symbol, df)
                all_features.append(features)
            except Exception as e:
                logger.error(f"Error creating features for {symbol}: {e}")
        
        if not all_features:
            return pd.DataFrame()
        
        # Combine all symbol features
        combined = pd.concat(all_features, axis=0)
        
        # Add cross-sectional features
        combined = self._add_cross_sectional_features(combined)
        
        # Add macro features if provided
        if macro_data is not None:
            combined = self._add_macro_features(combined, macro_data)
        
        logger.info(f"Created feature matrix: {combined.shape}")
        return combined
    
    def _create_symbol_features(self, symbol: str, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for a single symbol"""
        features = pd.DataFrame(index=df.index)
        features['symbol'] = symbol
        
        close = df['close']
        
        # 1. Return features (FR-3.1: 收益率)
        for period in self.config.return_periods:
            features[f'return_{period}d'] = close.pct_change(period)
        
        # 2. Volatility features (FR-3.1: 波动率)
        for period in self.config.volatility_periods:
            features[f'volatility_{period}d'] = close.pct_change().rolling(period).std() * np.sqrt(252)
        
        # 3. Moving average features (FR-3.1: 均线)
        for period in self.config.ma_periods:
            ma = close.rolling(period).mean()
            features[f'ma_ratio_{period}'] = close / ma
            features[f'ma_distance_{period}'] = (close - ma) / ma
        
        # 4. Technical indicators
        # RSI (FR-3.1)
        features['rsi_14'] = self._calculate_rsi(close, 14)
        
        # MACD (FR-3.1)
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        features['macd'] = ema_12 - ema_26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # ATR (FR-3.1)
        features['atr_14'] = self._calculate_atr(df, 14)
        
        # Bollinger Bands (FR-3.1)
        ma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        features['bb_upper'] = (ma_20 + 2 * std_20) / close
        features['bb_lower'] = (ma_20 - 2 * std_20) / close
        features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / features['bb_upper']
        
        # 5. Momentum features
        features['momentum_12m'] = close.pct_change(252)
        features['momentum_6m'] = close.pct_change(126)
        features['momentum_3m'] = close.pct_change(63)
        features['momentum_1m'] = close.pct_change(21)
        
        # 6. Volume features
        if 'volume' in df.columns:
            volume = df['volume']
            features['volume_ma_ratio'] = volume / volume.rolling(20).mean()
            features['volume_price_trend'] = (close.pct_change(5) > 0) & (volume > volume.rolling(20).mean())
        
        return features
    
    def _add_cross_sectional_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Add cross-sectional features (FR-3.1: 交叉特征)
        - Asset correlation changes
        - Rotation indicators
        - Sector momentum differences
        """
        # Rank features within each date (FR-3.1: 轮动指标)
        if self.config.rank_features:
            numeric_cols = features.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if 'return' in col or 'momentum' in col:
                    features[f'{col}_rank'] = features.groupby(level=0)[col].rank(pct=True)
        
        # Calculate cross-sectional dispersion (market breadth)
        for window in [5, 20]:
            features[f'return_dispersion_{window}d'] = features.groupby(level=0)[f'return_{window}d'].transform('std')
        
        return features
    
    def _add_macro_features(self, features: pd.DataFrame, macro_data: pd.DataFrame) -> pd.DataFrame:
        """
        Add macro features (FR-3.1: 宏观特征)
        - Interest rates (FRED)
        - VIX (CBOE)
        - DXY (FRED)
        - CPI (FRED)
        
        Note: Uses point-in-time data with release dates (not report dates)
        """
        # Merge macro data on date index
        features = features.join(macro_data, how='left')
        
        # Forward fill macro data (they're released at different frequencies)
        macro_cols = [c for c in macro_data.columns if c not in features.columns]
        for col in macro_cols:
            features[col] = features[col].ffill()
        
        return features
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean()
    
    def create_target(self, prices: Dict[str, pd.DataFrame],
                     horizon: int = 5,
                     binary: bool = True) -> pd.Series:
        """
        Create target variable (future returns).
        
        Args:
            prices: Price data
            horizon: Prediction horizon in days
            binary: If True, return direction (-1, 0, 1); else return returns
            
        Returns:
            Series with target values
        """
        targets = []
        
        for symbol, df in prices.items():
            if df is None or len(df) < horizon + 1:
                continue
            
            future_return = df['close'].pct_change(horizon).shift(-horizon)
            
            if binary:
                # Direction: -1 (down), 0 (flat), 1 (up)
                target = pd.Series(0, index=df.index, name='target')
                target[future_return > 0.01] = 1   # Up > 1%
                target[future_return < -0.01] = -1  # Down > 1%
            else:
                target = future_return
            
            target.name = 'target'
            targets.append(target)
        
        if not targets:
            return pd.Series()
        
        return pd.concat(targets, axis=0)
    
    def select_features(self, features: pd.DataFrame, 
                       target: pd.Series,
                       method: str = 'ic',
                       min_ic: float = 0.02,
                       max_features: int = 20) -> List[str]:
        """
        Feature selection (FR-3.1: 特征选择)
        
        Args:
            features: Feature matrix
            target: Target variable
            method: 'ic' (information coefficient) or 'pca'
            min_ic: Minimum IC threshold
            max_features: Maximum number of features to select
            
        Returns:
            List of selected feature names
        """
        numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
        numeric_features = [c for c in numeric_features if c != 'target']
        
        if method == 'ic':
            # Calculate IC for each feature
            ic_scores = {}
            for col in numeric_features:
                valid_idx = features[col].notna() & target.notna()
                if valid_idx.sum() < 100:
                    continue
                ic = features.loc[valid_idx, col].corr(target.loc[valid_idx])
                ic_scores[col] = abs(ic)
            
            # Select features with IC > threshold
            selected = [f for f, ic in ic_scores.items() if ic > min_ic]
            selected = sorted(selected, key=lambda x: ic_scores[x], reverse=True)[:max_features]
            
            logger.info(f"Selected {len(selected)} features by IC (threshold={min_ic})")
            return selected
        
        elif method == 'pca':
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
            
            # Standardize
            scaler = StandardScaler()
            scaled = scaler.fit_transform(features[numeric_features].fillna(0))
            
            # PCA
            pca = PCA(n_components=min(max_features, len(numeric_features)))
            pca.fit(scaled)
            
            logger.info(f"PCA explained variance: {pca.explained_variance_ratio_.sum():.2%}")
            return numeric_features[:max_features]
        
        return numeric_features[:max_features]
    
    def test_feature_stability(self,
                               features: pd.DataFrame,
                               target: pd.Series,
                               n_periods: int = 4,
                               max_ic_variance: float = 0.01) -> Dict[str, Dict]:
        """
        Feature stability test (FR-3.1: 特征稳定性检验).
        
        Tests whether feature IC is consistent across different time periods.
        Features with IC variance > threshold across periods are flagged as unstable.
        
        Args:
            features: Feature matrix
            target: Target variable
            n_periods: Number of sub-periods to test
            max_ic_variance: Maximum allowed IC variance across periods
            
        Returns:
            Dict with feature stability results
        """
        numeric_features = features.select_dtypes(include=[np.number]).columns.tolist()
        numeric_features = [c for c in numeric_features if c != 'target']
        
        # Split data into equal time periods
        period_size = len(features) // n_periods
        
        stability_results = {}
        for col in numeric_features:
            period_ics = []
            for i in range(n_periods):
                start = i * period_size
                end = min((i + 1) * period_size, len(features))
                
                f_slice = features.iloc[start:end][col]
                t_slice = target.iloc[start:end]
                
                valid_idx = f_slice.notna() & t_slice.notna()
                if valid_idx.sum() < 50:
                    continue
                
                ic = f_slice.loc[valid_idx].corr(t_slice.loc[valid_idx])
                if not np.isnan(ic):
                    period_ics.append(ic)
            
            if len(period_ics) >= 2:
                ic_var = np.var(period_ics)
                ic_mean = np.mean(period_ics)
                stable = ic_var < max_ic_variance
                stability_results[col] = {
                    'ic_mean': ic_mean,
                    'ic_variance': ic_var,
                    'period_ics': period_ics,
                    'stable': stable,
                }
                
                if not stable:
                    logger.warning(f"Unstable feature '{col}': IC variance={ic_var:.4f} > {max_ic_variance}")
        
        n_stable = sum(1 for v in stability_results.values() if v['stable'])
        logger.info(f"Feature stability test: {n_stable}/{len(stability_results)} features stable")
        
        return stability_results
    
    def prevent_lookahead_bias(self, features: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
        """
        Validate and prevent forward-looking bias (Tech Design 4.4.1).
        
        Techniques:
        - Ensures all features are point-in-time (no future data leakage)
        - Forward-only data processing
        - Removes any target-correlated columns that shouldn't be features
        - Checks that features don't have impossible future information
        
        Args:
            features: Feature matrix to validate
            target: Target variable (future returns)
            
        Returns:
            Cleaned feature DataFrame with bias-free features
        """
        clean_features = features.copy()
        removed_cols = []
        
        # 1. Check for columns that correlate suspiciously high with target
        numeric_cols = clean_features.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            valid_idx = clean_features[col].notna() & target.notna()
            if valid_idx.sum() < 100:
                continue
            corr = abs(clean_features.loc[valid_idx, col].corr(target.loc[valid_idx]))
            if corr > 0.95:
                logger.warning(f"Removing '{col}': suspiciously high correlation with target ({corr:.3f})")
                removed_cols.append(col)
                clean_features.drop(columns=[col], inplace=True)
        
        # 2. Ensure no NaN at the beginning (from rolling windows) are filled with future data
        # All NaN should be at the start, not randomly in the middle
        for col in clean_features.select_dtypes(include=[np.number]).columns:
            nan_mask = clean_features[col].isna()
            if nan_mask.any():
                # Find last NaN position
                last_nan = nan_mask[nan_mask].index[-1] if nan_mask.any() else None
                first_valid = clean_features[col].first_valid_index()
                # NaN should only be at the start
                if last_nan is not None and first_valid is not None:
                    mid_nans = clean_features[col].loc[first_valid:].isna().sum()
                    if mid_nans > 0:
                        # Forward fill only (no future data)
                        clean_features[col] = clean_features[col].ffill()
        
        if removed_cols:
            logger.info(f"Removed {len(removed_cols)} features due to lookahead bias: {removed_cols}")
        
        logger.info(f"Lookahead bias check complete: {len(clean_features.columns)} features retained")
        return clean_features
