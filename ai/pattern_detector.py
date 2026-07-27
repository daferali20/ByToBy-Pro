# ai/pattern_detector.py
"""
كشف النماذج الفنية باستخدام الذكاء الاصطناعي
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

def detect_patterns(data: pd.DataFrame) -> Dict:
    """
    كشف النماذج الفنية في بيانات السهم
    
    Args:
        data: DataFrame يحتوي على بيانات OHLCV
    
    Returns:
        Dictionary مع النماذج المكتشفة
    """
    patterns = {
        'bullish': [],
        'bearish': [],
        'neutral': []
    }
    
    # التحقق من وجود البيانات المطلوبة
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in data.columns for col in required_columns):
        return {'error': 'البيانات غير مكتملة', 'patterns': patterns}
    
    try:
        # كشف النماذج الصاعدة
        bullish_patterns = detect_bullish_patterns(data)
        patterns['bullish'] = bullish_patterns
        
        # كشف النماذج الهابطة
        bearish_patterns = detect_bearish_patterns(data)
        patterns['bearish'] = bearish_patterns
        
        # كشف النماذج المحايدة
        neutral_patterns = detect_neutral_patterns(data)
        patterns['neutral'] = neutral_patterns
        
    except Exception as e:
        return {'error': str(e), 'patterns': patterns}
    
    return patterns

def detect_bullish_patterns(data: pd.DataFrame) -> List[Dict]:
    """كشف النماذج الصاعدة"""
    patterns = []
    
    # التحقق من وجود بيانات كافية
    if len(data) < 20:
        return patterns
    
    close = data['close'].values
    high = data['high'].values
    low = data['low'].values
    
    # 1. نموذج القاع المزدوج
    double_bottom = detect_double_bottom(data)
    if double_bottom:
        patterns.append({
            'name': 'القاع المزدوج',
            'strength': 0.85,
            'description': 'نموذج انعكاسي صاعد قوي',
            'price_target': double_bottom
        })
    
    # 2. نموذج المطرقة
    hammer = detect_hammer(data)
    if hammer:
        patterns.append({
            'name': 'المطرقة',
            'strength': 0.70,
            'description': 'نموذج انعكاسي صاعد في قاع الاتجاه',
            'price_target': None
        })
    
    # 3. نموذج الابتلاع الصاعد
    bullish_engulfing = detect_bullish_engulfing(data)
    if bullish_engulfing:
        patterns.append({
            'name': 'الابتلاع الصاعد',
            'strength': 0.80,
            'description': 'شمعة صاعدة تبتلع الشمعة السابقة',
            'price_target': None
        })
    
    # 4. نموذج الاختراق
    breakout = detect_breakout(data)
    if breakout:
        patterns.append({
            'name': 'اختراق المقاومة',
            'strength': 0.75,
            'description': 'اختراق مستوى مقاومة مهم',
            'price_target': breakout
        })
    
    return patterns

def detect_bearish_patterns(data: pd.DataFrame) -> List[Dict]:
    """كشف النماذج الهابطة"""
    patterns = []
    
    if len(data) < 20:
        return patterns
    
    # 1. نموذج القمة المزدوجة
    double_top = detect_double_top(data)
    if double_top:
        patterns.append({
            'name': 'القمة المزدوجة',
            'strength': 0.85,
            'description': 'نموذج انعكاسي هابط قوي',
            'price_target': double_top
        })
    
    # 2. نموذج النجم المتساقط
    shooting_star = detect_shooting_star(data)
    if shooting_star:
        patterns.append({
            'name': 'النجم المتساقط',
            'strength': 0.70,
            'description': 'نموذج انعكاسي هابط في قمة الاتجاه',
            'price_target': None
        })
    
    # 3. نموذج الابتلاع الهابط
    bearish_engulfing = detect_bearish_engulfing(data)
    if bearish_engulfing:
        patterns.append({
            'name': 'الابتلاع الهابط',
            'strength': 0.80,
            'description': 'شمعة هابطة تبتلع الشمعة السابقة',
            'price_target': None
        })
    
    return patterns

def detect_neutral_patterns(data: pd.DataFrame) -> List[Dict]:
    """كشف النماذج المحايدة"""
    patterns = []
    
    if len(data) < 20:
        return patterns
    
    # 1. نموذج الدوجي
    doji = detect_doji(data)
    if doji:
        patterns.append({
            'name': 'الدوجي',
            'strength': 0.50,
            'description': 'شمعة ذات جسم صغير تشير إلى التردد',
            'price_target': None
        })
    
    # 2. نموذج المثلث
    triangle = detect_triangle(data)
    if triangle:
        patterns.append({
            'name': f'المثلث {triangle["type"]}',
            'strength': 0.60,
            'description': f'نموذج استمراري {triangle["type"]}',
            'price_target': triangle.get('target')
        })
    
    return patterns

# ============================================
# دوال الكشف المساعدة
# ============================================

def detect_double_bottom(data: pd.DataFrame) -> Optional[float]:
    """كشف نموذج القاع المزدوج"""
    if len(data) < 30:
        return None
    
    low = data['low'].values
    # البحث عن قاعين متقاربين
    # (تنفيذ مبسط - يمكن تحسينه)
    return None

def detect_double_top(data: pd.DataFrame) -> Optional[float]:
    """كشف نموذج القمة المزدوجة"""
    if len(data) < 30:
        return None
    
    high = data['high'].values
    # البحث عن قمتين متقاربتين
    # (تنفيذ مبسط - يمكن تحسينه)
    return None

def detect_hammer(data: pd.DataFrame) -> bool:
    """كشف نموذج المطرقة"""
    if len(data) < 2:
        return False
    
    last = data.iloc[-1]
    body = abs(last['close'] - last['open'])
    lower_shadow = min(last['close'], last['open']) - last['low']
    upper_shadow = last['high'] - max(last['close'], last['open'])
    
    return lower_shadow > body * 2 and upper_shadow < body * 0.3

def detect_shooting_star(data: pd.DataFrame) -> bool:
    """كشف نموذج النجم المتساقط"""
    if len(data) < 2:
        return False
    
    last = data.iloc[-1]
    body = abs(last['close'] - last['open'])
    upper_shadow = last['high'] - max(last['close'], last['open'])
    lower_shadow = min(last['close'], last['open']) - last['low']
    
    return upper_shadow > body * 2 and lower_shadow < body * 0.3

def detect_bullish_engulfing(data: pd.DataFrame) -> bool:
    """كشف نموذج الابتلاع الصاعد"""
    if len(data) < 2:
        return False
    
    prev = data.iloc[-2]
    curr = data.iloc[-1]
    
    return (curr['close'] > curr['open'] and 
            prev['close'] < prev['open'] and
            curr['close'] > prev['open'] and
            curr['open'] < prev['close'])

def detect_bearish_engulfing(data: pd.DataFrame) -> bool:
    """كشف نموذج الابتلاع الهابط"""
    if len(data) < 2:
        return False
    
    prev = data.iloc[-2]
    curr = data.iloc[-1]
    
    return (curr['close'] < curr['open'] and 
            prev['close'] > prev['open'] and
            curr['close'] < prev['open'] and
            curr['open'] > prev['close'])

def detect_doji(data: pd.DataFrame) -> bool:
    """كشف نموذج الدوجي"""
    if len(data) < 1:
        return False
    
    last = data.iloc[-1]
    body = abs(last['close'] - last['open'])
    total_range = last['high'] - last['low']
    
    return total_range > 0 and body / total_range < 0.1

def detect_breakout(data: pd.DataFrame) -> Optional[float]:
    """كشف اختراق المقاومة"""
    if len(data) < 20:
        return None
    
    # حساب مقاومة مؤقتة
    resistance = data['high'].iloc[-20:-5].max()
    current_price = data['close'].iloc[-1]
    
    if current_price > resistance * 1.02:
        return current_price + (current_price - resistance) * 0.5
    
    return None

def detect_triangle(data: pd.DataFrame) -> Optional[Dict]:
    """كشف نموذج المثلث"""
    if len(data) < 30:
        return None
    
    # تنفيذ مبسط - يمكن تحسينه
    return None
