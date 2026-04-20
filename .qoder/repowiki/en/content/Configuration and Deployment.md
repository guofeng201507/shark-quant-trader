# Configuration and Deployment

<cite>
**Referenced Files in This Document**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md)
- [Tech_Design_Document.md](file://Tech_Design_Document.md)
- [pyproject.toml](file://pyproject.toml)
- [strategy.yaml](file://config/strategy.yaml)
- [main.py](file://main.py)
- [.env.example](file://.env.example)
- [domain.py](file://src/models/domain.py)
- [PHASE1_COMPLETE.md](file://PHASE1_COMPLETE.md)
- [run_backtest.sh](file://run_backtest.sh)
- [order_manager.py](file://src/execution/order_manager.py)
- [brokers.py](file://src/live_trading/brokers.py)
- [models.py](file://src/live_trading/models.py)
- [demo_phase6.py](file://demo_phase6.py)
- [manager.py](file://src/alerts/manager.py)
- [engine.py](file://src/paper_trading/engine.py)
- [monitor.py](file://src/paper_trading/monitor.py)
- [code_review_log.md](file://code_review_log.md)
</cite>

## Update Summary
**Changes Made**
- Enhanced operational guidance for paper trading mode with cloud deployment support
- Added comprehensive live trading deployment procedures for cloud servers
- Expanded background service management documentation for production operations
- Updated API key configuration documentation with detailed broker credential setup
- Improved SSL certificate validation documentation for secure broker connections
- Enhanced deployment automation procedures for production environments

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Paper Trading Environment Setup](#paper-trading-environment-setup)
7. [Live Trading Broker Integration](#live-trading-broker-integration)
8. [Cloud Server Deployment Procedures](#cloud-server-deployment-procedures)
9. [Background Service Management](#background-service-management)
10. [Automated Deployment Procedures](#automated-deployment-procedures)
11. [API Key Configuration Documentation](#api-key-configuration-documentation)
12. [Dependency Analysis](#dependency-analysis)
13. [Performance Considerations](#performance-considerations)
14. [Troubleshooting Guide](#troubleshooting-guide)
15. [Conclusion](#conclusion)
16. [Appendices](#appendices)

## Introduction
This document explains configuration management and containerized deployment strategies for the Intelligent Trading Decision System. It focuses on:
- Pydantic-based configuration validation and environment-specific settings
- Multi-environment configuration (development, staging, production)
- Containerization with Docker and multi-service orchestration via docker-compose
- Deployment automation, scaling, and maintenance procedures
- Operational workflows linking development and production operations
- Practical examples for local development, staging deployment, and production rollout
- Guidance on avoiding configuration drift, handling deployment failures, and performing rollbacks
- **Enhanced** Comprehensive paper trading mode support for cloud deployment with background service management
- **Enhanced** Detailed live trading deployment procedures for cloud servers with SSL certificate validation
- **Enhanced** Complete API key configuration documentation for all broker integrations

**Updated** Complete implementation of strategy configuration management now includes comprehensive core assets (GLD, SPY, QQQ, BTC-USD), risk parameters, portfolio constraints, factor lookback periods, and alert channel settings supporting expandable asset universes for Phase 2. Additionally, the system now supports paper trading gates, live trading broker integration, automated deployment procedures for Phases 5-7, and comprehensive cloud deployment with background service management.

## Project Structure
The repository defines a modular project layout with dedicated directories for configuration, source code, notebooks, tests, scripts, reports, logs, backups, and packaging. The PRD and Tech Design documents describe the intended structure and deployment approach.

```mermaid
graph TB
subgraph "Repository Root"
A["config/"]
B["src/"]
C["notebooks/"]
D["tests/"]
E["scripts/"]
F["reports/"]
G["logs/"]
H["backups/"]
I["data/"]
J["requirements.txt"]
K["pyproject.toml"]
L["Dockerfile"]
M["docker-compose.yml"]
N[".env.example"]
O[".env"]
P["run_backtest.sh"]
Q["demo_phase6.py"]
R["main.py"]
S["cloud-init.yml"]
T["systemd.service"]
U["nginx.conf"]
end
A --> |"strategy.yaml<br/>assets.yaml<br/>risk.yaml<br/>compliance.yaml"| A
B --> |"data/, factors/, signals/, portfolio/, execution/, risk/, backtest/, ml/, nlp/, state/, alerts/, utils/, paper_trading/, live_trading/"| B
I --> |"raw/, processed/, cache/, state.db"| I
N --> |"Environment variables<br/>API keys<br/>broker credentials"| O
P --> |"Backtest automation<br/>deployment scripts"| P
Q --> |"Live trading validation<br/>demo scripts"| Q
R --> |"Main application entry<br/>live trading mode<br/>paper trading mode"| R
S --> |"Cloud initialization<br/>server setup"| S
T --> |"Systemd service<br/>background execution"| T
U --> |"Reverse proxy<br/>load balancing"| U
```

**Diagram sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1040-L1239)
- [.env.example](file://.env.example#L1-L82)
- [demo_phase6.py](file://demo_phase6.py#L1-L426)
- [main.py](file://main.py#L306-L365)

**Section sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1040-L1239)

## Core Components
- Configuration management leverages Pydantic and YAML for type-safe, human-readable configuration. The PRD documents a comprehensive configuration schema including strategy parameters, asset definitions, risk rules, compliance settings, and alert channels.
- Packaging and dependency management use Poetry (via pyproject.toml), ensuring reproducible environments across development and CI/CD.
- Containerization is defined with Docker and docker-compose for local development and production orchestration.
- **Paper Trading Environment**: Implements comprehensive paper trading gates with backtest validation, code quality requirements, and performance criteria.
- **Live Trading Integration**: Provides broker integration interfaces for Alpaca, Interactive Brokers, and Binance with order management and execution capabilities.
- **Automated Deployment**: Includes CI/CD pipeline with GitHub Actions, automated testing, security scanning, and deployment procedures.
- **Cloud Deployment**: Supports deployment on AWS EC2 instances with systemd service management and nginx reverse proxy.
- **Background Service Management**: Provides systemd service configuration for continuous operation in production environments.

Key configuration areas:
- Strategy parameters (rebalancing, thresholds)
- Asset universe and constraints (weights, lookbacks, stops)
- Risk controls (levels, correlation thresholds, re-entry logic)
- Compliance (PDT, wash sale tracking)
- Data sources and caching
- Alert channels and credentials via environment variables
- **Broker credentials and API endpoints**
- **Paper trading validation criteria**
- **Deployment environment variables**
- **Cloud server specifications**
- **Background service configuration**

**Updated** Strategy configuration now includes complete core assets (GLD, SPY, QQQ, BTC-USD) with detailed risk parameters, portfolio constraints, factor lookback periods, and alert channel settings supporting expandable asset universes for Phase 2 expansion. The system also includes comprehensive paper trading gates and live trading broker integration capabilities with enhanced SSL certificate validation for secure cloud deployments.

**Section sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L121-L1323)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L121-L149)
- [pyproject.toml](file://pyproject.toml)
- [strategy.yaml](file://config/strategy.yaml)
- [order_manager.py](file://src/execution/order_manager.py#L87-L106)

## Architecture Overview
The system follows a layered architecture with clear separation of concerns. Configuration drives behavior across modules, while Docker and docker-compose enable consistent deployment across environments. The architecture now includes paper trading validation, live trading execution layers, and cloud deployment infrastructure.

```mermaid
graph TB
subgraph "Configuration Layer"
CFG["Pydantic + YAML<br/>strategy.yaml, assets.yaml, risk.yaml, compliance.yaml"]
ENV[".env + .env.example<br/>API keys, broker creds"]
MODE["Execution Modes<br/>--mode paper/live/backtest/stress"]
end
subgraph "Runtime Services"
DS["Data Service"]
SG["Signals Service"]
PO["Portfolio Service"]
EX["Execution Service<br/>(Paper/Live)"]
RM["Risk Service"]
ST["State Service"]
AL["Alerts Service"]
PT["Paper Trading Monitor"]
LT["Live Trading Manager"]
end
subgraph "Validation Layers"
PG["Paper Trading Gates<br/>(Backtest + Code Quality)"]
LTG["Live Trading Validation<br/>(Capital Ramp + Rollback)"]
end
subgraph "Cloud Infrastructure"
CI["CI/CD Pipeline<br/>(GitHub Actions)"]
CD["Container Deployment<br/>(Docker + Compose)"]
CS["Cloud Servers<br/>(AWS EC2)"]
BS["Background Services<br/>(systemd)"]
RP["Reverse Proxy<br/>(nginx)"]
end
CFG --> DS
CFG --> SG
CFG --> PO
CFG --> EX
CFG --> RM
CFG --> ST
CFG --> AL
ENV --> EX
ENV --> DS
MODE --> EX
PG --> LT
LT --> EX
PT --> LTG
LTG --> EX
DS --> SG
SG --> PO
PO --> EX
EX --> ST
ST --> AL
CI --> CD
CD --> CS
CS --> BS
BS --> RP
```

**Diagram sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L34-L86)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1040-L1239)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1115-L1169)
- [demo_phase6.py](file://demo_phase6.py#L378-L426)

## Detailed Component Analysis

### Configuration Management with Pydantic and YAML
- Schema-driven configuration ensures type safety and reduces runtime errors.
- Environment-specific overrides are supported via environment variable substitution in configuration files.
- Configuration is split into focused domains (strategy, assets, risk, compliance) for maintainability.
- **Paper trading configuration**: Includes validation criteria and performance thresholds.
- **Broker configuration**: Supports multiple broker integrations with API credentials.

```mermaid
flowchart TD
Start(["Load config"]) --> ReadYAML["Read YAML files"]
ReadYAML --> EnvSub["Expand env vars from .env"]
EnvSub --> Validate["Validate with Pydantic models"]
Validate --> ModeCheck{"Execution Mode?"}
ModeCheck --> |paper| PaperConfig["Load paper trading configs"]
ModeCheck --> |live| LiveConfig["Load live broker configs"]
ModeCheck --> |backtest| BTConfig["Load backtest configs"]
ModeCheck --> |stress| STConfig["Load stress test configs"]
PaperConfig --> PGCheck{"Paper Trading?"}
PGCheck --> |Yes| PGValidate["Validate against Gates"]
PGCheck --> |No| Apply["Apply to runtime services"]
LiveConfig --> Apply
BTConfig --> Apply
STConfig --> Apply
PGValidate --> PGPass{"Gates Passed?"}
PGPass --> |No| PGFail["Reject Paper Trade"]
PGPass --> |Yes| Apply
Apply --> End(["Ready"])
PGFail --> End
```

**Diagram sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L121-L1323)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1115-L1169)
- [demo_phase6.py](file://demo_phase6.py#L378-L426)

**Section sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L121-L1323)

### Environment-Specific Settings
- Development: Local execution with Poetry-managed virtual environments, optional Jupyter exploration, and minimal external dependencies.
- Staging: Containerized services with docker-compose, shared volumes for logs/backups/reports, and environment variables for secrets.
- Production: Multi-stage Docker builds, restricted runtime privileges, persistent storage for state and backups, and strict environment variable injection for API keys and alert credentials.
- **Paper Trading**: Dedicated environment with validation gates and performance monitoring.
- **Live Trading**: Production-grade environment with broker connectivity and real-time execution.

Operational guidance:
- Keep secrets out of code; inject via environment variables.
- Use separate configuration overlays for each environment.
- Validate configuration before deploying to avoid drift.
- **Implement paper trading gates before live trading activation**.
- **Configure cloud-specific environment variables for production deployment**.

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1171-L1230)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L889-L1005)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1115-L1169)

### Containerization with Docker and docker-compose
- Dockerfile defines a reproducible image for the system.
- docker-compose orchestrates multi-service deployments across environments.
- Services include data ingestion, factor computation, signal generation, portfolio optimization, execution, risk management, state persistence, and alerting.
- **Multi-environment support**: Separate configurations for development, staging, and production.

```mermaid
sequenceDiagram
participant Dev as "Developer"
participant DC as "docker-compose"
participant DF as "Dockerfile"
participant Svc as "Service Container"
Dev->>DC : "compose up"
DC->>DF : "build images"
DF-->>DC : "built image"
DC->>Svc : "run service(s)"
Svc-->>Dev : "ready on ports"
```

**Diagram sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1110-L1112)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1171-L1230)

**Section sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1110-L1112)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1171-L1230)

### Deployment Automation and Rollout Procedures
- Local development: Use Poetry to manage dependencies and run scripts for data download, signal generation, backtests, and paper trading.
- Staging: Run docker-compose with environment-specific overrides; validate configuration and health checks.
- Production: Perform blue/green or rolling updates; retain previous image/tag for quick rollback; automate backups of state and logs.
- **CI/CD Pipeline**: Automated testing, security scanning, and deployment through GitHub Actions workflow.

```mermaid
flowchart TD
Prep["Prepare artifacts<br/>Docker image + configs"] --> Stage["Deploy to staging"]
Stage --> Validate["Run smoke tests<br/>health checks + basic workflows"]
Validate --> Pass{"Pass?"}
Pass --> |No| Fix["Fix issues<br/>rollback configs/images"]
Pass --> |Yes| PG["Paper Trading Validation"]
PG --> PGPass{"Gates Passed?"}
PGPass --> |No| PGFix["Address validation issues"]
PGPass --> |Yes| LT["Live Trading Validation"]
LT --> LTPass{"Capital Ramp OK?"}
LTPass --> |No| LTFix["Rollback to paper trading"]
LTPass --> |Yes| Prod["Deploy to production"]
Prod --> Monitor["Monitor metrics/alerts"]
Fix --> Stage
PGFix --> PG
LTFix --> LT
```

**Diagram sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1171-L1230)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L889-L1005)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1219-L1229)

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1171-L1230)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L889-L1005)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1219-L1229)

### Strategy Configuration Details

**Updated** Complete strategy configuration implementation now includes comprehensive parameter sets:

#### Core Assets Configuration
The system supports four core assets with detailed risk parameters:

| Asset | Max Weight | Momentum Lookback | Vol Target | Asset Stop Loss |
|-------|------------|-------------------|------------|-----------------|
| GLD | 50% | 90 days | 12% | 12% |
| SPY | 40% | 60 days | 15% | 12% |
| QQQ | 30% | 60 days | 18% | 12% |
| BTC-USD | 15% | 30 days | 25% | 18% |

#### Extended Asset Universe (Phase 2)
Support for 15+ assets including:
- **Precious Metals**: SLV (Silver ETF)
- **Sector ETFs**: XLK (Technology), XLF (Financials), XLE (Energy), XLV (Healthcare)
- **Bond ETFs**: TLT (20-Year Treasury), TIP (Inflation-Protected Bonds)
- **International**: EFA (Developed Markets), EEM (Emerging Markets)
- **Commodities**: DBC (Commodities), VNQ (REITs)

#### Risk Management Framework
Four-level hierarchical risk control:
- **Level 1** (5% drawdown): Alert, increase confidence threshold, block BTC new positions
- **Level 2** (8% drawdown): Reduce positions 25%, close BTC, sell-only mode
- **Level 3** (12% drawdown): Reduce positions 50%, safe-haven only, manual review
- **Level 4** (15% drawdown): Emergency liquidation, require manual confirmation

#### Portfolio Constraints
- Target volatility: 15%
- Max leverage: 1.5x
- Minimum trade amount: $100
- Min rebalance threshold: 2%
- Cash buffer: 5%
- Max daily trades: 5
- Max daily turnover: 30%

#### Factor Configuration
- **Momentum**: 60-day and 120-day periods
- **Volatility**: 20-day and 60-day periods (annualized)
- **SMA**: 20-day, 50-day, and 200-day periods
- **RSI**: 14-day period
- **ATR**: 14-day period

#### Alert Channel Configuration
Multi-channel alerting system supporting:
- Slack webhooks
- Email via SMTP
- Telegram bots
- Discord webhooks

**Section sources**
- [strategy.yaml](file://config/strategy.yaml)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L55-L76)
- [PHASE1_COMPLETE.md](file://PHASE1_COMPLETE.md#L261-L279)

### Scaling Requirements
- Horizontal scaling: Stateless services (signals, backtesting) can scale independently; ensure shared caches/backends are resilient.
- Vertical scaling: CPU-bound tasks (feature engineering, backtesting) benefit from increased cores; GPU resources may be required for NLP inference in later phases.
- Storage: Persist state and logs; configure retention policies for backups and logs.
- Network: Ensure low-latency access to data providers and brokers; consider caching strategies.

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L141-L150)

### Maintenance Procedures
- Regular model retraining and lifecycle management for ML components.
- Periodic review of configuration drift; enforce configuration-as-code with version control.
- Automated database backups and log rotation.
- Compliance and audit trails for regulatory reporting.

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L526-L573)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1225-L1323)

## Paper Trading Environment Setup

### Paper Trading Gates (NEW)
The system implements comprehensive paper trading validation before live trading activation.

#### Pre-Paper Trading Requirements
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

#### Paper Trading Criteria (Minimum 3 Months)
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

#### Live Trading Progression
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

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L2156-L2210)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L870-L934)

## Live Trading Broker Integration

### Enhanced Broker Integration Support
The system provides standardized interfaces for multiple broker integrations with enhanced capabilities:

| Broker | API Type | Supported Assets | Paper Trading | SSL Certificate Validation |
|--------|----------|------------------|---------------|----------------------------|
| Alpaca | REST/WebSocket | US ETFs | ✅ (free) | ✅ (certifi certificates) |
| Interactive Brokers | TWS API | Global | ✅ (free) | ✅ (certifi certificates) |
| Binance | REST/WebSocket | Cryptocurrency | ✅ (Testnet) | ✅ (certifi certificates) |

#### SSL Context Creation with Certificate Validation
All broker adapters now implement secure SSL context creation using certifi certificates for macOS compatibility and proper certificate validation:

```python
# SSL context creation with certificate validation
ssl_context = ssl.create_default_context(cafile=certifi.where())
connector = aiohttp.TCPConnector(ssl=ssl_context)
headers = {"X-MBX-APIKEY": self.api_key}
self.session = aiohttp.ClientSession(headers=headers, connector=connector)
```

#### Order Management System
The OrderManagementSystem handles order lifecycle with broker integration capabilities:

```mermaid
flowchart TD
Create["create_orders()"] --> Validate["Validate positions & prices"]
Validate --> PriceCheck{"Valid price?"}
PriceCheck --> |No| Skip["Skip order"]
PriceCheck --> |Yes| Build["Build Order object"]
Build --> Submit["submit_order()"]
Submit --> SimCheck{"Live or Paper?"}
SimCheck --> |Paper| SimFill["Immediate fill simulation"]
SimCheck --> |Live| RealSubmit["Real broker submission"]
SimFill --> Track["check_order_status()"]
RealSubmit --> Track
Track --> Archive["archive_completed_orders()"]
```

**Diagram sources**
- [order_manager.py](file://src/execution/order_manager.py#L29-L85)
- [order_manager.py](file://src/execution/order_manager.py#L87-L125)

#### Enhanced Error Reporting and Edge Case Handling
The BinanceAdapter includes comprehensive error reporting and edge case handling:

- **SSL Certificate Validation**: Uses certifi certificates for secure API connections
- **Error Response Handling**: Detailed error messages with HTTP status codes
- **Demo Mode Support**: Comprehensive demo mode for testing without real API keys
- **Testnet Integration**: Built-in support for Binance Testnet for safe testing
- **Connection Resilience**: Robust connection handling with proper cleanup

#### Order Cost Calculation
Transaction cost estimation for different asset classes:

- **Commission**: $0/trade (Alpaca), 0.1% fallback
- **Slippage**: 0.05% for stocks, 0.1% for BTC
- **Spread**: Half-spread impact

**Section sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L878-L899)
- [order_manager.py](file://src/execution/order_manager.py#L188-L226)
- [brokers.py](file://src/live_trading/brokers.py#L129-L132)
- [brokers.py](file://src/live_trading/brokers.py#L339-L343)

### Environment-Based Configuration for Live Trading Mode Switching
The system now supports dynamic live trading mode switching through environment variables and command-line arguments:

#### Live Trading Mode Configuration
```python
# Global flag for live mode switching
USE_LIVE_BROKER = False

# Command-line argument parsing
parser.add_argument("--live", action="store_true", help="Use live broker APIs")

# Environment variable configuration
ALPACA_PAPER=true  # true for paper trading, false for live
BINANCE_TESTNET=true  # true for testnet, false for live
```

#### Demo vs Live Mode Implementation
The demo script demonstrates the new live trading mode switching capability:

```python
# Live mode with API keys
if alpaca_key and alpaca_secret and USE_LIVE_BROKER:
    alpaca = AlpacaAdapter(
        api_key=alpaca_key,
        secret_key=alpaca_secret,
        paper=alpaca_paper,
        demo_mode=False
    )

# Demo mode without API keys  
else:
    alpaca = AlpacaAdapter(
        api_key="demo_key",
        secret_key="demo_secret",
        paper=True,
        demo_mode=True
    )
```

**Section sources**
- [demo_phase6.py](file://demo_phase6.py#L66-L67)
- [demo_phase6.py](file://demo_phase6.py#L383-L386)
- [demo_phase6.py](file://demo_phase6.py#L80-L98)
- [demo_phase6.py](file://demo_phase6.py#L113-L131)

## Cloud Server Deployment Procedures

### AWS EC2 Server Configuration
For production deployment, the system supports AWS EC2 instances with specific hardware requirements:

#### Hardware Specifications
- **Phase 1-2**: t3.medium (2 vCPU, 4GB RAM)
- **Phase 4 NLP**: g4dn.xlarge (GPU) for machine learning inference
- **Storage**: 20GB SSD for OS and applications
- **Network**: 100Mbps bandwidth minimum

#### Server Setup Process
```bash
# 1. Launch EC2 Instance
# Choose Ubuntu 20.04 LTS AMI
# Select t3.medium for Phase 1-2 deployment

# 2. Configure Security Groups
# Allow inbound: SSH (22), HTTP (80), HTTPS (443)
# Allow outbound: All traffic

# 3. Connect to Server
ssh -i your-key.pem ubuntu@your-instance-ip

# 4. Install Dependencies
sudo apt update
sudo apt install -y docker.io docker-compose git curl

# 5. Configure Docker
sudo usermod -aG docker ubuntu
newgrp docker

# 6. Deploy Application
git clone https://github.com/your-repo/shark-quant-trader.git
cd shark-quant-trader
cp .env.example .env
# Edit .env with your API keys and configurations
docker-compose up -d
```

#### Cloud Initialization Script
```yaml
# cloud-init.yml
# Cloud-init script for automatic server setup
# This runs on first boot

# Package updates
package_update: true
package_upgrade: true

# Install packages
packages:
  - docker.io
  - docker-compose
  - git
  - curl

# Create trading user
users:
  - name: trading
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: docker

# Clone repository
runcmd:
  - git clone https://github.com/your-repo/shark-quant-trader.git /home/trading/app
  - cd /home/trading/app && cp .env.example .env
  - echo "Server ready for deployment"

# Configure firewall
firewall:
  enabled: true
  rules:
    - { port: "22", protocol: "tcp", cidr: "0.0.0.0/0" }
    - { port: "80", protocol: "tcp", cidr: "0.0.0.0/0" }
    - { port: "443", protocol: "tcp", cidr: "0.0.0.0/0" }
```

**Section sources**
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1041-L1052)
- [code_review_log.md](file://code_review_log.md#L870-L878)

### Production Deployment Architecture
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
      - TRADING_MODE=live
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    
  monitoring:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./metrics:/app/metrics
      
  dashboard:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - ./grafana-storage:/var/lib/grafana
```

### Deployment Flow
```
Development → Backtest Validation → Stress Testing → Paper Trading (≥3 months) → Small Capital Live → Full Capital Live

Paper Trading Gates:
- Sharpe > 0.5 (paper trading period)
- Max Drawdown < 15%

Live Trading Gates:
- Small Capital: 4 weeks no major issues, deviation < 2%
- Full Capital: Gradual ramp with risk verification at each stage
```

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1170-L1258)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1062-L1078)

## Background Service Management

### Systemd Service Configuration
For continuous operation in production environments, the system can be managed as a background service:

#### Service Definition
```ini
# /etc/systemd/system/shark-trader.service
[Unit]
Description=Shark Quant Trader Service
After=network.target docker.service

[Service]
Type=simple
User=trading
Group=docker
WorkingDirectory=/home/trading/app
EnvironmentFile=/home/trading/app/.env
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Service Management Commands
```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable shark-trader.service

# Start the service
sudo systemctl start shark-trader.service

# Check service status
sudo systemctl status shark-trader.service

# View service logs
sudo journalctl -u shark-trader.service -f

# Restart the service
sudo systemctl restart shark-trader.service
```

#### Log Rotation Configuration
```bash
# /etc/logrotate.d/shark-trader
/home/trading/app/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    copytruncate
}
```

### Reverse Proxy Configuration
For web-based monitoring and management interfaces:

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/shark-trader
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /metrics {
        proxy_pass http://localhost:9090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/shark-trader /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1909-L1971)

## API Key Configuration Documentation

### Comprehensive Broker Credential Setup
Complete documentation for configuring API keys and broker credentials for all supported trading platforms:

#### Alpaca API Configuration
```bash
# .env file configuration
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_PAPER=true  # Use paper trading (true) or live trading (false)
```

**Alpaca Integration Details:**
- **Paper Trading**: Free API access for testing and development
- **Live Trading**: Requires approved brokerage account
- **Rate Limits**: 200 requests per minute for market data
- **Authentication**: API key/secret pair with REST and WebSocket endpoints

#### Binance API Configuration
```bash
# .env file configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_TESTNET=true  # Use testnet (true) or mainnet (false)
BINANCE_FAPI_BASE=https://fapi.binance.com  # Mainnet futures endpoint
```

**Binance Integration Details:**
- **Testnet**: Free sandbox environment for development
- **Mainnet**: Requires funded trading account
- **Cryptocurrency Focus**: BTC, ETH, and other digital assets
- **API Endpoints**: Spot trading, futures trading, margin trading

#### Interactive Brokers Configuration
```bash
# .env file configuration
IBKR_HOST=127.0.0.1  # TWS or IB Gateway host
IBKR_PORT=7497       # Connection port
IBKR_CLIENT_ID=1     # Client identifier
```

**IBKR Integration Details:**
- **TWS API**: Requires running Trader Workstation or Gateway
- **Global Markets**: Access to international exchanges
- **Advanced Features**: Options, futures, forex trading
- **Setup Complexity**: Higher barrier to entry due to TWS requirement

#### Polygon.io Data Configuration
```bash
# .env file configuration
POLYGON_API_KEY=your_polygon_api_key_here
```

**Data Provider Details:**
- **Primary US Equity Data**: High-quality historical and real-time data
- **Free Tier Available**: Limited requests for development
- **Commercial Licensing**: Required for production-scale usage

#### Alert System Credentials
```bash
# Slack Webhook
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Email SMTP
ALERT_SMTP_URL=mailtos://username:password@smtp.gmail.com?to=recipient@example.com

# Telegram Bot
ALERT_TELEGRAM_TOKEN=your_telegram_bot_token
ALERT_TELEGRAM_CHAT_ID=your_chat_id

# Discord Webhook
ALERT_DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK
```

### SSL Certificate Validation for Secure Connections
All broker adapters implement SSL certificate validation using the certifi package:

```python
# SSL context creation with certificate validation
import ssl
import certifi
import aiohttp

ssl_context = ssl.create_default_context(cafile=certifi.where())
connector = aiohttp.TCPConnector(ssl=ssl_context)
headers = {"X-MBX-APIKEY": self.api_key}
self.session = aiohttp.ClientSession(headers=headers, connector=connector)
```

**Certificate Validation Benefits:**
- **macOS Compatibility**: Proper certificate chain validation
- **Security**: Protection against man-in-the-middle attacks
- **Reliability**: Consistent behavior across different operating systems

### Environment Variable Management
Best practices for managing sensitive configuration data:

#### Development Environment
```bash
# .env.development
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Production Environment
```bash
# .env.production
ENV=production
DEBUG=false
LOG_LEVEL=INFO
SSL_CERT_PATH=/etc/ssl/certs/ca-certificates.crt
```

#### Configuration Loading Pattern
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access configuration with defaults
alpaca_key = os.getenv('ALPACA_API_KEY', '')
alpaca_paper = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
initial_capital = float(os.getenv('INITIAL_CAPITAL', '100000'))
```

**Section sources**
- [.env.example](file://.env.example#L67-L82)
- [brokers.py](file://src/live_trading/brokers.py#L129-L132)
- [brokers.py](file://src/live_trading/brokers.py#L339-L343)
- [code_review_log.md](file://code_review_log.md#L831-L845)

## Dependency Analysis
- Packaging: Poetry manages dependencies and virtual environments.
- Configuration: Pydantic validates YAML configurations at runtime.
- Orchestration: Docker and docker-compose coordinate multi-service deployments.
- **Paper Trading**: Validates strategy performance and code quality before live trading.
- **Broker Integration**: Provides standardized interfaces for multiple trading platforms with SSL certificate validation.
- **Cloud Deployment**: Supports AWS EC2 deployment with systemd service management.
- **Background Services**: Manages continuous operation through systemd and log rotation.

```mermaid
graph LR
P["pyproject.toml"] --> PY["Poetry"]
P --> CFG["Config YAML"]
CFG --> PYD["Pydantic"]
PYD --> RUNTIME["Runtime Services"]
DC["docker-compose.yml"] --> DOCKER["Dockerfile"]
DOCKER --> RUNTIME
ENV[".env"] --> RUNTIME
CI["CI/CD Pipeline"] --> DEPLOY["Automated Deployment"]
BROKERS["Broker Adapters"] --> SSL["SSL Cert Validation"]
RUNTIME --> BROKERS
CS["Cloud Servers"] --> SYS["Systemd Services"]
SYS --> MON["Monitoring"]
MON --> ALERT["Alerts"]
```

**Diagram sources**
- [pyproject.toml](file://pyproject.toml)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1110-L1112)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L121-L149)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1219-L1229)
- [brokers.py](file://src/live_trading/brokers.py#L129-L132)

**Section sources**
- [pyproject.toml](file://pyproject.toml)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L121-L149)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1110-L1112)

## Performance Considerations
- Favor lightweight base images and multi-stage builds to reduce attack surface and improve startup times.
- Use environment-specific resource limits (CPU/memory) in docker-compose to prevent noisy-neighbor effects.
- Cache frequently accessed data and model artifacts to minimize cold-start latency.
- Monitor service health and set up auto-recovery for transient failures.
- **Paper trading performance**: Ensure paper trading environment mirrors production conditions for accurate validation.
- **SSL Certificate Validation**: Use certifi certificates for reliable SSL connections across different operating systems.
- **Cloud Performance**: Optimize EC2 instance types based on workload requirements (CPU-intensive vs I/O-intensive).
- **Background Service Reliability**: Implement proper restart policies and health checks for continuous operation.

## Troubleshooting Guide
Common issues and resolutions:
- Configuration drift: Enforce configuration validation and keep all config under version control; use environment-specific overlays.
- Deployment failures: Validate compose files locally; pin image digests; use rollback to previous tag.
- Secrets exposure: Never commit secrets; use environment variables and secret managers.
- Data freshness: Verify cache invalidation and retry logic for data providers.
- Model degradation: Monitor concept drift and trigger retraining proactively.
- **Paper trading validation failures**: Address performance issues before progressing to live trading.
- **Broker integration issues**: Verify API credentials and network connectivity for selected broker.
- **SSL Certificate Errors**: Ensure certifi package is installed and properly configured for certificate validation.
- **Live Trading Mode Switching**: Use --live flag and proper environment variables for live broker activation.
- **Rollback procedures**: Implement staged rollbacks with clear rollback triggers and procedures.
- **Cloud Server Issues**: Check security group rules, IAM permissions, and instance health.
- **Background Service Failures**: Review systemd logs and ensure proper service configuration.
- **API Rate Limiting**: Implement proper rate limiting and retry mechanisms for broker APIs.

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1171-L1230)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L1225-L1323)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1325-L1334)
- [brokers.py](file://src/live_trading/brokers.py#L129-L132)
- [brokers.py](file://src/live_trading/brokers.py#L339-L343)

## Conclusion
The system's configuration and deployment strategy emphasizes type-safe configuration, environment isolation, and reproducible containerized deployments. By leveraging Pydantic, YAML, Docker, and docker-compose, teams can maintain consistency across development, staging, and production while enforcing robust operational practices such as validation, backups, and rollback procedures.

**Updated** The complete implementation of strategy configuration management now provides comprehensive support for core assets, risk controls, portfolio constraints, and expandable asset universes, enabling seamless transition to Phase 2 with its 15+ asset universe capabilities. The system now includes comprehensive paper trading validation gates, live trading broker integration capabilities with SSL certificate validation, automated deployment procedures for Phases 5-7, and complete cloud deployment support with background service management for production environments.

## Appendices

### Practical Examples

- **Local development setup**
  - Install dependencies via Poetry.
  - Configure environment variables from `.env.example`.
  - Run scripts for data download, signal generation, and backtests.
  - Use environment variables for API keys and alert credentials.

- **Paper trading environment setup**
  - Configure paper trading mode in environment variables.
  - Set up broker credentials for paper trading accounts.
  - Validate strategy against paper trading gates.
  - Monitor performance metrics during paper trading period.

- **Live trading broker integration**
  - Configure broker-specific API credentials.
  - Set up order routing and execution parameters.
  - Implement risk controls for live trading.
  - Monitor order execution and performance.
  - Enable SSL certificate validation for secure connections.

- **Cloud Server Deployment**
  - Launch AWS EC2 instance with appropriate specifications.
  - Configure security groups and network access.
  - Install Docker and Docker Compose.
  - Deploy application containers with proper environment variables.
  - Set up reverse proxy and monitoring services.

- **Background Service Management**
  - Create systemd service definition for continuous operation.
  - Configure log rotation and backup procedures.
  - Set up monitoring and alerting for service health.
  - Implement proper restart policies and failover mechanisms.

- **API Key Configuration**
  - Generate API keys for all supported brokers.
  - Configure environment variables for development and production.
  - Implement SSL certificate validation for secure connections.
  - Set up proper credential management and rotation procedures.

- **Live Trading Mode Switching**
  - Use --live flag to activate live broker APIs.
  - Configure environment variables for broker credentials.
  - Set ALPACA_PAPER and BINANCE_TESTNET for mode selection.
  - Test demo mode first, then switch to live mode.

- **Automated deployment procedures**
  - Build images with docker-compose.
  - Override configuration via environment variables and mounted volumes for logs/backups/reports.
  - Validate health checks and basic workflows.
  - Execute CI/CD pipeline for automated testing and deployment.

- **Strategy configuration examples**
  - Core assets configuration with risk parameters for GLD, SPY, QQQ, BTC-USD
  - Extended asset universe setup for Phase 2 expansion
  - Risk management framework with 4-level hierarchical controls
  - Portfolio constraints and factor configuration
  - Multi-channel alert system configuration
  - Paper trading validation criteria and performance thresholds
  - Live trading broker integration parameters with SSL certificate validation
  - Environment-based configuration for live trading mode switching
  - Cloud server specifications and deployment procedures
  - Background service configuration and management

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1171-L1230)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L889-L1005)
- [.env.example](file://.env.example)
- [strategy.yaml](file://config/strategy.yaml)
- [run_backtest.sh](file://run_backtest.sh)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1115-L1169)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L878-L934)
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1170-L1258)
- [demo_phase6.py](file://demo_phase6.py#L378-L426)
- [brokers.py](file://src/live_trading/brokers.py#L129-L132)
- [brokers.py](file://src/live_trading/brokers.py#L339-L343)
- [engine.py](file://src/paper_trading/engine.py#L195-L232)
- [monitor.py](file://src/paper_trading/monitor.py#L47-L97)
- [code_review_log.md](file://code_review_log.md#L831-L878)