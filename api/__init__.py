"""
ByToBy Pro - API Package
"""

from .yahoo_api import (
    YahooAPI,
    get_company_info,
    get_price,
    get_history,
    get_dashboard_data,
    get_portfolio_data,
    validate_symbol,
)

__version__ = "1.0.0"
__author__ = "ByToBy Pro Team"

__all__ = [
    "YahooAPI",
    "get_company_info",
    "get_price",
    "get_history",
    "get_dashboard_data",
    "get_portfolio_data",
    "validate_symbol",
]

# Package initialization
print("✅ ByToBy Pro API loaded")
