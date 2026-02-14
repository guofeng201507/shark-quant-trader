# Shark Quant Trader - Investor Pitch / 投资人推介

---

## English Version

### Project Overview

**Shark Quant Trader** is an intelligent quantitative trading system that combines traditional factor investing with machine learning enhancement and NLP sentiment analysis. The system manages a multi-asset portfolio covering precious metals (GLD), US equity ETFs (SPY, QQQ), and cryptocurrencies (BTC).

### Investment Thesis

1. **Risk-Adjusted Returns**: Target Sharpe Ratio > 1.0 through multi-factor diversification
2. **Downside Protection**: 4-level hierarchical risk control with max drawdown < 15%
3. **Adaptive Strategy**: ML models continuously learn from market data
4. **Alternative Alpha**: NLP sentiment provides non-traditional edge

---

### Technology Architecture & Phase Roadmap

#### Phase 1: Foundation (Complete)
**Core Strategy**: Time Series Momentum + Risk Parity

| Component | Implementation |
|-----------|---------------|
| Data Source | Polygon.io → Binance → yfinance (automatic fallback) |
| Factors | Momentum (60/120d), Volatility (20/60d), RSI, ATR |
| Signals | VIX-based regime filtering (Normal/Elevated/High/Extreme) |
| Risk Control | 4-level drawdown triggers: 5% → 8% → 12% → 15% |
| Portfolio | Risk parity with 1.5x max leverage |

**Rationale**: Establish baseline with proven factor strategies before adding complexity.

---

#### Phase 2: Enhanced Strategies (Complete)
**Core Strategy**: Cross-Sectional Momentum + Crypto Carry + Asset Rotation

| Strategy | Description |
|----------|-------------|
| Cross-Sectional Momentum | Rank 15 assets by 12-1 month returns, long Top 30% |
| Crypto Carry | BTC funding rate arbitrage (annualized 5-15%) |
| Asset Rotation | Momentum + Risk Parity optimization |
| Defense Mode | Switch to safe havens (GLD+TLT) when >50% assets below SMA200 |

**Rationale**: Expand alpha sources while maintaining risk discipline.

---

#### Phase 3: Machine Learning Enhancement (Complete)
**Core Strategy**: ML Signal Augmentation

| Component | Implementation |
|-----------|---------------|
| Feature Engineering | 44 features: price, macro, cross-sectional |
| Models | XGBoost, LightGBM, Random Forest, Ridge |
| Validation | Purged Walk-Forward CV (3yr train, 6mo test) |
| Overfitting Detection | IC < 0.03, IC std > 0.1, Sharpe diff > 0.5 |
| Hyperopt | Optuna TPE, 100 trials |
| Signal Fusion | ML weight capped at 50%, auto-degradation |
| Lifecycle | Monthly retraining, drift detection (KS test) |

**Rationale**: ML enhances but never replaces traditional signals.

---

#### Phase 4: NLP Sentiment Analysis (Complete)
**Core Strategy**: Alternative Data Alpha

| Component | Implementation |
|-----------|---------------|
| News Sentiment | FinBERT for financial text analysis |
| Data Sources | GDELT (free), RSS feeds, NewsAPI |
| COT Sentiment | CFTC Commitment of Traders (contrarian) |
| Integration | Sentiment as ML input, SHAP-validated |

**Rationale**: Sentiment provides leading indicator for short-term moves.

---

### Recent Performance (Last 30 Days)

| Asset | Return | Status |
|-------|--------|--------|
| GLD (Gold) | **+9.28%** | Strong momentum |
| SPY (S&P 500) | -1.52% | Slight pullback |
| QQQ (Nasdaq) | -3.19% | Tech weakness |
| BTC-USD | -27.90% | Crypto drawdown |

**Weighted Portfolio**: -2.03%
**Benchmark (60/40)**: +4.96%

> Note: Recent underperformance due to heavy BTC weighting in current allocation and crypto market correction. The system's risk management correctly reduced equity exposure during this period.

---

### Why This Project?

| Advantage | Description |
|-----------|-------------|
| ✅ Production-Ready | Full backtest + stress test + paper trading workflow |
| ✅ Modular Design | Easy to add new strategies or assets |
| ✅ Risk-First | 4-level controls prevent catastrophic losses |
| ✅ Transparent | Every signal has explainable reasoning |
| ✅ Cost-Efficient | Mostly free data sources (yfinance, Binance, CFTC) |

---

### Ask & Use of Funds

- **Current Stage**: Seed / Angel
- **Funding Ask**: $50,000 - $100,000
- **Use of Funds**:
  - Premium data subscriptions (Polygon Pro)
  - Cloud infrastructure (AWS with GPU for NLP)
  - Legal/compliance setup
  - Initial capital for paper trading

---

## 中文版本

### 项目概述

**Shark Quant Trader** 智能量化交易系统，结合传统因子投资、机器学习增强和NLP情绪分析。系统管理多资产组合，覆盖贵金属(GLD)、美股ETF(SPY, QQQ)和加密货币(BTC)。

### 投资理念

1. **风险调整收益**: 通过多因子分散化，目标夏普比率 > 1.0
2. **下行保护**: 4级分层风控，最大回撤 < 15%
3. **自适应策略**: 机器学习模型持续从市场数据中学习
4. **另类阿尔法**: NLP情绪分析提供非传统优势

---

### 技术架构与阶段路线图

#### 阶段一：基础框架（已完成）
**核心策略**: 时序动量 + 风险平价

| 组件 | 实现方式 |
|------|---------|
| 数据源 | Polygon.io → Binance → yfinance（自动降级）|
| 因子 | 动量(60/120日)、波动率(20/60日)、RSI、ATR |
| 信号 | VIX市场环境过滤（正常/ Elevated/高波动/极端）|
| 风控 | 4级回撤触发：5% → 8% → 12% → 15% |
| 组合 | 风险平价，最高1.5倍杠杆 |

**逻辑**: 用经过验证的因子策略建立基准后再增加复杂度。

---

#### 阶段二：增强策略（已完成）
**核心策略**: 截面动量 + 加密货币套利 + 资产轮动

| 策略 | 描述 |
|------|------|
| 截面动量 | 15资产按12-1月收益排名，做多前30% |
| 加密货币套利 | BTC资金费率套利（年化5-15%）|
| 资产轮动 | 动量 + 风险平价优化 |
| 防御模式 | 当>50%资产低于SMA200时切换至避险资产(GLD+TLT) |

**逻辑**: 在保持风险纪律的同时扩展阿尔法来源。

---

#### 阶段三：机器学习增强（已完成）
**核心策略**: 机器学习信号增强

| 组件 | 实现方式 |
|------|---------|
| 特征工程 | 44个特征：价格、宏观、截面 |
| 模型 | XGBoost、LightGBM、Random Forest、Ridge |
| 验证 | 清除型Walk-Forward交叉验证（3年训练、6个月测试）|
| 过拟合检测 | IC < 0.03、IC标准差 > 0.1、夏普差异 > 0.5 |
| 超参优化 | Optuna TPE，100次试验 |
| 信号融合 | ML权重上限50%，自动降级 |
| 生命周期 | 每月重训练、漂移检测（KS检验）|

**逻辑**: 机器学习增强但绝不取代传统信号。

---

#### 阶段四：NLP情绪分析（已完成）
**核心策略**: 另类数据阿尔法

| 组件 | 实现方式 |
|------|---------|
| 新闻情绪 | FinBERT金融文本分析 |
| 数据源 | GDELT（免费）、RSS订阅、NewsAPI |
| COT情绪 | CFTC交易商持仓报告（逆向指标）|
| 集成 | 情绪作为ML输入，SHAP验证 |

**逻辑**: 情绪提供短期走势的领先指标。

---

### 近30天表现

| 资产 | 收益 | 状态 |
|------|------|------|
| GLD（黄金）| **+9.28%** | 强势动量 |
| SPY（标普500）| -1.52% | 小幅回调 |
| QQQ（纳斯达克）| -3.19% | 科技股疲软 |
| BTC-USD | -27.90% | 加密货币回调 |

**加权组合**: -2.03%
**基准（60/40）**: +4.96%

> 注：近期表现不佳是因为当前配置中BTC权重较高，且加密货币市场回调。系统的风控模块在此期间正确降低了股票敞口。

---

### 项目优势

| 优势 | 描述 |
|------|------|
| ✅ 生产就绪 | 完整回测 + 压力测试 + 纸盘交易工作流 |
| ✅ 模块化设计 | 易于添加新策略或新资产 |
| ✅ 风险优先 | 4级风控防止灾难性损失 |
| ✅ 透明可解释 | 每个信号都有可解释的原因 |
| ✅ 成本效益 | 主要是免费数据源（yfinance、Binance、CFTC）|

---

### 融资计划

- **当前阶段**: 种子轮/天使轮
- **融资需求**: $50,000 - $100,000
- **资金用途**:
  - 高级数据订阅（Polygon Pro）
  - 云基础设施（AWS GPU用于NLP）
  - 法律/合规设置
  - 纸盘交易初始资金

---

*Generated: February 14, 2026*
*System: Shark Quant Trader v1.0*
*Code: ~10,000 lines | 27 modules | Phase 4 Complete*
