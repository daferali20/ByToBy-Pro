```python
"""
ByToBy Pro
Yahoo Finance API Layer
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests
import yfinance as yf

from utils.cache import cache, cached
from utils.logger import get_logger, timer


logger = get_logger("YahooAPI")


class YahooAPI:
    """
    Professional Yahoo Finance API Wrapper
    """

    def __init__(
        self,
        timeout: int = 15,
        retries: int = 3,
    ):

        self.timeout = timeout
        self.retries = retries

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent":
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept":
                    "application/json,text/plain,*/*",
            }
        )

        logger.info("Yahoo API Initialized")

    # =====================================================
    # Internal Helpers
    # =====================================================

    def _request(self, symbol: str) -> yf.Ticker | None:
        """
        Return Yahoo Ticker object.
        """

        try:

            ticker = yf.Ticker(symbol)

            return ticker

        except Exception as e:

            logger.exception(e)

            return None

    def _retry(self, func, *args, **kwargs):

        last_error = None

        for attempt in range(self.retries):

            try:

                return func(*args, **kwargs)

            except Exception as e:

                last_error = e

                logger.warning(
                    f"Retry {attempt+1}/{self.retries}"
                )

                time.sleep(1)

        logger.exception(last_error)

        return None

    # =====================================================
    # Validation
    # =====================================================

    def validate_symbol(self, symbol: str) -> bool:

        try:

            ticker = self._request(symbol)

            if ticker is None:

                return False

            info = ticker.fast_info

            return len(info) > 0

        except Exception:

            return False

    # =====================================================
    # Current Price
    # =====================================================

    @timer
    @cached(ttl=20)

    def get_price(self, symbol: str) -> dict[str, Any]:

        """
        Current stock price.
        """

        ticker = self._request(symbol)

        if ticker is None:

            return {}

        try:

            info = ticker.fast_info

            return {

                "symbol": symbol,

                "price":
                    info.get("lastPrice"),

                "open":
                    info.get("open"),

                "high":
                    info.get("dayHigh"),

                "low":
                    info.get("dayLow"),

                "volume":
                    info.get("lastVolume"),

                "market_cap":
                    info.get("marketCap"),

                "currency":
                    info.get("currency"),

            }

        except Exception as e:

            logger.exception(e)

            return {}

    # =====================================================
    # Historical Data
    # =====================================================

    @timer
    @cached(ttl=300)
    def get_history(
        self,
        symbol: str,
        period: str = "6mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        جلب البيانات التاريخية للسهم.

        Parameters
        ----------
        symbol : رمز السهم
        period : الفترة (1d,5d,1mo,3mo,6mo,1y,2y,5y,max)
        interval : الفاصل الزمني (1m,5m,15m,1h,1d,1wk)

        Returns
        -------
        DataFrame
        """

        ticker = self._request(symbol)

        if ticker is None:
            return pd.DataFrame()

        try:

            df = ticker.history(
                period=period,
                interval=interval,
                auto_adjust=True
            )

            if df.empty:
                logger.warning(f"No history found for {symbol}")
                return pd.DataFrame()

            df.reset_index(inplace=True)

            logger.info(
                f"{symbol} history loaded ({len(df)} rows)"
            )

            return df

        except Exception as e:

            logger.exception(e)

            return pd.DataFrame()
try:
            df = ticker.history(
                period=period,
                interval=interval,
                auto_adjust=True
            )
            if df.empty:
                logger.warning(f"No history found for {symbol}")
                return pd.DataFrame()
            df.reset_index(inplace=True)
            logger.info(f"{symbol} history loaded ({len(df)} rows)")
            return df
        except Exception as e:
            logger.exception(e)
            return pd.DataFrame()

    # =====================================================
    # NEW: Company Information (Dashboard & Portfolio)
    # =====================================================

    @timer
    @cached(ttl=3600)  # Cache for 1 hour
    def get_company_info(self, symbol: str) -> dict[str, Any]:
        """
        Get comprehensive company information for Dashboard and Portfolio pages.
        
        Parameters
        ----------
        symbol : Stock symbol (e.g., 'AAPL', 'TSLA', '2222.SR')
        
        Returns
        -------
        dict with:
            - companyName: str
            - sector: str
            - industry: str
            - marketCap: float (in billions)
            - employees: int
            - country: str
            - website: str
            - description: str
        """
        ticker = self._request(symbol)
        if ticker is None:
            logger.error(f"Failed to get ticker for {symbol}")
            return self._get_fallback_info(symbol)

        try:
            # Get full info from Yahoo Finance
            info = ticker.info
            
            if not info:
                logger.warning(f"No info found for {symbol}")
                return self._get_fallback_info(symbol)

            # Extract and format company info
            company_info = {
                "companyName": info.get("longName") or info.get("shortName") or symbol,
                "sector": info.get("sector") or "N/A",
                "industry": info.get("industry") or "N/A",
                "marketCap": self._format_market_cap(info.get("marketCap")),
                "employees": info.get("fullTimeEmployees") or info.get("employees") or 0,
                "country": info.get("country") or info.get("state") or "N/A",
                "website": info.get("website") or f"https://finance.yahoo.com/quote/{symbol}",
                "description": self._clean_description(info.get("longBusinessSummary") or "No description available.")
            }
            
            logger.info(f"Company info retrieved for {symbol}")
            return company_info

        except Exception as e:
            logger.exception(f"Error fetching company info for {symbol}: {e}")
            return self._get_fallback_info(symbol)

    def _format_market_cap(self, market_cap: Optional[int]) -> float:
        """
        Convert market cap to billions.
        
        Parameters
        ----------
        market_cap : Market cap in raw currency units
        
        Returns
        -------
        float : Market cap in billions (B)
        """
        if not market_cap:
            return 0.0
        
        # Convert to billions
        return round(market_cap / 1_000_000_000, 2)

    def _clean_description(self, description: str) -> str:
        """
        Clean and truncate company description if needed.
        """
        if not description:
            return "No description available."
        
        # Remove extra whitespace
        description = " ".join(description.split())
        
        # Truncate if too long (max 500 chars for dashboard)
        if len(description) > 500:
            description = description[:497] + "..."
        
        return description

    def _get_fallback_info(self, symbol: str) -> dict[str, Any]:
        """
        Provide fallback information when API fails.
        """
        # Common Saudi companies fallback
        saudi_companies = {
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
            }
        }
        
        # US companies fallback
        us_companies = {
            "AAPL": {
                "companyName": "Apple Inc.",
                "sector": "التكنولوجيا",
                "industry": "الأجهزة الإلكترونية والبرمجيات",
                "marketCap": 2800.0,
                "employees": 164000,
                "country": "الولايات المتحدة",
                "website": "https://www.apple.com",
                "description": "شركة Apple هي شركة تكنولوجيا أمريكية متعددة الجنسيات."
            },
            "MSFT": {
                "companyName": "Microsoft Corporation",
                "sector": "التكنولوجيا",
                "industry": "البرمجيات",
                "marketCap": 2500.0,
                "employees": 221000,
                "country": "الولايات المتحدة",
                "website": "https://www.microsoft.com",
                "description": "شركة Microsoft هي شركة تكنولوجيا أمريكية متعددة الجنسيات."
            },
            "TSLA": {
                "companyName": "Tesla Inc.",
                "sector": "السيارات",
                "industry": "السيارات الكهربائية",
                "marketCap": 800.0,
                "employees": 140000,
                "country": "الولايات المتحدة",
                "website": "https://www.tesla.com",
                "description": "شركة Tesla هي شركة أمريكية متخصصة في السيارات الكهربائية."
            }
        }
        
        # Merge fallbacks
        all_fallbacks = {**saudi_companies, **us_companies}
        
        # Return fallback if exists, else generic
        if symbol in all_fallbacks:
            return all_fallbacks[symbol]
        
        return {
            "companyName": symbol,
            "sector": "N/A",
            "industry": "N/A",
            "marketCap": 0.0,
            "employees": 0,
            "country": "N/A",
            "website": f"https://finance.yahoo.com/quote/{symbol}",
            "description": f"No information available for {symbol}."
        }


# =====================================================
# Convenience Function (for easy import)
# =====================================================

def get_company_info(symbol: str) -> dict[str, Any]:
    """
    Convenience function to get company information.
    
    Usage:
        info = get_company_info("AAPL")
        print(info["companyName"])  # Apple Inc.
    """
    api = YahooAPI()
    return api.get_company_info(symbol)
       
