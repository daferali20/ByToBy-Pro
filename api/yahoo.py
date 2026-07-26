# api/yahoo_api.py
"""
ByToBy Pro - Yahoo Finance API Layer
"""

from __future__ import annotations

import time
from typing import Any, Optional, Dict, List
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf

# Import utils
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.logger import get_logger
    from utils.cache import cached
except ImportError:
    # Simple logger if utils not available
    import logging
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)
    
    def cached(ttl=300):
        def decorator(func):
            return func
        return decorator

logger = get_logger("YahooAPI")


class YahooAPI:
    """Professional Yahoo Finance API Wrapper."""
    
    def __init__(self, timeout: int = 15, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json,text/plain,*/*",
        })
        logger.info("Yahoo API Initialized")
    
    def _request(self, symbol: str) -> Optional[yf.Ticker]:
        """Get Yahoo Ticker object."""
        try:
            ticker = yf.Ticker(symbol)
            return ticker
        except Exception as e:
            logger.debug(f"Failed to create ticker for {symbol}: {e}")
            return None
    
    def _format_market_cap(self, market_cap: Optional[float]) -> float:
        """Format market cap to billions."""
        if not market_cap:
            return 0.0
        return round(float(market_cap) / 1_000_000_000, 2)
    
    def _clean_description(self, description: str, max_length: int = 500) -> str:
        """Clean and truncate description."""
        if not description:
            return "No description available."
        description = " ".join(description.split())
        if len(description) > max_length:
            description = description[:max_length - 3] + "..."
        return description
    
    def _get_fallback_info(self, symbol: str) -> Dict[str, Any]:
        """Get fallback company information."""
        fallbacks = {
            "2222.SR": {
                "companyName": "أرامكو السعودية",
                "sector": "الطاقة",
                "industry": "النفط والغاز",
                "marketCap": 7500.0,
                "employees": 70000,
                "country": "السعودية",
                "website": "https://www.aramco.com",
                "description": "شركة الزيت العربية السعودية (أرامكو) هي شركة نفط وغاز طبيعي مملوكة للدولة السعودية."
            },
            "1120.SR": {
                "companyName": "مصرف الراجحي",
                "sector": "المالية",
                "industry": "الخدمات المصرفية",
                "marketCap": 320.0,
                "employees": 12000,
                "country": "السعودية",
                "website": "https://www.alrajhibank.com.sa",
                "description": "مصرف الراجحي هو أحد أكبر البنوك الإسلامية في العالم."
            },
            "7010.SR": {
                "companyName": "شركة الاتصالات السعودية (STC)",
                "sector": "الاتصالات",
                "industry": "الاتصالات وتقنية المعلومات",
                "marketCap": 180.0,
                "employees": 22000,
                "country": "السعودية",
                "website": "https://www.stc.com.sa",
                "description": "شركة الاتصالات السعودية هي أكبر مشغل للاتصالات في الشرق الأوسط."
            },
            "AAPL": {
                "companyName": "Apple Inc.",
                "sector": "التكنولوجيا",
                "industry": "الأجهزة الإلكترونية والبرمجيات",
                "marketCap": 2800.0,
                "employees": 164000,
                "country": "الولايات المتحدة",
                "website": "https://www.apple.com",
                "description": "Apple Inc. is an American multinational technology company."
            },
            "TSLA": {
                "companyName": "Tesla Inc.",
                "sector": "السيارات",
                "industry": "السيارات الكهربائية",
                "marketCap": 800.0,
                "employees": 140000,
                "country": "الولايات المتحدة",
                "website": "https://www.tesla.com",
                "description": "Tesla Inc. is an American electric vehicle and clean energy company."
            },
            "MSFT": {
                "companyName": "Microsoft Corporation",
                "sector": "التكنولوجيا",
                "industry": "البرمجيات والخدمات السحابية",
                "marketCap": 2500.0,
                "employees": 221000,
                "country": "الولايات المتحدة",
                "website": "https://www.microsoft.com",
                "description": "Microsoft Corporation is an American multinational technology company."
            }
        }
        
        if symbol in fallbacks:
            return fallbacks[symbol]
        
        return {
            "companyName": symbol,
            "sector": "غير متوفر",
            "industry": "غير متوفر",
            "marketCap": 0.0,
            "employees": 0,
            "country": "غير متوفر",
            "website": f"https://finance.yahoo.com/quote/{symbol}",
            "description": f"لا توجد معلومات متاحة للرمز {symbol}."
        }
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol exists."""
        try:
            ticker = self._request(symbol)
            if ticker is None:
                return False
            info = ticker.fast_info
            return len(info) > 0
        except Exception:
            return False
    
    @cached(ttl=20)
    def get_price(self, symbol: str) -> Dict[str, Any]:
        """Get current stock price."""
        ticker = self._request(symbol)
        if ticker is None:
            return {"symbol": symbol, "error": "Failed to get ticker"}
        
        try:
            info = ticker.fast_info
            return {
                "symbol": symbol,
                "price": info.get("lastPrice", 0.0),
                "open": info.get("open", 0.0),
                "high": info.get("dayHigh", 0.0),
                "low": info.get("dayLow", 0.0),
                "volume": info.get("lastVolume", 0),
                "market_cap": info.get("marketCap", 0.0),
                "currency": info.get("currency", "USD"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.exception(f"Error getting price for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    @cached(ttl=300)
    def get_history(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        """Get historical data."""
        ticker = self._request(symbol)
        if ticker is None:
            return pd.DataFrame()
        
        try:
            df = ticker.history(period=period, interval=interval, auto_adjust=True)
            if df.empty:
                return pd.DataFrame()
            
            df.reset_index(inplace=True)
            df['Date'] = pd.to_datetime(df['Date'])
            return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            logger.exception(f"Error getting history for {symbol}: {e}")
            return pd.DataFrame()
    
    @cached(ttl=3600)
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive company information."""
        ticker = self._request(symbol)
        
        if ticker is not None:
            try:
                info = ticker.info
                if info:
                    return {
                        "companyName": info.get("longName") or info.get("shortName") or symbol,
                        "sector": info.get("sector") or "غير متوفر",
                        "industry": info.get("industry") or "غير متوفر",
                        "marketCap": self._format_market_cap(info.get("marketCap")),
                        "employees": info.get("fullTimeEmployees") or info.get("employees") or 0,
                        "country": info.get("country") or info.get("state") or "غير متوفر",
                        "website": info.get("website") or f"https://finance.yahoo.com/quote/{symbol}",
                        "description": self._clean_description(
                            info.get("longBusinessSummary") or "No description available."
                        ),
                        "symbol": symbol
                    }
            except Exception as e:
                logger.warning(f"Yahoo API failed for {symbol}, using fallback: {e}")
        
        fallback = self._get_fallback_info(symbol)
        fallback["symbol"] = symbol
        return fallback
    
    def get_dashboard_data(self, symbol: str) -> Dict[str, Any]:
        """Get complete dashboard data."""
        company = self.get_company_info(symbol)
        price = self.get_price(symbol)
        history = self.get_history(symbol, period="1mo")
        
        return {
            "symbol": symbol,
            "company": company,
            "price": price,
            "history": history.to_dict('records') if not history.empty else [],
            "dividends": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def get_portfolio_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get data for multiple symbols."""
        results = []
        for symbol in symbols:
            company = self.get_company_info(symbol)
            price = self.get_price(symbol)
            results.append({
                "symbol": symbol,
                "companyName": company.get("companyName", symbol),
                "sector": company.get("sector", "غير متوفر"),
                "industry": company.get("industry", "غير متوفر"),
                "marketCap": company.get("marketCap", 0.0),
                "employees": company.get("employees", 0),
                "country": company.get("country", "غير متوفر"),
                "website": company.get("website", ""),
                "description": company.get("description", ""),
                "currentPrice": price.get("price", 0.0),
                "currency": price.get("currency", "USD"),
                "volume": price.get("volume", 0),
            })
        return results


# =====================================================
# Convenience Functions
# =====================================================

_api_instance = None

def get_api():
    """Get or create API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = YahooAPI()
    return _api_instance

def get_company_info(symbol: str) -> Dict[str, Any]:
    """Convenience function to get company info."""
    return get_api().get_company_info(symbol)

def get_price(symbol: str) -> Dict[str, Any]:
    """Convenience function to get price."""
    return get_api().get_price(symbol)

def get_history(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Convenience function to get history."""
    return get_api().get_history(symbol, period, interval)

def get_dashboard_data(symbol: str) -> Dict[str, Any]:
    """Convenience function to get dashboard data."""
    return get_api().get_dashboard_data(symbol)

def get_portfolio_data(symbols: List[str]) -> List[Dict[str, Any]]:
    """Convenience function to get portfolio data."""
    return get_api().get_portfolio_data(symbols)

def validate_symbol(symbol: str) -> bool:
    """Convenience function to validate symbol."""
    return get_api().validate_symbol(symbol)


__all__ = [
    'YahooAPI',
    'get_company_info',
    'get_price',
    'get_history',
    'get_dashboard_data',
    'get_portfolio_data',
    'validate_symbol'
]
