import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import json

# --- تكوين Apify ---
APIFY_API_TOKEN = ""  # يمكنك تركها فارغة للاستخدام المجاني
APIFY_ACTOR_ID = "sheshinmcfly~financial-calendar-scraper"
APIFY_BASE_URL = "https://api.apify.com/v2"

def get_earnings_apify(days_ahead=30, wait_for_completion=True, timeout_seconds=300):
    """
    جلب مواعيد الأرباح من Apify Financial Calendar Scraper
    
    المعاملات:
    - days_ahead: عدد الأيام القادمة لجلب البيانات
    - wait_for_completion: انتظار اكتمال التشغيل (True) أو العودة فوراً (False)
    - timeout_seconds: أقصى وقت للانتظار بالثواني
    
    العائد: DataFrame يحتوي على بيانات الأرباح
    """
    
    # حساب التواريخ
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    # إعداد الطلب لتشغيل Actor
    run_payload = {
        "calendars": ["earnings"],  # نوع التقويم: الأرباح
        "dateFrom": start_date,
        "dateTo": end_date,
        "symbols": [],  # قائمة فارغة لجلب كل الشركات
        "country": "US"  # السوق الأمريكي
    }
    
    # إعداد الهيدرز
    headers = {
        "Content-Type": "application/json"
    }
    
    # إضافة التوكن إذا كان موجوداً
    if APIFY_API_TOKEN:
        headers["Authorization"] = f"Bearer {APIFY_API_TOKEN}"
    
    try:
        # 1. بدء تشغيل Actor
        print(f"🔄 جاري بدء تشغيل أداة Apify لجلب بيانات الأرباح من {start_date} إلى {end_date}...")
        
        run_url = f"{APIFY_BASE_URL}/acts/{APIFY_ACTOR_ID}/runs"
        response = requests.post(run_url, json=run_payload, headers=headers)
        response.raise_for_status()
        
        run_data = response.json()
        run_id = run_data.get('data', {}).get('id')
        
        if not run_id:
            print("❌ فشل في الحصول على معرف التشغيل")
            return pd.DataFrame()
        
        print(f"✅ تم بدء التشغيل بنجاح. معرف التشغيل: {run_id}")
        
        # 2. إذا طلبنا الانتظار، نتابع حالة التشغيل
        if wait_for_completion:
            print("⏳ جاري الانتظار حتى اكتمال التشغيل...")
            
            start_time = time.time()
            while True:
                # التحقق من حالة التشغيل
                status_url = f"{APIFY_BASE_URL}/acts/{APIFY_ACTOR_ID}/runs/{run_id}"
                status_response = requests.get(status_url, headers=headers)
                status_response.raise_for_status()
                
                status_data = status_response.json()
                status = status_data.get('data', {}).get('status')
                
                if status == 'SUCCEEDED':
                    print("✅ اكتمل التشغيل بنجاح!")
                    break
                elif status in ['FAILED', 'TIMED-OUT', 'ABORTED']:
                    print(f"❌ فشل التشغيل: {status}")
                    return pd.DataFrame()
                else:
                    # لا يزال قيد التشغيل
                    elapsed = int(time.time() - start_time)
                    if elapsed > timeout_seconds:
                        print(f"⏰ انتهى وقت الانتظار ({timeout_seconds} ثانية)")
                        return pd.DataFrame()
                    
                    print(f"⏳ جاري التنفيذ... الحالة: {status} (انقضى {elapsed} ثانية)")
                    time.sleep(5)  # انتظار 5 ثواني قبل التحقق مرة أخرى
            
            # 3. جلب النتائج
            print("📥 جاري جلب النتائج...")
            
            # جلب عناصر النتائج
            items_url = f"{APIFY_BASE_URL}/acts/{APIFY_ACTOR_ID}/runs/{run_id}/items"
            items_response = requests.get(items_url, headers=headers)
            items_response.raise_for_status()
            
            items_data = items_response.json()
            
            # تحليل البيانات
            earnings_list = []
            
            # البيانات تأتي بصيغة {items: [...]}
            items = items_data.get('items', [])
            
            if not items:
                print("⚠️ لم يتم العثور على بيانات")
                return pd.DataFrame()
            
            # تحويل البيانات إلى DataFrame
            for item in items:
                # استخراج الحقول المهمة
                earnings_item = {
                    'ticker': item.get('symbol', '').upper(),
                    'company_name': item.get('name', ''),
                    'expected_date': item.get('reportDate', ''),
                    'fiscal_quarter': item.get('fiscalQuarter', ''),
                    'fiscal_year': item.get('fiscalYear', ''),
                    'eps_estimate': item.get('epsEstimate'),
                    'eps_actual': item.get('epsActual'),
                    'revenue_estimate': item.get('revenueEstimate'),
                    'revenue_actual': item.get('revenueActual'),
                    'time': item.get('time', ''),  # قبل السوق/بعد السوق
                    'currency': item.get('currency', 'USD')
                }
                
                # تنظيف البيانات
                if earnings_item['expected_date']:
                    earnings_list.append(earnings_item)
            
            if earnings_list:
                df = pd.DataFrame(earnings_list)
                
                # تحويل عمود التاريخ إلى نوع datetime
                df['expected_date'] = pd.to_datetime(df['expected_date'])
                
                # تنظيف الأعمدة الرقمية
                numeric_cols = ['eps_estimate', 'eps_actual', 'revenue_estimate', 'revenue_actual']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                print(f"✅ تم جلب بيانات {len(df)} شركة بنجاح")
                return df
            else:
                print("⚠️ لا توجد بيانات صالحة للاستخراج")
                return pd.DataFrame()
        
        else:
            # العودة فوراً بدون انتظار
            print("ℹ️ تم بدء التشغيل. يمكنك جلب النتائج لاحقاً باستخدام معرف التشغيل.")
            print(f"🔗 رابط النتائج: {APIFY_BASE_URL}/acts/{APIFY_ACTOR_ID}/runs/{run_id}/items")
            return pd.DataFrame()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في الاتصال بـ Apify: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"تفاصيل الخطأ: {e.response.text}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def get_earnings_apify_dataset(dataset_id):
    """
    جلب البيانات من مجموعة بيانات (Dataset) موجودة مسبقاً
    
    المعاملات:
    - dataset_id: معرف مجموعة البيانات
    
    العائد: DataFrame يحتوي على بيانات الأرباح
    """
    headers = {}
    if APIFY_API_TOKEN:
        headers["Authorization"] = f"Bearer {APIFY_API_TOKEN}"
    
    try:
        url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        items = response.json()
        
        if not items:
            return pd.DataFrame()
        
        df = pd.DataFrame(items)
        
        # تحويل الأعمدة إلى تنسيق مناسب
        if 'reportDate' in df.columns:
            df['expected_date'] = pd.to_datetime(df['reportDate'])
        
        return df
        
    except Exception as e:
        print(f"❌ خطأ في جلب البيانات من dataset: {e}")
        return pd.DataFrame()

# --- وظائف مساعدة إضافية ---

def filter_earnings(df, min_eps=None, max_eps=None, date_range=None, tickers=None):
    """
    تصفية بيانات الأرباح حسب معايير محددة
    
    المعاملات:
    - df: DataFrame الناتج من get_earnings_apify
    - min_eps: الحد الأدنى لتقدير EPS
    - max_eps: الحد الأقصى لتقدير EPS
    - date_range: tuple (start_date, end_date) لتحديد نطاق التواريخ
    - tickers: قائمة بالرموز للتصفية
    
    العائد: DataFrame مصفى
    """
    filtered = df.copy()
    
    if filtered.empty:
        return filtered
    
    # تصفية حسب EPS
    if min_eps is not None and 'eps_estimate' in filtered.columns:
        filtered = filtered[filtered['eps_estimate'] >= min_eps]
    
    if max_eps is not None and 'eps_estimate' in filtered.columns:
        filtered = filtered[filtered['eps_estimate'] <= max_eps]
    
    # تصفية حسب التاريخ
    if date_range is not None and 'expected_date' in filtered.columns:
        start_date, end_date = date_range
        filtered = filtered[(filtered['expected_date'] >= start_date) & 
                           (filtered['expected_date'] <= end_date)]
    
    # تصفية حسب الرموز
    if tickers is not None:
        tickers_upper = [t.upper() for t in tickers]
        filtered = filtered[filtered['ticker'].isin(tickers_upper)]
    
    return filtered

def display_earnings_summary(df):
    """
    عرض ملخص لبيانات الأرباح
    """
    if df.empty:
        print("📊 لا توجد بيانات للعرض")
        return
    
    print("\n" + "="*80)
    print("📊 ملخص بيانات الأرباح القادمة")
    print("="*80)
    
    # إحصائيات عامة
    print(f"\n📈 إجمالي الشركات: {len(df)}")
    
    if 'expected_date' in df.columns:
        earliest_date = df['expected_date'].min()
        latest_date = df['expected_date'].max()
        print(f"📅 نطاق التواريخ: {earliest_date.strftime('%Y-%m-%d')} إلى {latest_date.strftime('%Y-%m-%d')}")
    
    if 'eps_estimate' in df.columns:
        valid_eps = df['eps_estimate'].dropna()
        if not valid_eps.empty:
            print(f"💰 متوسط تقدير EPS: ${valid_eps.mean():.2f}")
            print(f"💰 أعلى تقدير EPS: ${valid_eps.max():.2f} ({df[df['eps_estimate'] == valid_eps.max()]['ticker'].iloc[0]})")
            print(f"💰 أقل تقدير EPS: ${valid_eps.min():.2f} ({df[df['eps_estimate'] == valid_eps.min()]['ticker'].iloc[0]})")
    
    # عرض أول 10 شركات حسب التاريخ
    print("\n📋 أول 10 شركات (مرتبة حسب التاريخ):")
    print("-"*80)
    display_cols = ['ticker', 'expected_date', 'eps_estimate', 'time']
    if all(col in df.columns for col in display_cols[:3]):
        df_sorted = df.sort_values('expected_date')
        print(df_sorted[display_cols].head(10).to_string(index=False))
    
    print("\n" + "="*80)

# --- الوظيفة الرئيسية ---

def main():
    """
    الوظيفة الرئيسية لتشغيل الكود
    """
    print("🚀 بدء تشغيل أداة جلب بيانات الأرباح من Apify")
    print("-" * 50)
    
    # جلب البيانات للأيام الـ 30 القادمة
    df_earnings = get_earnings_apify(days_ahead=30, wait_for_completion=True)
    
    if df_earnings.empty:
        print("\n❌ لم يتم العثور على بيانات. تأكد من اتصال الإنترنت وحاول مرة أخرى.")
        return
    
    # عرض الملخص
    display_earnings_summary(df_earnings)
    
    # --- مثال على التصفية والفرز ---
    
    # 1. الفرز حسب التاريخ (الأقرب أولاً)
    df_sorted_by_date = df_earnings.sort_values('expected_date')
    print("\n📅 الأسهم مرتبة حسب التاريخ (أول 10):")
    print(df_sorted_by_date[['ticker', 'expected_date', 'eps_estimate']].head(10).to_string(index=False))
    
    # 2. الفرز حسب تقدير EPS (الأعلى أولاً)
    if 'eps_estimate' in df_earnings.columns:
        df_sorted_by_eps = df_earnings.sort_values('eps_estimate', ascending=False)
        print("\n💰 الأسهم ذات أعلى تقدير EPS (أول 10):")
        print(df_sorted_by_eps[['ticker', 'expected_date', 'eps_estimate']].head(10).to_string(index=False))
    
    # 3. تصفية حسب EPS مرتفع (أكبر من $2)
    if 'eps_estimate' in df_earnings.columns:
        high_eps = filter_earnings(df_earnings, min_eps=2.0)
        if not high_eps.empty:
            print(f"\n⭐ الأسهم بتقدير EPS > $2.00: {len(high_eps)} شركة")
            print(high_eps[['ticker', 'expected_date', 'eps_estimate']].head(10).to_string(index=False))
    
    # 4. البحث عن شركات محددة
    target_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    target_df = filter_earnings(df_earnings, tickers=target_tickers)
    if not target_df.empty:
        print(f"\n🎯 البيانات للشركات المحددة:")
        print(target_df[['ticker', 'company_name', 'expected_date', 'eps_estimate', 'time']].to_string(index=False))
    
    # 5. حفظ البيانات إلى ملف CSV
    filename = f"earnings_{datetime.now().strftime('%Y%m%d')}.csv"
    df_earnings.to_csv(filename, index=False, encoding='utf-8')
    print(f"\n💾 تم حفظ البيانات في ملف: {filename}")

# --- تشغيل البرنامج ---

if __name__ == "__main__":
    main()
