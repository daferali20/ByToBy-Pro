from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

from config import config
import subprocess
import sys

def check_package(package_name):
    try:
        __import__(package_name)
        return f"✅ {package_name} installed"
    except ImportError:
        return f"❌ {package_name} NOT installed"

# التحقق من المكتبات المهمة
st.write(check_package("streamlit_option_menu"))
st.write(check_package("streamlit_autorefresh"))
# =============================
# Page Config
# =============================
st.set_page_config(
    page_title=f"{config.APP_NAME} v{config.VERSION}",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================
# Custom Theme
# =============================
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
    }

    .stApp {
        background-color: #0f172a;
        color: white;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #111827 100%);
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .title {
        font-size: 2rem;
        font-weight: 700;
        color: #f8fafc;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# Session State
# =============================
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "NVDA", "TSLA", "MSFT"]

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "market_status" not in st.session_state:
    st.session_state.market_status = "🟢 مفتوح"

# =============================
# Auto Refresh
# =============================
st_autorefresh(interval=config.AUTO_REFRESH_SECONDS * 1000, key="market_refresh")

# =============================
# Sidebar
# =============================
with st.sidebar:
    st.markdown("# 📈 ByToBy Pro")
    st.caption(f"الإصدار {config.VERSION}")

    selected = option_menu(
        menu_title="القائمة الرئيسية",
        options=[
            "Dashboard",
            "Smart Screener",
            "AI Recommendations",
            "News",
            "HeatMap",
            "Portfolio",
            "Watchlist",
            "Alerts",
            "Settings",
        ],
        icons=[
            "speedometer2",
            "search",
            "cpu",
            "newspaper",
            "grid-3x3-gap",
            "wallet2",
            "star",
            "bell",
            "gear",
        ],
        menu_icon="cast",
        default_index=0,
    )

    st.markdown("---")
    st.markdown(f"**حالة السوق:** {st.session_state.market_status}")
    st.markdown(f"**آخر تحديث:** {datetime.now().strftime('%H:%M:%S')}")

# =============================
# Header
# =============================
st.markdown(f'<div class="title">🚀 {config.APP_NAME}</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">منصة احترافية لتحليل الأسهم الأمريكية والسعودية بالذكاء الاصطناعي</div>', unsafe_allow_html=True)
st.markdown("---")

# =============================
# Top Metrics
# =============================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("NASDAQ", "19,245", "+1.12%")

with col2:
    st.metric("S&P 500", "6,412", "+0.84%")

with col3:
    st.metric("Dow Jones", "44,180", "+0.51%")

with col4:
    st.metric("TASI", "12,480", "+0.67%")

st.markdown("---")

# =============================
# Navigation Router
# =============================
if selected == "Dashboard":
    st.switch_page("pages/Dashboard.py")

elif selected == "Smart Screener":
    st.switch_page("pages/Smart_Screener.py")

elif selected == "AI Recommendations":
    st.switch_page("pages/AI_Recommendations.py")

elif selected == "News":
    st.switch_page("pages/News.py")

elif selected == "HeatMap":
    st.switch_page("pages/HeatMap.py")

elif selected == "Portfolio":
    st.switch_page("pages/Portfolio.py")

elif selected == "Watchlist":
    st.switch_page("pages/Watchlist.py")

elif selected == "Alerts":
    st.switch_page("pages/Alerts.py")

elif selected == "Settings":
    st.switch_page("pages/Settings.py")

# =============================
# Footer
# =============================
st.markdown("---")
st.caption(f"© 2026 {config.APP_NAME} — Powered by AI • Polygon • Finnhub • Yahoo Finance")
