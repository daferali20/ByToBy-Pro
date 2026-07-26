# pages/Dashboard.py
"""
ByToBy Pro - Dashboard Page
"""

import sys
import os
from pathlib import Path

# 🔧 Fix: Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import numpy as np  # ⚠️ أضف هذا السطر
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Import API - with error handling
try:
    from api.yahoo_api import YahooAPI
    from api import get_company_info, get_price, get_history, get_dashboard_data
    API_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ خطأ في الاستيراد: {e}")
    API_AVAILABLE = False
    
    # Create dummy functions for development
    def get_company_info(symbol):
        return {
            "companyName": f"شركة {symbol}",
            "sector": "الطاقة",
            "industry": "النفط والغاز",
            "marketCap": 7500.0,
            "employees": 70000,
            "country": "السعودية",
            "website": "https://example.com",
            "description": "هذه شركة نموذجية للعرض"
        }
    
    def get_price(symbol):
        return {
            "symbol": symbol,
            "price": 100.50,
            "open": 99.00,
            "high": 102.00,
            "low": 98.50,
            "volume": 1000000,
            "market_cap": 750000000000,
            "currency": "USD"
        }
    
    def get_history(symbol, period="6mo", interval="1d"):
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        return pd.DataFrame({
            'Date': dates,
            'Open': 100 + np.random.randn(100) * 2,
            'High': 102 + np.random.randn(100) * 2,
            'Low': 98 + np.random.randn(100) * 2,
            'Close': 100 + np.random.randn(100) * 2,
            'Volume': np.random.randint(100000, 1000000, 100)
        })
    
    def get_dashboard_data(symbol):
        return {
            "company": get_company_info(symbol),
            "price": get_price(symbol),
            "history": get_history(symbol),
            "dividends": [],
            "last_updated": datetime.now().isoformat()
        }

# =====================================================
# Dashboard Class
# =====================================================

class Dashboard:
    """Main Dashboard class for displaying company data."""
    
    def __init__(self, symbol: str = None):
        self.symbol = symbol
        self.data = None
        self.api = YahooAPI() if API_AVAILABLE else None
        
        self.config = {
            "chart_height": 500,
            "chart_colors": {
                "primary": "#00B386",
                "secondary": "#FF6B35",
                "volume": "#1E88E5",
                "positive": "#00C853",
                "negative": "#FF1744"
            }
        }
        
        if symbol:
            self.load_company(symbol)
    
    def load_company(self, symbol: str) -> bool:
        """Load company data."""
        try:
            self.symbol = symbol
            data = get_dashboard_data(symbol)
            self.data = data
            return True
        except Exception as e:
            st.error(f"❌ خطأ: {e}")
            self.data = None
            return False
    
    def update_price(self) -> bool:
        """Update current price."""
        try:
            if self.symbol and self.data:
                price_data = get_price(self.symbol)
                self.data['price'] = price_data
                return True
        except Exception:
            pass
        return False
    
    def get_price_change(self) -> float:
        """Calculate price change."""
        if not self.data:
            return 0.0
        
        price = self.data.get('price', {}).get('price', 0)
        history = pd.DataFrame(self.data.get('history', []))
        
        if history.empty or len(history) < 2:
            return 0.0
        
        prev_close = history.iloc[-2]['Close'] if len(history) >= 2 else price
        
        if prev_close == 0:
            return 0.0
        
        return ((price - prev_close) / prev_close) * 100
    
    def create_price_chart(self, period: str = "6mo", chart_type: str = "candlestick") -> go.Figure:
        """Create price chart."""
        if not self.data:
            return self._empty_chart("لا توجد بيانات")
        
        history = pd.DataFrame(self.data.get('history', []))
        
        if history.empty:
            return self._empty_chart("لا توجد بيانات تاريخية")
        
        fig = go.Figure()
        
        if chart_type == "candlestick":
            fig.add_trace(
                go.Candlestick(
                    x=history['Date'],
                    open=history['Open'],
                    high=history['High'],
                    low=history['Low'],
                    close=history['Close'],
                    name="السعر",
                    increasing_line_color="#00C853",
                    decreasing_line_color="#FF1744"
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=history['Date'],
                    y=history['Close'],
                    mode="lines",
                    name="سعر الإغلاق",
                    line=dict(color="#00B386", width=2)
                )
            )
        
        # Add moving averages
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
        
        if len(history) > 50:
            ma50 = history['Close'].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=history['Date'],
                    y=ma50,
                    mode="lines",
                    name="MA 50",
                    line=dict(color="#1E88E5", width=1.5, dash="dot")
                )
            )
        
        company_name = self.data.get('company', {}).get('companyName', self.symbol)
        
        fig.update_layout(
            title=f"{company_name} - تحليل السعر",
            xaxis_title="التاريخ",
            yaxis_title="السعر ($)",
            height=self.config["chart_height"],
            template="plotly_dark",
            hovermode="x unified",
            xaxis_rangeslider_visible=False,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        return fig
    
    def _empty_chart(self, message: str) -> go.Figure:
        """Create empty chart."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="#888")
        )
        fig.update_layout(
            height=300,
            template="plotly_dark",
            margin=dict(l=40, r=40, t=40, b=40)
        )
        return fig
    
    # =====================================================
    # Render Methods
    # =====================================================
    
    def render_header(self):
        """Render company header."""
        if not self.data:
            st.warning("⚠️ لم يتم تحميل البيانات")
            return
        
        company = self.data.get('company', {})
        price = self.data.get('price', {})
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"## 🏢 {company.get('companyName', 'N/A')}")
            st.markdown(f"**{company.get('sector', 'N/A')}** | {company.get('industry', 'N/A')}")
        
        with col2:
            st.metric(
                label="رمز السهم",
                value=self.symbol
            )
        
        with col3:
            current_price = price.get('price', 0)
            change = self.get_price_change()
            st.metric(
                label="السعر الحالي",
                value=f"${current_price:.2f}",
                delta=f"{change:.2f}%",
                delta_color="normal"
            )
    
    def render_metrics(self):
        """Render metrics cards."""
        if not self.data:
            return
        
        company = self.data.get('company', {})
        price = self.data.get('price', {})
        
        metrics = [
            ("📊 القيمة السوقية", f"${company.get('marketCap', 0):.2f}B"),
            ("👥 عدد الموظفين", f"{company.get('employees', 0):,}"),
            ("💰 السعر الحالي", f"${price.get('price', 0):.2f}"),
            ("📈 حجم التداول", f"{price.get('volume', 0):,}"),
            ("⬆️ أعلى اليوم", f"${price.get('high', 0):.2f}"),
            ("⬇️ أدنى اليوم", f"${price.get('low', 0):.2f}"),
            ("🏗️ القطاع", company.get('sector', 'N/A')),
            ("📍 الدولة", company.get('country', 'N/A'))
        ]
        
        cols = st.columns(4)
        for idx, (label, value) in enumerate(metrics):
            with cols[idx % 4]:
                st.metric(label=label, value=value)
    
    def render_chart(self):
        """Render price chart."""
        if not self.data:
            st.warning("📊 لا توجد بيانات")
            return
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            period = st.selectbox(
                "الفترة",
                options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
                index=4
            )
        
        with col2:
            chart_type = st.selectbox(
                "نوع الرسم",
                options=["candlestick", "line"],
                index=0
            )
        
        fig = self.create_price_chart(period=period, chart_type=chart_type)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_details(self):
        """Render company details."""
        if not self.data:
            return
        
        company = self.data.get('company', {})
        
        with st.expander("📋 تفاصيل الشركة", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📝 وصف الشركة**")
                st.write(company.get('description', 'لا يوجد وصف'))
                
                st.markdown("**🌐 الموقع الإلكتروني**")
                st.markdown(f"[{company.get('website', 'N/A')}]({company.get('website', '#')})")
            
            with col2:
                st.markdown("**📊 معلومات إضافية**")
                details = {
                    "الدولة": company.get('country', 'N/A'),
                    "القطاع": company.get('sector', 'N/A'),
                    "الصناعة": company.get('industry', 'N/A'),
                    "القيمة السوقية": f"${company.get('marketCap', 0):.2f}B",
                    "عدد الموظفين": f"{company.get('employees', 0):,}"
                }
                for key, value in details.items():
                    st.markdown(f"**{key}:** {value}")
    
    def render_all(self):
        """Render complete dashboard."""
        if not self.data:
            st.error("❌ فشل تحميل بيانات الشركة")
            st.info("💡 تأكد من صحة رمز السهم وحاول مرة أخرى")
            return
        
        tabs = st.tabs(["📊 نظرة عامة", "📈 تحليل السعر", "📋 معلومات الشركة"])
        
        with tabs[0]:
            self.render_header()
            st.divider()
            self.render_metrics()
            st.divider()
            
            # Quick chart
            fig = self.create_price_chart(period="1mo", chart_type="line")
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show additional metrics
            col1, col2 = st.columns(2)
            with col1:
                if self.data and not pd.DataFrame(self.data.get('history', [])).empty:
                    history = pd.DataFrame(self.data.get('history', []))
                    st.metric("أعلى سعر خلال الفترة", f"${history['High'].max():.2f}")
                    st.metric("أدنى سعر خلال الفترة", f"${history['Low'].min():.2f}")
            
            with col2:
                if self.data:
                    st.metric("آخر تحديث", self.data.get('last_updated', 'N/A')[:19])
        
        with tabs[1]:
            self.render_chart()
        
        with tabs[2]:
            self.render_details()
    
    def render_sidebar(self):
        """Render sidebar with controls."""
        with st.sidebar:
            st.title("📊 ByToBy Pro")
            st.markdown("---")
            
            symbol = st.text_input(
                "🔍 رمز السهم",
                value=self.symbol or "2222.SR"
            )
            
            if st.button("🔄 تحميل", use_container_width=True):
                st.session_state['symbol'] = symbol
                st.rerun()
            
            st.markdown("---")
            st.markdown("### 🔗 روابط سريعة")
            
            quick_symbols = [
                ("🏢 أرامكو", "2222.SR"),
                ("🏦 الراجحي", "1120.SR"),
                ("📡 STC", "7010.SR"),
                ("🍎 Apple", "AAPL"),
                ("🚗 Tesla", "TSLA"),
                ("💻 Microsoft", "MSFT")
            ]
            
            for name, sym in quick_symbols:
                if st.button(name, key=sym, use_container_width=True):
                    st.session_state['symbol'] = sym
                    st.rerun()
            
            st.markdown("---")
            
            if st.button("🔄 تحديث البيانات", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
            
            st.info("ℹ️ يتم تحديث البيانات تلقائياً")
            
            # Display API status
            if API_AVAILABLE:
                st.success("✅ API متصلة")
            else:
                st.warning("⚠️ وضع التجربة - بيانات وهمية")


# =====================================================
# Main App
# =====================================================

def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="ByToBy Pro - Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'symbol' not in st.session_state:
        st.session_state['symbol'] = "2222.SR"
    
    # Create dashboard
    dashboard = Dashboard(st.session_state['symbol'])
    
    # Render sidebar
    dashboard.render_sidebar()
    
    # Render main content
    dashboard.render_all()


# =====================================================
# Entry Point
# =====================================================

if __name__ == "__main__":
    main()
