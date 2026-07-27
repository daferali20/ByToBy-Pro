# pattern_detector.py
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

@dataclass
class PatternResult:
    """نتيجة اكتشاف النمط"""
    name: str
    detected: bool
    strength: float  # 0-1
    direction: str  # 'bullish', 'bearish', 'neutral'
    confidence: float  # 0-1
    details: Optional[Dict] = None

class PatternDetector:
    """كاشف الأنماط الفنية"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.model = None
        self.scaler = StandardScaler()
    
    def _initialize_patterns(self) -> Dict:
        """تهيئة قائمة الأنماط المدعومة"""
        return {
            'Head and Shoulders': {'type': 'reversal', 'direction': 'bearish'},
            'Inverse Head and Shoulders': {'type': 'reversal', 'direction': 'bullish'},
            'Double Top': {'type': 'reversal', 'direction': 'bearish'},
            'Double Bottom': {'type': 'reversal', 'direction': 'bullish'},
            'Cup and Handle': {'type': 'continuation', 'direction': 'bullish'},
            'Morning Star': {'type': 'reversal', 'direction': 'bullish'},
            'Evening Star': {'type': 'reversal', 'direction': 'bearish'},
            'Three White Soldiers': {'type': 'continuation', 'direction': 'bullish'},
            'Three Black Crows': {'type': 'continuation', 'direction': 'bearish'},
            'Bullish Engulfing': {'type': 'reversal', 'direction': 'bullish'},
            'Bearish Engulfing': {'type': 'reversal', 'direction': 'bearish'},
            'Ascending Triangle': {'type': 'continuation', 'direction': 'bullish'},
            'Descending Triangle': {'type': 'continuation', 'direction': 'bearish'},
            'Bullish Flag': {'type': 'continuation', 'direction': 'bullish'},
            'Bearish Flag': {'type': 'continuation', 'direction': 'bearish'},
            'Hammer': {'type': 'reversal', 'direction': 'bullish'},
            'Shooting Star': {'type': 'reversal', 'direction': 'bearish'},
            'Doji': {'type': 'neutral', 'direction': 'neutral'}
        }
    
    def detect_patterns(self, data: pd.DataFrame) -> List[PatternResult]:
        """
        اكتشاف الأنماط في البيانات
        
        Args:
            data: DataFrame يحتوي على بيانات OHLCV
            
        Returns:
            List[PatternResult]: قائمة بالأنماط المكتشفة
        """
        results = []
        
        for pattern_name, pattern_info in self.patterns.items():
            # محاكاة اكتشاف النمط (للتوضيح)
            detected, strength, confidence = self._simulate_pattern_detection(data, pattern_name)
            
            result = PatternResult(
                name=pattern_name,
                detected=detected,
                strength=strength,
                direction=pattern_info['direction'],
                confidence=confidence
            )
            results.append(result)
        
        return results
    
    def _simulate_pattern_detection(self, data: pd.DataFrame, pattern_name: str) -> Tuple[bool, float, float]:
        """
        محاكاة اكتشاف النمط (يجب استبدالها بخوارزميات حقيقية)
        """
        # هذه محاكاة بسيطة - في التطبيق الحقيقي استخدم خوارزميات متقدمة
        np.random.seed(hash(pattern_name) % 2**32)
        
        # محاكاة احتمالية الاكتشاف
        detection_prob = np.random.random()
        detected = detection_prob > 0.6
        
        if detected:
            strength = np.random.uniform(0.4, 0.95)
            confidence = np.random.uniform(0.5, 0.95)
        else:
            strength = np.random.uniform(0, 0.3)
            confidence = np.random.uniform(0, 0.4)
        
        return detected, strength, confidence
    
    def train(self, X, y):
        """تدريب النموذج"""
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
    
    def predict(self, X):
        """التنبؤ"""
        if self.model is None:
            raise ValueError("النموذج لم يتم تدريبه بعد")
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """التنبؤ مع الاحتمالات"""
        if self.model is None:
            raise ValueError("النموذج لم يتم تدريبه بعد")
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
