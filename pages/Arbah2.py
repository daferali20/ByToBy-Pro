import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="مفاجآت الأرباح", layout="wide")
st.title("📈 الأسهم التي فاقت توقعات الأرباح")

# --- إعدادات الشريط الجانبي ---
with st.sidebar:
    st.header("🔑 الإعدادات")
    api_key = st.text_input("bz.LEHKFPWH4EKQTBUMQ5HJ5HW3ZABANSAJ", type="default", 
                           help="أدخل مفتاح API من Benzinga أو Intrinio")
    
    days_back = st.slider("عدد الأيام السابقة", 1, 30, 7)
    
    source = st.selectbox(
        "اختر مصدر البيانات",
        ["Benzinga", "Intrinio", "Nasdaq Data Link"],
        key="source_select"
    )
    
    # زر الجلب
    fetch_clicked = st.button("🔄 جلب البيانات", type="primary")

# --- دوال الجلب مع معالجة الأخطاء ---
def safe_json_parse(response):
    """محاولة تحليل الاستجابة كـ JSON مع معالجة الأخطاء"""
    try:
        return response.json()
    except json.JSONDecodeError as e:
        # إذا فشل التحليل، اطبع الرد للمساعدة في التشخيص
        st.error(f"❌ الـ API لم يعد بيانات JSON صالحة")
        st.code(f"نوع المحتوى: {response.headers.get('content-type')}\n"
                f"الحالة: {response.status_code}\n"
                f"الرد: {response.text[:500]}")
        return None

def fetch_benzinga(api_key, days_back):
    """جلب من Benzinga API مع معالجة الأخطاء"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    url = "https://api.benzinga.com/api/v2.1/calendar/earnings"
    
    # المحاولة الأولى: المفتاح كمعامل
    params = {
        "token": api_key,
        "date_from": start_date,
        "date_to": end_date,
        "pagesize": 200
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        # التحقق من حالة الاستجابة
        if response.status_code == 401:
            return None, "❌ مفتاح API غير صحيح (Unauthorized). تأكد من المفتاح."
        elif response.status_code == 403:
            return None, "❌ لا تملك صلاحية الوصول (Forbidden). قد يكون المفتاح منتهي الصلاحية."
        elif response.status_code == 404:
            return None, "❌ الـ API غير موجود. تحقق من الرابط."
        elif response.status_code != 200:
            return None, f"❌ خطأ {response.status_code}: {response.text[:200]}"
        
        # محاولة تحليل JSON
        data = safe_json_parse(response)
        if data is None:
            return None, "❌ فشل تحليل البيانات. تأكد من أن المفتاح صحيح."
        
        # التحقق من وجود البيانات
        if "earnings" not in data:
            return None, "⚠️ لم يتم العثور على بيانات أرباح في هذه الفترة."
        
        df = pd.DataFrame(data["earnings"])
        if df.empty:
            return None, "ℹ️ لا توجد بيانات في هذه الفترة."
        
        # تنظيف البيانات
        if "eps_surprise_percent" in df.columns:
            df["eps_surprise_percent"] = pd.to_numeric(df["eps_surprise_percent"], errors="coerce")
            df = df[df["eps_surprise_percent"] > 0]
        
        return df, f"✅ تم العثور على {len(df)} شركة فاقت التوقعات"
        
    except requests.exceptions.Timeout:
        return None, "⏰ انتهى وقت الاتصال. حاول مرة أخرى."
    except requests.exceptions.ConnectionError:
        return None, "🔌 فشل الاتصال بالإنترنت. تحقق من اتصالك."
    except Exception as e:
        return None, f"❌ خطأ غير متوقع: {str(e)}"

def fetch_intrinio(api_key, days_back):
    """جلب من Intrinio API"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    url = "https://api-v2.intrinio.com/companies/upcoming_earnings"
    params = {"api_key": api_key}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            return None, f"❌ خطأ {response.status_code}: {response.text[:200]}"
        
        data = safe_json_parse(response)
        if data is None:
            return None, "❌ فشل تحليل البيانات."
        
        if "expected_earnings_dates" not in data:
            return None, "⚠️ لم يتم العثور على بيانات."
        
        df = pd.DataFrame(data["expected_earnings_dates"])
        return df, f"✅ تم العثور على {len(df)} شركة"
        
    except Exception as e:
        return None, f"❌ خطأ: {str(e)}"

# --- تنفيذ الجلب عند الضغط على الزر ---
if fetch_clicked:
    if not api_key:
        st.error("⚠️ الرجاء إدخال مفتاح API")
    else:
        with st.spinner(f"جاري جلب البيانات من {source}..."):
            if source == "Benzinga":
                df, message = fetch_benzinga(api_key, days_back)
            elif source == "Intrinio":
                df, message = fetch_intrinio(api_key, days_back)
            else:
                st.warning("⚠️ مصدر Nasdaq Data Link يحتاج إلى تهيئة خاصة")
                df, message = None, "⚠️ هذا المصدر قيد التطوير"
            
            # عرض الرسالة
            if "✅" in message:
                st.success(message)
            else:
                st.warning(message)
            
            # عرض البيانات إذا وجدت
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # زر تحميل
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 تحميل CSV",
                    data=csv,
                    file_name=f"earnings_beats_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

# --- رسالة ترحيبية إذا لم يتم الضغط على الزر ---
else:
    st.info("👈 أدخل مفتاح API في الشريط الجانبي واضغط 'جلب البيانات'")

# --- تعليمات في الشريط الجانبي ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### ℹ️ تعليمات")
    st.markdown("""
    **للحصول على مفتاح API:**
    
    1. **Benzinga**: [سجل هنا](https://www.benzinga.com/apis/)
    2. **Intrinio**: [سجل هنا](https://intrinio.com/)
    
    **ملاحظة**: المفاتيح التجريبية قد تكون محدودة.
    """)
