# pages/Profile.py
import sys
from pathlib import Path

# إضافة المسار الصحيح للمشروع
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px

# التحقق من تسجيل الدخول
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.switch_page("pages/Login.py")

# إعدادات الصفحة
st.set_page_config(
    page_title="ByToBy Pro - الملف الشخصي",
    page_icon="👤",
    layout="wide"
)

def get_user_portfolio_summary():
    """الحصول على ملخص محفظة المستخدم"""
    if 'portfolio' in st.session_state and st.session_state.portfolio:
        total_value = sum(entry['current_value'] for entry in st.session_state.portfolio)
        total_cost = sum(entry['total_cost'] for entry in st.session_state.portfolio)
        total_gain = total_value - total_cost
        gain_percent = (total_gain / total_cost * 100) if total_cost > 0 else 0
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_gain': total_gain,
            'gain_percent': gain_percent,
            'num_stocks': len(st.session_state.portfolio)
        }
    return None

def main():
    """الدالة الرئيسية للصفحة"""
    st.title("👤 الملف الشخصي")
    
    # ============================================
    # معلومات المستخدم
    # ============================================
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://ui-avatars.com/api/?name=" + st.session_state.username + "&size=150&background=00ff88&color=000&bold=true", 
                 width=150)
        
        st.markdown(f"""
        ### 👋 مرحباً، {st.session_state.username}
        
        **الدور:** {st.session_state.user_role}
        **البريد:** {st.session_state.user_email if st.session_state.user_email else 'غير محدد'}
        **عضو منذ:** {datetime.now().strftime('%Y-%m-%d')}
        """)
        
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            for key in ['logged_in', 'username', 'user_role', 'user_email']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        st.subheader("📊 إحصائيات المستخدم")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        # إحصائيات المحفظة
        portfolio_summary = get_user_portfolio_summary()
        if portfolio_summary:
            with col_a:
                st.metric("💰 قيمة المحفظة", f"${portfolio_summary['total_value']:,.2f}")
            with col_b:
                st.metric("📈 إجمالي الأرباح", f"${portfolio_summary['total_gain']:,.2f}",
                         delta=f"{portfolio_summary['gain_percent']:.1f}%")
            with col_c:
                st.metric("📊 عدد الأسهم", portfolio_summary['num_stocks'])
            with col_d:
                st.metric("🔄 عدد المعاملات", len(st.session_state.get('transactions', [])))
        else:
            st.info("💡 لم تقم بإضافة أي أسهم للمحفظة بعد")
    
    st.divider()
    
    # ============================================
    # سجل النشاطات
    # ============================================
    st.subheader("📋 سجل النشاطات")
    
    # بيانات تجريبية للنشاطات
    activities = [
        {"التاريخ": "2026-07-28 14:30", "النشاط": "شراء", "السهم": "AAPL", "الكمية": 10, "السعر": "$185.50"},
        {"التاريخ": "2026-07-28 10:15", "النشاط": "بيع", "السهم": "TSLA", "الكمية": 5, "السعر": "$245.60"},
        {"التاريخ": "2026-07-27 16:45", "النشاط": "شراء", "السهم": "MSFT", "الكمية": 15, "السعر": "$420.30"},
        {"التاريخ": "2026-07-27 09:20", "النشاط": "شراء", "السهم": "GOOGL", "الكمية": 8, "السعر": "$175.80"},
    ]
    
    activities_df = pd.DataFrame(activities)
    st.dataframe(activities_df, use_container_width=True)
    
    # ============================================
    # إعدادات المستخدم
    # ============================================
    st.divider()
    st.subheader("⚙️ إعدادات المستخدم")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔔 إعدادات الإشعارات**")
        email_notifications = st.checkbox("إشعارات البريد الإلكتروني", value=True)
        price_alerts = st.checkbox("تنبيهات الأسعار", value=True)
        daily_summary = st.checkbox("ملخص يومي", value=False)
        
        if st.button("💾 حفظ إعدادات الإشعارات", use_container_width=True):
            st.success("✅ تم حفظ الإعدادات")
    
    with col2:
        st.markdown("**🎨 تفضيلات العرض**")
        theme = st.selectbox("المظهر", ["داكن", "فاتح", "تلقائي"])
        language = st.selectbox("اللغة", ["العربية", "English"])
        chart_style = st.selectbox("نمط الرسوم البيانية", ["حديث", "كلاسيكي", "بسيط"])
        
        if st.button("💾 حفظ تفضيلات العرض", use_container_width=True):
            st.success("✅ تم حفظ التفضيلات")
    
    # ============================================
    # Footer
    # ============================================
    st.divider()
    st.caption(f"🕐 آخر زيارة: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
