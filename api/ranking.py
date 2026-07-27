import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from recommendation import RecommendationSystem

class RankingSystem:
    """نظام ترتيب وتصنيف الصفقات"""
    
    def __init__(self, data: pd.DataFrame, score: float = None):
        self.data = data
        self.score = score
        self.recommendation_system = RecommendationSystem(data)
        self.recommendations = self.recommendation_system.generate_recommendations()
        self.rank_metrics = {}
        
    def rank_trade(self) -> Dict:
        """ترتيب الصفقة بناءً على معايير متعددة"""
        # حساب معايير الترتيب
        self.rank_metrics = {
            'signal_quality': self._calculate_signal_quality(),
            'risk_reward': self._calculate_risk_reward_metric(),
            'momentum': self._calculate_momentum_metric(),
            'volume': self._calculate_volume_metric(),
            'trend': self._calculate_trend_metric(),
            'volatility': self._calculate_volatility_metric(),
            'pattern_quality': self._calculate_pattern_quality()
        }
        
        # حساب النتيجة الإجمالية للترتيب
        overall_rank_score = self._calculate_overall_rank_score()
        
        return {
            'overall_rank': overall_rank_score,
            'rank_grade': self._get_rank_grade(overall_rank_score),
            'metrics': self.rank_metrics,
            'recommendation': self.recommendations['primary_recommendation']['action'],
            'confidence': self.recommendations['primary_recommendation']['confidence']
        }
    
    def _calculate_signal_quality(self) -> float:
        """حساب جودة الإشارة"""
        primary_rec = self.recommendations['primary_recommendation']
        score = 0.0
        
        # جودة الإشارة بناءً على النتيجة والثقة
        if primary_rec['score'] >= 70:
            score += 30
        elif primary_rec['score'] >= 60:
            score += 20
        elif primary_rec['score'] >= 50:
            score += 10
        
        # الثقة في الإشارة
        confidence = primary_rec['confidence']
        score += confidence * 70  # أقصى 70 نقطة للثقة
        
        return min(score, 100)
    
    def _calculate_risk_reward_metric(self) -> float:
        """حساب مقياس المخاطرة/المكافأة"""
        risk_reward = self.recommendations.get('risk_reward_ratio', 0)
        
        if risk_reward >= 3:
            return 100
        elif risk_reward >= 2:
            return 80
        elif risk_reward >= 1.5:
            return 60
        elif risk_reward >= 1:
            return 40
        else:
            return max(0, risk_reward * 40)
    
    def _calculate_momentum_metric(self) -> float:
        """حساب مقياس الزخم"""
        if len(self.data) < 50:
            return 50.0
        
        returns = self.data['close'].pct_change()
        momentum_10d = (self.data['close'].iloc[-1] / self.data['close'].iloc[-10] - 1) * 100
        momentum_30d = (self.data['close'].iloc[-1] / self.data['close'].iloc[-30] - 1) * 100
        
        # تسجيل الزخم على مقياس 0-100
        score = 50 + (momentum_10d * 2) + (momentum_30d * 1)
        
        # تطبيع النتيجة
        normalized_score = max(0, min(100, score))
        
        return normalized_score
    
    def _calculate_volume_metric(self) -> float:
        """حساب مقياس الحجم"""
        if len(self.data) < 20:
            return 50.0
        
        volume = self.data['volume']
        latest_volume = volume.iloc[-1]
        avg_volume = volume.iloc[-20:-1].mean()
        
        if avg_volume > 0:
            volume_ratio = latest_volume / avg_volume
            if volume_ratio >= 2:
                return 100
            elif volume_ratio >= 1.5:
                return 80
            elif volume_ratio >= 1:
                return 60
            elif volume_ratio >= 0.5:
                return 40
            else:
                return 20
        else:
            return 50.0
    
    def _calculate_trend_metric(self) -> float:
        """حساب مقياس الاتجاه"""
        if len(self.data) < 50:
            return 50.0
        
        close = self.data['close']
        
        # حساب ميل الاتجاه
        x = np.arange(len(close))
        slope = np.polyfit(x[-50:], close.iloc[-50:], 1)[0]
        
        # حساب R² لقوة الاتجاه
        slope_normalized = slope / close.iloc[-50:].mean()
        
        # تحويل الميل إلى درجة 0-100
        if slope_normalized > 0.01:
            trend_score = 70 + min(slope_normalized * 1000, 30)
        elif slope_normalized < -0.01:
            trend_score = 30 + max(slope_normalized * 1000, -30)
        else:
            trend_score = 50
        
        return max(0, min(100, trend_score))
    
    def _calculate_volatility_metric(self) -> float:
        """حساب مقياس التقلب"""
        if len(self.data) < 20:
            return 50.0
        
        returns = self.data['close'].pct_change()
        volatility = returns.std() * np.sqrt(252)
        
        # تسجيل التقلب (التقلب المنخفض أفضل للصفقات طويلة المدى)
        if volatility < 0.15:
            return 70
        elif volatility < 0.25:
            return 50
        elif volatility < 0.35:
            return 30
        else:
            return 10
    
    def _calculate_pattern_quality(self) -> float:
        """حساب جودة النماذج الفنية"""
        pattern_recommendations = self.recommendations.get('pattern_recommendations', [])
        
        if not pattern_recommendations:
            return 50.0
        
        # حساب متوسط جودة النماذج
        total_quality = 0
        for pattern in pattern_recommendations[:5]:  # أعلى 5 نماذج
            total_quality += pattern['confidence'] * 100
        
        average_quality = total_quality / len(pattern_recommendations[:5])
        
        return average_quality
    
    def _calculate_overall_rank_score(self) -> float:
        """حساب نتيجة الترتيب الإجمالية"""
        weights = {
            'signal_quality': 0.25,
            'risk_reward': 0.20,
            'momentum': 0.15,
            'volume': 0.15,
            'trend': 0.15,
            'volatility': 0.05,
            'pattern_quality': 0.05
        }
        
        total_score = sum(self.rank_metrics[key] * weight 
                         for key, weight in weights.items())
        
        return min(100, total_score)
    
    def _get_rank_grade(self, score: float) -> str:
        """الحصول على درجة الترتيب"""
        if score >= 85:
            return 'A+'
        elif score >= 75:
            return 'A'
        elif score >= 65:
            return 'B+'
        elif score >= 55:
            return 'B'
        elif score >= 45:
            return 'C'
        elif score >= 35:
            return 'D'
        else:
            return 'F'
    
    def get_ranking_summary(self) -> Dict:
        """الحصول على ملخص الترتيب"""
        ranking = self.rank_trade()
        summary = {
            'rank_score': ranking['overall_rank'],
            'rank_grade': ranking['rank_grade'],
            'recommendation': ranking['recommendation'],
            'confidence': ranking['confidence'],
            'signal_quality': ranking['metrics']['signal_quality'],
            'best_metric': max(ranking['metrics'].items(), key=lambda x: x[1])[0],
            'worst_metric': min(ranking['metrics'].items(), key=lambda x: x[1])[0]
        }
        
        # إضافة نصائح للتحسين
        improvement_areas = []
        for metric, score in ranking['metrics'].items():
            if score < 50:
                improvement_areas.append(metric)
        
        if improvement_areas:
            summary['improvement_areas'] = improvement_areas
        
        return summary
