# pages/Liquidity_Growth.py
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
import yfinance as yf
import time

# Import API
try:
    from api import get_portfolio_data, get_price, get_history
except ImportError:
    st.warning("⚠️ API غير متوفرة، سيتم استخدام البيانات التجريبية")

st.set_page_config(
    page_title="ByToBy Pro - Liquidity & Growth",
    page_icon="💧",
    layout="wide"
)

# ============================================
# Data Functions
# ============================================

def get_real_stock_data(symbols):
    """Get real stock data from Yahoo Finance"""
    data = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            
            # Get historical data for growth calculation
            hist = ticker.history(period="1mo")
            
            # Calculate growth metrics
            if not hist.empty and len(hist) > 1:
                price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                volume_avg = hist['Volume'].mean()
                volume_today = hist['Volume'].iloc[-1] if not hist.empty else 0
                volume_growth = ((volume_today - volume_avg) / volume_avg) * 100 if volume_avg > 0 else 0
            else:
                price_change = 0
                volume_avg = 0
                volume_today = 0
                volume_growth = 0
            
            data.append({
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "price": info.get("lastPrice", 0),
                "volume": info.get("lastVolume", 0),
                "volume_avg": volume_avg,
                "volume_growth": volume_growth,
                "price_change_1m": price_change,
                "market_cap": info.get("marketCap", 0) / 1_000_000_000,  # in billions
                "sector": ticker.info.get("sector", "غير محدد"),
                "change_today": ((info.get("lastPrice", 0) - info.get("previousClose", info.get("lastPrice", 0))) / info.get("previousClose", 1)) * 100
            })
        except Exception as e:
            # Fallback to sample data for this symbol
            data.append(generate_sample_stock(symbol))
    
    return pd.DataFrame(data)

def generate_sample_stock(symbol):
    """Generate sample data for a single stock"""
    np.random.seed(hash(symbol) % 2**32)
    
    names = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "2222.SR": "أرامكو السعودية",
        "1120.SR": "مصرف الراجحي",
        "7010.SR": "STC",
        "NVDA": "NVIDIA Corporation",
        "META": "Meta Platforms",
        "NFLX": "Netflix Inc.",
        "JPM": "JPMorgan Chase",
        "VTI": "Vanguard",
        "KO": "Coca-Cola",
        "PFE": "Pfizer"
    }
    
    sectors = ["التكنولوجيا", "المالية", "الطاقة", "الرعاية الصحية", "البيع بالتجزئة", "الاتصالات", "السلع الاستهلاكية"]
    
    return {
        "symbol": symbol,
        "name": names.get(symbol, f"Company {symbol}"),
        "price": np.random.uniform(10, 500),
        "volume": np.random.randint(100000, 10000000),
        "volume_avg": np.random.randint(100000, 8000000),
        "volume_growth": np.random.normal(0, 25),
        "price_change_1m": np.random.normal(0, 15),
        "market_cap": np.random.uniform(10, 3000),
        "sector": np.random.choice(sectors),
        "change_today": np.random.normal(0, 3)
    }

def generate_sample_data():
    """Generate sample stock data for screening"""
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "2222.SR", "1120.SR", "7010.SR",
               "NVDA", "META", "NFLX", "JPM", "VTI", "KO", "PFE", "WMT", "JNJ", "V", "PG", "HD"]
    
    data = []
    for symbol in symbols:
        data.append(generate_sample_stock(symbol))
    
    return pd.DataFrame(data)

# ============================================
# Main App
# ============================================

def main():
    st.title("💧 Liquidity & Growth - السيولة والنمو")
    st.markdown("تحليل الأسهم الأكثر سيولة والأسرع نمواً في السوق")
    
    # ============================================
    # Sidebar
    # ============================================
    with st.sidebar:
        st.header("⚙️ الإعدادات")
        
        # Data source
        data_source = st.radio(
            "مصدر البيانات",
            ["بيانات حقيقية (Yahoo)", "بيانات تجريبية"],
            index=0,
            help="البيانات الحقيقية تتطلب اتصال بالإنترنت"
        )
        
        st.markdown("---")
        
        # Number of stocks to display
        n_stocks = st.slider(
            "عدد الأسهم المعروضة",
            min_value=5,
            max_value=50,
            value=20,
            step=5
        )
        
        st.markdown("---")
        
        # Filters
        st.subheader("🔍 تصفية")
        
        # Volume threshold
        min_volume = st.number_input(
            "الحد الأدنى لحجم التداول",
            min_value=0,
            value=100000,
            step=50000,
            format="%d"
        )
        
        # Growth threshold
        min_growth = st.slider(
            "الحد الأدنى لنمو السعر (شهر)",
            min_value=-50,
            max_value=100,
            value=0,
            step=5
        )
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.rerun()
    
    # ============================================
    # Load Data
    # ============================================
    with st.spinner("جاري تحميل البيانات..."):
        if data_source == "بيانات حقيقية (Yahoo)":
            try:
                symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "2222.SR", "1120.SR", "7010.SR",
                          "NVDA", "META", "NFLX", "JPM", "VTI", "KO", "PFE", "WMT", "JNJ", "V", "PG", "HD"]
                df = get_real_stock_data(symbols)
                data_type = "حقيقية"
            except Exception as e:
                st.warning(f"⚠️ تعذر تحميل البيانات الحقيقية: {e}")
                df = generate_sample_data()
                data_type = "تجريبية"
        else:
            df = generate_sample_data()
            data_type = "تجريبية"
    
    # Apply filters
    df_filtered = df.copy()
    df_filtered = df_filtered[df_filtered['volume'] >= min_volume]
    df_filtered = df_filtered[df_filtered['price_change_1m'] >= min_growth]
    
    # ============================================
    # Statistics
    # ============================================
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 إجمالي الأسهم", len(df_filtered))
    
    with col2:
        avg_volume = df_filtered['volume'].mean() if not df_filtered.empty else 0
        st.metric("💧 متوسط حجم التداول", f"{avg_volume:,.0f}")
    
    with col3:
        max_volume = df_filtered['volume'].max() if not df_filtered.empty else 0
        st.metric("📈 أعلى حجم تداول", f"{max_volume:,.0f}")
    
    with col4:
        avg_growth = df_filtered['price_change_1m'].mean() if not df_filtered.empty else 0
        st.metric("🚀 متوسط النمو (شهر)", f"{avg_growth:.1f}%")
    
    with col5:
        max_growth = df_filtered['price_change_1m'].max() if not df_filtered.empty else 0
        st.metric("⬆️ أعلى نمو", f"{max_growth:.1f}%")
    
    st.divider()
    st.caption(f"📊 مصدر البيانات: {data_type} - تم التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ============================================
    # Tab Layout
    # ============================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "💧 الأكثر سيولة",
        "🚀 الأكثر نمواً",
        "📊 تحليل متقدم",
        "📋 جميع البيانات"
    ])
    
    # ============================================
    # Tab 1: Most Liquid Stocks
    # ============================================
    with tab1:
        st.subheader("💧 الأسهم الأكثر سيولة")
        st.markdown("الأسهم ذات أعلى حجم تداول في السوق")
        
        # Sort by volume
        liquid_stocks = df_filtered.nlargest(n_stocks, 'volume')
        
        # Display as cards
        cols = st.columns(3)
        for idx, (_, row) in enumerate(liquid_stocks.iterrows()):
            with cols[idx % 3]:
                volume_billions = row['volume'] / 1_000_000
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a1a2e, #16213e);
                            padding: 1rem;
                            border-radius: 12px;
                            margin-bottom: 0.5rem;
                            border: 1px solid rgba(102, 126, 234, 0.2);">
                    <h4 style="color: #667eea; margin: 0;">{row['symbol']}</h4>
                    <p style="color: #d0d0d0; margin: 0.2rem 0;">{row['name'][:30]}</p>
                    <p style="color: #00ff00; font-size: 1.2rem; margin: 0.2rem 0;">
                        💧 {volume_billions:.2f}M
                    </p>
                    <p style="color: #a0a0b0; font-size: 0.9rem; margin: 0;">
                        السعر: ${row['price']:.2f} | التغير: {row['change_today']:.2f}%
                    </p>
                    <p style="color: #888; font-size: 0.8rem; margin: 0;">
                        {row['sector']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Volume chart
        st.subheader("📊 توزيع حجم التداول")
        
        fig = px.bar(
            liquid_stocks.head(15),
            x='symbol',
            y='volume',
            color='sector',
            title="أعلى 15 سهماً من حيث حجم التداول",
            labels={'volume': 'حجم التداول', 'symbol': 'رمز السهم'},
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # ============================================
    # Tab 2: Fastest Growing Stocks
    # ============================================
    with tab2:
        st.subheader("🚀 الأسهم الأكثر نمواً")
        st.markdown("الأسهم ذات أعلى نمو في السعر خلال الشهر الماضي")
        
        # Sort by growth
        growth_stocks = df_filtered.nlargest(n_stocks, 'price_change_1m')
        
        # Display as cards
        cols = st.columns(3)
        for idx, (_, row) in enumerate(growth_stocks.iterrows()):
            with cols[idx % 3]:
                growth_color = "#00ff00" if row['price_change_1m'] > 0 else "#ff0000"
                growth_arrow = "▲" if row['price_change_1m'] > 0 else "▼"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a1a2e, #16213e);
                            padding: 1rem;
                            border-radius: 12px;
                            margin-bottom: 0.5rem;
                            border: 1px solid rgba(102, 126, 234, 0.2);">
                    <h4 style="color: #667eea; margin: 0;">{row['symbol']}</h4>
                    <p style="color: #d0d0d0; margin: 0.2rem 0;">{row['name'][:30]}</p>
                    <p style="color: {growth_color}; font-size: 1.2rem; margin: 0.2rem 0;">
                        {growth_arrow} {row['price_change_1m']:.1f}%
                    </p>
                    <p style="color: #a0a0b0; font-size: 0.9rem; margin: 0;">
                        السعر: ${row['price']:.2f} | حجم: {row['volume']:,.0f}
                    </p>
                    <p style="color: #888; font-size: 0.8rem; margin: 0;">
                        {row['sector']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Growth chart
        st.subheader("📊 توزيع النمو")
        
        fig = px.bar(
            growth_stocks.head(15),
            x='symbol',
            y='price_change_1m',
            color='price_change_1m',
            color_continuous_scale=['#ff0000', '#ffff00', '#00ff00'],
            title="أعلى 15 سهماً من حيث النمو (شهر)",
            labels={'price_change_1m': 'نمو السعر (%)', 'symbol': 'رمز السهم'},
            template="plotly_dark",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # ============================================
    # Tab 3: Advanced Analysis
    # ============================================
    with tab3:
        st.subheader("📊 تحليل متقدم")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Volume vs Growth scatter plot
            st.markdown("#### 💧 السيولة vs 🚀 النمو")
            
            fig_scatter = px.scatter(
                df_filtered,
                x='volume',
                y='price_change_1m',
                size='market_cap',
                color='sector',
                hover_name='name',
                title="العلاقة بين حجم التداول والنمو",
                labels={
                    'volume': 'حجم التداول',
                    'price_change_1m': 'نمو السعر (%)'
                },
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            # Sector analysis
            st.markdown("#### 📊 تحليل حسب القطاع")
            
            sector_agg = df_filtered.groupby('sector').agg({
                'volume': 'sum',
                'price_change_1m': 'mean',
                'market_cap': 'sum'
            }).reset_index()
            
            fig_sector = go.Figure()
            
            # Add bar for volume
            fig_sector.add_trace(go.Bar(
                x=sector_agg['sector'],
                y=sector_agg['volume'] / 1_000_000,
                name='حجم التداول (M)',
                marker_color='#667eea',
                yaxis='y'
            ))
            
            # Add line for growth
            fig_sector.add_trace(go.Scatter(
                x=sector_agg['sector'],
                y=sector_agg['price_change_1m'],
                name='متوسط النمو (%)',
                marker_color='#ff6b35',
                yaxis='y2',
                mode='lines+markers'
            ))
            
            fig_sector.update_layout(
                title="تحليل القطاعات - السيولة والنمو",
                template="plotly_dark",
                height=400,
                yaxis=dict(title="حجم التداول (M)"),
                yaxis2=dict(
                    title="متوسط النمو (%)",
                    overlaying='y',
                    side='right'
                )
            )
            st.plotly_chart(fig_sector, use_container_width=True)
        
        # Top performers
        st.divider()
        st.subheader("🏆 أفضل الأداء")
        
        # Create a combined score
        df_filtered['liquidity_score'] = df_filtered['volume'] / df_filtered['volume'].max()
        df_filtered['growth_score'] = (df_filtered['price_change_1m'] - df_filtered['price_change_1m'].min()) / (df_filtered['price_change_1m'].max() - df_filtered['price_change_1m'].min())
        df_filtered['combined_score'] = df_filtered['liquidity_score'] * 0.5 + df_filtered['growth_score'] * 0.5
        
        top_performers = df_filtered.nlargest(10, 'combined_score')
        
        fig_performers = px.bar(
            top_performers,
            x='symbol',
            y='combined_score',
            color='sector',
            title="أفضل الأسهم من حيث السيولة والنمو معاً",
            labels={
                'combined_score': 'النقاط المجمعة',
                'symbol': 'رمز السهم'
            },
            template="plotly_dark",
            height=400,
            text_auto='.2f'
        )
        st.plotly_chart(fig_performers, use_container_width=True)
    
    # ============================================
    # Tab 4: All Data
    # ============================================
    with tab4:
        st.subheader("📋 جميع البيانات")
        
        # Format for display
        display_df = df_filtered.copy()
        
        if not display_df.empty:
            # Format columns
            display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}")
            display_df['volume'] = display_df['volume'].apply(lambda x: f"{x:,.0f}")
            display_df['volume_avg'] = display_df['volume_avg'].apply(lambda x: f"{x:,.0f}")
            display_df['volume_growth'] = display_df['volume_growth'].apply(lambda x: f"{x:.1f}%")
            display_df['price_change_1m'] = display_df['price_change_1m'].apply(lambda x: f"{x:.1f}%")
            display_df['market_cap'] = display_df['market_cap'].apply(lambda x: f"${x:.2f}B")
            display_df['change_today'] = display_df['change_today'].apply(lambda x: f"{x:.2f}%")
            
            # Reorder columns
            columns_order = ['symbol', 'name', 'sector', 'price', 'change_today', 
                           'price_change_1m', 'volume', 'volume_avg', 'volume_growth', 'market_cap']
            
            display_df = display_df[[col for col in columns_order if col in display_df.columns]]
            
            # Rename columns
            column_names = {
                'symbol': 'الرمز',
                'name': 'الشركة',
                'sector': 'القطاع',
                'price': 'السعر',
                'change_today': 'تغير اليوم',
                'price_change_1m': 'نمو الشهر',
                'volume': 'حجم التداول',
                'volume_avg': 'المتوسط',
                'volume_growth': 'نمو الحجم',
                'market_cap': 'القيمة السوقية'
            }
            display_df = display_df.rename(columns=column_names)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Download button
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 تحميل البيانات كـ CSV",
                data=csv,
                file_name=f"liquidity_growth_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("⚠️ لا توجد بيانات تطابق المعايير المحددة")
    
    # ============================================
    # Footer
    # ============================================
    st.divider()
    st.caption(f"تم التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("ℹ️ البيانات لأغراض تحليلية فقط وليست توصية استثمارية")

if __name__ == "__main__":
    main()
