# api/endpoints/portfolio.py
"""
Portfolio Endpoints
====================================

FastAPI endpoints for portfolio management.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from api import get_portfolio_data, YahooAPI

# Create router
router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])

# =====================================================
# Response Models
# =====================================================

class HoldingResponse(BaseModel):
    """Single holding in portfolio."""
    symbol: str
    companyName: str
    sector: str
    industry: str
    marketCap: float
    employees: int
    country: str
    website: str
    description: str
    currentPrice: float
    currency: str
    volume: int
    
    # Optional: portfolio-specific fields
    shares: float = 0
    buyPrice: float = 0
    totalValue: float = 0
    profitLoss: float = 0
    profitLossPercent: float = 0

class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary."""
    totalHoldings: int
    totalValue: float
    totalMarketCap: float
    sectors: Dict[str, Any]
    countries: Dict[str, Any]
    holdings: List[HoldingResponse]

class AddHoldingRequest(BaseModel):
    """Request to add a holding."""
    symbol: str
    shares: float
    buyPrice: float

# =====================================================
# Endpoints
# =====================================================

@router.post("/holdings", response_model=List[HoldingResponse])
async def get_portfolio_holdings(symbols: List[str]):
    """
    Get data for portfolio holdings.
    
    Parameters
    ----------
    symbols : List[str]
        List of stock symbols in portfolio
        
    Returns
    -------
    List[HoldingResponse]
        Portfolio holding data
    """
    try:
        data = get_portfolio_data(symbols)
        return [HoldingResponse(**item) for item in data]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio data: {str(e)}"
        )

@router.post("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    symbols: List[str],
    holdings: Dict[str, Dict[str, float]] = None
):
    """
    Get complete portfolio summary with analytics.
    
    Parameters
    ----------
    symbols : List[str]
        List of stock symbols in portfolio
    holdings : Dict, optional
        Additional holding details (shares, buyPrice)
        
    Returns
    -------
    PortfolioSummaryResponse
        Complete portfolio summary
    """
    try:
        api = YahooAPI()
        
        # Get company data
        company_data = get_portfolio_data(symbols)
        
        # Get sector breakdown
        sector_breakdown = api.get_sector_breakdown(symbols)
        
        # Get country breakdown
        country_breakdown = api.get_country_breakdown(symbols)
        
        # Calculate totals
        total_value = sum(
            item["currentPrice"] * (holdings.get(item["symbol"], {}).get("shares", 0) if holdings else 0)
            for item in company_data
        )
        
        total_market_cap = sum(item["marketCap"] for item in company_data)
        
        # Create holdings with portfolio-specific data
        holdings_list = []
        for item in company_data:
            holding_info = item.copy()
            if holdings and item["symbol"] in holdings:
                holding_info["shares"] = holdings[item["symbol"]].get("shares", 0)
                holding_info["buyPrice"] = holdings[item["symbol"]].get("buyPrice", 0)
                holding_info["totalValue"] = holding_info["shares"] * holding_info["currentPrice"]
                holding_info["profitLoss"] = holding_info["totalValue"] - (holding_info["shares"] * holding_info["buyPrice"])
                holding_info["profitLossPercent"] = (
                    ((holding_info["currentPrice"] - holding_info["buyPrice"]) / holding_info["buyPrice"]) * 100
                    if holding_info["buyPrice"] > 0 else 0
                )
            holdings_list.append(HoldingResponse(**holding_info))
        
        return PortfolioSummaryResponse(
            totalHoldings=len(symbols),
            totalValue=total_value,
            totalMarketCap=total_market_cap,
            sectors=sector_breakdown,
            countries=country_breakdown,
            holdings=holdings_list
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio summary: {str(e)}"
        )

@router.post("/add")
async def add_holding(request: AddHoldingRequest):
    """
    Add a holding to portfolio.
    
    This validates the symbol and returns company info.
    """
    try:
        api = YahooAPI()
        
        # Validate symbol
        if not api.validate_symbol(request.symbol):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid symbol: {request.symbol}"
            )
        
        # Get company info
        company = api.get_company_info(request.symbol)
        
        return {
            "status": "success",
            "message": f"Added {request.symbol} to portfolio",
            "holding": {
                "symbol": request.symbol,
                "companyName": company["companyName"],
                "sector": company["sector"],
                "shares": request.shares,
                "buyPrice": request.buyPrice,
                "totalValue": request.shares * request.buyPrice,
                "industry": company["industry"],
                "country": company["country"],
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add holding: {str(e)}"
        )
