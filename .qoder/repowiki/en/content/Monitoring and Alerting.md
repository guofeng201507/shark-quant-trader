# Monitoring and Alerting

<cite>
**Referenced Files in This Document**
- [manager.py](file://src/alerts/manager.py)
- [__init__.py](file://src/alerts/__init__.py)
- [.env](file://.env)
- [.env.example](file://.env.example)
- [main.py](file://main.py)
- [manager.py](file://src/risk/manager.py)
- [correlation.py](file://src/risk/correlation.py)
- [logger.py](file://src/utils/logger.py)
- [manager.py](file://src/state/manager.py)
- [Tech_Design_Document.md](file://Tech_Design_Document.md)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md)
- [PHASE1_COMPLETE.md](file://PHASE1_COMPLETE.md)
</cite>

## Update Summary
**Changes Made**
- Enhanced monitoring requirements for Phases 5-7 including real-time performance tracking capabilities
- Added automated alerting for paper trading with comprehensive risk control validation
- Integrated operational monitoring for live trading with advanced state persistence and recovery
- Updated alert hierarchy documentation with paper trading gates and live trading progression criteria
- Expanded configuration examples for operational monitoring and paper trading scenarios
- Added practical examples for real-time performance tracking and operational monitoring procedures

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Enhanced Monitoring Framework](#enhanced-monitoring-framework)
6. [Paper Trading Monitoring](#paper-trading-monitoring)
7. [Live Trading Operational Monitoring](#live-trading-operational-monitoring)
8. [Real-Time Performance Tracking](#real-time-performance-tracking)
9. [Detailed Component Analysis](#detailed-component-analysis)
10. [Dependency Analysis](#dependency-analysis)
11. [Performance Considerations](#performance-considerations)
12. [Troubleshooting Guide](#troubleshooting-guide)
13. [Conclusion](#conclusion)
14. [Appendices](#appendices)

## Introduction
This document explains the comprehensive multi-channel monitoring and alerting system for the Intelligent Trading Decision System, enhanced for Phases 5-7 with real-time performance tracking, automated alerting for paper trading, and operational monitoring for live trading. The system provides complete implementation of four notification channels (Email, Slack, Telegram, Discord) through Apprise integration, supporting four distinct alert levels (INFO, WARNING, CRITICAL, EMERGENCY) with specialized notifications for risk events, stop losses, correlation breaches, data quality issues, execution failures, compliance violations, and daily summaries.

The enhanced monitoring system integrates seamlessly with risk management, paper trading gates, and operational monitoring components to provide comprehensive oversight across all trading phases with sophisticated escalation policies and automated routing mechanisms.

## Project Structure
The monitoring and alerting capability is implemented as a dedicated module within the broader system architecture with enhanced integration for operational monitoring:

```mermaid
graph TB
subgraph "Enhanced System Layers"
Data["Data Layer"]
Strategy["Strategy Layer"]
Execution["Execution Layer"]
Risk["Risk Management"]
Alerts["Alerting & Monitoring"]
PaperTrading["Paper Trading Gates"]
LiveTrading["Live Trading Operations"]
State["State Persistence"]
Reporting["Reporting & Dashboards"]
end
Data --> Strategy
Strategy --> Execution
Risk --> Alerts
Execution --> Alerts
PaperTrading --> Alerts
LiveTrading --> Alerts
State --> Alerts
Alerts --> Reporting
```

The AlertManager module serves as the central orchestrator, managing channel configurations and notification routing while maintaining integration with risk assessment, paper trading validation, and operational monitoring components.

**Section sources**
- [manager.py](file://src/alerts/manager.py#L1-L239)
- [main.py](file://main.py#L24-L55)

## Core Components

### Enhanced AlertManager Implementation
The AlertManager class provides comprehensive multi-channel alerting capabilities with enhanced features for operational monitoring:

- **Channel Configuration**: Automatic detection and setup of Email (SMTP), Slack, Telegram, and Discord channels via environment variables
- **Alert Level Classification**: Four-tier hierarchy (INFO, WARNING, CRITICAL, EMERGENCY) with precise escalation rules
- **Specialized Notification Types**: Context-aware alerts for risk events, stop losses, correlation breaches, data quality issues, execution failures, compliance violations, and daily summaries
- **Apprise Integration**: Seamless integration with the Apprise library for unified multi-channel messaging
- **Fallback Mechanisms**: Graceful degradation to logging-only operation when Apprise is unavailable
- **Operational Monitoring**: Integration with state persistence for comprehensive system health tracking

### Enhanced Alert Levels and Trigger Conditions
The system implements a sophisticated four-tier alert hierarchy with expanded coverage for operational monitoring:

- **INFO**: Daily trading summaries, normal operational signals, routine status updates, and paper trading validation results
- **WARNING**: Risk Level 1 events, data quality issues, preliminary risk indicators, and paper trading gate warnings
- **CRITICAL**: Risk Level 2+ events, system errors, broker API disconnections, compliance violations, and live trading operational issues
- **EMERGENCY**: Risk Level 4 events, system crashes, emergency liquidation triggers, and critical operational failures

**Section sources**
- [manager.py](file://src/alerts/manager.py#L18-L24)
- [manager.py](file://src/alerts/manager.py#L128-L239)

## Architecture Overview
The enhanced alerting system integrates deeply with the trading system's risk management, paper trading validation, and operational monitoring components:

```mermaid
sequenceDiagram
participant RM as "Risk Manager"
participant PM as "Paper Trading Monitor"
participant OM as "Order Manager"
participant AM as "AlertManager"
participant SM as "StateManager"
participant APP as "Apprise Router"
participant SL as "Slack Channel"
participant EM as "Email Inbox"
participant TG as "Telegram Chat"
participant DC as "Discord Server"
RM->>AM : "Risk Level Change Alert"
PM->>AM : "Paper Trading Gate Alert"
OM->>AM : "Execution Failure Alert"
SM->>AM : "State Recovery Alert"
AM->>APP : "Multi-channel Notification"
APP-->>SL : "Slack Webhook"
APP-->>EM : "Email SMTP"
APP-->>TG : "Telegram Bot"
APP-->>DC : "Discord Webhook"
APP-->>AM : "Delivery Status"
AM-->>RM : "Alert Acknowledgment"
```

**Diagram sources**
- [manager.py](file://src/alerts/manager.py#L128-L239)
- [main.py](file://main.py#L145-L150)
- [manager.py](file://src/state/manager.py#L255-L296)

**Section sources**
- [manager.py](file://src/alerts/manager.py#L128-L239)
- [main.py](file://main.py#L145-L150)

## Enhanced Monitoring Framework

### Real-Time Performance Tracking
The system now provides comprehensive real-time performance monitoring with automated alerting:

- **Live Performance Metrics**: Continuous tracking of portfolio NAV, daily P&L, and risk metrics
- **Automated Performance Reports**: Scheduled daily summaries with performance analytics
- **Real-Time Risk Assessment**: Continuous monitoring of correlation levels and risk exposure
- **Performance Anomaly Detection**: Automated alerts for unusual performance patterns

### Operational Monitoring Integration
Enhanced integration with operational monitoring components:

- **State Persistence Monitoring**: Alerts for database connectivity and backup failures
- **System Health Checks**: Automated monitoring of API connections and data freshness
- **Recovery Procedures**: Automated alerts for system recovery and restoration
- **Disaster Recovery Testing**: Regular testing and alerting for backup restoration procedures

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1233-L1271)
- [manager.py](file://src/state/manager.py#L365-L392)

## Paper Trading Monitoring

### Paper Trading Gates and Validation
The system implements comprehensive monitoring for paper trading validation:

- **Pre-Paper Trading Requirements**: Automated validation of backtest results and code quality
- **Paper Trading Criteria Monitoring**: Continuous monitoring of performance metrics during paper trading
- **Gate Validation Alerts**: Automated alerts for passing or failing paper trading gates
- **Performance Deviation Tracking**: Monitoring of live vs paper performance deviations

### Automated Paper Trading Alerting
Enhanced alerting for paper trading scenarios:

- **Paper Trading Performance Alerts**: Alerts for underperformance compared to backtest expectations
- **Risk Control Validation**: Alerts for proper functioning of risk controls during paper trading
- **Data Quality Monitoring**: Alerts for data interruptions or quality issues during paper trading
- **System Stability Monitoring**: Alerts for system crashes or interruptions during paper trading period

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1115-L1169)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L401-L416)

## Live Trading Operational Monitoring

### Live Trading Progression Monitoring
The system monitors progression through live trading stages:

- **Small Capital Gate Monitoring**: Tracking progress toward small capital deployment
- **Full Capital Gate Monitoring**: Monitoring gradual ramp-up to full capital deployment
- **Risk Controls Verification**: Continuous verification of risk controls at each deployment stage
- **Performance Validation**: Monitoring performance consistency across deployment stages

### Operational Monitoring Components
Enhanced operational monitoring for live trading:

- **Broker API Monitoring**: Alerts for broker connectivity issues and API failures
- **Order Execution Monitoring**: Real-time monitoring of order execution and settlement
- **Position Monitoring**: Continuous monitoring of positions and exposure levels
- **Market Data Monitoring**: Alerts for data quality issues and market data interruptions

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1152-L1166)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L870-L898)

## Real-Time Performance Tracking

### Performance Metrics Monitoring
The system tracks comprehensive performance metrics in real-time:

- **Portfolio NAV Tracking**: Continuous tracking of portfolio net asset value
- **Daily P&L Monitoring**: Real-time monitoring of daily profit and loss
- **Sharpe Ratio Calculation**: Automated calculation and alerting for performance ratios
- **Drawdown Monitoring**: Real-time monitoring of portfolio drawdown and peak NAV tracking

### Performance Anomaly Detection
Advanced anomaly detection for performance monitoring:

- **Performance Trend Analysis**: Automated detection of performance degradation trends
- **Outlier Detection**: Alerts for unusual performance outliers or deviations
- **Benchmark Comparison**: Real-time comparison with benchmark performance metrics
- **Stress Test Monitoring**: Continuous monitoring during stress testing scenarios

**Section sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1235-L1258)
- [PHASE1_COMPLETE.md](file://PHASE1_COMPLETE.md#L327-L335)

## Detailed Component Analysis

### Enhanced Channel Configuration and Setup
The AlertManager automatically configures notification channels based on environment variables with enhanced operational monitoring:

- **Email (SMTP)**: Configured via `ALERT_SMTP_URL` environment variable
- **Slack**: Configured via `ALERT_SLACK_WEBHOOK` incoming webhook URL  
- **Telegram**: Configured via `ALERT_TELEGRAM_TOKEN` and `ALERT_TELEGRAM_CHAT_ID`
- **Discord**: Configured via `ALERT_DISCORD_WEBHOOK` webhook URL
- **Operational Monitoring**: Enhanced integration with state persistence and system health monitoring

The system provides graceful fallback behavior - if Apprise is not installed, alerts are logged but not delivered to external channels.

**Section sources**
- [manager.py](file://src/alerts/manager.py#L39-L70)
- [.env.example](file://.env.example#L27-L45)

### Enhanced Specialized Alert Types and Workflows

#### Risk Level Change Alerts
Monitors portfolio drawdown and escalates alerts based on predefined thresholds:

```mermaid
flowchart TD
Start(["Risk Assessment"]) --> Check{"New Level > Old Level?"}
Check --> |Yes| Compare{"New Level ≥ 3?"}
Check --> |No| Info["Send INFO Alert"]
Compare --> |Yes| Critical["Send CRITICAL Alert"]
Compare --> |No| Warning["Send WARNING Alert"]
Critical --> End(["Alert Dispatched"])
Warning --> End
Info --> End
```

#### Stop Loss Alerts
Automatically detects individual asset stop loss triggers and sends appropriate warnings:

- **Partial Stop Loss**: 12% drawdown triggers 50% position reduction recommendation
- **Full Exit**: 18% drawdown triggers complete position exit recommendation

#### Correlation Breach Alerts
Monitors cross-asset correlations and triggers alerts based on correlation thresholds:

- **Pair Warning**: Individual asset pairs with correlation > 70%
- **Portfolio Warning**: Average correlation > 50% across all assets
- **Extreme Warning**: Average correlation > 80% indicating systemic risk

#### Data Quality Alerts
Detects and reports data integrity issues:

- Missing data percentage thresholds
- Price jump detection
- Volume anomaly identification

#### Execution Failure Alerts
Captures and reports order execution problems requiring manual intervention

#### Compliance Violation Alerts
Monitors trading activities for compliance breaches and generates critical alerts

#### Daily Summary Alerts
Provides comprehensive daily performance reporting including portfolio NAV, daily P&L, and top performing assets

#### Paper Trading Gate Alerts
Monitors paper trading validation and progression:

- **Gate Validation Alerts**: Alerts for passing or failing paper trading gates
- **Performance Deviation Alerts**: Alerts for significant deviations between paper and live performance
- **Risk Control Validation Alerts**: Alerts for proper functioning of risk controls during paper trading

#### Live Trading Operation Alerts
Monitors live trading operations:

- **Broker API Connection Alerts**: Alerts for broker connectivity issues
- **Order Execution Alerts**: Alerts for order execution failures or delays
- **Position Monitoring Alerts**: Alerts for abnormal position levels or exposures
- **System Health Alerts**: Alerts for system performance or stability issues

**Section sources**
- [manager.py](file://src/alerts/manager.py#L128-L239)

### Enhanced Notification Routing and Delivery
The AlertManager uses Apprise's intelligent routing system to deliver notifications across multiple channels simultaneously with enhanced operational monitoring:

- **Message Formatting**: Timestamped headers with alert level indicators
- **Priority Handling**: Critical and emergency alerts receive highest priority delivery
- **Delivery Receipts**: Comprehensive logging of delivery success/failure status
- **Retry Logic**: Built-in retry mechanisms through Apprise transport layer
- **Operational Monitoring**: Integration with state persistence for comprehensive delivery tracking

**Section sources**
- [manager.py](file://src/alerts/manager.py#L71-L127)

### Enhanced Integration with Risk Management Components
The alert system maintains deep integration with risk management, paper trading validation, and operational monitoring components:

- **Risk Manager Integration**: Direct correlation with portfolio drawdown calculations and risk level assessments
- **Correlation Monitor Integration**: Real-time correlation analysis and breach detection
- **Order Manager Integration**: Execution failure monitoring and reporting
- **State Management Integration**: Persistent alert history, delivery status tracking, and system recovery monitoring
- **Paper Trading Integration**: Automated monitoring of paper trading validation and progression
- **Live Trading Integration**: Operational monitoring for live trading deployment stages

**Section sources**
- [main.py](file://main.py#L145-L170)
- [manager.py](file://src/risk/manager.py#L39-L80)
- [manager.py](file://src/state/manager.py#L255-L296)

## Dependency Analysis
The enhanced alerting system relies on several key dependencies and integrations with expanded operational monitoring:

```mermaid
graph TB
AM["AlertManager"] --> APP["Apprise Library"]
AM --> CFG["Environment Variables"]
AM --> LOG["Loguru Logger"]
AM --> RM["Risk Manager"]
AM --> CM["Correlation Monitor"]
AM --> OM["Order Manager"]
AM --> SM["StateManager"]
AM --> PM["Paper Trading Monitor"]
APP --> SL["Slack Webhook"]
APP --> EM["SMTP Email"]
APP --> TG["Telegram Bot"]
APP --> DC["Discord Webhook"]
SM --> DB["SQLite Database"]
SM --> BK["Backup System"]
PM --> PTG["Paper Trading Gates"]
PM --> PTP["Paper Trading Progression"]
```

**Diagram sources**
- [manager.py](file://src/alerts/manager.py#L1-L16)
- [main.py](file://main.py#L24-L28)
- [manager.py](file://src/state/manager.py#L1-L392)

**Section sources**
- [manager.py](file://src/alerts/manager.py#L1-L16)
- [main.py](file://main.py#L24-L28)

## Performance Considerations
The enhanced alerting system is designed for high-performance operation in trading environments with comprehensive monitoring:

- **Non-blocking Operations**: Alert sending is asynchronous to avoid impacting trading cycle timing
- **Connection Pooling**: Apprise manages efficient connection reuse across channels
- **Memory Efficiency**: Minimal memory footprint with lazy channel initialization
- **Network Optimization**: Optimized delivery timing to minimize network overhead
- **Error Containment**: Isolated failure handling prevents cascading system impacts
- **Operational Monitoring**: Comprehensive system health monitoring without performance impact
- **Real-time Processing**: Efficient real-time performance tracking and alerting

## Troubleshooting Guide

### Common Configuration Issues
- **Missing Apprise**: System falls back to logging-only mode with warning messages
- **Invalid Webhook URLs**: Channel setup fails gracefully with configuration warnings
- **Authentication Failures**: SMTP authentication errors logged with specific error codes
- **Rate Limiting**: External service rate limits handled with exponential backoff

### Enhanced Delivery Failure Scenarios
- **Network Connectivity**: Automatic retry with progressive backoff
- **Service Outages**: Fallback to alternative channels when available
- **Credential Expiration**: Graceful degradation with persistent error logging
- **Message Size Limits**: Automatic truncation for services with size constraints
- **Operational Failures**: Enhanced monitoring and alerting for system recovery procedures

### Enhanced Monitoring and Diagnostics
- **Delivery Metrics**: Track success rates, delivery times, and failure patterns
- **Channel Health**: Monitor individual channel availability and performance
- **Alert Volume**: Monitor alert frequency to prevent alert fatigue
- **System Self-Monitoring**: Built-in health checks for alert infrastructure
- **Paper Trading Monitoring**: Track paper trading validation progress and performance
- **Live Trading Monitoring**: Monitor live trading deployment stages and operational health
- **State Persistence Monitoring**: Track database connectivity and backup procedures

## Conclusion
The enhanced multi-channel alerting system provides a comprehensive, production-ready notification backbone for the Intelligent Trading Decision System across all trading phases. Through complete implementation of four notification channels (Email, Slack, Telegram, Discord) with sophisticated alert classification, specialized notification types, and comprehensive operational monitoring, the system ensures reliable, timely communication during both normal operations and emergency situations.

The integration with risk management, paper trading validation, and operational monitoring components enables automated escalation based on portfolio performance, market conditions, and trading phase progression, while the modular design allows for easy extension and customization of alert types, delivery channels, and monitoring capabilities.

## Appendices

### Appendix A: Enhanced Alert Types Reference

#### Risk Management Alerts
- **Risk Level Change**: Portfolio drawdown-based escalation with automatic action recommendations
- **Emergency Liquidation**: Level 4 risk control activation with complete position liquidation

#### Market Monitoring Alerts
- **Correlation Breach**: Systematic risk detection through cross-asset correlation analysis
- **Stop Loss Triggered**: Individual asset risk control activation with position adjustment recommendations

#### Data Quality Alerts
- **Data Quality Issues**: Missing data detection, price anomaly identification, and volume irregularity reporting

#### Operational Alerts
- **Execution Failures**: Order processing errors requiring manual intervention
- **Compliance Violations**: Regulatory and policy violation detection with detailed reporting
- **Daily Summaries**: Comprehensive performance reporting and portfolio status updates

#### Paper Trading Alerts
- **Paper Trading Gate Validation**: Alerts for passing or failing paper trading validation gates
- **Performance Deviation Monitoring**: Alerts for significant deviations between paper and live performance
- **Risk Control Validation**: Alerts for proper functioning of risk controls during paper trading

#### Live Trading Operation Alerts
- **Broker API Connectivity**: Alerts for broker connectivity issues and API failures
- **Order Execution Monitoring**: Alerts for order execution failures or delays
- **Position Monitoring**: Alerts for abnormal position levels or exposures
- **Deployment Stage Progression**: Alerts for progress through live trading deployment stages

**Section sources**
- [manager.py](file://src/alerts/manager.py#L128-L239)

### Appendix B: Enhanced Configuration Reference

#### Environment Variables
- **ALERT_SMTP_URL**: Email SMTP configuration in mailtos:// format
- **ALERT_SLACK_WEBHOOK**: Slack incoming webhook URL
- **ALERT_TELEGRAM_TOKEN**: Telegram bot authentication token
- **ALERT_TELEGRAM_CHAT_ID**: Telegram chat/channel identifier
- **ALERT_DISCORD_WEBHOOK**: Discord webhook URL

#### Enhanced Channel Configuration Examples
```bash
# Slack Configuration
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Email Configuration (SMTP)
ALERT_SMTP_URL=mailtos://username:password@smtp.gmail.com?to=recipient@example.com

# Telegram Configuration
ALERT_TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ALERT_TELEGRAM_CHAT_ID=YOUR_CHAT_ID

# Discord Configuration
ALERT_DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
```

#### Paper Trading Configuration
```bash
# Paper Trading Mode
TRADING_MODE=paper

# Paper Trading Validation Settings
MIN_PAPER_TRADING_DAYS=63
MIN_SHARPE_RATIO=0.5
MAX_DRAWDOWN=0.15
```

#### Live Trading Configuration
```bash
# Live Trading Mode
TRADING_MODE=live

# Live Trading Deployment Settings
SMALL_CAPITAL_GATE=true
FULL_CAPITAL_GATE=true
GRADUAL_RAMP=true
```

**Section sources**
- [.env.example](file://.env.example#L27-L45)
- [.env](file://.env#L24-L28)

### Appendix C: Enhanced Alert Level Escalation Matrix

| Alert Level | Trigger Conditions | Typical Response | Channel Priority | Monitoring Scope |
|-------------|-------------------|------------------|------------------|------------------|
| INFO | Daily summaries, normal operations, paper trading validation | Routine monitoring | Low | Performance, Paper Trading |
| WARNING | Risk Level 1, data quality issues, paper trading gate warnings | Review and mitigation | Medium | Risk, Data Quality, Paper Trading |
| CRITICAL | Risk Level 2+, system errors, compliance, live trading issues | Immediate action required | High | Risk, System, Live Trading |
| EMERGENCY | Risk Level 4, system crashes, critical operational failures | Emergency response | Highest | Risk, System, Live Trading |

**Section sources**
- [manager.py](file://src/alerts/manager.py#L18-L24)
- [manager.py](file://src/risk/manager.py#L12-L19)

### Appendix D: Paper Trading Monitoring Workflow

```mermaid
flowchart TD
PTG["Paper Trading Gates"] --> Gate1["Gate 1 Validation"]
Gate1 --> Gate2["Gate 2 Validation"]
Gate2 --> PT["Paper Trading Period"]
PT --> Performance["Performance Monitoring"]
PT --> RiskControls["Risk Control Validation"]
PT --> DataQuality["Data Quality Monitoring"]
Performance --> Alerts["Automated Alerts"]
RiskControls --> Alerts
DataQuality --> Alerts
PT --> Live["Live Trading Transition"]
Live --> LiveMonitoring["Live Trading Monitoring"]
```

**Diagram sources**
- [Tech_Design_Document.md](file://Tech_Design_Document.md#L1115-L1169)
- [PRD_Intelligent_Trading_System_v2.md](file://PRD_Intelligent_Trading_System_v2.md#L870-L898)