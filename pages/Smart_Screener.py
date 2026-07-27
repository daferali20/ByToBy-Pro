# pages/Smart_Screener.py
import sys
from pathlib import Path
from scanners.pattern_ai import PatternAI
from ai.pattern_score import pattern_score

scanner = PatternAI()

patterns = scanner.scan_all(df)

score = pattern_score(df, patterns)

if score >= 70:
    recommendation = "🔥 نموذج قوي"

elif score >= 50:
    recommendation = "✅ جيد"

else:
    recommendation = "⚠ ضعيف"
# Add project root
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# Import API
try:
    from api import get_portfolio_data, get_price
except ImportError as e:
    st.error(f"❌ خطأ في استيراد API: {e}")
    st.stop()

st.set_page_config(
    page_title="ByToBy Pro - Smart Screener", 
    page_icon="🔍", 
    layout="wide"
)

# ============================================
# Sample Data (for demonstration)
# ============================================
def generate_sample_stocks():
    """Generate sample stock data for screening"""
    np.random.seed(42)
    
    sectors = ["التكنولوجيا", "الطاقة", "المالية", "الرعاية الصحية", "السيارات", "الاتصالات", "البيع بالتجزئة"]
    industries = {
        "التكنولوجيا": ["البرمجيات", "الأجهزة", "الإنترنت", "الذكاء الاصطناعي"],
        "الطاقة": ["النفط", "الغاز", "الطاقة المتجددة"],
        "المالية": ["البنوك", "التأمين", "الاستثمار"],
        "الرعاية الصحية": ["الأدوية", "المستشفيات", "الأجهزة الطبية"],
        "السيارات": ["السيارات الكهربائية", "السيارات التقليدية", "قطع الغيار"],
        "الاتصالات": ["الاتصالات", "التقنية", "الإعلام"],
        "البيع بالتجزئة": ["التجارة الإلكترونية", "المتاجر", "السلع"]
    }
    
    stocks = []
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "2222.SR", "1120.SR", "7010.SR", 
               "NVDA", "META", "NFLX", "JPM", "VTI", "KO", "PFE"]
    
    for i, symbol in enumerate(symbols):
        sector = np.random.choice(sectors)
        industry = np.random.choice(industries.get(sector, ["عام"]))
        
        price = np.random.uniform(10, 500)
        market_cap = np.random.uniform(10, 3000)
        volume = np.random.randint(100000, 5000000)
        pe_ratio = np.random.uniform(5, 50)
        eps = np.random.uniform(0.5, 15)
        dividend_yield = np.random.uniform(0, 5)
        revenue_growth = np.random.uniform(-20, 50)
        profit_margin = np.random.uniform(-10, 40)
        debt_to_equity = np.random.uniform(0, 3)
        
        # Company names
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
            "VTI": "Vanguard Total Stock Market",
            "KO": "Coca-Cola Company",
            "PFE": "Pfizer Inc."
        }
        
        stocks.append({
            "symbol": symbol,
            "companyName": names.get(symbol, f"Company {i+1}"),
            "sector": sector,
            "industry": industry,
            "currentPrice": price,
            "marketCap": market_cap,
            "volume": volume,
            "peRatio": pe_ratio,
            "eps": eps,
            "dividendYield": dividend_yield,
            "revenueGrowth": revenue_growth,
            "profitMargin": profit_margin,
            "debtToEquity": debt_to_equity,
            "country": np.random.choice(["الولايات المتحدة", "السعودية", "الإمارات", "الكويت", "مصر"])
        })
    
    return pd.DataFrame(stocks)

# ============================================
# Main App
# ============================================
def main():
    st.title("🔍 Smart Screener - تصفية الأسهم الذكية")
    st.markdown("قم بتصفية الأسهم بناءً على معاييرك المفضلة")
    
    # Initialize session state
    if 'screener_results' not in st.session_state:
        st.session_state['screener_results'] = None
    
    # ============================================
    # Sidebar - Filters
    # ============================================
    with st.sidebar:
        st.header("🎯 معايير التصفية")
        
        # Data source
        data_source = st.radio(
            "مصدر البيانات",
            ["بيانات تجريبية", "بيانات حقيقية (Yahoo)"],
            index=0,
            help="البيانات التجريبية للعرض، البيانات الحقيقية تتطلب اتصال بالإنترنت"
        )
        
        st.markdown("---")
        
        # Sector filter
        sectors = ["الكل", "التكنولوجيا", "الطاقة", "المالية", "الرعاية الصحية", 
                   "السيارات", "الاتصالات", "البيع بالتجزئة"]
        selected_sector = st.selectbox("القطاع", sectors)
        
        st.markdown("---")
        
        # Price range
        st.subheader("💰 نطاق السعر")
        price_range = st.slider(
            "السعر ($)",
            min_value=0,
            max_value=500,
            value=(0, 500),
            step=10
        )
        
        st.markdown("---")
        
        # Market Cap range
        st.subheader("📊 القيمة السوقية")
        market_cap_range = st.slider(
            "القيمة السوقية (بالمليارات $)",
            min_value=0,
            max_value=3000,
            value=(0, 3000),
            step=50
        )
        
        st.markdown("---")
        
        # Additional filters
        st.subheader("📈 مؤشرات مالية")
        
        col1, col2 = st.columns(2)
        with col1:
            min_pe = st.number_input("نسبة PE (الحد الأدنى)", min_value=0.0, value=0.0, step=0.5)
            min_eps = st.number_input("ربحية السهم (الحد الأدنى)", min_value=0.0, value=0.0, step=0.1)
        
        with col2:
            min_dividend = st.number_input("نسبة التوزيع (الحد الأدنى %)", min_value=0.0, value=0.0, step=0.5)
            min_growth = st.number_input("نمو الإيرادات (الحد الأدنى %)", min_value=-100.0, value=-100.0, step=5.0)
        
        st.markdown("---")
        
        # Sort options
        st.subheader("🔽 ترتيب النتائج")
        sort_by = st.selectbox(
            "ترتيب حسب",
            ["القيمة السوقية", "السعر", "حجم التداول", "نسبة PE", "نمو الإيرادات", "نسبة التوزيع"]
        )
        sort_order = st.radio("الترتيب", ["تنازلي", "تصاعدي"], horizontal=True)
        
        st.markdown("---")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            search_clicked = st.button("🔍 بحث", use_container_width=True, type="primary")
        with col2:
            reset_clicked = st.button("🔄 إعادة تعيين", use_container_width=True)
        
        if reset_clicked:
            st.session_state['screener_results'] = None
            st.rerun()
    
    # ============================================
    # Main Area
    # ============================================
    
    # Load data
    if data_source == "بيانات حقيقية (Yahoo)":
        try:
            # Try to get real data
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "2222.SR", "1120.SR", "7010.SR"]
            data = get_portfolio_data(symbols)
            df = pd.DataFrame(data)
            
            # Add missing columns for screener
            if not df.empty:
                df['peRatio'] = np.random.uniform(5, 50, len(df))
                df['eps'] = np.random.uniform(0.5, 15, len(df))
                df['dividendYield'] = np.random.uniform(0, 5, len(df))
                df['revenueGrowth'] = np.random.uniform(-20, 50, len(df))
                df['profitMargin'] = np.random.uniform(-10, 40, len(df))
                df['debtToEquity'] = np.random.uniform(0, 3, len(df))
                df['country'] = "الولايات المتحدة"
        except Exception as e:
            st.warning(f"⚠️ تعذر تحميل البيانات الحقيقية: {e}")
            df = generate_sample_stocks()
    else:
        df = generate_sample_stocks()
    
    # Apply filters
    filtered_df = df.copy()
    
    # Filter by sector
    if selected_sector != "الكل":
        filtered_df = filtered_df[filtered_df['sector'] == selected_sector]
    
    # Filter by price
    filtered_df = filtered_df[
        (filtered_df['currentPrice'] >= price_range[0]) & 
        (filtered_df['currentPrice'] <= price_range[1])
    ]
    
    # Filter by market cap
    filtered_df = filtered_df[
        (filtered_df['marketCap'] >= market_cap_range[0]) & 
        (filtered_df['marketCap'] <= market_cap_range[1])
    ]
    
    # Filter by PE ratio
    if min_pe > 0:
        filtered_df = filtered_df[filtered_df['peRatio'] >= min_pe]
    
    # Filter by EPS
    if min_eps > 0:
        filtered_df = filtered_df[filtered_df['eps'] >= min_eps]
    
    # Filter by dividend yield
    if min_dividend > 0:
        filtered_df = filtered_df[filtered_df['dividendYield'] >= min_dividend]
    
    # Filter by revenue growth
    if min_growth > -100:
        filtered_df = filtered_df[filtered_df['revenueGrowth'] >= min_growth]
    
    # Sort
    sort_map = {
        "القيمة السوقية": "marketCap",
        "السعر": "currentPrice",
        "حجم التداول": "volume",
        "نسبة PE": "peRatio",
        "نمو الإيرادات": "revenueGrowth",
        "نسبة التوزيع": "dividendYield"
    }
    sort_column = sort_map.get(sort_by, "marketCap")
    ascending = sort_order == "تصاعدي"
    filtered_df = filtered_df.sort_values(by=sort_column, ascending=ascending)
    
    # Store results
    if search_clicked:
        st.session_state['screener_results'] = filtered_df
    
    # Display results
    if st.session_state['screener_results'] is not None:
        results = st.session_state['screener_results']
    else:
        results = filtered_df
    
    # ============================================
    # Results Display
    # ============================================
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 إجمالي الأسهم", len(results))
    with col2:
        avg_price = results['currentPrice'].mean() if not results.empty else 0
        st.metric("💰 متوسط السعر", f"${avg_price:.2f}")
    with col3:
        avg_mcap = results['marketCap'].mean() if not results.empty else 0
        st.metric("📈 متوسط القيمة السوقية", f"${avg_mcap:.2f}B")
    with col4:
        avg_growth = results['revenueGrowth'].mean() if not results.empty else 0
        st.metric("🚀 متوسط النمو", f"{avg_growth:.1f}%")
    
    st.divider()
    
    # Results table
    if not results.empty:
        # Format columns for display
        display_df = results.copy()
        display_df['currentPrice'] = display_df['currentPrice'].apply(lambda x: f"${x:.2f}")
        display_df['marketCap'] = display_df['marketCap'].apply(lambda x: f"${x:.2f}B")
        display_df['volume'] = display_df['volume'].apply(lambda x: f"{x:,}")
        display_df['peRatio'] = display_df['peRatio'].apply(lambda x: f"{x:.1f}")
        display_df['eps'] = display_df['eps'].apply(lambda x: f"${x:.2f}")
        display_df['dividendYield'] = display_df['dividendYield'].apply(lambda x: f"{x:.2f}%")
        display_df['revenueGrowth'] = display_df['revenueGrowth'].apply(lambda x: f"{x:.1f}%")
        display_df['profitMargin'] = display_df['profitMargin'].apply(lambda x: f"{x:.1f}%")
        display_df['debtToEquity'] = display_df['debtToEquity'].apply(lambda x: f"{x:.2f}")
        
        # Select columns to show
        columns_to_show = [
            'symbol', 'companyName', 'sector', 'industry', 'currentPrice', 
            'marketCap', 'volume', 'peRatio', 'eps', 'dividendYield',
            'revenueGrowth', 'profitMargin', 'debtToEquity', 'country'
        ]
        
        column_names = {
            'symbol': 'الرمز',
            'companyName': 'الشركة',
            'sector': 'القطاع',
            'industry': 'الصناعة',
            'currentPrice': 'السعر',
            'marketCap': 'القيمة السوقية',
            'volume': 'حجم التداول',
            'peRatio': 'نسبة PE',
            'eps': 'ربحية السهم',
            'dividendYield': 'نسبة التوزيع',
            'revenueGrowth': 'نمو الإيرادات',
            'profitMargin': 'هامش الربح',
            'debtToEquity': 'الدين/حقوق الملكية',
            'country': 'الدولة'
        }
        
        display_df = display_df[[col for col in columns_to_show if col in display_df.columns]]
        display_df = display_df.rename(columns=column_names)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            column_config={
                "الرمز": st.column_config.TextColumn("الرمز", width="small"),
                "الشركة": st.column_config.TextColumn("الشركة", width="medium"),
                "السعر": st.column_config.TextColumn("السعر", width="small"),
                "القيمة السوقية": st.column_config.TextColumn("القيمة السوقية", width="small"),
                "نسبة PE": st.column_config.TextColumn("نسبة PE", width="small"),
            }
        )
        
        # Download button
        csv = results.to_csv(index=False)
        st.download_button(
            label="📥 تحميل النتائج كـ CSV",
            data=csv,
            file_name=f"screener_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # ============================================
        # Visualization
        # ============================================
        st.divider()
        st.subheader("📊 تحليل الرسوم البيانية")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Market Cap by Sector
            if not results.empty and 'sector' in results.columns:
                sector_data = results.groupby('sector')['marketCap'].sum().reset_index()
                fig = px.pie(
                    sector_data,
                    values='marketCap',
                    names='sector',
                    title='توزيع القيمة السوقية حسب القطاع',
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # PE vs Growth scatter
            if not results.empty and 'peRatio' in results.columns and 'revenueGrowth' in results.columns:
                fig = px.scatter(
                    results,
                    x='peRatio',
                    y='revenueGrowth',
                    size='marketCap',
                    color='sector',
                    hover_name='companyName',
                    title='نسبة PE مقابل نمو الإيرادات',
                    labels={'peRatio': 'نسبة PE', 'revenueGrowth': 'نمو الإيرادات (%)'},
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Price distribution
        if not results.empty and 'currentPrice' in results.columns:
            fig = px.histogram(
                results,
                x='currentPrice',
                color='sector',
                title='توزيع الأسعار',
                labels={'currentPrice': 'السعر ($)', 'count': 'عدد الأسهم'},
                template='plotly_dark',
                nbins=30
            )
            st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("⚠️ لا توجد نتائج تطابق معايير البحث")
        st.info("💡 حاول تعديل معايير التصفية لتوسيع نطاق البحث")
    
    # ============================================
    # Footer
    # ============================================
    st.divider()
    st.caption(f"تم التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("ℹ️ البيانات المعروضة هي لأغراض توضيحية فقط وليست توصية استثمارية")

if __name__ == "__main__":
    main()
