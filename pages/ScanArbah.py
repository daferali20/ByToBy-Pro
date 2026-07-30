import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="أكبر الأسهم صعوداً - السوق الأمريكي",
    page_icon="📈",
    layout="wide"
)

st.title("📈 الأسهم الأكثر صعوداً في السوق الأمريكي")
st.markdown("تعرض هذه الصفحة الأسهم التي سجلت أكبر نسبة ارتفاع في السوق الأمريكي.")

# --- إعدادات الشريط الجانبي ---
with st.sidebar:
    st.header("🔑 الإعدادات")
    
    # إدخال مفتاح API
    api_key = st.text_input(
        "مفتاح Benzinga API",
        type="password",
        help="يمكنك الحصول على مفتاح API من موقع Benzinga"
    )
    
    # اختيار نوع المتصدرين
    mover_type = st.selectbox(
        "اختر نوع المتصدرين",
        ["gainers", "losers", "mostactive"],
        format_func=lambda x: {
            "gainers": "🏆 الأكثر ارتفاعاً",
            "losers": "📉 الأكثر انخفاضاً",
            "mostactive": "📊 الأكثر نشاطاً"
        }.get(x, x)
    )
    
    # عدد النتائج
    limit = st.slider("عدد النتائج", 10, 50, 25)
    
    # زر التحديث
    if st.button("🔄 تحديث البيانات", type="primary"):
        if not api_key:
            st.error("⚠️ الرجاء إدخال مفتاح API")
            st.stop()
        else:
            st.session_state['api_key'] = api_key
            st.session_state['mover_type'] = mover_type
            st.session_state['limit'] = limit
            st.rerun()

# --- دالة جلب البيانات من Benzinga API ---
@st.cache_data(ttl=300)  # تخزين البيانات لمدة 5 دقائق
def fetch_top_movers(api_key, mover_type="gainers", limit=25):
    """
    جلب الأسهم الأكثر صعوداً من Benzinga API
    
    المعاملات:
        api_key: مفتاح Benzinga API
        mover_type: نوع المتصدرين (gainers, losers, mostactive)
        limit: عدد النتائج المطلوبة
    
    العائد:
        DataFrame يحتوي على بيانات الأسهم
    """
    
    # عنوان API الخاص بـ Market Movers من Benzinga [citation:3][citation:7]
    url = "https://api.benzinga.com/api/v2.1/market-movers"
    
    # معاملات الطلب
    params = {
        "token": api_key,
        "type": mover_type,  # gainers, losers, mostactive
        "limit": limit
    }
    
    # طلب البيانات بصيغة JSON
    headers = {
        "Accept": "application/json"
    }
    
    try:
        with st.spinner(f"جاري جلب بيانات {mover_type}..."):
            response = requests.get(url, params=params, headers=headers, timeout=30)
        
        # التحقق من حالة الاستجابة
        if response.status_code == 401:
            st.error("❌ مفتاح API غير صحيح. تأكد من المفتاح.")
            return pd.DataFrame()
        elif response.status_code == 403:
            st.error("❌ لا تملك صلاحية الوصول لهذه البيانات.")
            return pd.DataFrame()
        elif response.status_code != 200:
            st.error(f"❌ خطأ {response.status_code}: {response.text[:200]}")
            return pd.DataFrame()
        
        # تحليل البيانات
        data = response.json()
        
        # التحقق من وجود البيانات
        if not data or "movers" not in data:
            st.warning("⚠️ لم يتم العثور على بيانات")
            return pd.DataFrame()
        
        # تحويل البيانات إلى DataFrame
        df = pd.DataFrame(data["movers"])
        
        if df.empty:
            st.warning("⚠️ لا توجد بيانات متاحة حالياً")
            return pd.DataFrame()
        
        # تنظيف البيانات وتحويل الأعمدة الرقمية
        numeric_cols = ["last_price", "change", "percent_change", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # إعادة ترتيب الأعمدة
        column_order = ["ticker", "last_price", "change", "percent_change", "volume"]
        available_cols = [col for col in column_order if col in df.columns]
        df = df[available_cols]
        
        # ترتيب حسب نسبة التغير (تنازلياً للأسهم الرابحة)
        if "percent_change" in df.columns and mover_type == "gainers":
            df = df.sort_values("percent_change", ascending=False)
        
        return df
        
    except requests.exceptions.Timeout:
        st.error("⏰ انتهى وقت الاتصال. حاول مرة أخرى.")
        return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error("🔌 فشل الاتصال بالإنترنت.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ خطأ غير متوقع: {str(e)}")
        return pd.DataFrame()

# --- عرض البيانات ---
# التحقق من وجود المفتاح في session_state
api_key = st.session_state.get('api_key', '')
mover_type = st.session_state.get('mover_type', 'gainers')
limit = st.session_state.get('limit', 25)

if api_key:
    # جلب البيانات
    df = fetch_top_movers(api_key, mover_type, limit)
    
    if not df.empty:
        # --- عرض الإحصائيات السريعة ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 عدد الأسهم", len(df))
        
        if "percent_change" in df.columns:
            avg_change = df["percent_change"].mean()
            with col2:
                st.metric(
                    "📈 متوسط نسبة التغير",
                    f"{avg_change:.2f}%",
                    delta=f"{avg_change:.2f}%" if avg_change > 0 else None
                )
            
            max_change = df["percent_change"].max()
            if not df.empty and "ticker" in df.columns:
                top_ticker = df.loc[df["percent_change"].idxmax(), "ticker"]
                with col3:
                    st.metric(
                        "🏆 أعلى نسبة ارتفاع",
                        f"{top_ticker} (+{max_change:.2f}%)"
                    )
        
        st.divider()
        
        # --- عرض الجدول الرئيسي ---
        st.subheader("📋 قائمة الأسهم")
        
        # تنسيق الجدول
        column_config = {
            "ticker": "رمز السهم",
            "last_price": st.column_config.NumberColumn(
                "السعر الحالي",
                format="$%.2f"
            ),
            "change": st.column_config.NumberColumn(
                "التغير (بالدولار)",
                format="$%.2f"
            ),
            "percent_change": st.column_config.NumberColumn(
                "نسبة التغير",
                format="%.2f%%"
            ),
            "volume": st.column_config.NumberColumn(
                "حجم التداول",
                format="%d"
            )
        }
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config=column_config
        )
        
        # --- عرض أفضل 5 أسهم في بطاقات منفصلة ---
        if mover_type == "gainers" and len(df) >= 5:
            st.subheader("🏆 أفضل 5 أسهم صعوداً")
            
            top5 = df.head(5)
            cols = st.columns(5)
            
            for i, (_, row) in enumerate(top5.iterrows()):
                with cols[i]:
                    st.metric(
                        label=f"#{i+1} {row['ticker']}",
                        value=f"${row['last_price']:.2f}" if pd.notna(row['last_price']) else "N/A",
                        delta=f"{row['percent_change']:.2f}%" if pd.notna(row['percent_change']) else None
                    )
        
        # --- زر تحميل البيانات ---
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 تحميل البيانات (CSV)",
            data=csv,
            file_name=f"top_movers_{mover_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # --- وقت التحديث ---
        st.caption(f"🔄 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
else:
    st.info("👈 أدخل مفتاح API في الشريط الجانبي واضغط 'تحديث البيانات'")

# --- تعليمات إضافية في الشريط الجانبي ---
with st.sidebar:
    st.divider()
    st.markdown("### ℹ️ معلومات")
    st.markdown("""
    - **المصدر**: Benzinga Market Movers API [citation:3][citation:7]
    - **التغطية**: Wilshire 5000 + 1000 إضافية [citation:7]
    - **التحديث**: بيانات لحظية خلال جلسة التداول
    
    **للحصول على مفتاح API**:
    [Benzinga APIs](https://www.benzinga.com/apis/)
    """)
    
    st.markdown("### 📌 ملاحظات")
    st.markdown("""
    - تعرض الصفحة الأسهم ذات أعلى نسبة ارتفاع
    - يتم تحديث البيانات تلقائياً كل 5 دقائق
    - يمكنك تحميل البيانات بصيغة CSV
    """)
