# models/company.py
from typing import Optional
from pydantic import BaseModel

class CompanyInfo(BaseModel):
    """Company information model for Dashboard and Portfolio."""
    companyName: str
    sector: str
    industry: str
    marketCap: float  # in billions
    employees: int
    country: str
    website: str
    description: str
    
    class Config:
        schema_extra = {
            "example": {
                "companyName": "أرامكو السعودية",
                "sector": "الطاقة",
                "industry": "النفط والغاز",
                "marketCap": 7500.0,
                "employees": 70000,
                "country": "السعودية",
                "website": "https://www.aramco.com",
                "description": "شركة الزيت العربية السعودية..."
            }
        }

class PriceData(BaseModel):
    symbol: str
    price: Optional[float]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    volume: Optional[int]
    market_cap: Optional[float]
    currency: Optional[str]
