"""NLP Module - Phase 4

Implements NLP-based sentiment analysis for trading signals.
FR-4.1: News Sentiment Module (FinBERT)
FR-4.2: CFTC COT Retail Sentiment Module
FR-4.3: Sentiment Factor Integration into ML pipeline
"""

from .sentiment import NewsSentimentAnalyzer, SentimentConfig
from .cot import COTSentimentAnalyzer, COTConfig
from .integrator import SentimentFactorIntegrator, IntegrationConfig

__all__ = [
    # FR-4.1: News Sentiment
    "NewsSentimentAnalyzer",
    "SentimentConfig",
    
    # FR-4.2: COT Sentiment
    "COTSentimentAnalyzer",
    "COTConfig",
    
    # FR-4.3: Integration
    "SentimentFactorIntegrator",
    "IntegrationConfig",
]
