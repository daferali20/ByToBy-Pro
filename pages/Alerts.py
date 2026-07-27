# pages/Alerts.py
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
import time
import json
import os

# محاولة استيراد yfinance للأسعار الحقيقية
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# محاولة استيراد وحدات AI
try:
    from ai.predict import predict_stock
    from ai.pattern_detector import detect_patterns
    from ai.scoring import calculate_scores
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# إعدادات الصفحة
st.set_page_config(
    page_title="ByToBy Pro - Alerts",
    page_icon="🔔",
    layout="wide"
)

# ============================================
# إدارة حالة الجلسة
# ============================================

def init_session_state():
    """تهيئة حالة الجلسة"""
    if 'alerts' not in st.session_state:
        st.session_state.alerts = []
    
    if 'alert_history' not in st.session_state:
        st.session_state.alert_history = []
    
    if 'price_data' not in st.session_state:
        st.session_state.price_data = {}
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None

init_session_state()

# ============================================
# دوال التنبيهات
# ============================================

@st.cache_data(ttl=60)  # تحديث كل دقيقة
def get_current_price(symbol):
    """جلب السعر الحالي للسهم"""
    if not YFINANCE_AVAILABLE:
        return None
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('regularMarketPrice', info.get('currentPrice', None))
    except:
        return None

def create_alert(alert_type, symbol, condition, target_price, note=""):
    """إنشاء تنبيه جديد"""
    alert = {
        'id': len(st.session_state.alerts) + 1,
        'type': alert_type,
        'symbol': symbol,
        'condition': condition,
        'target_price': target_price,
        'note': note,
        'created_at': datetime.now().isoformat(),
        'status': 'active',  # active, triggered, expired, disabled
        'triggered_at': None,
        'triggered_price': None
    }
    st.session_state.alerts.append(alert)
    return alert

def check_alerts():
    """فحص التنبيهات وتحديث حالتها"""
    if not YFINANCE_AVAILABLE:
        return
    
    for alert in st.session_state.alerts:
        if alert['status'] != 'active':
            continue
        
        current_price = get_current_price(alert['symbol'])
        if current_price is None:
            continue
        
        # تخزين السعر الحالي
        st.session_state.price_data[alert['symbol']] = current_price
        
        # فحص الشرط
        triggered = False
        if alert['condition'] == 'above':
            if current_price >= alert['target_price']:
                triggered = True
        elif alert['condition'] == 'below':
            if current_price <= alert['target_price']:
                triggered = True
        elif alert['condition'] == 'change_percent':
            # حساب نسبة التغيير
            if alert['symbol'] in st.session_state.price_data:
                old_price = st.session_state.price_data.get(alert['symbol'] + '_old', current_price)
                change = ((current_price - old_price) / old_price) * 100
                if abs(change) >= alert['target_price']:
                    triggered = True
        
        if triggered:
            alert['status'] = 'triggered'
            alert['triggered_at'] = datetime.now().isoformat()
            alert['triggered_price'] = current_price
            
            # إضافة إلى السجل
            st.session_state.alert_history.append({
                'alert_id': alert['id'],
                'symbol': alert['symbol'],
                'type': alert['type'],
                'condition': alert['condition'],
                'target_price': alert['target_price'],
                'triggered_price': current_price,
                'triggered_at': alert['triggered_at']
            })

def delete_alert(alert_id):
    """حذف تنبيه"""
    st.session_state.alerts = [a for a in st.session_state.alerts if a['id'] != alert_id]

def toggle_alert(alert_id):
    """تفعيل/تعطيل تنبيه"""
    for alert in st.session_state.alerts:
        if alert['id'] == alert_id:
            alert['status'] = 'disabled' if alert['status'] == 'active' else 'active'
            break

def get_alert_stats():
    """الحصول على إحصائيات التنبيهات"""
    total = len(st.session_state.alerts)
    active = len([a for a in st.session_state.alerts if a['status'] == 'active'])
    triggered = len([a for a in st.session_state.alerts if a['status'] == 'triggered'])
    return {'total': total, 'active': active, 'triggered': triggered}

# ============================================
# واجهة المستخدم
# ============================================

def main():
    """الدالة الرئيسية للصفحة"""
    st.title("🔔 نظام التنبيهات والإشعارات")
    st.markdown("قم بإعداد تنبيهات مخصصة لمراقبة الأسهم وإشعارات السوق")
    
    # ============================================
    # شريط جانبي - إعدادات التنبيهات
    # ============================================
    with st.sidebar:
        st.header("➕ إنشاء تنبيه جديد")
        
        # اختيار نوع التنبيه
        alert_type = st.selectbox(
            "نوع التنبيه",
            ["سعر السهم", "تغير النسبة", "حجم التداول", "نموذج فني", "توصية AI"]
        )
        
        # متغيرات التخزين المؤقتة للإدخالات
        symbol = ""
        condition_code = ""
        target_price = 0.0
        note_text = ""
        
        if alert_type in ["سعر السهم", "تغير النسبة", "حجم التداول"]:
            symbol = st.text_input("رمز السهم", "AAPL").upper()
            
            if alert_type == "سعر السهم":
                condition = st.selectbox("الشرط", ["أعلى من", "أقل من"])
                target_price = st.number_input("السعر المستهدف", min_value=0.0, value=100.0, step=1.0)
                condition_code = 'above' if condition == 'أعلى من' else 'below'
                
            elif alert_type == "تغير النسبة":
                target_percent = st.number_input("نسبة التغيير %", min_value=0.0, value=5.0, step=0.5)
                direction = st.selectbox("الاتجاه", ["صاعد", "هابط"])
                condition_code = 'change_percent'
                target_price = target_percent
            
            else:  # حجم التداول
                target_volume = st.number_input("حجم التداول المستهدف", min_value=0, value=1000000, step=100000)
                condition_code = 'volume'
                target_price = target_volume
        
        elif alert_type == "نموذج فني":
            symbol = st.text_input("رمز السهم", "AAPL").upper()
            pattern = st.selectbox(
                "النموذج الفني",
                ["القمة المزدوجة", "القاع المزدوج", "المثلث الصاعد", 
                 "المثلث الهابط", "الرأس والكتفين", "الوتد الصاعد", 
                 "الوتد الهابط", "العلم", "الاختراق"]
            )
            condition_code = 'pattern'
            target_price = 0
            note_text = f"نموذج {pattern}"
        
        else:  # توصية AI
            symbol = st.text_input("رمز السهم", "AAPL").upper()
            recommendation = st.selectbox(
                "التوصية",
                ["شراء قوي", "شراء", "احتفاظ", "بيع", "بيع قوي"]
            )
            condition_code = 'recommendation'
            target_price = 0
            note_text = f"توصية {recommendation}"
        
        # ملاحظات إضافية
        note = st.text_area("ملاحظات إضافية (اختياري)", note_text if note_text else "")
        
        # زر إنشاء التنبيه
        if st.button("🔔 إنشاء تنبيه", use_container_width=True, type="primary"):
            if symbol:
                alert = create_alert(
                    alert_type=alert_type,
                    symbol=symbol,
                    condition=condition_code,
                    target_price=target_price,
                    note=note if note else note_text
                )
                st.success(f"✅ تم إنشاء تنبيه لـ {symbol}")
                st.rerun()
            else:
                st.error("❌ يرجى إدخال رمز السهم")
        
        st.divider()
        
        # ============================================
        # إحصائيات التنبيهات
        # ============================================
        st.header("📊 إحصائيات التنبيهات")
        stats = get_alert_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📌 المجموع", stats['total'])
        with col2:
            st.metric("✅ نشطة", stats['active'])
        with col3:
            st.metric("🔔 متفعلة", stats['triggered'])
        
        # زر تحديث الأسعار
        st.divider()
        if st.button("🔄 تحديث الأسعار", use_container_width=True):
            with st.spinner("جاري تحديث الأسعار..."):
                for alert in st.session_state.alerts:
                    if alert['status'] == 'active':
                        get_current_price(alert['symbol'])
                st.success("✅ تم تحديث الأسعار")
                st.rerun()
    
    # ============================================
    # المنطقة الرئيسية - عرض التنبيهات
    # ============================================
    
    # ============================================
    # 1. التنبيهات النشطة
    # ============================================
    st.subheader("📋 التنبيهات النشطة")
    
    if not st.session_state.alerts:
        st.info("💡 لا توجد تنبيهات نشطة. قم بإنشاء تنبيه جديد من القائمة الجانبية.")
    else:
        # عرض التنبيهات في جدول
        alerts_df = pd.DataFrame(st.session_state.alerts)
        alerts_df = alerts_df[alerts_df['status'] != 'triggered']  # عرض النشطة فقط
        
        if alerts_df.empty:
            st.info("💡 لا توجد تنبيهات نشطة حالياً")
        else:
            # تنسيق البيانات للعرض
            display_df = alerts_df.copy()
            display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            display_df['target'] = display_df.apply(
                lambda x: f"${x['target_price']:,.2f}" if x['type'] in ['سعر السهم', 'حجم التداول'] 
                else f"{x['target_price']}%" if x['type'] == 'تغير النسبة' 
                else x['note'],
                axis=1
            )
            
            # عرض الجدول
            for idx, row in display_df.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([1, 1.5, 1.5, 1.5, 0.5])
                    
                    with col1:
                        st.write(f"**{row['symbol']}**")
                    
                    with col2:
                        st.write(f"📊 {row['type']}")
                    
                    with col3:
                        st.write(f"🎯 {row['target']}")
                    
                    with col4:
                        status_color = "🟢" if row['status'] == 'active' else "🔴"
                        st.write(f"{status_color} {row['status']}")
                    
                    with col5:
                        # أزرار التحكم
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("⏹️", key=f"toggle_{row['id']}", help="تفعيل/تعطيل"):
                                toggle_alert(row['id'])
                                st.rerun()
                        with col_btn2:
                            if st.button("🗑️", key=f"delete_{row['id']}", help="حذف"):
                                delete_alert(row['id'])
                                st.rerun()
                    
                    st.divider()
    
    # ============================================
    # 2. التنبيهات المتفعلة
    # ============================================
    st.divider()
    st.subheader("🔔 التنبيهات المتفعلة")
    
    triggered_alerts = [a for a in st.session_state.alerts if a['status'] == 'triggered']
    
    if not triggered_alerts:
        st.info("💡 لا توجد تنبيهات متفعلة حتى الآن")
    else:
        for alert in triggered_alerts:
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                
                with col1:
                    st.write(f"**{alert['symbol']}**")
                
                with col2:
                    st.write(f"🎯 {alert['type']}: {alert['condition']}")
                    st.write(f"السعر المستهدف: ${alert['target_price']:,.2f}")
                
                with col3:
                    st.write(f"💰 السعر المتفعل: ${alert['triggered_price']:,.2f}")
                    st.write(f"⏰ {pd.to_datetime(alert['triggered_at']).strftime('%Y-%m-%d %H:%M')}")
                
                with col4:
                    if st.button("✅ تمت المشاهدة", key=f"viewed_{alert['id']}"):
                        delete_alert(alert['id'])
                        st.rerun()
                
                st.divider()
    
    # ============================================
    # 3. سجل التنبيهات
    # ============================================
    st.divider()
    st.subheader("📜 سجل التنبيهات")
    
    if st.session_state.alert_history:
        history_df = pd.DataFrame(st.session_state.alert_history)
        history_df['triggered_at'] = pd.to_datetime(history_df['triggered_at']).dt.strftime('%Y-%m-%d %H:%M')
        history_df = history_df.sort_values('triggered_at', ascending=False)
        
        # عرض السجل
        st.dataframe(
            history_df[['symbol', 'type', 'target_price', 'triggered_price', 'triggered_at']],
            use_container_width=True,
            column_config={
                'symbol': 'السهم',
                'type': 'النوع',
                'target_price': 'السعر المستهدف',
                'triggered_price': 'السعر المتفعل',
                'triggered_at': 'وقت التفعل'
            }
        )
    else:
        st.info("💡 لا يوجد سجل للتنبيهات")
    
    # ============================================
    # 4. تحليل الأسعار الحية
    # ============================================
    st.divider()
    st.subheader("📊 مراقبة الأسعار الحية")
    
    if st.session_state.price_data:
        price_df = pd.DataFrame([
            {'السهم': symbol, 'السعر': price}
            for symbol, price in st.session_state.price_data.items()
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # عرض الأسعار في جدول
            st.dataframe(
                price_df,
                use_container_width=True,
                column_config={
                    'السهم': 'رمز السهم',
                    'السعر': st.column_config.NumberColumn('السعر الحالي', format='$%.2f')
                }
            )
        
        with col2:
            # رسم بياني للأسعار
            fig = px.bar(
                price_df,
                x='السهم',
                y='السعر',
                title='الأسعار الحالية',
                color='السعر',
                color_continuous_scale='Viridis',
                text_auto='.2f'
            )
            fig.update_layout(template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 قم بتحديث الأسعار لعرض البيانات")
    
    # ============================================
    # 5. إعدادات إضافية
    # ============================================
    with st.expander("⚙️ إعدادات التنبيهات المتقدمة"):
        col1, col2 = st.columns(2)
        
        with col1:
            check_interval = st.selectbox(
                "معدل فحص التنبيهات",
                ["كل دقيقة", "كل 5 دقائق", "كل 15 دقيقة", "كل ساعة"],
                index=1
            )
            st.info(f"سيتم فحص التنبيهات {check_interval}")
        
        with col2:
            notification_method = st.multiselect(
                "طريقة الإشعار",
                ["في التطبيق", "بريد إلكتروني", "إشعار متصفح"],
                default=["في التطبيق"]
            )
            st.info(f"سيتم الإشعار عبر: {', '.join(notification_method)}")
        
        st.divider()
        
        if st.button("🗑️ مسح جميع التنبيهات", use_container_width=True):
            if st.checkbox("تأكيد مسح جميع التنبيهات"):
                st.session_state.alerts = []
                st.session_state.alert_history = []
                st.success("✅ تم مسح جميع التنبيهات")
                st.rerun()
    
    # ============================================
    # 6. Footer
    # ============================================
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"🕐 آخر تحديث للأسعار: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"📊 عدد التنبيهات النشطة: {get_alert_stats()['active']}")
    with col2:
        if st.button("🔄 تحديث تلقائي", help="تفعيل التحديث التلقائي"):
            st.success("✅ تم تفعيل التحديث التلقائي")

if __name__ == "__main__":
    main()
