# app.py
from __future__ import annotations

from datetime import datetime
import subprocess
import sys
import os
from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh

# ============================================
# Configuration handling
# ============================================
try:
    from config import config
except ImportError:
    # Create a simple config class if config.py doesn't exist
    class Config:
        APP_NAME = "ByToBy Pro"
        VERSION = "1.0.0"
        AUTO_REFRESH_SECONDS = 30
        THEME = "dark"
    
    config = Config()

# ============================================
# Functions
# ============================================

def check_package(package_name: str) -> str:
    """
    Check if a Python package is installed.
    """
    try:
        __import__(package_name)
        return f"✅ {package_name} installed"
    except ImportError:
        return f"❌ {package_name} NOT installed"

def load_css():
    """Load custom CSS styles"""
    try:
        css_path = Path('.streamlit/styles.css')
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                css = f.read()
                st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
        else:
            # Fallback styles
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
    except Exception as e:
        st.warning(f"⚠️ Could not load CSS: {e}")

def init_session_state():
    """Initialize session state variables"""
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = ["AAPL", "NVDA", "TSLA", "MSFT", "2222.SR"]
    
    if "alerts" not in st.session_state:
        st.session_state.alerts = []
    
    if "market_status" not in st.session_state:
        st.session_state.market_status = "🟢 مفتوح"
    
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Dashboard"

def display_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #667eea; margin: 0;">📈 ByToBy Pro</h2>
            <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.25rem;">الإصدار {config.VERSION}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation menu
        selected = option_menu(
            menu_title="القائمة الرئيسية",
            options=[
                "📊 Dashboard",
                "🔍 Smart Screener",
                "🤖 AI Recommendations",
                "📰 News",
                "🔥 HeatMap",
                "💰 Portfolio",
                "⭐ Watchlist",
                "🔔 Alerts",
                "⚙️ Settings",
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
            styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "transparent"
                },
                "icon": {
                    "color": "#667eea",
                    "font-size": "20px"
                },
                "nav-link": {
                    "font-size": "15px",
                    "text-align": "right",
                    "margin": "5px 0",
                    "padding": "10px 15px",
                    "border-radius": "10px",
                    "color": "#94a3b8",
                    "transition": "all 0.3s ease"
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2))",
                    "color": "#ffffff",
                    "border": "1px solid rgba(102, 126, 234, 0.3)",
                    "font-weight": "600"
                },
                "nav-link-hover": {
                    "background": "rgba(102, 126, 234, 0.05)",
                    "color": "#ffffff"
                }
            }
        )
        
        st.markdown("---")
        
        # Market status
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**حالة السوق:**")
            st.markdown(f"{st.session_state.market_status}")
        with col2:
            st.markdown(f"**آخر تحديث:**")
            st.markdown(f"{datetime.now().strftime('%H:%M:%S')}")
        
        # Auto refresh indicator
        if hasattr(config, 'AUTO_REFRESH_SECONDS') and config.AUTO_REFRESH_SECONDS > 0:
            st.caption(f"⏰ تحديث تلقائي كل {config.AUTO_REFRESH_SECONDS} ثانية")
        
        # System info
        with st.expander("ℹ️ نظام", expanded=False):
            st.caption(f"🐍 Python {sys.version[:10]}")
            st.caption(f"📦 Streamlit {st.__version__}")
    
    return selected

def display_header():
    """Display page header"""
    st.markdown(f'<div class="title">🚀 {config.APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">منصة احترافية لتحليل الأسهم الأمريكية والسعودية بالذكاء الاصطناعي</div>', unsafe_allow_html=True)
    st.markdown("---")

def display_top_metrics():
    """Display top market metrics"""
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

def navigate_to_page(page_name: str):
    """Navigate to a specific page"""
    try:
        # Remove emojis from page name for file path
        clean_name = page_name.split(" ")[-1] if " " in page_name else page_name
        
        # Map display names to file names
        page_map = {
            "Dashboard": "Dashboard",
            "Smart Screener": "Smart_Screener",
            "AI Recommendations": "AI_Recommendations",
            "News": "News",
            "HeatMap": "HeatMap2",
            "Portfolio": "Portfolio",
            "Watchlist": "Watchlist",
            "Alerts": "Alerts",
            "Settings": "Settings"
        }
        
        # Get the actual file name
        file_name = page_map.get(clean_name, clean_name)
        
        # Check if page file exists
        page_path = Path(f"pages/{file_name}.py")
        if page_path.exists():
            st.switch_page(f"pages/{file_name}.py")
        else:
            st.warning(f"⚠️ الصفحة {page_name} غير موجودة")
            st.info(f"البحث عن: pages/{file_name}.py")
            
            # Try to find similar pages
            pages_dir = Path("pages")
            if pages_dir.exists():
                available_pages = [p.stem for p in pages_dir.glob("*.py")]
                st.write("الصفحات المتاحة:", available_pages)
    
    except Exception as e:
        st.error(f"❌ خطأ في التنقل: {str(e)}")

def display_footer():
    """Display footer"""
    st.markdown("---")
    st.caption(f"© 2026 {config.APP_NAME} — Powered by AI • Polygon • Finnhub • Yahoo Finance")

# ============================================
# Main App
# ============================================

def main():
    """Main application entry point"""
    
    # Load CSS
    load_css()
    
    # Initialize session state
    init_session_state()
    
    # Auto refresh
    if hasattr(config, 'AUTO_REFRESH_SECONDS') and config.AUTO_REFRESH_SECONDS > 0:
        st_autorefresh(
            interval=config.AUTO_REFRESH_SECONDS * 1000,
            key="market_refresh"
        )
    
    # Check packages (optional - uncomment if needed)
    # st.write(check_package("streamlit_option_menu"))
    # st.write(check_package("streamlit_autorefresh"))
    
    # Set page config
    st.set_page_config(
        page_title=f"{config.APP_NAME} v{config.VERSION}",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar
    selected = display_sidebar()
    
    # Header
    display_header()
    
    # Top metrics
    display_top_metrics()
    
    # Navigation
    try:
        # Check if we should navigate to a page
        if selected and selected != st.session_state.get('selected_page', ''):
            st.session_state.selected_page = selected
            navigate_to_page(selected)
        else:
            # If no page selected or same page, show Dashboard by default
            if selected == "📊 Dashboard" or not selected:
                # Import and show dashboard content directly
                try:
                    from pages.Dashboard import main as dashboard_main
                    dashboard_main()
                except ImportError:
                    st.info("💡 الصفحة الرئيسية قيد التحميل...")
                    st.markdown("""
                    <div style="text-align: center; padding: 3rem;">
                        <h2 style="color: #667eea;">📊 Dashboard</h2>
                        <p style="color: #94a3b8;">مرحباً بك في منصة ByToBy Pro</p>
                        <p style="color: #64748b; font-size: 0.9rem;">
                            اختر صفحة من القائمة الجانبية للبدء
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")
        st.info("💡 تأكد من وجود جميع ملفات الصفحات في مجلد 'pages'")
    
    # Footer
    display_footer()

# ============================================
# Entry point
# ============================================

if __name__ == "__main__":
    main()
