"""Multi-source Data Provider - Tech Design v1.1 Section 4.1"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from ..utils.logger import logger

# Optional imports with graceful fallback
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed")

try:
    from polygon import RESTClient as PolygonClient
    POLYGON_AVAILABLE = True
except ImportError:
    POLYGON_AVAILABLE = False
    logger.warning("polygon-api-client not installed")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed")


class DataProvider:
    """
    Multi-source data acquisition with automatic fallback.
    Priority: Polygon → Binance (for BTC) → yfinance
    
    Based on PRD FR-1.1 and Tech Design Section 4.1
    """
    
    # Data validation thresholds from PRD
    VALIDATION = {
        "max_price_jump": 0.50,      # 50% single-day price jump
        "max_missing_pct": 0.05,     # 5% max missing data
        "cross_source_deviation": 0.01  # 1% cross-source price deviation
    }
    
    def __init__(self):
        """Initialize data provider with available clients"""
        self._init_clients()
        self._init_cache()
        logger.info("DataProvider initialized")
    
    def _init_clients(self):
        """Initialize data source clients"""
        # Polygon.io client
        self.polygon_client = None
        if POLYGON_AVAILABLE:
            api_key = os.getenv("POLYGON_API_KEY")
            if api_key:
                try:
                    self.polygon_client = PolygonClient(api_key)
                    logger.info("Polygon client initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Polygon client: {e}")
        
        # Binance public API (no key required)
        self.binance_base_url = os.getenv("BINANCE_FAPI_BASE", "https://fapi.binance.com")
        logger.info(f"Binance public API configured: {self.binance_base_url}")
    
    def _init_cache(self):
        """Initialize SQLite cache"""
        cache_dir = Path("data/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_path = cache_dir / "price_cache.db"
        
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_cache (
                symbol TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                source TEXT,
                cached_at TEXT,
                PRIMARY KEY (symbol, date)
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Cache initialized at {self.cache_path}")
    
    def fetch(self, symbols: List[str], start_date: str, 
              end_date: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for symbols with automatic fallback.
        
        Priority: Polygon → Binance (BTC only) → yfinance
        
        Args:
            symbols: List of asset symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dict mapping symbol -> OHLCV DataFrame
        """
        result = {}
        
        for symbol in symbols:
            logger.info(f"Fetching data for {symbol}")
            
            # Try cache first
            cached_data = self._fetch_from_cache(symbol, start_date, end_date)
            if cached_data is not None and len(cached_data) > 0:
                # Check if cache is fresh enough
                if self._is_cache_valid(cached_data, end_date):
                    result[symbol] = cached_data
                    logger.debug(f"Using cached data for {symbol}")
                    continue
            
            # Try Polygon first (for US equities/ETFs)
            df = None
            source = None
            
            if self.polygon_client and symbol not in ["BTC-USD"]:
                df = self._fetch_polygon(symbol, start_date, end_date)
                source = "polygon"
            
            # Try Binance for BTC (public API, no key required)
            if df is None and symbol == "BTC-USD" and REQUESTS_AVAILABLE:
                df = self._fetch_binance(symbol, start_date, end_date)
                source = "binance"
            
            # Fall back to yfinance
            if df is None and YFINANCE_AVAILABLE:
                df = self._fetch_yfinance(symbol, start_date, end_date)
                source = "yfinance"
            
            if df is not None and not df.empty:
                # Validate data quality
                validation = self.validate(df)
                if validation["passed"]:
                    result[symbol] = df
                    self._save_to_cache(symbol, df, source)
                    logger.info(f"Fetched {len(df)} rows for {symbol} from {source}")
                else:
                    logger.warning(f"Data validation failed for {symbol}: {validation['issues']}")
                    # Still use the data but log warning
                    result[symbol] = df
            else:
                logger.error(f"Failed to fetch data for {symbol}")
        
        return result
    
    def _fetch_polygon(self, symbol: str, start_date: str, 
                      end_date: str) -> Optional[pd.DataFrame]:
        """Fetch from Polygon.io"""
        if not self.polygon_client:
            return None
        
        try:
            aggs = self.polygon_client.get_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_=start_date,
                to=end_date
            )
            
            if aggs:
                data = [{
                    'date': pd.Timestamp(a.timestamp, unit='ms'),
                    'open': a.open,
                    'high': a.high,
                    'low': a.low,
                    'close': a.close,
                    'volume': a.volume
                } for a in aggs]
                
                df = pd.DataFrame(data)
                df.set_index('date', inplace=True)
                return df
                
        except Exception as e:
            logger.error(f"Polygon fetch failed for {symbol}: {e}")
        
        return None
    
    def _fetch_binance(self, symbol: str, start_date: str, 
                      end_date: str) -> Optional[pd.DataFrame]:
        """Fetch from Binance public Futures API (no auth required)"""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            import requests
            
            # Convert symbol to Binance format
            binance_symbol = "BTCUSDT" if symbol == "BTC-USD" else symbol.replace("-", "")
            
            # Convert dates to timestamps
            start_ts = int(pd.Timestamp(start_date).timestamp() * 1000)
            end_ts = int(pd.Timestamp(end_date).timestamp() * 1000)
            
            # Binance Futures public klines endpoint
            url = f"{self.binance_base_url}/fapi/v1/klines"
            params = {
                "symbol": binance_symbol,
                "interval": "1d",
                "startTime": start_ts,
                "endTime": end_ts,
                "limit": 1500
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            klines = response.json()
            
            if klines:
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                
                df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('date', inplace=True)
                
                # Convert to float
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                return df[['open', 'high', 'low', 'close', 'volume']]
                
        except Exception as e:
            logger.error(f"Binance fetch failed for {symbol}: {e}")
        
        return None
    
    def _fetch_yfinance(self, symbol: str, start_date: str, 
                       end_date: str) -> Optional[pd.DataFrame]:
        """Fetch from yfinance (fallback)"""
        if not YFINANCE_AVAILABLE:
            return None
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
            
            if not df.empty:
                # Standardize column names
                df.columns = df.columns.str.lower()
                df = df[['open', 'high', 'low', 'close', 'volume']]
                return df
                
        except Exception as e:
            logger.error(f"yfinance fetch failed for {symbol}: {e}")
        
        return None
    
    def validate(self, data: pd.DataFrame) -> Dict:
        """
        Validate data quality per PRD FR-1.1.
        
        Checks:
        - Price jumps > 50%
        - Missing data > 5%
        
        Returns:
            Dict with validation results
        """
        issues = []
        
        # Check for missing data
        missing_pct = data.isnull().sum().sum() / (len(data) * len(data.columns))
        if missing_pct > self.VALIDATION["max_missing_pct"]:
            issues.append(f"Missing data: {missing_pct:.1%} > {self.VALIDATION['max_missing_pct']:.0%}")
        
        # Check for extreme price jumps
        if 'close' in data.columns:
            returns = data['close'].pct_change().abs()
            price_jumps = (returns > self.VALIDATION["max_price_jump"]).sum()
            if price_jumps > 0:
                issues.append(f"Detected {price_jumps} price jump(s) > {self.VALIDATION['max_price_jump']:.0%}")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "missing_pct": missing_pct,
            "rows": len(data)
        }
    
    def _fetch_from_cache(self, symbol: str, start_date: str, 
                         end_date: str) -> Optional[pd.DataFrame]:
        """Fetch data from SQLite cache"""
        try:
            conn = sqlite3.connect(self.cache_path)
            
            query = """
                SELECT date, open, high, low, close, volume
                FROM price_cache
                WHERE symbol = ? AND date >= ? AND date <= ?
                ORDER BY date
            """
            
            df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
                
        except Exception as e:
            logger.error(f"Cache read failed: {e}")
        
        return None
    
    def _save_to_cache(self, symbol: str, data: pd.DataFrame, source: str):
        """Save data to SQLite cache"""
        try:
            conn = sqlite3.connect(self.cache_path)
            cursor = conn.cursor()
            
            cached_at = datetime.now().isoformat()
            
            for date, row in data.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO price_cache 
                    (symbol, date, open, high, low, close, volume, source, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    date.strftime('%Y-%m-%d'),
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume'],
                    source,
                    cached_at
                ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Cached {len(data)} rows for {symbol}")
            
        except Exception as e:
            logger.error(f"Cache write failed: {e}")
    
    def _is_cache_valid(self, data: pd.DataFrame, end_date: str) -> bool:
        """Check if cached data is fresh enough"""
        if data.empty:
            return False
        
        # Cache is valid if it contains data up to end_date (or close to it)
        last_date = data.index.max()
        end_dt = pd.to_datetime(end_date)
        
        # Allow 3 days gap for weekends/holidays
        return (end_dt - last_date).days <= 3
    
    def get_source_status(self) -> Dict[str, str]:
        """Get health status of each data source"""
        status = {}
        
        status["polygon"] = "connected" if self.polygon_client else "unavailable"
        status["binance"] = "available (public API)" if REQUESTS_AVAILABLE else "unavailable"
        status["yfinance"] = "available" if YFINANCE_AVAILABLE else "unavailable"
        status["cache"] = "active" if self.cache_path.exists() else "unavailable"
        
        return status