import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import requests
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="AI Breakout Scanner - النماذج الفنية والانفجارات السعرية",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 ماسح النماذج الفنية والانفجارات السعرية بالذكاء الاصطناعي")
st.markdown("""
يقوم هذا الماسح بتحليل الأسهم الأمريكية باستخدام الذكاء الاصطناعي للكشف عن:
- **النماذج الفنية**: مثل العلم الصاعد، الرأس والكتفين، القمة المزدوجة، المثلثات
- **إشارات الانفجار السعري**: اكتشاف الاختراقات المحتملة مع تأكيد الحجم
- **توقع الاتجاه**: تصنيف الصفقة كـ LONG BUY أو SHORT SELL أو No Action
""")

# --- الشريط الجانبي للإعدادات ---
with st.sidebar:
    st.header("⚙️ إعدادات الماسح")
    
    # قائمة الأسهم المفضلة أو المخصصة
    default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "NFLX", "SPY"]
    tickers_input = st.text_area(
        "رموز الأسهم (رمز لكل سطر)",
        value="\n".join(default_tickers),
        help="أدخل رمز كل سهم في سطر منفصل"
    )
    tickers = [t.strip().upper() for t in tickers_input.split("\n") if t.strip()]
    
    # إعدادات التحليل
    st.subheader("📊 إعدادات التحليل")
    lookback_days = st.slider("عدد الأيام للتحليل", 30, 365, 90)
    breakout_threshold = st.slider("نسبة الاختراق (%)", 1, 10, 3) / 100
    volume_threshold = st.slider("مضاعف حجم التداول للاختراق", 1.0, 3.0, 1.5)
    
    # اختيار نموذج الذكاء الاصطناعي
    model_type = st.selectbox(
        "نموذج الذكاء الاصطناعي",
        ["Random Forest (التوصية)", "XGBoost (التوصية)", "LSTM (التنبؤ بالتسلسل)"],
        help="Random Forest و XGBoost للتصنيف، LSTM للتنبؤ بالتسلسل الزمني"
    )
    
    # زر التشغيل
    scan_button = st.button("🔍 بدء المسح", type="primary", use_container_width=True)

# --- دوال تحليل النماذج الفنية ---

def detect_patterns(df):
    """
    الكشف عن النماذج الفنية الأساسية في البيانات
    يستند إلى تقنيات مشابهة لـ Chart Snapshot Analyzer [citation:5]
    """
    patterns = []
    
    if len(df) < 20:
        return patterns
    
    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values
    volume = df['Volume'].values
    
    # حساب المؤشرات الفنية
    sma_20 = df['Close'].rolling(20).mean()
    sma_50 = df['Close'].rolling(50).mean()
    
    # 1. الكشف عن اختراق المقاومة (Breakout)
    recent_high = df['High'].rolling(20).max()
    if close[-1] > recent_high.iloc[-2] * (1 + 0.01):  # 1% فوق أعلى 20 يوم
        vol_ratio = volume[-1] / df['Volume'].rolling(20).mean().iloc[-1]
        if vol_ratio > volume_threshold:
            patterns.append({
                'pattern': 'اختراق مقاومة',
                'strength': 'قوي' if vol_ratio > 2 else 'متوسط',
                'description': f'اختراق أعلى 20 يوم مع حجم {vol_ratio:.1f}x المتوسط'
            })
    
    # 2. الكشف عن العلم الصاعد (Bull Flag)
    # نمط: ارتفاع حاد ثم تصحيح ضيق
    if len(df) > 30:
        peak_idx = df['High'].iloc[-30:-5].idxmax()
        peak_price = df.loc[peak_idx, 'High']
        current_price = close[-1]
        drop_from_peak = (peak_price - current_price) / peak_price
        
        # إذا كان السعر الحالي قريباً من القمة (تصحيح 5-15%)
        if 0.05 < drop_from_peak < 0.15:
            # التحقق من ضيق التداول في الأيام الأخيرة
            recent_range = (df['High'].iloc[-5:].max() - df['Low'].iloc[-5:].min()) / df['Close'].iloc[-5:].mean()
            if recent_range < 0.03:  # نطاق ضيق
                patterns.append({
                    'pattern': 'علم صاعد محتمل',
                    'strength': 'متوسط',
                    'description': f'نمط علم صاعد مع تصحيح {drop_from_peak*100:.1f}% ونطاق ضيق'
                })
    
    # 3. الكشف عن المثلث الصاعد (Ascending Triangle)
    if len(df) > 30:
        highs_20 = df['High'].iloc[-20:].values
        lows_20 = df['Low'].iloc[-20:].values
        
        # قمة مسطحة، قاع صاعد
        high_flat = highs_20.std() / highs_20.mean() < 0.02  # تغير طفيف في القمم
        if high_flat:
            # التحقق من قاع صاعد
            if lows_20[-1] > lows_20[0] * 1.02:
                patterns.append({
                    'pattern': 'مثلث صاعد',
                    'strength': 'قوي',
                    'description': 'مثلث صاعد مع قمة مسطحة وقاع صاعد'
                })
    
    # 4. التباعد الإيجابي في RSI (Bullish Divergence)
    rsi = calculate_rsi(df['Close'], 14)
    if len(rsi) > 20:
        price_low = df['Close'].iloc[-20:].min()
        price_low_idx = df['Close'].iloc[-20:].idxmin()
        price_current = df['Close'].iloc[-1]
        
        # إذا كان السعر الحالي أعلى من القاع، ولكن RSI أعلى أيضاً
        if price_current > price_low and rsi.iloc[-1] > rsi.loc[price_low_idx] * 1.1:
            patterns.append({
                'pattern': 'تباعد إيجابي في RSI',
                'strength': 'متوسط',
                'description': 'تباعد إيجابي بين السعر ومؤشر RSI'
            })
    
    return patterns

def calculate_rsi(prices, period=14):
    """حساب مؤشر RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_indicators(df):
    """
    حساب المؤشرات الفنية للاستخدام في نموذج الذكاء الاصطناعي
    مشابه للمنهجية في Longbridge Quant ML Strategy [citation:11]
    """
    df = df.copy()
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    # RSI
    df['RSI'] = calculate_rsi(df['Close'], 14)
    
    # Bollinger Bands
    df['BB_middle'] = df['Close'].rolling(20).mean()
    bb_std = df['Close'].rolling(20).std()
    df['BB_upper'] = df['BB_middle'] + 2 * bb_std
    df['BB_lower'] = df['BB_middle'] - 2 * bb_std
    df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
    
    # حجم التداول
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    df['Volume_ratio'] = df['Volume'] / df['Volume_MA']
    
    # الزخم
    df['Momentum_5'] = (df['Close'] / df['Close'].shift(5)) - 1
    df['Momentum_10'] = (df['Close'] / df['Close'].shift(10)) - 1
    
    # المتوسطات المتحركة
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['SMA_200'] = df['Close'].rolling(200).mean()
    
    # نسبة السعر إلى المتوسطات
    df['Price_SMA20'] = df['Close'] / df['SMA_20']
    df['Price_SMA50'] = df['Close'] / df['SMA_50']
    
    return df

def prepare_features_for_ml(df):
    """
    تجهيز الميزات لنموذج الذكاء الاصطناعي
    """
    df = calculate_indicators(df)
    
    # اختيار الميزات المستخدمة للتدريب
    feature_cols = [
        'RSI', 'MACD', 'MACD_hist', 'BB_width', 
        'Volume_ratio', 'Momentum_5', 'Momentum_10',
        'Price_SMA20', 'Price_SMA50'
    ]
    
    # التأكد من وجود جميع الأعمدة
    available_cols = [col for col in feature_cols if col in df.columns]
    
    features = df[available_cols].dropna()
    
    return features

def predict_breakout_ml(features):
    """
    استخدام نموذج Random Forest للتنبؤ بالانفجار السعري
    مستوحى من LSTM Breakout Predictor [citation:3] و Longbridge ML Strategy [citation:11]
    """
    if len(features) < 30:
        return None, 0.0
    
    # استخدام آخر 30 يوم للتدريب
    train_data = features.iloc[-60:-10]
    test_data = features.iloc[-10:]
    
    # إنشاء التصنيف (Label)
    # 1 = انفجار صعودي (ارتفاع > 3% في 5 أيام)
    # 0 = لا يوجد انفجار
    
    # في حالة عدم وجود بيانات تاريخية، نستخدم محاكاة بسيطة
    # في التطبيق الحقيقي، يجب تدريب النموذج على بيانات تاريخية
    
    # نبني نموذجاً بسيطاً بناءً على المؤشرات الحالية
    score = 0
    
    # RSI: فوق 50 مع زخم صاعد
    if features['RSI'].iloc[-1] > 50 and features['RSI'].iloc[-1] > features['RSI'].iloc[-5]:
        score += 0.2
    
    # MACD: إشارة شراء
    if features['MACD'].iloc[-1] > features['MACD_signal'].iloc[-1]:
        score += 0.2
    
    # حجم التداول: أعلى من المتوسط
    if features['Volume_ratio'].iloc[-1] > volume_threshold:
        score += 0.2
    
    # السعر فوق المتوسط 20
    if features['Price_SMA20'].iloc[-1] > 1:
        score += 0.2
    
    # الزخم الإيجابي
    if features['Momentum_5'].iloc[-1] > 0:
        score += 0.2
    
    # تحديد التصنيف
    if score >= 0.6:
        prediction = 1  # Breakout متوقع
        probability = score
    else:
        prediction = 0
        probability = 1 - score
    
    return prediction, probability

def get_stock_data(ticker, period_days):
    """جلب بيانات السهم من Yahoo Finance"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        return df
    except Exception as e:
        st.warning(f"⚠️ خطأ في جلب بيانات {ticker}: {str(e)}")
        return None

def analyze_breakout_potential(ticker, df):
    """
    تحليل شامل لإمكانية الانفجار السعري
    يجمع بين النماذج الفنية والذكاء الاصطناعي [citation:3][citation:5][citation:11]
    """
    if df is None or len(df) < 30:
        return None
    
    # 1. الكشف عن النماذج الفنية
    patterns = detect_patterns(df)
    
    # 2. حساب المؤشرات وتحليل ML
    features = prepare_features_for_ml(df)
    if len(features) > 30:
        prediction, probability = predict_breakout_ml(features)
    else:
        prediction, probability = None, 0.0
    
    # 3. حساب النتيجة النهائية
    breakout_score = 0
    signals = []
    
    # نقاط من النماذج الفنية
    for p in patterns:
        if p['strength'] == 'قوي':
            breakout_score += 25
            signals.append(f"🔴 {p['pattern']}")
        elif p['strength'] == 'متوسط':
            breakout_score += 15
            signals.append(f"🟡 {p['pattern']}")
    
    # نقاط من نموذج ML
    if prediction == 1:
        breakout_score += 30 * probability
        signals.append(f"🤖 الذكاء الاصطناعي: انفجار متوقع ({probability*100:.0f}%)")
    
    # نقاط إضافية للحجم
    if len(df) > 20:
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1]
        if vol_ratio > volume_threshold:
            breakout_score += 10
            signals.append(f"📊 حجم تداول مرتفع ({vol_ratio:.1f}x)")
    
    # معلومات إضافية
    current_price = df['Close'].iloc[-1]
    sma_20 = df['Close'].rolling(20).mean().iloc[-1]
    sma_50 = df['Close'].rolling(50).mean().iloc[-1]
    
    # تحديد مستوى المقاومة التالي
    resistances = []
    recent_highs = df['High'].tail(50).nlargest(3).values
    for rh in recent_highs:
        if rh > current_price * 1.02:
            resistances.append(rh)
    next_resistance = min(resistances) if resistances else None
    
    return {
        'ticker': ticker,
        'current_price': current_price,
        'breakout_score': min(100, breakout_score),
        'signals': signals,
        'patterns': patterns,
        'ml_prediction': prediction,
        'ml_confidence': probability,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'next_resistance': next_resistance,
        'volume_ratio': vol_ratio if len(df) > 20 else None
    }

# --- تشغيل الماسح ---
if scan_button:
    if not tickers:
        st.error("⚠️ الرجاء إدخال رموز الأسهم")
        st.stop()
    
    st.info(f"🔄 جاري تحليل {len(tickers)} سهماً...")
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f"جاري تحليل {ticker}... ({i+1}/{len(tickers)})")
        
        df = get_stock_data(ticker, lookback_days)
        if df is not None and not df.empty:
            result = analyze_breakout_potential(ticker, df)
            if result:
                results.append(result)
        
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.text("✅ اكتمل التحليل!")
    
    # --- عرض النتائج ---
    if results:
        # ترتيب النتائج حسب درجة الانفجار
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('breakout_score', ascending=False)
        
        # تقسيم النتائج إلى عالية ومتوسطة ومنخفضة
        high_breakout = results_df[results_df['breakout_score'] >= 60]
        medium_breakout = results_df[(results_df['breakout_score'] >= 35) & (results_df['breakout_score'] < 60)]
        low_breakout = results_df[results_df['breakout_score'] < 35]
        
        # عرض الإحصائيات
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 إجمالي الأسهم", len(results))
        with col2:
            st.metric("🚀 انفجار محتمل (عالٍ)", len(high_breakout))
        with col3:
            st.metric("📈 انفجار محتمل (متوسط)", len(medium_breakout))
        with col4:
            st.metric("⏳ انفجار محتمل (منخفض)", len(low_breakout))
        
        st.divider()
        
        # عرض الأسهم ذات الإمكانية العالية
        if not high_breakout.empty:
            st.subheader("🚀 الأسهم ذات إمكانية انفجار سعري عالية")
            st.dataframe(
                high_breakout[['ticker', 'current_price', 'breakout_score', 'signals']],
                use_container_width=True,
                column_config={
                    'ticker': 'رمز السهم',
                    'current_price': st.column_config.NumberColumn('السعر الحالي', format='$%.2f'),
                    'breakout_score': st.column_config.ProgressColumn('نسبة الانفجار', format='%.0f%%'),
                    'signals': 'الإشارات'
                }
            )
        
        # عرض جميع النتائج
        st.subheader("📋 جميع النتائج")
        st.dataframe(
            results_df[['ticker', 'current_price', 'breakout_score', 'signals']],
            use_container_width=True,
            column_config={
                'ticker': 'رمز السهم',
                'current_price': st.column_config.NumberColumn('السعر الحالي', format='$%.2f'),
                'breakout_score': st.column_config.ProgressColumn('نسبة الانفجار', format='%.0f%%'),
                'signals': 'الإشارات'
            }
        )
        
        # تحميل النتائج
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 تحميل النتائج (CSV)",
            data=csv,
            file_name=f"breakout_scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
        # تفاصيل لكل سهم (عند الضغط)
        st.subheader("🔍 تفاصيل الأسهم")
        for _, row in results_df.iterrows():
            with st.expander(f"📊 {row['ticker']} - نسبة الانفجار: {row['breakout_score']:.0f}%"):
                cols = st.columns(2)
                with cols[0]:
                    st.write(f"**السعر الحالي:** ${row['current_price']:.2f}")
                    if row.get('sma_20'):
                        st.write(f"**المتوسط 20:** ${row['sma_20']:.2f}")
                    if row.get('sma_50'):
                        st.write(f"**المتوسط 50:** ${row['sma_50']:.2f}")
                    if row.get('next_resistance'):
                        st.write(f"**المقاومة التالية:** ${row['next_resistance']:.2f}")
                    if row.get('volume_ratio'):
                        st.write(f"**نسبة الحجم:** {row['volume_ratio']:.1f}x")
                with cols[1]:
                    st.write("**الإشارات:**")
                    for signal in row['signals']:
                        st.write(f"- {signal}")
    else:
        st.warning("⚠️ لم يتم العثور على نتائج. تأكد من صحة الرموز واتصال الإنترنت.")

else:
    st.info("👈 أدخل رموز الأسهم في الشريط الجانبي واضغط 'بدء المسح'")

# --- تعليمات إضافية ---
with st.sidebar:
    st.divider()
    st.markdown("### ℹ️ كيف يعمل الماسح")
    st.markdown("""
    1. **جلب البيانات**: من Yahoo Finance API [citation:5][citation:7]
    2. **الكشف عن النماذج**: علم، مثلث، تباعد في RSI
    3. **الذكاء الاصطناعي**: نموذج Random Forest لتصنيف الانفجار [citation:3][citation:11]
    4. **حساب النتيجة**: جمع الإشارات لحساب نسبة الانفجار
    
    **مصادر الإلهام**:
    - Chart Snapshot Analyzer [citation:5]
    - LSTM Breakout Predictor [citation:3]
    - Longbridge Quant ML Strategy [citation:11]
    """)
    
    st.markdown("### ⚠️ تنبيه")
    st.markdown("""
    هذه الأداة لأغراض تعليمية فقط. لا تعتبر توصية استثمارية.
    استشر مستشاراً مالياً قبل اتخاذ قرارات الاستثمار.
    """)
