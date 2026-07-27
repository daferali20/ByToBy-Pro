import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from score import ScoreCalculator

class RecommendationSystem:
    """نظام توليد التوصيات الفنية"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.score_calculator = ScoreCalculator(data)
        self.scores = {}
        self.recommendations = []
        
    def generate_recommendations(self) -> Dict:
        """توليد التوصيات الشاملة"""
        # حساب النتائج
        self.scores = self.score_calculator.calculate_all_scores()
        
        # توليد التوصيات
        self.recommendations = {
            'primary_recommendation': self._generate_primary_recommendation(),
            'technical_recommendations': self._generate_technical_recommendations(),
            'pattern_recommendations': self._generate_pattern_recommendations(),
            'risk_assessment': self._assess_risk(),
            'entry_points': self._identify_entry_points(),
            'exit_points': self._identify_exit_points(),
            'stop_loss': self._calculate_stop_loss(),
            'take_profit': self._calculate_take_profit(),
            'risk_reward_ratio': 0.0
        }
        
        # حساب نسبة المخاطرة/المكافأة
        self.recommendations['risk_reward_ratio'] = self._calculate_risk_reward_ratio()
        
        return self.recommendations
    
    def _generate_primary_recommendation(self) -> Dict:
        """توليد التوصية الرئيسية"""
        overall_score = self.scores.get('overall_score', 50)
        confidence = self.score_calculator.get_detailed_analysis().get('confidence', 0.5)
        
        if overall_score >= 70:
            action = 'STRONG_BUY'
            signal_strength = 'Strong'
        elif overall_score >= 60:
            action = 'BUY'
            signal_strength = 'Moderate'
        elif overall_score >= 55:
            action = 'SLIGHT_BUY'
            signal_strength = 'Weak'
        elif overall_score >= 45:
            action = 'NEUTRAL'
            signal_strength = 'Neutral'
        elif overall_score >= 40:
            action = 'SLIGHT_SELL'
            signal_strength = 'Weak'
        elif overall_score >= 30:
            action = 'SELL'
            signal_strength = 'Moderate'
        else:
            action = 'STRONG_SELL'
            signal_strength = 'Strong'
        
        return {
            'action': action,
            'score': overall_score,
            'confidence': confidence,
            'signal_strength': signal_strength,
            'summary': f"{action} signal with {confidence*100:.0f}% confidence"
        }
    
    def _generate_technical_recommendations(self) -> List[Dict]:
        """توليد توصيات المؤشرات الفنية"""
        recommendations = []
        
        if self.score_calculator.technical_features is not None:
            latest = self.score_calculator.technical_features.iloc[-1]
            current_price = self.data['close'].iloc[-1]
            
            # RSI
            if 'rsi' in latest and not pd.isna(latest['rsi']):
                rsi = latest['rsi']
                if rsi < 30:
                    recommendations.append({
                        'indicator': 'RSI',
                        'signal': 'Oversold',
                        'action': 'BUY',
                        'value': rsi
                    })
                elif rsi > 70:
                    recommendations.append({
                        'indicator': 'RSI',
                        'signal': 'Overbought',
                        'action': 'SELL',
                        'value': rsi
                    })
            
            # MACD
            if 'macd' in latest and 'macd_signal' in latest:
                if not pd.isna(latest['macd']) and not pd.isna(latest['macd_signal']):
                    if latest['macd'] > latest['macd_signal']:
                        recommendations.append({
                            'indicator': 'MACD',
                            'signal': 'Bullish Crossover',
                            'action': 'BUY',
                            'value': latest['macd']
                        })
                    else:
                        recommendations.append({
                            'indicator': 'MACD',
                            'signal': 'Bearish Crossover',
                            'action': 'SELL',
                            'value': latest['macd']
                        })
            
            # Bollinger Bands
            if 'bb_position' in latest and not pd.isna(latest['bb_position']):
                if latest['bb_position'] < 0.2:
                    recommendations.append({
                        'indicator': 'Bollinger Bands',
                        'signal': 'Near Lower Band',
                        'action': 'BUY',
                        'value': latest['bb_position']
                    })
                elif latest['bb_position'] > 0.8:
                    recommendations.append({
                        'indicator': 'Bollinger Bands',
                        'signal': 'Near Upper Band',
                        'action': 'SELL',
                        'value': latest['bb_position']
                    })
            
            # Moving Averages
            for ma in ['sma_20', 'sma_50', 'sma_200']:
                if ma in latest and not pd.isna(latest[ma]):
                    if current_price > latest[ma]:
                        recommendations.append({
                            'indicator': ma.upper(),
                            'signal': 'Price Above MA',
                            'action': 'BULLISH',
                            'value': latest[ma]
                        })
                    else:
                        recommendations.append({
                            'indicator': ma.upper(),
                            'signal': 'Price Below MA',
                            'action': 'BEARISH',
                            'value': latest[ma]
                        })
        
        return recommendations
    
    def _generate_pattern_recommendations(self) -> List[Dict]:
        """توليد توصيات النماذج"""
        pattern_recommendations = []
        detailed_analysis = self.score_calculator.get_detailed_analysis()
        
        for pattern in detailed_analysis.get('patterns', []):
            if pattern['direction'] == 'bullish':
                action = 'BUY'
            elif pattern['direction'] == 'bearish':
                action = 'SELL'
            else:
                action = 'NEUTRAL'
            
            pattern_recommendations.append({
                'pattern': pattern['name'],
                'direction': pattern['direction'],
                'strength': pattern['strength'],
                'action': action,
                'confidence': pattern['strength'] * 0.7 + 0.3
            })
        
        return sorted(pattern_recommendations, key=lambda x: x['confidence'], reverse=True)
    
    def _assess_risk(self) -> Dict:
        """تقييم المخاطر"""
        risk_factors = []
        overall_risk = 'Medium'
        
        # تقييم التقلب
        if 'volatility_score' in self.scores:
            if self.scores['volatility_score'] > 60:
                risk_factors.append('High volatility')
                overall_risk = 'High'
            elif self.scores['volatility_score'] < 40:
                risk_factors.append('Low volatility')
        
        # تقييم السيولة (حجم التداول)
        if 'volume_score' in self.scores:
            if self.scores['volume_score'] < 40:
                risk_factors.append('Low volume')
                if overall_risk != 'High':
                    overall_risk = 'Medium-High'
        
        # تقييم اتجاه السوق
        if 'technical_score' in self.scores:
            if self.scores['technical_score'] < 30 or self.scores['technical_score'] > 70:
                risk_factors.append('Strong trend')
        
        return {
            'overall_risk': overall_risk,
            'risk_factors': risk_factors,
            'risk_level': {'Low': 1, 'Medium': 2, 'Medium-High': 3, 'High': 4}.get(overall_risk, 2)
        }
    
    def _identify_entry_points(self) -> List[Dict]:
        """تحديد نقاط الدخول المحتملة"""
        entry_points = []
        current_price = self.data['close'].iloc[-1]
        
        # نقاط الدخول المحتملة بناءً على المؤشرات الفنية
        if self.score_calculator.technical_features is not None:
            latest = self.score_calculator.technical_features.iloc[-1]
            
            # BB Lower Band كحافز للشراء
            if 'bb_lower' in latest and not pd.isna(latest['bb_lower']):
                if current_price > latest['bb_lower']:
                    entry_points.append({
                        'type': 'Support Entry',
                        'price': latest['bb_lower'],
                        'reason': 'Bollinger Band Support',
                        'strength': 'Strong' if current_price / latest['bb_lower'] < 1.02 else 'Moderate'
                    })
            
            # SMA 200 كدعم
            if 'sma_200' in latest and not pd.isna(latest['sma_200']):
                if current_price > latest['sma_200']:
                    entry_points.append({
                        'type': 'Trend Entry',
                        'price': latest['sma_200'],
                        'reason': '200-Day SMA Support',
                        'strength': 'Strong' if current_price / latest['sma_200'] < 1.03 else 'Moderate'
                    })
        
        return entry_points
    
    def _identify_exit_points(self) -> List[Dict]:
        """تحديد نقاط الخروج المحتملة"""
        exit_points = []
        current_price = self.data['close'].iloc[-1]
        
        if self.score_calculator.technical_features is not None:
            latest = self.score_calculator.technical_features.iloc[-1]
            
            # BB Upper Band كمقاومة
            if 'bb_upper' in latest and not pd.isna(latest['bb_upper']):
                if current_price < latest['bb_upper']:
                    exit_points.append({
                        'type': 'Resistance Exit',
                        'price': latest['bb_upper'],
                        'reason': 'Bollinger Band Resistance',
                        'strength': 'Strong' if latest['bb_upper'] / current_price < 1.02 else 'Moderate'
                    })
            
            # SMA 200 كمقاومة (في حالة الاتجاه الهابط)
            if 'sma_200' in latest and not pd.isna(latest['sma_200']):
                if current_price < latest['sma_200']:
                    exit_points.append({
                        'type': 'Trend Exit',
                        'price': latest['sma_200'],
                        'reason': '200-Day SMA Resistance',
                        'strength': 'Strong' if latest['sma_200'] / current_price < 1.03 else 'Moderate'
                    })
        
        return exit_points
    
    def _calculate_stop_loss(self) -> Dict:
        """حساب وقف الخسارة"""
        current_price = self.data['close'].iloc[-1]
        
        # الحصول على ATR لتحديد وقف الخسارة الديناميكي
        if self.score_calculator.technical_features is not None:
            latest = self.score_calculator.technical_features.iloc[-1]
            if 'atr' in latest and not pd.isna(latest['atr']):
                atr = latest['atr']
                stop_loss = current_price - (atr * 2)  # 2 ATR للوقف
                return {
                    'price': stop_loss,
                    'percentage': ((current_price - stop_loss) / current_price) * 100,
                    'method': 'ATR-Based'
                }
        
        # إذا لم يتوفر ATR، استخدام نسبة مئوية ثابتة
        stop_loss = current_price * 0.95  # وقف خسارة 5%
        return {
            'price': stop_loss,
            'percentage': 5.0,
            'method': 'Percentage-Based'
        }
    
    def _calculate_take_profit(self) -> Dict:
        """حساب جني الأرباح"""
        current_price = self.data['close'].iloc[-1]
        
        # استخدام Bollinger Bands العلوية كهدف
        if self.score_calculator.technical_features is not None:
            latest = self.score_calculator.technical_features.iloc[-1]
            if 'bb_upper' in latest and not pd.isna(latest['bb_upper']):
                take_profit = latest['bb_upper']
                return {
                    'price': take_profit,
                    'percentage': ((take_profit - current_price) / current_price) * 100,
                    'method': 'Bollinger Band Upper'
                }
        
        # إذا لم يتوفر، استخدام نسبة مئوية ثابتة
        take_profit = current_price * 1.10  # جني أرباح 10%
        return {
            'price': take_profit,
            'percentage': 10.0,
            'method': 'Percentage-Based'
        }
    
    def _calculate_risk_reward_ratio(self) -> float:
        """حساب نسبة المخاطرة/المكافأة"""
        stop_loss = self._calculate_stop_loss()['price']
        take_profit = self._calculate_take_profit()['price']
        current_price = self.data['close'].iloc[-1]
        
        risk = current_price - stop_loss
        reward = take_profit - current_price
        
        if risk > 0:
            return reward / risk
        else:
            return 0.0
