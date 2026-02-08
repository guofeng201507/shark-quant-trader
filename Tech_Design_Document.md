# Intelligent Trading System - Technical Design Document

> **Version**: 1.1  
> **Author**: Technical Architecture Team  
> **Date**: 2026-02-08  
> **Based on**: PRD v2.0  

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-08 | Technical Architecture Team | Initial draft |
| 1.1 | 2026-02-08 | Technical Architecture Team | Added: asset universe specs, detailed factor definitions, re-entry logic, correlation monitoring, cost model, stress test scenarios, paper trading gates, Phase 2/4 strategy details, model lifecycle management, disaster recovery flow, interface definitions |

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

### 13.1 Planned Extensions

```
Phase 5: Advanced Features
- Real options pricing for volatility trading
- Reinforcement learning for dynamic position sizing
- Alternative data sources (satellite imagery, web scraping)
- Cross-market arbitrage opportunities

Phase 6: Institutional Features
- Multi-account management
- Custom strategy marketplace
- Client portal and reporting
- Regulatory reporting automation
```

### 13.2 Architecture Flexibility Points

```
Designed Extension Points:
1. Strategy plugins: Pluggable strategy interface
2. Data adapters: Easy addition of new data sources
3. Broker integrations: Standardized execution interface
4. ML model registry: Version-controlled model deployment
5. Risk modules: Configurable risk rules and constraints
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

See detailed timeline in PRD Section 9. This technical design supports the 4-phase development plan with clear milestones and gates.

---

## 16. Conclusion

This technical design provides a robust foundation for building a production-ready quantitative trading system. The modular architecture enables iterative development while maintaining system reliability and regulatory compliance. Key strengths include:

- **Risk-first approach**: Hierarchical risk management built into core architecture
- **Data quality focus**: Multi-source validation prevents garbage-in-garbage-out
- **Extensible design**: Plugin architecture supports future enhancements
- **Production readiness**: Containerization, monitoring, and alerting from day one

The system balances sophistication with practicality, ensuring it can evolve from research prototype to production trading platform.