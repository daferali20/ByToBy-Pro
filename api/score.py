import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from .features import TechnicalFeatures
from .pattern_detector import PatternDetector
from .pattern_score import PatternScorer

class ScoreCalculator:
    """حساب النتيجة النهائية للتداول"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.technical_features = None
        self.patterns = None
        self.scores = {}
        
    def calculate_all_scores(self) -> Dict[str, float]:
        """حساب جميع أنواع النتائج"""
        tech_features = TechnicalFeatures(self.data)
        self.technical_features = tech_features.extract_all_features()
        
        pattern_detector = PatternDetector(self.data)
        self.patterns = pattern_detector.detect_all_patterns()
        
        self.scores = {
            'technical_score': self._calculate_technical_score(),
            'pattern_score': self._calculate_pattern_score(),
            'volume_score': self._calculate_volume_score(),
            'momentum_score': self._calculate_momentum_score(),
            'volatility_score': self._calculate_volatility_score(),
            'overall_score': 0.0
        }
        
        self.scores['overall_score'] = self._calculate_overall_score()
        
        return self.scores
    
    def _calculate_technical_score(self) -> float:
        """حساب النتيجة الفنية"""
        if self.technical_features is None:
            return 50.0
            
        score = 50.0
        latest = self.technical_features.iloc[-1]
        
        if 'rsi' in latest and not pd.isna(latest['rsi']):
            if latest['rsi'] < 30:
                score += 10
            elif latest['rsi'] > 70:
                score -= 10
        
        if 'macd' in latest and 'macd_signal' in latest and not pd.isna(latest['macd']):
            if latest['macd'] > latest['macd_signal']:
                score += 5
            else:
                score -= 5
        
        if 'bb_position' in latest and not pd.isna(latest['bb_position']):
            if latest['bb_position'] < 0.2:
                score += 8
            elif latest['bb_position'] > 0.8:
                score -= 8
        
        if 'adx' in latest and not pd.isna(latest['adx']):
            if latest['adx'] > 25:
                score += 5
            else:
                score -= 5
        
        if 'sma_200' in latest and not pd.isna(latest['sma_200']):
            current_price = self.data['close'].iloc[-1]
            if current_price > latest['sma_200']:
                score += 5
            else:
                score -= 5
        
        return np.clip(score, 0, 100)
    
    def _calculate_pattern_score(self) -> float:
        """حساب نتيجة النماذج"""
        if not self.patterns:
            return 50.0
            
        pattern_scorer = PatternScorer(self.patterns)
        return pattern_scorer.calculate_pattern_score()
    
    def _calculate_volume_score(self) -> float:
        """حساب نتيجة الحجم"""
        score = 50.0
        
        if len(self.data) > 20:
            volume = self.data['volume']
            latest_volume = volume.iloc[-1]
            avg_volume = volume.iloc[-20:-1].mean()
            
            if latest_volume > avg_volume * 1.5:
                score += 15
            elif latest_volume > avg_volume * 1.2:
                score += 8
            elif latest_volume < avg_volume * 0.5:
                score -= 10
            
            volume_trend = volume.iloc[-5:].mean() / volume.iloc[-20:-5].mean()
            if volume_trend > 1.2:
                score += 10
            elif volume_trend < 0.8:
                score -= 10
        
        return np.clip(score, 0, 100)
    
    def _calculate_momentum_score(self) -> float:
        """حساب نتيجة الزخم"""
        score = 50.0
        
        if len(self.data) > 20:
            close = self.data['close']
            
            short_momentum = (close.iloc[-1] / close.iloc[-5] - 1) * 100
            if short_momentum > 2:
                score += 10
            elif short_momentum < -2:
                score -= 10
            
            medium_momentum = (close.iloc[-1] / close.iloc[-20] - 1) * 100
            if medium_momentum > 5:
                score += 8
            elif medium_momentum < -5:
                score -= 8
            
            roc = (close.iloc[-1] / close.iloc[-10] - 1) * 100
            if roc > 3:
                score += 5
            elif roc < -3:
                score -= 5
        
        return np.clip(score, 0, 100)
    
    def _calculate_volatility_score(self) -> float:
        """حساب نتيجة التقلب"""
        score = 50.0
        
        if len(self.data) > 20:
            returns = self.data['close'].pct_change()
            volatility = returns.std() * np.sqrt(252)
            
            if volatility < 0.15:
                score += 5
            elif volatility > 0.30:
                score -= 5
            
            high = self.data['high']
            low = self.data['low']
            close = self.data['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            
            avg_price = close.iloc[-20:].mean()
            atr_percent = (atr / avg_price) * 100
            
            if atr_percent < 1:
                score += 8
            elif atr_percent > 5:
                score -= 8
        
        return np.clip(score, 0, 100)
    
    def _calculate_overall_score(self) -> float:
        """حساب النتيجة الإجمالية المرجحة"""
        weights = {
            'technical_score': 0.25,
            'pattern_score': 0.25,
            'volume_score': 0.20,
            'momentum_score': 0.15,
            'volatility_score': 0.15
        }
        
        overall_score = sum(self.scores.get(key, 50.0) * weight 
                          for key, weight in weights.items())
        
        return np.clip(overall_score, 0, 100)
    
    def get_detailed_analysis(self) -> Dict:
        """الحصول على تحليل مفصل للنتائج"""
        return {
            'scores': self.scores,
            'technical_indicators': self.technical_features.iloc[-1].to_dict() if self.technical_features is not None else {},
            'patterns': [{'name': p.name, 'direction': p.direction, 'strength': p.strength} 
                        for p in self.patterns if p.detected] if self.patterns else [],
            'recommendation': self._get_recommendation(),
            'confidence': self._calculate_confidence()
        }
    
    def _get_recommendation(self) -> str:
        """الحصول على توصية بناءً على النتيجة"""
        overall = self.scores.get('overall_score', 50)
        
        if overall >= 70:
            return 'Strong Buy'
        elif overall >= 60:
            return 'Buy'
        elif overall >= 55:
            return 'Slight Buy'
        elif overall >= 45:
            return 'Neutral'
        elif overall >= 40:
            return 'Slight Sell'
        elif overall >= 30:
            return 'Sell'
        else:
            return 'Strong Sell'
    
    def _calculate_confidence(self) -> float:
        """حساب مستوى الثقة في النتيجة"""
        scores = [v for k, v in self.scores.items() if k != 'overall_score']
        if not scores:
            return 0.0
            
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        max_std = 20
        confidence = 1 - min(std_score / max_std, 0.5)
        
        return float(confidence)
