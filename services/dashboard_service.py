# services/dashboard_service.py
from typing import Dict, Any
from api.yahoo_api import YahooAPI

class DashboardService:
    """Service for Dashboard page."""
    
    def __init__(self):
        self.api = YahooAPI()
    
    def get_dashboard_data(self, symbol: str) -> Dict[str, Any]:
        """Get all data needed for Dashboard page."""
        company_info = self.api.get_company_info(symbol)
        price_data = self.api.get_price(symbol)
        history = self.api.get_history(symbol, period="1mo", interval="1d")
        
        return {
            "company": company_info,
            "price": price_data,
            "history": history.to_dict('records') if not history.empty else []
        }
