import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import xml.etree.ElementTree as ET

st.set_page_config(page_title="bz.LEHKFPWH4EKQTBUMQ5HJ5HW3ZABANSAJ", layout="wide")
st.title("📈 الأسهم التي فاقت توقعات الأرباح")

# --- إعدادات الشريط الجانبي ---
with st.sidebar:
    st.header("🔑 الإعدادات")
    api_key = st.text_input("🔐 مفتاح Benzinga API", type="default", 
                           help="أدخل مفتاح API من Benzinga")
    
    days_back = st.slider("عدد الأيام السابقة", 1, 30, 7)
    
    if st.button("🔄 جلب البيانات", type="primary"):
        if not api_key:
            st.error("⚠️ الرجاء إدخال مفتاح API")
            st.stop()
        else:
            st.session_state['api_key'] = api_key
            st.session_state['days_back'] = days_back
            st.rerun()

# --- دالة تحويل XML إلى DataFrame ---
def parse_benzinga_xml(xml_text):
    """تحويل استجابة XML من Benzinga إلى DataFrame"""
    try:
        root = ET.fromstring(xml_text)
        earnings_list = []
        
        # البحث عن عناصر earnings
        for item in root.findall(".//item"):
            earnings_item = {}
            
            # استخراج البيانات من XML
            for child in item:
                tag = child.tag
                text = child.text or ''
                
                # تحويل الأسماء إلى صيغة مناسبة
                if tag == 'id':
                    earnings_item['id'] = text
                elif tag == 'ticker':
                    earnings_item['ticker'] = text
                elif tag == 'exchange':
                    earnings_item['exchange'] = text
                elif tag == 'date':
                    earnings_item['date'] = text
                elif tag == 'eps_est':
                    earnings_item['eps_est'] = text
                elif tag == 'eps':
                    earnings_item['eps'] = text
                elif tag == 'eps_surprise_percent':
                    earnings_item['eps_surprise_percent'] = text
                elif tag == 'revenue_est':
                    earnings_item['revenue_est'] = text
                elif tag == 'revenue':
                    earnings_item['revenue'] = text
                elif tag == 'revenue_surprise_percent':
                    earnings_item['revenue_surprise_percent'] = text
                elif tag == 'period_year':
                    earnings_item['period_year'] = text
                elif tag == 'period_quarter':
                    earnings_item['period_quarter'] = text
                elif tag == 'importance':
                    earnings_item['importance'] = text
                elif tag == 'currency':
                    earnings_item['currency'] = text
            
            if earnings_item:
                earnings_list.append(earnings_item)
        
        if not earnings_list:
            return pd.DataFrame()
        
        # تحويل إلى DataFrame
        df = pd.DataFrame(earnings_list)
        
        # تحويل الأعمدة الرقمية
        for col in ['eps_est', 'eps', 'eps_surprise_percent', 'revenue_est', 'revenue', 'revenue_surprise_percent']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
        
    except ET.ParseError as e:
        st.error(f"❌ خطأ في تحليل XML: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ خطأ غير متوقع في تحليل XML: {e}")
        return pd.DataFrame()

# --- دالة جلب البيانات من Benzinga ---
@st.cache_data(ttl=3600)
def fetch_benzinga(api_key, days_back):
    """جلب بيانات الأرباح من Benzinga API"""
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    url = "https://api.benzinga.com/api/v2.1/calendar/earnings"
    
    params = {
        "token": api_key,
        "date_from": start_date,
        "date_to": end_date,
        "pagesize": 500  # زيادة عدد النتائج
    }
    
    # طلب JSON بوضوح
    headers = {
        "Accept": "application/json"  # هذا هو المفتاح لحل المشكلة!
    }
    
    try:
        with st.spinner(f"جاري جلب البيانات من {start_date} إلى {end_date}..."):
            response = requests.get(url, params=params, headers=headers, timeout=30)
        
        # التحقق من الاستجابة
        if response.status_code != 200:
            return pd.DataFrame(), f"❌ خطأ {response.status_code}: {response.text[:200]}"
        
        # التحقق من نوع المحتوى
        content_type = response.headers.get('content-type', '')
        
        if 'json' in content_type.lower():
            # معالجة JSON
            try:
                data = response.json()
                if "earnings" in data:
                    df = pd.DataFrame(data["earnings"])
                else:
                    return pd.DataFrame(), "⚠️ لم يتم العثور على بيانات"
            except json.JSONDecodeError:
                return pd.DataFrame(), "❌ فشل تحليل JSON"
                
        elif 'xml' in content_type.lower():
            # معالجة XML
            df = parse_benzinga_xml(response.text)
            if df.empty:
                return pd.DataFrame(), "⚠️ لم يتم العثور على بيانات في XML"
        else:
            # محاولة تخمين الصيغة
            try:
                data = response.json()
                if "earnings" in data:
                    df = pd.DataFrame(data["earnings"])
                else:
                    return pd.DataFrame(), f"⚠️ صيغة غير معروفة: {content_type}"
            except:
                return pd.DataFrame(), f"⚠️ صيغة غير معروفة: {content_type}"
        
        # تصفية الأسهم التي فاقت التوقعات
        if not df.empty and 'eps_surprise_percent' in df.columns:
            df['eps_surprise_percent'] = pd.to_numeric(df['eps_surprise_percent'], errors='coerce')
            
            # تصفية فقط الشركات التي فاقت التوقعات
            earnings_beats = df[df['eps_surprise_percent'] > 0].copy()
            
            if earnings_beats.empty:
                return earnings_beats, f"ℹ️ تم جلب {len(df)} شركة، ولكن لم توجد شركات فاقت التوقعات"
            
            # ترتيب حسب نسبة المفاجأة
            earnings_beats = earnings_beats.sort_values('eps_surprise_percent', ascending=False)
            
            return earnings_beats, f"✅ تم العثور على {len(earnings_beats)} شركة فاقت التوقعات من أصل {len(df)}"
        else:
            return df, f"✅ تم جلب {len(df)} شركة (لا توجد بيانات مفاجأة)"
        
    except requests.exceptions.Timeout:
        return pd.DataFrame(), "⏰ انتهى وقت الاتصال. حاول مرة أخرى."
    except requests.exceptions.ConnectionError:
        return pd.DataFrame(), "🔌 فشل الاتصال بالإنترنت."
    except Exception as e:
        return pd.DataFrame(), f"❌ خطأ غير متوقع: {str(e)}"

# --- عرض النتائج ---
if 'api_key' in st.session_state:
    df, message = fetch_benzinga(
        st.session_state['api_key'],
        st.session_state.get('days_back', 7)
    )
    
    # عرض الرسالة
    if "✅" in message:
        st.success(message)
    else:
        st.warning(message)
    
    # عرض البيانات إذا وجدت
    if not df.empty:
        # إحصائيات سريعة
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 عدد الشركات", len(df))
        
        if 'eps_surprise_percent' in df.columns:
            with col2:
                avg_surprise = df['eps_surprise_percent'].mean()
                st.metric("📈 متوسط المفاجأة", f"{avg_surprise:.2f}%")
            
            with col3:
                max_surprise = df['eps_surprise_percent'].max()
                if not df.empty:
                    top_ticker = df.loc[df['eps_surprise_percent'].idxmax(), 'ticker'] if 'ticker' in df.columns else 'N/A'
                    st.metric("🏆 أعلى مفاجأة", f"{top_ticker} (+{max_surprise:.2f}%)")
        
        # عرض الجدول
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "ticker": "رمز السهم",
                "date": "التاريخ",
                "eps_est": st.column_config.NumberColumn("التوقع", format="$%.2f"),
                "eps": st.column_config.NumberColumn("الفعلي", format="$%.2f"),
                "eps_surprise_percent": st.column_config.NumberColumn("نسبة المفاجأة", format="%.2f%%"),
                "exchange": "البورصة",
                "period_year": "السنة",
                "period_quarter": "الربع"
            }
        )
        
        # زر تحميل CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 تحميل النتائج (CSV)",
            data=csv,
            file_name=f"earnings_beats_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # عرض أفضل 5 شركات
        if 'eps_surprise_percent' in df.columns:
            st.subheader("🏆 أفضل 5 شركات من حيث نسبة المفاجأة")
            top5 = df.nlargest(5, 'eps_surprise_percent')[['ticker', 'eps_est', 'eps', 'eps_surprise_percent']]
            st.dataframe(top5, use_container_width=True)
else:
    st.info("👈 أدخل مفتاح API في الشريط الجانبي واضغط 'جلب البيانات'")

# --- تعليمات إضافية ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### ℹ️ معلومات")
    st.markdown("""
    - **المصدر**: Benzinga API
    - **نسبة المفاجأة**: `(الفعلي - التوقع) / |التوقع| * 100`
    - **البيانات**: الأرباح الفعلية > التوقعات
    
    **للحصول على مفتاح**: [Benzinga APIs](https://www.benzinga.com/apis/)
    """)
