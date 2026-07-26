# pages/Dashboard.py
"""
ByToBy Pro - Dashboard Page
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Import API
from api import get_dashboard_data, get_price

# =====================================================
# Main App
# =====================================================

def main():
    st.set_page_config(
        page_title="ByToBy Pro - Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 ByToBy Pro - Dashboard")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 بحث")
        symbol = st.text_input("رمز السهم", value="2222.SR")
        
        if st.button("🔄 تحميل", use_container_width=True):
            st.session_state['symbol'] = symbol
            st.rerun()
        
        st.markdown("---")
        st.markdown("### روابط سريعة")
        
        quick = {
            "🏢 أرامكو": "2222.SR",
            "🏦 الراجحي": "1120.SR",
            "📡 STC": "7010.SR",
            "🍎 Apple": "AAPL",
            "🚗 Tesla": "TSLA",
            "💻 Microsoft": "MSFT"
        }
        
        for name, sym in quick.items():
            if st.button(name, key=sym, use_container_width=True):
                st.session_state['symbol'] = sym
                st.rerun()
    
    # Initialize
    if 'symbol' not in st.session_state:
        st.session_state['symbol'] = "2222.SR"
    
    symbol = st.session_state['symbol']
    
    try:
        # Load data
        data = get_dashboard_data(symbol)
        
        if not data or not data.get('company'):
            st.error(f"❌ لا توجد بيانات للرمز {symbol}")
            return
        
        company = data['company']
        price = data['price']
        history = pd.DataFrame(data.get('history', []))
        
        # Show data source
        if data.get('source') == 'yahoo':
            st.success("✅ عرض بيانات حقيقية من Yahoo Finance")
        else:
            st.info("ℹ️ عرض بيانات تجريبية (تأكد من اتصال الإنترنت)")
        
        # Header
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"## 🏢 {company.get('companyName', symbol)}")
            st.markdown(f"**{company.get('sector', 'N/A')}** | {company.get('industry', 'N/A')}")
        
        with col2:
            st.metric("رمز السهم", symbol)
        
        with col3:
            current_price = price.get('price', 0)
            st.metric("السعر الحالي", f"${current_price:.2f}")
        
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
            
            fig.add_trace(
                go.Candlestick(
                    x=history['Date'],
                    open=history['Open'],
                    high=history['High'],
                    low=history['Low'],
                    close=history['Close'],
                    name="السعر"
                )
            )
            
            # Moving averages
            if len(history) > 20:
                ma20 = history['Close'].rolling(window=20).mean()
                fig.add_trace(
                    go.Scatter(
                        x=history['Date'],
                        y=ma20,
                        mode="lines",
                        name="MA 20",
                        line=dict(color="#FF6B35", width=1.5, dash="dash")
                    )
                )
            
            fig.update_layout(
                title=f"{company.get('companyName', symbol)} - تحليل السعر",
                xaxis_title="التاريخ",
                yaxis_title="السعر ($)",
                height=500,
                template="plotly_dark",
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("📊 لا توجد بيانات تاريخية")
        
        # Details
        with st.expander("📋 تفاصيل الشركة"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📝 الوصف**")
                st.write(company.get('description', 'لا يوجد وصف'))
            
            with col2:
                st.markdown("**🌐 الموقع**")
                st.markdown(f"[{company.get('website', 'N/A')}]({company.get('website', '#')})")
                
                st.markdown("**📊 معلومات إضافية**")
                st.json({
                    "القطاع": company.get('sector'),
                    "الصناعة": company.get('industry'),
                    "الدولة": company.get('country'),
                    "القيمة السوقية": f"${company.get('marketCap', 0):.2f}B",
                    "الموظفين": company.get('employees', 0)
                })
        
        st.caption(f"آخر تحديث: {data.get('last_updated', datetime.now().isoformat())[:19]}")
        
    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")
        st.info("💡 تأكد من صحة رمز السهم وحاول مرة أخرى")


if __name__ == "__main__":
    main()
