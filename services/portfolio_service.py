# services/portfolio_service.py
from typing import List, Dict, Any
from api.yahoo_api import YahooAPI
from utils.logger import get_logger

logger = get_logger("PortfolioService")

class PortfolioService:
    """Service for Portfolio page."""
    
    def __init__(self):
        self.api = YahooAPI()
    
    def get_portfolio_companies(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get company info for multiple symbols."""
        result = []
        for symbol in symbols:
            try:
                company_info = self.api.get_company_info(symbol)
                price_data = self.api.get_price(symbol)
                
                result.append({
                    "symbol": symbol,
                    "companyName": company_info["companyName"],
                    "sector": company_info["sector"],
                    "industry": company_info["industry"],
                    "marketCap": company_info["marketCap"],
                    "country": company_info["country"],
                    "currentPrice": price_data.get("price", 0),
                    "employees": company_info["employees"],
                    "website": company_info["website"],
                    "description": company_info["description"]
                })
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
        
        return result
    
    def get_sector_breakdown(self, symbols: List[str]) -> Dict[str, Any]:
        """Get sector breakdown for portfolio."""
        sector_data = {}
        for symbol in symbols:
            try:
                info = self.api.get_company_info(symbol)
                sector = info["sector"]
                market_cap = info["marketCap"]
                
                if sector not in sector_data:
                    sector_data[sector] = {"total_market_cap": 0, "companies": []}
                
                sector_data[sector]["total_market_cap"] += market_cap
                sector_data[sector]["companies"].append(symbol)
            except Exception as e:
                logger.error(f"Failed to get sector for {symbol}: {e}")
        
        return sector_data
