# pages/Dashboard.py
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Import API
try:
    from api import get_dashboard_data
except ImportError as e:
    st.error(f"❌ خطأ في استيراد API: {e}")
    st.stop()

st.set_page_config(
    page_title="ByToBy Pro - Dashboard", 
    page_icon="📊", 
    layout="wide"
)

def main():
    st.title("📊 ByToBy Pro - Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("🔍 بحث")
        symbol = st.text_input("رمز السهم", value=st.session_state.get('symbol', "2222.SR"))
        
        if st.button("🔄 تحميل", use_container_width=True):
            st.session_state['symbol'] = symbol.strip().upper()
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
        
        # Use columns for better layout
        cols = st.columns(2)
        for i, (name, sym) in enumerate(quick.items()):
            with cols[i % 2]:
                if st.button(name, key=sym, use_container_width=True):
                    st.session_state['symbol'] = sym
                    st.rerun()
    
    # Initialize session state
    if 'symbol' not in st.session_state:
        st.session_state['symbol'] = "2222.SR"
    
    symbol = st.session_state['symbol']
    
    # Loading spinner
    with st.spinner(f"جاري تحميل بيانات {symbol}..."):
        try:
            data = get_dashboard_data(symbol)
            
            if not data or not data.get('company'):
                st.error(f"❌ لا توجد بيانات للرمز {symbol}")
                return
            
            company = data['company']
            price = data['price']
            history = pd.DataFrame(data.get('history', []))
            
            # Source indicator
            source = data.get('source', 'unknown')
            if source == 'yahoo':
                st.success("✅ بيانات حقيقية من Yahoo Finance")
            elif source == 'fallback':
                st.info("ℹ️ بيانات تجريبية (للتطوير)")
            else:
                st.warning(f"⚠️ مصدر البيانات: {source}")
            
            # Header
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                company_name = company.get('companyName', symbol)
                st.markdown(f"## 🏢 {company_name}")
                sector = company.get('sector', 'N/A')
                industry = company.get('industry', 'N/A')
                st.markdown(f"**{sector}** | {industry}")
            with col2:
                st.metric("رمز السهم", symbol)
            with col3:
                current_price = price.get('price', 0)
                currency = price.get('currency', 'USD')
                st.metric("السعر الحالي", f"{currency} {current_price:.2f}")
            
            st.divider()
            
            # Metrics
            cols = st.columns(4)
            market_cap = company.get('marketCap', 0)
            employees = company.get('employees', 0)
            volume = price.get('volume', 0)
            country = company.get('country', 'N/A')
            
            metrics = [
                ("📊 القيمة السوقية", f"${market_cap:.2f}B" if market_cap > 0 else "N/A"),
                ("👥 الموظفين", f"{employees:,}" if employees > 0 else "N/A"),
                ("📈 حجم التداول", f"{volume:,}" if volume > 0 else "N/A"),
                ("📍 الدولة", country)
            ]
            for i, (label, value) in enumerate(metrics):
                with cols[i]:
                    st.metric(label, value)
            
            st.divider()
            
            # Chart
            if not history.empty and len(history) > 1:
                try:
                    fig = go.Figure()
                    
                    # Candlestick chart
                    fig.add_trace(go.Candlestick(
                        x=history['Date'],
                        open=history['Open'],
                        high=history['High'],
                        low=history['Low'],
                        close=history['Close'],
                        name="السعر",
                        increasing_line_color='#00ff00',
                        decreasing_line_color='#ff0000'
                    ))
                    
                    # Moving averages
                    if len(history) > 20:
                        ma20 = history['Close'].rolling(20).mean()
                        fig.add_trace(go.Scatter(
                            x=history['Date'],
                            y=ma20,
                            mode="lines",
                            name="MA 20",
                            line=dict(color="#FF6B35", width=2)
                        ))
                    
                    if len(history) > 50:
                        ma50 = history['Close'].rolling(50).mean()
                        fig.add_trace(go.Scatter(
                            x=history['Date'],
                            y=ma50,
                            mode="lines",
                            name="MA 50",
                            line=dict(color="#FFD700", width=2)
                        ))
                    
                    fig.update_layout(
                        title=f"{company_name} - تحليل السعر",
                        height=500,
                        template="plotly_dark",
                        xaxis_rangeslider_visible=False,
                        yaxis_title="السعر",
                        xaxis_title="التاريخ",
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as chart_error:
                    st.warning(f"⚠️ تعذر عرض الرسم البياني: {chart_error}")
            else:
                st.info("ℹ️ لا توجد بيانات تاريخية كافية لعرض الرسم البياني")
            
            # Details
            with st.expander("📋 تفاصيل الشركة", expanded=False):
                description = company.get('description', 'لا يوجد وصف')
                if description:
                    st.write("**📝 الوصف**")
                    st.write(description)
                
                website = company.get('website', 'N/A')
                if website and website != 'N/A':
                    st.write(f"**🌐 الموقع:** [{website}]({website})")
                
                # Additional info
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**📅 آخر تحديث:**")
                    st.write(data.get('last_updated', datetime.now().isoformat())[:19])
                with col2:
                    st.write("**📊 مصدر البيانات:**")
                    st.write(source)
            
            # Footer
            st.divider()
            st.caption(f"تم التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء تحميل البيانات: {str(e)}")
            st.info("💡 تأكد من أن رمز السهم صحيح وحاول مرة أخرى")

if __name__ == "__main__":
    main()
