import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="bz.LEHKFPWH4EKQTBUMQ5HJ5HW3ZABANSAJ", layout="wide")
st.title("📈 الأسهم التي فاقت توقعات الأرباح")

# --- إدخال المفتاح فقط (بدون كلمة مرور) ---
with st.sidebar:
    st.header("🔑 الإعدادات")
    api_key = st.text_input("🔐 مفتاح API", type="default")
    days_back = st.slider("عدد الأيام السابقة", 1, 30, 7)
    
    # اختيار المصدر
    source = st.selectbox(
        "اختر مصدر البيانات",
        ["Benzinga", "Intrinio", "Nasdaq Data Link"],
        key="source_select"  # إضافة key فريد
    )
    
    if st.button("🔄 جلب البيانات", type="primary"):
        if not api_key:
            st.error("⚠️ الرجاء إدخال مفتاح API")
            st.stop()
        else:
            # تخزين القيم في session_state
            st.session_state['api_key'] = api_key
            st.session_state['source'] = source
            st.session_state['days_back'] = days_back
            st.rerun()  # إعادة تشغيل التطبيق لتحديث الحالة

# --- التحقق الآمن من وجود القيم في session_state ---
# استخدم .get() للوصول الآمن
api_key = st.session_state.get('api_key', '')
source = st.session_state.get('source', 'Benzinga')
days_back = st.session_state.get('days_back', 7)

# --- دوال جلب البيانات حسب المصدر ---
def fetch_benzinga(api_key, days_back):
    """جلب من Benzinga API"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    url = "https://api.benzinga.com/api/v2.1/calendar/earnings"
    params = {
        "token": api_key,
        "date_from": start_date,
        "date_to": end_date,
        "pagesize": 200
    }
    
    response = requests.get(url, params=params, timeout=30)
    return response

def fetch_intrinio(api_key, days_back):
    """جلب من Intrinio API"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    url = "https://api-v2.intrinio.com/companies/upcoming_earnings"
    params = {
        "api_key": api_key,
        "expected_date_after": start_date,
        "expected_date_before": end_date
    }
    
    response = requests.get(url, params=params, timeout=30)
    return response

def fetch_nasdaq(api_key, days_back):
    """جلب من Nasdaq Data Link"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    url = "https://data.nasdaq.com/api/v3/datatables/ZACKS/EA"
    params = {
        "api_key": api_key,
        "qopts.columns": "ticker,exp_rpt_date_qr1,eps_mean_est_qr1"
    }
    
    response = requests.get(url, params=params, timeout=30)
    return response

# --- دالة معالجة النتائج وعرضها ---
@st.cache_data(ttl=3600)
def get_earnings_beats(api_key, days_back, source):
    """جلب ومعالجة بيانات الأرباح"""
    
    if not api_key:
        return pd.DataFrame(), "⚠️ الرجاء إدخال مفتاح API"
    
    try:
        # اختيار الدالة المناسبة
        if source == "Benzinga":
            response = fetch_benzinga(api_key, days_back)
        elif source == "Intrinio":
            response = fetch_intrinio(api_key, days_back)
        else:  # Nasdaq Data Link
            response = fetch_nasdaq(api_key, days_back)
        
        # التحقق من الاستجابة
        if response.status_code != 200:
            error_msg = f"❌ خطأ {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('message', response.text[:100])}"
            except:
                error_msg += f": {response.text[:100]}"
            return pd.DataFrame(), error_msg
        
        # معالجة البيانات حسب المصدر
        data = response.json()
        
        if source == "Benzinga":
            if "earnings" not in data:
                return pd.DataFrame(), "⚠️ لم يتم العثور على بيانات"
            df = pd.DataFrame(data["earnings"])
            df["eps_surprise_percent"] = pd.to_numeric(df.get("eps_surprise_percent"), errors="coerce")
            df = df[df["eps_surprise_percent"] > 0]
            
        elif source == "Intrinio":
            if "expected_earnings_dates" not in data:
                return pd.DataFrame(), "⚠️ لم يتم العثور على بيانات"
            df = pd.DataFrame(data["expected_earnings_dates"])
            # Intrinio قد لا توفر نسبة المفاجأة مباشرة
            df = df[df.get("surprise_percent", 0) > 0]
            
        else:  # Nasdaq
            if "datatable" not in data:
                return pd.DataFrame(), "⚠️ لم يتم العثور على بيانات"
            rows = data["datatable"].get("data", [])
            if not rows:
                return pd.DataFrame(), "⚠️ لم يتم العثور على بيانات"
            df = pd.DataFrame(rows, columns=["ticker", "date", "eps_est"])
        
        if df.empty:
            return df, "ℹ️ لم يتم العثور على شركات فاقت التوقعات"
        
        return df, f"✅ تم العثور على {len(df)} شركة فاقت التوقعات"
        
    except requests.exceptions.Timeout:
        return pd.DataFrame(), "⏰ انتهى وقت الاتصال"
    except requests.exceptions.ConnectionError:
        return pd.DataFrame(), "🔌 فشل الاتصال بالإنترنت"
    except Exception as e:
        return pd.DataFrame(), f"❌ خطأ: {str(e)}"

# --- عرض النتائج ---
# التحقق من وجود api_key في session_state
if api_key:
    with st.spinner("جاري جلب البيانات..."):
        df, message = get_earnings_beats(api_key, days_back, source)
    
    if "✅" in message:
        st.success(message)
    else:
        st.warning(message)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # زر تحميل
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 تحميل CSV",
            data=csv,
            file_name=f"earnings_beats_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
else:
    st.info("👈 الرجاء إدخال مفتاح API في الشريط الجانبي")

# --- عرض تعليمات في الشريط الجانبي ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### ℹ️ كيفية الحصول على مفتاح API")
    st.markdown("""
    - **Benzinga**: سجل في [Benzinga](https://www.benzinga.com/apis/)
    - **Intrinio**: سجل في [Intrinio](https://intrinio.com/)
    - **Nasdaq**: سجل في [Nasdaq Data Link](https://data.nasdaq.com/)
    """)
