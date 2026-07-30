import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# تكوين الصفحة
st.set_page_config(page_title="مفاجآت الأرباح", layout="wide")
st.title("📈 الأسهم التي فاقت توقعات الأرباح")

# --- إدخال المفتاح بأمان (من خلال شريط جانبي) ---
with st.sidebar:
    st.header("🔑 الإعدادات")
    api_key = st.text_input("bz.LEHKFPWH4EKQTBUMQ5HJ5HW3ZABANSAJ", type="password")
    days_back = st.slider("عدد الأيام السابقة", 1, 30, 7)
    
    if st.button("🔄 جلب البيانات", type="primary"):
        if not api_key:
            st.error("⚠️ الرجاء إدخال مفتاح API")
            st.stop()
        else:
            # تخزين المفتاح في session state
            st.session_state['api_key'] = api_key

# --- دالة جلب البيانات مع معالجة الأخطاء ---
@st.cache_data(ttl=3600)
def fetch_earnings_beats(api_key, days_back=7):
    """جلب الأسهم التي فاقت توقعات الأرباح"""
    
    # حساب التواريخ
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    url = "https://api.benzinga.com/api/v2.1/calendar/earnings"
    
    params = {
        "token": api_key,
        "date_from": start_date,
        "date_to": end_date,
        "pagesize": 200  # جلب عدد أكبر من النتائج
    }
    
    try:
        # إرسال الطلب
        response = requests.get(url, params=params, timeout=30)
        
        # التحقق من حالة الطلب
        if response.status_code != 200:
            error_msg = f"خطأ في الاتصال: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail.get('message', '')}"
            except:
                error_msg += f" - {response.text[:100]}"
            return pd.DataFrame(), error_msg
        
        # تحويل البيانات
        data = response.json()
        
        if "earnings" not in data or not data["earnings"]:
            return pd.DataFrame(), "لم يتم العثور على بيانات في هذه الفترة"
        
        # تحويل إلى DataFrame
        df = pd.DataFrame(data["earnings"])
        
        # تنظيف البيانات
        df["eps_surprise_percent"] = pd.to_numeric(df.get("eps_surprise_percent"), errors="coerce")
        df["eps_est"] = pd.to_numeric(df.get("eps_est"), errors="coerce")
        df["eps"] = pd.to_numeric(df.get("eps"), errors="coerce")
        
        # تصفية الشركات التي فاقت التوقعات
        earnings_beats = df[df["eps_surprise_percent"] > 0].copy()
        
        if earnings_beats.empty:
            return earnings_beats, "✅ تم جلب البيانات، ولكن لم يتم العثور على شركات فاقت التوقعات."
        
        # ترتيب حسب نسبة المفاجأة (الأعلى أولاً)
        earnings_beats = earnings_beats.sort_values("eps_surprise_percent", ascending=False)
        
        return earnings_beats, f"✅ تم العثور على {len(earnings_beats)} شركة فاقت التوقعات"
        
    except requests.exceptions.Timeout:
        return pd.DataFrame(), "⏰ انتهى وقت الاتصال. حاول مرة أخرى."
    except requests.exceptions.ConnectionError:
        return pd.DataFrame(), "🔌 فشل الاتصال بالإنترنت أو بالـ API."
    except Exception as e:
        return pd.DataFrame(), f"❌ خطأ غير متوقع: {str(e)}"

# --- تنفيذ الجلب وعرض النتائج ---
if 'api_key' in st.session_state:
    with st.spinner("جاري جلب البيانات..."):
        df, message = fetch_earnings_beats(st.session_state['api_key'], days_back)
    
    # عرض الرسالة
    if "✅" in message:
        st.success(message)
    else:
        st.warning(message)
    
    # عرض النتائج إذا كانت موجودة
    if not df.empty:
        # إحصائيات سريعة
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 عدد الشركات", len(df))
        with col2:
            avg_surprise = df["eps_surprise_percent"].mean()
            st.metric("📈 متوسط نسبة المفاجأة", f"{avg_surprise:.2f}%")
        with col3:
            max_surprise = df["eps_surprise_percent"].max()
            top_ticker = df[df["eps_surprise_percent"] == max_surprise]["ticker"].iloc[0]
            st.metric("🏆 أعلى مفاجأة", f"{top_ticker} (+{max_surprise:.2f}%)")
        
        # عرض الجدول
        st.dataframe(
            df[["ticker", "date", "eps_est", "eps", "eps_surprise_percent"]],
            use_container_width=True,
            column_config={
                "ticker": "رمز السهم",
                "date": "التاريخ",
                "eps_est": "التوقع",
                "eps": "الفعلي",
                "eps_surprise_percent": st.column_config.NumberColumn("نسبة المفاجأة (%)", format="%.2f%%")
            }
        )
        
        # زر تحميل
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 تحميل النتائج (CSV)",
            data=csv,
            file_name=f"earnings_beats_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
else:
    st.info("👈 الرجاء إدخال مفتاح API في الشريط الجانبي")

# --- معلومات إضافية في الشريط الجانبي ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### ℹ️ معلومات")
    st.markdown("""
    - **بيانات من**: Benzinga API
    - **تعريف**: الأسهم التي حققت أرباحاً فعلية أعلى من التوقعات
    - **نسبة المفاجأة**: `(الفعلي - التوقع) / |التوقع| * 100`
    """)
