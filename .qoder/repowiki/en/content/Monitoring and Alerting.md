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
</cite>

## Update Summary
**Changes Made**
- Updated to reflect complete implementation of four multi-channel notification systems (Email, Slack, Telegram, Discord through Apprise integration)
- Added comprehensive coverage of specialized alert types: risk events, stop losses, correlation breaches, data quality issues, execution failures, compliance violations, and daily summaries
- Enhanced alert hierarchy documentation with precise trigger conditions and escalation policies
- Updated configuration examples and integration points with risk management components
- Added practical examples for normal operations and emergency situations

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the comprehensive multi-channel monitoring and alerting system for the Intelligent Trading Decision System. The system provides complete implementation of four notification channels (Email, Slack, Telegram, Discord) through Apprise integration, supporting four distinct alert levels (INFO, WARNING, CRITICAL, EMERGENCY) with specialized notifications for risk events, stop losses, correlation breaches, data quality issues, execution failures, compliance violations, and daily summaries.

The alerting system integrates seamlessly with risk management and system health monitoring to provide timely, actionable notifications across multiple channels with sophisticated escalation policies and automated routing mechanisms.

## Project Structure
The monitoring and alerting capability is implemented as a dedicated module within the broader system architecture:

```mermaid
graph TB
subgraph "System Layers"
Data["Data Layer"]
Strategy["Strategy Layer"]
Execution["Execution Layer"]
Risk["Risk Management"]
Alerts["Alerting & Monitoring"]
Reporting["Reporting & Dashboards"]
end
Data --> Strategy
Strategy --> Execution
Risk --> Alerts
Execution --> Alerts
Alerts --> Reporting
```

The AlertManager module serves as the central orchestrator, managing channel configurations and notification routing while maintaining integration with risk assessment and system monitoring components.

**Section sources**
- [manager.py](file://src/alerts/manager.py#L1-L239)
- [main.py](file://main.py#L24-L55)

## Core Components

### AlertManager Implementation
The AlertManager class provides comprehensive multi-channel alerting capabilities with the following key features:

- **Channel Configuration**: Automatic detection and setup of Email (SMTP), Slack, Telegram, and Discord channels via environment variables
- **Alert Level Classification**: Four-tier hierarchy (INFO, WARNING, CRITICAL, EMERGENCY) with precise escalation rules
- **Specialized Notification Types**: Context-aware alerts for risk events, stop losses, correlation breaches, data quality issues, execution failures, compliance violations, and daily summaries
- **Apprise Integration**: Seamless integration with the Apprise library for unified multi-channel messaging
- **Fallback Mechanisms**: Graceful degradation to logging-only operation when Apprise is unavailable

### Alert Levels and Trigger Conditions
The system implements a sophisticated four-tier alert hierarchy:

- **INFO**: Daily trading summaries, normal operational signals, and routine status updates
- **WARNING**: Risk Level 1 events, data quality issues, and preliminary risk indicators
- **CRITICAL**: Risk Level 2+ events, system errors, broker API disconnections, and compliance violations
- **EMERGENCY**: Risk Level 4 events, system crashes, and emergency liquidation triggers

**Section sources**
- [manager.py](file://src/alerts/manager.py#L18-L24)
- [manager.py](file://src/alerts/manager.py#L128-L239)

## Architecture Overview
The alerting system integrates deeply with the trading system's risk management and execution components:

```mermaid
sequenceDiagram
participant RM as "Risk Manager"
participant CM as "Correlation Monitor"
participant OM as "Order Manager"
participant AM as "AlertManager"
participant APP as "Apprise Router"
participant SL as "Slack Channel"
participant EM as "Email Inbox"
participant TG as "Telegram Chat"
participant DC as "Discord Server"
RM->>AM : "Risk Level Change Alert"
CM->>AM : "Correlation Breach Alert"
OM->>AM : "Execution Failure Alert"
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

**Section sources**
- [manager.py](file://src/alerts/manager.py#L128-L239)
- [main.py](file://main.py#L145-L150)

## Detailed Component Analysis

### Channel Configuration and Setup
The AlertManager automatically configures notification channels based on environment variables:

- **Email (SMTP)**: Configured via `ALERT_SMTP_URL` environment variable
- **Slack**: Configured via `ALERT_SLACK_WEBHOOK` incoming webhook URL  
- **Telegram**: Configured via `ALERT_TELEGRAM_TOKEN` and `ALERT_TELEGRAM_CHAT_ID`
- **Discord**: Configured via `ALERT_DISCORD_WEBHOOK` webhook URL

The system provides graceful fallback behavior - if Apprise is not installed, alerts are logged but not delivered to external channels.

**Section sources**
- [manager.py](file://src/alerts/manager.py#L39-L70)
- [.env.example](file://.env.example#L27-L45)

### Specialized Alert Types and Workflows

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

**Section sources**
- [manager.py](file://src/alerts/manager.py#L128-L239)

### Notification Routing and Delivery
The AlertManager uses Apprise's intelligent routing system to deliver notifications across multiple channels simultaneously:

- **Message Formatting**: Timestamped headers with alert level indicators
- **Priority Handling**: Critical and emergency alerts receive highest priority delivery
- **Delivery Receipts**: Comprehensive logging of delivery success/failure status
- **Retry Logic**: Built-in retry mechanisms through Apprise transport layer

**Section sources**
- [manager.py](file://src/alerts/manager.py#L71-L127)

### Integration with Risk Management Components
The alert system maintains deep integration with risk management and execution components:

- **Risk Manager Integration**: Direct correlation with portfolio drawdown calculations and risk level assessments
- **Correlation Monitor Integration**: Real-time correlation analysis and breach detection
- **Order Manager Integration**: Execution failure monitoring and reporting
- **State Management Integration**: Persistent alert history and delivery status tracking

**Section sources**
- [main.py](file://main.py#L145-L170)
- [manager.py](file://src/risk/manager.py#L39-L80)

## Dependency Analysis
The alerting system relies on several key dependencies and integrations:

```mermaid
graph TB
AM["AlertManager"] --> APP["Apprise Library"]
AM --> CFG["Environment Variables"]
AM --> LOG["Loguru Logger"]
AM --> RM["Risk Manager"]
AM --> CM["Correlation Monitor"]
AM --> OM["Order Manager"]
APP --> SL["Slack Webhook"]
APP --> EM["SMTP Email"]
APP --> TG["Telegram Bot"]
APP --> DC["Discord Webhook"]
```

**Diagram sources**
- [manager.py](file://src/alerts/manager.py#L1-L16)
- [main.py](file://main.py#L24-L28)

**Section sources**
- [manager.py](file://src/alerts/manager.py#L1-L16)
- [main.py](file://main.py#L24-L28)

## Performance Considerations
The alerting system is designed for high-performance operation in trading environments:

- **Non-blocking Operations**: Alert sending is asynchronous to avoid impacting trading cycle timing
- **Connection Pooling**: Apprise manages efficient connection reuse across channels
- **Memory Efficiency**: Minimal memory footprint with lazy channel initialization
- **Network Optimization**: Optimized delivery timing to minimize network overhead
- **Error Containment**: Isolated failure handling prevents cascading system impacts

## Troubleshooting Guide

### Common Configuration Issues
- **Missing Apprise**: System falls back to logging-only mode with warning messages
- **Invalid Webhook URLs**: Channel setup fails gracefully with configuration warnings
- **Authentication Failures**: SMTP authentication errors logged with specific error codes
- **Rate Limiting**: External service rate limits handled with exponential backoff

### Delivery Failure Scenarios
- **Network Connectivity**: Automatic retry with progressive backoff
- **Service Outages**: Fallback to alternative channels when available
- **Credential Expiration**: Graceful degradation with persistent error logging
- **Message Size Limits**: Automatic truncation for services with size constraints

### Monitoring and Diagnostics
- **Delivery Metrics**: Track success rates, delivery times, and failure patterns
- **Channel Health**: Monitor individual channel availability and performance
- **Alert Volume**: Monitor alert frequency to prevent alert fatigue
- **System Self-Monitoring**: Built-in health checks for alert infrastructure

## Conclusion
The multi-channel alerting system provides a comprehensive, production-ready notification backbone for the Intelligent Trading Decision System. Through complete implementation of four notification channels (Email, Slack, Telegram, Discord) with sophisticated alert classification and specialized notification types, the system ensures reliable, timely communication during both normal operations and emergency situations.

The integration with risk management components enables automated escalation based on portfolio performance and market conditions, while the modular design allows for easy extension and customization of alert types and delivery channels.

## Appendices

### Appendix A: Complete Alert Types Reference

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

**Section sources**
- [manager.py](file://src/alerts/manager.py#L128-L239)

### Appendix B: Configuration Reference

#### Environment Variables
- **ALERT_SMTP_URL**: Email SMTP configuration in mailtos:// format
- **ALERT_SLACK_WEBHOOK**: Slack incoming webhook URL
- **ALERT_TELEGRAM_TOKEN**: Telegram bot authentication token
- **ALERT_TELEGRAM_CHAT_ID**: Telegram chat/channel identifier
- **ALERT_DISCORD_WEBHOOK**: Discord webhook URL

#### Channel Configuration Examples
```bash
# Slack Configuration
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR_SLACK_WEBHOOK_HERE

# Email Configuration (SMTP)
ALERT_SMTP_URL=mailtos://username:password@smtp.gmail.com?to=recipient@example.com

# Telegram Configuration
ALERT_TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ALERT_TELEGRAM_CHAT_ID=YOUR_CHAT_ID

# Discord Configuration
ALERT_DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
```

**Section sources**
- [.env.example](file://.env.example#L27-L45)
- [.env](file://.env#L24-L28)

### Appendix C: Alert Level Escalation Matrix

| Alert Level | Trigger Conditions | Typical Response | Channel Priority |
|-------------|-------------------|------------------|------------------|
| INFO | Daily summaries, normal operations | Routine monitoring | Low |
| WARNING | Risk Level 1, data quality issues | Review and mitigation | Medium |
| CRITICAL | Risk Level 2+, system errors, compliance | Immediate action required | High |
| EMERGENCY | Risk Level 4, system crashes | Emergency response | Highest |

**Section sources**
- [manager.py](file://src/alerts/manager.py#L18-L24)
- [manager.py](file://src/risk/manager.py#L12-L19)