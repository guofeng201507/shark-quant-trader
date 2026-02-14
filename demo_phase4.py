"""Phase 4 NLP Sentiment Demo

Demonstrates the NLP sentiment analysis pipeline per PRD FR-4.1, FR-4.2, FR-4.3:
- FR-4.1: News Sentiment Module (FinBERT, GDELT/RSS/NewsAPI)
- FR-4.2: COT Retail Sentiment Module (CFTC data)
- FR-4.3: Sentiment Factor Integration into ML pipeline
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


def create_mock_ml_features(n_samples: int = 100) -> pd.DataFrame:
    """Create mock ML features for integration demo"""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='D')
    symbols = ['GLD', 'SPY', 'QQQ', 'BTC-USD']
    
    data = []
    for date in dates:
        for symbol in symbols:
            data.append({
                'date': date,
                'symbol': symbol,
                'returns_5d': np.random.randn() * 0.02,
                'volatility_20d': np.random.uniform(0.1, 0.3),
                'momentum_60d': np.random.randn() * 0.05,
            })
    
    return pd.DataFrame(data)


def demo_news_sentiment():
    """Demo FR-4.1: News Sentiment Module"""
    print("\n" + "=" * 60)
    print("FR-4.1: News Sentiment Module (FinBERT)")
    print("=" * 60)
    
    from src.nlp.sentiment import NewsSentimentAnalyzer, SentimentConfig
    
    # Initialize analyzer
    config = SentimentConfig(
        use_gdelt=True,
        use_rss=True,
        newsapi_key=os.getenv('NEWSAPI_KEY'),
        min_articles_per_day=1,  # Lower for demo
    )
    analyzer = NewsSentimentAnalyzer(config)
    
    # Test with sample symbols
    symbols = ['GLD', 'SPY', 'BTC-USD']
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n1. Fetching news for {symbols} on {yesterday}...")
    articles = analyzer.fetch_news(symbols, yesterday)
    print(f"   Found {len(articles)} articles")
    
    if articles:
        print(f"\n   Sample headlines:")
        for i, article in enumerate(articles[:3]):
            print(f"   [{i+1}] {article['title'][:60]}...")
        
        print(f"\n2. Analyzing sentiment with FinBERT (or keyword fallback)...")
        sentiment_df = analyzer.analyze_sentiment(articles)
        
        if not sentiment_df.empty:
            print(f"   Analyzed {len(sentiment_df)} articles")
            
            # Aggregate by asset
            aggregated = analyzer.aggregate_by_asset(sentiment_df)
            print(f"\n3. Aggregated sentiment by asset:")
            if not aggregated.empty:
                for _, row in aggregated.iterrows():
                    print(f"   {row['symbol']}: sentiment={row['sentiment_mean']:.3f}, "
                          f"articles={int(row['article_count'])}")
            else:
                print("   No aggregated data (articles below minimum threshold)")
        else:
            print("   No sentiment results")
    else:
        print("   No articles found (network/API limitation)")
    
    # Get latest sentiment scores
    print(f"\n4. Getting latest sentiment summary:")
    latest = analyzer.get_latest_sentiment(symbols)
    for symbol, score in latest.items():
        print(f"   {symbol}: {score:.3f}")
    
    return analyzer, latest


def demo_cot_sentiment():
    """Demo FR-4.2: COT Retail Sentiment Module"""
    print("\n" + "=" * 60)
    print("FR-4.2: COT Retail Sentiment Module (CFTC)")
    print("=" * 60)
    
    from src.nlp.cot import COTSentimentAnalyzer, COTConfig
    
    # Initialize analyzer
    config = COTConfig(
        use_quandl=False,  # Use free CFTC data
        lookback_years=3,
    )
    analyzer = COTSentimentAnalyzer(config)
    
    # Test with symbols that have COT data
    symbols = ['GLD', 'XLE', 'BTC-USD']  # These have COT data
    
    print(f"\n1. Checking COT data availability for {symbols}...")
    
    for symbol in symbols:
        signal_data = analyzer.get_latest_cot_signal(symbol)
        print(f"\n   {symbol}:")
        print(f"      Signal: {signal_data['signal']}")
        print(f"      Net Long Ratio: {signal_data['net_long_ratio']:.3f}")
        print(f"      Percentile: {signal_data['percentile']:.3f}")
    
    print(f"\n2. Getting aggregate COT sentiment:")
    aggregate = analyzer.get_aggregate_sentiment(symbols)
    for symbol, score in aggregate.items():
        print(f"   {symbol}: {score:.3f} (contrarian: {'bullish' if score > 0.3 else 'bearish' if score < -0.3 else 'neutral'})")
    
    return analyzer, aggregate


def demo_sentiment_integration(news_sentiment: dict, cot_sentiment: dict):
    """Demo FR-4.3: Sentiment Factor Integration"""
    print("\n" + "=" * 60)
    print("FR-4.3: Sentiment Factor Integration")
    print("=" * 60)
    
    from src.nlp.integrator import SentimentFactorIntegrator, IntegrationConfig
    
    # Initialize integrator
    config = IntegrationConfig(
        news_weight=0.6,
        cot_weight=0.4,
        min_shap_contribution=0.05,
    )
    integrator = SentimentFactorIntegrator(config)
    
    # Create mock ML features
    print("\n1. Creating mock ML features for integration test...")
    ml_features = create_mock_ml_features(50)
    print(f"   ML features shape: {ml_features.shape}")
    
    # Create mock sentiment DataFrames from dicts
    print("\n2. Preparing sentiment DataFrames...")
    
    # Use datetime objects for consistency with ML features
    current_date = pd.to_datetime(datetime.now().date())
    
    news_df = pd.DataFrame([
        {'symbol': symbol, 'date': current_date, 
         'Sentiment_News_5d': score}
        for symbol, score in news_sentiment.items()
    ])
    
    cot_df = pd.DataFrame([
        {'symbol': symbol, 'date': current_date,
         'Sentiment_COT_Percentile': score}
        for symbol, score in cot_sentiment.items()
    ])
    
    print(f"   News sentiment: {len(news_df)} symbols")
    print(f"   COT sentiment: {len(cot_df)} symbols")
    
    # Integrate sentiment into ML features
    print("\n3. Integrating sentiment factors...")
    integrated = integrator.integrate(ml_features, news_df, cot_df)
    
    sentiment_cols = [c for c in integrated.columns if 'sentiment' in c.lower()]
    print(f"   Integrated features shape: {integrated.shape}")
    print(f"   Sentiment columns: {sentiment_cols}")
    
    # Get combined sentiment
    print("\n4. Combined sentiment scores:")
    combined = integrator.get_combined_sentiment(news_sentiment, cot_sentiment)
    for symbol, score in combined.items():
        signal = integrator.create_sentiment_signal(score)
        print(f"   {symbol}: {score:.3f} -> {signal}")
    
    # Get summary
    print("\n5. Sentiment feature summary:")
    summary = integrator.get_sentiment_summary(integrated)
    print(f"   Number of sentiment features: {summary['n_sentiment_features']}")
    for feat, coverage in summary['coverage'].items():
        print(f"   {feat}: {coverage:.1%} coverage")
    
    return integrator, integrated


def main():
    """Run Phase 4 NLP demo"""
    print("\n" + "#" * 60)
    print("#  PHASE 4: NLP SENTIMENT ANALYSIS DEMO")
    print("#" * 60)
    
    results = {}
    
    # 1. News Sentiment (FR-4.1)
    try:
        news_analyzer, news_sentiment = demo_news_sentiment()
        results['FR-4.1'] = 'PASS'
    except Exception as e:
        print(f"\nFR-4.1 Error: {e}")
        news_sentiment = {'GLD': 0.0, 'SPY': 0.0, 'BTC-USD': 0.0}
        results['FR-4.1'] = f'ERROR: {e}'
    
    # 2. COT Sentiment (FR-4.2)
    try:
        cot_analyzer, cot_sentiment = demo_cot_sentiment()
        results['FR-4.2'] = 'PASS'
    except Exception as e:
        print(f"\nFR-4.2 Error: {e}")
        cot_sentiment = {'GLD': 0.0, 'XLE': 0.0, 'BTC-USD': 0.0}
        results['FR-4.2'] = f'ERROR: {e}'
    
    # 3. Sentiment Integration (FR-4.3)
    try:
        integrator, integrated_features = demo_sentiment_integration(
            news_sentiment, cot_sentiment
        )
        results['FR-4.3'] = 'PASS'
    except Exception as e:
        print(f"\nFR-4.3 Error: {e}")
        results['FR-4.3'] = f'ERROR: {e}'
    
    # Summary
    print("\n" + "=" * 60)
    print("PHASE 4 DEMO SUMMARY")
    print("=" * 60)
    
    for req, status in results.items():
        status_icon = "✓" if status == 'PASS' else "✗"
        print(f"   {status_icon} {req}: {status}")
    
    all_passed = all(s == 'PASS' for s in results.values())
    print("\n" + "-" * 60)
    if all_passed:
        print("   All Phase 4 requirements PASSED")
    else:
        print("   Some requirements failed - see details above")
    print("-" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
