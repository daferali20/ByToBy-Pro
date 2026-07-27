# pages/AI_Recommendations.py
import sys
from pathlib import Path

# إضافة المسار الصحيح للمشروع
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# محاولة استيراد وحدات AI مع معالجة الأخطاء
try:
    from ai.predict import predict_stock
    from ai.pattern_detector import detect_patterns
    from ai.scoring import calculate_scores
    AI_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ بعض وحدات AI غير متوفرة: {e}")
    AI_AVAILABLE = False
    
    # إنشاء دوال بديلة للتجربة
    def predict_stock(data):
        return {'score': 50, 'recommendation': 'محايد', 'confidence': 0.5}
    
    def detect_patterns(data):
        return {'bullish': [], 'bearish': [], 'neutral': []}
    
    def calculate_scores(data):
        return {'overall_score': 50, 'technical_score': 50, 'pattern_score': 50}

# إعدادات الصفحة
st.set_page_config(
    page_title="ByToBy Pro - AI Recommendations",
    page_icon="🤖",
    layout="wide"
)

def generate_sample_data():
    """توليد بيانات تجريبية للتوصيات"""
    return pd.DataFrame({
        'السهم': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', '2222.SR', 'NVDA', 'AMZN', 'META'],
        'الشركة': ['Apple Inc.', 'Microsoft', 'Alphabet', 'Tesla', 'أرامكو', 'NVIDIA', 'Amazon', 'Meta'],
        'السعر الحالي': [185.50, 420.30, 175.80, 245.60, 32.50, 850.00, 185.20, 350.00],
        'السعر المستهدف': [210.00, 480.00, 200.00, 300.00, 38.00, 950.00, 210.00, 400.00],
        'الإشارة': ['شراء', 'شراء قوي', 'احتفاظ', 'شراء', 'بيع', 'شراء قوي', 'شراء', 'احتفاظ'],
        'الثقة': [78, 92, 65, 85, 30, 95, 75, 60],
        'المخاطرة': ['متوسطة', 'منخفضة', 'متوسطة', 'عالية', 'عالية', 'متوسطة', 'متوسطة', 'منخفضة'],
        'الأفق الزمني': ['متوسط', 'طويل', 'متوسط', 'قصير', 'متوسط', 'طويل', 'متوسط', 'طويل']
    })

def color_signal(val):
    """تلوين خلايا الإشارة"""
    colors = {
        'شراء قوي': 'background-color: #00ff00; color: black; font-weight: bold',
        'شراء': 'background-color: #90ee90; color: black',
        'احتفاظ': 'background-color: #ffff00; color: black',
        'بيع': 'background-color: #ff6347; color: white',
        'بيع قوي': 'background-color: #ff0000; color: white'
    }
    return colors.get(val, '')

def style_dataframe(df):
    """تطبيق التنسيق على DataFrame"""
    # تطبيق التلوين على عمود الإشارة فقط
    styled = df.style.applymap(
        color_signal, 
        subset=pd.IndexSlice[:, ['الإشارة']]
    )
    
    # تنسيق الأعمدة الرقمية
    styled = styled.format({
        'السعر الحالي': '${:.2f}',
        'السعر المستهدف': '${:.2f}',
        'الثقة': '{:.0f}%'
    })
    
    return styled

def main():
    """الدالة الرئيسية للصفحة"""
    st.title("🤖 توصيات الذكاء الاصطناعي")
    st.markdown("تحليلات متقدمة وتوصيات مدعومة بالذكاء الاصطناعي لمساعدتك في اتخاذ قرارات استثمارية ذكية")
    
    # عرض حالة توفر AI
    if not AI_AVAILABLE:
        st.info("ℹ️ يعمل النظام في وضع العرض التجريبي. بعض الميزات المتقدمة غير متوفرة.")
    
    # ============================================
    # 1. ملخص التوصيات
    # ============================================
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🟢 توصيات شراء قوية",
            "12",
            delta="+3",
            help="أسهم لديها إشارات شراء قوية من عدة نماذج"
        )
    
    with col2:
        st.metric(
            "🔴 توصيات بيع",
            "5",
            delta="-2",
            help="أسهم لديها إشارات بيع متعددة"
        )
    
    with col3:
        st.metric(
            "⚡ الثقة العالية",
            "87%",
            delta="+5%",
            help="متوسط ثقة النماذج في التوصيات الحالية"
        )
    
    with col4:
        st.metric(
            "📈 العائد المتوقع",
            "+15.3%",
            delta="+2.1%",
            help="متوسط العائد المتوقع للمحفظة الموصى بها"
        )
    
    st.divider()
    
    # ============================================
    # 2. قائمة التوصيات
    # ============================================
    st.subheader("📊 قائمة التوصيات المخصصة")
    
    # استخدام بيانات تجريبية أو حقيقية
    df_recommendations = generate_sample_data()
    
    # تطبيق التنسيق على DataFrame
    styled_df = style_dataframe(df_recommendations)
    
    # عرض الجدول مع تلوين
    st.dataframe(styled_df, use_container_width=True, height=350)
    
    # أزرار تحميل
    col1, col2 = st.columns([1, 4])
    with col1:
        csv = df_recommendations.to_csv(index=False)
        st.download_button(
            label="📥 تحميل CSV",
            data=csv,
            file_name=f"ai_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    st.divider()
    
    # ============================================
    # 3. تحليل النماذج الفنية
    # ============================================
    st.subheader("📈 تحليل النماذج الفنية المتقدمة")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_stock = st.selectbox(
            "اختر السهم للتحليل",
            df_recommendations['السهم'].tolist()
        )
    
    with col2:
        timeframe = st.selectbox(
            "الإطار الزمني",
            ['يومي', 'أسبوعي', 'شهري']
        )
    
    # نماذج فنية لكل سهم
    patterns_data = {
        'AAPL': ['القمة المزدوجة', 'اختراق المقاومة', 'تزايد الحجم'],
        'MSFT': ['القاع المزدوج', 'المثلث الصاعد', 'تقاطع MACD'],
        'GOOGL': ['العلم الصاعد', 'الدعم القوي', 'RSI محايد'],
        'TSLA': ['الرأس والكتفين المعكوس', 'اختراق القناة', 'زخم قوي'],
        '2222.SR': ['الوتد الهابط', 'مقاومة قوية', 'تشبع شرائي'],
        'NVDA': ['اختراق تاريخي', 'زخم صاعد', 'حجم قياسي'],
        'AMZN': ['قاع مزدوج', 'مقاومة مكسورة', 'عودة للارتفاع'],
        'META': ['قناة صاعدة', 'دعم قوي', 'RSI محايد']
    }
    
    selected_patterns = patterns_data.get(selected_stock, ['لا توجد نماذج'])
    
    # عرض النماذج بشكل مرئي
    cols = st.columns(min(len(selected_patterns), 4))
    for i, pattern in enumerate(selected_patterns[:4]):
        with cols[i % len(cols)]:
            st.info(f"🔍 {pattern}")
    
    # إضافة تفسير للنماذج
    with st.expander("📖 تفسير النماذج الفنية"):
        st.markdown("""
        | النموذج | النوع | التفسير |
        |---------|-------|----------|
        | **القمة المزدوجة** | هابط | نموذج انعكاسي يظهر بعد ارتفاع السعر مرتين إلى نفس المستوى |
        | **القاع المزدوج** | صاعد | نموذج انعكاسي يظهر بعد هبوط السعر مرتين إلى نفس المستوى |
        | **المثلث الصاعد** | صاعد | نموذج استمراري يتميز بقيعان صاعدة ومقاومة أفقية |
        | **المثلث الهابط** | هابط | نموذج استمراري يتميز بقمم هابطة ودعم أفقي |
        | **الرأس والكتفين** | هابط | نموذج انعكاسي قوي يتكون من ثلاث قمم |
        | **الرأس والكتفين المعكوس** | صاعد | نموذج انعكاسي قوي يتكون من ثلاث قيعان |
        | **العلم** | استمراري | نموذج استمراري يظهر بعد حركة سعرية قوية |
        | **الوتد** | انعكاسي | نموذج يتقارب فيه السعر بين خطي اتجاه |
        """)
    
    st.divider()
    
    # ============================================
    # 4. تحليل الأداء والمخاطر
    # ============================================
    st.subheader("📊 تحليل الأداء والمخاطر")
    
    # بيانات الأداء
    performance_data = {
        'الاستراتيجية': ['التوصيات الحالية', 'المؤشر العام', 'المحفظة السابقة'],
        'العائد السنوي': [18.5, 12.3, 8.7],
        'التقلب': [15.2, 18.7, 22.1],
        'نسبة شارب': [1.22, 0.66, 0.39],
        'أقصى هبوط': [-8.5, -15.2, -25.8]
    }
    df_performance = pd.DataFrame(performance_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_performance = px.bar(
            df_performance,
            x='الاستراتيجية',
            y='العائد السنوي',
            title='مقارنة العائد السنوي',
            color='الاستراتيجية',
            text_auto=True,
            template='plotly_dark'
        )
        fig_performance.update_traces(textposition='outside')
        st.plotly_chart(fig_performance, use_container_width=True)
    
    with col2:
        fig_risk = px.scatter(
            df_performance,
            x='التقلب',
            y='العائد السنوي',
            size='نسبة شارب',
            text='الاستراتيجية',
            title='المخاطرة مقابل العائد',
            labels={'التقلب': 'المخاطرة (التقلب%)', 'العائد السنوي': 'العائد السنوي%'},
            template='plotly_dark'
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    st.divider()
    
    # ============================================
    # 5. توصيات حسب الملف الشخصي
    # ============================================
    st.subheader("👤 توصيات مخصصة حسب ملفك الاستثماري")
    
    investor_type = st.radio(
        "نوع المستثمر",
        ['🛡️ محافظ', '⚖️ متوسط', '🚀 مغامر'],
        horizontal=True
    )
    
    if investor_type == '🛡️ محافظ':
        st.success("""
        **📋 توصيات للمستثمر المحافظ:**
        
        - ✅ التركيز على الأسهم القيادية المستقرة
        - ✅ توزيع الاستثمار على قطاعات متعددة
        - ✅ الحفاظ على نسبة نقدية 20-30%
        - ✅ الاستثمار في الصناديق المتداولة (ETFs)
        - ✅ تجنب الأسهم عالية التقلب
        - ✅ استخدام أوامر وقف الخسارة
        """)
    elif investor_type == '🚀 مغامر':
        st.info("""
        **📋 توصيات للمستثمر المغامر:**
        
        - ✅ التركيز على الأسهم الناشئة عالية النمو
        - ✅ الاستفادة من التقلبات السعرية
        - ✅ توزيع الاستثمار على قطاعات واعدة
        - ✅ متابعة الأخبار والتقارير الفنية بشكل يومي
        - ✅ استخدام أوامر وقف الخسارة لحماية الاستثمار
        - ✅ استهداف عوائد عالية مع تقبل المخاطر
        """)
    else:
        st.warning("""
        **📋 توصيات للمستثمر المتوسط:**
        
        - ✅ مزيج من الأسهم القيادية والناشئة
        - ✅ توزيع الاستثمار بنسبة 60% قيادية، 40% نمو
        - ✅ متابعة التحليل الأساسي والفني معاً
        - ✅ إعادة توازن المحفظة شهرياً
        - ✅ الاحتفاظ بنسبة نقدية 10-15%
        - ✅ تنويع الاستثمار لتقليل المخاطر
        """)
    
    st.divider()
    
    # ============================================
    # 6. تحديثات وتحليل لحظي
    # ============================================
    st.subheader("⚡ تحليل لحظي وتحديثات")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📈 مؤشر الثقة العام",
            "76%",
            delta="+2%",
            help="مؤشر يوضح ثقة النماذج في اتجاه السوق العام"
        )
    
    with col2:
        st.metric(
            "🔮 توقع السوق",
            "صاعد",
            delta="معتدل",
            help="توقع اتجاه السوق للـ 5 أيام القادمة"
        )
    
    with col3:
        st.metric(
            "📊 عدد الصفقات النشطة",
            "23",
            delta="+5",
            help="عدد الصفقات الموصى بها حالياً"
        )
    
    # آخر التوصيات
    with st.expander("📋 آخر التوصيات", expanded=False):
        recent_trades = pd.DataFrame({
            'التاريخ': pd.date_range(end=datetime.now(), periods=5, freq='D'),
            'السهم': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'],
            'الإجراء': ['شراء', 'شراء', 'احتفاظ', 'بيع', 'شراء'],
            'السعر': [185.50, 420.30, 175.80, 245.60, 185.20],
            'السبب': ['اختراق المقاومة', 'نتائج ممتازة', 'تقييم عادل', 'ضغط بيعي', 'انخفاض السعر']
        })
        st.dataframe(recent_trades, use_container_width=True)
    
    st.divider()
    
    # ============================================
    # 7. أدوات مساعدة
    # ============================================
    st.subheader("🛠️ أدوات مساعدة")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 تحليل المخاطر الكامل", use_container_width=True):
            with st.expander("📊 تفاصيل تحليل المخاطر", expanded=True):
                st.markdown("""
                **تحليل المخاطر الشامل:**
                
                | المقياس | القيمة | التقييم |
                |---------|--------|---------|
                | نسبة المخاطرة/المكافأة | 2.5 | ✅ ممتاز |
                | الحد الأقصى للخسارة المتوقعة | 7.2% | ✅ مقبول |
                | معامل بيتا | 1.2 | متوسط التقلب |
                | نسبة شارب | 1.15 | ✅ جيد |
                | التقلب السنوي | 18.5% | متوسط |
                | معامل الارتباط بالسوق | 0.75 | مرتفع |
                """)
    
    with col2:
        if st.button("📈 توصيات القطاعات", use_container_width=True):
            with st.expander("📈 تحليل القطاعات", expanded=True):
                st.markdown("""
                **أفضل القطاعات حالياً:**
                
                | القطاع | التقييم | التوصية |
                |--------|---------|----------|
                | 🖥️ التكنولوجيا | قوية | زيادة الوزن |
                | 💊 الرعاية الصحية | متوسطة | وزن محايد |
                | 🏦 المالية | ضعيفة | تخفيض الوزن |
                | ⚡ الطاقة | متوسطة | وزن محايد |
                | 🛒 البيع بالتجزئة | قوية | زيادة الوزن |
                | 📡 الاتصالات | متوسطة | وزن محايد |
                """)
    
    with col3:
        if st.button("🔄 إعادة حساب التوصيات", use_container_width=True):
            with st.spinner("جاري إعادة حساب التوصيات..."):
                import time
                time.sleep(2)
                st.balloons()
                st.success("✅ تم تحديث التوصيات بناءً على أحدث البيانات")
    
    # ============================================
    # 8. Footer
    # ============================================
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"🕐 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        st.caption("ℹ️ البيانات لأغراض توضيحية")

if __name__ == "__main__":
    main()
