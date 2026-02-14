"""CFTC COT Sentiment Module - PRD FR-4.2

Implements retail sentiment analysis using CFTC Commitment of Traders report.
Generates weekly contrarian signals based on non-commercial positioning.
"""

import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

from ..utils.logger import logger


# CFTC commodity codes for our asset universe
COT_COMMODITY_CODES = {
    'GLD': '088691',      # Gold
    'SLV': '084691',      # Silver
    'SPY': None,          # S&P 500 - not in COT
    'QQQ': None,          # Nasdaq - not in COT
    'BTC-USD': '133741',  # Bitcoin
    'TLT': None,          # Bonds - not in COT
    'EFA': None,          # International - not in COT
    'EEM': None,          # Emerging - not in COT
    'XLF': None,          # Financials - not in COT
    'XLK': None,          # Tech - not in COT
    'XLE': '021601',      # Crude Oil
    'XLV': None,          # Healthcare - not in COT
    'VNQ': None,          # Real Estate - not in COT
    'DBC': '025601',      # Commodities Index
    'TIP': None,          # TIPS - not in COT
}

# Alternative: Use broader market indicators
COT_MARKET_INDICATORS = {
    'SPY_Proxy': '098601',  # S&P 500 Total Return Index
    'Nasdaq_Proxy': '209742',  # Nasdaq-100 Index
}


@dataclass
class COTConfig:
    """Configuration for COT sentiment analysis"""
    # Data source
    use_quandl: bool = False  # Use Quandl API (paid) vs CFTC website (free)
    quandl_api_key: Optional[str] = None
    
    # Analysis parameters
    lookback_years: int = 3  # 3-year rolling percentile
    bullish_threshold: float = 0.90  # > 90% = extreme bullish (contrarian sell)
    bearish_threshold: float = 0.10  # < 10% = extreme bearish (contrarian buy)
    
    # Cache settings
    cache_dir: str = "data/nlp"
    cache_days: int = 7  # Weekly data, cache for 7 days


class COTSentimentAnalyzer:
    """
    CFTC Commitment of Traders sentiment analysis.
    
    FR-4.2 Requirements:
    - Data source: CFTC.gov (free, weekly, released Fridays)
    - Indicators: Non-commercial net long ratio, 3-year rolling percentile
    - Signals: > 90% percentile = bearish (contrarian), < 10% = bullish
    """
    
    def __init__(self, config: Optional[COTConfig] = None):
        self.config = config or COTConfig()
        self._init_cache()
        self._historical_data = None
        
        logger.info("COTSentimentAnalyzer initialized")
    
    def _init_cache(self):
        """Initialize cache directory"""
        cache_path = Path(self.config.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
    
    def fetch_cot_data(self, commodity_code: str) -> pd.DataFrame:
        """
        Fetch COT report data for a commodity.
        
        Args:
            commodity_code: CFTC commodity code
            
        Returns:
            DataFrame with COT data
        """
        cache_file = Path(self.config.cache_dir) / f"cot_{commodity_code}.parquet"
        
        # Check cache
        if cache_file.exists():
            cached = pd.read_parquet(cache_file)
            # Check if fresh (within cache_days)
            if (datetime.now() - cached['date'].max()).days < self.config.cache_days:
                logger.info(f"Using cached COT data for {commodity_code}")
                return cached
        
        # Fetch from CFTC
        if self.config.use_quandl and self.config.quandl_api_key:
            df = self._fetch_quandl(commodity_code)
        else:
            df = self._fetch_cftc_gov(commodity_code)
        
        if df is not None and not df.empty:
            # Save to cache
            df.to_parquet(cache_file, index=False)
        
        return df
    
    def _fetch_cftc_gov(self, commodity_code: str) -> Optional[pd.DataFrame]:
        """Fetch COT data from CFTC website (free)"""
        try:
            # CFTC provides legacy futures data
            # URL for futures data in legacy format
            url = (
                f"https://cftc.gov/files/cotarchives/{datetime.now().year}/"
                f"futurescombinedinfo{commodity_code}.txt"
            )
            
            # Try alternative: use the legacy text files
            url = f"https://www.cftc.gov/files/futures/discoverallcommitments{commodity_code}.txt"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"CFTC fetch failed for {commodity_code}: HTTP {response.status_code}")
                return None
            
            # Parse the legacy format (tab-separated)
            lines = response.text.strip().split('\n')
            
            data = []
            in_data = False
            for line in lines:
                if 'Report Date' in line:
                    in_data = True
                    continue
                if in_data and line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 8:
                        try:
                            date_str = parts[0].strip()
                            if '/' in date_str:
                                date = datetime.strptime(date_str, '%m/%d/%Y')
                            else:
                                date = datetime.strptime(date_str, '%Y-%m-%d')
                            
                            # Commercial and non-commercial positions
                            # Format varies, try to parse common fields
                            data.append({
                                'date': date,
                                'commodity_code': commodity_code,
                                # These field positions vary by report type
                                'commercial_long': self._safe_float(parts, 2),
                                'commercial_short': self._safe_float(parts, 3),
                                'noncommercial_long': self._safe_float(parts, 5),
                                'noncommercial_short': self._safe_float(parts, 6),
                            })
                        except:
                            continue
            
            if data:
                df = pd.DataFrame(data)
                df = df.sort_values('date')
                logger.info(f"Fetched {len(df)} COT records for {commodity_code}")
                return df
            
        except Exception as e:
            logger.warning(f"CFTC parse failed for {commodity_code}: {e}")
        
        return None
    
    def _safe_float(self, parts: List[str], idx: int) -> float:
        """Safely parse float from list"""
        try:
            if idx < len(parts):
                val = parts[idx].replace(',', '').strip()
                return float(val) if val else 0.0
        except:
            pass
        return 0.0
    
    def _fetch_quandl(self, commodity_code: str) -> Optional[pd.DataFrame]:
        """Fetch COT data from Quandl (requires API key)"""
        if not self.config.quandl_api_key:
            return None
        
        try:
            url = f"https://data.nasdaq.com/api/v3/datasets/CFTC/{commodity_code}_FO.csv"
            params = {
                'api_key': self.config.quandl_api_key,
                'order': 'asc'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                df['date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('date')
                
                # Rename columns
                rename = {
                    'Commercial Long': 'commercial_long',
                    'Commercial Short': 'commercial_short',
                    'Noncommercial Long': 'noncommercial_long',
                    'Noncommercial Short': 'noncommercial_short',
                }
                df = df.rename(columns=rename)
                
                df['commodity_code'] = commodity_code
                
                return df[['date', 'commodity_code', 'commercial_long', 'commercial_short', 
                          'noncommercial_long', 'noncommercial_short']]
                
        except Exception as e:
            logger.warning(f"Quandl fetch failed for {commodity_code}: {e}")
        
        return None
    
    def calculate_positioning(self, cot_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate positioning indicators.
        
        FR-4.2:
        - Non-commercial net long ratio
        - Historical percentile (3-year rolling)
        
        Args:
            cot_df: DataFrame with COT data
            
        Returns:
            DataFrame with positioning indicators
        """
        if cot_df is None or cot_df.empty:
            return pd.DataFrame()
        
        df = cot_df.copy()
        
        # Calculate net positions
        df['noncommercial_net'] = df['noncommercial_long'] - df['noncommercial_short']
        df['commercial_net'] = df['commercial_long'] - df['commercial_short']
        
        # Total open interest
        total_oi = (df['noncommercial_long'] + df['noncommercial_short'] + 
                    df['commercial_long'] + df['commercial_short'])
        
        # Non-commercial net long ratio
        df['net_long_ratio'] = df['noncommercial_net'] / total_oi
        
        # 3-year rolling percentile
        lookback = 52 * self.config.lookback_years  # ~52 weeks per year
        df['percentile'] = df['net_long_ratio'].rolling(
            lookback, min_periods=20
        ).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) > 0 else np.nan,
            raw=False
        )
        
        # Generate contrarian signals
        df['contrarian_signal'] = 'neutral'
        df.loc[df['percentile'] > self.config.bullish_threshold, 'contrarian_signal'] = 'sell'  # Extreme bullish
        df.loc[df['percentile'] < self.config.bearish_threshold, 'contrarian_signal'] = 'buy'  # Extreme bearish
        
        return df
    
    def get_cot_factors(self, 
                        symbols: List[str],
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get COT-based sentiment factors for symbols.
        
        Args:
            symbols: List of asset symbols
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            DataFrame with COT factors per symbol
        """
        all_factors = []
        
        for symbol in symbols:
            commodity_code = COT_COMMODITY_CODES.get(symbol)
            
            if commodity_code is None:
                # Skip symbols without COT data
                logger.debug(f"No COT data available for {symbol}")
                continue
            
            cot_df = self.fetch_cot_data(commodity_code)
            
            if cot_df is None or cot_df.empty:
                continue
            
            # Calculate positioning
            positioned = self.calculate_positioning(cot_df)
            
            if positioned.empty:
                continue
            
            # Filter date range
            if start_date:
                positioned = positioned[positioned['date'] >= pd.to_datetime(start_date)]
            if end_date:
                positioned = positioned[positioned['date'] <= pd.to_datetime(end_date)]
            
            # Add symbol column
            positioned['symbol'] = symbol
            
            all_factors.append(positioned)
        
        if not all_factors:
            return pd.DataFrame()
        
        # Combine all symbols
        combined = pd.concat(all_factors, ignore_index=True)
        
        logger.info(f"Generated COT factors: {combined.shape}")
        
        return combined
    
    def get_latest_cot_signal(self, symbol: str) -> Dict:
        """
        Get latest COT contrarian signal for a symbol.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Dict with signal, net_long_ratio, percentile
        """
        commodity_code = COT_COMMODITY_CODES.get(symbol)
        
        if commodity_code is None:
            return {
                'symbol': symbol,
                'signal': 'no_data',
                'net_long_ratio': 0.0,
                'percentile': 0.5,
                'date': None
            }
        
        cot_df = self.fetch_cot_data(commodity_code)
        
        if cot_df is None or cot_df.empty:
            return {
                'symbol': symbol,
                'signal': 'no_data',
                'net_long_ratio': 0.0,
                'percentile': 0.5,
                'date': None
            }
        
        positioned = self.calculate_positioning(cot_df)
        
        if positioned.empty:
            return {
                'symbol': symbol,
                'signal': 'no_data',
                'net_long_ratio': 0.0,
                'percentile': 0.5,
                'date': None
            }
        
        latest = positioned.iloc[-1]
        
        return {
            'symbol': symbol,
            'signal': latest['contrarian_signal'],
            'net_long_ratio': float(latest['net_long_ratio']),
            'percentile': float(latest['percentile']) if pd.notna(latest['percentile']) else 0.5,
            'date': latest['date'].isoformat() if hasattr(latest['date'], 'isoformat') else str(latest['date'])
        }
    
    def get_aggregate_sentiment(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get aggregate COT sentiment across all available symbols.
        
        Args:
            symbols: List of asset symbols
            
        Returns:
            Dict mapping symbol -> COT sentiment score (-1 to +1)
        """
        # Contrarian: extreme bullish -> negative sentiment, extreme bearish -> positive
        sentiments = {}
        
        for symbol in symbols:
            signal_data = self.get_latest_cot_signal(symbol)
            
            if signal_data['signal'] == 'no_data':
                sentiments[symbol] = 0.0
            elif signal_data['signal'] == 'buy':
                # Extreme bearish = contrarian buy signal
                sentiments[symbol] = 1.0
            elif signal_data['signal'] == 'sell':
                # Extreme bullish = contrarian sell signal
                sentiments[symbol] = -1.0
            else:
                # Neutral - use percentile
                # High percentile (bullish) -> negative sentiment
                # Low percentile (bearish) -> positive sentiment
                percentile = signal_data['percentile']
                sentiments[symbol] = 1 - 2 * percentile  # Maps 0->1, 1->-1
        
        return sentiments
