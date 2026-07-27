import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pattern_detector import PatternDetector, PatternResult

class PatternScorer:
    """تقييم وتسجيل النماذج الفنية"""
    
    def __init__(self, patterns: List[PatternResult]):
        self.patterns = patterns
        self.weights = self._initialize_weights()
        
    def _initialize_weights(self) -> Dict[str, float]:
        """تهيئة أوزان النماذج بناءً على أهميتها"""
        return {
            'Head and Shoulders': 0.9,
            'Inverse Head and Shoulders': 0.9,
            'Double Top': 0.85,
            'Double Bottom': 0.85,
            'Cup and Handle': 0.85,
            'Morning Star': 0.8,
            'Evening Star': 0.8,
            'Three White Soldiers': 0.8,
            'Three Black Crows': 0.8,
            'Bullish Engulfing': 0.75,
            'Bearish Engulfing': 0.75,
            'Ascending Triangle': 0.75,
            'Descending Triangle': 0.75,
            'Bullish Flag': 0.7,
            'Bearish Flag': 0.7,
            'Hammer': 0.6,
            'Shooting Star': 0.6,
            'Doji': 0.5,
            'default': 0.5
        }
    
    def calculate_pattern_score(self) -> float:
        """حساب النتيجة الإجمالية للنماذج"""
        if not self.patterns:
            return 50.0  # نتيجة محايدة
        
        total_score = 0
        weighted_sum = 0
        
        for pattern in self.patterns:
            if pattern.detected:
                weight = self.weights.get(pattern.name, self.weights['default'])
                direction_multiplier = 1 if pattern.direction == 'bullish' else -1 if pattern.direction == 'bearish' else 0
                
                # حساب النتيجة
                pattern_score = pattern.strength * weight * 100
                weighted_sum += pattern_score * direction_multiplier
                total_score += weight
        
        if total_score > 0:
            final_score = weighted_sum / total_score
        else:
            final_score = 0
            
        # تحويل النتيجة إلى مقياس 0-100
        normalized_score = 50 + (final_score * 0.5)
        return np.clip(normalized_score, 0, 100)
    
    def get_pattern_contribution(self) -> Dict[str, float]:
        """الحصول على مساهمة كل نمط في النتيجة النهائية"""
        contributions = {}
        
        for pattern in self.patterns:
            if pattern.detected:
                weight = self.weights.get(pattern.name, self.weights['default'])
                contribution = pattern.strength * weight * 100
                contributions[pattern.name] = contribution
        
        return contributions
    
    def get_best_patterns(self, top_n: int = 3) -> List[Dict]:
        """الحصول على أفضل النماذج"""
        sorted_patterns = sorted(
            [p for p in self.patterns if p.detected],
            key=lambda x: x.strength * self.weights.get(x.name, self.weights['default']),
            reverse=True
        )
        
        return [{
            'name': p.name,
            'strength': p.strength,
            'direction': p.direction,
            'score': p.strength * self.weights.get(p.name, self.weights['default']) * 100
        } for p in sorted_patterns[:top_n]]
