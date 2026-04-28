#!/usr/bin/env python3
"""ANEWFN Market Data API Client.

Provides access to:
- Historical bars (OHLCV)
- Real-time quotes
- Market news
- Symbol search

Base URL: https://market-data.anewfn.com
Auth: Bearer token via ANEWFN_API_KEY env var
"""

import os
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd

# Load .env if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

BASE_URL = "https://market-data.anewfn.com"


class AnewfnClient:
    """Client for ANEWFN Market Data API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize client with API key."""
        self.api_key = api_key or os.getenv("ANEWFN_API_KEY")
        if not self.api_key:
            raise ValueError("ANEWFN_API_KEY not provided and not in environment")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        })
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make GET request to API."""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API request failed: {e}")
            return None
    
    def get_markets(self) -> Optional[List[Dict]]:
        """Get list of available markets.
        
        Returns:
            List of markets with symbol, name, timezone
        """
        data = self._get("/v1/markets")
        return data if data else None
    
    def get_bars(
        self,
        market: str,
        symbol: str,
        timeframe: str = "1d",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """Get historical OHLCV bars.
        
        Args:
            market: Exchange code (e.g., 'L' for London, 'FX' for Forex)
            symbol: Ticker symbol
            timeframe: Bar timeframe (1d, 1h, etc.)
            from_date: Start date YYYYMMDD
            to_date: End date YYYYMMDD
            
        Returns:
            DataFrame with bars data
        """
        endpoint = f"/v1/markets/{market}/{symbol}/bars/{timeframe}"
        params = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        data = self._get(endpoint, params)
        if not data or "bars" not in data:
            return None
        
        df = pd.DataFrame(data["bars"])
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["tsOpen"], unit="ms")
            df = df.drop(columns=["tsOpen"])
        return df
    
    def get_quote(self, market: str, symbol: str) -> Optional[Dict]:
        """Get real-time quote snapshot.
        
        Args:
            market: Exchange code
            symbol: Ticker symbol
            
        Returns:
            Quote data with price, volume, etc.
        """
        endpoint = f"/v1/markets/{market}/{symbol}/quote"
        return self._get(endpoint)
    
    def get_news(
        self,
        market: str,
        symbol: Optional[str] = None,
        page: int = 0,
        page_size: int = 20
    ) -> Optional[Dict]:
        """Get market news articles.
        
        Args:
            market: Exchange code
            symbol: Optional ticker filter
            page: Page index (0-based)
            page_size: Max 100
            
        Returns:
            News articles with pagination
        """
        if symbol:
            endpoint = f"/v1/markets/{market}/{symbol}/news"
        else:
            endpoint = f"/v1/markets/{market}/news"
        
        params = {"page": page, "pageSize": page_size}
        return self._get(endpoint, params)
    
    def search_symbols(self, query: str, page: int = 0, page_size: int = 20) -> Optional[Dict]:
        """Search for symbols by name/ticker.
        
        Args:
            query: Search text
            page: Page index
            page_size: Results per page
            
        Returns:
            Symbol search results
        """
        params = {"q": query, "page": page, "pageSize": page_size}
        return self._get("/v1/symbols", params)
    
    def get_intraday(self, market: str, symbol: str) -> Optional[Dict]:
        """Get intraday OHLCV periods.
        
        Args:
            market: Exchange code
            symbol: Ticker symbol
            
        Returns:
            Intraday periods data
        """
        endpoint = f"/v1/markets/{market}/{symbol}/intraday"
        return self._get(endpoint)


def main():
    """Demo the ANEWFN client."""
    print("="*60)
    print("ANEWFN API Client Demo")
    print("="*60)
    
    try:
        client = AnewfnClient()
        print("\n[✓] Client initialized")
        
        # Get markets
        print("\n[1] Fetching available markets...")
        markets = client.get_markets()
        if markets:
            print(f"  Found {len(markets)} markets")
            for m in markets[:3]:
                print(f"    - {m['symbol']}: {m['name']}")
        
        # Get quote for Vodafone (London)
        print("\n[2] Fetching quote for VOD (London)...")
        quote = client.get_quote("L", "VOD")
        if quote:
            print(f"  Current price: {quote.get('current_price')}")
            print(f"  Volume: {quote.get('volume')}")
        
        # Search symbols
        print("\n[3] Searching for 'grid'...")
        results = client.search_symbols("grid")
        if results and "items" in results:
            print(f"  Found {results.get('totalHits', 0)} results")
        
        # Get news
        print("\n[4] Fetching news for L market...")
        news = client.get_news("L", page_size=5)
        if news and "articles" in news:
            print(f"  Retrieved {len(news['articles'])} articles")
        
        print("\n" + "="*60)
        print("Demo complete!")
        
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
