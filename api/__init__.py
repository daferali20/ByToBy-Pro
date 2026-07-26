# api/__init__.py
"""
وحدة API للتعامل مع البيانات المالية
Financial Data API Module
"""
# api/__init__.py
"""
ByToBy Pro - API Package
====================================

This package provides a professional Yahoo Finance API wrapper
with comprehensive company data, price feeds, and historical data.

Main Components:
- YahooAPI: Main class with all API methods
- Convenience functions for quick access

Usage Examples:
---------------
```python
# Get company info for Dashboard
from api import get_company_info, get_dashboard_data

# Saudi company
info = get_company_info("2222.SR")
print(info["companyName"])  # أرامكو السعودية

# US company
info = get_company_info("AAPL")
print(info["sector"])  # التكنولوجيا

# Complete dashboard data
dashboard = get_dashboard_data("2222.SR")
print(dashboard["price"]["price"])

# Portfolio data
from api import get_portfolio_data
portfolio = get_portfolio_data(["AAPL", "2222.SR", "TSLA"])
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
