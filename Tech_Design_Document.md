# Intelligent Trading System - Technical Design Document

> **Version**: 1.2  
> **Author**: Technical Architecture Team  
> **Date**: 2026-02-08  
> **Based on**: PRD v2.0  

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|--------|
| 1.0 | 2026-02-08 | Technical Architecture Team | Initial draft |
| 1.1 | 2026-02-08 | Technical Architecture Team | Added: asset universe specs, detailed factor definitions, re-entry logic, correlation monitoring, cost model, stress test scenarios, paper trading gates, Phase 2/4 strategy details, model lifecycle management, disaster recovery flow, interface definitions |
| 1.2 | 2026-02-08 | Technical Architecture Team | Added: Phase 5 Paper Trading System (4.11), Phase 6 Live Trading System (4.12), Phase 7 DevOps Automation (4.13), updated roadmap (Section 15), aligned future extensibility with PRD (Section 13) |

---

## 1. Executive Summary

This document outlines the technical architecture and implementation plan for the Intelligent Trading Decision System, a multi-phase quantitative trading platform covering precious metals, equity ETFs, international ETFs, and cryptocurrencies.

### Key Technical Decisions

1. **Architecture Style**: Modular microservices-like structure with clear separation of concerns
2. **Programming Language**: Python 3.10+ for rapid development and rich ecosystem
3. **Data Pipeline**: Multi-source with automatic fallback and quality validation
4. **Risk Management**: Hierarchical risk control with 4 progressive levels
5. **ML Integration**: Ensemble learning with rigorous overfitting prevention
6. **Deployment**: Containerized with cron-based scheduling for simplicity

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Intelligent Trading System                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Data Tier   │  │ Strategy Tier │  │ Execution Tier│             │
│  │  Data Layer   │  │   Strategy    │  │  Execution    │             │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤             │
│  │ • Multi-source│  │ • Factor Calc │  │ • Signal Gen  │             │
│  │ • Validation  │  │ • Portfolio   │  │ • Order Mgmt  │             │
│  │ • Caching     │  │ • Risk Mgmt   │  │ • Compliance  │             │
│  │ • Persistence │  │ • ML Models   │  │ • State Sync  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Monitoring   │  │  Backtesting  │  │   Reporting   │             │
│  │   & Alerting  │  │  & Stress     │  │               │             │
│  │               │  │   Testing     │  │               │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                             Main System                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │   Data Module    │  │  Strategy Core   │  │  Execution Engine│    │
│  │                 │  │                 │  │                 │    │
│  │ • Provider      │  │ • Signals       │  │ • Broker API    │    │
│  │ • Validator     │  │ • Factors       │  │ • Order Router  │    │
│  │ • Processor     │  │ • Optimizer     │  │ • Risk Checker  │    │
│  │ • Cache         │  │ • Risk Manager  │  │ • Compliance    │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│           │                    │                      │             │
│           ▼                    ▼                      ▼             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │   ML Pipeline    │  │   Monitoring     │  │   Persistence    │   │
│  │ (Phase 3+)       │  │   & Alerting     │  │   Manager        │   │
│  │                 │  │                 │  │                 │   │
│  │ • Features      │  │ • Health Checks  │  │ • State DB      │   │
│  │ • Models        │  │ • Metrics        │  │ • Trade Logs    │   │
│  │ • Trainer       │  │ • Alerts         │  │ • Recovery      │   │
│  │ • Monitor       │  │ • Dashboard      │  │ • Backup        │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Data Flow Architecture

```
Market Data Sources
       │
       ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Polygon.io  │───▶│ Data        │───▶│ Factor      │
│ Tiingo      │    │ Validator   │    │ Calculator  │
│ yfinance    │    │ & Cache     │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                            │                 │
                            ▼                 ▼
                   ┌─────────────┐   ┌─────────────┐
                   │ Risk        │◀──│ Signal      │
                   │ Manager     │   │ Generator   │
                   └─────────────┘   └─────────────┘
                            │                 │
                            ▼                 ▼
                   ┌─────────────┐   ┌─────────────┐
                   │ Portfolio   │───▶│ Execution   │
                   │ Optimizer   │   │ Engine      │
                   └─────────────┘   └─────────────┘
                            │                 │
                            ▼                 ▼
                   ┌─────────────┐   ┌─────────────┐
                   │ State       │   │ Broker/API  │
                   │ Persister   │   │             │
                   └─────────────┘   └─────────────┘
```

---

## 3. Technology Stack

### 3.1 Core Technologies

| Layer | Technology | Version | Justification |
|-------|------------|---------|---------------|
| Language | Python | 3.10+ | Rich ecosystem, rapid prototyping |
| Package Manager | Poetry | Latest | Dependency resolution, virtual environments |
| Data Processing | pandas, numpy | Latest | Industry standard |
| Technical Analysis | pandas-ta | Latest | Replaces ta-lib (compilation issues) |
| Backtesting | Backtrader | Latest | Unified framework (dropped Zipline) |
| Portfolio Optimization | riskfolio-lib | Latest | Active maintenance, comprehensive |
| Machine Learning | scikit-learn, XGBoost, LightGBM | Latest | Interpretable, efficient |
| NLP | transformers (FinBERT) | Latest | Pre-trained financial models |
| Visualization | matplotlib, plotly | Latest | Interactive charts |
| Configuration | pydantic, yaml | Latest | Type-safe, human-readable |
| Logging | loguru | Latest | Modern structured logging |
| Alerts | apprise | Latest | Multi-channel notifications |
| Testing | pytest | Latest | Standard Python testing |

### 3.2 Infrastructure

| Component | Choice | Reason |
|-----------|--------|---------|
| Deployment | Docker + Docker Compose | Containerization, reproducibility |
| Scheduling | cron (simple), Airflow (complex) | Cron for MVP, Airflow for advanced workflows |
| Monitoring | Prometheus + Grafana | Industry standard observability |
| Database | SQLite (initial) → PostgreSQL (scale) | SQLite for simplicity, PostgreSQL for production |
| Cloud | AWS EC2 | t3.medium for Phases 1-2, g4dn.xlarge for Phase 4 GPU |
| Backup | S3 | Reliable, cost-effective |

### 3.3 Data Sources

| Data Type | Primary Source | Fallback | Cost | Notes |
|-----------|----------------|----------|------|-------|
| US Equity/ETF | Polygon.io | yfinance | $29/month | Production data |
| Cryptocurrency | Binance API | yfinance | Free | BTC canonical source |
| Macro Data | FRED API | - | Free | Interest rates, inflation |
| Alternative Data | NewsAPI, CFTC | GDELT, RSS | Free-$449/month | Phase 4 NLP inputs |

### 3.4 Asset Universe (NEW)

#### 3.4.1 Core Assets (Phase 1)

| Asset | Symbol | Type | Max Weight | Vol Target | Stop Loss |
|-------|--------|------|------------|------------|-----------|
| Gold ETF | GLD | Safe Haven | 50% | 10-12% | 12% |
| S&P 500 ETF | SPY | Core Equity | 40% | 15% | 12% |
| Nasdaq 100 ETF | QQQ | Growth Equity | 30% | 18% | 12% |
| Bitcoin | BTC-USD | Crypto | 15% | 20-25% | 18% |

#### 3.4.2 Extended Assets (Phase 2 - Cross-Sectional Momentum)

| Category | Symbol | Max Weight | Purpose |
|----------|--------|------------|---------|
| Precious Metals | SLV | 15% | Cross-section with GLD |
| Sector - Tech | XLK | 20% | Sector rotation |
| Sector - Finance | XLF | 15% | Sector rotation |
| Sector - Energy | XLE | 15% | Commodity cycle |
| Sector - Healthcare | XLV | 15% | Defensive |
| Bonds - Long Duration | TLT | 30% | Rate risk/safe haven |
| Bonds - TIPS | TIP | 15% | Inflation hedge |
| International - DM | EFA | 20% | Geographic diversification |
| International - EM | EEM | 15% | Geographic diversification |
| Commodities | DBC | 15% | Commodity exposure |
| Real Estate | VNQ | 15% | Alternative asset |

**Total**: 15 assets enabling statistically meaningful cross-sectional ranking (Top 30% = 4-5 assets)

### 3.5 Cost Model (NEW)

| Asset Type | Commission | Slippage | Min Trade Unit |
|------------|------------|----------|----------------|
| US ETFs | 0.10% | 0.05% | 1 share |
| Bitcoin | 0.10% | 0.15% | 0.0001 BTC |

**Portfolio Constraints:**
- Minimum trade amount: $100
- Minimum rebalance threshold: 2% weight change
- Cash buffer: ≥5% always reserved
- Maximum portfolio leverage: 1.5x
- Maximum daily trades: 5
- Maximum daily turnover: 30%

---

## 4. Detailed Module Design

### 4.1 Data Layer

#### 4.1.1 DataProvider Class

```python
class DataProvider:
    """Multi-source data acquisition with automatic fallback"""
    
    def __init__(self):
        self.primary_source = PolygonClient()
        self.backup_source = YFinanceClient()
        self.crypto_source = BinanceClient()
        self.cache = SQLiteCache()
        
    def fetch(self, symbols: List[str], start_date: str, 
              end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch data with priority: Polygon → Binance → yfinance
        Implements exponential backoff and circuit breaker
        """
        pass
        
    def validate(self, data: pd.DataFrame) -> DataQualityReport:
        """
        Validate data quality:
        - Price jumps > 50%
        - Missing data > 5%
        - Cross-source deviation > 1%
        """
        pass
```

#### 4.1.2 Caching Strategy

```
Cache Hierarchy:
1. In-memory LRU (last 100 requests) - Fastest
2. SQLite disk cache (30-day retention) - Persistent
3. Remote cache (Redis/S3) - Shared across instances
```

### 4.2 Factor Calculation Layer (NEW)

#### 4.2.1 Factor Definitions

| Factor | Calculation | Lookback | Usage |
|--------|-------------|----------|-------|
| Momentum_60 | 60-day cumulative return | 60 days | Time-series momentum signal |
| Momentum_120 | 120-day cumulative return | 120 days | Long-term momentum |
| Volatility_20 | 20-day annualized std dev | 20 days | Short-term risk |
| Volatility_60 | 60-day annualized std dev | 60 days | Medium-term risk |
| SMA_20 | 20-day simple moving average | 20 days | Short-term trend |
| SMA_50 | 50-day simple moving average | 50 days | Medium-term trend |
| SMA_200 | 200-day simple moving average | 200 days | Long-term trend |
| RSI_14 | 14-day relative strength index | 14 days | Overbought/oversold |
| ATR_14 | 14-day average true range | 14 days | Stop loss calculation |

#### 4.2.2 Factor Calculator Class

```python
class FactorCalculator:
    """Calculate all technical factors for signal generation"""
    
    FACTOR_CONFIG = {
        "momentum": {"periods": [60, 120]},
        "volatility": {"periods": [20, 60], "annualize": True},
        "sma": {"periods": [20, 50, 200]},
        "rsi": {"period": 14},
        "atr": {"period": 14}
    }
    
    def calculate(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all factors for given price data.
        Uses pandas-ta for technical indicators.
        Returns DataFrame with columns: symbol, date, factor_name, value
        """
        pass
    
    def calculate_cross_sectional_rank(self, factor_df: pd.DataFrame, 
                                       factor_name: str) -> pd.DataFrame:
        """
        Rank assets cross-sectionally for momentum strategy.
        Used in Phase 2 for Top/Bottom 30% selection.
        """
        pass
```

### 4.3 Strategy Layer

#### 4.3.1 Signal Generation Pipeline

```
Input: Raw price data
   │
   ▼
Factor Calculator (momentum, volatility, moving averages)
   │
   ▼
Market Regime Detector (VIX-based filtering)
   │
   ▼
Signal Generator (BUY/SELL/HOLD with confidence)
   │
   ▼
Output: List[TradeSignal]
```

#### 4.3.2 Signal Logic (NEW - from PRD)

```python
class SignalGenerator:
    """Generate trading signals with market regime filtering"""
    
    def generate_signal(self, factors: pd.DataFrame, 
                       current_positions: Dict,
                       market_regime: str) -> List[TradeSignal]:
        """
        Signal Logic:
        - STRONG_BUY: momentum > high_threshold AND price > SMA_50 
                      AND price > SMA_200 AND VIX < 30
        - BUY: momentum > low_threshold AND price > SMA_20
        - SELL: momentum < neg_threshold OR price < SMA_50
        - STRONG_SELL: momentum < neg_high_threshold AND price < SMA_200
        - HOLD: all other cases
        
        Market Regime Filters:
        - High volatility (VIX > 30): Reduce all signal confidence by 50%
        - Extreme volatility (VIX > 40): Only allow reduce position signals
        """
        pass
        
    def apply_regime_filter(self, signal: TradeSignal, 
                           vix: float) -> TradeSignal:
        """Apply VIX-based confidence adjustment"""
        if vix > 40:
            if signal.signal in [SignalType.BUY, SignalType.STRONG_BUY]:
                return signal._replace(signal=SignalType.HOLD)
        elif vix > 30:
            return signal._replace(confidence=signal.confidence * 0.5)
        return signal
```

#### 4.3.3 Risk Manager (EXPANDED - Hierarchical Control)

```python
class RiskManager:
    """4-level hierarchical risk control system with correlation monitoring"""
    
    # Portfolio-level drawdown triggers
    LEVELS = {
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
        "pair_warning": 0.7,      # Single asset pair
        "portfolio_warning": 0.5,  # Portfolio average
        "extreme_threshold": 0.8   # All assets same direction
    }
    
    def assess_risk_level(self, portfolio: Portfolio) -> int:
        """Determine current risk level based on drawdown from peak NAV"""
        pass
    
    def check_correlation_risk(self, returns: pd.DataFrame) -> CorrelationAlert:
        """
        Monitor 60-day rolling correlation matrix.
        Returns alert if thresholds breached.
        """
        pass
        
    def apply_controls(self, level: int, portfolio: Portfolio) -> List[Order]:
        """Apply risk controls for given level"""
        pass
    
    def check_single_asset_stop(self, symbol: str, 
                                entry_price: float,
                                current_price: float) -> Optional[str]:
        """Check if single asset stop loss triggered"""
        drawdown = (entry_price - current_price) / entry_price
        if drawdown > self.ASSET_STOPS["drawdown_exit"]:
            return "EXIT"
        elif drawdown > self.ASSET_STOPS["drawdown_reduce"]:
            return "REDUCE_50%"
        return None
```

#### 4.3.4 Re-Entry Logic (NEW)

```python
class ReEntryManager:
    """Manage position recovery after risk events"""
    
    CONFIG = {
        "cooldown_days": 5,           # Consecutive days of low vol required
        "vol_threshold_multiplier": 1.0,  # Vol must be < target vol
        "initial_position_pct": 0.25,  # Start with 25% of normal position
        "ramp_up_weekly_pct": 0.25,    # Add 25% each week
        "max_leverage_recovery": 1.0   # Lower leverage during recovery
    }
    
    def check_reentry_conditions(self, portfolio: Portfolio,
                                 volatility_history: pd.Series) -> bool:
        """
        Check if conditions met to resume trading after Level 4 exit.
        Requires 5 consecutive days where portfolio vol < target vol.
        """
        recent_vol = volatility_history.tail(self.CONFIG["cooldown_days"])
        return all(recent_vol < portfolio.target_volatility)
    
    def calculate_recovery_position(self, target_weight: float,
                                   weeks_in_recovery: int) -> float:
        """
        Gradual position rebuild: 25% → 50% → 75% → 100% over 4 weeks
        """
        recovery_pct = min(1.0, self.CONFIG["initial_position_pct"] + 
                          weeks_in_recovery * self.CONFIG["ramp_up_weekly_pct"])
        return target_weight * recovery_pct
```

#### 4.3.5 Correlation Monitor (NEW)

```python
class CorrelationMonitor:
    """Monitor cross-asset correlations for risk management"""
    
    def calculate_rolling_correlation(self, returns: pd.DataFrame,
                                     window: int = 60) -> pd.DataFrame:
        """Calculate 60-day rolling correlation matrix"""
        return returns.rolling(window).corr()
    
    def check_correlation_breach(self, corr_matrix: pd.DataFrame) -> List[Alert]:
        """
        Check for correlation threshold breaches:
        - Any pair > 0.7: Reduce combined weight cap
        - Portfolio avg > 0.5: Level 1 alert
        - All assets > 0.8 same direction: Auto Level 2
        """
        alerts = []
        # Check pairwise correlations
        for i, asset1 in enumerate(corr_matrix.columns):
            for asset2 in corr_matrix.columns[i+1:]:
                if corr_matrix.loc[asset1, asset2] > 0.7:
                    alerts.append(Alert("WARNING", 
                        f"High correlation {asset1}-{asset2}: {corr_matrix.loc[asset1, asset2]:.2f}"))
        
        # Check portfolio average
        avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix, k=1)].mean()
        if avg_corr > 0.5:
            alerts.append(Alert("LEVEL_1", f"Portfolio avg correlation: {avg_corr:.2f}"))
        
        return alerts
```

### 4.4 ML Pipeline (Phase 3)

#### 4.4.1 Feature Engineering Pipeline

```python
class FeatureEngineer:
    """Robust feature engineering with forward-looking bias prevention"""
    
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Features:
        - Price: Returns, volatility, moving averages
        - Macro: Rates, VIX, inflation
        - Cross-sectional: Correlations, momentum ranks
        - (Phase 4) Sentiment: News scores, retail positioning
        """
        pass
    
    def prevent_lookahead_bias(self):
        """
        Techniques:
        - Point-in-time data only
        - Forward-only data processing
        - Walk-forward validation
        """
        pass
```

#### 4.4.2 Model Training Framework

```python
class MLTrainer:
    """Overfitting-resistant model training"""
    
    def train_with_cpcv(self, X, y):
        """
        Combinatorial Purged Cross-Validation:
        - Purge gap: 21 trading days
        - Embargo: 5 trading days
        - Minimum 6 folds
        """
        pass
    
    def detect_overfitting(self, train_score, val_score):
        """
        Overfitting detection:
        - Sharpe difference > 0.5
        - IC < 0.03
        - Stability variance threshold
        """
        pass
```

#### 4.4.3 Model Lifecycle Management (NEW)

```python
class ModelLifecycleManager:
    """Manage ML model training, deployment, and retirement"""
    
    CONFIG = {
        "retrain_schedule": "monthly",         # Regular retraining frequency
        "rolling_window_years": 3,             # Training data lookback
        "ic_threshold_warning": 0.02,          # IC below this triggers retrain
        "ic_threshold_retire": 0.0,            # IC below this for 30 days = retire
        "drift_ks_threshold": 0.1,             # KS stat for concept drift warning
        "drift_ks_critical": 0.2               # KS stat triggers retrain
    }
    
    def schedule_retrain(self) -> datetime:
        """
        Retraining triggers:
        - Monthly scheduled retraining (end of month)
        - Rolling IC < 0.02 for 10 consecutive days
        - Concept drift KS > 0.2
        """
        pass
    
    def validate_new_model(self, old_model: Model, new_model: Model,
                          validation_data: pd.DataFrame) -> bool:
        """
        New model must significantly outperform old:
        - IC difference > 0.01
        - p-value < 0.05 (statistical significance)
        """
        pass
    
    def detect_concept_drift(self, feature_df: pd.DataFrame) -> float:
        """
        Calculate KS statistic for feature distribution shift.
        Compare recent 20 days vs training distribution.
        """
        pass
    
    def retire_model(self, model: Model, reason: str) -> None:
        """
        Retire model when:
        - IC < 0 for 30 consecutive days
        - Superseded by significantly better model
        """
        pass
```

### 4.5 Phase 2 Strategies (NEW)

#### 4.5.1 Cross-Sectional Momentum

```python
class CrossSectionalMomentum:
    """
    Cross-sectional momentum across 15 assets.
    Based on Asness (2013) "Value and Momentum Everywhere"
    """
    
    def rank_assets(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Rank assets by 12-1 month momentum:
        - Use 12-month cumulative return
        - Exclude most recent 1 month (avoid short-term reversal)
        """
        momentum_12m = returns.rolling(252).sum()  # ~12 months
        momentum_1m = returns.rolling(21).sum()    # ~1 month
        momentum_12_1 = momentum_12m - momentum_1m
        return momentum_12_1.rank(axis=1, pct=True)
    
    def generate_signals(self, ranks: pd.DataFrame) -> Dict[str, str]:
        """
        Signal generation:
        - Top 30% (rank > 0.7): LONG signal
        - Bottom 30% (rank < 0.3): AVOID (not SHORT - ETF shorting costs high)
        - Middle 40%: HOLD existing weight
        
        Additional filter: Asset must be above SMA_200 to receive LONG signal
        Defense mode: If >50% of Top group below SMA_200, go to GLD+TLT
        """
        pass
```

#### 4.5.2 Crypto Carry Strategy

```python
class CryptoCarryStrategy:
    """
    Funding rate arbitrage for BTC perpetual futures.
    Based on Brunnermeier (2009) carry trade principles.
    """
    
    DATA_SOURCES = {
        "binance": "/fapi/v1/fundingRate",
        "bybit": "/v5/market/funding/history"
    }
    
    THRESHOLDS = {
        "entry_rate": 0.0001,    # 0.01% per 8h = ~10% annualized
        "exit_rate": -0.0001,   # Close when rate inverts
        "max_position": 0.10,    # Max 10% of portfolio
        "max_exchange_exposure": 0.08  # Max 8% per exchange (counterparty risk)
    }
    
    def calculate_annualized_carry(self, funding_rate: float) -> float:
        """Convert 8-hour funding rate to annualized return"""
        return funding_rate * 3 * 365  # 3 funding periods per day
    
    def generate_carry_signal(self, funding_rate: float,
                             current_position: float) -> Optional[TradeSignal]:
        """
        Strategy: Long spot + Short perpetual when funding rate positive
        - Entry: 8h rate > 0.01% (annualized > 10%)
        - Exit: 8h rate < -0.01%
        - Risk control: Funding rate volatility > 3x historical std = pause
        """
        pass
```

#### 4.5.3 Asset Rotation Model

```python
class AssetRotationModel:
    """
    Tactical asset allocation combining momentum ranking with risk parity.
    Based on Keller & Butler (2015).
    """
    
    def select_assets(self, momentum_ranks: pd.DataFrame,
                     sma_200: pd.DataFrame) -> List[str]:
        """
        Step 1: Filter by cross-sectional momentum (Top 30%)
        Step 2: Filter by trend (price > SMA_200)
        """
        pass
    
    def optimize_weights(self, selected_assets: List[str],
                        cov_matrix: pd.DataFrame) -> Dict[str, float]:
        """
        Step 3: Apply risk parity optimization on selected subset
        Uses riskfolio-lib for optimization
        """
        pass
    
    def apply_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Step 4: Apply position constraints
        - Monthly turnover < 40%
        - Transaction cost estimate < 0.2%/month
        """
        pass
```

### 4.6 NLP Pipeline (Phase 4 - NEW)

#### 4.6.1 News Sentiment Module

```python
class NewsSentimentAnalyzer:
    """
    News sentiment analysis using FinBERT.
    Outputs sentiment factor for ML model input.
    """
    
    DATA_SOURCES = {
        "newsapi": {"cost": "$449/month", "coverage": "global"},
        "gdelt": {"cost": "free", "coverage": "global"},
        "rss": {"cost": "free", "coverage": "limited"}
    }
    
    def collect_news(self, symbols: List[str], date: str) -> List[NewsArticle]:
        """
        Collect news headlines and summaries.
        Daily volume: ~500-2000 articles
        """
        pass
    
    def analyze_sentiment(self, articles: List[NewsArticle]) -> pd.DataFrame:
        """
        NLP Pipeline:
        1. News collection → Deduplication → Asset tagging (keywords + NER)
        2. FinBERT sentiment analysis → Score (-1, 0, +1)
        3. Aggregate by asset → Daily sentiment score
        4. Sentiment momentum = 5-day moving average change
        
        Compute requirements:
        - GPU recommended (T4/A10), CPU viable but 10x slower
        - Latency: T+1 (daily factor, no real-time requirement)
        """
        pass
```

#### 4.6.2 CFTC COT Sentiment

```python
class COTSentimentAnalyzer:
    """
    Retail positioning from CFTC Commitment of Traders report.
    Weekly release, used as contrarian indicator.
    """
    
    def fetch_cot_data(self) -> pd.DataFrame:
        """
        Source: CFTC.gov (free, released every Friday)
        Alternative: Nasdaq Data Link API for convenience
        """
        pass
    
    def calculate_positioning(self, cot_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate:
        - Non-commercial net long ratio
        - 3-year rolling percentile
        - Extreme signals: >90% = bearish, <10% = bullish (contrarian)
        """
        pass
```

#### 4.6.3 Sentiment Factor Integration

```python
class SentimentFactorIntegrator:
    """
    Integrate sentiment factors into ML feature set.
    Sentiment is INPUT to ML model, not standalone signal.
    """
    
    FACTORS = [
        "Sentiment_News_5d",      # 5-day news sentiment average
        "Sentiment_Momentum",      # Sentiment change rate
        "Sentiment_COT_Percentile" # COT positioning percentile
    ]
    
    def integrate(self, ml_features: pd.DataFrame,
                 sentiment_features: pd.DataFrame) -> pd.DataFrame:
        """
        Integration rules:
        - Sentiment features added to ML feature set
        - Validate via SHAP analysis
        - Remove if SHAP contribution < 5% (reduce model complexity)
        """
        pass
```

### 4.7 Execution Layer

#### 4.7.1 Order Management

```python
class OrderManager:
    """Smart order routing and execution"""
    
    def generate_orders(self, target_positions: Dict, 
                       current_positions: Dict) -> List[Order]:
        """
        Smart order generation:
        - Minimize transaction costs
        - Respect PDT rules
        - Handle wash sale avoidance
        """
        pass
    
    def route_order(self, order: Order) -> ExecutionResult:
        """
        Route to appropriate broker:
        - Alpaca for US equities
        - Binance for crypto
        - IBKR for global markets
        """
        pass
```

#### 4.7.2 Compliance Engine

```python
class ComplianceChecker:
    """Regulatory compliance enforcement"""
    
    def check_pdt_rule(self, account_value: float, 
                      day_trades: int) -> bool:
        """Pattern Day Trader rule enforcement"""
        pass
    
    def check_wash_sale(self, sell_transaction: Transaction) -> bool:
        """Wash sale rule checking"""
        pass
```

### 4.8 Monitoring & Alerting

#### 4.8.1 Alert Levels

```python
class AlertManager:
    """Multi-channel alerting system"""
    
    ALERT_LEVELS = {
        "INFO": ["Daily summary", "Normal signals"],
        "WARNING": ["Risk Level 1", "Data quality issues"],
        "CRITICAL": ["Risk Level 2+", "System errors"],
        "EMERGENCY": ["Risk Level 4", "System crash"]
    }
    
    def send_alert(self, level: str, message: str, context: dict):
        """Send via Slack, Email, Telegram using apprise"""
        pass
```

### 4.9 State Persistence & Disaster Recovery (NEW)

#### 4.9.1 State Manager

```python
class StateManager:
    """Persist portfolio state for crash recovery"""
    
    PERSISTENCE_ITEMS = [
        "portfolio_state",     # Positions, cost basis, unrealized P&L
        "risk_state",          # Current level, peak NAV, drawdown
        "trade_history",       # Complete audit trail
        "signal_history",      # Signals with reasoning
        "pending_orders"       # Orders not yet confirmed
    ]
    
    def save_state(self, portfolio: Portfolio) -> None:
        """
        Persist to SQLite (portfolio.db).
        Backup: Daily automatic backup, 30-day retention.
        """
        pass
    
    def load_state(self) -> Portfolio:
        """Restore from most recent persisted state"""
        pass
```

#### 4.9.2 Disaster Recovery

```python
class DisasterRecoveryManager:
    """Handle system crash recovery"""
    
    def recover(self) -> RecoveryReport:
        """
        Recovery flow:
        1. Load last persisted portfolio state
        2. Query broker API for pending order status
        3. Cancel unexecuted orders
        4. Update state for partially executed orders
        5. Write recovery log
        6. Resume normal operation
        """
        pass
    
    def reconcile_with_broker(self, local_state: Portfolio,
                             broker_state: Dict) -> List[Discrepancy]:
        """
        Reconcile local state with broker actual positions.
        Flag any discrepancies for manual review.
        """
        pass
```

### 4.10 Stress Testing Framework (NEW)

#### 4.10.1 Stress Test Scenarios

| Scenario | Period | Description | Max DD Limit |
|----------|--------|-------------|--------------|
| 2008 Financial Crisis | 2008-2009 | Global market crash | < 25% |
| COVID Crash | 2020-03 | Rapid market selloff | < 18% |
| 2022 Rate Hikes | 2022 | Rising rates + crypto winter | < 20% |
| All-Asset Decline | Custom | Simulated 20% drop in all assets | < 22% |

#### 4.10.2 Stress Tester Class

```python
class StressTester:
    """Run strategy through historical crisis periods"""
    
    SCENARIOS = {
        "2008_crisis": {"start": "2008-01-01", "end": "2009-12-31", "max_dd": 0.25},
        "covid_crash": {"start": "2020-02-01", "end": "2020-06-30", "max_dd": 0.18},
        "2022_rates": {"start": "2022-01-01", "end": "2022-12-31", "max_dd": 0.20},
        "all_asset_decline": {"type": "synthetic", "decline": 0.20, "max_dd": 0.22}
    }
    
    PASS_CRITERIA = {
        "max_single_scenario_dd": 0.25,
        "avg_scenario_dd": 0.18,
        "no_level_4_trigger": True
    }
    
    def run_stress_tests(self, strategy: Strategy) -> StressTestReport:
        """
        Run all scenarios and validate against criteria.
        Must pass ALL criteria before paper trading.
        """
        pass
    
    def generate_synthetic_scenario(self, decline_pct: float) -> pd.DataFrame:
        """Generate synthetic all-asset decline scenario"""
        pass
```

### 4.11 Paper Trading System (Phase 5 - NEW)

#### 4.11.1 Paper Trading Engine

```python
class PaperTradingEngine:
    """
    Simulates real trading execution with realistic market conditions.
    Based on PRD FR-5.1 requirements.
    """
    
    # Slippage model parameters
    SLIPPAGE_CONFIG = {
        "base_slippage_bps": 5,           # 5 bps base slippage
        "volatility_multiplier": 0.1,     # Additional slippage per 1% volatility
        "size_impact_threshold": 10000,   # Orders above this get extra slippage
        "size_impact_bps_per_10k": 2      # Additional bps per $10k over threshold
    }
    
    # Execution delay model
    DELAY_CONFIG = {
        "min_delay_seconds": 60,          # Minimum 1 minute
        "max_delay_seconds": 1800,        # Maximum 30 minutes
        "market_order_delay": 60,         # Market orders: 1 minute
        "limit_order_delay": 300,         # Limit orders: 5 minutes
        "twap_interval_minutes": 15       # TWAP slice interval
    }
    
    def __init__(self, market_data_provider: 'DataProvider'):
        self.data_provider = market_data_provider
        self.pending_orders: List['PaperOrder'] = []
        self.executed_orders: List['PaperExecutionResult'] = []
        self.portfolio_state: 'Portfolio' = None
    
    def submit_order(self, order: 'Order') -> 'PaperOrder':
        """
        Submit order for paper execution.
        Calculates expected slippage and execution time.
        """
        slippage = self._calculate_slippage(order)
        delay = self._calculate_delay(order)
        
        paper_order = PaperOrder(
            order=order,
            expected_slippage=slippage,
            expected_execution_time=datetime.now() + timedelta(seconds=delay),
            status="PENDING"
        )
        self.pending_orders.append(paper_order)
        return paper_order
    
    def _calculate_slippage(self, order: 'Order') -> float:
        """
        Calculate realistic slippage based on:
        - Base slippage
        - Current volatility
        - Order size relative to average volume
        """
        volatility = self.data_provider.get_current_volatility(order.symbol)
        base = self.SLIPPAGE_CONFIG["base_slippage_bps"] / 10000
        vol_impact = volatility * self.SLIPPAGE_CONFIG["volatility_multiplier"]
        
        # Size impact for large orders
        order_value = order.quantity * order.limit_price if order.limit_price else 0
        size_impact = 0
        if order_value > self.SLIPPAGE_CONFIG["size_impact_threshold"]:
            excess = order_value - self.SLIPPAGE_CONFIG["size_impact_threshold"]
            size_impact = (excess / 10000) * self.SLIPPAGE_CONFIG["size_impact_bps_per_10k"] / 10000
        
        return base + vol_impact + size_impact
    
    def execute_pending_orders(self) -> List['PaperExecutionResult']:
        """
        Execute orders that have reached their execution time.
        Simulates partial fills for large orders.
        """
        results = []
        current_time = datetime.now()
        
        for paper_order in self.pending_orders:
            if paper_order.expected_execution_time <= current_time:
                result = self._execute_single_order(paper_order)
                results.append(result)
                self.executed_orders.append(result)
        
        # Remove executed orders from pending
        self.pending_orders = [o for o in self.pending_orders 
                              if o.expected_execution_time > current_time]
        return results
    
    def _execute_single_order(self, paper_order: 'PaperOrder') -> 'PaperExecutionResult':
        """
        Execute a single order with slippage applied.
        Returns execution result with actual fill price.
        """
        order = paper_order.order
        current_price = self.data_provider.get_current_price(order.symbol)
        
        # Apply slippage (negative for buys, positive for sells)
        if order.action == "BUY":
            fill_price = current_price * (1 + paper_order.expected_slippage)
        else:
            fill_price = current_price * (1 - paper_order.expected_slippage)
        
        return PaperExecutionResult(
            order=order,
            fill_price=fill_price,
            fill_quantity=order.quantity,
            slippage_actual=paper_order.expected_slippage,
            execution_time=datetime.now(),
            status="FILLED"
        )
```

#### 4.11.2 Real-Time Performance Monitor

```python
class RealTimePerformanceMonitor:
    """
    Real-time tracking of portfolio performance metrics.
    Based on PRD FR-5.2 requirements.
    """
    
    ROLLING_WINDOWS = {
        "sharpe_short": 20,     # 20-day rolling Sharpe
        "sharpe_medium": 60,   # 60-day rolling Sharpe
        "sharpe_long": 252,    # 252-day rolling Sharpe
        "ic_window": 20,       # 20-day rolling IC
        "ks_window": 20        # 20-day KS comparison window
    }
    
    IC_THRESHOLDS = {
        "warning": 0.02,       # IC below this triggers warning
        "critical": 0.0,       # IC below this triggers model review
        "retrain": 0.02        # IC below this for 10 days triggers retrain
    }
    
    KS_THRESHOLDS = {
        "warning": 0.1,        # KS statistic above this triggers warning
        "critical": 0.2        # KS above this triggers retrain
    }
    
    def __init__(self, portfolio: 'Portfolio'):
        self.portfolio = portfolio
        self.returns_history: pd.Series = pd.Series(dtype=float)
        self.predictions_history: pd.DataFrame = pd.DataFrame()
        self.actuals_history: pd.DataFrame = pd.DataFrame()
        self.feature_history: pd.DataFrame = pd.DataFrame()
        self.training_feature_distribution: pd.DataFrame = None
    
    def update_nav(self, current_prices: Dict[str, float]) -> float:
        """Update portfolio NAV in real-time"""
        nav = self.portfolio.cash
        for symbol, quantity in self.portfolio.positions.items():
            nav += quantity * current_prices.get(symbol, 0)
        self.portfolio.nav = nav
        return nav
    
    def calculate_realtime_pnl(self) -> Dict[str, float]:
        """Calculate real-time P&L breakdown"""
        return {
            "unrealized_pnl": self.portfolio.unrealized_pnl,
            "realized_pnl": sum(self.portfolio.realized_pnl_history),
            "total_pnl": self.portfolio.nav - self.portfolio.initial_capital,
            "pnl_pct": (self.portfolio.nav / self.portfolio.initial_capital - 1) * 100
        }
    
    def calculate_rolling_sharpe(self, window: int = 20) -> float:
        """
        Calculate rolling Sharpe ratio.
        Uses annualized returns and volatility.
        """
        if len(self.returns_history) < window:
            return 0.0
        
        recent_returns = self.returns_history.tail(window)
        annualized_return = recent_returns.mean() * 252
        annualized_vol = recent_returns.std() * np.sqrt(252)
        
        if annualized_vol == 0:
            return 0.0
        return annualized_return / annualized_vol
    
    def calculate_max_drawdown(self) -> float:
        """Calculate current maximum drawdown from peak NAV"""
        if self.portfolio.peak_nav == 0:
            return 0.0
        return (self.portfolio.peak_nav - self.portfolio.nav) / self.portfolio.peak_nav
    
    def track_ic(self, predictions: pd.Series, actuals: pd.Series) -> float:
        """
        Track Information Coefficient (IC) - correlation between predictions and actuals.
        Rolling 20-day IC for model quality monitoring.
        """
        self.predictions_history = pd.concat([self.predictions_history, predictions])
        self.actuals_history = pd.concat([self.actuals_history, actuals])
        
        if len(self.predictions_history) < self.ROLLING_WINDOWS["ic_window"]:
            return np.nan
        
        recent_pred = self.predictions_history.tail(self.ROLLING_WINDOWS["ic_window"])
        recent_actual = self.actuals_history.tail(self.ROLLING_WINDOWS["ic_window"])
        
        ic = recent_pred.corrwith(recent_actual).mean()
        return ic
    
    def track_ks_drift(self, current_features: pd.DataFrame) -> float:
        """
        Track Kolmogorov-Smirnov statistic for concept drift detection.
        Compares current feature distribution to training distribution.
        """
        if self.training_feature_distribution is None:
            return 0.0
        
        ks_stats = []
        for col in current_features.columns:
            if col in self.training_feature_distribution.columns:
                ks_stat, _ = scipy.stats.ks_2samp(
                    self.training_feature_distribution[col].dropna(),
                    current_features[col].dropna()
                )
                ks_stats.append(ks_stat)
        
        return np.mean(ks_stats) if ks_stats else 0.0
    
    def generate_daily_report(self) -> 'DailyPerformanceReport':
        """Generate comprehensive daily performance report"""
        return DailyPerformanceReport(
            date=datetime.now().date(),
            nav=self.portfolio.nav,
            daily_return=self.returns_history.iloc[-1] if len(self.returns_history) > 0 else 0,
            cumulative_return=(self.portfolio.nav / self.portfolio.initial_capital - 1),
            sharpe_20d=self.calculate_rolling_sharpe(20),
            sharpe_60d=self.calculate_rolling_sharpe(60),
            max_drawdown=self.calculate_max_drawdown(),
            rolling_ic=self.track_ic(self.predictions_history.tail(1), self.actuals_history.tail(1)),
            ks_drift=self.track_ks_drift(self.feature_history.tail(self.ROLLING_WINDOWS["ks_window"]))
        )
```

#### 4.11.3 Gate Validation System

```python
class GateValidationSystem:
    """
    Automated validation of paper trading gates.
    Based on PRD FR-5.3 requirements.
    """
    
    # Phase 1+2 Paper Trading Gates
    PHASE_1_2_GATES = {
        "min_trading_days": 63,           # Minimum 3 months
        "min_sharpe": 0.5,                # Sharpe ratio threshold
        "max_drawdown": 0.15,             # 15% max drawdown
        "min_availability": 0.999,        # 99.9% system availability
        "risk_level_coverage": [1, 2, 3, 4],  # All levels must trigger at least once
        "min_rolling_ic": 0.02            # Rolling IC threshold
    }
    
    # Phase 3 (ML) Additional Gates
    PHASE_3_GATES = {
        "ml_outperformance": True,        # ML must beat traditional
        "min_trading_days": 63,           # Additional 3 months
        "max_drawdown": 0.15,
        "min_ic_sustained": 0.02          # IC must stay above threshold
    }
    
    def __init__(self, performance_monitor: 'RealTimePerformanceMonitor'):
        self.monitor = performance_monitor
        self.trading_days_count = 0
        self.risk_levels_triggered: Set[int] = set()
        self.system_uptime_seconds = 0
        self.total_seconds = 0
        self.gate_history: List['GateCheckResult'] = []
    
    def record_trading_day(self) -> None:
        """Record a completed trading day"""
        self.trading_days_count += 1
    
    def record_risk_level_trigger(self, level: int) -> None:
        """Record when a risk level is triggered"""
        self.risk_levels_triggered.add(level)
    
    def validate_phase_1_2_gates(self) -> 'GateValidationResult':
        """
        Validate all Phase 1+2 paper trading gates.
        Returns detailed result with pass/fail for each gate.
        """
        gates = self.PHASE_1_2_GATES
        results = {}
        
        # Gate 1: Minimum trading days
        results["min_trading_days"] = {
            "required": gates["min_trading_days"],
            "actual": self.trading_days_count,
            "passed": self.trading_days_count >= gates["min_trading_days"]
        }
        
        # Gate 2: Sharpe ratio
        current_sharpe = self.monitor.calculate_rolling_sharpe(252)
        results["sharpe_ratio"] = {
            "required": f"> {gates['min_sharpe']}",
            "actual": current_sharpe,
            "passed": current_sharpe > gates["min_sharpe"]
        }
        
        # Gate 3: Maximum drawdown
        current_dd = self.monitor.calculate_max_drawdown()
        results["max_drawdown"] = {
            "required": f"< {gates['max_drawdown'] * 100}%",
            "actual": f"{current_dd * 100:.2f}%",
            "passed": current_dd < gates["max_drawdown"]
        }
        
        # Gate 4: System availability
        availability = self.system_uptime_seconds / self.total_seconds if self.total_seconds > 0 else 0
        results["system_availability"] = {
            "required": f"> {gates['min_availability'] * 100}%",
            "actual": f"{availability * 100:.3f}%",
            "passed": availability >= gates["min_availability"]
        }
        
        # Gate 5: Risk level coverage
        results["risk_level_coverage"] = {
            "required": set(gates["risk_level_coverage"]),
            "actual": self.risk_levels_triggered,
            "passed": self.risk_levels_triggered >= set(gates["risk_level_coverage"])
        }
        
        # Gate 6: Rolling IC (for ML phases)
        # Only applicable if ML is active
        
        all_passed = all(r["passed"] for r in results.values())
        
        return GateValidationResult(
            phase="Phase 1+2",
            gates=results,
            overall_passed=all_passed,
            validation_date=datetime.now()
        )
    
    def generate_deviation_report(self, backtest_results: 'BacktestResult') -> 'DeviationReport':
        """
        Compare paper trading results with backtest expectations.
        Identify significant deviations for investigation.
        """
        paper_sharpe = self.monitor.calculate_rolling_sharpe(252)
        paper_dd = self.monitor.calculate_max_drawdown()
        paper_return = (self.monitor.portfolio.nav / self.monitor.portfolio.initial_capital - 1)
        
        return DeviationReport(
            metric_comparisons={
                "sharpe_ratio": {
                    "backtest": backtest_results.sharpe_ratio,
                    "paper": paper_sharpe,
                    "deviation": abs(paper_sharpe - backtest_results.sharpe_ratio)
                },
                "max_drawdown": {
                    "backtest": backtest_results.max_drawdown,
                    "paper": paper_dd,
                    "deviation": abs(paper_dd - backtest_results.max_drawdown)
                },
                "return": {
                    "backtest": backtest_results.total_return,
                    "paper": paper_return,
                    "deviation": abs(paper_return - backtest_results.total_return)
                }
            },
            significant_deviations=[
                m for m, v in {
                    "sharpe_ratio": abs(paper_sharpe - backtest_results.sharpe_ratio) > 0.3,
                    "max_drawdown": abs(paper_dd - backtest_results.max_drawdown) > 0.05,
                    "return": abs(paper_return - backtest_results.total_return) > 0.05
                }.items() if v
            ]
        )
```

### 4.12 Live Trading System (Phase 6 - NEW)

#### 4.12.1 Broker Integration Layer

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import asyncio

class BrokerAdapter(ABC):
    """
    Abstract broker adapter for multi-broker support.
    Based on PRD FR-6.1 requirements.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to broker API"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> 'AccountInfo':
        """Get account balance, buying power, positions"""
        pass
    
    @abstractmethod
    async def submit_order(self, order: 'Order') -> 'OrderResponse':
        """Submit order to broker"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> 'OrderStatus':
        """Get status of submitted order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        pass
    
    @abstractmethod
    async def subscribe_positions(self, callback: callable) -> None:
        """Subscribe to real-time position updates via WebSocket"""
        pass


class AlpacaAdapter(BrokerAdapter):
    """
    Alpaca broker adapter for US ETFs.
    Supports REST API and WebSocket streaming.
    """
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self.ws_url = "wss://stream.data.alpaca.markets/v2/iex"
        self.session = None
        self.ws_connection = None
    
    async def connect(self) -> bool:
        """Connect to Alpaca API"""
        # Implementation: Initialize aiohttp session, authenticate
        pass
    
    async def submit_order(self, order: 'Order') -> 'OrderResponse':
        """
        Submit order to Alpaca.
        Supports: market, limit, stop, stop_limit orders.
        """
        payload = {
            "symbol": order.symbol,
            "qty": order.quantity,
            "side": order.action.lower(),
            "type": order.order_type.lower(),
            "time_in_force": "day"
        }
        if order.limit_price:
            payload["limit_price"] = order.limit_price
        
        # POST to /v2/orders
        pass


class BinanceAdapter(BrokerAdapter):
    """
    Binance adapter for cryptocurrency trading.
    Supports spot and futures markets.
    """
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        self.futures_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
    
    async def submit_order(self, order: 'Order') -> 'OrderResponse':
        """
        Submit order to Binance.
        Handles signature generation for authenticated endpoints.
        """
        pass


class IBKRAdapter(BrokerAdapter):
    """
    Interactive Brokers adapter for global markets.
    Uses TWS API via ib_insync library.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497):
        self.host = host
        self.port = port
        self.ib = None  # ib_insync.IB instance
    
    async def connect(self) -> bool:
        """Connect to TWS/Gateway"""
        pass
```

#### 4.12.2 Order Management System

```python
class OrderManagementSystem:
    """
    Intelligent order management with routing and retry logic.
    Based on PRD FR-6.2 requirements.
    """
    
    # Order routing configuration
    ROUTING_CONFIG = {
        "US_ETF": "alpaca",
        "CRYPTO": "binance",
        "GLOBAL": "ibkr"
    }
    
    # Order splitting thresholds
    SPLIT_CONFIG = {
        "max_single_order_usd": 50000,     # Split orders above this
        "max_pct_of_volume": 0.01,         # Max 1% of average daily volume
        "slice_count": 5,                   # Number of slices for TWAP
        "slice_interval_minutes": 5         # Time between slices
    }
    
    # Retry configuration
    RETRY_CONFIG = {
        "max_retries": 3,
        "retry_delay_seconds": 5,
        "exponential_backoff": True
    }
    
    def __init__(self, brokers: Dict[str, 'BrokerAdapter']):
        self.brokers = brokers
        self.pending_orders: Dict[str, 'ManagedOrder'] = {}
        self.order_log: List['OrderLogEntry'] = []
    
    def route_order(self, order: 'Order') -> str:
        """
        Determine which broker to use for the order.
        Based on asset type and availability.
        """
        if order.symbol.endswith("-USD") or order.symbol in ["BTC", "ETH"]:
            return "binance"
        elif order.symbol in ["GLD", "SPY", "QQQ", "SLV", "XLK", "XLF", "TLT"]:
            return "alpaca"
        else:
            return "ibkr"
    
    def should_split_order(self, order: 'Order', current_price: float) -> bool:
        """Determine if order should be split into smaller pieces"""
        order_value = order.quantity * current_price
        return order_value > self.SPLIT_CONFIG["max_single_order_usd"]
    
    def split_order(self, order: 'Order', current_price: float) -> List['Order']:
        """
        Split large order into TWAP slices.
        Returns list of smaller orders to be executed over time.
        """
        total_value = order.quantity * current_price
        slice_count = min(
            self.SPLIT_CONFIG["slice_count"],
            int(total_value / self.SPLIT_CONFIG["max_single_order_usd"]) + 1
        )
        
        slice_quantity = order.quantity / slice_count
        slices = []
        
        for i in range(slice_count):
            slice_order = Order(
                symbol=order.symbol,
                action=order.action,
                quantity=slice_quantity,
                order_type="LIMIT",
                limit_price=current_price * (1.001 if order.action == "BUY" else 0.999),
                reason=f"{order.reason} (slice {i+1}/{slice_count})"
            )
            slices.append(slice_order)
        
        return slices
    
    async def execute_with_retry(self, order: 'Order') -> 'OrderExecutionResult':
        """
        Execute order with retry logic on failure.
        Implements exponential backoff.
        """
        broker_name = self.route_order(order)
        broker = self.brokers[broker_name]
        
        for attempt in range(self.RETRY_CONFIG["max_retries"]):
            try:
                result = await broker.submit_order(order)
                self._log_order(order, result, broker_name, attempt + 1)
                return result
            except Exception as e:
                if attempt < self.RETRY_CONFIG["max_retries"] - 1:
                    delay = self.RETRY_CONFIG["retry_delay_seconds"] * (2 ** attempt if self.RETRY_CONFIG["exponential_backoff"] else 1)
                    await asyncio.sleep(delay)
                else:
                    self._log_order(order, None, broker_name, attempt + 1, error=str(e))
                    raise
    
    def _log_order(self, order: 'Order', result: Optional['OrderResponse'], 
                   broker: str, attempt: int, error: str = None) -> None:
        """Log all order activity for audit trail"""
        self.order_log.append(OrderLogEntry(
            timestamp=datetime.now(),
            order=order,
            broker=broker,
            attempt=attempt,
            result=result,
            error=error
        ))
```

#### 4.12.3 Capital Transition Manager

```python
class CapitalTransitionManager:
    """
    Manages gradual capital deployment from paper to live trading.
    Based on PRD FR-6.2 capital transition requirements.
    """
    
    # Transition stages
    STAGES = [
        {"name": "Stage 1", "capital_pct": 0.10, "duration_weeks": 4, "loss_limit": 0.05},
        {"name": "Stage 2", "capital_pct": 0.25, "duration_weeks": 4, "loss_limit": 0.05},
        {"name": "Stage 3", "capital_pct": 0.50, "duration_weeks": 2, "loss_limit": 0.05},
        {"name": "Stage 4", "capital_pct": 1.00, "duration_weeks": None, "loss_limit": 0.10}  # Final stage
    ]
    
    # Rollback triggers
    ROLLBACK_TRIGGERS = {
        "daily_loss_threshold": 0.03,      # Single day loss > 3% triggers evaluation
        "cumulative_dd_threshold": 0.10,   # Cumulative drawdown > 10% rolls back
        "system_failure_count": 2           # 2+ failures rolls back to paper
    }
    
    def __init__(self, total_capital: float):
        self.total_capital = total_capital
        self.current_stage = 0
        self.stage_start_date: datetime = None
        self.stage_start_nav: float = None
        self.system_failure_count = 0
        self.transition_log: List['TransitionEvent'] = []
    
    def get_current_allocation(self) -> float:
        """Get current capital allocation amount"""
        return self.total_capital * self.STAGES[self.current_stage]["capital_pct"]
    
    def can_advance_stage(self, current_nav: float, days_in_stage: int) -> Tuple[bool, str]:
        """
        Check if conditions are met to advance to next stage.
        Returns (can_advance, reason)
        """
        stage = self.STAGES[self.current_stage]
        
        # Check if at final stage
        if self.current_stage >= len(self.STAGES) - 1:
            return False, "Already at final stage"
        
        # Check duration requirement
        required_days = stage["duration_weeks"] * 7 if stage["duration_weeks"] else float('inf')
        if days_in_stage < required_days:
            return False, f"Need {required_days - days_in_stage} more days in current stage"
        
        # Check loss limit
        stage_return = (current_nav - self.stage_start_nav) / self.stage_start_nav
        if stage_return < -stage["loss_limit"]:
            return False, f"Stage loss {stage_return:.2%} exceeds limit {-stage['loss_limit']:.2%}"
        
        return True, "All conditions met for advancement"
    
    def check_rollback_triggers(self, daily_return: float, cumulative_dd: float) -> Optional[str]:
        """
        Check if any rollback conditions are triggered.
        Returns rollback action or None.
        """
        # Daily loss trigger
        if daily_return < -self.ROLLBACK_TRIGGERS["daily_loss_threshold"]:
            self._log_transition("EVALUATION", f"Daily loss {daily_return:.2%} exceeded threshold")
            return "EVALUATE"
        
        # Cumulative drawdown trigger
        if cumulative_dd > self.ROLLBACK_TRIGGERS["cumulative_dd_threshold"]:
            self._log_transition("ROLLBACK", f"Cumulative DD {cumulative_dd:.2%} exceeded threshold")
            return "ROLLBACK_STAGE"
        
        # System failure trigger
        if self.system_failure_count >= self.ROLLBACK_TRIGGERS["system_failure_count"]:
            self._log_transition("ROLLBACK_TO_PAPER", f"{self.system_failure_count} system failures")
            return "ROLLBACK_TO_PAPER"
        
        return None
    
    def advance_stage(self) -> bool:
        """Advance to next stage if conditions are met"""
        if self.current_stage < len(self.STAGES) - 1:
            self.current_stage += 1
            self.stage_start_date = datetime.now()
            self._log_transition("ADVANCE", f"Advanced to {self.STAGES[self.current_stage]['name']}")
            return True
        return False
    
    def rollback_stage(self) -> bool:
        """Rollback to previous stage"""
        if self.current_stage > 0:
            self.current_stage -= 1
            self.stage_start_date = datetime.now()
            self._log_transition("ROLLBACK", f"Rolled back to {self.STAGES[self.current_stage]['name']}")
            return True
        return False
    
    def _log_transition(self, action: str, reason: str) -> None:
        """Log transition event for audit"""
        self.transition_log.append(TransitionEvent(
            timestamp=datetime.now(),
            action=action,
            from_stage=self.current_stage,
            reason=reason
        ))
```

#### 4.12.4 Live Monitoring System

```python
class LiveMonitoringSystem:
    """
    Real-time monitoring for live trading operations.
    Based on PRD FR-6.3 requirements.
    """
    
    # System health thresholds
    HEALTH_THRESHOLDS = {
        "api_response_time_ms": 1000,      # Max 1 second API response
        "data_freshness_minutes": 30,       # Data must be < 30 min old
        "memory_usage_pct": 80,             # Max 80% memory usage
        "cpu_usage_pct": 80                 # Max 80% CPU usage
    }
    
    # Strategy performance alerts
    PERFORMANCE_ALERTS = {
        "deviation_sigma": 2.0,             # Alert if performance deviates > 2 sigma
        "sharpe_warning": 0.3,              # Sharpe below this triggers warning
        "drawdown_warning": 0.10,           # Drawdown above this triggers warning
        "drawdown_critical": 0.15           # Drawdown above this triggers critical alert
    }
    
    # Model quality thresholds
    MODEL_QUALITY = {
        "ic_warning": 0.02,                 # IC below this triggers warning
        "ic_retrain": 0.02,                 # IC below this for 10 days triggers retrain
        "ks_warning": 0.1,                  # KS above this triggers warning
        "ks_retrain": 0.2                   # KS above this triggers retrain
    }
    
    def __init__(self, alert_manager: 'AlertManager'):
        self.alert_manager = alert_manager
        self.health_history: List['HealthCheck'] = []
        self.performance_history: List['PerformanceSnapshot'] = []
        self.ic_history: List[float] = []
        self.ks_history: List[float] = []
    
    async def check_system_health(self) -> 'HealthReport':
        """
        Comprehensive system health check.
        Returns health report with any issues identified.
        """
        issues = []
        
        # Check API response times
        api_times = await self._check_api_latencies()
        for api, latency in api_times.items():
            if latency > self.HEALTH_THRESHOLDS["api_response_time_ms"]:
                issues.append(f"{api} API latency {latency}ms exceeds threshold")
        
        # Check data freshness
        data_age = self._check_data_freshness()
        if data_age > self.HEALTH_THRESHOLDS["data_freshness_minutes"]:
            issues.append(f"Data is {data_age} minutes old, exceeds {self.HEALTH_THRESHOLDS['data_freshness_minutes']} min threshold")
        
        # Check resource usage
        memory_pct, cpu_pct = self._check_resource_usage()
        if memory_pct > self.HEALTH_THRESHOLDS["memory_usage_pct"]:
            issues.append(f"Memory usage {memory_pct}% exceeds threshold")
        if cpu_pct > self.HEALTH_THRESHOLDS["cpu_usage_pct"]:
            issues.append(f"CPU usage {cpu_pct}% exceeds threshold")
        
        health_status = "HEALTHY" if not issues else "DEGRADED"
        return HealthReport(status=health_status, issues=issues, timestamp=datetime.now())
    
    def check_performance_deviation(self, daily_return: float, 
                                   expected_daily_std: float) -> Optional['Alert']:
        """
        Check if daily performance deviates significantly from expectation.
        Returns alert if deviation exceeds threshold.
        """
        deviation_sigma = abs(daily_return) / expected_daily_std if expected_daily_std > 0 else 0
        
        if deviation_sigma > self.PERFORMANCE_ALERTS["deviation_sigma"]:
            return Alert(
                level="WARNING",
                message=f"Daily return {daily_return:.2%} deviates {deviation_sigma:.1f} sigma from expectation",
                context={"daily_return": daily_return, "deviation_sigma": deviation_sigma}
            )
        return None
    
    def check_model_quality(self, current_ic: float, current_ks: float) -> List['Alert']:
        """
        Monitor ML model quality via IC and KS metrics.
        Returns list of alerts if thresholds breached.
        """
        alerts = []
        self.ic_history.append(current_ic)
        self.ks_history.append(current_ks)
        
        # Check IC
        if current_ic < self.MODEL_QUALITY["ic_warning"]:
            alerts.append(Alert(
                level="WARNING",
                message=f"Rolling IC {current_ic:.4f} below warning threshold {self.MODEL_QUALITY['ic_warning']}",
                context={"action": "PREPARE_RETRAIN"}
            ))
        
        # Check if IC has been low for 10 consecutive days
        if len(self.ic_history) >= 10:
            recent_ic = self.ic_history[-10:]
            if all(ic < self.MODEL_QUALITY["ic_retrain"] for ic in recent_ic):
                alerts.append(Alert(
                    level="CRITICAL",
                    message=f"IC below {self.MODEL_QUALITY['ic_retrain']} for 10 consecutive days - triggering retrain",
                    context={"action": "TRIGGER_RETRAIN"}
                ))
        
        # Check KS drift
        if current_ks > self.MODEL_QUALITY["ks_retrain"]:
            alerts.append(Alert(
                level="CRITICAL",
                message=f"KS drift {current_ks:.4f} exceeds retrain threshold {self.MODEL_QUALITY['ks_retrain']}",
                context={"action": "TRIGGER_RETRAIN"}
            ))
        elif current_ks > self.MODEL_QUALITY["ks_warning"]:
            alerts.append(Alert(
                level="WARNING",
                message=f"KS drift {current_ks:.4f} exceeds warning threshold {self.MODEL_QUALITY['ks_warning']}",
                context={"action": "MONITOR_CLOSELY"}
            ))
        
        return alerts
    
    async def _check_api_latencies(self) -> Dict[str, int]:
        """Check response times for all connected APIs"""
        # Implementation: Ping each broker API and measure response time
        pass
    
    def _check_data_freshness(self) -> int:
        """Check age of most recent market data in minutes"""
        # Implementation: Compare latest data timestamp to current time
        pass
    
    def _check_resource_usage(self) -> Tuple[float, float]:
        """Check current memory and CPU usage"""
        import psutil
        return psutil.virtual_memory().percent, psutil.cpu_percent()
```

### 4.13 DevOps Automation (Phase 7 - NEW)

#### 4.13.1 CI/CD Pipeline

```python
class CICDPipeline:
    """
    Automated deployment pipeline for trading system.
    Based on PRD Phase 7 requirements.
    """
    
    # Pipeline stages
    STAGES = [
        "lint",           # Code quality (black, ruff, mypy)
        "test_unit",      # Unit tests (pytest)
        "test_integration", # Integration tests
        "security_scan",  # Security scanning (bandit, safety)
        "build",          # Docker build
        "deploy_staging", # Deploy to staging
        "test_staging",   # Smoke tests on staging
        "deploy_prod"     # Deploy to production
    ]
    
    # Deployment targets
    TARGETS = {
        "staging": {
            "host": "staging.trading.internal",
            "requires_approval": False
        },
        "production": {
            "host": "prod.trading.internal",
            "requires_approval": True,
            "approval_timeout_hours": 24
        }
    }
    
    # Performance targets
    TARGETS_METRICS = {
        "deployment_time_minutes": 10,     # Target < 10 minutes
        "rollback_time_minutes": 2,        # Target < 2 minutes
        "test_coverage_pct": 80            # Minimum 80% coverage
    }
```

#### 4.13.2 Automated Monitoring & Alerting

```python
class AutomatedMonitoring:
    """
    Automated monitoring with self-healing capabilities.
    Target: MTTR < 5 minutes
    """
    
    # Auto-remediation actions
    REMEDIATION_RULES = {
        "high_memory": {
            "condition": "memory_pct > 85",
            "actions": ["clear_cache", "restart_non_critical_services"]
        },
        "api_timeout": {
            "condition": "api_latency > 5000",
            "actions": ["switch_to_backup_api", "alert_oncall"]
        },
        "data_stale": {
            "condition": "data_age_minutes > 60",
            "actions": ["force_data_refresh", "switch_to_backup_source"]
        },
        "broker_disconnect": {
            "condition": "broker_connected == False",
            "actions": ["reconnect_broker", "pause_trading", "alert_critical"]
        }
    }
    
    # Escalation policy
    ESCALATION = {
        "level_1": {"delay_minutes": 0, "channels": ["slack"]},
        "level_2": {"delay_minutes": 5, "channels": ["slack", "email"]},
        "level_3": {"delay_minutes": 15, "channels": ["slack", "email", "pagerduty"]}
    }
    
    async def auto_remediate(self, issue: 'SystemIssue') -> 'RemediationResult':
        """
        Attempt automatic remediation of system issues.
        Returns result indicating if remediation was successful.
        """
        rule = self.REMEDIATION_RULES.get(issue.type)
        if not rule:
            return RemediationResult(success=False, reason="No remediation rule")
        
        for action in rule["actions"]:
            try:
                await self._execute_action(action)
            except Exception as e:
                return RemediationResult(success=False, reason=str(e))
        
        return RemediationResult(success=True, actions_taken=rule["actions"])
    
    async def _execute_action(self, action: str) -> None:
        """Execute a remediation action"""
        actions_map = {
            "clear_cache": self._clear_cache,
            "restart_non_critical_services": self._restart_services,
            "switch_to_backup_api": self._switch_api,
            "force_data_refresh": self._refresh_data,
            "reconnect_broker": self._reconnect_broker,
            "pause_trading": self._pause_trading,
            "alert_oncall": self._alert_oncall,
            "alert_critical": self._alert_critical
        }
        await actions_map[action]()
```

#### 4.13.3 Automated Backup System

```python
class AutomatedBackupSystem:
    """
    Automated backup and recovery system.
    Ensures data integrity and quick recovery.
    """
    
    BACKUP_CONFIG = {
        "database": {
            "frequency": "hourly",
            "retention_days": 30,
            "destination": "s3://trading-backups/db/"
        },
        "state": {
            "frequency": "every_trade",
            "retention_days": 90,
            "destination": "s3://trading-backups/state/"
        },
        "config": {
            "frequency": "on_change",
            "retention_days": 365,
            "destination": "s3://trading-backups/config/"
        },
        "logs": {
            "frequency": "daily",
            "retention_days": 90,
            "destination": "s3://trading-backups/logs/"
        }
    }
    
    async def perform_backup(self, backup_type: str) -> 'BackupResult':
        """Perform backup of specified type"""
        config = self.BACKUP_CONFIG[backup_type]
        
        # Create backup
        backup_path = await self._create_backup(backup_type)
        
        # Upload to S3
        s3_path = await self._upload_to_s3(backup_path, config["destination"])
        
        # Verify backup integrity
        verified = await self._verify_backup(s3_path)
        
        # Clean up old backups
        await self._cleanup_old_backups(config["destination"], config["retention_days"])
        
        return BackupResult(
            success=verified,
            backup_type=backup_type,
            s3_path=s3_path,
            timestamp=datetime.now()
        )
    
    async def restore_from_backup(self, backup_type: str, 
                                 timestamp: datetime = None) -> 'RestoreResult':
        """
        Restore system from backup.
        If timestamp not specified, uses most recent backup.
        """
        pass
```

---

## 5. Data Models

### 5.1 Core Domain Objects

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import pandas as pd

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"

class MarketRegime(Enum):
    NORMAL = "NORMAL"           # VIX < 20
    ELEVATED = "ELEVATED"       # 20 <= VIX < 30
    HIGH_VOL = "HIGH_VOL"       # 30 <= VIX < 40
    EXTREME = "EXTREME"         # VIX >= 40

@dataclass
class TradeSignal:
    symbol: str
    signal: SignalType
    confidence: float  # 0.0 to 1.0
    target_weight: float
    reason: str
    timestamp: datetime
    regime: MarketRegime

@dataclass
class Portfolio:
    positions: Dict[str, float]  # symbol -> quantity
    cash: float
    nav: float  # Net Asset Value
    peak_nav: float  # For drawdown calculation
    weights: Dict[str, float]
    unrealized_pnl: float
    cost_basis: Dict[str, float]  # symbol -> average cost
    target_volatility: float = 0.15

@dataclass
class RiskAssessment:
    level: int  # 0-4
    portfolio_drawdown: float
    correlation_matrix: pd.DataFrame
    violations: List[str]
    recovery_mode: bool = False
    weeks_in_recovery: int = 0

@dataclass
class Order:
    symbol: str
    action: str  # BUY/SELL
    quantity: float
    order_type: str  # MARKET/LIMIT
    limit_price: Optional[float]
    estimated_commission: float
    reason: str
```

### 5.2 Database Schema

```sql
-- portfolio.db SQLite schema

CREATE TABLE portfolio_state (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    nav REAL,
    cash REAL,
    positions_json TEXT,  -- JSON serialized positions
    weights_json TEXT,    -- JSON serialized weights
    unrealized_pnl REAL
);

CREATE TABLE trade_history (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    action TEXT,  -- BUY/SELL
    quantity REAL,
    price REAL,
    commission REAL,
    realized_pnl REAL,
    reason TEXT
);

CREATE TABLE risk_events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    level INTEGER,
    trigger_reason TEXT,
    actions_taken TEXT,
    resolved BOOLEAN DEFAULT FALSE
);

CREATE TABLE signal_log (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    signal TEXT,
    confidence REAL,
    target_weight REAL,
    actual_weight REAL,
    reason TEXT
);
```

---

## 6. Security & Compliance

### 6.1 Data Security

```
Security Measures:
1. API Keys: Environment variables, never in code
2. Data Encryption: At rest (disk encryption), in transit (TLS)
3. Access Control: Principle of least privilege
4. Audit Trail: All transactions logged with timestamps
5. Secrets Management: AWS Secrets Manager or HashiCorp Vault
```

### 6.2 Regulatory Compliance

```
Compliance Features:
1. PDT Rule Enforcement: Automatic trade counting and restriction
2. Wash Sale Prevention: 30-day buy-back tracking
3. Tax Reporting: Automatic 8949 form generation
4. Position Limits: Configurable exposure caps
5. Trade Documentation: Complete audit trail for regulators
```

---

## 7. Performance Requirements

### 7.1 Strategy Performance Targets (from PRD)

| Metric | Target | Minimum Acceptable |
|--------|--------|-------------------|
| Annual Return | > 10% | > 7% |
| Annual Volatility | < 15% | < 18% |
| Sharpe Ratio | > 1.0 | > 0.7 |
| Max Drawdown | < 15% | < 20% |
| Calmar Ratio | > 0.7 | > 0.4 |
| Win Rate | > 52% | > 48% |
| Profit Factor | > 1.3 | > 1.1 |
| Monthly Turnover | < 30% | < 50% |
| Annual Cost Drag | < 1% | < 2% |

### 7.2 System Performance Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Signal Latency | < 1 minute | Data receipt to signal generation |
| Backtest Speed | < 30 seconds | 5-year history, 15 assets |
| Memory Usage | < 4GB | Peak during backtesting |
| Recovery Time | < 5 minutes | Crash to operational |
| Data Refresh | < 30 minutes | Market close to data ready |

### 7.3 Scalability Considerations

```
Current Design: Single-instance deployment
Future Scaling Options:
1. Horizontal scaling: Multiple instances for different asset classes
2. Microservices: Split data, strategy, execution into separate services
3. Message queues: RabbitMQ/Kafka for async processing
4. Load balancing: Distribute computational load
5. Caching layers: Redis for shared state
```

---

## 8. Paper Trading Gates (NEW)

### 8.1 Pre-Paper Trading Requirements

Before entering paper trading, the strategy must pass:

```
Gate 1: Backtest Validation
├── Sharpe Ratio > 0.7 (5-year backtest)
├── Max Drawdown < 20%
├── All stress test scenarios pass
└── No Level 4 risk trigger in any scenario

Gate 2: Code Quality
├── Unit test coverage > 80%
├── Integration tests pass
├── All data quality checks implemented
└── State persistence verified
```

### 8.2 Paper Trading Criteria (Minimum 3 Months)

```
Phase 1+2 Paper Trading Gate:
├── Duration: ≥ 3 months (≥ 63 trading days)
├── Sharpe Ratio > 0.5
├── Max Drawdown < 15%
├── No system crashes or data interruptions
└── All risk control levels triggered at least once (verification)

Phase 3 (ML) Paper Trading Gate:
├── Duration: ≥ 3 months additional
├── ML-enhanced strategy outperforms traditional strategy
├── Max Drawdown < 15%
└── Model IC remains > 0.02 throughout
```

### 8.3 Live Trading Progression

```
Small Capital Gate:
├── Paper trading gate passed
├── Initial capital ≤ 10% of planned total
├── Run for 4 weeks without major issues
└── Live P&L vs paper simulation deviation < 2%

Full Capital Gate:
├── Small capital gate passed
├── Gradual ramp: 10% → 25% → 50% → 100%
├── Each stage minimum 2 weeks
└── Risk controls verified at each stage
```

---

## 9. Deployment Architecture

### 9.1 Development Environment

```dockerfile
# Dockerfile.dev
FROM python:3.10-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install

COPY . .
CMD ["poetry", "run", "python", "scripts/generate_signals.py"]
```

### 9.2 Production Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  trading-engine:
    build: .
    environment:
      - ENV=production
      - POLYGON_API_KEY=${POLYGON_API_KEY}
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    
  monitoring:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  dashboard:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
```

### 9.3 CI/CD Pipeline

```
GitHub Actions Workflow:
1. Code Quality: black, ruff, mypy
2. Unit Tests: pytest with coverage > 80%
3. Integration Tests: Backtest validation
4. Security Scan: bandit, safety
5. Docker Build: Multi-stage build
6. Deployment: SSH to production server
```

---

## 10. Monitoring & Observability

### 10.1 Key Metrics to Track

```
Performance Metrics:
- Portfolio NAV and P&L
- Strategy Sharpe ratio
- Maximum drawdown
- Win rate and profit factor
- Transaction costs

System Metrics:
- API response times
- Data freshness
- Memory and CPU usage
- Error rates and exceptions
- Alert frequency

Risk Metrics:
- Current risk level
- Position concentration
- Correlation levels
- VaR estimates
- Stress test results
```

### 10.2 Dashboard Structure

```
Main Dashboard:
├── Portfolio Overview (NAV, P&L, Risk Level)
├── Strategy Performance (Sharpe, Drawdown, Returns)
├── Risk Indicators (Correlations, Concentration)
├── System Health (API Status, Resource Usage)
└── Recent Alerts (Last 24 hours)
```

---

## 11. Testing Strategy

### 11.1 Test Categories

```
Unit Tests (70% coverage):
- Individual module functionality
- Mathematical calculations
- Data transformations

Integration Tests (20%):
- Module interactions
- Data pipeline flows
- Strategy composition

System Tests (10%):
- End-to-end backtesting
- Stress scenario validation
- Recovery procedures
```

### 11.2 Backtesting Validation

```python
def test_strategy_validity():
    """Validate strategy meets minimum criteria"""
    results = run_backtest(strategy, data_period="5Y")
    
    assert results.sharpe_ratio > 0.7
    assert results.max_drawdown < 0.20
    assert results.win_rate > 0.48
    assert results.volatility < 0.18
    
    # Stress test validation
    stress_results = run_stress_tests(strategy)
    assert all(r.max_drawdown < 0.25 for r in stress_results)
```

---

## 12. Risk Mitigation

### 12.1 Technical Risks

| Risk | Mitigation Strategy |
|------|-------------------|
| Data quality issues | Multi-source validation, automated alerts |
| Model overfitting | CPCV, out-of-sample testing, regularization |
| System downtime | Automated recovery, health checks, alerts |
| Security breaches | Secrets management, access controls, audits |
| Regulatory violations | Compliance engine, automated checking |

### 12.2 Operational Risks

```
Operational Safeguards:
1. Paper trading requirement (≥3 months) before live trading
2. Manual review gates at each risk level escalation
3. Daily performance reporting and anomaly detection
4. Regular backup and disaster recovery testing
5. Clear incident response procedures
```

---

## 13. Future Extensibility

### 13.1 Phase 5-7 Implementation (PRD Aligned)

```
Phase 5: Paper Trading System (Week 30-41)
- Paper trading engine with realistic slippage/delay simulation
- Real-time performance monitoring (IC, KS, Sharpe, Drawdown)
- Automated gate validation system
- Paper vs backtest deviation analysis

Phase 6: Live Trading & Monitoring (Week 42-52)
- Multi-broker integration (Alpaca, Binance, IBKR)
- Intelligent order management system
- Capital transition management (10% → 25% → 50% → 100%)
- Real-time monitoring with automated alerts

Phase 7: DevOps Automation (Week 53+)
- CI/CD pipeline with < 10 minute deployment
- Automated monitoring with MTTR < 5 minutes
- Self-healing remediation rules
- Automated backup with S3 retention
```

### 13.2 Future Extensions (Post Phase 7)

```
Advanced Features:
- Real options pricing for volatility trading
- Reinforcement learning for dynamic position sizing
- Alternative data sources (satellite imagery, web scraping)
- Cross-market arbitrage opportunities

Institutional Features:
- Multi-account management
- Custom strategy marketplace
- Client portal and reporting
- Regulatory reporting automation
```

### 13.3 Architecture Flexibility Points

```
Designed Extension Points:
1. Strategy plugins: Pluggable strategy interface
2. Data adapters: Easy addition of new data sources
3. Broker integrations: Standardized execution interface (see Section 4.12.1)
4. ML model registry: Version-controlled model deployment
5. Risk modules: Configurable risk rules and constraints
6. Monitoring hooks: Extensible alerting and remediation
```

---

## 14. Interface Definitions (NEW)

### 14.1 Core Interfaces (from PRD)

```python
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

class DataProvider(ABC):
    """Multi-source data acquisition interface"""
    
    @abstractmethod
    def fetch(self, symbols: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
        """Fetch OHLCV data for symbols"""
        pass
    
    @abstractmethod
    def validate(self, data: pd.DataFrame) -> 'DataQualityReport':
        """Validate data quality"""
        pass
    
    @abstractmethod
    def get_source_status(self) -> Dict[str, str]:
        """Get health status of each data source"""
        pass


class SignalGenerator(ABC):
    """Trading signal generation interface"""
    
    @abstractmethod
    def generate(self, factors: pd.DataFrame, positions: Dict, 
                regime: 'MarketRegime') -> List['TradeSignal']:
        """Generate trading signals from factors"""
        pass


class PositionManager(ABC):
    """Position sizing and optimization interface"""
    
    @abstractmethod
    def calculate_target(self, signals: List['TradeSignal'], 
                        portfolio_value: float,
                        risk_budget: 'RiskBudget') -> Dict[str, float]:
        """Calculate target position weights"""
        pass


class RiskManagerInterface(ABC):
    """Risk management interface"""
    
    @abstractmethod
    def check(self, portfolio: 'Portfolio') -> 'RiskAssessment':
        """Assess current risk state"""
        pass
    
    @abstractmethod
    def get_risk_level(self) -> int:
        """Get current risk level (0-4)"""
        pass
    
    @abstractmethod
    def get_correlation_matrix(self) -> pd.DataFrame:
        """Get current correlation matrix"""
        pass
    
    @abstractmethod
    def check_reentry_conditions(self) -> bool:
        """Check if re-entry conditions are met"""
        pass


class Backtester(ABC):
    """Backtesting engine interface"""
    
    @abstractmethod
    def run(self, strategy: 'Strategy', 
           data: Dict[str, pd.DataFrame]) -> 'BacktestResult':
        """Run backtest on historical data"""
        pass
    
    @abstractmethod
    def stress_test(self, strategy: 'Strategy', 
                   scenarios: List['StressScenario']) -> 'StressTestReport':
        """Run stress tests on specified scenarios"""
        pass


class StateManagerInterface(ABC):
    """State persistence interface"""
    
    @abstractmethod
    def save(self, portfolio: 'Portfolio') -> None:
        """Persist portfolio state"""
        pass
    
    @abstractmethod
    def load(self) -> 'Portfolio':
        """Load persisted state"""
        pass
    
    @abstractmethod
    def recover(self) -> 'RecoveryReport':
        """Recover from crash"""
        pass


class AlertManagerInterface(ABC):
    """Alert notification interface"""
    
    @abstractmethod
    def send(self, level: 'AlertLevel', message: str, context: Dict) -> None:
        """Send alert via configured channels"""
        pass
```

---

## 15. Implementation Roadmap

### 15.1 Phase 1-4 (PRD Section 9)

See detailed timeline in PRD Section 9 for Phase 1-4 development plan.

### 15.2 Phase 5: Paper Trading System (Week 30-41)

| Week | Component | Deliverables | Gate Criteria |
|------|-----------|--------------|---------------|
| 30-32 | Paper Trading Engine | `PaperTradingEngine` class, slippage/delay models | Simulation accuracy > 95% vs expected |
| 33-35 | Performance Monitor | `RealTimePerformanceMonitor`, IC/KS tracking | Data latency < 1 minute |
| 36-38 | Gate Validation | `GateValidationSystem`, deviation reports | Automated gate checks passing |
| 39-41 | Paper Trading Run | 3-month paper trading execution | Sharpe > 0.5, MaxDD < 15% |

### 15.3 Phase 6: Live Trading (Week 42-52)

| Week | Component | Deliverables | Gate Criteria |
|------|-----------|--------------|---------------|
| 42-44 | Broker Integration | `AlpacaAdapter`, `BinanceAdapter`, `IBKRAdapter` | API success rate > 99% |
| 45-47 | Order Management | `OrderManagementSystem`, smart routing | Order execution no anomalies |
| 48-50 | Stage 1 Live (10%) | `CapitalTransitionManager`, 4-week run | Cumulative loss < 5% |
| 51-52 | Stage 2 Live (25%) | Capital ramp-up | No rollback triggers |

### 15.4 Phase 7: DevOps Automation (Week 53+)

| Week | Component | Deliverables | Gate Criteria |
|------|-----------|--------------|---------------|
| 53-56 | CI/CD Pipeline | GitHub Actions workflow, Docker deployment | Deploy time < 10 minutes |
| 57-60 | Monitoring | `AutomatedMonitoring`, self-healing rules | MTTR < 5 minutes |
| 61-64 | Backup System | `AutomatedBackupSystem`, S3 retention | Restore test passed |
| 65+ | Full Automation | 50%-100% capital, < 1 manual intervention/week | Availability > 99.9% |

---

## 16. Conclusion

This technical design provides a robust foundation for building a production-ready quantitative trading system. The modular architecture enables iterative development while maintaining system reliability and regulatory compliance. Key strengths include:

- **Risk-first approach**: Hierarchical risk management built into core architecture
- **Data quality focus**: Multi-source validation prevents garbage-in-garbage-out
- **Extensible design**: Plugin architecture supports future enhancements
- **Production readiness**: Containerization, monitoring, and alerting from day one
- **Complete lifecycle**: Full coverage from paper trading (Phase 5) through live trading (Phase 6) to automated operations (Phase 7)

The system balances sophistication with practicality, ensuring it can evolve from research prototype to production trading platform with confidence.
