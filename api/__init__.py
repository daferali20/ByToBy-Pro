# api/__init__.py
"""
ByToBy Pro - API Package
"""

# Import all functions
from .yahoo_api import (
    YahooAPI,
    get_company_info,
    get_price,
    get_history,
    get_dashboard_data,
    get_portfolio_data,
    validate_symbol
)

__version__ = "1.0.0"

__all__ = [
    'YahooAPI',
    'get_company_info',
    'get_price',
    'get_history',
    'get_dashboard_data',
    'get_portfolio_data',
    'validate_symbol'
]

# Print status
print(f"✅ ByToBy Pro API v{__version__} loaded")
