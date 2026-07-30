import requests
import pandas as pd
from datetime import datetime, timedelta

# --- 1. اختيار مصدر البيانات ---
# يمكنك الاختيار بين المصادر التالية حسب احتياجاتك وميزانيتك.
# اختر المصدر المناسب وأدخل مفتاح API إذا كان مطلوباً.

# المصدر الأول: Intrinio (يحتاج إلى مفتاح API، يوفر بيانات شاملة)
INTRINIO_API_KEY = "YOUR_INTRINIO_API_KEY"  # استبدل بمفتاحك
INTRINIO_URL = "https://api-v2.intrinio.com/companies/upcoming_earnings"

# المصدر الثاني: Nasdaq Data Link (Zacks Data) (يحتاج إلى مفتاح API، دقة عالية)
NASDAQ_API_KEY = "YOUR_NASAQ_API_KEY"  # استبدل بمفتاحك
NASDAQ_URL = "https://data.nasdaq.com/api/v3/datatables/ZACKS/EA"

# المصدر الثالث: Apify Financial Calendar Scraper (مجاني وسهل، بدون مفتاح API)
APIFY_URL = "https://api.apify.com/v2/acts/sheshinmcfly~financial-calendar-scraper/runs"

def get_earnings_intrinio(days_ahead=30):
    """جلب مواعيد الأرباح من Intrinio"""
    params = {
        'api_key': INTRINIO_API_KEY,
        'expected_date_after': datetime.now().strftime('%Y-%m-%d'),
        'expected_date_before': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d'),
        'page_size': 100
    }
    try:
        response = requests.get(INTRINIO_URL, params=params)
        response.raise_for_status()
        data = response.json()
        earnings_list = []
        for item in data.get('expected_earnings_dates', []):
            earnings_list.append({
                'ticker': item.get('ticker'),
                'fiscal_quarter': item.get('fiscal_period'),
                'fiscal_year': item.get('fiscal_year'),
                'expected_date': item.get('expected_date')
            })
        return pd.DataFrame(earnings_list)
    except Exception as e:
        print(f"خطأ في Intrinio: {e}")
        return pd.DataFrame()

def get_earnings_nasdaq(days_ahead=30):
    """جلب مواعيد الأرباح من Nasdaq Data Link"""
    params = {
        'api_key': NASDAQ_API_KEY,
        'qopts.columns': 'ticker,exp_rpt_date_qr1,eps_mean_est_qr1',
        'exp_rpt_date_qr1.gte': datetime.now().strftime('%Y-%m-%d'),
        'exp_rpt_date_qr1.lt': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    }
    try:
        response = requests.get(NASDAQ_URL, params=params)
        response.raise_for_status()
        data = response.json()
        earnings_list = []
        for row in data.get('datatable', {}).get('data', []):
            earnings_list.append({
                'ticker': row[0],
                'expected_date': row[1],
                'eps_estimate': row[2] if len(row) > 2 else None
            })
        return pd.DataFrame(earnings_list)
    except Exception as e:
        print(f"خطأ في Nasdaq: {e}")
        return pd.DataFrame()

def get_earnings_apify(days_ahead=30):
    """جلب مواعيد الأرباح من Apify (بدون مفتاح API)"""
    end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    payload = {
        "calendars": ["earnings"],
        "dateFrom": datetime.now().strftime('%Y-%m-%d'),
        "dateTo": end_date,
        "symbols": []  # اتركه فارغاً لجلب كل الشركات
    }
    try:
        response = requests.post(APIFY_URL, json=payload)
        response.raise_for_status()
        run_id = response.json().get('data', {}).get('id')
        # في التطبيق الحقيقي، ستحتاج إلى الانتظار حتى يكتمل التشغيل ثم جلب النتائج
        print(f"تم بدء تشغيل Apify. معرف التشغيل: {run_id}")
        print("ملاحظة: تحتاج إلى تنفيذ منطق إضافي لجلب النتائج.")
        return pd.DataFrame()
    except Exception as e:
        print(f"خطأ في Apify: {e}")
        return pd.DataFrame()

# --- 2. اختيار المصدر وتنفيذ الجلب ---

# اختر المصدر المناسب:
# df_earnings = get_earnings_intrinio(days_ahead=30)
# df_earnings = get_earnings_nasdaq(days_ahead=30)
# df_earnings = get_earnings_apify(days_ahead=30)

# مثال باستخدام بيانات وهمية للتوضيح
df_earnings = pd.DataFrame([
    {'ticker': 'AAPL', 'expected_date': '2026-08-15', 'eps_estimate': 1.35},
    {'ticker': 'MSFT', 'expected_date': '2026-07-25', 'eps_estimate': 2.85},
    {'ticker': 'GOOGL', 'expected_date': '2026-07-20', 'eps_estimate': 1.92},
    {'ticker': 'AMZN', 'expected_date': '2026-08-01', 'eps_estimate': 0.75},
    {'ticker': 'META', 'expected_date': '2026-07-28', 'eps_estimate': 3.45},
])

# --- 3. فرز البيانات وعرضها ---

if not df_earnings.empty:
    # فرز حسب التاريخ (الأقرب أولاً)
    df_sorted_by_date = df_earnings.sort_values(by='expected_date')
    print("\n--- الأسهم المعلنة عن أرباحها (مرتبة حسب التاريخ) ---")
    print(df_sorted_by_date[['ticker', 'expected_date', 'eps_estimate']])

    # فرز حسب تقدير EPS (الأعلى أولاً)
    if 'eps_estimate' in df_earnings.columns:
        df_sorted_by_eps = df_earnings.sort_values(by='eps_estimate', ascending=False)
        print("\n--- الأسهم المعلنة عن أرباحها (مرتبة حسب أعلى تقدير EPS) ---")
        print(df_sorted_by_eps[['ticker', 'expected_date', 'eps_estimate']])
else:
    print("لم يتم العثور على بيانات.")
