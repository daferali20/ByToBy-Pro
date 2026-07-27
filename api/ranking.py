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
    
    def _calculate_trend_metric
