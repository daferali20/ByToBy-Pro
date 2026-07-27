# pages/HeatMap2.py
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import time

# Import API
try:
    from api import get_portfolio_data, get_price, get_history
except ImportError as e:
    st.error(f"❌ خطأ في استيراد API: {e}")
    st.stop()

st.set_page_config(
    page_title="ByToBy Pro - Heat Map", 
    page_icon="🔥", 
    layout="wide"
)

# ============================================
# Data Generation
# ============================================
def generate_sample_data():
    """Generate sample stock data for heatmap"""
    np.random.seed(42)
    
    # List of stocks with their sectors
    stocks = [
        {"symbol": "AAPL", "name": "Apple Inc.", "sector": "التكنولوجيا"},
        {"symbol": "MSFT", "name": "Microsoft", "sector": "التكنولوجيا"},
        {"symbol": "GOOGL", "name": "Alphabet", "sector": "التكنولوجيا"},
        {"symbol": "AMZN", "name": "Amazon", "sector": "البيع بالتجزئة"},
        {"symbol": "TSLA", "name": "Tesla", "sector": "السيارات"},
        {"symbol": "2222.SR", "name": "أرامكو", "sector": "الطاقة"},
        {"symbol": "1120.SR", "name": "الراجحي", "sector": "المالية"},
        {"symbol": "7010.SR", "name": "STC", "sector": "الاتصالات"},
        {"symbol": "NVDA", "name": "NVIDIA", "sector": "التكنولوجيا"},
        {"symbol": "META", "name": "Meta", "sector": "التكنولوجيا"},
        {"symbol": "NFLX", "name": "Netflix", "sector": "التكنولوجيا"},
        {"symbol": "JPM", "name": "JPMorgan", "sector": "المالية"},
        {"symbol": "VTI", "name": "Vanguard", "sector": "المالية"},
        {"symbol": "KO", "name": "Coca-Cola", "sector": "السلع الاستهلاكية"},
        {"symbol": "PFE", "name": "Pfizer", "sector": "الرعاية الصحية"},
        {"symbol": "WMT", "name": "Walmart", "sector": "البيع بالتجزئة"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "الرعاية الصحية"},
        {"symbol": "V", "name": "Visa", "sector": "المالية"},
        {"symbol": "PG", "name": "Procter & Gamble", "sector": "السلع الاستهلاكية"},
        {"symbol": "HD", "name": "Home Depot", "sector": "البيع بالتجزئة"},
        {"symbol": "DIS", "name": "Disney", "sector": "الإعلام"},
        {"symbol": "MA", "name": "Mastercard", "sector": "المالية"},
        {"symbol": "BAC", "name": "Bank of America", "sector": "المالية"},
        {"symbol": "XOM", "name": "Exxon Mobil", "sector": "الطاقة"},
        {"symbol": "CVX", "name": "Chevron", "sector": "الطاقة"},
    ]
    
    data = []
    for stock in stocks:
        # Random performance metrics
        change_pct = np.random.normal(0, 3)  # Daily change
        volume = np.random.randint(100000, 10000000)
        market_cap = np.random.uniform(10, 3000)
        pe_ratio = np.random.uniform(5, 50)
        price = np.random.uniform(10, 500)
        
        # RSI (Relative Strength Index)
        rsi = np.random.uniform(30, 70)
        
        # Volume change
        volume_change = np.random.normal(0, 15)
        
        # 52-week high/low
        high_52w = price * np.random.uniform(1.1, 1.5)
        low_52w = price * np.random.uniform(0.5, 0.9)
        
        data.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "sector": stock["sector"],
            "price": price,
            "change_pct": change_pct,
            "volume": volume,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "rsi": rsi,
            "volume_change": volume_change,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "volume_ratio": np.random.uniform(0.5, 2.0),
            "momentum": np.random.uniform(-30, 30),
            "volatility": np.random.uniform(10, 40),
        })
    
    return pd.DataFrame(data)

# ============================================
# Heatmap Functions
# ============================================
def create_heatmap(df, metric, title, color_scale="RdYlGn"):
    """Create a heatmap from dataframe"""
    
    # Create grid for heatmap (arrange in rows of 5)
    n_cols = 5
    n_rows = int(np.ceil(len(df) / n_cols))
    
    # Create matrix
    matrix_data = []
    labels = []
    
    for i in range(n_rows):
        row_data = []
        row_labels = []
        for j in range(n_cols):
            idx = i * n_cols + j
            if idx < len(df):
                row_data.append(df.iloc[idx][metric])
                row_labels.append(f"{df.iloc[idx]['symbol']}<br>{df.iloc[idx]['name']}<br>{df.iloc[idx][metric]:.2f}")
            else:
                row_data.append(np.nan)
                row_labels.append("")
        matrix_data.append(row_data)
        labels.append(row_labels)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix_data,
        x=[f"Col{j+1}" for j in range(n_cols)],
        y=[f"Row{i+1}" for i in range(n_rows)],
        text=labels,
        texttemplate="%{text}",
        textfont={"size": 10, "color": "white"},
        colorscale=color_scale,
        showscale=True,
        zmid=0,  # Center at 0 for change metrics
        hovertemplate="<b>%{text}</b><br>القيمة: %{z:.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=title,
        height=600,
        xaxis_showticklabels=False,
        yaxis_showticklabels=False,
        template="plotly_dark",
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    return fig

def create_scatter_matrix(df):
    """Create scatter matrix for multi-dimensional analysis"""
    # Select numerical columns
    num_cols = ['change_pct', 'volume', 'market_cap', 'pe_ratio', 'rsi']
    
    fig = px.scatter_matrix(
        df,
        dimensions=num_cols,
        color='sector',
        title="مصفوفة التشتت - علاقات المؤشرات",
        labels={
            'change_pct': 'التغير %',
            'volume': 'حجم التداول',
            'market_cap': 'القيمة السوقية',
            'pe_ratio': 'نسبة PE',
            'rsi': 'RSI'
        },
        template="plotly_dark",
        height=800
    )
    
    fig.update_traces(diagonal_visible=False)
    return fig

# ============================================
# Display Leaderboard
# ============================================
def display_leaderboard(df):
    """Display top gainers, losers, and most active stocks"""
    
    if df.empty:
        st.warning("لا توجد بيانات لعرضها")
        return
    
    st.divider()
    st.subheader("🏆 قادة السوق")
    
    # Create three columns for the leaderboards
    col1, col2, col3 = st.columns(3)
    
    # 1. Top Gainers (الأكثر ارتفاعاً)
    with col1:
        st.markdown("### 📈 الأكثر ارتفاعاً")
        top_gainers = df.nlargest(5, 'change_pct')[['symbol', 'name', 'change_pct', 'price', 'sector']]
        
        if not top_gainers.empty:
            for idx, row in top_gainers.iterrows():
                change_color = "🟢" if row['change_pct'] > 0 else "🔴"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                            padding: 10px; 
                            border-radius: 10px; 
                            margin-bottom: 8px;
                            border-right: 4px solid #00ff00;">
                    <b>{row['symbol']}</b> - {row['name']}<br>
                    <span style="color: #00ff00; font-size: 1.2em;">▲ {row['change_pct']:.2f}%</span>
                    <span style="color: #888; font-size: 0.9em;"> | ${row['price']:.2f}</span><br>
                    <span style="color: #666; font-size: 0.8em;">{row['sector']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات كافية")
    
    # 2. Top Losers (الأكثر انخفاضاً)
    with col2:
        st.markdown("### 📉 الأكثر انخفاضاً")
        top_losers = df.nsmallest(5, 'change_pct')[['symbol', 'name', 'change_pct', 'price', 'sector']]
        
        if not top_losers.empty:
            for idx, row in top_losers.iterrows():
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                            padding: 10px; 
                            border-radius: 10px; 
                            margin-bottom: 8px;
                            border-right: 4px solid #ff0000;">
                    <b>{row['symbol']}</b> - {row['name']}<br>
                    <span style="color: #ff0000; font-size: 1.2em;">▼ {row['change_pct']:.2f}%</span>
                    <span style="color: #888; font-size: 0.9em;"> | ${row['price']:.2f}</span><br>
                    <span style="color: #666; font-size: 0.8em;">{row['sector']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات كافية")
    
    # 3. Most Active (الأكثر تحركاً)
    with col3:
        st.markdown("### 🔥 الأكثر تحركاً")
        
        # Calculate absolute change for volatility
        df['abs_change'] = df['change_pct'].abs()
        most_active = df.nlargest(5, 'abs_change')[['symbol', 'name', 'change_pct', 'price', 'sector', 'volume']]
        
        if not most_active.empty:
            for idx, row in most_active.iterrows():
                change_color = "🟢" if row['change_pct'] > 0 else "🔴"
                arrow = "▲" if row['change_pct'] > 0 else "▼"
                color = "#00ff00" if row['change_pct'] > 0 else "#ff0000"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); 
                            padding: 10px; 
                            border-radius: 10px; 
                            margin-bottom: 8px;
                            border-right: 4px solid #ff6600;">
                    <b>{row['symbol']}</b> - {row['name']}<br>
                    <span style="color: {color}; font-size: 1.2em;">{arrow} {row['change_pct']:.2f}%</span>
                    <span style="color: #888; font-size: 0.9em;"> | ${row['price']:.2f}</span><br>
                    <span style="color: #666; font-size: 0.8em;">حجم: {row['volume']:,} | {row['sector']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات كافية")
    
    # Display additional statistics
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_change = df['change_pct'].mean()
        st.metric("📊 متوسط التغير", f"{avg_change:.2f}%")
    
    with col2:
        total_gainers = len(df[df['change_pct'] > 0])
        st.metric("📈 عدد الرابحين", total_gainers)
    
    with col3:
        total_losers = len(df[df['change_pct'] < 0])
        st.metric("📉 عدد الخاسرين", total_losers)
    
    with col4:
        # Most active sector
        most_active_sector = df.groupby('sector')['abs_change'].mean().idxmax()
        st.metric("🔥 أكثر قطاع نشاطاً", most_active_sector)

# ============================================
# Main App
# ============================================
def main():
    st.title("🔥 Heat Map - خريطة أداء الأسهم")
    st.markdown("عرض أداء الأسهم بشكل بصري باستخدام الخريطة الحرارية")
    
    # ============================================
    # Sidebar
    # ============================================
    with st.sidebar:
        st.header("⚙️ إعدادات الخريطة")
        
        # Data source
        data_source = st.radio(
            "مصدر البيانات",
            ["بيانات تجريبية", "بيانات حقيقية (Yahoo)"],
            index=0,
            help="البيانات التجريبية للعرض، البيانات الحقيقية تتطلب اتصال بالإنترنت"
        )
        
        st.markdown("---")
        
        # Metric selection
        st.subheader("📊 المؤشر المعروض")
        metric = st.selectbox(
            "اختر المؤشر",
            [
                "التغير اليومي (%)",
                "القيمة السوقية",
                "حجم التداول",
                "نسبة PE",
                "RSI",
                "التغير في الحجم",
                "المومنتوم",
                "التقلب"
            ],
            index=0
        )
        
        metric_map = {
            "التغير اليومي (%)": "change_pct",
            "القيمة السوقية": "market_cap",
            "حجم التداول": "volume",
            "نسبة PE": "pe_ratio",
            "RSI": "rsi",
            "التغير في الحجم": "volume_change",
            "المومنتوم": "momentum",
            "التقلب": "volatility"
        }
        
        metric_col = metric_map[metric]
        
        # Color scheme
        color_scheme = st.selectbox(
            "نظام الألوان",
            ["RdYlGn", "RdYlBu", "RdBu", "Viridis", "Plasma", "Cividis"],
            index=0
        )
        
        st.markdown("---")
        
        # Filter by sector
        st.subheader("🔍 تصفية")
        all_sectors = ["الكل"] + sorted(list(set(generate_sample_data()['sector'])))
        selected_sector = st.selectbox("القطاع", all_sectors)
        
        # Number of stocks
        n_stocks = st.slider("عدد الأسهم المعروضة", min_value=5, max_value=30, value=20, step=5)
        
        st.markdown("---")
        
        # Auto-refresh
        auto_refresh = st.checkbox("تحديث تلقائي")
        if auto_refresh:
            refresh_interval = st.slider("فترة التحديث (ثواني)", min_value=5, max_value=60, value=30)
        
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.rerun()
    
    # ============================================
    # Load Data
    # ============================================
    with st.spinner("جاري تحميل البيانات..."):
        if data_source == "بيانات حقيقية (Yahoo)":
            try:
                # Get real data
                symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "2222.SR", "1120.SR", "7010.SR",
                          "NVDA", "META", "NFLX", "JPM", "VTI", "KO", "PFE"]
                df = get_portfolio_data(symbols)
                df = pd.DataFrame(df)
                
                # Add random metrics for demonstration
                if not df.empty:
                    df['change_pct'] = np.random.normal(0, 3, len(df))
                    df['rsi'] = np.random.uniform(30, 70, len(df))
                    df['volume_change'] = np.random.normal(0, 15, len(df))
                    df['pe_ratio'] = np.random.uniform(5, 50, len(df))
                    df['momentum'] = np.random.uniform(-30, 30, len(df))
                    df['volatility'] = np.random.uniform(10, 40, len(df))
                    df['sector'] = np.random.choice(["التكنولوجيا", "المالية", "الطاقة", "البيع بالتجزئة"], len(df))
                    df['name'] = df['symbol']
            except Exception as e:
                st.warning(f"⚠️ تعذر تحميل البيانات الحقيقية: {e}")
                df = generate_sample_data()
        else:
            df = generate_sample_data()
    
    # Filter by sector
    if selected_sector != "الكل":
        df = df[df['sector'] == selected_sector]
    
    # Limit number of stocks
    if len(df) > n_stocks:
        # Sort by market cap and take top n
        df = df.sort_values('market_cap', ascending=False).head(n_stocks)
    
    # ============================================
    # Display Leaderboard
    # ============================================
    display_leaderboard(df)
    
    # ============================================
    # Heatmap
    # ============================================
    
    # Create heatmap
    title = f"الخريطة الحرارية - {metric} حسب السهم"
    fig = create_heatmap(df, metric_col, title, color_scheme)
    st.plotly_chart(fig, use_container_width=True)
    
    # ============================================
    # Additional Visualizations
    # ============================================
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart of selected metric
        st.subheader(f"📊 {metric} - ترتيب الأسهم")
        
        sorted_df = df.sort_values(metric_col, ascending=False)
        
        # Limit for readability
        display_df = sorted_df.head(15)
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=display_df['symbol'],
            y=display_df[metric_col],
            text=display_df[metric_col].round(2),
            textposition='outside',
            marker_color=display_df[metric_col],
            marker_colorscale=color_scheme,
            name=metric
        ))
        
        fig_bar.update_layout(
            title=f"ترتيب الأسهم حسب {metric}",
            xaxis_title="السهم",
            yaxis_title=metric,
            template="plotly_dark",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Sector analysis
        st.subheader("📊 تحليل حسب القطاع")
        
        sector_agg = df.groupby('sector').agg({
            'change_pct': 'mean',
            'volume': 'sum',
            'market_cap': 'sum'
        }).reset_index()
        
        fig_sector = go.Figure()
        fig_sector.add_trace(go.Bar(
            x=sector_agg['sector'],
            y=sector_agg['change_pct'],
            text=sector_agg['change_pct'].round(2),
            textposition='outside',
            marker_color=sector_agg['change_pct'],
            marker_colorscale=color_scheme,
            name="متوسط التغير"
        ))
        
        fig_sector.update_layout(
            title="متوسط التغير اليومي حسب القطاع",
            xaxis_title="القطاع",
            yaxis_title="متوسط التغير (%)",
            template="plotly_dark",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_sector, use_container_width=True)
    
    # ============================================
    # Scatter Matrix (if enough data)
    # ============================================
    if len(df) > 5:
        st.divider()
        st.subheader("📊 تحليل متعدد المؤشرات")
        
        fig_matrix = create_scatter_matrix(df)
        st.plotly_chart(fig_matrix, use_container_width=True)
    
    # ============================================
    # Data Table
    # ============================================
    with st.expander("📋 عرض البيانات التفصيلية", expanded=False):
        display_df = df.copy()
        display_df['change_pct'] = display_df['change_pct'].apply(lambda x: f"{x:.2f}%")
        display_df['market_cap'] = display_df['market_cap'].apply(lambda x: f"${x:.2f}B")
        display_df['volume'] = display_df['volume'].apply(lambda x: f"{x:,}")
        display_df['pe_ratio'] = display_df['pe_ratio'].apply(lambda x: f"{x:.1f}")
        display_df['rsi'] = display_df['rsi'].apply(lambda x: f"{x:.1f}")
        display_df['momentum'] = display_df['momentum'].apply(lambda x: f"{x:.1f}%")
        display_df['volatility'] = display_df['volatility'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(display_df, use_container_width=True)
    
    # ============================================
    # Footer
    # ============================================
    st.divider()
    st.caption(f"تم التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("ℹ️ الألوان: الأخضر = أداء إيجابي، الأحمر = أداء سلبي")
    
    # Auto-refresh
    if auto_refresh:
        st.caption(f"⏰ سيتم التحديث تلقائياً كل {refresh_interval} ثانية")
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
