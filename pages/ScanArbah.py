import requests
import pandas as pd

API_KEY = "bz.LEHKFPWH4EKQTBUMQ5HJ5HW3ZABANSAJ"  # استبدل بمفتاحك
url = "https://api.benzinga.com/api/v2.1/calendar/earnings"

headers = {"accept": "application/json"}
params = {
    "token": API_KEY,
    "parameters[date_from]": "2026-07-01",  # تاريخ البداية
    "parameters[date_to]": "2026-07-30",    # تاريخ النهاية
    "pagesize": 100
}

try:
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    if "earnings" in data:
        df = pd.DataFrame(data["earnings"])
        
        # تحويل عمود نسبة المفاجأة إلى رقمي
        df["eps_surprise_percent"] = pd.to_numeric(df["eps_surprise_percent"], errors="coerce")
        
        # تصفية الأسهم التي فاقت التوقعات (نسبة المفاجأة > 0)
        earnings_beats = df[df["eps_surprise_percent"] > 0]
        
        # عرض النتائج
        if not earnings_beats.empty:
            print(f"✅ تم العثور على {len(earnings_beats)} شركة فاقت توقعات الأرباح:")
            print(earnings_beats[["ticker", "date", "eps_est", "eps", "eps_surprise_percent"]])
        else:
            print("ℹ️ لم يتم العثور على شركات فاقت التوقعات في هذه الفترة.")
            
except Exception as e:
    print(f"❌ حدث خطأ: {e}")
