# api/market_api.py
"""
API احترافي لجلب البيانات المالية
Professional Financial Data API
"""

import time
import asyncio
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
import json

from ..config import config
from ..utils.logger import get_logger
from ..utils.cache import cache, cached

logger = get_logger("MarketAPI")

class MarketAPI:
    """
    واجهة برمجة تطبيقات متكاملة للأسواق المالية
    تدعم: Yahoo Finance, Finnhub, Polygon, Alpha Vantage
    """
    
    def __init__(self):
        self.logger = get_logger("MarketAPI")
        
        # إعدادات API
        self.api_keys = {
            'finnhub': config.FINNHUB_API_KEY,
            'polygon': config.POLYGON_API_KEY,
            'alpha_vantage': config.ALPHA_VANTAGE_KEY,
        }
        
        # إعدادات الطلبات مع Retry و Timeout
        self.session = self._create_session()
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        # المنفذون للعمليات المتزامنة
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        
        self.logger.info("MarketAPI initialized successfully")
    
    def _create_session(self) -> requests.Session:
        """إنشاء جلسة مع إعدادات Retry و Timeout"""
        session = requests.Session()
        
        # استراتيجية إعادة المحاولة
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,
            pool_maxsize=20
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # إعدادات إضافية
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ByToByBot/2.0)',
            'Accept': 'application/json'
        })
        
        return session
    
    # ======================== الأسعار اللحظية ========================
    
    @cached(ttl=10)  # تحديث كل 10 ثواني
    def get_price(self, symbol: str) -> Dict[str, Any]:
        """
        جلب السعر اللحظي للسهم
        
        Args:
            symbol: رمز السهم (مثل AAPL)
        
        Returns:
            dict: معلومات السعر الحالي
        """
        self.logger.debug(f"Fetching price for {symbol}")
        
        try:
            # محاولة من Yahoo Finance أولاً
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [])
                
                if result:
                    meta = result[0].get('meta', {})
                    price_data = {
                        'symbol': symbol,
                        'price': meta.get('regularMarketPrice', 0),
                        'change': meta.get('regularMarketChange', 0),
                        'change_percent': meta.get('regularMarketChangePercent', 0),
                        'volume': meta.get('regularMarketVolume', 0),
                        'market_cap': meta.get('marketCap', 0),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'yahoo'
                    }
                    self.logger.debug(f"Price fetched for {symbol}: ${price_data['price']}")
                    return price_data
            
            # إذا فشل Yahoo، حاول Finnhub
            return self._get_price_finnhub(symbol)
            
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return self._get_fallback_price(symbol)
    
    def _get_price_finnhub(self, symbol: str) -> Dict[str, Any]:
        """جلب السعر من Finnhub"""
        try:
            api_key = self.api_keys.get('finnhub')
            if not api_key:
                raise ValueError("Finnhub API key not found")
            
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'price': data.get('c', 0),  # السعر الحالي
                    'change': data.get('d', 0),  # التغير
                    'change_percent': data.get('dp', 0),  # نسبة التغير
                    'high': data.get('h', 0),  # أعلى سعر
                    'low': data.get('l', 0),  # أدنى سعر
                    'open': data.get('o', 0),  # سعر الافتتاح
                    'prev_close': data.get('pc', 0),  # الإغلاق السابق
                    'timestamp': datetime.now().isoformat(),
                    'source': 'finnhub'
                }
        except Exception as e:
            self.logger.error(f"Finnhub price error for {symbol}: {str(e)}")
        
        return {}
    
    def _get_fallback_price(self, symbol: str) -> Dict[str, Any]:
        """بيانات احتياطية في حالة فشل جميع المصادر"""
        self.logger.warning(f"Using fallback data for {symbol}")
        return {
            'symbol': symbol,
            'price': 0,
            'change': 0,
            'change_percent': 0,
            'timestamp': datetime.now().isoformat(),
            'source': 'fallback',
            'error': 'Unable to fetch live data'
        }
    
    # ======================== البيانات التاريخية ========================
    
    @cached(ttl=300)  # تخزين لمدة 5 دقائق
    def get_historical_data(
        self,
        symbol: str,
        interval: str = '1d',
        period: str = '1y'
    ) -> List[Dict[str, Any]]:
        """
        جلب البيانات التاريخية للسهم
        
        Args:
            symbol: رمز السهم
            interval: الفترة (1d, 1h, 15m, 5m, 1m)
            period: المدة (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            list: البيانات التاريخية
        """
        self.logger.info(f"Fetching historical data for {symbol} ({interval}, {period})")
        
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'interval': interval,
                'range': period,
                'includePrePost': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('chart', {}).get('result', [])
                
                if result:
                    timestamps = result[0].get('timestamp', [])
                    indicators = result[0].get('indicators', {})
                    quote = indicators.get('quote', [{}])[0]
                    
                    historical_data = []
                    for i, ts in enumerate(timestamps):
                        historical_data.append({
                            'date': datetime.fromtimestamp(ts).isoformat(),
                            'open': quote.get('open', [0])[i] if i < len(quote.get('open', [])) else 0,
                            'high': quote.get('high', [0])[i] if i < len(quote.get('high', [])) else 0,
                            'low': quote.get('low', [0])[i] if i < len(quote.get('low', [])) else 0,
                            'close': quote.get('close', [0])[i] if i < len(quote.get('close', [])) else 0,
                            'volume': quote.get('volume', [0])[i] if i < len(quote.get('volume', [])) else 0,
                        })
                    
                    self.logger.info(f"Retrieved {len(historical_data)} records for {symbol}")
                    return historical_data
            
            self.logger.warning(f"No historical data found for {symbol}")
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return []
    
    # ======================== معلومات الشركة ========================
    
    @cached(ttl=3600)  # تخزين لمدة ساعة
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        جلب معلومات الشركة
        
        Args:
            symbol: رمز السهم
        
        Returns:
            dict: معلومات الشركة
        """
        self.logger.info(f"Fetching company info for {symbol}")
        
        try:
            # محاولة من Yahoo Finance
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            params = {
                'modules': 'assetProfile,summaryDetail,price,defaultKeyStatistics,financialData'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('quoteSummary', {}).get('result', [])
                
                if result:
                    info = result[0]
                    price = info.get('price', {})
                    asset_profile = info.get('assetProfile', {})
                    summary = info.get('summaryDetail', {})
                    stats = info.get('defaultKeyStatistics', {})
                    financial = info.get('financialData', {})
                    
                    return {
                        'symbol': symbol,
                        'name': price.get('longName', ''),
                        'short_name': price.get('shortName', ''),
                        'sector': asset_profile.get('sector', ''),
                        'industry': asset_profile.get('industry', ''),
                        'country': asset_profile.get('country', ''),
                        'website': asset_profile.get('website', ''),
                        'description': asset_profile.get('longBusinessSummary', ''),
                        'employees': asset_profile.get('fullTimeEmployees', 0),
                        'market_cap': price.get('marketCap', {}).get('raw', 0),
                        'pe_ratio': summary.get('trailingPE', {}).get('raw', 0),
                        'eps': summary.get('trailingEps', {}).get('raw', 0),
                        'dividend_yield': summary.get('dividendYield', {}).get('raw', 0),
                        'target_price': financial.get('targetMeanPrice', {}).get('raw', 0),
                        'source': 'yahoo'
                    }
            
            # إذا فشل Yahoo، حاول Finnhub
            return self._get_company_info_finnhub(symbol)
            
        except Exception as e:
            self.logger.error(f"Error fetching company info for {symbol}: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _get_company_info_finnhub(self, symbol: str) -> Dict[str, Any]:
        """جلب معلومات الشركة من Finnhub"""
        try:
            api_key = self.api_keys.get('finnhub')
            if not api_key:
                return {'symbol': symbol, 'error': 'Finnhub API key not found'}
            
            url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={api_key}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'name': data.get('name', ''),
                    'sector': data.get('finnhubIndustry', ''),
                    'country': data.get('country', ''),
                    'website': data.get('weburl', ''),
                    'description': data.get('description', ''),
                    'employees': data.get('employeeCount', 0),
                    'market_cap': data.get('marketCapitalization', 0),
                    'source': 'finnhub'
                }
        except Exception as e:
            self.logger.error(f"Finnhub company info error for {symbol}: {str(e)}")
        
        return {'symbol': symbol, 'error': 'Unable to fetch company info'}
    
    # ======================== النتائج المالية ========================
    
    @cached(ttl=86400)  # تخزين لمدة يوم
    def get_financials(self, symbol: str) -> Dict[str, Any]:
        """
        جلب النتائج المالية للشركة
        
        Args:
            symbol: رمز السهم
        
        Returns:
            dict: البيانات المالية
        """
        self.logger.info(f"Fetching financials for {symbol}")
        
        try:
            # محاولة من Yahoo Finance
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            params = {
                'modules': 'incomeStatementHistory,balanceSheetHistory,cashflowStatementHistory'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('quoteSummary', {}).get('result', [])
                
                if result:
                    info = result[0]
                    
                    # قائمة الدخل
                    income = info.get('incomeStatementHistory', {}).get('incomeStatementHistory', [])
                    # الميزانية العمومية
                    balance = info.get('balanceSheetHistory', {}).get('balanceSheetStatements', [])
                    # التدفقات النقدية
                    cashflow = info.get('cashflowStatementHistory', {}).get('cashflowStatements', [])
                    
                    return {
                        'symbol': symbol,
                        'income_statement': income[:4] if income else [],
                        'balance_sheet': balance[:4] if balance else [],
                        'cash_flow': cashflow[:4] if cashflow else [],
                        'source': 'yahoo'
                    }
            
            return {'symbol': symbol, 'error': 'No financial data available'}
            
        except Exception as e:
            self.logger.error(f"Error fetching financials for {symbol}: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}
    
    # ======================== توصيات المحللين ========================
    
    @cached(ttl=3600)  # تخزين لمدة ساعة
    def get_analyst_ratings(self, symbol: str) -> Dict[str, Any]:
        """
        جلب توصيات المحللين
        
        Args:
            symbol: رمز السهم
        
        Returns:
            dict: توصيات المحللين
        """
        self.logger.info(f"Fetching analyst ratings for {symbol}")
        
        try:
            # محاولة من Yahoo Finance
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            params = {
                'modules': 'upgradeDowngradeHistory,recommendationTrend'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('quoteSummary', {}).get('result', [])
                
                if result:
                    info = result[0]
                    trends = info.get('recommendationTrend', {}).get('trend', [])
                    
                    return {
                        'symbol': symbol,
                        'recommendation': info.get('recommendationTrend', {}).get('currentRecommendation', ''),
                        'trend': trends,
                        'source': 'yahoo'
                    }
            
            # محاولة من Finnhub
            return self._get_analyst_ratings_finnhub(symbol)
            
        except Exception as e:
            self.logger.error(f"Error fetching analyst ratings for {symbol}: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _get_analyst_ratings_finnhub(self, symbol: str) -> Dict[str, Any]:
        """جلب توصيات المحللين من Finnhub"""
        try:
            api_key = self.api_keys.get('finnhub')
            if not api_key:
                return {'symbol': symbol, 'error': 'Finnhub API key not found'}
            
            url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={symbol}&token={api_key}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    latest = data[0] if data else {}
                    return {
                        'symbol': symbol,
                        'rating': 'buy' if latest.get('buy', 0) > latest.get('sell', 0) else 'sell',
                        'buy': latest.get('buy', 0),
                        'hold': latest.get('hold', 0),
                        'sell': latest.get('sell', 0),
                        'strong_buy': latest.get('strongBuy', 0),
                        'strong_sell': latest.get('strongSell', 0),
                        'source': 'finnhub'
                    }
        except Exception as e:
            self.logger.error(f"Finnhub analyst ratings error for {symbol}: {str(e)}")
        
        return {'symbol': symbol, 'error': 'Unable to fetch analyst ratings'}
    
    # ======================== الأخبار =======================
