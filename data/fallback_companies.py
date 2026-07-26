# data/fallback_companies.py
from typing import Dict, Any

# Saudi Companies
SAUDI_COMPANIES: Dict[str, Dict[str, Any]] = {
    "2222.SR": {
        "companyName": "أرامكو السعودية",
        "sector": "الطاقة",
        "industry": "النفط والغاز",
        "marketCap": 7500.0,
        "employees": 70000,
        "country": "السعودية",
        "website": "https://www.aramco.com",
        "description": "شركة الزيت العربية السعودية (أرامكو) هي شركة نفط وغاز طبيعي مملوكة للدولة السعودية."
    },
    "1120.SR": {
        "companyName": "مصرف الراجحي",
        "sector": "المالية",
        "industry": "الخدمات المصرفية",
        "marketCap": 320.0,
        "employees": 12000,
        "country": "السعودية",
        "website": "https://www.alrajhibank.com.sa",
        "description": "مصرف الراجحي هو أحد أكبر البنوك الإسلامية في العالم."
    },
    "7010.SR": {
        "companyName": "شركة الاتصالات السعودية (STC)",
        "sector": "الاتصالات",
        "industry": "الاتصالات وتقنية المعلومات",
        "marketCap": 180.0,
        "employees": 22000,
        "country": "السعودية",
        "website": "https://www.stc.com.sa",
        "description": "شركة الاتصالات السعودية هي أكبر مشغل للاتصالات في الشرق الأوسط."
    }
}

# US Companies
US_COMPANIES: Dict[str, Dict[str, Any]] = {
    "AAPL": {
        "companyName": "Apple Inc.",
        "sector": "التكنولوجيا",
        "industry": "الأجهزة الإلكترونية والبرمجيات",
        "marketCap": 2800.0,
        "employees": 164000,
        "country": "الولايات المتحدة",
        "website": "https://www.apple.com",
        "description": "شركة Apple هي شركة تكنولوجيا أمريكية متعددة الجنسيات."
    },
    "MSFT": {
        "companyName": "Microsoft Corporation",
        "sector": "التكنولوجيا",
        "industry": "البرمجيات",
        "marketCap": 2500.0,
        "employees": 221000,
        "country": "الولايات المتحدة",
        "website": "https://www.microsoft.com",
        "description": "شركة Microsoft هي شركة تكنولوجيا أمريكية."
    },
    "TSLA": {
        "companyName": "Tesla Inc.",
        "sector": "السيارات",
        "industry": "السيارات الكهربائية",
        "marketCap": 800.0,
        "employees": 140000,
        "country": "الولايات المتحدة",
        "website": "https://www.tesla.com",
        "description": "شركة Tesla هي شركة أمريكية متخصصة في السيارات الكهربائية."
    }
}

# Merge all fallbacks
ALL_FALLBACKS: Dict[str, Dict[str, Any]] = {**SAUDI_COMPANIES, **US_COMPANIES}

def get_fallback_info(symbol: str) -> Dict[str, Any]:
    """Get fallback company info by symbol."""
    return ALL_FALLBACKS.get(symbol, {
        "companyName": symbol,
        "sector": "N/A",
        "industry": "N/A",
        "marketCap": 0.0,
        "employees": 0,
        "country": "N/A",
        "website": f"https://finance.yahoo.com/quote/{symbol}",
        "description": f"No information available for {symbol}."
    })
