# api/endpoints/company.py
from fastapi import APIRouter, HTTPException
from typing import List
from models.company import CompanyInfo
from services.dashboard_service import DashboardService
from services.portfolio_service import PortfolioService

router = APIRouter(prefix="/api/company", tags=["Company"])

@router.get("/info/{symbol}", response_model=CompanyInfo)
async def get_company_info(symbol: str):
    """Get company information for Dashboard and Portfolio."""
    service = DashboardService()
    data = service.get_dashboard_data(symbol)
    
    if not data.get("company"):
        raise HTTPException(status_code=404, detail=f"Company {symbol} not found")
    
    return data["company"]

@router.post("/portfolio")
async def get_portfolio_data(symbols: List[str]):
    """Get company data for multiple portfolio symbols."""
    service = PortfolioService()
    return service.get_portfolio_companies(symbols)
