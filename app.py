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
import pandas as pd
import yfinance as yf

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
        USE_REAL_DATA = True  # New setting to use real data
    
    config = Config()

# ============================================
# Real Data Functions
# ============================================

def get_real_market_data():
    """Get real market data from Yahoo Finance"""
    try:
        # Get major indices
        indices = {
            "NASDAQ": "^IXIC",
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI",
            "TASI": "^TASI"  # Saudi Tadawul
        }
        
        market_data = {}
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                price = info.get("lastPrice", 0)
                prev_close = info.get("previousClose", price)
                change = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                
                market_data[name] = {
                    "price": price,
                    "change": change,
                    "symbol": symbol
                }
            except:
                # Fallback data if Yahoo fails
                market_data[name] = {
                    "price": 0,
                    "change": 0,
                    "symbol": symbol
                }
        
        return market_data
    except Exception as e:
        st.error(f"❌ خطأ في تحميل بيانات السوق: {e}")
        return None

def get_real_top_stocks():
    """Get real top stocks from Yahoo Finance"""
    try:
        # Popular stocks
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", 
                   "JPM", "VTI", "2222.SR", "1120.SR", "7010.SR"]
        
        stocks_data = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                price = info.get("lastPrice", 0)
                prev_close = info.get("previousClose", price)
                change = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                
                stocks_data.append({
                    "symbol": symbol,
                    "price": price,
                    "change": change,
                    "volume": info.get("lastVolume", 0)
                })
            except:
                pass
        
        return stocks_data
    except Exception as e:
        st.error(f"❌ خطأ في تحميل بيانات الأسهم: {e}")
        return []

# ============================================
# Functions
# ============================================

def check_package(package_name: str) -> str:
    """Check if a Python package is installed."""
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
                .real-data-badge {
                    background: #22c55e;
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    display: inline-block;
                }
                .fallback-badge {
                    background: #f59e0b;
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    display: inline-block;
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
    
    if "market_data" not in st.session_state:
        st.session_state.market_data = None
    
    if "last_update" not in st.session_state:
        st.session_state.last_update = None

def get_market_status():
    """Determine market status based on time"""
    now = datetime.now()
    # Simple logic: markets are open Monday-Friday 9:30 AM - 4:00 PM ET
    # For simplicity, we'll just check if it's a weekday
    if now.weekday() < 5:  # Monday = 0, Sunday = 6
        return "🟢 مفتوح"
    else:
        return "🔴 مغلق"

def display_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #667eea; margin: 0;">📈 ByToBy Pro</h2>
            <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.25rem;">الإصدار {config.VERSION}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Data source indicator
        if hasattr(config, 'USE_REAL_DATA') and config.USE_REAL_DATA:
            st.markdown('<span class="real-data-badge">✅ بيانات حقيقية</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="fallback-badge">⚠️ بيانات تجريبية</span>', unsafe_allow_html=True)
        
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
        
        # Update market status
        st.session_state.market_status = get_market_status()
        
        # Market status
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**حالة السوق:**")
            st.markdown(f"{st.session_state.market_status}")
        with col2:
            st.markdown(f"**آخر تحديث:**")
            last_update = st.session_state.last_update
            if last_update:
                st.markdown(f"{last_update.strftime('%H:%M:%S')}")
            else:
                st.markdown("جاري التحميل...")
        
        # Auto refresh indicator
        if hasattr(config, 'AUTO_REFRESH_SECONDS') and config.AUTO_REFRESH_SECONDS > 0:
            st.caption(f"⏰ تحديث تلقائي كل {config.AUTO_REFRESH_SECONDS} ثانية")
        
        # System info
        with st.expander("ℹ️ نظام", expanded=False):
            st.caption(f"🐍 Python {sys.version[:10]}")
            st.caption(f"📦 Streamlit {st.__version__}")
            st.caption(f"📊 مصدر البيانات: {'Yahoo Finance (حقيقي)' if hasattr(config, 'USE_REAL_DATA') and config.USE_REAL_DATA else 'تجريبي'}")
    
    return selected

def display_header():
    """Display page header"""
    st.markdown(f'<div class="title">🚀 {config.APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">منصة احترافية لتحليل الأسهم الأمريكية والسعودية بالذكاء الاصطناعي</div>', unsafe_allow_html=True)
    st.markdown("---")

def display_top_metrics():
    """Display real top market metrics"""
    # Get real market data
    if hasattr(config, 'USE_REAL_DATA') and config.USE_REAL_DATA:
        market_data = get_real_market_data()
        st.session_state.market_data = market_data
        st.session_state.last_update = datetime.now()
    else:
        # Fallback sample data
        market_data = {
            "NASDAQ": {"price": 19245, "change": 1.12},
            "S&P 500": {"price": 6412, "change": 0.84},
            "Dow Jones": {"price": 44180, "change": 0.51},
            "TASI": {"price": 12480, "change": 0.67}
        }
    
    col1, col2, col3, col4 = st.columns(4)
    
    if market_data:
        with col1:
            if "NASDAQ" in market_data:
                price = market_data["NASDAQ"].get("price", 0)
                change = market_data["NASDAQ"].get("change", 0)
                st.metric("NASDAQ", f"{price:,.0f}", f"{change:+.2f}%")
            else:
                st.metric("NASDAQ", "N/A", "N/A")
        
        with col2:
            if "S&P 500" in market_data:
                price = market_data["S&P 500"].get("price", 0)
                change = market_data["S&P 500"].get("change", 0)
                st.metric("S&P 500", f"{price:,.0f}", f"{change:+.2f}%")
            else:
                st.metric("S&P 500", "N/A", "N/A")
        
        with col3:
            if "Dow Jones" in market_data:
                price = market_data["Dow Jones"].get("price", 0)
                change = market_data["Dow Jones"].get("change", 0)
                st.metric("Dow Jones", f"{price:,.0f}", f"{change:+.2f}%")
            else:
                st.metric("Dow Jones", "N/A", "N/A")
        
        with col4:
            if "TASI" in market_data:
                price = market_data["TASI"].get("price", 0)
                change = market_data["TASI"].get("change", 0)
                st.metric("TASI", f"{price:,.0f}", f"{change:+.2f}%")
            else:
                st.metric("TASI", "N/A", "N/A")
    else:
        for col in [col1, col2, col3, col4]:
            with col:
                st.metric("جاري التحميل...", "---", "---")
    
    st.markdown("---")

def navigate_to_page(page_name: str):
    """Navigate to a specific page"""
    try:
        # Remove emojis from page name for file path
        parts = page_name.split(" ")
        clean_name = parts[-1] if parts else page_name
        
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
            
            # Try to find similar pages
            pages_dir = Path("pages")
            if pages_dir.exists():
                available_pages = [p.stem for p in pages_dir.glob("*.py")]
                st.info(f"الصفحات المتاحة: {', '.join(available_pages)}")
    
    except Exception as e:
        st.error(f"❌ خطأ في التنقل: {str(e)}")

def display_footer():
    """Display footer"""
    st.markdown("---")
    st.caption(f"© 2026 {config.APP_NAME} — Powered by AI • Data: Yahoo Finance")

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
    
    # Top metrics with real data
    display_top_metrics()
    
    # Navigation
    try:
        # Check if we should navigate to a page
        if selected and selected != st.session_state.get('selected_page', ''):
            st.session_state.selected_page = selected
            navigate_to_page(selected)
        else:
            # If no page selected or same page, show Dashboard content
            if selected == "📊 Dashboard" or not selected:
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
                            استخدم القائمة الجانبية للتنقل بين الصفحات
                        </p>
                        <p style="color: #22c55e; font-size: 0.8rem;">
                            ✅ استخدام البيانات الحقيقية من Yahoo Finance
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
