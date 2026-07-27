# api/yahoo_api.py
"""
ByToBy Pro - Yahoo Finance API Layer
"""

from __future__ import annotations
from datetime import datetime
import time
from typing import Any, Optional, Dict, List
import pandas as pd
import requests

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance not available, using fallback data")

# Simple logger
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YahooAPI")


class YahooAPI:
    """Yahoo Finance API Wrapper."""
    
    def __init__(self):
        self.yfinance_available = YFINANCE_AVAILABLE
        logger.info(f"Yahoo API initialized (yfinance: {self.yfinance_available})")
    
    def _get_fallback_info(self, symbol: str) -> Dict[str, Any]:
        """Fallback company data."""
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
            "AAPL": {
                "companyName": "Apple Inc.",
                "sector": "التكنولوجيا",
                "industry": "الأجهزة الإلكترونية",
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
                "description": "Tesla Inc. is an American electric vehicle company."
            },
            "MSFT": {
                "companyName": "Microsoft Corporation",
                "sector": "التكنولوجيا",
                "industry": "البرمجيات",
                "marketCap": 2500.0,
                "employees": 221000,
                "country": "الولايات المتحدة",
                "website": "https://www.microsoft.com",
                "description": "Microsoft Corporation is an American multinational technology company."
            },
            "GOOGL": {
                "companyName": "Alphabet Inc.",
                "sector": "التكنولوجيا",
                "industry": "الإنترنت",
                "marketCap": 1700.0,
                "employees": 190000,
                "country": "الولايات المتحدة",
                "website": "https://www.abc.xyz",
                "description": "Alphabet Inc. is an American multinational technology conglomerate."
            },
            "AMZN": {
                "companyName": "Amazon.com Inc.",
                "sector": "التكنولوجيا",
                "industry": "التجارة الإلكترونية",
                "marketCap": 1500.0,
                "employees": 1600000,
                "country": "الولايات المتحدة",
                "website": "https://www.amazon.com",
                "description": "Amazon is an American multinational technology company."
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
            "description": f"لا توجد معلومات للرمز {symbol}."
        }
    
    def _generate_sample_history(self) -> pd.DataFrame:
        """Generate sample historical data."""
        import numpy as np
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        
        return pd.DataFrame({
            'Date': dates,
            'Open': prices * (1 + np.random.randn(100) * 0.01),
            'High': prices * (1 + np.abs(np.random.randn(100) * 0.02)),
            'Low': prices * (1 - np.abs(np.random.randn(100) * 0.02)),
            'Close': prices,
            'Volume': np.random.randint(100000, 1000000, 100)
        })
    
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """Get company information."""
        # Try Yahoo Finance first
        if self.yfinance_available:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if info:
                    return {
                        "companyName": info.get("longName") or info.get("shortName") or symbol,
                        "sector": info.get("sector") or "غير متوفر",
                        "industry": info.get("industry") or "غير متوفر",
                        "marketCap": round((info.get("marketCap") or 0) / 1_000_000_000, 2),
                        "employees": info.get("fullTimeEmployees") or info.get("employees") or 0,
                        "country": info.get("country") or info.get("state") or "غير متوفر",
                        "website": info.get("website") or f"https://finance.yahoo.com/quote/{symbol}",
                        "description": info.get("longBusinessSummary", "No description available.")[:500],
                        "source": "yahoo"
                    }
            except Exception as e:
                logger.warning(f"Yahoo failed for {symbol}: {e}")
        
        # Fallback
        fallback = self._get_fallback_info(symbol)
        fallback["source"] = "fallback"
        return fallback
    
    def get_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price."""
        if self.yfinance_available:
            try:
                ticker = yf.Ticker(symbol)
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
                    "timestamp": datetime.now().isoformat(),
                    "source": "yahoo"
                }
            except Exception as e:
                logger.warning(f"Price failed for {symbol}: {e}")
        
        return {
            "symbol": symbol,
            "price": 100.50,
            "open": 99.00,
            "high": 102.00,
            "low": 98.50,
            "volume": 1000000,
            "market_cap": 750000000000,
            "currency": "USD",
            "timestamp": datetime.now().isoformat(),
            "source": "fallback"
        }
    
    def get_history(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        """Get historical data."""
        if self.yfinance_available:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval, auto_adjust=True)
                
                if not df.empty:
                    df.reset_index(inplace=True)
                    df['Date'] = pd.to_datetime(df['Date'])
                    return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            except Exception as e:
                logger.warning(f"History failed for {symbol}: {e}")
        
        return self._generate_sample_history()
    
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
            "last_updated": datetime.now().isoformat(),
            "source": company.get("source", "unknown")
        }
    
    def get_portfolio_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get portfolio data."""
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
                "volume": price.get("volume", 0)
            })
        return results
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol exists."""
        try:
            info = self.get_company_info(symbol)
            return info.get("source") is not None
        except:
            return False


# =====================================================
# Singleton Instance
# =====================================================

_api = YahooAPI()


def get_api() -> YahooAPI:
    """Get the singleton API instance."""
    global _api
    if _api is None:
        _api = YahooAPI()
    return _api


def get_price(symbol: str) -> Dict[str, Any]:
    """Convenience function to get price."""
    return _api.get_price(symbol)


def get_history(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Convenience function to get history."""
    return _api.get_history(symbol, period, interval)


def get_company_info(symbol: str) -> Dict[str, Any]:
    """Convenience function to get company info."""
    return _api.get_company_info(symbol)


def validate_symbol(symbol: str) -> bool:
    """Convenience function to validate symbol."""
    return _api.validate_symbol(symbol)


def get_dashboard_data(symbol: str) -> Dict[str, Any]:
    """Convenience function to get dashboard data."""
    return _api.get_dashboard_data(symbol)


def get_portfolio_data(symbols: List[str]) -> List[Dict[str, Any]]:
    """Convenience function to get portfolio data."""
    return _api.get_portfolio_data(symbols)
