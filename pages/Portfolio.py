# pages/Portfolio.py
import sys
from pathlib import Path

# إضافة المسار الصحيح للمشروع
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json
import time

# محاولة استيراد yfinance للأسعار الحقيقية
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# إعدادات الصفحة
st.set_page_config(
    page_title="ByToBy Pro - Portfolio",
    page_icon="💼",
    layout="wide"
)

# ============================================
# إدارة حالة الجلسة
# ============================================

def init_session_state():
    """تهيئة حالة الجلسة"""
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    
    if 'portfolio_performance' not in st.session_state:
        st.session_state.portfolio_performance = {}
    
    if 'selected_portfolio' not in st.session_state:
        st.session_state.selected_portfolio = None

init_session_state()

# ============================================
# دوال إدارة المحفظة
# ============================================

@st.cache_data(ttl=300)
def get_stock_data(symbol):
    """جلب بيانات السهم من Yahoo Finance"""
    if not YFINANCE_AVAILABLE:
        return None
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1y")
        
        return {
            'info': info,
            'history': hist,
            'current_price': info.get('regularMarketPrice', info.get('currentPrice', 0)),
            'change': info.get('regularMarketChangePercent', 0),
            'market_cap': info.get('marketCap', 0)
        }
    except Exception as e:
        return None

def add_stock_to_portfolio(symbol, shares, purchase_price, purchase_date=None):
    """إضافة سهم إلى المحفظة"""
    if purchase_date is None:
        purchase_date = datetime.now().strftime('%Y-%m-%d')
    
    # جلب بيانات السهم
    stock_data = get_stock_data(symbol)
    current_price = stock_data['current_price'] if stock_data else purchase_price
    
    # إنشاء إدخال المحفظة
    portfolio_entry = {
        'id': len(st.session_state.portfolio) + 1,
        'symbol': symbol,
        'shares': shares,
        'purchase_price': purchase_price,
        'current_price': current_price,
        'purchase_date': purchase_date,
        'total_cost': shares * purchase_price,
        'current_value': shares * current_price,
        'gain_loss': shares * (current_price - purchase_price),
        'gain_loss_percent': ((current_price - purchase_price) / purchase_price) * 100 if purchase_price > 0 else 0,
        'last_updated': datetime.now().isoformat()
    }
    
    st.session_state.portfolio.append(portfolio_entry)
    
    # إضافة إلى سجل المعاملات
    add_transaction('buy', symbol, shares, purchase_price, purchase_date)
    
    return portfolio_entry

def remove_stock_from_portfolio(entry_id):
    """حذف سهم من المحفظة"""
    entry = next((e for e in st.session_state.portfolio if e['id'] == entry_id), None)
    if entry:
        add_transaction('sell', entry['symbol'], entry['shares'], entry['current_price'], datetime.now().strftime('%Y-%m-%d'))
        st.session_state.portfolio = [e for e in st.session_state.portfolio if e['id'] != entry_id]
        return True
    return False

def add_transaction(transaction_type, symbol, shares, price, date):
    """إضافة معاملة إلى السجل"""
    transaction = {
        'id': len(st.session_state.transactions) + 1,
        'type': transaction_type,
        'symbol': symbol,
        'shares': shares,
        'price': price,
        'total': shares * price,
        'date': date,
        'timestamp': datetime.now().isoformat()
    }
    st.session_state.transactions.append(transaction)
    return transaction

def update_portfolio_prices():
    """تحديث أسعار المحفظة"""
    for entry in st.session_state.portfolio:
        stock_data = get_stock_data(entry['symbol'])
        if stock_data:
            current_price = stock_data['current_price']
            entry['current_price'] = current_price
            entry['current_value'] = entry['shares'] * current_price
            entry['gain_loss'] = entry['shares'] * (current_price - entry['purchase_price'])
            entry['gain_loss_percent'] = ((current_price - entry['purchase_price']) / entry['purchase_price']) * 100 if entry['purchase_price'] > 0 else 0
            entry['last_updated'] = datetime.now().isoformat()

def get_portfolio_summary():
    """الحصول على ملخص المحفظة"""
    if not st.session_state.portfolio:
        return {
            'total_value': 0,
            'total_cost': 0,
            'total_gain_loss': 0,
            'total_gain_loss_percent': 0,
            'num_stocks': 0,
            'num_transactions': 0
        }
    
    total_value = sum(entry['current_value'] for entry in st.session_state.portfolio)
    total_cost = sum(entry['total_cost'] for entry in st.session_state.portfolio)
    total_gain_loss = total_value - total_cost
    total_gain_loss_percent = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
    
    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_gain_loss,
        'total_gain_loss_percent': total_gain_loss_percent,
        'num_stocks': len(st.session_state.portfolio),
        'num_transactions': len(st.session_state.transactions)
    }

def get_top_performers(n=3):
    """الحصول على أفضل الأسهم أداءً"""
    if not st.session_state.portfolio:
        return []
    
    sorted_portfolio = sorted(st.session_state.portfolio, key=lambda x: x['gain_loss_percent'], reverse=True)
    return sorted_portfolio[:n]

def get_worst_performers(n=3):
    """الحصول على أسوأ الأسهم أداءً"""
    if not st.session_state.portfolio:
        return []
    
    sorted_portfolio = sorted(st.session_state.portfolio, key=lambda x: x['gain_loss_percent'])
    return sorted_portfolio[:n]

def get_signal_badge(signal):
    """الحصول على علامة HTML للإشارة"""
    badges = {
        'شراء قوي': '<span style="background-color: #00ff00; color: black; padding: 2px 8px; border-radius: 12px; font-weight: bold;">شراء قوي</span>',
        'شراء': '<span style="background-color: #90ee90; color: black; padding: 2px 8px; border-radius: 12px;">شراء</span>',
        'احتفاظ': '<span style="background-color: #ffff00; color: black; padding: 2px 8px; border-radius: 12px;">احتفاظ</span>',
        'بيع': '<span style="background-color: #ff6347; color: white; padding: 2px 8px; border-radius: 12px;">بيع</span>',
        'بيع قوي': '<span style="background-color: #ff0000; color: white; padding: 2px 8px; border-radius: 12px; font-weight: bold;">بيع قوي</span>'
    }
    return badges.get(signal, signal)

def format_gain_loss(val):
    """تنسيق قيمة الربح/الخسارة مع تلوين"""
    if val > 0:
        return f'<span style="color: #00ff00; font-weight: bold;">+${val:,.2f}</span>'
    elif val < 0:
        return f'<span style="color: #ff4444; font-weight: bold;">-${abs(val):,.2f}</span>'
    else:
        return f'<span style="color: #ffffff;">${val:,.2f}</span>'

# ============================================
# واجهة المستخدم
# ============================================

def main():
    """الدالة الرئيسية للصفحة"""
    st.title("💼 إدارة المحفظة الاستثمارية")
    st.markdown("تتبع أداء محفظتك الاستثمارية وإدارة الصفقات")
    
    # تحديث الأسعار تلقائياً
    if st.session_state.portfolio:
        update_portfolio_prices()
    
    # ============================================
    # شريط جانبي - إضافة سهم
    # ============================================
    with st.sidebar:
        st.header("➕ إضافة سهم إلى المحفظة")
        
        with st.form("add_stock_form"):
            symbol = st.text_input("رمز السهم", "AAPL").upper()
            
            col1, col2 = st.columns(2)
            with col1:
                shares = st.number_input("عدد الأسهم", min_value=1, value=10, step=1)
            with col2:
                purchase_price = st.number_input("سعر الشراء ($)", min_value=0.01, value=100.0, step=0.01)
            
            purchase_date = st.date_input("تاريخ الشراء", datetime.now())
            
            # عرض السعر الحالي إذا كان متاحاً
            if symbol and YFINANCE_AVAILABLE:
                stock_data = get_stock_data(symbol)
                if stock_data:
                    current_price = stock_data['current_price']
                    st.info(f"💰 السعر الحالي: ${current_price:,.2f}")
                    
                    if shares > 0:
                        total_cost = shares * purchase_price
                        current_value = shares * current_price
                        st.write(f"📊 القيمة المتوقعة: ${current_value:,.2f}")
                        st.write(f"📈 الربح/الخسارة المتوقع: ${current_value - total_cost:,.2f}")
            
            submitted = st.form_submit_button("➕ إضافة إلى المحفظة", use_container_width=True, type="primary")
            
            if submitted and symbol:
                if shares <= 0:
                    st.error("❌ يجب أن يكون عدد الأسهم أكبر من 0")
                elif purchase_price <= 0:
                    st.error("❌ يجب أن يكون سعر الشراء أكبر من 0")
                else:
                    entry = add_stock_to_portfolio(
                        symbol=symbol,
                        shares=shares,
                        purchase_price=purchase_price,
                        purchase_date=purchase_date.strftime('%Y-%m-%d')
                    )
                    st.success(f"✅ تم إضافة {symbol} إلى المحفظة")
                    st.rerun()
        
        st.divider()
        
        # ============================================
        # ملخص سريع للمحفظة
        # ============================================
        st.header("📊 ملخص المحفظة")
        summary = get_portfolio_summary()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 القيمة الإجمالية", f"${summary['total_value']:,.2f}")
            st.metric("📈 إجمالي الربح/الخسارة", f"${summary['total_gain_loss']:,.2f}", 
                     delta=f"{summary['total_gain_loss_percent']:.1f}%")
        with col2:
            st.metric("📊 عدد الأسهم", summary['num_stocks'])
            st.metric("🔄 عدد المعاملات", summary['num_transactions'])
    
    # ============================================
    # المنطقة الرئيسية
    # ============================================
    
    # ============================================
    # 1. نظرة عامة على المحفظة
    # ============================================
    if not st.session_state.portfolio:
        st.info("💡 محفظتك فارغة. قم بإضافة أسهم من القائمة الجانبية.")
    else:
        # عرض إحصائيات إضافية
        col1, col2, col3, col4 = st.columns(4)
        
        summary = get_portfolio_summary()
        
        with col1:
            st.metric(
                "💰 إجمالي القيمة",
                f"${summary['total_value']:,.2f}"
            )
        with col2:
            st.metric(
                "📈 إجمالي الربح/الخسارة",
                f"${summary['total_gain_loss']:,.2f}",
                delta=f"{summary['total_gain_loss_percent']:.1f}%"
            )
        with col3:
            st.metric(
                "📊 عدد الأسهم",
                summary['num_stocks']
            )
        with col4:
            st.metric(
                "🔄 عدد المعاملات",
                summary['num_transactions']
            )
        
        st.divider()
        
        # ============================================
        # 2. جدول المحفظة (باستخدام HTML للتلوين)
        # ============================================
        st.subheader("📋 تفاصيل المحفظة")
        
        # إنشاء DataFrame للعرض
        portfolio_df = pd.DataFrame(st.session_state.portfolio)
        
        # تنسيق DataFrame باستخدام HTML
        display_df = portfolio_df.copy()
        display_df['purchase_price'] = display_df['purchase_price'].apply(lambda x: f"${x:,.2f}")
        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:,.2f}")
        display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"${x:,.2f}")
        display_df['current_value'] = display_df['current_value'].apply(lambda x: f"${x:,.2f}")
        display_df['gain_loss'] = display_df.apply(lambda row: format_gain_loss(row['gain_loss']), axis=1)
        display_df['gain_loss_percent'] = display_df['gain_loss_percent'].apply(
            lambda x: f'<span style="color: {"#00ff00" if x > 0 else "#ff4444" if x < 0 else "#ffffff"};">{x:.1f}%</span>'
        )
        
        # إضافة عمود الإجراءات
        display_df['actions'] = display_df['id'].apply(
            lambda x: f'<button onclick="alert(\'حذف السهم {x}\')">🗑️</button>'
        )
        
        # عرض الجدول مع HTML
        st.markdown("""
        <style>
        .dataframe td {
            white-space: nowrap;
            padding: 8px 12px;
        }
        .dataframe th {
            background-color: #1e1e1e;
            color: white;
            padding: 10px 12px;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # اختيار الأعمدة للعرض
        columns_to_show = ['symbol', 'shares', 'purchase_price', 'current_price', 
                          'total_cost', 'current_value', 'gain_loss', 'gain_loss_percent', 'purchase_date']
        
        display_df = display_df[columns_to_show]
        
        # عرض الجدول
        st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        
        # أزرار إدارة المحفظة
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 تحديث الأسعار", use_container_width=True):
                with st.spinner("جاري تحديث الأسعار..."):
                    update_portfolio_prices()
                    st.success("✅ تم تحديث الأسعار")
                    st.rerun()
        with col2:
            if st.button("📥 تصدير CSV", use_container_width=True):
                csv = portfolio_df.to_csv(index=False)
                st.download_button(
                    label="📥 تحميل CSV",
                    data=csv,
                    file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        st.divider()
        
        # ============================================
        # 3. تحليل الأداء
        # ============================================
        st.subheader("📊 تحليل أداء المحفظة")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # توزيع الأسهم حسب القطاع
            sectors = {
                'AAPL': 'التكنولوجيا',
                'MSFT': 'التكنولوجيا',
                'GOOGL': 'التكنولوجيا',
                'TSLA': 'السيارات',
                'NVDA': 'التكنولوجيا',
                'AMZN': 'البيع بالتجزئة',
                'META': 'التكنولوجيا',
                'JPM': 'المالية',
                'KO': 'السلع الاستهلاكية',
                'PFE': 'الرعاية الصحية'
            }
            
            sector_data = []
            for entry in st.session_state.portfolio:
                sector = sectors.get(entry['symbol'], 'أخرى')
                sector_data.append({
                    'القطاع': sector,
                    'القيمة': entry['current_value']
                })
            
            if sector_data:
                sector_df = pd.DataFrame(sector_data)
                sector_summary = sector_df.groupby('القطاع')['القيمة'].sum().reset_index()
                
                fig_pie = px.pie(
                    sector_summary,
                    values='القيمة',
                    names='القطاع',
                    title='توزيع المحفظة حسب القطاع',
                    template='plotly_dark'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # أداء الأسهم
            performance_df = portfolio_df.copy()
            performance_df = performance_df.sort_values('gain_loss_percent', ascending=False)
            
            fig_bar = px.bar(
                performance_df,
                x='symbol',
                y='gain_loss_percent',
                title='أداء الأسهم (الربح/الخسارة %)',
                color='gain_loss_percent',
                color_continuous_scale=['red', 'yellow', 'green'],
                text_auto='.1f'
            )
            fig_bar.update_layout(template='plotly_dark')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # ============================================
        # 4. أفضل وأسوأ الأسهم أداءً
        # ============================================
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 أفضل الأسهم أداءً")
            top_performers = get_top_performers(3)
            if top_performers:
                for stock in top_performers:
                    st.success(f"""
                    **{stock['symbol']}**  
                    الربح: ${stock['gain_loss']:,.2f} ({stock['gain_loss_percent']:.1f}%)  
                    السعر: ${stock['current_price']:,.2f}
                    """)
            else:
                st.info("لا توجد بيانات")
        
        with col2:
            st.subheader("📉 أسوأ الأسهم أداءً")
            worst_performers = get_worst_performers(3)
            if worst_performers:
                for stock in worst_performers:
                    st.error(f"""
                    **{stock['symbol']}**  
                    الخسارة: ${stock['gain_loss']:,.2f} ({stock['gain_loss_percent']:.1f}%)  
                    السعر: ${stock['current_price']:,.2f}
                    """)
            else:
                st.info("لا توجد بيانات")
        
        # ============================================
        # 5. سجل المعاملات
        # ============================================
        st.divider()
        st.subheader("📜 سجل المعاملات")
        
        if st.session_state.transactions:
            transactions_df = pd.DataFrame(st.session_state.transactions)
            transactions_df = transactions_df.sort_values('timestamp', ascending=False)
            
            # تنسيق البيانات
            display_transactions = transactions_df.copy()
            display_transactions['price'] = display_transactions['price'].apply(lambda x: f"${x:,.2f}")
            display_transactions['total'] = display_transactions['total'].apply(lambda x: f"${x:,.2f}")
            display_transactions['type'] = display_transactions['type'].apply(
                lambda x: '🟢 شراء' if x == 'buy' else '🔴 بيع'
            )
            
            st.dataframe(
                display_transactions[['date', 'type', 'symbol', 'shares', 'price', 'total']],
                use_container_width=True,
                column_config={
                    'date': 'التاريخ',
                    'type': 'النوع',
                    'symbol': 'السهم',
                    'shares': 'العدد',
                    'price': 'السعر',
                    'total': 'الإجمالي'
                },
                height=200
            )
        else:
            st.info("💡 لا توجد معاملات مسجلة")
        
        # ============================================
        # 6. توصيات إضافية
        # ============================================
        st.divider()
        st.subheader("💡 توصيات إضافية")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(st.session_state.portfolio) < 3:
                st.info("📊 **تنويع المحفظة**\n\nيوصى بتنويع استثماراتك عبر قطاعات متعددة لتقليل المخاطر.")
            else:
                st.success("✅ **تنويع جيد**\n\nمحفظتك متنوعة عبر عدة قطاعات.")
        
        with col2:
            if summary['total_gain_loss_percent'] > 20:
                st.warning("⚖️ **إعادة التوازن**\n\nقد يكون من الجيد إعادة توازن محفظتك لجني الأرباح.")
            else:
                st.info("⚖️ **توازن جيد**\n\nأداء محفظتك متوازن.")
        
        with col3:
            if summary['total_gain_loss_percent'] < -10:
                st.error("⚠️ **مخاطر عالية**\n\nقد يكون من الحكمة تقليل المخاطر في محفظتك.")
            else:
                st.info("✅ **مخاطر مقبولة**\n\nمستوى المخاطرة في محفظتك مقبول.")
        
        # ============================================
        # 7. Footer
        # ============================================
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"🕐 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        with col2:
            st.caption("ℹ️ البيانات لأغراض توضيحية")

if __name__ == "__main__":
    main()
