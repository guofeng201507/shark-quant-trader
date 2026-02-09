# Shark Quant Trader

**Intelligent Trading Decision System - Phase 2 Enhanced Strategies**

A production-ready quantitative trading system with hierarchical risk management, cross-sectional momentum, crypto carry arbitrage, and tactical asset rotation.

---

## 🎯 Features

### Phase 1 (Complete)
- ✅ **Multi-Source Data Acquisition**: Polygon.io → Binance (public API) → yfinance fallback chain
- ✅ **Technical Factor Calculation**: Momentum, Volatility, SMA, RSI, ATR
- ✅ **VIX-Based Signal Generation**: Market regime filtering (Normal/Elevated/High Vol/Extreme)
- ✅ **4-Level Hierarchical Risk Control**: 5%, 8%, 12%, 15% drawdown triggers
- ✅ **Cross-Asset Correlation Monitoring**: Real-time correlation breach alerts
- ✅ **Position Recovery Management**: Gradual re-entry after Level 4 exits
- ✅ **Portfolio Optimization**: Risk parity principles with constraint checking
- ✅ **Compliance Engine**: Pre-trade and post-trade compliance validation
- ✅ **State Persistence**: SQLite-based disaster recovery
- ✅ **Multi-Channel Alerts**: Email, Slack, Telegram, Discord via Apprise
- ✅ **Backtesting Engine**: Historical performance metrics (Sharpe, Calmar, MaxDD)
- ✅ **Stress Testing**: 5 historical crisis scenarios + Monte Carlo simulation

### Phase 2 (Complete - Enhanced Strategies)
- ✅ **Expanded Asset Universe**: 15 assets (GLD, SPY, QQQ, BTC + 11 ETFs)
- ✅ **Cross-Sectional Momentum (FR-2.1)**: 12-1 month ranking with Top 30% selection
- ✅ **Crypto Carry Strategy (FR-2.2)**: Binance funding rate arbitrage with risk monitoring
- ✅ **Tactical Asset Rotation (FR-2.3)**: Momentum + Risk Parity optimization using riskfolio-lib
- ✅ **Enhanced Data Provider**: Funding rate API integration for carry strategies
- ✅ **Trend Filter**: SMA_200 filter with Defense Mode for adverse market conditions
- ✅ **Volatility Targeting**: Portfolio-level volatility scaling with 1.5x leverage cap

### Phase 3 (Complete - ML Enhancement)
- ✅ **Feature Engineering (FR-3.1)**: Price, macro, and cross-sectional features with IC-based selection
- ✅ **Feature Stability Test (FR-3.1)**: IC variance across sub-periods to detect unstable features
- ✅ **Lookahead Bias Prevention (Tech Design 4.4.1)**: Point-in-time validation, high-correlation removal
- ✅ **Purged Walk-Forward CV (FR-3.2)**: 3-year train, 6-month test, 21-day purge gap
- ✅ **XGBoost/LightGBM/Random Forest/Ridge (FR-3.2)**: Multi-model support with label encoding
- ✅ **Overfitting Detection (FR-3.2)**: IC < 0.03, IC std > 0.1, Sharpe diff > 0.5
- ✅ **Optuna Hyperparameter Optimization (FR-3.2)**: TPE sampler, 100 trials
- ✅ **Model Evaluation (FR-3.3)**: IC, IC_IR, AUC-ROC, SHAP explainability, partial dependence
- ✅ **Turnover-Adjusted Returns (FR-3.3)**: Cost-adjusted performance metrics
- ✅ **Signal Fusion (FR-3.4)**: ML + traditional blending with 50% ML cap, auto-degradation
- ✅ **Lifecycle Management (FR-3.5)**: Monthly retraining, drift detection (KS test), auto-retirement

### Asset Universe (Phase 2 - Expanded)
- **Core 4 Assets**: GLD, SPY, QQQ, BTC-USD
- **Extended 11 Assets**: SLV, XLK, XLF, XLE, XLV, TLT, TIP, EFA, EEM, DBC, VNQ
- **Total**: 15 assets enabling statistically meaningful cross-sectional ranking

---

## 📊 System Architecture

```
shark-quant-trader/
├── src/
│   ├── data/          # Multi-source data provider with caching
│   │   └── provider.py    # Polygon → Binance (+ Funding Rates) → yfinance fallback
│   ├── factors/       # Technical indicator calculation
│   │   ├── calculator.py  # Technical factors (Phase 1)
│   │   ├── momentum.py    # Cross-sectional momentum (Phase 2)
│   │   ├── carry.py       # Crypto carry strategy (Phase 2)
│   │   └── rotation.py    # Asset rotation model (Phase 2)
│   ├── ml/            # Machine Learning module (Phase 3)
│   │   ├── features.py    # Feature engineering (FR-3.1)
│   │   ├── cpcv.py        # Combinatorial Purged CV (FR-3.2)
│   │   ├── trainer.py     # XGBoost/LightGBM training (FR-3.2)
│   │   ├── evaluator.py   # IC, SHAP evaluation (FR-3.3)
│   │   ├── fusion.py      # Signal fusion (FR-3.4)
│   │   └── lifecycle.py   # Model lifecycle management (FR-3.5)
│   ├── signals/       # Signal generation with regime filtering
│   ├── risk/          # 4-level risk manager + correlation monitor
│   ├── portfolio/     # Position sizing and optimization
│   │   ├── manager.py     # Position management (Phase 1)
│   │   └── optimizer.py   # riskfolio-lib integration (Phase 2)
│   ├── execution/     # Order management and compliance
│   ├── state/         # State persistence (SQLite)
│   ├── alerts/        # Multi-channel notifications
│   ├── backtest/      # Backtesting engine
│   ├── stress/        # Stress testing (crisis scenarios + Monte Carlo)
│   ├── models/        # Domain models and dataclasses
│   └── utils/         # Logging and utilities
│       └── logger.py      # Loguru-based structured logging
├── config/
│   └── strategy.yaml  # Strategy configuration (risk levels, assets, etc.)
├── tests/             # Unit and integration tests
├── data/              # Data cache and state database
├── demo_phase1.py     # Phase 1 demo script
├── demo_phase2.py     # Phase 2 demo script
├── demo_phase3.py     # Phase 3 demo script (NEW)
├── verify_carry.py    # Carry strategy verification
├── .env.example       # Environment configuration template
├── .gitignore         # Git ignore rules
├── pyproject.toml     # Poetry dependencies & project config
├── code_review_log.md # Code review tracking
└── main.py            # Main execution script
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
cd /Users/fengguo/my_projs/shark-quant-trader

# Install dependencies with Poetry
poetry install
```

**Requirements**: Python 3.12+

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
vim .env
```

Required API Keys:
- `POLYGON_API_KEY`: Polygon.io API key (primary data source)
- Binance: Uses public Futures API - no key required
- Alert channels (optional): SMTP, Slack, Telegram, Discord webhooks

### 3. Run Modes

#### Live Trading
```bash
poetry run python main.py --mode live --interval 86400
```

#### Backtesting
```bash
poetry run python main.py --mode backtest \
  --start-date 2020-01-01 \
  --end-date 2023-12-31
```

#### Stress Testing
```bash
poetry run python main.py --mode stress
```

---

## 📈 Risk Management Framework

### 4-Level Hierarchical Control

| Level | Drawdown Trigger | Actions |
|-------|-----------------|---------|
| **0** | 0% | Normal operation |
| **1** | 5% | Alert + Increase confidence threshold + Block BTC new positions |
| **2** | 8% | Reduce positions 25% + Close BTC + Sell-only mode |
| **3** | 12% | Reduce positions 50% + Safe haven only (GLD, TLT) + Manual review |
| **4** | 15% | Emergency liquidation + Manual confirmation required |

### Single Asset Stop Loss
- **12% Drawdown**: Reduce position to 50%
- **18% Drawdown**: Full exit

### Correlation Monitoring
- **Pair > 0.7**: Warning + Reduce combined weight cap
- **Portfolio avg > 0.5**: Level 1 alert
- **All assets > 0.8**: Auto escalate to Level 2

---

## 🧪 Testing

```bash
# Run all tests
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_risk.py -v
```

**Current Coverage**: Factor calculation and risk management core modules

---

## 📊 Backtesting Results Format

```
Period: 2020-01-01 to 2023-12-31
Total Return: 45.23%
Annualized Return: 12.34%
Sharpe Ratio: 1.45
Max Drawdown: -18.56%
Calmar Ratio: 0.66
Win Rate: 58.3%
Number of Trades: 127
```

---

## 🔧 Configuration

### Strategy Configuration (`config/strategy.yaml`)

```yaml
core_assets:
  GLD:
    max_weight: 0.50
    momentum_lookback: 90
    vol_target: 0.12
    asset_stop_loss: 0.12
  SPY:
    max_weight: 0.40
    momentum_lookback: 60
    vol_target: 0.15
    asset_stop_loss: 0.12
  # ... more assets

risk:
  levels:
    level_1:
      drawdown_trigger: 0.05
      actions: ["alert", "increase_confidence_threshold", "block_btc_new"]
    # ... more levels

portfolio:
  initial_capital: 100000
  target_volatility: 0.15
  max_leverage: 1.5
  min_cash_buffer: 0.05
```

---

## 🔐 Security & Compliance

- ✅ Pre-trade compliance checks (concentration, leverage, cash buffer)
- ✅ Post-trade validation
- ✅ Daily trading limits (max 5 trades, 30% turnover)
- ✅ Blacklist support for restricted symbols
- ✅ Position concentration limits (50% max for GLD)

---

## 📡 Alerting Channels

Supports multiple notification channels via Apprise:
- Email (SMTP)
- Slack
- Telegram
- Discord

Alerts sent for:
- Risk level changes
- Stop loss triggers
- Correlation breaches
- Data quality issues
- Order execution failures
- Compliance violations
- Daily performance summaries

---

## 🗺️ Roadmap

### Phase 2 (Complete - Q1 2026)
- ✅ Expand to 15 assets
- ✅ Cross-sectional momentum ranking (FR-2.1)
- ✅ Crypto carry arbitrage strategy (FR-2.2)
- ✅ Tactical asset rotation with riskfolio-lib (FR-2.3)
- ✅ Funding rate API integration
- ✅ SMA_200 trend filter with Defense Mode

### Phase 3 (Complete - Q2 2026)
- ✅ Machine learning signal augmentation (XGBoost/LightGBM)
- ✅ Purged walk-forward validation (CPCV)
- ✅ Feature engineering with macro factors (FR-3.1)
- ✅ Model lifecycle management (FR-3.5)
- ✅ Concept drift monitoring (KS test)
- ✅ Signal fusion with auto-degradation (FR-3.4)

### Phase 4 (Q4 2026)
- [ ] NLP sentiment analysis (FinBERT)
- [ ] CFTC COT Report integration
- [ ] Sentiment factor integration into ML models

---

## 📚 Technical Documentation

- **PRD**: `PRD_Intelligent_Trading_System_v2.md`
- **Tech Design**: `Tech_Design_Document.md` (v1.1)
- **Code Review Log**: `code_review_log.md` - Tracks all code reviews and changes
- **Architecture**: Modular design with clear separation of concerns
- **Testing**: Pytest-based unit and integration tests

---

## 🤝 Contributing

This is a proprietary trading system. For questions or support:
- Review technical design document
- Check logs in `logs/` directory
- Examine state database in `data/state.db`

---

## ⚠️ Disclaimer

**This is a trading system for educational and research purposes. Use at your own risk.**

- Past performance does not guarantee future results
- Trading involves substantial risk of loss
- Always conduct thorough backtesting and paper trading before live deployment
- Ensure compliance with local regulations
- Start with small capital allocation

---

## 📝 License

Proprietary - All rights reserved

---

## 🏆 System Metrics (Phase 3)

- **Total Lines of Code**: ~8,500+
- **Core Modules**: 23 (includes Phase 3 ML modules)
- **Test Coverage**: Risk, Factor & ML modules
- **Dependencies**: 20+ (pandas, numpy, xgboost, lightgbm, shap, optuna, scikit-learn, yfinance, pandas-ta, backtrader, polygon-api-client, requests, riskfolio-lib, etc.)
- **Database**: SQLite for state persistence and data caching
- **Logging**: Structured logging with loguru
- **Last Review**: February 10, 2026 - Phase 3 compliance review (Review #7), 12 issues fixed

### Phase 3 Demo Results (Feb 10, 2026)

| Component | Status | Details |
|-----------|--------|--------|
| Feature Engineering | PASS | 7,918 samples x 44 features, 20 selected by IC |
| Model Training | PASS | XGBoost + PurgedWalkForwardCV (756 train, 126 test, 21 purge) |
| Overfitting Detection | PASS | Train-Val IC gap 0.91 > 0.5 correctly flagged |
| Model Evaluation | PASS | IC=0.608, AUC=0.837, Rolling IC=0.337 |
| SHAP Explainability | PASS | Top feature: rsi_14 |
| Signal Fusion | PASS | ML weight 50%, disagreement 0.48 |
| Lifecycle Management | PASS | Retrain needed (initial), No retirement |

### Phase 2 Demo Results (Feb 9, 2026)

| Component | Status | Details |
|-----------|--------|--------|
| Data Provider | PASS | Polygon + Binance (Prices & Funding Rates) + yfinance fallback |
| Cross-Sectional Momentum | PASS | Top 30%: SLV (+141.77%), GLD (+54.94%), EEM (+35.21%), EFA (+26.80%), XLK (+25.14%) |
| Crypto Carry Strategy | PASS | BTC Funding: -0.0049% (Annualized: -5.33%), Signal: HOLD |
| Asset Rotation | PASS | 5 assets selected, Risk Parity weights: EFA (25.91%), EEM (23.19%), GLD (17.80%), XLK (15.56%), SLV (8.89%) |
| riskfolio-lib Integration | PASS | Inverse volatility fallback successful |

### Phase 1 Demo Results (Feb 8, 2026)

| Component | Status | Details |
|-----------|--------|--------|
| Data Provider | PASS | Polygon (GLD, SPY, QQQ), Binance (BTC-USD) |
| Factor Calculator | PASS | 13 factors per asset |
| Signal Generator | PASS | VIX-based signal generation |
| Risk Manager | PASS | 4-level hierarchical control |
| Alert Manager | PASS | Telegram alerts working |
| State Manager | PASS | SQLite persistence |
| Backtest Engine | PASS | 1.01% return, 0.40 Sharpe |

---

**Built with ❤️ for quantitative trading excellence**