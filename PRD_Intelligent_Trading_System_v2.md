# 智能交易决策系统 - 产品需求文档 (PRD)

> **Version**: 2.0  
> **Original Author**: AI Chief Scientist Assistant  
> **Revised by**: Technical Review Board  
> **Date**: 2026-02-08  
> **Status**: Revised Draft  
> **Changes from v1.0**: Expanded asset universe, redesigned risk management, realistic timelines, replaced Phase 4 HFT with NLP sentiment, added regulatory/compliance section, added non-functional requirements, added stress testing framework

---

## Revision Summary

Key changes from PRD v1.0 based on technical feasibility assessment:

1. **Expanded asset universe** from 4 to 15 instruments for statistically meaningful cross-sectional signals
2. **Redesigned risk management** — replaced blunt 10% stop-loss with graduated de-risking, added correlation monitoring and re-entry logic
3. **Doubled Phase 3 timeline** (6 weeks → 10–12 weeks) with mandatory anti-overfitting safeguards
4. **Replaced Phase 4 HFT/LOB** (infeasible with Python/cron architecture) with achievable NLP sentiment pipeline
5. **Added mandatory paper trading gate** — minimum 3 months before any live capital deployment
6. **Added regulatory, compliance, and tax section**
7. **Added non-functional requirements** — disaster recovery, state persistence, alerting, data reconciliation
8. **Committed to Backtrader** as sole backtesting framework (removed Zipline ambiguity)
9. **Added tiered data strategy** — Polygon/Tiingo as primary, yfinance as fallback, Binance as canonical BTC source
10. **Added stress testing framework** — mandatory backtests across 2008, 2020, 2022 crisis periods

---

## 1. 项目概述

### 1.1 项目背景

构建一个面向多资产类别的智能交易决策系统，覆盖贵金属、美股指数、行业ETF、国际ETF及加密货币。系统采用分阶段迭代开发，从基础因子策略逐步演进至机器学习增强与NLP情绪分析的复杂策略。

### 1.2 设计原则

- **工程优先**: 所有策略必须经过长期回测验证（≥5年），考虑交易成本，并通过多场景压力测试
- **可解释性**: 每个交易决策必须有明确的逻辑和可追溯的原因
- **风险控制**: 内置多层分级风控机制，包括渐进式减仓、仓位限制、波动率控制、相关性监控
- **可扩展性**: 模块化设计，支持新资产、新策略的无缝接入
- **防过拟合**: ML策略必须通过Purged Walk-Forward验证，满足最低纸盘交易期
- **合规意识**: 遵守相关证券法规和税务要求

### 1.3 目标资产

#### 1.3.1 核心资产 (Phase 1)

| 资产 | 代码 | 特性 | 目标波动率 |
|------|------|------|-----------|
| 黄金ETF | GLD | 避险资产，低波动 | 10-12% |
| 标普500ETF | SPY | 核心权益资产 | 15% |
| 纳斯达克100ETF | QQQ | 成长型权益资产 | 18% |
| 比特币 | BTC-USD | 高风险高收益 | 20-25% |

#### 1.3.2 扩展资产池 (Phase 2 截面动量)

为实现统计上有意义的截面排名，扩展至15个资产:

| 类别 | 资产 | 代码 | 用途 |
|------|------|------|------|
| 贵金属 | 白银ETF | SLV | 与GLD形成贵金属截面 |
| 美股行业 | 科技精选 | XLK | 行业轮动信号 |
| 美股行业 | 金融精选 | XLF | 行业轮动信号 |
| 美股行业 | 能源精选 | XLE | 大宗商品周期暴露 |
| 美股行业 | 医疗保健 | XLV | 防御性配置 |
| 债券 | 20年国债 | TLT | 利率风险/避险 |
| 债券 | 通胀保值债 | TIP | 通胀对冲 |
| 国际 | 发达市场 | EFA | 地域分散 |
| 国际 | 新兴市场 | EEM | 地域分散/高波动 |
| 大宗商品 | 商品综合 | DBC | 大宗商品暴露 |
| 房地产 | REITs | VNQ | 另类资产 |

**资产选择依据**: 扩展至15个资产后，Top 30%做多 = 4-5个资产，Bottom 30%做空/回避 = 4-5个资产，具备统计学意义的截面排名。所有扩展资产均可通过yfinance/Polygon获取免费或低成本数据。

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                       智能交易决策系统 v2.0                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  数据层       │  │  策略层       │  │  执行层       │              │
│  │  Data Layer  │  │ Strategy     │  │ Execution    │              │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤              │
│  │ • 价格数据    │  │ • 因子计算    │  │ • 信号生成    │              │
│  │ • 宏观数据    │  │ • 组合优化    │  │ • 订单管理    │              │
│  │ • 情绪数据    │  │ • 风险管理    │  │ • 交易执行    │              │
│  │ • 数据校验    │  │ • ML预测     │  │ • 状态持久化   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  监控与告警    │  │  回测引擎     │  │  报告系统     │              │
│  │  Monitor &   │  │ Backtester & │  │  Reporter    │              │
│  │  Alerting    │  │ Stress Test  │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                                │
│  │  合规引擎     │  │  灾难恢复     │                                │
│  │  Compliance  │  │  Recovery    │                                │
│  └──────────────┘  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| 数据获取 (主) | `polygon-api-client`, `tiingo` | 稳定可靠的付费数据源，yfinance作为备用 |
| 数据获取 (备) | `yfinance` | 免费，用于开发/回测 |
| 数据获取 (BTC) | `python-binance` | Binance为BTC规范数据源，解决yfinance BTC数据缺失问题 |
| 数据处理 | `pandas`, `numpy` | 行业标准 |
| 技术分析 | `pandas-ta` | 成熟的技术指标库 (放弃ta-lib因编译依赖问题) |
| 回测框架 | `Backtrader` | 功能完善，社区活跃 (统一选择，不再同时支持Zipline) |
| 组合优化 | `riskfolio-lib` | 替代pyriskparity，更活跃维护，功能更全 |
| 机器学习 | `scikit-learn`, `XGBoost`, `LightGBM` | 高效、可解释 |
| NLP情绪分析 | `transformers` (FinBERT) | Phase 4 情绪因子 |
| 可视化 | `matplotlib`, `plotly` | 交互式图表 |
| 配置管理 | `pydantic`, `yaml` | 类型安全、易维护 |
| 状态持久化 | `sqlite3`, `pickle` | 组合状态、交易记录持久化 |
| 日志监控 | `loguru` | 现代化日志 |
| 告警 | `apprise` | 多渠道通知 (Slack, Email, Telegram) |

---

## 3. 阶段规划

### Phase 1: 基础因子策略 (MVP)

**目标**: 实现可运行的基础交易系统，产生明确的买卖信号

**时间预估**: 3-4周

#### 3.1.1 核心策略

| 策略 | 论文参考 | 实现库 | 复杂度 |
|------|---------|--------|--------|
| 时间序列动量 | "Time Series Momentum" (Moskowitz & Grinblatt, 1999) | 自实现 | 低 |
| 波动率目标 | "Volatility Targeting" (Perchet et al., 2016) | 自实现 | 低 |
| 风险平价组合 | "Levering Up to Risk Parity" (Asness, 2012) | `riskfolio-lib` | 中 |

#### 3.1.2 论文详解

**Paper 1: Time Series Momentum**
- **Title**: "Time Series Momentum"
- **Authors**: Tobias J. Moskowitz, Mark Grinblatt
- **Journal**: Journal of Financial Economics, 1999
- **Key Insight**: 资产自身的过去收益可以预测未来收益，动量效应存在于股票、债券、商品、外汇
- **Implementation**: 
  - 回看周期: 60-120天
  - 信号生成: `sign(cumulative_return)`
  - 仓位调整: 基于波动率缩放

**Paper 2: Volatility Targeting**
- **Title**: "Volatility Targeting and Portfolio Construction"
- **Authors**: Romain Perchet, et al.
- **Key Insight**: 根据资产波动率动态调整仓位，保持组合波动率恒定
- **Implementation**:
  - 目标波动率: 10-15%
  - 仓位 = 目标波动率 / 实际波动率
  - 限制最大杠杆: 2x (含组合级别杠杆上限)

**Paper 3: Risk Parity**
- **Title**: "Levering Up to Risk Parity"
- **Authors**: Cliff Asness
- **Key Insight**: 每个资产对组合风险的贡献相等，而非资金相等
- **Implementation**:
  - 权重 ∝ 1/波动率
  - 结合适度杠杆可超越60/40组合

#### 3.1.3 GitHub参考实现

| 项目 | Stars | 说明 | 参考点 |
|------|-------|------|--------|
| [riskfolio-lib](https://github.com/dcajasn/Riskfolio-Lib) | 2.5k+ | 组合优化库 | 风险平价、均值-方差优化 |
| [momentum-strategy](https://github.com/topics/momentum-strategy) | - | 动量策略集合 | 信号生成 |
| [bt](https://github.com/pmorissette/bt) | 1.5k+ | Python回测框架 | 回测结构参考 |

#### 3.1.4 功能需求

**FR-1.1 数据获取模块**
```
输入: 资产代码列表, 时间范围
输出: OHLCV DataFrame

功能:
- 主数据源: Polygon.io (美股/ETF) + Binance API (BTC)
- 备用数据源: yfinance (自动降级)
- 自动处理缺失值、复权
- 缓存机制避免重复下载 (SQLite缓存层)
- 异常重试机制 (指数退避, 最大3次)
- 数据完整性校验 (检测缺失日期、异常价格跳变)

数据质量校验:
- 价格跳变检测: 单日涨跌幅 > 50% 触发告警
- 缺失值比例: > 5% 拒绝该数据段
- 数据源交叉验证: 多源价格偏差 > 1% 触发告警
```

**FR-1.2 因子计算模块**
```
输入: 价格DataFrame
输出: 因子DataFrame (动量、波动率、均线等)

因子列表:
- Momentum_60: 60日累计收益
- Momentum_120: 120日累计收益
- Volatility_20: 20日年化波动率 (短期)
- Volatility_60: 60日年化波动率 (中期)
- SMA_20: 20日简单移动平均
- SMA_50: 50日简单移动平均
- SMA_200: 200日简单移动平均 (长期趋势)
- RSI_14: 14日相对强弱指标
- ATR_14: 14日真实波幅 (用于止损计算)
```

**FR-1.3 信号生成模块**
```
输入: 因子DataFrame, 当前持仓, 市场环境状态
输出: 交易信号 (BUY/SELL/HOLD) + 置信度

信号逻辑 (含市场环境过滤):
- STRONG_BUY: 动量 > 高阈值 且 价格 > SMA_50 且 价格 > SMA_200 且 VIX < 30
- BUY: 动量 > 低阈值 且 价格 > SMA_20
- SELL: 动量 < 负阈值 或 价格 < SMA_50
- STRONG_SELL: 动量 < 负高阈值 且 价格 < SMA_200
- HOLD: 其他情况

市场环境过滤器:
- 高波动环境 (VIX > 30): 降低所有信号置信度50%
- 极端波动环境 (VIX > 40): 仅允许减仓信号

输出格式:
{
  "symbol": "GLD",
  "signal": "BUY",
  "confidence": 0.75,
  "target_weight": 0.35,
  "reason": "动量8.56%, 价格>20日及50日均线, VIX=22正常",
  "regime": "NORMAL"
}
```

**FR-1.4 仓位管理模块**
```
输入: 信号列表, 当前组合价值, 风险预算
输出: 目标持仓

约束:
- 单一资产最大权重: GLD 50%, SPY 40%, QQQ 30%, BTC 15%
- 组合目标波动率: 15%
- 组合最大杠杆: 1.5x (含波动率目标产生的隐含杠杆)
- 最小交易金额: $100
- 最小调仓幅度: 权重变化 > 2% 才执行 (避免过度交易)
- 现金缓冲: 始终保留 ≥ 5% 现金

仓位缩放:
- weight = min(信号权重, 风险预算权重, 最大权重约束)
- 风险预算权重 = 目标波动率 / (资产波动率 × 相关性调整因子)
```

**FR-1.5 交易执行模块**
```
输入: 目标持仓, 当前持仓
输出: 交易指令

成本模型:
- 手续费: 0.1% (ETF), 0.1% (BTC现货)
- 滑点: 0.05% (流动性ETF), 0.15% (BTC)
- 最小交易单位: 1股 (ETF), 0.0001 (BTC)

输出格式:
{
  "symbol": "GLD",
  "action": "BUY",
  "shares": 149.0,
  "price": 268.45,
  "estimated_value": 40000.0,
  "commission": 40.0,
  "order_type": "LIMIT",
  "limit_offset": 0.05
}
```

**FR-1.6 风控模块 (重新设计)**
```
分级风控机制 (替代原v1.0硬止损):

Level 1 - 监控告警 (组合回撤 5-8%):
- 发送告警通知 (Slack/Email/Telegram)
- 降低新开仓置信度要求 (提高至 > 0.8)
- 禁止新增BTC仓位

Level 2 - 渐进减仓 (组合回撤 8-12%):
- 所有仓位按比例减仓25%
- 仅允许减仓和对冲操作
- BTC仓位清至0
- 记录减仓原因和市场状态

Level 3 - 大幅减仓 (组合回撤 12-15%):
- 所有仓位按比例减仓至50%
- 仅保留避险资产 (GLD, TLT)
- 触发人工复核流程

Level 4 - 紧急清仓 (组合回撤 > 15%):
- 清仓所有风险资产
- 仅保留现金和GLD (如GLD未触发单一资产止损)
- 需要人工确认才能恢复交易

单一资产止损:
- 单一资产回撤 > 12%: 减仓至50%
- 单一资产回撤 > 18%: 清仓该资产

恢复交易 (re-entry) 规则:
- 从Level 4恢复: 需连续5个交易日组合波动率 < 目标波动率
- 恢复时以25%仓位重新进入，每周递增25%
- 恢复期间最大杠杆降至1.0x

相关性监控:
- 每日计算滚动60日相关性矩阵
- 当任意两个核心资产相关性 > 0.7: 降低该对资产合计权重上限
- 当组合平均相关性 > 0.5: 触发Level 1告警
- 极端相关性事件 (所有资产同向 > 0.8): 自动执行Level 2

日内限制:
- 最大日交易次数: 5次
- 波动率上限: 组合年化波动不超过20%
- 单日最大换手率: 30% (防止过度交易)
```

**FR-1.7 回测模块**
```
输入: 历史数据, 策略配置
输出: 回测报告

回测指标:
- 累计收益 (Cumulative Return)
- 年化收益 (Annualized Return)
- 年化波动 (Annualized Volatility)
- Sharpe Ratio
- 最大回撤 (Max Drawdown)
- Calmar Ratio
- 胜率 (Win Rate)
- 盈亏比 (Profit/Loss Ratio)
- 换手率 (Turnover Rate)
- 交易成本拖累 (Cost Drag)

压力测试场景 (必须全部通过):
- 2008-2009 全球金融危机
- 2020-03 COVID暴跌
- 2022 加息周期 + 加密寒冬
- 2023-2024 AI泡沫行情
- 自定义: 所有资产同时下跌20%

压力测试通过标准:
- 任何单一压力场景最大回撤 < 25%
- 所有压力场景平均最大回撤 < 18%
- 无一场景触发Level 4紧急清仓
```

**FR-1.8 报告模块**
```
输出:
- 每日信号报告 (JSON)
- 交易记录 (CSV)
- 回测结果图表 (PNG/PDF)
- 绩效指标摘要
- 风控触发记录
- 压力测试报告

实时监控仪表板:
- 当前持仓与权重
- 组合P&L曲线
- 风控状态指示灯
- 最近交易记录
```

**FR-1.9 状态持久化模块 (新增)**
```
持久化内容:
- 当前组合状态 (持仓、成本基准、未实现P&L)
- 风控状态 (当前Level, 峰值NAV, 回撤水位)
- 交易历史 (完整审计轨迹)
- 信号历史 (含原因追溯)

存储: SQLite数据库 (portfolio.db)
备份: 每日自动备份，保留30天
恢复: 系统启动时自动从最近状态恢复

中断恢复逻辑:
- 系统崩溃时: 从最近持久化状态恢复
- 检查待执行订单状态 (通过券商API)
- 未执行订单自动取消
- 部分执行订单按实际成交更新状态
- 写入恢复日志
```

**FR-1.10 告警模块 (新增)**
```
告警渠道: Slack, Email, Telegram (通过apprise)

告警级别:
- INFO: 正常交易信号、每日摘要
- WARNING: 风控Level 1, 数据质量问题
- CRITICAL: 风控Level 2+, 系统异常, 券商API错误
- EMERGENCY: 风控Level 4, 系统崩溃

告警规则:
- 数据获取失败连续3次: CRITICAL
- 券商API连接断开: CRITICAL
- 未知异常: CRITICAL + 自动暂停交易
- 每日收盘后: INFO (当日交易摘要)
```

#### 3.1.5 接口定义

```python
# 核心接口

class DataProvider:
    def fetch(self, symbols: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]
    def validate(self, data: pd.DataFrame) -> DataQualityReport
    def get_source_status(self) -> Dict[str, str]  # 各数据源健康状态
    
class FactorCalculator:
    def calculate(self, prices: pd.DataFrame) -> pd.DataFrame
    
class SignalGenerator:
    def generate(self, factors: pd.DataFrame, positions: Dict, regime: MarketRegime) -> List[Signal]
    
class PositionManager:
    def calculate_target(self, signals: List[Signal], portfolio_value: float, 
                         risk_budget: RiskBudget) -> Dict[str, float]
    
class RiskManager:
    def check(self, portfolio: Portfolio) -> RiskAssessment
    def get_risk_level(self) -> int  # 当前风控级别 (0-4)
    def get_correlation_matrix(self) -> pd.DataFrame
    def check_reentry_conditions(self) -> bool
    
class Backtester:
    def run(self, strategy: Strategy, data: Dict[str, pd.DataFrame]) -> BacktestResult
    def stress_test(self, strategy: Strategy, scenarios: List[StressScenario]) -> StressTestReport
    
class StateManager:
    def save(self, portfolio: Portfolio) -> None
    def load(self) -> Portfolio
    def recover(self) -> RecoveryReport
    
class AlertManager:
    def send(self, level: AlertLevel, message: str, context: Dict) -> None
```

---

### Phase 2: 截面动量与Carry策略

**目标**: 利用扩展资产池实现跨资产轮动选择，引入Crypto Carry收益

**时间预估**: 4-5周

#### 3.2.1 核心策略

| 策略 | 论文参考 | 实现库 | 复杂度 |
|------|---------|--------|--------|
| 截面动量 (扩展资产池) | "Value and Momentum Everywhere" (Asness, 2013) | 自实现 | 中 |
| Crypto Carry策略 | "Carry Trade and Currency Crashes" (Brunnermeier, 2009) | 自实现 | 中 |
| 资产轮动模型 | "Tactical Asset Allocation" (Keller & Butler, 2015) | 自实现 | 中 |

#### 3.2.2 论文详解

**Paper 4: Cross-Sectional Momentum**
- **Title**: "Value and Momentum Everywhere"
- **Authors**: Clifford S. Asness, et al.
- **Journal**: Journal of Finance, 2013
- **Key Insight**: 在多个资产类别中，过去表现好的资产未来继续表现好
- **Implementation (修订)**:
  - 资产池: 15个ETF + BTC (见Section 1.3.2)
  - 每月对所有资产按过去12个月收益排序 (排除最近1个月，避免短期反转)
  - 做多Top 30% (4-5个资产)，回避Bottom 30% (4-5个资产)
  - 中间40%资产维持当前权重
  - **注意**: 仅做多侧，不实施做空 (ETF做空成本高且风险不对称)

**Paper 5: Carry Strategy (聚焦Crypto)**
- **Title**: "Carry Trade and Currency Crashes"
- **Authors**: Markus K. Brunnermeier, et al.
- **Key Insight**: 高收益率货币倾向于继续升值
- **Application to Crypto (修订 — 仅限加密货币)**:
  - 资金费率套利: 做多现货，做空永续合约
  - 数据来源: Binance, Bybit API (免费实时数据)
  - 历史年化收益: 5-15% (修正值，反映2023-2025资金费率压缩)
  - **已移除**: COMEX期限结构和VIX期货曲线 (CME数据成本过高，与项目预算不匹配)

**Paper 6: Tactical Asset Allocation (新增 — 替代原期限结构)**
- **Title**: "Momentum and Markowitz: A Golden Combination"  
- **Authors**: Wouter Keller, Jan Willem Keuning
- **Key Insight**: 结合动量信号和均值方差优化进行战术资产配置
- **Implementation**:
  - 使用动量排名筛选资产子集
  - 在筛选后的子集上运行风险平价优化
  - 月度再平衡

#### 3.2.3 GitHub参考实现

| 项目 | Stars | 说明 |
|------|-------|------|
| [ffn](https://github.com/pmorissette/ffn) | 1.2k+ | 金融函数库 |
| [pyfolio](https://github.com/quantopian/pyfolio) | 4.5k+ | 绩效分析 |
| [riskfolio-lib](https://github.com/dcajasn/Riskfolio-Lib) | 2.5k+ | 组合优化 |

#### 3.2.4 功能需求

**FR-2.1 截面动量模块 (修订)**
```
输入: 15个资产收益DataFrame
输出: 资产排名, 做多组合 (不做空)

逻辑:
- 计算各资产过去12个月收益 (排除最近1个月)
- 按收益排序，划分为3组: Top/Middle/Bottom
- Top 30%: 做多信号
- Bottom 30%: 回避信号 (权重→0，但不做空)
- Middle 40%: 维持现有权重

附加过滤器:
- 资产必须在SMA_200之上才能入选做多组
- 如果Top组中 > 50%资产在SMA_200之下，触发防御模式 (全部配置GLD+TLT)
```

**FR-2.2 Crypto Carry计算模块 (修订 — 仅限加密货币)**
```
输入: Binance/Bybit永续合约资金费率数据
输出: Carry收益率, 套利信号

数据来源:
- Binance API: /fapi/v1/fundingRate (免费)
- Bybit API: /v5/market/funding/history (免费)

策略逻辑:
- 8小时资金费率 > 0.01% (年化 > 10%): 做空永续+做多现货
- 8小时资金费率 < -0.01%: 平仓套利头寸
- 最大套利仓位: 组合的10%

风险控制:
- 单一交易所敞口 < 组合的8% (交易对手风险)
- 资金费率波动 > 3x 历史标准差: 暂停新开仓
- 基差偏离 > 2%: 触发告警
```

**FR-2.3 资产轮动模块 (新增 — 替代原期限结构)**
```
输入: 截面动量排名, 资产波动率, 相关性矩阵
输出: 月度目标配置

逻辑:
- Step 1: 截面动量筛选 → Top 30%资产
- Step 2: 在筛选后资产上运行风险平价优化
- Step 3: 应用仓位约束和风控规则
- Step 4: 生成月度再平衡指令

约束:
- 月度换手率 < 40%
- 交易成本预估 < 组合的0.2%/月
```

---

### Phase 3: 机器学习增强

**目标**: 引入ML模型预测短期收益，提升信号质量

**时间预估**: 10-12周 (修订: 从4-6周大幅扩展)

**前置条件**: Phase 1-2策略在回测和纸盘中验证有效

#### 3.3.1 核心策略

| 策略 | 论文参考 | 实现库 | 复杂度 |
|------|---------|--------|--------|
| 双重集成学习 | "Double Ensemble" (Microsoft, 2020) | `Qlib` | 高 |
| XGBoost因子 | "XGBoost: A Scalable Tree Boosting System" (Chen, 2016) | `XGBoost` | 中 |
| 特征重要性 | "SHAP Values for Finance" | `shap` | 中 |

#### 3.3.2 论文详解

**Paper 7: Double Ensemble Learning**
- **Title**: "Double Ensemble Learning for Quantitative Investing"
- **Authors**: Microsoft Research Asia
- **Key Insight**: 通过特征集成和模型集成解决ML在量化中的过拟合问题
- **Implementation**:
  - 特征集成: 动态选择特征子集
  - 模型集成: 多个基学习器投票
  - **注意**: 原论文报告的15-20%年化收益来自A股特定时期，不应作为本系统预期

**Paper 8: XGBoost for Stock Prediction**
- **Title**: "XGBoost: A Scalable Tree Boosting System"
- **Authors**: Tianqi Chen, Carlos Guestrin
- **Conference**: KDD 2016
- **Application**:
  - 特征: 技术指标、宏观因子
  - 目标: 未来5日收益方向
  - 优势: 可解释性强，训练速度快

#### 3.3.3 GitHub参考实现

| 项目 | Stars | 说明 |
|------|-------|------|
| [Qlib](https://github.com/microsoft/qlib) | 15k+ | 微软开源量化平台 |
| [mlfinlab](https://github.com/hudson-and-thames/mlfinlab) | 4k+ | 机器学习金融库 |

#### 3.3.4 功能需求

**FR-3.1 特征工程模块 (修订 — 扩展时间至4-5周)**
```
特征类别:
- 价格特征: 收益率、波动率、均线、RSI、MACD、ATR、布林带
- 宏观特征: 利率 (FRED)、VIX (CBOE)、DXY (FRED)、CPI (FRED)
- 交叉特征: 资产间相关性变化率、轮动指标、板块动量差
- (Phase 4加入) 情绪特征: NLP衍生因子

特征处理:
- 标准化/归一化 (仅使用训练集统计量，防止前视偏差)
- 缺失值填充 (前向填充，不使用未来数据)
- 特征选择 (PCA, 相关性过滤, 单变量IC筛选)

关键防过拟合措施:
- 所有特征计算严格使用point-in-time数据
- 宏观数据使用发布日期而非报告日期
- 特征版本控制 (Git追踪每个特征定义变更)
- 特征稳定性检验: IC在不同时间段方差 < 阈值
```

**FR-3.2 模型训练模块 (修订 — 强化验证框架)**
```
支持模型:
- XGBoost (主要)
- LightGBM
- Random Forest
- Ridge回归 (基准)

训练流程 (修订):
1. Purged Walk-Forward验证 (替代简单时间序列CV):
   - 训练窗口: 3年滚动
   - 验证窗口: 6个月
   - 清除间隔 (Purge gap): 21个交易日 (防止标签泄漏)
   - 禁区 (Embargo): 5个交易日
   
2. Combinatorial Purged Cross-Validation (CPCV):
   - 按López de Prado方法实现
   - 最少6折
   
3. 超参数优化:
   - Optuna (Tree-structured Parzen Estimator)
   - 搜索空间: 保守 (防止过拟合优化本身)
   - 最大试验次数: 100
   
4. 模型保存/加载:
   - 每个模型含元数据 (训练日期、数据范围、性能指标)
   - 模型版本控制

过拟合检测:
- 训练集 vs 验证集 Sharpe差异 > 0.5: 标记过拟合风险
- 验证集IC < 0.03: 模型信号太弱，不投入使用
- 10次随机种子训练结果方差 > 阈值: 模型不稳定
```

**FR-3.3 模型评估模块**
```
评估指标:
- 信息系数 (IC) 及 IC_IR (IC的信息比率)
- AUC-ROC
- 风险调整收益 (Sharpe of signal-based portfolio)
- 换手率调整后收益

可解释性:
- SHAP值分析 (每次预测)
- 特征重要性 (全局)
- 部分依赖图

模型监控 (新增):
- 滚动IC衰减曲线
- 特征重要性漂移检测
- 预测分布偏移检测 (KS检验)
```

**FR-3.4 预测融合模块**
```
融合策略:
- 加权平均 (按滚动窗口历史IC加权)
- 投票机制 (当模型间分歧 > 阈值时降低置信度)
- 动态权重: ML信号权重 = min(0.5, 滚动IC / 基准IC)

关键约束:
- ML信号永远不会完全覆盖传统信号
- ML权重上限50%，传统信号下限50%
- 当ML模型IC < 0.02 (连续20个交易日): 自动降权至0，仅使用传统信号

输出:
- 综合信号 = 传统信号权重 × 传统信号 + ML权重 × ML信号
```

**FR-3.5 模型生命周期管理 (新增)**
```
重训练计划:
- 定期重训练: 每月末使用最新3年数据
- 触发式重训练: 滚动IC < 0.02 连续10天
- 重训练后必须通过CPCV验证才能部署

模型退役:
- IC < 0 连续30天: 自动退役
- 新模型必须在验证集上显著优于旧模型 (IC差异 > 0.01, p < 0.05)

概念漂移监控:
- 每日计算特征分布KS统计量
- KS > 0.1: 告警
- KS > 0.2: 触发重训练
```

---

### Phase 4: NLP情绪分析 (修订: 原"高频/另类数据"重新设计)

**目标**: 通过NLP情绪分析生成另类alpha因子，作为ML模型的输入特征

**时间预估**: 6-8周

**重大变更**: 移除了原v1.0中的限价订单簿(LOB)预测和高频交易策略。LOB策略需要微秒级延迟、C++/Rust实现、交易所co-location和Level-2数据订阅($10K-50K+/月)，与本系统的Python/cron架构根本不兼容。

#### 3.4.1 核心策略

| 策略 | 论文参考 | 实现库 | 复杂度 |
|------|---------|--------|--------|
| 新闻情绪因子 | "Predicting Stock Returns with NLP" (Ke, 2019) | `transformers` (FinBERT) | 高 |
| 散户情绪因子 | "Retail Trading and Market Quality" (Barber, 2022) | 自实现 | 中 |
| 社交媒体情绪 | "Twitter Sentiment and Stock Returns" (Bollen, 2011) | `transformers` | 中 |

#### 3.4.2 论文详解

**Paper 9: NLP for Finance**
- **Title**: "Predicting Stock Returns with Natural Language Processing"
- **Authors**: Zheng Tracy Ke, et al.
- **Key Insight**: 财报电话会议文本和新闻标题可以预测短期收益漂移
- **Implementation**:
  - 使用FinBERT分析新闻标题和摘要
  - 输出情绪得分 (-1 to +1) 作为ML特征输入
  - 不独立产生交易信号，仅作为Phase 3 ML模型的输入特征

**Paper 10: Retail Sentiment**
- **Title**: "Retail Trading and Market Quality"
- **Authors**: Brad Barber, et al.
- **Key Insight**: 散户净买入/卖出可以作为反向指标
- **Implementation**:
  - 数据来源: CFTC COT Report (免费，周度发布)
  - 计算商业 vs 非商业持仓比
  - 极端值作为反向信号

#### 3.4.3 功能需求

**FR-4.1 新闻情绪模块**
```
输入: 新闻标题/摘要文本流
输出: 资产级情绪得分时间序列

数据来源:
- NewsAPI.org ($449/月 Business Plan, 或免费Developer Plan用于开发)
- GDELT Project (免费)
- RSS feeds (免费)

NLP管线:
- Step 1: 新闻采集 → 去重 → 资产关联 (关键词+NER)
- Step 2: FinBERT情绪分析 → 得分 (-1, 0, +1)
- Step 3: 按资产聚合 → 日度情绪得分
- Step 4: 情绪动量 = 情绪得分5日均值变化

计算需求:
- FinBERT推理: GPU推荐 (T4/A10), CPU可行但慢10x
- 每日处理: ~500-2000条新闻标题
- 延迟要求: 日度因子，T+1使用 (无实时要求)
```

**FR-4.2 散户情绪模块**
```
输入: CFTC COT报告数据
输出: 散户定位指标

数据来源:
- CFTC.gov (免费，每周五发布)
- Quandl/Nasdaq Data Link (可选付费，更方便的API)

指标:
- 非商业净多头占比
- 历史分位数 (3年滚动)
- 极端值信号: > 90%分位 → 看空信号, < 10%分位 → 看多信号
```

**FR-4.3 情绪因子集成**
```
输出: 情绪因子DataFrame (与Phase 3特征库合并)

集成方式:
- 情绪因子作为ML特征输入 (不独立交易)
- 特征名: Sentiment_News_5d, Sentiment_COT_Percentile, Sentiment_Momentum
- 通过Phase 3的SHAP分析验证情绪特征贡献度
- 如果情绪特征SHAP贡献 < 5%: 移除以降低模型复杂度
```

---

## 4. 数据需求

### 4.1 价格数据

| 数据类型 | 主数据源 | 备用数据源 | 频率 | 成本 |
|---------|---------|-----------|------|------|
| 美股/ETF OHLCV | Polygon.io | yfinance | 日度 | $29/月 (Basic) |
| BTC OHLCV | Binance API | yfinance | 日度/小时 | 免费 |
| BTC资金费率 | Binance API | Bybit API | 8小时 | 免费 |

### 4.2 宏观数据

| 数据 | 来源 | 频率 | 用途 | 成本 |
|------|------|------|------|------|
| 利率 (Fed Funds, 10Y) | FRED API | 日度 | 黄金定价、股票估值 | 免费 |
| VIX | CBOE/yfinance | 日度 | 市场情绪、风控输入 | 免费 |
| DXY | FRED | 日度 | 美元强弱 | 免费 |
| CPI | FRED | 月度 | 通胀预期 (point-in-time) | 免费 |

### 4.3 另类数据

| 数据 | 来源 | 频率 | 用途 | 成本 |
|------|------|------|------|------|
| BTC资金费率 | Binance/Bybit API | 8小时 | Crypto Carry | 免费 |
| 新闻标题 | NewsAPI / GDELT | 日度 | 情绪因子 (Phase 4) | 免费-$449/月 |
| 散户持仓 | CFTC COT Report | 周度 | 反向指标 (Phase 4) | 免费 |

### 4.4 数据预算摘要

| 阶段 | 月度数据成本 |
|------|-------------|
| Phase 1-2 (开发/回测) | $0 (yfinance + Binance免费) |
| Phase 1-2 (生产) | $29/月 (Polygon Basic) |
| Phase 3 | $29/月 |
| Phase 4 | $29-$478/月 (Polygon + NewsAPI) |

---

## 5. 性能指标

### 5.1 回测指标

| 指标 | 说明 | 目标值 | 最低接受值 |
|------|------|--------|-----------|
| 年化收益 | Annualized Return | > 10% | > 7% |
| 年化波动 | Annualized Volatility | < 15% | < 18% |
| Sharpe Ratio | 风险调整收益 | > 1.0 | > 0.7 |
| 最大回撤 | Max Drawdown | < 15% | < 20% |
| Calmar Ratio | 收益/回撤比 | > 0.7 | > 0.4 |
| 胜率 | Win Rate | > 52% | > 48% |
| 盈亏比 | Profit Factor | > 1.3 | > 1.1 |
| 月度换手率 | Monthly Turnover | < 30% | < 50% |
| 交易成本拖累 | Annual Cost Drag | < 1% | < 2% |

### 5.2 压力测试指标

| 场景 | 最大回撤上限 | 恢复天数上限 |
|------|-------------|-------------|
| 2008 金融危机 | < 25% | < 365天 |
| 2020 COVID暴跌 | < 18% | < 180天 |
| 2022 加息+加密寒冬 | < 20% | < 270天 |
| 全资产同跌20% | < 22% | N/A |

### 5.3 系统指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| 信号延迟 | 从数据到信号 | < 1分钟 |
| 回测速度 | 5年数据 | < 30秒 (扩展资产池后) |
| 内存占用 | 运行时 | < 4GB (扩展资产池后) |
| 状态恢复时间 | 从崩溃到恢复 | < 5分钟 |
| 数据刷新周期 | 日度数据更新 | 收盘后30分钟内完成 |

---

## 6. 部署架构

### 6.1 本地开发

```
开发环境:
- Python 3.10+
- Poetry 依赖管理
- Jupyter Notebook 探索
- Pytest 单元测试 (覆盖率 > 80%)
- pre-commit hooks (black, ruff, mypy)
```

### 6.2 生产部署

```
部署选项:
- 云服务器: AWS EC2 t3.medium (2 vCPU, 4GB RAM) — Phase 1-2
- 云服务器: AWS EC2 g4dn.xlarge (GPU) — Phase 4 NLP推理
- 容器化: Docker + Docker Compose
- 定时任务: cron (简单) 或 Airflow (复杂依赖)
- 监控: Prometheus + Grafana
- 数据库: SQLite (状态持久化) → PostgreSQL (如需扩展)
- 备份: 每日自动备份至S3
```

### 6.3 实盘集成

| 券商 | API | 支持资产 | 纸盘支持 |
|------|-----|---------|---------|
| Alpaca | REST/WebSocket | 美股/ETF | ✅ (免费) |
| Interactive Brokers | TWS API | 全球 | ✅ (免费) |
| Binance | REST/WebSocket | 加密货币 | ✅ (Testnet) |

### 6.4 部署流程

```
开发 → 回测验证 → 压力测试 → 纸盘交易 (≥3个月) → 小资金实盘 → 正式实盘

纸盘交易Gate:
- Sharpe > 0.5 (纸盘期间)
- 最大回撤 < 15%
- 无系统崩溃或数据中断事件
- 所有风控Level触发过至少一次 (确认风控正常工作)

小资金实盘Gate:
- 纸盘 ≥ 3个月
- 初始资金 ≤ 计划总资金的10%
- 运行4周无重大异常
- 实盘P&L与纸盘模拟偏差 < 2%
```

---

## 7. 合规与风控 (新增)

### 7.1 证券法规

```
Pattern Day Trader (PDT) 规则:
- 适用: 美股保证金账户 < $25,000
- 约束: 5个交易日内不超过3次日内交易
- 系统实现: 交易执行模块内置PDT计数器
- 如触发PDT限制: 自动推迟次日执行

做空限制:
- 本系统Phase 2截面动量仅做多侧 (无做空)
- 如未来扩展做空: 需确认券商借券可用性
```

### 7.2 加密货币合规

```
交易所交易对手风险:
- 单一交易所敞口 < 组合总值的8%
- 不使用交易所理财/借贷产品
- 定期 (每周) 将超出交易所需的资产转至冷钱包

KYC/AML:
- 使用已通过KYC验证的个人账户
- 保留完整交易记录用于合规审计
```

### 7.3 税务考虑

```
美股:
- Wash Sale规则: 30天内不可买回已止损资产并申报亏损
- 系统实现: 交易执行模块内置Wash Sale追踪器
- 如检测到潜在Wash Sale: 延迟买回或标记税务影响

加密货币:
- IRS将加密货币视为财产 (Property)
- 每笔交易均为应税事件
- 系统自动生成年度8949表格所需的交易记录

税损收割 (可选):
- 年末自动识别可收割亏损的持仓
- 以相关但非"substantially identical"资产替换 (避免Wash Sale)

输出:
- 年度交易汇总 (按短期/长期资本利得分类)
- 8949表格草稿
- Wash Sale标记记录
```

### 7.4 数据许可

```
yfinance: 非官方API，仅用于个人研究
Polygon.io: 商业许可，允许个人交易使用
Binance API: 需遵守Binance API使用条款
FRED: 公共数据，无限制
CFTC: 公共数据，无限制
NewsAPI: 按订阅计划，注意redistribution限制
```

---

## 8. 项目结构

```
trading-system/
├── config/                    # 配置文件
│   ├── strategy.yaml          # 策略参数
│   ├── assets.yaml            # 资产配置 (含扩展资产池)
│   ├── risk.yaml              # 风控参数 (分级风控)
│   └── compliance.yaml        # 合规参数 (PDT, Wash Sale)
├── data/                      # 数据目录
│   ├── raw/                   # 原始数据
│   ├── processed/             # 处理后数据
│   ├── cache/                 # 缓存
│   └── portfolio.db           # 组合状态数据库
├── src/                       # 源代码
│   ├── __init__.py
│   ├── data/                  # 数据模块
│   │   ├── __init__.py
│   │   ├── provider.py        # 数据获取 (多源+降级)
│   │   ├── processor.py       # 数据处理
│   │   └── validator.py       # 数据质量校验 (新增)
│   ├── factors/               # 因子模块
│   │   ├── __init__.py
│   │   ├── momentum.py        # 动量因子
│   │   ├── volatility.py      # 波动率因子
│   │   ├── carry.py           # Carry因子 (Crypto only)
│   │   └── rotation.py        # 轮动因子 (新增)
│   ├── signals/               # 信号模块
│   │   ├── __init__.py
│   │   ├── generator.py       # 信号生成 (含市场环境过滤)
│   │   └── ensemble.py        # 信号融合
│   ├── portfolio/             # 组合模块
│   │   ├── __init__.py
│   │   ├── optimizer.py       # 组合优化 (riskfolio-lib)
│   │   └── risk_parity.py     # 风险平价
│   ├── execution/             # 执行模块
│   │   ├── __init__.py
│   │   ├── order.py           # 订单管理
│   │   ├── broker.py          # 券商接口
│   │   └── compliance.py      # 合规检查 (新增: PDT, Wash Sale)
│   ├── risk/                  # 风控模块 (重新设计)
│   │   ├── __init__.py
│   │   ├── manager.py         # 分级风控管理
│   │   ├── rules.py           # 风控规则
│   │   ├── correlation.py     # 相关性监控 (新增)
│   │   └── reentry.py         # 恢复交易逻辑 (新增)
│   ├── backtest/              # 回测模块
│   │   ├── __init__.py
│   │   ├── engine.py          # 回测引擎
│   │   ├── metrics.py         # 绩效指标
│   │   └── stress.py          # 压力测试 (新增)
│   ├── ml/                    # 机器学习模块 (Phase 3)
│   │   ├── __init__.py
│   │   ├── features.py        # 特征工程
│   │   ├── models.py          # 模型定义
│   │   ├── trainer.py         # 模型训练 (含CPCV)
│   │   ├── monitor.py         # 模型监控 (新增: 概念漂移)
│   │   └── lifecycle.py       # 模型生命周期管理 (新增)
│   ├── nlp/                   # NLP模块 (Phase 4, 替代原HFT)
│   │   ├── __init__.py
│   │   ├── news.py            # 新闻情绪分析
│   │   ├── sentiment.py       # 情绪得分计算
│   │   └── cot.py             # CFTC COT数据处理
│   ├── state/                 # 状态管理 (新增)
│   │   ├── __init__.py
│   │   ├── persistence.py     # 状态持久化
│   │   └── recovery.py        # 灾难恢复
│   ├── alerts/                # 告警模块 (新增)
│   │   ├── __init__.py
│   │   └── notifier.py        # 多渠道通知
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       ├── logger.py          # 日志
│       └── helpers.py         # 辅助函数
├── notebooks/                 # Jupyter笔记本
│   ├── 01_data_exploration.ipynb
│   ├── 02_factor_analysis.ipynb
│   ├── 03_backtest_analysis.ipynb
│   ├── 04_stress_test.ipynb   # (新增)
│   └── 05_ml_validation.ipynb # (新增)
├── tests/                     # 测试
│   ├── __init__.py
│   ├── test_data.py
│   ├── test_factors.py
│   ├── test_backtest.py
│   ├── test_risk.py           # (新增)
│   ├── test_compliance.py     # (新增)
│   └── test_recovery.py       # (新增)
├── scripts/                   # 脚本
│   ├── download_data.py       # 数据下载
│   ├── generate_signals.py    # 信号生成
│   ├── run_backtest.py        # 回测运行
│   ├── run_stress_test.py     # 压力测试 (新增)
│   └── run_paper_trade.py     # 纸盘交易 (新增)
├── reports/                   # 报告输出
│   ├── signals/               # 信号报告
│   ├── trades/                # 交易记录
│   ├── backtests/             # 回测报告
│   ├── stress_tests/          # 压力测试报告 (新增)
│   └── tax/                   # 税务报告 (新增)
├── logs/                      # 日志
├── backups/                   # 数据库备份 (新增)
├── requirements.txt           # 依赖
├── pyproject.toml             # Poetry配置
├── README.md                  # 项目说明
├── Dockerfile                 # Docker配置
└── docker-compose.yml         # Docker Compose (新增)
```

---

## 9. 开发计划

### Phase 1: MVP (Week 1-4)

| Week | 任务 | 产出 | Gate |
|------|------|------|------|
| 1 | 数据模块 + 数据验证 + 缓存 | 多源数据获取，质量校验通过 | 数据校验100%通过 |
| 2 | 因子计算 + 信号生成 (含市场环境过滤) | 产生分级BUY/SELL/HOLD信号 | 信号逻辑单元测试通过 |
| 3 | 分级风控 + 仓位管理 + 状态持久化 | 4级风控运行，组合状态可恢复 | 风控模拟触发测试通过 |
| 4 | 回测引擎 + 压力测试 + 报告 | 完整回测报告 + 4场景压力测试 | 压力测试通过标准 |

### Phase 2: 增强策略 (Week 5-9)

| Week | 任务 | 产出 | Gate |
|------|------|------|------|
| 5 | 扩展资产池数据接入 | 15个资产数据就绪 | 数据完整性验证 |
| 6 | 截面动量 (15资产排名) | 多资产轮动信号 | 截面IC > 0.03 |
| 7 | Crypto Carry (Binance资金费率) | 资金费率套利信号 | 回测Carry收益为正 |
| 8 | 资产轮动模型 + 组合优化 | 动量+风险平价综合配置 | 综合策略Sharpe > 0.8 |
| 9 | 整合测试 + 压力测试 | 完整Phase 1+2综合回测 | 压力测试通过 |

### Phase 2.5: 纸盘交易 Gate (Week 10-22) ⚠️ 关键里程碑

| Period | 任务 | Gate |
|--------|------|------|
| Week 10-22 | Phase 1+2策略纸盘交易 (≥3个月) | Sharpe > 0.5, MaxDD < 15% |

**纸盘交易期间并行启动Phase 3开发**

### Phase 3: ML增强 (Week 10-21, 与纸盘并行)

| Week | 任务 | 产出 | Gate |
|------|------|------|------|
| 10-11 | 特征工程 (价格+宏观) | 特征库v1 (30+特征) | 无前视偏差验证 |
| 12-13 | 特征工程 (交叉特征+稳定性) | 特征库v2 (筛选后15-20特征) | IC稳定性检验通过 |
| 14-15 | XGBoost/LightGBM训练 (Purged WF) | 基础ML模型 | 验证集IC > 0.03 |
| 16-17 | CPCV验证 + 过拟合检测 | 验证通过的模型 | 训练-验证Sharpe差 < 0.5 |
| 18-19 | 信号融合 + 回测 | ML+传统融合策略 | 融合策略 > 纯传统策略 |
| 20-21 | 压力测试 + 模型监控 | 生产就绪ML管线 | 压力测试通过 |

### Phase 3.5: ML纸盘交易 Gate (Week 22-34)

| Period | 任务 | Gate |
|--------|------|------|
| Week 22-34 | ML增强策略纸盘交易 (≥3个月) | ML融合 > 传统策略, MaxDD < 15% |

### Phase 4: NLP情绪 (Week 22-29, 与ML纸盘并行)

| Week | 任务 | 产出 | Gate |
|------|------|------|------|
| 22-23 | 新闻数据采集管线 | 日度新闻流 | 数据覆盖 > 90% |
| 24-25 | FinBERT情绪分析 | 情绪得分时间序列 | 情绪因子IC > 0.02 |
| 26-27 | CFTC COT散户情绪 | 散户定位指标 | 反向信号回测有效 |
| 28-29 | 情绪因子集成到ML模型 | 增强ML模型 | SHAP贡献 > 5% |

---

## 10. 参考文献

### 必读论文

1. **Moskowitz, T.J. & Grinblatt, M. (1999)**. "Do Industries Explain Momentum?" *Journal of Finance*, 54(4), 1249-1290.

2. **Asness, C.S. (2012)**. "Levering Up to Risk Parity". *AQR Working Paper*.

3. **Asness, C.S., et al. (2013)**. "Value and Momentum Everywhere". *Journal of Finance*, 68(3), 929-985.

4. **Brunnermeier, M.K., et al. (2009)**. "Carry Trades and Currency Crashes". *NBER Macroeconomics Annual*, 23(1), 313-348.

5. **Chen, T. & Guestrin, C. (2016)**. "XGBoost: A Scalable Tree Boosting System". *KDD 2016*.

6. **Ke, Z.T., et al. (2019)**. "Predicting Returns with Text Data". *Working Paper*.

7. **López de Prado, M. (2018)**. "Advances in Financial Machine Learning". *Wiley*. — **特别重要: Purged Walk-Forward, CPCV, 过拟合检测**

8. **Microsoft Research (2020)**. "Qlib: An AI-oriented Quantitative Investment Platform". *GitHub Repository*.

9. **Keller, W.J. & Butler, A. (2015)**. "Momentum and Markowitz: A Golden Combination". *SSRN Working Paper*.

### 推荐书籍

1. **"Advances in Financial Machine Learning"** by Marcos López de Prado — 必读 (Phase 3核心参考)
2. **"Machine Learning for Asset Managers"** by Marcos López de Prado
3. **"Quantitative Trading"** by Ernest P. Chan
4. **"Inside the Black Box"** by Rishi K. Narang
5. **"Trading and Exchanges"** by Larry Harris — 市场微观结构基础

---

## 11. 附录

### A. 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 动量 | Momentum | 过去收益预测未来收益 |
| 波动率 | Volatility | 收益率的标准差 |
| 夏普比率 | Sharpe Ratio | 超额收益/波动率 |
| 最大回撤 | Max Drawdown | 峰值到谷底的最大跌幅 |
| 风险平价 | Risk Parity | 各资产风险贡献相等 |
| Carry | Carry | 持有资产的收益 |
| 截面动量 | Cross-Sectional Momentum | 资产间相对强弱排名 |
| 前视偏差 | Look-Ahead Bias | 使用未来信息导致的回测虚高 |
| 概念漂移 | Concept Drift | 数据分布随时间变化导致模型失效 |
| Purged CV | Purged Cross-Validation | 带清除间隔的交叉验证，防止标签泄漏 |
| CPCV | Combinatorial Purged CV | 组合式清除交叉验证 |
| 资金费率 | Funding Rate | 永续合约多空双方定期交换的费用 |

### B. 配置文件示例

```yaml
# strategy.yaml (v2.0)
strategy:
  name: "momentum_risk_parity_v2"
  rebalance_frequency: "monthly"
  min_rebalance_threshold: 0.02  # 权重变化 > 2% 才调仓
  
# 核心资产
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
  QQQ:
    max_weight: 0.30
    momentum_lookback: 60
    vol_target: 0.18
    asset_stop_loss: 0.12
  BTC-USD:
    max_weight: 0.15
    momentum_lookback: 30
    vol_target: 0.25
    asset_stop_loss: 0.18

# 扩展资产池 (Phase 2)
extended_assets:
  - { symbol: SLV, max_weight: 0.15 }
  - { symbol: XLK, max_weight: 0.20 }
  - { symbol: XLF, max_weight: 0.15 }
  - { symbol: XLE, max_weight: 0.15 }
  - { symbol: XLV, max_weight: 0.15 }
  - { symbol: TLT, max_weight: 0.30 }
  - { symbol: TIP, max_weight: 0.15 }
  - { symbol: EFA, max_weight: 0.20 }
  - { symbol: EEM, max_weight: 0.15 }
  - { symbol: DBC, max_weight: 0.15 }
  - { symbol: VNQ, max_weight: 0.15 }

# 分级风控 (v2.0)
risk:
  levels:
    level_1:
      drawdown_trigger: 0.05
      actions: ["alert", "increase_confidence_threshold"]
    level_2:
      drawdown_trigger: 0.08
      actions: ["reduce_positions_25pct", "close_btc", "sell_only"]
    level_3:
      drawdown_trigger: 0.12
      actions: ["reduce_positions_50pct", "safe_haven_only"]
    level_4:
      drawdown_trigger: 0.15
      actions: ["emergency_liquidation", "require_manual_review"]
  
  correlation:
    warning_threshold: 0.7      # 单一资产对
    portfolio_warning: 0.5      # 组合平均
    extreme_threshold: 0.8      # 全资产同向
  
  reentry:
    cooldown_days: 5
    initial_position_pct: 0.25
    ramp_up_weekly_pct: 0.25
    max_leverage_during_recovery: 1.0
  
  max_portfolio_leverage: 1.5
  cash_buffer: 0.05
  max_daily_trades: 5
  max_daily_turnover: 0.30
  commission_rate: 0.001
  slippage_rate: 0.0005

# 合规
compliance:
  pdt_tracking: true
  wash_sale_tracking: true
  tax_lot_method: "FIFO"

# 数据源
data:
  primary: "polygon"          # Polygon.io API
  fallback: "yfinance"        # yfinance备用
  btc_primary: "binance"      # BTC规范数据源
  cache_backend: "sqlite"
  
# 告警
alerts:
  channels: ["slack", "email"]
  slack_webhook: "${SLACK_WEBHOOK_URL}"
  email_to: "${ALERT_EMAIL}"
```

### C. Phase 4 LOB/HFT 降级说明

原PRD v1.0 Phase 4包含限价订单簿(LOB)预测和高频交易策略。技术可行性评估后决定移除，原因如下:

1. **基础设施不兼容**: LOB策略需要微秒级延迟，本系统Python/cron架构无法满足
2. **数据成本**: 美股Level-2数据 $10K-50K+/月，远超项目预算
3. **技术栈不匹配**: 需要C++/Rust、kernel bypass networking、交易所co-location
4. **监管风险**: 高频交易触发SEC Rule 15c3-5等额外合规要求

如未来需要探索LOB/HFT，建议作为独立项目立项，采用不同的技术栈和基础设施。

---

**End of Document — PRD v2.0**

---

### Phase 5: 纸盘交易系统 (Week 30-41)

**目标**: 实现完整的纸盘交易模拟系统，验证策略在真实市场环境下的表现

**时间预估**: 12周

#### 3.5.1 核心功能

| 功能 | 说明 |
|-----|------|
| 纸盘订单执行 | 模拟真实交易执行（含滑点、延迟） |
| 绩效实时追踪 | 实时计算组合绩效、IC、KS指标 |
| 门禁验证系统 | 自动验证通过标准 |
| 偏差分析 | 纸盘vs回测差异分析 |

#### 3.5.2 功能需求

**FR-5.1 纸盘交易引擎**

- 模拟订单类型: 市价单、限价单、TWAP
- 模拟滑点: 基于波动率和订单规模计算
- 模拟成交延迟: 模拟1-30分钟延迟
- 模拟部分成交: 大单拆分模拟

**FR-5.2 实时绩效追踪**

- 组合NAV和P&L (实时)
- 夏普比率 (滚动20/60/252天)
- 最大回撤 (实时)
- IC监控: Rolling IC (20天滚动)
- KS监控: 特征分布漂移检测

**FR-5.3 门禁验证系统**

纸盘通过标准 (Phase 1+2):
- 运行时长 ≥ 63个交易日
- 夏普比率 > 0.5
- 最大回撤 < 15%
- 系统可用性 > 99.9%
- 所有风控级别至少触发1次
- Rolling IC > 0.02

#### 3.5.3 模块接口

```python
class PaperTrader:
    def execute_order(self, signal, portfolio) -> PaperExecutionResult
    def get_realtime_performance(self) -> PerformanceReport
    def validate_gates(self) -> GateValidationResult

class PerformanceMonitor:
    def track_ic(self, predictions, actuals) -> float
    def track_ks_drift(self, features) -> float
    def generate_daily_report(self) -> DailyReport
```

---

### Phase 6: 实盘交易与监控 (Week 42-52)

**目标**: 实现完整的实盘交易系统，包括券商集成、实时监控、过渡管理

**时间预估**: 10-12周

**前置条件**: Phase 5 纸盘交易通过所有门禁

#### 3.6.1 券商集成

| 券商 | API | 支持资产 |
|-----|-----|---------|
| Alpaca | REST/WebSocket | US ETFs |
| Binance | REST/WebSocket | Crypto |
| Interactive Brokers | TWS API | Global |

**FR-6.1 券商API集成**

- 账户信息查询
- 订单下单 (市价、限价、止损)
- 订单状态查询
- 实时持仓推送 (WebSocket)

**FR-6.2 订单管理系统**

- 智能订单路由
- 订单拆分 (大单拆分为小单)
- 订单重试
- 订单日志记录

#### 3.6.2 资金过渡管理

**小资金试运行 (10%资本)**
- 验证: 4周无异常
- 条件: 累计亏损 < 5%

**渐进式资金放大**
- Stage 1: 10% → 25% (4周)
- Stage 2: 25% → 50% (2周)
- Stage 3: 50% → 100% (2周)

**回滚机制**
- 单日亏损 > 3% → 评估
- 累计回撤 > 10% → 回到上一阶段
- 系统故障 > 2次 → 回到纸盘

#### 3.6.3 实时监控系统

**系统健康监控**
- API响应时间 < 1秒
- 数据新鲜度 < 30分钟
- 内存使用 < 80%

**策略表现监控**
- 每日收益、累计收益
- 夏普比率、最大回撤
- 告警条件: 偏离预期 > 2σ

**模型质量监控**
- Rolling IC (20天)
- KS漂移统计量
- IC < 0.02: 告警 + 准备重训练
- KS > 0.2: 触发重训练

---

### Phase 7: 运维自动化 (Week 53+)

**目标**: 实现完全自动化的运维体系

**功能**:
- 自动化部署 (CI/CD)
- 自动化监控
- 自动化告警响应
- 自动化备份

**目标**:
- MTTR < 5分钟
- 可用性 > 99.9%
- 人工介入 < 1次/周

