# ai/scoring.py
"""
نظام تسجيل وتقييم الأسهم
"""

import pandas as pd
import numpy as np
from typing import Dict

def calculate_scores(data: pd.DataFrame) -> Dict:
    """
    حساب النتائج المختلفة للسهم
    
    Args:
        data: DataFrame مع بيانات OHLCV
    
    Returns:
        Dictionary مع النتائج
    """
    scores = {
        'technical_score': 50.0,
        'pattern_score': 50.0,
        'volume_score': 50.0,
        'momentum_score': 50.0,
        'overall_score': 50.0
    }
    
    if data.empty:
        return scores
    
    try:
        # حساب النتيجة الفنية
        scores['technical_score'] = calculate_technical_score(data)
        
        # حساب نتيجة النماذج
        scores['pattern_score'] = calculate_pattern_score(data)
        
        # حساب نتيجة الحجم
        scores['volume_score'] = calculate_volume_score(data)
        
        # حساب نتيجة الزخم
        scores['momentum_score'] = calculate_momentum_score(data)
        
        # حساب النتيجة الإجمالية
        scores['overall_score'] = (
            scores['technical_score'] * 0.30 +
            scores['pattern_score'] * 0.25 +
            scores['volume_score'] * 0.20 +
            scores['momentum_score'] * 0.25
        )
        
    except Exception as e:
        scores['error'] = str(e)
    
    return scores

def calculate_technical_score(data: pd.DataFrame) -> float:
    """حساب النتيجة الفنية"""
    score = 50.0
    
    if len(data) < 20:
        return score
    
    close = data['close']
    
    # المتوسطات المتحركة
    sma_20 = close.rolling(20).mean().iloc[-1]
    sma_50 = close.rolling(50).mean().iloc[-1] if len(data) >= 50 else close.mean()
    
    if close.iloc[-1] > sma_20:
        score += 10
    if close.iloc[-1] > sma_50:
        score += 10
    
    # RSI مبسط
    returns = close.pct_change()
    gain = returns[returns > 0].mean()
    loss = abs(returns[returns < 0].mean())
    
    if loss > 0:
        rsi = 100 - (100 / (1 + gain/loss))
        if rsi < 30:
            score += 10
        elif rsi > 70:
            score -= 10
    
    return max(0, min(100, score))

def calculate_pattern_score(data: pd.DataFrame) -> float:
    """حساب نتيجة النماذج"""
    # استخدام دالة detect_patterns إن وجدت
    try:
        from .pattern_detector import detect_patterns
        patterns = detect_patterns(data)
        
        bullish_count = len(patterns.get('bullish', []))
        bearish_count = len(patterns.get('bearish', []))
        
        if bullish_count > bearish_count:
            return 60 + (bullish_count - bearish_count) * 5
        elif bearish_count > bullish_count:
            return 40 - (bearish_count - bullish_count) * 5
        else:
            return 50
    except:
        return 50

def calculate_volume_score(data: pd.DataFrame) -> float:
    """حساب نتيجة الحجم"""
    score = 50.0
    
    if len(data) < 20:
        return score
    
    volume = data['volume']
    avg_volume = volume.iloc[-20:-1].mean()
    current_volume = volume.iloc[-1]
    
    if current_volume > avg_volume * 1.5:
        score += 15
    elif current_volume > avg_volume * 1.2:
        score += 8
    elif current_volume < avg_volume * 0.5:
        score -= 10
    
    return max(0, min(100, score))

def calculate_momentum_score(data: pd.DataFrame) -> float:
    """حساب نتيجة الزخم"""
    score = 50.0
    
    if len(data) < 20:
        return score
    
    close = data['close']
    
    # الزخم قصير المدى
    short_momentum = (close.iloc[-1] / close.iloc[-5] - 1) * 100
    
    if short_momentum > 2:
        score += 10
    elif short_momentum < -2:
        score -= 10
    
    # الزخم متوسط المدى
    medium_momentum = (close.iloc[-1] / close.iloc[-20] - 1) * 100
    
    if medium_momentum > 5:
        score += 8
    elif medium_momentum < -5:
        score -= 8
    
    return max(0, min(100, score))
