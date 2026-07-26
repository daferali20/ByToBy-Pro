# api/__init__.py
"""
وحدة API للتعامل مع البيانات المالية
Financial Data API Module
"""

from .market_api import (
    MarketAPI,
    get_stock_price,
    get_historical_data,
    get_company_info,
    get_financials,
    get_analyst_ratings,
    get_stock_news,
    get_market_status
)

__all__ = [
    'MarketAPI',
    'get_stock_price',
    'get_historical_data',
    'get_company_info',
    'get_financials',
    'get_analyst_ratings',
    'get_stock_news',
    'get_market_status'
]
