# محتوى الصفحة هنا
# Dashboard.py
"""
ByToBy Pro - Dashboard Page
====================================

This module handles the Dashboard page functionality including:
- Company overview with key metrics
- Stock price chart with interactive controls
- Company details and statistics
- Real-time data updates
- Responsive design for all screen sizes

Usage:
    from Dashboard import Dashboard
    
    # Initialize dashboard
    dashboard = Dashboard()
    
    # Load company data
    dashboard.load_company("2222.SR")
    
    # Get dashboard data
    data = dashboard.get_dashboard_data()
    
    # Update price (real-time)
    dashboard.update_price()
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Import API layer
from api import (
    get_company_info,
    get_price,
    get_history,
    get_dashboard_data,
    YahooAPI
)

# Import utilities
from utils.logger import get_logger
from utils.cache import cached

# Initialize logger
logger = get_logger("Dashboard")


# =====================================================
# Data Classes
# =====================================================

@dataclass
class DashboardData:
    """Structured dashboard data."""
    symbol: str
    company: Dict[str, Any]
    price: Dict[str, Any]
    history: pd.DataFrame
    dividends: pd.DataFrame = field(default_factory=pd.DataFrame)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_price_change(self) -> float:
        """Calculate price change percentage."""
        if self.history.empty or len(self.history) < 2:
            return 0.0
        
        current = self.price.get("price", 0)
        prev_close = self.history.iloc[-2]["Close"] if len(self.history) >= 2 else current
        
        if prev_close == 0:
            return 0.0
        
        return ((current - prev_close) / prev_close) * 100
    
    def get_high_low(self) -> Tuple[float, float]:
        """Get 52-week high and low."""
        if self.history.empty:
            return (0, 0)
        
        return (
            self.history["High"].max(),
            self.history["Low"].min()
        )
    
    def get_volume_avg(self) -> float:
        """Get average volume."""
        if self.history.empty:
            return 0.0
        
        return self.history["Volume"].mean()


# =====================================================
# Dashboard Class
# =====================================================

class Dashboard:
    """
    Main Dashboard class for displaying company data.
    
    Features:
    - Company profile with key metrics
    - Interactive price chart
    - Volume analysis
    - Price alerts
    - Real-time updates
    """
    
    def __init__(self, symbol: str = None):
        """
        Initialize Dashboard.
        
        Parameters
        ----------
        symbol : str, optional
            Initial stock symbol to load
        """
        self.symbol = symbol
        self.data: Optional[DashboardData] = None
        self.api = YahooAPI()
        
        # Dashboard configuration
        self.config = {
            "chart_height": 500,
            "chart_colors": {
                "primary": "#00B386",
                "secondary": "#FF6B35",
                "volume": "#1E88E5",
                "positive": "#00C853",
                "negative": "#FF1744"
            },
            "update_interval": 30,  # seconds
            "max_history_days": 365,
            "default_period": "6mo",
            "default_interval": "1d"
        }
        
        # Chart periods
        self.periods = {
            "1 يوم": "1d",
            "5 أيام": "5d",
            "شهر واحد": "1mo",
            "3 أشهر": "3mo",
            "6 أشهر": "6mo",
            "سنة واحدة": "1y",
            "سنتين": "2y",
            "5 سنوات": "5y",
            "الكل": "max"
        }
        
        # Chart intervals
        self.intervals = {
            "دقيقة": "1m",
            "5 دقائق": "5m",
            "15 دقيقة": "15m",
            "ساعة": "1h",
            "يومي": "1d",
            "أسبوعي": "1wk",
            "شهري": "1mo"
        }
        
        # Load initial data if symbol provided
        if symbol:
            self.load_company(symbol)
        
        logger.info(f"Dashboard initialized for {symbol or 'no symbol'}")
    
    # =====================================================
    # Data Loading Methods
    # =====================================================
    
    @cached(ttl=60)
    def load_company(self, symbol: str) -> bool:
        """
        Load company data for dashboard.
        
        Parameters
        ----------
        symbol : str
            Stock symbol to load
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        try:
            self.symbol = symbol
            
            # Get dashboard data
            data = get_dashboard_data(symbol)
            
            # Create DashboardData object
            self.data = DashboardData(
                symbol=symbol,
                company=data.get("company", {}),
                price=data.get("price", {}),
                history=pd.DataFrame(data.get("history", [])),
                dividends=pd.DataFrame(data.get("dividends", [])),
                last_updated=data.get("last_updated", datetime.now().isoformat())
            )
            
            logger.info(f"Dashboard data loaded for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load dashboard data: {e}")
            self.data = None
            return False
    
    @cached(ttl=20)
    def update_price(self) -> bool:
        """
        Update only the price data (faster than full reload).
        
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not self.symbol:
            return False
        
        try:
            price_data = get_price(self.symbol)
            if self.data:
                self.data.price = price_data
                self.data.last_updated = datetime.now().isoformat()
            
            logger.info(f"Price updated for {self.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update price: {e}")
            return False
    
    @cached(ttl=300)
    def refresh_history(self, period: str = "6mo", interval: str = "1d") -> bool:
        """
        Refresh historical data with new period/interval.
        
        Parameters
        ----------
        period : str
            Data period (1d, 5d, 1mo, etc.)
        interval : str
            Data interval (1m, 5m, 1d, etc.)
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not self.symbol:
            return False
        
        try:
            history = get_history(self.symbol, period=period, interval=interval)
            if self.data:
                self.data.history = history
                self.data.last_updated = datetime.now().isoformat()
            
            logger.info(f"History refreshed for {self.symbol} ({period}, {interval})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh history: {e}")
            return False
    
    # =====================================================
    # Data Access Methods
    # =====================================================
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get complete dashboard data.
        
        Returns
        -------
        Dict[str, Any]
            Complete dashboard data
        """
        if not self.data:
            return {}
        
        return {
            "symbol": self.data.symbol,
            "company": self.data.company,
            "price": self.data.price,
            "history": self.data.history.to_dict('records') if not self.data.history.empty else [],
            "dividends": self.data.dividends.to_dict('records') if not self.data.dividends.empty else [],
            "last_updated": self.data.last_updated
        }
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get company information."""
        return self.data.company if self.data else {}
    
    def get_price_data(self) -> Dict[str, Any]:
        """Get current price data."""
        return self.data.price if self.data else {}
    
    def get_history_data(self) -> pd.DataFrame:
        """Get historical data."""
        return self.data.history if self.data else pd.DataFrame()
    
    def get_key_metrics(self) -> Dict[str, Any]:
        """Get key metrics for display."""
        if not self.data:
            return {}
        
        company = self.data.company
        price = self.data.price
        
        return {
            "القيمة السوقية": f"${company.get('marketCap', 0):.2f}B",
            "عدد الموظفين": f"{company.get('employees', 0):,}",
            "السعر الحالي": f"${price.get('price', 0):.2f}",
            "أعلى اليوم": f"${price.get('high', 0):.2f}",
            "أدنى اليوم": f"${price.get('low', 0):.2f}",
            "حجم التداول": f"{price.get('volume', 0):,}",
            "القطاع": company.get('sector', 'N/A'),
            "الدولة": company.get('country', 'N/A'),
            "العملة": price.get('currency', 'USD')
        }
    
    # =====================================================
    # Chart Generation Methods
    # =====================================================
    
    def create_price_chart(
        self,
        period: str = "6mo",
        interval: str = "1d",
        chart_type: str = "candlestick",
        show_volume: bool = True
    ) -> go.Figure:
        """
        Create interactive price chart.
        
        Parameters
        ----------
        period : str
            Data period
        interval : str
            Data interval
        chart_type : str
            Chart type: 'candlestick', 'line', 'area'
        show_volume : bool
            Show volume subplot
            
        Returns
        -------
        go.Figure
            Plotly figure object
        """
        # Get data
        df = self.get_history_data()
        
        if df.empty:
            return self._create_empty_chart("لا توجد بيانات متاحة")
        
        # Create figure with secondary y-axis
        if show_volume:
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.7, 0.3],
                subplot_titles=(f"السعر - {self.symbol}", "حجم التداول")
            )
        else:
            fig = go.Figure()
        
        # Add price data
        if chart_type == "candlestick":
            fig.add_trace(
                go.Candlestick(
                    x=df["Date"],
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name="السعر",
                    increasing_line_color=self.config["chart_colors"]["positive"],
                    decreasing_line_color=self.config["chart_colors"]["negative"]
                ),
                row=1 if show_volume else None,
                col=1 if show_volume else None
            )
        elif chart_type == "line":
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["Close"],
                    mode="lines",
                    name="سعر الإغلاق",
                    line=dict(
                        color=self.config["chart_colors"]["primary"],
                        width=2
                    ),
                    fill=None
                ),
                row=1 if show_volume else None,
                col=1 if show_volume else None
            )
        else:  # area
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df["Close"],
                    mode="lines",
                    name="سعر الإغلاق",
                    line=dict(
                        color=self.config["chart_colors"]["primary"],
                        width=2
                    ),
                    fill="tozeroy",
                    fillcolor=f"rgba(0, 179, 134, 0.2)"
                ),
                row=1 if show_volume else None,
                col=1 if show_volume else None
            )
        
        # Add moving averages
        if len(df) > 20:
            # 20-day moving average
            ma20 = df["Close"].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=ma20,
                    mode="lines",
                    name="المتوسط المتحرك 20",
                    line=dict(color="#FF6B35", width=1.5, dash="dash")
                ),
                row=1 if show_volume else None,
                col=1 if show_volume else None
            )
        
        if len(df) > 50:
            # 50-day moving average
            ma50 = df["Close"].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=ma50,
                    mode="lines",
                    name="المتوسط المتحرك 50",
                    line=dict(color="#1E88E5", width=1.5, dash="dot")
                ),
                row=1 if show_volume else None,
                col=1 if show_volume else None
            )
        
        # Add volume
        if show_volume:
            # Determine volume colors based on price movement
            colors = [
                self.config["chart_colors"]["positive"] if close >= open 
                else self.config["chart_colors"]["negative"]
                for close, open in zip(df["Close"], df["Open"])
            ]
            
            fig.add_trace(
                go.Bar(
                    x=df["Date"],
                    y=df["Volume"],
                    name="حجم التداول",
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2,
                col=1
            )
        
        # Update layout
        fig.update_layout(
            title=f"{self.data.company.get('companyName', self.symbol)} - تحليل السعر",
            xaxis_title="التاريخ",
            yaxis_title="السعر ($)",
            height=self.config["chart_height"],
            template="plotly_dark",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Update axes
        if show_volume:
            fig.update_xaxes(title_text="التاريخ", row=2, col=1)
            fig.update_yaxes(title_text="حجم التداول", row=2, col=1)
        
        # Add range selector
        fig.update_xaxes(
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1م", step="month", stepmode="backward"),
                    dict(count=3, label="3م", step="month", stepmode="backward"),
                    dict(count=6, label="6م", step="month", stepmode="backward"),
                    dict(count=1, label="1س", step="year", stepmode="backward"),
                    dict(step="all", label="الكل")
                ])
            )
        )
        
        return fig
    
    def create_metrics_chart(self) -> go.Figure:
        """
        Create metrics visualization chart.
        
        Returns
        -------
        go.Figure
            Metrics gauge chart
        """
        metrics = self.get_key_metrics()
        
        fig = go.Figure()
        
        # Add gauge for price change
        if self.data and not self.data.history.empty:
            price_change = self.data.get_price_change()
            
            fig.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=price_change,
                title={"text": "تغير السعر (%)"},
                delta={"reference": 0},
                gauge={
                    "axis": {"range": [-20, 20]},
                    "bar": {"color": (
                        self.config["chart_colors"]["positive"] 
                        if price_change >= 0 
                        else self.config["chart_colors"]["negative"]
                    )},
                    "steps": [
                        {"range": [-20, -5], "color": "rgba(255, 23, 68, 0.2)"},
                        {"range": [-5, 5], "color": "rgba(255, 215, 0, 0.2)"},
                        {"range": [5, 20], "color": "rgba(0, 200, 83, 0.2)"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 0
                    }
                }
            ))
        
        return fig
    
    def create_volume_profile(self) -> go.Figure:
        """
        Create volume profile chart.
        
        Returns
        -------
        go.Figure
            Volume profile figure
        """
        df = self.get_history_data()
        
        if df.empty:
            return self._create_empty_chart("لا توجد بيانات حجم")
        
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("حجم التداول اليومي", "توزيع الحجم"),
            specs=[[{"type": "bar"}, {"type": "histogram"}]]
        )
        
        # Daily volume
        fig.add_trace(
            go.Bar(
                x=df["Date"][-30:],
                y=df["Volume"][-30:],
                name="حجم التداول",
                marker_color=self.config["chart_colors"]["volume"]
            ),
            row=1,
            col=1
        )
        
        # Volume distribution
        fig.add_trace(
            go.Histogram(
                x=df["Volume"],
                nbinsx=20,
                name="توزيع الحجم",
                marker_color=self.config["chart_colors"]["primary"]
            ),
            row=1,
            col=2
        )
        
        fig.update_layout(
            height=300,
            template="plotly_dark",
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
    
    def create_sector_chart(self, sectors: Dict[str, Any]) -> go.Figure:
        """
        Create sector allocation chart.
        
        Parameters
        ----------
        sectors : Dict[str, Any]
            Sector data from portfolio
            
        Returns
        -------
        go.Figure
            Sector chart
        """
        if not sectors:
            return self._create_empty_chart("لا توجد بيانات قطاعات")
        
        # Prepare data
        labels = list(sectors.keys())
        values = [sectors[sector]["total_market_cap"] for sector in sectors]
        
        # Create donut chart
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(
                    colors=[
                        "#00B386", "#FF6B35", "#1E88E5", 
                        "#FFD700", "#E91E63", "#9C27B0"
                    ]
                ),
                textinfo="label+percent",
                hoverinfo="label+value+percent"
            )
        ])
        
        fig.update_layout(
            title="توزيع القطاعات",
            height=400,
            template="plotly_dark",
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message."""
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
    # Streamlit Rendering Methods
    # =====================================================
    
    def render_company_header(self):
        """Render company header with name, sector, and logo."""
        if not self.data:
            st.warning("⚠️ لم يتم تحميل بيانات الشركة")
            return
        
        company = self.data.company
        
        # Main header
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"## 🏢 {company.get('companyName', 'N/A')}")
            st.markdown(f"""
            **{company.get('sector', 'N/A')}** | {company.get('industry', 'N/A')}
            """)
        
        with col2:
            st.metric(
                label="رمز السهم",
                value=self.symbol,
                delta=""
            )
        
        with col3:
            price = self.data.price.get("price", 0)
            change = self.data.get_price_change()
            st.metric(
                label="السعر الحالي",
                value=f"${price:.2f}",
                delta=f"{change:.2f}%",
                delta_color="normal"
            )
    
    def render_metrics(self):
        """Render key metrics cards."""
        if not self.data:
            return
        
        metrics = self.get_key_metrics()
        
        # Create metrics grid
        cols = st.columns(4)
        
        metrics_items = [
            ("القيمة السوقية", metrics.get("القيمة السوقية", "N/A"), "📊"),
            ("عدد الموظفين", metrics.get("عدد الموظفين", "N/A"), "👥"),
            ("السعر الحالي", metrics.get("السعر الحالي", "N/A"), "💰"),
            ("حجم التداول", metrics.get("حجم التداول", "N/A"), "📈"),
            ("أعلى اليوم", metrics.get("أعلى اليوم", "N/A"), "⬆️"),
            ("أدنى اليوم", metrics.get("أدنى اليوم", "N/A"), "⬇️"),
            ("القطاع", metrics.get("القطاع", "N/A"), "🏗️"),
            ("الدولة", metrics.get("الدولة", "N/A"), "📍")
        ]
        
        for idx, (label, value, icon) in enumerate(metrics_items):
            col = cols[idx % 4]
            with col:
                st.metric(
                    label=f"{icon} {label}",
                    value=value
                )
    
    def render_price_chart(self):
        """Render interactive price chart with controls."""
        if not self.data or self.data.history.empty:
            st.warning("📊 لا توجد بيانات تاريخية للعرض")
            return
        
        # Chart controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            period = st.selectbox(
                "الفترة الزمنية",
                options=list(self.periods.keys()),
                index=3  # 6 months default
            )
        
        with col2:
            interval = st.selectbox(
                "الفاصل الزمني",
                options=list(self.intervals.keys()),
                index=3  # Daily default
            )
        
        with col3:
            chart_type = st.selectbox(
                "نوع الرسم",
                options=["candlestick", "line", "area"],
                index=0
            )
        
        # Refresh data if period/interval changed
        period_key = self.periods[period]
        interval_key = self.intervals[interval]
        
        if (hasattr(self, '_last_period') and self._last_period != period_key) or \
           (hasattr(self, '_last_interval') and self._last_interval != interval_key):
            self.refresh_history(period_key, interval_key)
            self._last_period = period_key
            self._last_interval = interval_key
        
        # Create and display chart
        fig = self.create_price_chart(
            period=period_key,
            interval=interval_key,
            chart_type=chart_type
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_company_details(self):
        """Render company details section."""
        if not self.data:
            return
        
        company = self.data.company
        
        with st.expander("📋 تفاصيل الشركة", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📝 وصف الشركة**")
                st.write(company.get("description", "لا يوجد وصف"))
                
                st.markdown(f"**🌐 الموقع الإلكتروني**")
                st.markdown(f"[{company.get('website', 'N/A')}]({company.get('website', '#')})")
            
            with col2:
                st.markdown("**📊 معلومات إضافية**")
                
                details = {
                    "الدولة": company.get("country", "N/A"),
                    "القطاع": company.get("sector", "N/A"),
                    "الصناعة": company.get("industry", "N/A"),
                    "القيمة السوقية": f"${company.get('marketCap', 0):.2f}B",
                    "عدد الموظفين": f"{company.get('employees', 0):,}"
                }
                
                for key, value in details.items():
                    st.markdown(f"**{key}:** {value}")
    
    def render_dividends(self):
        """Render dividends section."""
        if not self.data or self.data.dividends.empty:
            return
        
        with st.expander("💰 توزيعات الأرباح", expanded=False):
            df = self.data.dividends
            
            # Show dividend history
            st.dataframe(
                df.tail(10)[["Date", "Dividend"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Calculate dividend metrics
            total = df["Dividend"].sum()
            avg = df["Dividend"].mean()
            count = len(df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("إجمالي التوزيعات", f"${total:.2f}")
            with col2:
                st.metric("متوسط التوزيع", f"${avg:.2f}")
            with col3:
                st.metric("عدد التوزيعات", count)
    
    def render_price_alert(self):
        """Render price alert section."""
        if not self.data:
            return
        
        with st.expander("🔔 تنبيهات السعر", expanded=False):
            st.markdown("**أنشئ تنبيه للسعر**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                alert_price = st.number_input(
                    "سعر التنبيه",
                    min_value=0.01,
                    value=float(self.data.price.get("price", 100)),
                    step=0.1
                )
            
            with col2:
                alert_type = st.selectbox(
                    "نوع التنبيه",
                    options=["أعلى من", "أقل من"]
                )
            
            with col3:
                if st.button("إضافة تنبيه"):
                    st.success(f"✅ تم إضافة تنبيه عند السعر {alert_price} ({alert_type})")
    
    def render_all(self):
        """Render complete dashboard."""
        if not self.data:
            st.error("❌ فشل تحميل بيانات الشركة")
            return
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 نظرة عامة",
            "📈 تحليل السعر",
            "📋 معلومات الشركة",
            "💰 أرباح وتنبيهات"
        ])
        
        with tab1:
            self.render_company_header()
            st.divider()
            self.render_metrics()
            st.divider()
            
            # Price chart with smaller height for overview
            fig = self.create_price_chart(period="1mo", interval="1d", chart_type="line")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Quick metrics
            col1, col2 = st.columns(2)
            with col1:
                if not self.data.history.empty:
                    high, low = self.data.get_high_low()
                    st.metric("أعلى سعر خلال الفترة", f"${high:.2f}")
                    st.metric("أدنى سعر خلال الفترة", f"${low:.2f}")
            
            with col2:
                if not self.data.history.empty:
                    avg_vol = self.data.get_volume_avg()
                    st.metric("متوسط حجم التداول", f"{avg_vol:,.0f}")
                    st.metric("آخر تحديث", self.data.last_updated[:19])
        
        with tab2:
            self.render_price_chart()
            
            # Volume profile
            st.subheader("📊 تحليل الحجم")
            fig = self.create_volume_profile()
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            self.render_company_details()
        
        with tab4:
            self.render_dividends()
            st.divider()
            self.render_price_alert()
    
    # =====================================================
    # Export Methods
    # =====================================================
    
    def export_data(self, format: str = "json") -> str:
        """
        Export dashboard data.
        
        Parameters
        ----------
        format : str
            Export format ('json', 'csv', 'excel')
            
        Returns
        -------
        str
            Exported data
        """
        if not self.data:
            return ""
        
        if format == "json":
            return json.dumps(self.get_dashboard_data(), indent=2, default=str)
        
        elif format == "csv":
            return self.data.history.to_csv()
        
        elif format == "excel":
            # Would need to create Excel file
            return "Excel export coming soon"
        
        return "Unsupported format"


# =====================================================
# Utility Functions
# =====================================================

def create_dashboard(symbol: str) -> Dashboard:
    """
    Create and initialize dashboard for a symbol.
    
    Parameters
    ----------
    symbol : str
        Stock symbol
        
    Returns
    -------
    Dashboard
        Dashboard instance
    """
    dashboard = Dashboard(symbol)
    return dashboard


def get_dashboard_html(symbol: str) -> str:
    """
    Get dashboard as HTML for embedding.
    
    Parameters
    ----------
    symbol : str
        Stock symbol
        
    Returns
    -------
    str
        HTML representation
    """
    dashboard = Dashboard(symbol)
    if not dashboard.data:
        return "<p>لم يتم تحميل البيانات</p>"
    
    # Create simple HTML representation
    company = dashboard.data.company
    price = dashboard.data.price
    
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; direction: rtl;">
        <h2>{company.get('companyName', symbol)}</h2>
        <p><strong>القطاع:</strong> {company.get('sector', 'N/A')}</p>
        <p><strong>السعر الحالي:</strong> ${price.get('price', 0):.2f}</p>
        <p><strong>القيمة السوقية:</strong> ${company.get('marketCap', 0):.2f}B</p>
        <p><strong>عدد الموظفين:</strong> {company.get('employees', 0):,}</p>
        <p><strong>الدولة:</strong> {company.get('country', 'N/A')}</p>
        <p><strong>الموقع:</strong> <a href="{company.get('website', '#')}">{company.get('website', 'N/A')}</a></p>
        <p><strong>الوصف:</strong> {company.get('description', 'N/A')[:200]}...</p>
    </div>
    """
    
    return html


# =====================================================
# Main Demo Function
# =====================================================

def demo():
    """
    Demo function to showcase Dashboard functionality.
    """
    st.set_page_config(
        page_title="ByToBy Pro - Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80", caption="ByToBy Pro")
        st.title("📊 Dashboard")
        
        # Symbol input
        symbol = st.text_input(
            "رمز السهم",
            value="2222.SR",
            help="أدخل رمز السهم (مثال: 2222.SR, AAPL, TSLA)"
        )
        
        if st.button("🔄 تحميل", use_container_width=True):
            st.session_state['dashboard_symbol'] = symbol
            st.rerun()
        
        st.divider()
        
        # Quick links
        st.markdown("### 🔗 روابط سريعة")
        quick_symbols = [
            ("أرامكو", "2222.SR"),
            ("الراجحي", "1120.SR"),
            ("STC", "7010.SR"),
            ("Apple", "AAPL"),
            ("Tesla", "TSLA"),
            ("Microsoft", "MSFT")
        ]
        
        for name, sym in quick_symbols:
            if st.button(f"📌 {name}", key=sym):
                st.session_state['dashboard_symbol'] = sym
                st.rerun()
    
    # Main content
    if 'dashboard_symbol' not in st.session_state:
        st.session_state['dashboard_symbol'] = "2222.SR"
    
    # Initialize dashboard
    dashboard = Dashboard(st.session_state['dashboard_symbol'])
    
    if dashboard.data:
        # Render dashboard
        dashboard.render_all()
        
        # Auto-refresh option
        if st.sidebar.checkbox("🔄 تحديث تلقائي", value=False):
            st.sidebar.info(f"التحديث كل {dashboard.config['update_interval']} ثانية")
            time.sleep(dashboard.config['update_interval'])
            dashboard.update_price()
            st.rerun()
        
        # Export options
        st.sidebar.divider()
        if st.sidebar.button("📥 تصدير البيانات (JSON)"):
            data = dashboard.export_data("json")
            st.sidebar.download_button(
                label="تنزيل JSON",
                data=data,
                file_name=f"{dashboard.symbol}_dashboard.json",
                mime="application/json"
            )
    
    else:
        st.error(f"❌ فشل تحميل بيانات {st.session_state['dashboard_symbol']}")
        st.info("💡 تأكد من صحة رمز السهم وحاول مرة أخرى")


# =====================================================
# Main Entry Point
# =====================================================

if __name__ == "__main__":
    demo()
