# pages/Dashboard.py
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Import API
from api import get_dashboard_data

st.set_page_config(page_title="ByToBy Pro - Dashboard", page_icon="📊", layout="wide")

def main():
    st.title("📊 ByToBy Pro - Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 بحث")
        symbol = st.text_input("رمز السهم", value="2222.SR")
        
        if st.button("🔄 تحميل"):
            st.session_state['symbol'] = symbol
            st.rerun()
        
        st.markdown("---")
        st.markdown("### روابط سريعة")
        
        quick = {
            "🏢 أرامكو": "2222.SR",
            "🏦 الراجحي": "1120.SR",
            "📡 STC": "7010.SR",
            "🍎 Apple": "AAPL",
            "🚗 Tesla": "TSLA"
        }
        
        for name, sym in quick.items():
            if st.button(name, key=sym):
                st.session_state['symbol'] = sym
                st.rerun()
    
    # Initialize
    if 'symbol' not in st.session_state:
        st.session_state['symbol'] = "2222.SR"
    
    symbol = st.session_state['symbol']
    
    try:
        data = get_dashboard_data(symbol)
        
        if not data or not data.get('company'):
            st.error(f"❌ لا توجد بيانات للرمز {symbol}")
            return
        
        company = data['company']
        price = data['price']
        history = pd.DataFrame(data.get('history', []))
        
        # Source indicator
        if data.get('source') == 'yahoo':
            st.success("✅ بيانات حقيقية من Yahoo Finance")
        else:
            st.info("ℹ️ بيانات تجريبية (للتطوير)")
        
        # Header
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"## 🏢 {company.get('companyName', symbol)}")
            st.markdown(f"**{company.get('sector', 'N/A')}** | {company.get('industry', 'N/A')}")
        with col2:
            st.metric("رمز السهم", symbol)
        with col3:
            st.metric("السعر الحالي", f"${price.get('price', 0):.2f}")
        
        st.divider()
        
        # Metrics
        cols = st.columns(4)
        metrics = [
            ("📊 القيمة السوقية", f"${company.get('marketCap', 0):.2f}B"),
            ("👥 الموظفين", f"{company.get('employees', 0):,}"),
            ("📈 حجم التداول", f"{price.get('volume', 0):,}"),
            ("📍 الدولة", company.get('country', 'N/A'))
        ]
        for i, (label, value) in enumerate(metrics):
            with cols[i]:
                st.metric(label, value)
        
        st.divider()
        
        # Chart
        if not history.empty:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=history['Date'],
                open=history['Open'],
                high=history['High'],
                low=history['Low'],
                close=history['Close'],
                name="السعر"
            ))
            
            if len(history) > 20:
                ma20 = history['Close'].rolling(20).mean()
                fig.add_trace(go.Scatter(
                    x=history['Date'],
                    y=ma20,
                    mode="lines",
                    name="MA 20",
                    line=dict(color="#FF6B35", dash="dash")
                ))
            
            fig.update_layout(
                title=f"{company.get('companyName', symbol)} - تحليل السعر",
                height=500,
                template="plotly_dark",
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Details
        with st.expander("📋 تفاصيل الشركة"):
            st.write("**📝 الوصف**")
            st.write(company.get('description', 'لا يوجد وصف'))
            st.write(f"**🌐 الموقع:** [{company.get('website', 'N/A')}]({company.get('website', '#')})")
        
        st.caption(f"آخر تحديث: {data.get('last_updated', datetime.now().isoformat())[:19]}")
        
    except Exception as e:
        st.error(f"❌ خطأ: {str(e)}")

if __name__ == "__main__":
    main()
