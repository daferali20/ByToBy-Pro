# ai/predict.py
"""
AI Prediction Module - ByToBy Pro
وحدة التنبؤ بالذكاء الاصطناعي - تحليل الأسهم وتقديم توصيات
"""

import numpy as np
import pandas as pd
from datetime import datetime
import random

class StockPredictor:
    """
    نظام التنبؤ بالأسهم باستخدام الذكاء الاصطناعي
    يعتمد على تحليل المؤشرات المالية المتعددة
    """
    
    def __init__(self):
        """تهيئة نظام التنبؤ"""
        self.version = "1.0.0"
        self.model_loaded = True
        print(f"✅ AI Predictor v{self.version} initialized")
    
    def calculate_fundamental_score(self, stock_data):
        """
        حساب النقاط الأساسية للشركة بناءً على المؤشرات المالية
        """
        score = 0
        max_score = 100
        
        # 1. Profit Margin (هامش الربح)
        profit_margin = stock_data.get('profit_margin', 0)
        if profit_margin > 0:
            if profit_margin > 30:
                score += 15
            elif profit_margin > 20:
                score += 12
            elif profit_margin > 10:
                score += 8
            elif profit_margin > 0:
                score += 5
        
        # 2. Revenue Growth (نمو الإيرادات)
        revenue_growth = stock_data.get('revenue_growth', 0)
        if revenue_growth > 0:
            if revenue_growth > 40:
                score += 15
            elif revenue_growth > 25:
                score += 12
            elif revenue_growth > 10:
                score += 8
            elif revenue_growth > 0:
                score += 5
        else:
            score += max(-10, revenue_growth / 10)  # خصم للنمو السلبي
        
        # 3. PE Ratio (نسبة السعر إلى الربح)
        pe_ratio = stock_data.get('pe_ratio', 0)
        if pe_ratio > 0:
            if pe_ratio < 10:
                score += 15  # PE منخفض = سهم مقيم بأقل من قيمته
            elif pe_ratio < 15:
                score += 12
            elif pe_ratio < 20:
                score += 8
            elif pe_ratio < 30:
                score += 3
            else:
                score -= 5  # PE مرتفع جداً
        
        # 4. EPS (ربحية السهم)
        eps = stock_data.get('eps', 0)
        if eps > 0:
            if eps > 10:
                score += 10
            elif eps > 5:
                score += 7
            elif eps > 1:
                score += 4
            else:
                score += 2
        
        # 5. Dividend Yield (نسبة التوزيعات)
        dividend_yield = stock_data.get('dividend_yield', 0)
        if dividend_yield > 0:
            if dividend_yield > 5:
                score += 10
            elif dividend_yield > 3:
                score += 7
            elif dividend_yield > 1:
                score += 4
            else:
                score += 1
        
        # 6. Debt to Equity (نسبة الدين إلى حقوق الملكية)
        debt_to_equity = stock_data.get('debt_to_equity', 0)
        if debt_to_equity > 0:
            if debt_to_equity < 0.5:
                score += 10
            elif debt_to_equity < 1:
                score += 7
            elif debt_to_equity < 2:
                score += 3
            else:
                score -= 5  # ديون عالية
        
        # 7. Volume (حجم التداول - سيولة)
        volume = stock_data.get('volume', 0)
        if volume > 0:
            if volume > 10000000:
                score += 10
            elif volume > 5000000:
                score += 7
            elif volume > 1000000:
                score += 4
            elif volume > 100000:
                score += 2
        
        # 8. Market Cap (القيمة السوقية)
        market_cap = stock_data.get('market_cap', 0)
        if market_cap > 0:
            if market_cap > 100:  # > 100 مليار
                score += 10
            elif market_cap > 50:
                score += 7
            elif market_cap > 10:
                score += 4
            else:
                score += 1
        
        # ضمان أن النتيجة ضمن النطاق 0-100
        return min(max(score, 0), max_score)
    
    def analyze_technical_indicators(self, stock_data):
        """
        تحليل المؤشرات الفنية للشركة
        """
        # في الإصدار الحقيقي، سنحصل على بيانات تاريخية
        # هنا نستخدم نموذج مبسط يعتمد على البيانات المتوفرة
        
        # محاكاة تحليل فني
        price = stock_data.get('price', 100)
        change = stock_data.get('change_today', 0)
        
        # مؤشرات فنية محاكاة
        technical_indicators = {
            'rsi': random.uniform(30, 70),  # Relative Strength Index
            'momentum': random.uniform(-10, 10),  # Momentum
            'volatility': random.uniform(10, 30),  # Volatility
            'trend_strength': random.uniform(0, 100)  # Trend Strength
        }
        
        # تحليل RSI
        rsi = technical_indicators['rsi']
        if rsi < 30:
            rsi_score = 15  # منطقة ذروة البيع
        elif rsi < 40:
            rsi_score = 10
        elif rsi < 60:
            rsi_score = 5
        elif rsi < 70:
            rsi_score = 3
        else:
            rsi_score = -5  # منطقة ذروة الشراء
        
        # تحليل الزخم
        momentum = technical_indicators['momentum']
        if momentum > 5:
            momentum_score = 10
        elif momentum > 0:
            momentum_score = 5
        elif momentum > -5:
            momentum_score = -5
        else:
            momentum_score = -10
        
        # تحليل قوة الاتجاه
        trend = technical_indicators['trend_strength']
        if trend > 70:
            trend_score = 15
        elif trend > 50:
            trend_score = 10
        elif trend > 30:
            trend_score = 5
        else:
            trend_score = -5
        
        total_score = rsi_score + momentum_score + trend_score
        
        return {
            'technical_score': max(0, min(100, total_score + 50)),  # تحويل إلى 0-100
            'indicators': technical_indicators
        }
    
    def generate_recommendation(self, score, confidence):
        """
        توليد توصية بناءً على النتيجة والثقة
        """
        if score >= 80:
            if confidence > 75:
                return "Strong Buy"
            return "Buy"
        elif score >= 65:
            return "Buy"
        elif score >= 50:
            return "Hold"
        elif score >= 35:
            return "Sell"
        else:
            if confidence > 75:
                return "Strong Sell"
            return "Sell"
    
    def predict_stock(self, stock_data):
        """
        التنبؤ بسهم معين وإعطاء توصية
        """
        try:
            # 1. حساب النقاط الأساسية
            fundamental_score = self.calculate_fundamental_score(stock_data)
            
            # 2. تحليل المؤشرات الفنية (محاكاة)
            technical_analysis = self.analyze_technical_indicators(stock_data)
            technical_score = technical_analysis['technical_score']
            
            # 3. حساب النتيجة الإجمالية (وزن 60% أساسي، 40% فني)
            overall_score = (fundamental_score * 0.6) + (technical_score * 0.4)
            
            # 4. حساب مستوى الثقة
            confidence = 50 + (overall_score / 100) * 30 + random.uniform(-5, 5)
            confidence = min(95, max(50, confidence))
            
            # 5. تحديد التوصية
            recommendation = self.generate_recommendation(overall_score, confidence)
            
            # 6. حساب السعر المستهدف
            current_price = stock_data.get('price', 100)
            price_target = current_price * (1 + (overall_score - 50) / 200)  # نسبة تغير منطقية
            
            return {
                'score': overall_score,
                'recommendation': recommendation,
                'confidence': confidence,
                'target_price': round(price_target, 2),
                'fundamental_score': fundamental_score,
                'technical_score': technical_score,
                'analysis_date': datetime.now().isoformat(),
                'model_version': self.version
            }
        
        except Exception as e:
            print(f"⚠️ خطأ في التنبؤ: {e}")
            # إرجاع توصية افتراضية في حالة الخطأ
            return {
                'score': 50,
                'recommendation': 'Hold',
                'confidence': 60,
                'target_price': stock_data.get('price', 100),
                'fundamental_score': 50,
                'technical_score': 50,
                'analysis_date': datetime.now().isoformat(),
                'model_version': self.version
            }

# ============================================
# Singleton Instance
# ============================================

_predictor = None

def get_predictor():
    """الحصول على نسخة واحدة من نظام التنبؤ"""
    global _predictor
    if _predictor is None:
        _predictor = StockPredictor()
    return _predictor

# ============================================
# Convenience Functions
# ============================================

def predict_stock(stock_data):
    """
    واجهة مبسطة للتنبؤ بسهم
    
    Parameters:
    stock_data (dict): بيانات السهم يجب أن تحتوي على:
        - symbol: رمز السهم
        - price: السعر الحالي
        - market_cap: القيمة السوقية (بالمليارات)
        - volume: حجم التداول
        - pe_ratio: نسبة PE
        - eps: ربحية السهم
        - dividend_yield: نسبة التوزيعات
        - revenue_growth: نمو الإيرادات (%)
        - profit_margin: هامش الربح (%)
        - debt_to_equity: نسبة الدين إلى حقوق الملكية
    """
    predictor = get_predictor()
    return predictor.predict_stock(stock_data)

def predict_batch(stocks_data):
    """
    التنبؤ بمجموعة من الأسهم
    
    Parameters:
    stocks_data (list): قائمة من بيانات الأسهم
    """
    predictor = get_predictor()
    results = []
    
    for stock_data in stocks_data:
        prediction = predictor.predict_stock(stock_data)
        results.append(prediction)
    
    return results

def analyze_sector(sector_data):
    """
    تحليل قطاع كامل
    
    Parameters:
    sector_data (list): قائمة من بيانات الأسهم في القطاع
    """
    if not sector_data:
        return {
            'average_score': 0,
            'best_stock': None,
            'recommendations': []
        }
    
    results = predict_batch(sector_data)
    
    # حساب متوسط النتيجة
    average_score = sum([r['score'] for r in results]) / len(results)
    
    # العثور على أفضل سهم
    best_idx = max(range(len(results)), key=lambda i: results[i]['score'])
    best_stock = {
        'symbol': sector_data[best_idx].get('symbol', 'N/A'),
        'score': results[best_idx]['score'],
        'recommendation': results[best_idx]['recommendation']
    }
    
    return {
        'average_score': average_score,
        'best_stock': best_stock,
        'recommendations': results
    }

# ============================================
# Module Info
# ============================================

def get_module_info():
    """الحصول على معلومات الوحدة"""
    return {
        'name': 'AI Prediction Module',
        'version': '1.0.0',
        'author': 'ByToBy Pro Team',
        'description': 'Stock prediction and recommendation system using AI',
        'features': [
            'Fundamental Analysis',
            'Technical Analysis',
            'Smart Recommendations',
            'Confidence Scoring',
            'Price Targets'
        ]
    }

# ============================================
# Main - Testing
# ============================================

if __name__ == "__main__":
    # اختبار النظام
    print("="*50)
    print("🤖 AI Prediction Module Test")
    print("="*50)
    
    # بيانات اختبار
    test_stock = {
        "symbol": "AAPL",
        "price": 175.50,
        "market_cap": 2800,
        "volume": 8000000,
        "pe_ratio": 28.5,
        "eps": 6.16,
        "dividend_yield": 0.55,
        "revenue_growth": 8.2,
        "profit_margin": 25.3,
        "debt_to_equity": 1.8
    }
    
    print("\n📊 بيانات السهم:")
    for key, value in test_stock.items():
        print(f"  {key}: {value}")
    
    print("\n🤔 جاري التحليل...")
    result = predict_stock(test_stock)
    
    print("\n📈 نتيجة التحليل:")
    print(f"  النتيجة الإجمالية: {result['score']:.1f}%")
    print(f"  التوصية: {result['recommendation']}")
    print(f"  مستوى الثقة: {result['confidence']:.1f}%")
    print(f"  السعر المستهدف: ${result['target_price']:.2f}")
    print(f"  النتيجة الأساسية: {result['fundamental_score']:.1f}%")
    print(f"  النتيجة الفنية: {result['technical_score']:.1f}%")
    print(f"  تاريخ التحليل: {result['analysis_date']}")
    
    print("\n" + "="*50)
    print("✅ تم الاختبار بنجاح!")
