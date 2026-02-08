# Shark Quant Trader

**Intelligent Trading Decision System - Phase 1 MVP**

A production-ready quantitative trading system with hierarchical risk management, multi-asset support, and VIX-based market regime filtering.

---

## 🎯 Features

### Phase 1 (Current)
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

### Asset Universe (Phase 1)
- **Core 4 Assets**: GLD, SPY, QQQ, BTC-USD
- **Expandable to 15 in Phase 2**: SLV, XLK, XLF, XLE, XLV, TLT, TIP, EFA, EEM, DBC, VNQ

---

## 📊 System Architecture

```
shark-quant-trader/
├── src/
│   ├── data/          # Multi-source data provider with caching
│   │   └── provider.py    # Polygon → Binance → yfinance fallback
│   ├── factors/       # Technical indicator calculation
│   ├── signals/       # Signal generation with regime filtering
│   ├── risk/          # 4-level risk manager + correlation monitor
│   ├── portfolio/     # Position sizing and optimization
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

### Phase 2 (Q2 2026)
- [ ] Expand to 15 assets
- [ ] Cross-sectional momentum ranking
- [ ] Advanced portfolio optimization (riskfolio-lib)
- [ ] Factor decay monitoring

### Phase 3 (Q3 2026)
- [ ] Machine learning signal augmentation
- [ ] Regime detection (HMM)
- [ ] Sentiment integration

### Phase 4 (Q4 2026)
- [ ] Options strategies
- [ ] Intraday trading
- [ ] Multi-strategy ensemble

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

## 🏆 System Metrics (Phase 1)

- **Total Lines of Code**: ~4,500+
- **Core Modules**: 14
- **Test Coverage**: Risk & Factor modules
- **Dependencies**: 14+ (pandas, numpy, yfinance, pandas-ta, backtrader, polygon-api-client, requests, etc.)
- **Database**: SQLite for state persistence and data caching
- **Logging**: Structured logging with loguru
- **Last Review**: February 8, 2026 - Live demo validated all components

### Live Demo Results (Feb 8, 2026)

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