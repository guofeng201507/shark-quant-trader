"""Combinatorial Purged Cross-Validation (CPCV) - PRD FR-3.2

Implementation of Lopez de Prado's Combinatorial Purged Cross-Validation
for time series to prevent leakage and overfitting.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Generator, Optional
from itertools import combinations
from ..utils.logger import logger


class CombinatorialPurgedCV:
    """
    Combinatorial Purged Cross-Validation for time series.
    
    FR-3.2 Requirements:
    - Purge gap: 21 trading days (prevent label leakage)
    - Embargo: 5 trading days
    - Minimum 6 folds
    - Training window: 3 years rolling
    - Validation window: 6 months
    """
    
    def __init__(self,
                 n_splits: int = 6,
                 purge_gap: int = 21,
                 embargo_pct: float = 0.02,
                 train_size: Optional[int] = None,
                 test_size: Optional[int] = None):
        """
        Initialize CPCV.
        
        Args:
            n_splits: Number of splits (minimum 6 per PRD)
            purge_gap: Number of days to purge between train and test (21 per PRD)
            embargo_pct: Percentage of test set to embargo (0.02 = 5/252 trading days)
            train_size: Training window size in days (~756 for 3 years)
            test_size: Test window size in days (~126 for 6 months)
        """
        self.n_splits = n_splits
        self.purge_gap = purge_gap
        self.embargo_pct = embargo_pct
        self.train_size = train_size
        self.test_size = test_size
        
        logger.info(f"CPCV initialized: n_splits={n_splits}, purge_gap={purge_gap}")
    
    def split(self, X: pd.DataFrame, y=None, groups=None) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate train/test indices using CPCV.
        
        Yields:
            Tuple of (train_indices, test_indices)
        """
        n_samples = len(X)
        indices = np.arange(n_samples)
        
        # Generate combinatorial splits
        # We create groups and then use combinations
        n_groups = self.n_splits + 1
        group_size = n_samples // n_groups
        
        groups = []
        for i in range(n_groups):
            start = i * group_size
            end = min((i + 1) * group_size, n_samples)
            groups.append(indices[start:end])
        
        # Generate all combinations of train/test groups
        # For each split, we use k groups for test and rest for train
        test_group_size = max(1, n_groups // 3)  # Use ~1/3 for test
        
        for test_combo in combinations(range(n_groups), test_group_size):
            train_indices = []
            test_indices = []
            
            for i, group in enumerate(groups):
                if i in test_combo:
                    test_indices.extend(group)
                else:
                    train_indices.extend(group)
            
            train_indices = np.array(train_indices)
            test_indices = np.array(test_indices)
            
            # Apply purge gap and embargo
            train_indices, test_indices = self._apply_purge_embargo(
                train_indices, test_indices, n_samples
            )
            
            if len(train_indices) > 0 and len(test_indices) > 0:
                yield train_indices, test_indices
    
    def _apply_purge_embargo(self, 
                            train_indices: np.ndarray,
                            test_indices: np.ndarray,
                            n_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply purge gap and embargo to prevent leakage.
        
        Purge gap: Remove samples near train/test boundary
        Embargo: Remove samples from end of test set
        """
        if len(test_indices) == 0:
            return train_indices, test_indices
        
        test_min = test_indices.min()
        test_max = test_indices.max()
        
        # Purge gap: remove train samples within purge_gap of test set
        train_mask = (train_indices < test_min - self.purge_gap) | (train_indices > test_max + self.purge_gap)
        train_indices = train_indices[train_mask]
        
        # Embargo: remove last embargo_pct of test set
        embargo_size = int(len(test_indices) * self.embargo_pct)
        if embargo_size > 0:
            test_indices = test_indices[:-embargo_size]
        
        return train_indices, test_indices
    
    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Return number of splits"""
        from math import comb
        n_groups = self.n_splits + 1
        test_group_size = max(1, n_groups // 3)
        return comb(n_groups, test_group_size)


class PurgedWalkForwardCV:
    """
    Purged Walk-Forward Cross-Validation.
    
    Simpler alternative to CPCV with rolling windows.
    FR-3.2: Training window 3 years, validation window 6 months, purge gap 21 days
    """
    
    def __init__(self,
                 train_size: int = 756,  # ~3 years
                 test_size: int = 126,   # ~6 months
                 purge_gap: int = 21,    # 21 trading days
                 step_size: int = 63):   # ~3 months step
        """
        Initialize Purged Walk-Forward CV.
        
        Args:
            train_size: Training window in days
            test_size: Test window in days
            purge_gap: Days to purge between train and test
            step_size: Step size for rolling window
        """
        self.train_size = train_size
        self.test_size = test_size
        self.purge_gap = purge_gap
        self.step_size = step_size
        
        logger.info(f"PurgedWalkForwardCV: train={train_size}, test={test_size}, gap={purge_gap}")
    
    def split(self, X: pd.DataFrame, y=None, groups=None) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate train/test splits using walk-forward with purge.
        
        Yields:
            Tuple of (train_indices, test_indices)
        """
        n_samples = len(X)
        
        start = self.train_size
        while start + self.test_size <= n_samples:
            # Train: [start - train_size, start - purge_gap)
            train_end = start - self.purge_gap
            train_start = max(0, train_end - self.train_size)
            train_indices = np.arange(train_start, train_end)
            
            # Test: [start, start + test_size)
            test_end = min(start + self.test_size, n_samples)
            test_indices = np.arange(start, test_end)
            
            if len(train_indices) > 100 and len(test_indices) > 10:
                yield train_indices, test_indices
            
            start += self.step_size
    
    def get_n_splits(self, X=None, y=None, groups=None) -> int:
        """Estimate number of splits"""
        n_samples = len(X) if X is not None else 0
        if n_samples <= self.train_size + self.test_size:
            return 0
        return (n_samples - self.train_size - self.test_size) // self.step_size + 1


def create_time_series_split(X: pd.DataFrame,
                            method: str = 'cpcv',
                            **kwargs) -> object:
    """
    Factory function to create time series cross-validator.
    
    Args:
        X: Feature matrix
        method: 'cpcv' or 'purged_walkforward'
        **kwargs: Additional arguments for the validator
        
    Returns:
        Cross-validator instance
    """
    if method == 'cpcv':
        return CombinatorialPurgedCV(**kwargs)
    elif method == 'purged_walkforward':
        return PurgedWalkForwardCV(**kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")
