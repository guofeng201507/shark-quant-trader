"""News Sentiment Module - PRD FR-4.1

Implements NLP-based news sentiment analysis using FinBERT.
Generates daily sentiment scores for assets as ML model inputs.
"""

import os
import re
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import html2text

from ..utils.logger import logger


# Asset keyword mapping for news tagging
ASSET_KEYWORDS = {
    'GLD': ['gold', 'gld', 'goldman', 'goldman sachs', 'gold etf', 'precious metal', 'gold price', 'gold futures'],
    'SLV': ['slv', 'silver', 'silver etf', 'silver price', 'silver futures', 'precious metal'],
    'SPY': ['sp500', 'sp 500', 'spy', 's&p 500', 's&p500', 'wall street', 'us stock', 'us equity', 'us market'],
    'QQQ': ['nasdaq', 'qqq', 'tech stock', 'technology sector', 'nasdaq 100', 'faang', 'magnificent seven'],
    'BTC-USD': ['bitcoin', 'btc', 'crypto', 'cryptocurrency', 'bitcoin price', 'btc price', 'bitcoin etf'],
    'TLT': ['tlt', 'treasury', 'bond', 'treasury bond', 'yield', 'interest rate', 'fed funds', 'bond yield'],
    'EFA': ['eefa', 'msci eafe', 'international stock', 'foreign stock', 'european stock', 'japan stock'],
    'EEM': ['eem', 'emerging market', 'china stock', 'india stock', 'em stock', 'frontier market'],
    'XLF': ['xlf', 'financial sector', 'bank', 'jpmorgan', 'citi', 'goldman sachs', 'financial stock', 'banking'],
    'XLK': ['xlk', 'technology sector', 'tech stock', 'apple', 'microsoft', 'nvidia', 'semiconductor', 'ai stock'],
    'XLE': ['xle', 'energy sector', 'oil', 'gas', 'energy stock', 'opec', 'exxon', 'chevron'],
    'XLV': ['xlv', 'healthcare sector', 'pharma', 'drug', 'medical', 'health stock', 'hospital'],
    'VNQ': ['vnq', 'real estate', 'reit', 'property', 'real estate etf', 'commercial real estate'],
    'DBC': ['dbc', 'commodity', 'commodity etf', 'commodity index', 'gSCI', 'broad commodity'],
    'TIP': ['tip', 'tips', 'inflation protected', 'inflation bond', 'treasury inflation'],
}

# Sentiment model cache
_model_cache = {}
_pipeline_cache = {}


@dataclass
class SentimentConfig:
    """Configuration for news sentiment analysis"""
    # Data sources
    newsapi_key: Optional[str] = None
    use_gdelt: bool = True
    use_rss: bool = True
    
    # FinBERT model
    model_name: str = "ProsusAI/finbert"  # FinBERT model for financial text
    use_gpu: bool = False
    
    # Processing
    batch_size: int = 32
    max_headline_length: int = 512
    
    # Sentiment aggregation
    sentiment_momentum_window: int = 5  # 5-day moving average for momentum
    min_articles_per_day: int = 3  # Minimum articles to calculate sentiment
    
    # Cache settings
    cache_dir: str = "data/nlp"
    cache_days: int = 30


class NewsSentimentAnalyzer:
    """
    News sentiment analysis using FinBERT.
    
    FR-4.1 Requirements:
    - Data sources: NewsAPI, GDELT, RSS feeds
    - NLP pipeline: News collection → Deduplication → Asset tagging → FinBERT → Aggregation → Momentum
    - Output: Daily sentiment scores (-1 to +1), sentiment momentum
    - Note: This is INPUT to ML model, not standalone signal
    """
    
    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
        self._init_cache()
        self._model = None
        self._tokenizer = None
        
        logger.info(f"NewsSentimentAnalyzer initialized: model={self.config.model_name}")
    
    def _init_cache(self):
        """Initialize cache directory"""
        cache_path = Path(self.config.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
    
    def _load_model(self):
        """Load FinBERT model (lazy loading)"""
        if self._model is not None:
            return
        
        model_key = f"{self.config.model_name}_{self.config.use_gpu}"
        if model_key in _model_cache:
            self._model = _model_cache[model_key]['model']
            self._tokenizer = _model_cache[model_key]['tokenizer']
            logger.info("Loaded FinBERT from cache")
            return
        
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            logger.info(f"Loading FinBERT model: {self.config.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.config.model_name
            )
            
            if not self.config.use_gpu:
                self._model = self._model.cpu()
            
            _model_cache[model_key] = {
                'model': self._model,
                'tokenizer': self._tokenizer
            }
            logger.info("FinBERT model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load FinBERT: {e}. Using fallback sentiment.")
            self._model = None
            self._tokenizer = None
    
    def fetch_news(self, symbols: List[str], date: str) -> List[Dict]:
        """
        Fetch news articles for given symbols and date.
        
        Args:
            symbols: List of asset symbols
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of news articles with title, source, date
        """
        articles = []
        
        # Try GDELT (free)
        if self.config.use_gdelt:
            articles.extend(self._fetch_gdelt(symbols, date))
        
        # Try RSS feeds (free)
        if self.config.use_rss:
            articles.extend(self._fetch_rss(symbols, date))
        
        # Try NewsAPI (requires key)
        if self.config.newsapi_key:
            articles.extend(self._fetch_newsapi(symbols, date))
        
        # Deduplicate
        articles = self._deduplicate_articles(articles)
        
        logger.info(f"Fetched {len(articles)} unique articles for {symbols} on {date}")
        return articles
    
    def _fetch_gdelt(self, symbols: List[str], date: str) -> List[Dict]:
        """Fetch news from GDELT (free)"""
        articles = []
        
        try:
            # GDELT API - search for symbols in news
            for symbol in symbols:
                keywords = ' OR '.join(ASSET_KEYWORDS.get(symbol, [symbol]))
                url = (
                    f"https://api.gdeltproject.org/api/v2/doc/doc?"
                    f"query={keywords}%20sourcelang:english&"
                    f"mode=artlist&"
                    f"maxrecords=50&"
                    f"format=json"
                )
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('articles', [])[:20]:
                        articles.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': item.get('domain', ''),
                            'date': date,
                            'symbol': symbol
                        })
                        
        except Exception as e:
            logger.warning(f"GDELT fetch failed: {e}")
        
        return articles
    
    def _fetch_rss(self, symbols: List[str], date: str) -> List[Dict]:
        """Fetch news from RSS feeds"""
        articles = []
        
        # Financial RSS feeds
        rss_feeds = [
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://www.reutersagency.com/feed/?best-topics=business-finance",
            "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        ]
        
        try:
            for feed_url in rss_feeds:
                response = requests.get(feed_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    for item in soup.find_all('item')[:30]:
                        title = item.find('title')
                        if title:
                            title_text = title.get_text()
                            # Check if any symbol is mentioned
                            for symbol in symbols:
                                keywords = ASSET_KEYWORDS.get(symbol, [symbol])
                                if any(kw.lower() in title_text.lower() for kw in keywords):
                                    articles.append({
                                        'title': title_text,
                                        'url': item.find('link').get_text() if item.find('link') else '',
                                        'source': feed_url.split('//')[1].split('/')[0],
                                        'date': date,
                                        'symbol': symbol
                                    })
                                    break
                                    
        except Exception as e:
            logger.warning(f"RSS fetch failed: {e}")
        
        return articles
    
    def _fetch_newsapi(self, symbols: List[str], date: str) -> List[Dict]:
        """Fetch news from NewsAPI (requires API key)"""
        articles = []
        
        if not self.config.newsapi_key:
            return articles
        
        try:
            base_url = "https://newsapi.org/v2/everything"
            
            for symbol in symbols:
                keywords = ASSET_KEYWORDS.get(symbol, [symbol])[:3]
                query = ' OR '.join(keywords)
                
                params = {
                    'q': query,
                    'from': date,
                    'to': date,
                    'language': 'en',
                    'sortBy': 'relevancy',
                    'pageSize': 20,
                    'apiKey': self.config.newsapi_key
                }
                
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', []):
                        articles.append({
                            'title': article.get('title', ''),
                            'url': article.get('url', ''),
                            'source': article.get('source', {}).get('name', ''),
                            'date': date,
                            'symbol': symbol
                        })
                        
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}")
        
        return articles
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title hash"""
        seen = set()
        unique = []
        
        for article in articles:
            title_hash = hashlib.md5(article['title'].lower().encode()).hexdigest()
            if title_hash not in seen:
                seen.add(title_hash)
                unique.append(article)
        
        return unique
    
    def analyze_sentiment(self, articles: List[Dict]) -> pd.DataFrame:
        """
        Analyze sentiment of articles using FinBERT.
        
        Args:
            articles: List of article dicts with 'title' key
            
        Returns:
            DataFrame with sentiment scores per article
        """
        if not articles:
            return pd.DataFrame()
        
        # Load model if needed
        if self._model is None:
            self._load_model()
        
        results = []
        
        if self._model is not None:
            # Use FinBERT
            try:
                from transformers import pipeline
                
                # Create sentiment pipeline (cached)
                pipeline_key = f"sentiment_{self.config.model_name}"
                if pipeline_key not in _pipeline_cache:
                    _pipeline_cache[pipeline_key] = pipeline(
                        "sentiment-analysis",
                        model=self._model,
                        tokenizer=self._tokenizer,
                        device=-1 if not self.config.use_gpu else 0
                    )
                
                sentiment_pipeline = _pipeline_cache[pipeline_key]
                
                # Process in batches
                for i in range(0, len(articles), self.config.batch_size):
                    batch = articles[i:i + self.config.batch_size]
                    titles = [a['title'][:self.config.max_headline_length] for a in batch]
                    
                    # Get predictions
                    outputs = sentiment_pipeline(titles)
                    
                    for article, output in zip(batch, outputs):
                        # FinBERT returns: positive, negative, neutral
                        # Convert to -1 to +1 scale
                        score = output['score']
                        label = output['label'].lower()
                        
                        if label == 'positive':
                            sentiment = score
                        elif label == 'negative':
                            sentiment = -score
                        else:
                            sentiment = 0.0
                        
                        results.append({
                            'title': article['title'],
                            'symbol': article.get('symbol', 'UNKNOWN'),
                            'source': article.get('source', ''),
                            'date': article.get('date', ''),
                            'sentiment': sentiment,
                            'raw_label': output['label'],
                            'raw_score': score
                        })
                        
            except Exception as e:
                logger.warning(f"FinBERT analysis failed: {e}. Using keyword fallback.")
                results = self._keyword_sentiment_fallback(articles)
        else:
            # Use keyword-based fallback
            results = self._keyword_sentiment_fallback(articles)
        
        return pd.DataFrame(results)
    
    def _keyword_sentiment_fallback(self, articles: List[Dict]) -> List[Dict]:
        """Simple keyword-based sentiment when FinBERT unavailable"""
        
        positive_words = [
            'rise', 'rise', 'gain', 'surge', 'soar', 'jump', 'boost', 'grow', 'growth',
            'bullish', 'upgrade', 'buy', 'outperform', 'overweight', 'positive',
            'beat', 'exceed', 'record', 'high', 'high', 'profit', 'success', 'win'
        ]
        
        negative_words = [
            'fall', 'drop', 'decline', 'plunge', 'sink', 'slump', 'drop', 'lose',
            'bearish', 'downgrade', 'sell', 'underperform', 'negative', 'miss',
            'low', 'low', 'loss', 'fail', 'warning', 'risk', 'concern', 'fear'
        ]
        
        results = []
        for article in articles:
            title = article['title'].lower()
            
            pos_count = sum(1 for w in positive_words if w in title)
            neg_count = sum(1 for w in negative_words if w in title)
            
            total = pos_count + neg_count
            if total > 0:
                sentiment = (pos_count - neg_count) / total
            else:
                sentiment = 0.0
            
            results.append({
                'title': article['title'],
                'symbol': article.get('symbol', 'UNKNOWN'),
                'source': article.get('source', ''),
                'date': article.get('date', ''),
                'sentiment': sentiment,
                'raw_label': 'keyword_fallback',
                'raw_score': abs(sentiment)
            })
        
        return results
    
    def aggregate_by_asset(self, sentiment_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate sentiment scores by asset and date.
        
        Args:
            sentiment_df: DataFrame with 'symbol', 'date', 'sentiment' columns
            
        Returns:
            DataFrame with daily sentiment per asset
        """
        if sentiment_df.empty:
            return pd.DataFrame()
        
        # Group by symbol and date, calculate mean sentiment
        aggregated = sentiment_df.groupby(['symbol', 'date']).agg({
            'sentiment': ['mean', 'std', 'count']
        }).reset_index()
        
        aggregated.columns = ['symbol', 'date', 'sentiment_mean', 'sentiment_std', 'article_count']
        
        # Filter by minimum articles
        aggregated = aggregated[aggregated['article_count'] >= self.config.min_articles_per_day]
        
        return aggregated
    
    def calculate_sentiment_momentum(self, sentiment_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate 5-day sentiment momentum.
        
        FR-4.1: Sentiment momentum = 5-day moving average change
        
        Args:
            sentiment_df: DataFrame with 'symbol', 'date', 'sentiment_mean'
            
        Returns:
            DataFrame with momentum added
        """
        if sentiment_df.empty:
            return sentiment_df
        
        # Sort by symbol and date
        sentiment_df = sentiment_df.sort_values(['symbol', 'date'])
        
        # Calculate 5-day rolling mean
        sentiment_df['sentiment_ma5'] = sentiment_df.groupby('symbol')['sentiment_mean'].transform(
            lambda x: x.rolling(5, min_periods=1).mean()
        )
        
        # Calculate momentum (change in MA)
        sentiment_df['sentiment_momentum'] = sentiment_df.groupby('symbol')['sentiment_ma5'].transform(
            lambda x: x.diff()
        )
        
        return sentiment_df
    
    def get_sentiment_factors(self, 
                              symbols: List[str],
                              start_date: str,
                              end_date: str) -> pd.DataFrame:
        """
        Get complete sentiment factors for date range.
        
        Args:
            symbols: List of asset symbols
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            
        Returns:
            DataFrame with sentiment features per symbol per day
        """
        all_sentiments = []
        
        # Iterate through each day
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Fetch news for this date
            articles = self.fetch_news(symbols, date_str)
            
            if articles:
                # Analyze sentiment
                sentiment_df = self.analyze_sentiment(articles)
                
                # Aggregate by asset
                if not sentiment_df.empty:
                    aggregated = self.aggregate_by_asset(sentiment_df)
                    all_sentiments.append(aggregated)
            
            current_date += timedelta(days=1)
        
        if not all_sentiments:
            return pd.DataFrame()
        
        # Combine all dates
        combined = pd.concat(all_sentiments, ignore_index=True)
        
        # Calculate momentum
        combined = self.calculate_sentiment_momentum(combined)
        
        # Pivot to get features per asset per day
        # Feature columns: sentiment_mean, sentiment_ma5, sentiment_momentum
        features = combined.pivot_table(
            index='date',
            columns='symbol',
            values=['sentiment_mean', 'sentiment_momentum']
        )
        
        features.columns = ['_'.join(col).strip() for col in features.columns.values]
        features = features.reset_index()
        
        logger.info(f"Generated sentiment factors: {features.shape}")
        
        return features
    
    def get_latest_sentiment(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get latest sentiment scores for symbols.
        
        Args:
            symbols: List of asset symbols
            
        Returns:
            Dict mapping symbol -> latest sentiment score
        """
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        articles = self.fetch_news(symbols, yesterday)
        
        if not articles:
            return {s: 0.0 for s in symbols}
        
        sentiment_df = self.analyze_sentiment(articles)
        aggregated = self.aggregate_by_asset(sentiment_df)
        
        result = {}
        for symbol in symbols:
            symbol_data = aggregated[aggregated['symbol'] == symbol]
            if not symbol_data.empty:
                result[symbol] = symbol_data['sentiment_mean'].iloc[-1]
            else:
                result[symbol] = 0.0
        
        return result
