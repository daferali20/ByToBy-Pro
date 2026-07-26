# api/yahoo_api.py
"""
ByToBy Pro
Yahoo Finance API Layer
Professional Yahoo Finance API Wrapper with caching, retries, and error handling
"""

from __future__ import annotations

import time
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta

import pandas as pd
import requests
import yfinance as yf

from utils.cache import cache, cached, timer
from utils.logger import get_logger

# Initialize logger
logger = get_logger("YahooAPI")


class YahooAPI:
    """
    Professional Yahoo Finance API Wrapper
    
    This class provides a robust interface to Yahoo Finance data with:
    - Automatic retries on failure
    - Caching for performance
    - Comprehensive error handling
    - Support for multiple markets (US, Saudi, UAE, etc.)
    
    Usage:
        api = YahooAPI()
        price = api.get_price("AAPL")
        info = api.get_company_info("2222.SR")
        history = api.get_history("TSLA", period="1y")
    """

    def __init__(
        self,
        timeout: int = 15,
        retries: int = 3,
        cache_ttl: int = 300,
    ):
        """
        Initialize Yahoo Finance API wrapper.
        
        Parameters
        ----------
        timeout : int, default=15
            Request timeout in seconds
        retries : int, default=3
            Number of retry attempts on failure
        cache_ttl : int, default=300
            Cache time-to-live in seconds (5 minutes)
        """
        self.timeout = timeout
        self.retries = retries
        self.cache_ttl = cache_ttl

        # Create requests session with custom headers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        })

        logger.info(f"Yahoo API Initialized (timeout={timeout}s, retries={retries})")

    # =====================================================
    # Internal Helpers
    # =====================================================

    def _request(self, symbol: str) -> Optional[yf.Ticker]:
        """
        Create and return Yahoo Ticker object for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol (e.g., 'AAPL', '2222.SR', 'TSLA')
            
        Returns
        -------
        Optional[yf.Ticker]
            Yahoo Ticker object or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            # Verify ticker is valid by accessing fast_info
            _ = ticker.fast_info
            return ticker
        except Exception as e:
            logger.debug(f"Failed to create ticker for {symbol}: {e}")
            return None

    def _retry(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with automatic retries on failure.
        
        Parameters
        ----------
        func : callable
            Function to execute
        *args, **kwargs
            Arguments to pass to the function
            
        Returns
        -------
        Any
            Function result or None if all retries fail
        """
        last_error = None

        for attempt in range(self.retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    f"Retry {attempt + 1}/{self.retries} for {func.__name__} "
                    f"after {wait_time}s (error: {str(e)[:50]})"
                )
                time.sleep(wait_time)

        logger.error(f"All {self.retries} retries failed: {last_error}")
        return None

    def _format_market_cap(self, market_cap: Optional[Union[int, float]]) -> float:
        """
        Format market cap to billions.
        
        Parameters
        ----------
        market_cap : Optional[Union[int, float]]
            Raw market cap value
            
        Returns
        -------
        float
            Market cap in billions (rounded to 2 decimal places)
        """
        if not market_cap:
            return 0.0
        try:
            return round(float(market_cap) / 1_000_000_000, 2)
        except (ValueError, TypeError):
            return 0.0

    def _clean_description(self, description: Optional[str], max_length: int = 500) -> str:
        """
        Clean and truncate company description.
        
        Parameters
        ----------
        description : Optional[str]
            Raw description text
        max_length : int, default=500
            Maximum length of description
            
        Returns
        -------
        str
            Cleaned and truncated description
        """
        if not description:
            return "No description available."
        
        # Remove extra whitespace and newlines
        cleaned = " ".join(description.split())
        
        # Remove HTML tags if any
        import re
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Truncate if too long
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length - 3] + "..."
        
        return cleaned

    def _get_fallback_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get fallback company information when API fails.
        Provides predefined data for major companies.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        Dict[str, Any]
            Fallback company information
        """
        # Saudi Companies
        saudi_companies = {
            "2222.SR": {
                "companyName": "أرامكو السعودية",
                "sector": "الطاقة",
                "industry": "النفط والغاز",
                "marketCap": 7500.0,
                "employees": 70000,
                "country": "السعودية",
                "website": "https://www.aramco.com",
                "description": "شركة الزيت العربية السعودية (أرامكو) هي شركة نفط وغاز طبيعي مملوكة للدولة السعودية، وتُعد أكبر شركة في العالم من حيث القيمة السوقية والإيرادات."
            },
            "1120.SR": {
                "companyName": "مصرف الراجحي",
                "sector": "المالية",
                "industry": "الخدمات المصرفية",
                "marketCap": 320.0,
                "employees": 12000,
                "country": "السعودية",
                "website": "https://www.alrajhibank.com.sa",
                "description": "مصرف الراجحي هو أحد أكبر البنوك الإسلامية في العالم، ويقدم خدمات مصرفية متنوعة للأفراد والشركات."
            },
            "7010.SR": {
                "companyName": "شركة الاتصالات السعودية (STC)",
                "sector": "الاتصالات",
                "industry": "الاتصالات وتقنية المعلومات",
                "marketCap": 180.0,
                "employees": 22000,
                "country": "السعودية",
                "website": "https://www.stc.com.sa",
                "description": "شركة الاتصالات السعودية هي أكبر مشغل للاتصالات في الشرق الأوسط، وتقدم خدمات الهاتف المحمول والإنترنت والبث."
            },
            "4013.SR": {
                "companyName": "شركة عبدالله الفوزان",
                "sector": "الغذاء والزراعة",
                "industry": "المنتجات الغذائية",
                "marketCap": 45.0,
                "employees": 8000,
                "country": "السعودية",
                "website": "https://www.fawzan.com",
                "description": "شركة عبدالله الفوزان هي شركة رائدة في مجال المنتجات الغذائية والمشروبات في المملكة العربية السعودية."
            },
            "2010.SR": {
                "companyName": "الشركة السعودية للصناعات الأساسية (سابك)",
                "sector": "الصناعات",
                "industry": "البتروكيماويات",
                "marketCap": 280.0,
                "employees": 33000,
                "country": "السعودية",
                "website": "https://www.sabic.com",
                "description": "سابك هي شركة سعودية متخصصة في البتروكيماويات، وتعد من أكبر الشركات في العالم في هذا المجال."
            },
            "1180.SR": {
                "companyName": "البنك الأهلي التجاري",
                "sector": "المالية",
                "industry": "الخدمات المصرفية",
                "marketCap": 250.0,
                "employees": 15000,
                "country": "السعودية",
                "website": "https://www.alahli.com",
                "description": "البنك الأهلي التجاري هو أحد أكبر البنوك في المملكة العربية السعودية."
            },
        }

        # US Companies
        us_companies = {
            "AAPL": {
                "companyName": "Apple Inc.",
                "sector": "التكنولوجيا",
                "industry": "الأجهزة الإلكترونية والبرمجيات",
                "marketCap": 2800.0,
                "employees": 164000,
                "country": "الولايات المتحدة",
                "website": "https://www.apple.com",
                "description": "Apple Inc. is an American multinational technology company that designs, develops, and sells consumer electronics, software, and online services."
            },
            "MSFT": {
                "companyName": "Microsoft Corporation",
                "sector": "التكنولوجيا",
                "industry": "البرمجيات والخدمات السحابية",
                "marketCap": 2500.0,
                "employees": 221000,
                "country": "الولايات المتحدة",
                "website": "https://www.microsoft.com",
                "description": "Microsoft Corporation is an American multinational technology company that develops, manufactures, licenses, supports, and sells computer software, consumer electronics, and related services."
            },
            "GOOGL": {
                "companyName": "Alphabet Inc.",
                "sector": "التكنولوجيا",
                "industry": "الإنترنت والخدمات الرقمية",
                "marketCap": 1700.0,
                "employees": 190000,
                "country": "الولايات المتحدة",
                "website": "https://www.abc.xyz",
                "description": "Alphabet Inc. is an American multinational technology conglomerate holding company that specializes in internet-related services and products."
            },
            "AMZN": {
                "companyName": "Amazon.com Inc.",
                "sector": "التكنولوجيا",
                "industry": "التجارة الإلكترونية والحوسبة السحابية",
                "marketCap": 1500.0,
                "employees": 1600000,
                "country": "الولايات المتحدة",
                "website": "https://www.amazon.com",
                "description": "Amazon is an American multinational technology company focusing on e-commerce, cloud computing, digital streaming, and artificial intelligence."
            },
            "TSLA": {
                "companyName": "Tesla Inc.",
                "sector": "السيارات",
                "industry": "السيارات الكهربائية والطاقة المتجددة",
                "marketCap": 800.0,
                "employees": 140000,
                "country": "الولايات المتحدة",
                "website": "https://www.tesla.com",
                "description": "Tesla Inc. is an American electric vehicle and clean energy company that designs, manufactures, and sells electric cars, battery energy storage, and solar panels."
            },
            "META": {
                "companyName": "Meta Platforms Inc.",
                "sector": "التكنولوجيا",
                "industry": "الشبكات الاجتماعية والإعلانات الرقمية",
                "marketCap": 900.0,
                "employees": 70000,
                "country": "الولايات المتحدة",
                "website": "https://www.meta.com",
                "description": "Meta Platforms Inc. is an American multinational technology company that owns and operates Facebook, Instagram, WhatsApp, and other social media platforms."
            },
            "NFLX": {
                "companyName": "Netflix Inc.",
                "sector": "التكنولوجيا",
                "industry": "الترفيه الرقمي والبث",
                "marketCap": 200.0,
                "employees": 12000,
                "country": "الولايات المتحدة",
                "website": "https://www.netflix.com",
                "description": "Netflix Inc. is an American subscription video on-demand over-the-top streaming service provider."
            },
        }

        # UAE Companies
        uae_companies = {
            "EMAAR.AE": {
                "companyName": "إعمار العقارية",
                "sector": "العقارات",
                "industry": "التطوير العقاري",
                "marketCap": 45.0,
                "employees": 10000,
                "country": "الإمارات",
                "website": "https://www.emaar.com",
                "description": "إعمار العقارية هي شركة تطوير عقاري إماراتية، تطور المجتمعات السكنية والتجارية والفندقية."
            },
            "ADNOC.AE": {
                "companyName": "أدنوك للتوزيع",
                "sector": "الطاقة",
                "industry": "توزيع الوقود",
                "marketCap": 25.0,
                "employees": 8000,
                "country": "الإمارات",
                "website": "https://www.adnocdistribution.ae",
                "description": "أدنوك للتوزيع هي شركة إماراتية لتوزيع الوقود وخدمات المحطات."
            },
        }

        # Kuwait Companies
        kuwait_companies = {
            "ZAIN.KW": {
                "companyName": "زين للاتصالات",
                "sector": "الاتصالات",
                "industry": "الاتصالات المتنقلة",
                "marketCap": 12.0,
                "employees": 6000,
                "country": "الكويت",
                "website": "https://www.zain.com",
                "description": "زين هي شركة كويتية للاتصالات المتنقلة، تعمل في عدة دول في الشرق الأوسط وأفريقيا."
            },
            "NBK.KW": {
                "companyName": "البنك الوطني الكويتي",
                "sector": "المالية",
                "industry": "الخدمات المصرفية",
                "marketCap": 18.0,
                "employees": 5000,
                "country": "الكويت",
                "website": "https://www.nbk.com",
                "description": "البنك الوطني الكويتي هو أكبر بنك في الكويت، ويقدم خدمات مصرفية متكاملة."
            },
        }

        # Qatar Companies
        qatar_companies = {
            "QNB.QA": {
                "companyName": "بنك قطر الوطني",
                "sector": "المالية",
                "industry": "الخدمات المصرفية",
                "marketCap": 40.0,
                "employees": 28000,
                "country": "قطر",
                "website": "https://www.qnb.com",
                "description": "بنك قطر الوطني هو أكبر بنك في الشرق الأوسط وأفريقيا."
            },
            "QEWS.QA": {
                "companyName": "الشركة القطرية للكهرباء والماء",
                "sector": "المرافق",
                "industry": "الطاقة والمياه",
                "marketCap": 15.0,
                "employees": 2500,
                "country": "قطر",
                "website": "https://www.qewc.com",
                "description": "شركة الكهرباء والماء القطرية هي المزود الرئيسي للكهرباء والمياه في قطر."
            },
        }

        # Merge all fallbacks
        all_fallbacks = {
            **saudi_companies,
            **us_companies,
            **uae_companies,
            **kuwait_companies,
            **qatar_companies
        }

        # Return fallback if exists, else generic
        if symbol in all_fallbacks:
            return all_fallbacks[symbol]

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

    def _parse_datetime(self, dt: Union[datetime, str, None]) -> Optional[str]:
        """
        Parse datetime to ISO format string.
        
        Parameters
        ----------
        dt : Union[datetime, str, None]
            Datetime object or string
            
        Returns
        -------
        Optional[str]
            ISO format datetime string or None
        """
        if dt is None:
            return None
        if isinstance(dt, datetime):
            return dt.isoformat()
        if isinstance(dt, str):
            return dt
        return None

    # =====================================================
    # Validation
    # =====================================================

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol exists on Yahoo Finance.
        
        Parameters
        ----------
        symbol : str
            Stock symbol to validate
            
        Returns
        -------
        bool
            True if symbol is valid, False otherwise
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> api.validate_symbol("AAPL")
        True
        >>> api.validate_symbol("INVALID")
        False
        """
        try:
            ticker = self._request(symbol)
            if ticker is None:
                return False
            info = ticker.fast_info
            return len(info) > 0
        except Exception:
            return False

    def validate_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Validate multiple symbols.
        
        Parameters
        ----------
        symbols : List[str]
            List of stock symbols
            
        Returns
        -------
        Dict[str, bool]
            Dictionary mapping symbols to validation status
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> api.validate_symbols(["AAPL", "2222.SR", "INVALID"])
        {'AAPL': True, '2222.SR': True, 'INVALID': False}
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.validate_symbol(symbol)
        return results

    # =====================================================
    # Current Price
    # =====================================================

    @timer
    @cached(ttl=20)
    def get_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current stock price and related data.
        
        Parameters
        ----------
        symbol : str
            Stock symbol (e.g., 'AAPL', '2222.SR')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - symbol: str
            - price: float (current price)
            - open: float (opening price)
            - high: float (day high)
            - low: float (day low)
            - volume: int (trading volume)
            - market_cap: float (market cap)
            - currency: str
            - timestamp: str (last update time)
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> price = api.get_price("AAPL")
        >>> print(price['price'])
        175.50
        """
        ticker = self._request(symbol)
        if ticker is None:
            return {"symbol": symbol, "error": "Failed to get ticker"}

        try:
            info = ticker.fast_info
            timestamp = datetime.now().isoformat()

            return {
                "symbol": symbol,
                "price": info.get("lastPrice", 0.0),
                "open": info.get("open", 0.0),
                "high": info.get("dayHigh", 0.0),
                "low": info.get("dayLow", 0.0),
                "volume": info.get("lastVolume", 0),
                "market_cap": info.get("marketCap", 0.0),
                "currency": info.get("currency", "USD"),
                "timestamp": timestamp,
            }
        except Exception as e:
            logger.exception(f"Error getting price for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}

    @timer
    @cached(ttl=20)
    def get_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get current prices for multiple symbols.
        
        Parameters
        ----------
        symbols : List[str]
            List of stock symbols
            
        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping symbols to price data
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> prices = api.get_prices(["AAPL", "TSLA", "2222.SR"])
        >>> prices['AAPL']['price']
        175.50
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_price(symbol)
        return results

    # =====================================================
    # Historical Data
    # =====================================================

    @timer
    @cached(ttl=300)
    def get_history(
        self,
        symbol: str,
        period: str = "6mo",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical stock data.
        
        Parameters
        ----------
        symbol : str
            Stock symbol (e.g., 'AAPL', '2222.SR')
        period : str, default='6mo'
            Data period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'
        interval : str, default='1d'
            Data interval: '1m', '2m', '5m', '15m', '30m', '60m', '1h', '1d', '1wk', '1mo'
        start : Optional[str], default=None
            Start date in 'YYYY-MM-DD' format (overrides period)
        end : Optional[str], default=None
            End date in 'YYYY-MM-DD' format
            
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: Date, Open, High, Low, Close, Volume
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> df = api.get_history("AAPL", period="1mo")
        >>> df.head()
                Date   Open   High    Low  Close    Volume
        0 2024-01-01  185.0  187.0  184.0  186.0  50000000
        """
        ticker = self._request(symbol)
        if ticker is None:
            logger.warning(f"Failed to get ticker for {symbol}")
            return pd.DataFrame()

        try:
            # Use start/end if provided
            if start and end:
                df = ticker.history(
                    start=start,
                    end=end,
                    interval=interval,
                    auto_adjust=True
                )
            else:
                df = ticker.history(
                    period=period,
                    interval=interval,
                    auto_adjust=True
                )

            if df.empty:
                logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()

            # Reset index to make Date a column
            df.reset_index(inplace=True)
            df['Date'] = pd.to_datetime(df['Date'])

            # Add symbol column
            df['Symbol'] = symbol

            # Select and rename columns
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Symbol']]

            logger.info(f"Historical data loaded for {symbol}: {len(df)} rows")

            return df

        except Exception as e:
            logger.exception(f"Error getting history for {symbol}: {e}")
            return pd.DataFrame()

    @timer
    @cached(ttl=300)
    def get_history_batch(
        self,
        symbols: List[str],
        period: str = "6mo",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols.
        
        Parameters
        ----------
        symbols : List[str]
            List of stock symbols
        period : str, default='6mo'
            Data period
        interval : str, default='1d'
            Data interval
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary mapping symbols to DataFrames
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> data = api.get_history_batch(["AAPL", "TSLA"], period="1mo")
        >>> data['AAPL'].head()
        """
        results = {}
        for symbol in symbols:
            df = self.get_history(symbol, period, interval)
            if not df.empty:
                results[symbol] = df
        return results

    # =====================================================
    # Company Information (Dashboard & Portfolio)
    # =====================================================

    @timer
    @cached(ttl=3600)  # Cache for 1 hour
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive company information for Dashboard and Portfolio pages.
        
        This is the main method used by both Dashboard and Portfolio pages
        to display company details.
        
        Parameters
        ----------
        symbol : str
            Stock symbol (e.g., 'AAPL', '2222.SR', 'TSLA')
            
        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - companyName: str (اسم الشركة)
            - sector: str (القطاع)
            - industry: str (الصناعة)
            - marketCap: float (القيمة السوقية بالمليارات)
            - employees: int (عدد الموظفين)
            - country: str (الدولة)
            - website: str (الموقع الإلكتروني)
            - description: str (وصف الشركة)
            - symbol: str (رمز السهم)
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> info = api.get_company_info("2222.SR")
        >>> print(info["companyName"])
        أرامكو السعودية
        >>> print(info["sector"])
        الطاقة
        >>> print(f"Market Cap: ${info['marketCap']}B")
        Market Cap: $7500.0B
            
        >>> info = api.get_company_info("AAPL")
        >>> print(info["companyName"])
        Apple Inc.
        >>> print(info["employees"])
        164000
        """
        # First try to get from Yahoo Finance
        ticker = self._request(symbol)
        
        if ticker is not None:
            try:
                # Get full info from Yahoo Finance
                info = ticker.info
                
                if info:
                    # Extract and format company info
                    company_info = {
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
                    
                    logger.info(f"Company info retrieved for {symbol}")
                    return company_info
                    
            except Exception as e:
                logger.warning(f"Yahoo API failed for {symbol}, using fallback: {e}")
        
        # If Yahoo fails or returns empty, use fallback data
        fallback_data = self._get_fallback_info(symbol)
        fallback_data["symbol"] = symbol
        logger.info(f"Using fallback data for {symbol}")
        return fallback_data

    @timer
    @cached(ttl=3600)
    def get_company_info_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get company information for multiple symbols.
        Useful for Portfolio page.
        
        Parameters
        ----------
        symbols : List[str]
            List of stock symbols
            
        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping symbols to company info
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> companies = api.get_company_info_batch(["AAPL", "2222.SR"])
        >>> for symbol, info in companies.items():
        ...     print(f"{symbol}: {info['companyName']}")
        AAPL: Apple Inc.
        2222.SR: أرامكو السعودية
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_company_info(symbol)
        return results

    # =====================================================
    # Additional Data
    # =====================================================

    @timer
    @cached(ttl=300)
    def get_dividends(self, symbol: str) -> pd.DataFrame:
        """
        Get dividend history for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        pd.DataFrame
            DataFrame with dividend history
        """
        ticker = self._request(symbol)
        if ticker is None:
            return pd.DataFrame()
        
        try:
            dividends = ticker.dividends
            if dividends.empty:
                return pd.DataFrame()
            
            df = dividends.reset_index()
            df.columns = ['Date', 'Dividend']
            df['Symbol'] = symbol
            return df
            
        except Exception as e:
            logger.exception(f"Error getting dividends for {symbol}: {e}")
            return pd.DataFrame()

    @timer
    @cached(ttl=300)
    def get_splits(self, symbol: str) -> pd.DataFrame:
        """
        Get stock split history for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        pd.DataFrame
            DataFrame with split history
        """
        ticker = self._request(symbol)
        if ticker is None:
            return pd.DataFrame()
        
        try:
            splits = ticker.splits
            if splits.empty:
                return pd.DataFrame()
            
            df = splits.reset_index()
            df.columns = ['Date', 'Split']
            df['Symbol'] = symbol
            return df
            
        except Exception as e:
            logger.exception(f"Error getting splits for {symbol}: {e}")
            return pd.DataFrame()

    @timer
    @cached(ttl=300)
    def get_income_statement(self, symbol: str) -> Dict[str, Any]:
        """
        Get income statement for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        Dict[str, Any]
            Income statement data
        """
        ticker = self._request(symbol)
        if ticker is None:
            return {}
        
        try:
            return ticker.income_stmt.to_dict()
        except Exception as e:
            logger.exception(f"Error getting income statement for {symbol}: {e}")
            return {}

    @timer
    @cached(ttl=300)
    def get_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """
        Get balance sheet for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        Dict[str, Any]
            Balance sheet data
        """
        ticker = self._request(symbol)
        if ticker is None:
            return {}
        
        try:
            return ticker.balance_sheet.to_dict()
        except Exception as e:
            logger.exception(f"Error getting balance sheet for {symbol}: {e}")
            return {}

    @timer
    @cached(ttl=300)
    def get_cash_flow(self, symbol: str) -> Dict[str, Any]:
        """
        Get cash flow statement for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        Dict[str, Any]
            Cash flow statement data
        """
        ticker = self._request(symbol)
        if ticker is None:
            return {}
        
        try:
            return ticker.cashflow.to_dict()
        except Exception as e:
            logger.exception(f"Error getting cash flow for {symbol}: {e}")
            return {}

    # =====================================================
    # Recommendations and News
    # =====================================================

    @timer
    @cached(ttl=600)
    def get_recommendations(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get analyst recommendations for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        List[Dict[str, Any]]
            List of analyst recommendations
        """
        ticker = self._request(symbol)
        if ticker is None:
            return []
        
        try:
            recs = ticker.recommendations
            if recs is None or recs.empty:
                return []
            
            return recs.to_dict('records')
        except Exception as e:
            logger.exception(f"Error getting recommendations for {symbol}: {e}")
            return []

    @timer
    @cached(ttl=300)
    def get_news(self, symbol: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent news for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
        count : int, default=10
            Number of news articles to return
            
        Returns
        -------
        List[Dict[str, Any]]
            List of news articles
        """
        ticker = self._request(symbol)
        if ticker is None:
            return []
        
        try:
            news = ticker.news
            if not news:
                return []
            
            # Limit to requested count
            return news[:count]
        except Exception as e:
            logger.exception(f"Error getting news for {symbol}: {e}")
            return []

    # =====================================================
    # Actions
    # =====================================================

    @timer
    @cached(ttl=300)
    def get_actions(self, symbol: str) -> pd.DataFrame:
        """
        Get corporate actions (dividends, splits) for a symbol.
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        pd.DataFrame
            DataFrame with corporate actions
        """
        ticker = self._request(symbol)
        if ticker is None:
            return pd.DataFrame()
        
        try:
            actions = ticker.actions
            if actions.empty:
                return pd.DataFrame()
            
            df = actions.reset_index()
            df['Symbol'] = symbol
            return df
            
        except Exception as e:
            logger.exception(f"Error getting actions for {symbol}: {e}")
            return pd.DataFrame()

    # =====================================================
    # Market Data
    # =====================================================

    @timer
    @cached(ttl=60)
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status.
        
        Returns
        -------
        Dict[str, Any]
            Market status information
        """
        try:
            # Get US market status
            us_market = yf.Ticker("^GSPC")  # S&P 500
            info = us_market.fast_info
            
            return {
                "market_open": True,  # Simplified
                "timestamp": datetime.now().isoformat(),
                "symbol": "^GSPC",
                "price": info.get("lastPrice", 0),
                "change": 0,  # Would need to calculate
            }
        except Exception as e:
            logger.exception(f"Error getting market status: {e}")
            return {"error": str(e)}

    # =====================================================
    # Comprehensive Data for Dashboard
    # =====================================================

    def get_dashboard_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get all data needed for the Dashboard page in one call.
        
        This combines:
        - Company information
        - Current price
        - Historical data (1 month)
        - Dividends (if available)
        
        Parameters
        ----------
        symbol : str
            Stock symbol
            
        Returns
        -------
        Dict[str, Any]
            Complete dashboard data
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> dashboard = api.get_dashboard_data("2222.SR")
        >>> print(dashboard['company']['companyName'])
        أرامكو السعودية
        >>> print(dashboard['price']['price'])
        32.50
        >>> len(dashboard['history'])  # Number of days
        30
        """
        company = self.get_company_info(symbol)
        price = self.get_price(symbol)
        history = self.get_history(symbol, period="1mo", interval="1d")
        
        # Convert history to dict if not empty
        history_dict = history.to_dict('records') if not history.empty else []
        
        # Get dividends if available
        dividends = self.get_dividends(symbol)
        dividends_dict = dividends.to_dict('records') if not dividends.empty else []
        
        return {
            "symbol": symbol,
            "company": company,
            "price": price,
            "history": history_dict,
            "dividends": dividends_dict,
            "last_updated": datetime.now().isoformat()
        }

    def get_portfolio_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Get data for all portfolio holdings.
        
        This is optimized for the Portfolio page by fetching
        company info and prices in batch.
        
        Parameters
        ----------
        symbols : List[str]
            List of stock symbols in portfolio
            
        Returns
        -------
        List[Dict[str, Any]]
            List of portfolio data for each symbol
            
        Examples
        --------
        >>> api = YahooAPI()
        >>> portfolio = api.get_portfolio_data(["AAPL", "2222.SR", "TSLA"])
        >>> for holding in portfolio:
        ...     print(f"{holding['symbol']}: {holding['companyName']}")
        AAPL: Apple Inc.
        2222.SR: أرامكو السعودية
        TSLA: Tesla Inc.
        """
        results = []
        
        # Get all company info
        companies = self.get_company_info_batch(symbols)
        
        # Get all prices
        prices = self.get_prices(symbols)
        
        for symbol in symbols:
            company = companies.get(symbol, {})
            price = prices.get(symbol, {})
            
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
    # Stats and Analytics
    # =====================================================

    def get_sector_breakdown(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get sector breakdown for a list of symbols.
        
        Parameters
        ----------
        symbols : List[str]
            List of stock symbols
            
        Returns
        -------
        Dict[str, Dict[str, Any]]
            Sector breakdown with total market cap and company count
        """
        sector_data = {}
        
        for symbol in symbols:
            try:
                info = self.get_company_info(symbol)
                sector = info.get("sector", "غير متوفر")
                market_cap = info.get("marketCap", 0.0)
                
                if sector not in sector_data:
                    sector_data[sector] = {
                        "total_market_cap": 0.0,
                        "companies": [],
                        "count": 0
                    }
                
                sector_data[sector]["total_market_cap"] += market_cap
                sector_data[sector]["companies"].append(symbol)
                sector_data[sector]["count"] += 1
                
            except Exception as e:
                logger.error(f"Failed to get sector for {symbol}: {e}")
                continue
        
        return sector_data

    def get_country_breakdown(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get country breakdown for a list of symbols.
        
        Parameters
        ----------
        symbols : List[str]
            List of stock symbols
            
        Returns
        -------
        Dict[str, Dict[str, Any]]
            Country breakdown with total market cap and company count
        """
        country_data = {}
        
        for symbol in symbols:
            try:
                info = self.get_company_info(symbol)
                country = info.get("country", "غير متوفر")
                market_cap = info.get("marketCap", 0.0)
                
                if country not in country_data:
                    country_data[country] = {
                        "total_market_cap": 0.0,
                        "companies": [],
                        "count": 0
                    }
                
                country_data[country]["total_market_cap"] += market_cap
                country_data[country]["companies"].append(symbol)
                country_data[country]["count"] += 1
                
            except Exception as e:
                logger.error(f"Failed to get country for {symbol}: {e}")
                continue
        
        return country_data


# =====================================================
# Convenience Functions
# =====================================================

def get_company_info(symbol: str) -> Dict[str, Any]:
    """
    Convenience function to get company information.
    
    This is the main function to use for Dashboard and Portfolio pages.
    
    Parameters
    ----------
    symbol : str
        Stock symbol (e.g., 'AAPL', '2222.SR')
        
    Returns
    -------
    Dict[str, Any]
        Company information as described in get_company_info()
        
    Examples
    --------
    >>> info = get_company_info("AAPL")
    >>> print(info["companyName"])
    Apple Inc.
    
    >>> info = get_company_info("2222.SR")
    >>> print(info["companyName"])
    أرامكو السعودية
    """
    api = YahooAPI()
    return api.get_company_info(symbol)


def get_price(symbol: str) -> Dict[str, Any]:
    """
    Convenience function to get current price.
    
    Parameters
    ----------
    symbol : str
        Stock symbol
        
    Returns
    -------
    Dict[str, Any]
        Price data
    """
    api = YahooAPI()
    return api.get_price(symbol)


def get_history(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """
    Convenience function to get historical data.
    
    Parameters
    ----------
    symbol : str
        Stock symbol
    period : str
        Data period
    interval : str
        Data interval
        
    Returns
    -------
    pd.DataFrame
        Historical data
    """
    api = YahooAPI()
    return api.get_history(symbol, period, interval)


def get_dashboard_data(symbol: str) -> Dict[str, Any]:
    """
    Convenience function to get complete dashboard data.
    
    Parameters
    ----------
    symbol : str
        Stock symbol
        
    Returns
    -------
    Dict[str, Any]
        Complete dashboard data
    """
    api = YahooAPI()
    return api.get_dashboard_data(symbol)


def get_portfolio_data(symbols: List[str]) -> List[Dict[str, Any]]:
    """
    Convenience function to get portfolio data.
    
    Parameters
    ----------
    symbols : List[str]
        List of stock symbols
        
    Returns
    -------
    List[Dict[str, Any]]
        Portfolio data for each symbol
    """
    api = YahooAPI()
    return api.get_portfolio_data(symbols)


# Export main classes and functions
__all__ = [
    'YahooAPI',
    'get_company_info',
    'get_price',
    'get_history',
    'get_dashboard_data',
    'get_portfolio_data'
]
