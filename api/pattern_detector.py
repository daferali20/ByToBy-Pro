import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class PatternResult:
    """نتيجة اكتشاف النمط"""
    name: str
    detected: bool
    strength: float  # 0-1
    direction: str  # 'bullish', 'bearish', 'neutral'
    price_target: Optional[float] = None
    confidence: float = 0.0

class PatternDetector:
    """اكتشاف النماذج الفنية في بيانات السوق"""
    
    def __init__(self, data: pd.DataFrame):
        """
        تهيئة الكاشف
        
        Args:
            data: DataFrame يحتوي على أعمدة OHLCV
        """
        self.data = data
        self.patterns: List[PatternResult] = []
        
    def detect_all_patterns(self) -> List[PatternResult]:
        """اكتشاف جميع النماذج الفنية"""
        self.patterns = []
        
        # أنماط الانعكاس
        self.detect_double_top_bottom()
        self.detect_head_and_shoulders()
        self.detect_bullish_bearish_engulfing()
        self.detect_hammer_shooting_star()
        self.detect_doji()
        self.detect_morning_evening_star()
        self.detect_three_white_soldiers()
        self.detect_three_black_crows()
        
        # أنماط الاستمرار
        self.detect_flags_pennants()
        self.detect_triangles()
        self.detect_wedges()
        self.detect_rectangles()
        self.detect_cup_and_handle()
        
        # أنماط الشموع اليابانية
        self.detect_candle_patterns()
        
        # أنماط أخرى
        self.detect_gaps()
        self.detect_pivot_points()
        self.detect_support_resistance()
        
        return self.patterns
    
    def detect_double_top_bottom(self) -> None:
        """اكتشاف نموذج القمة/القاع المزدوج"""
        high_points = self._find_local_extrema(self.data['high'], mode='max')
        low_points = self._find_local_extrema(self.data['low'], mode='min')
        
        # Double Top
        if len(high_points) >= 2:
            last_two = high_points[-2:]
            if abs(last_two[0][1] - last_two[1][1]) / last_two[0][1] < 0.05:
                mid_low = self.data['low'][last_two[0][0]:last_two[1][0]].min()
                if mid_low / last_two[0][1] < 0.95:
                    self.patterns.append(PatternResult(
                        name='Double Top',
                        detected=True,
                        strength=0.7,
                        direction='bearish',
                        price_target=last_two[0][1] - (last_two[0][1] - mid_low)
                    ))
        
        # Double Bottom
        if len(low_points) >= 2:
            last_two = low_points[-2:]
            if abs(last_two[0][1] - last_two[1][1]) / last_two[0][1] < 0.05:
                mid_high = self.data['high'][last_two[0][0]:last_two[1][0]].max()
                if mid_high / last_two[0][1] > 1.05:
                    self.patterns.append(PatternResult(
                        name='Double Bottom',
                        detected=True,
                        strength=0.7,
                        direction='bullish',
                        price_target=last_two[0][1] + (mid_high - last_two[0][1])
                    ))
    
    def detect_head_and_shoulders(self) -> None:
        """اكتشاف نموذج الرأس والكتفين"""
        peaks = self._find_local_extrema(self.data['high'], mode='max', order=5)
        
        if len(peaks) >= 3:
            for i in range(len(peaks) - 2):
                left_shoulder, head, right_shoulder = peaks[i], peaks[i+1], peaks[i+2]
                
                # Head and Shoulders (bearish)
                if (head[1] > left_shoulder[1] and head[1] > right_shoulder[1] and
                    abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1] < 0.05 and
                    left_shoulder[0] < head[0] < right_shoulder[0]):
                    
                    neckline = (left_shoulder[1] + right_shoulder[1]) / 2
                    self.patterns.append(PatternResult(
                        name='Head and Shoulders',
                        detected=True,
                        strength=0.8,
                        direction='bearish',
                        price_target=neckline - (head[1] - neckline)
                    ))
                    break
                
                # Inverse Head and Shoulders (bullish)
                if (head[1] < left_shoulder[1] and head[1] < right_shoulder[1] and
                    abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1] < 0.05):
                    
                    neckline = (left_shoulder[1] + right_shoulder[1]) / 2
                    self.patterns.append(PatternResult(
                        name='Inverse Head and Shoulders',
                        detected=True,
                        strength=0.8,
                        direction='bullish',
                        price_target=neckline + (neckline - head[1])
                    ))
                    break
    
    def detect_bullish_bearish_engulfing(self) -> None:
        """اكتشاف نموذج الابتلاع الصاعد/الهابط"""
        for i in range(1, len(self.data)):
            # Bullish Engulfing
            if (self.data['close'].iloc[i] > self.data['open'].iloc[i] and
                self.data['open'].iloc[i-1] > self.data['close'].iloc[i-1] and
                self.data['close'].iloc[i] > self.data['open'].iloc[i-1] and
                self.data['open'].iloc[i] < self.data['close'].iloc[i-1]):
                
                self.patterns.append(PatternResult(
                    name='Bullish Engulfing',
                    detected=True,
                    strength=0.75,
                    direction='bullish'
                ))
            
            # Bearish Engulfing
            if (self.data['close'].iloc[i] < self.data['open'].iloc[i] and
                self.data['open'].iloc[i-1] < self.data['close'].iloc[i-1] and
                self.data['close'].iloc[i] < self.data['open'].iloc[i-1] and
                self.data['open'].iloc[i] > self.data['close'].iloc[i-1]):
                
                self.patterns.append(PatternResult(
                    name='Bearish Engulfing',
                    detected=True,
                    strength=0.75,
                    direction='bearish'
                ))
    
    def detect_hammer_shooting_star(self) -> None:
        """اكتشاف نموذج المطرقة/النجم المتساقط"""
        for i in range(1, len(self.data)):
            body = abs(self.data['close'].iloc[i] - self.data['open'].iloc[i])
            upper_shadow = self.data['high'].iloc[i] - max(self.data['close'].iloc[i], self.data['open'].iloc[i])
            lower_shadow = min(self.data['close'].iloc[i], self.data['open'].iloc[i]) - self.data['low'].iloc[i]
            
            # Hammer (bullish)
            if (lower_shadow > body * 2 and upper_shadow < body * 0.3 and
                self.data['close'].iloc[i] < self.data['close'].iloc[i-1]):
                
                self.patterns.append(PatternResult(
                    name='Hammer',
                    detected=True,
                    strength=0.6,
                    direction='bullish'
                ))
            
            # Shooting Star (bearish)
            if (upper_shadow > body * 2 and lower_shadow < body * 0.3 and
                self.data['close'].iloc[i] > self.data['close'].iloc[i-1]):
                
                self.patterns.append(PatternResult(
                    name='Shooting Star',
                    detected=True,
                    strength=0.6,
                    direction='bearish'
                ))
    
    def detect_doji(self) -> None:
        """اكتشاف نموذج الدوجي"""
        for i in range(len(self.data)):
            body = abs(self.data['close'].iloc[i] - self.data['open'].iloc[i])
            range_ = self.data['high'].iloc[i] - self.data['low'].iloc[i]
            
            if range_ > 0 and body / range_ < 0.1:
                direction = 'neutral'
                # تحديد الاتجاه المحتمل بناءً على السياق
                if i > 0 and self.data['close'].iloc[i-1] > self.data['open'].iloc[i-1]:
                    direction = 'bearish'  # دوجي بعد شمعة صاعدة
                elif i > 0 and self.data['close'].iloc[i-1] < self.data['open'].iloc[i-1]:
                    direction = 'bullish'  # دوجي بعد شمعة هابطة
                    
                self.patterns.append(PatternResult(
                    name='Doji',
                    detected=True,
                    strength=0.5,
                    direction=direction
                ))
    
    def detect_morning_evening_star(self) -> None:
        """اكتشاف نموذج نجمة الصباح/المساء"""
        if len(self.data) < 3:
            return
            
        for i in range(2, len(self.data)):
            # Morning Star (bullish)
            if (self.data['close'].iloc[i-2] < self.data['open'].iloc[i-2] and  # شمعة هابطة
                abs(self.data['close'].iloc[i-1] - self.data['open'].iloc[i-1]) < 0.3 * (self.data['high'].iloc[i-1] - self.data['low'].iloc[i-1]) and  # دوجي
                self.data['close'].iloc[i] > self.data['open'].iloc[i] and  # شمعة صاعدة
                self.data['close'].iloc[i] > (self.data['open'].iloc[i-2] + self.data['close'].iloc[i-2]) / 2):
                
                self.patterns.append(PatternResult(
                    name='Morning Star',
                    detected=True,
                    strength=0.8,
                    direction='bullish'
                ))
            
            # Evening Star (bearish)
            if (self.data['close'].iloc[i-2] > self.data['open'].iloc[i-2] and  # شمعة صاعدة
                abs(self.data['close'].iloc[i-1] - self.data['open'].iloc[i-1]) < 0.3 * (self.data['high'].iloc[i-1] - self.data['low'].iloc[i-1]) and  # دوجي
                self.data['close'].iloc[i] < self.data['open'].iloc[i] and  # شمعة هابطة
                self.data['close'].iloc[i] < (self.data['open'].iloc[i-2] + self.data['close'].iloc[i-2]) / 2):
                
                self.patterns.append(PatternResult(
                    name='Evening Star',
                    detected=True,
                    strength=0.8,
                    direction='bearish'
                ))
    
    def detect_three_white_soldiers(self) -> None:
        """اكتشاف نموذج الجنود البيض الثلاثة"""
        if len(self.data) < 3:
            return
            
        for i in range(2, len(self.data)):
            if all([
                self.data['close'].iloc[i-j] > self.data['open'].iloc[i-j] for j in range(3)
            ]):
                if all([
                    self.data['close'].iloc[i-j] > self.data['close'].iloc[i-j-1]
                    for j in range(1, 3)
                ]):
                    if all([
                        self.data['open'].iloc[i-j] > self.data['open'].iloc[i-j-1]
                        for j in range(1, 3)
                    ]):
                        self.patterns.append(PatternResult(
                            name='Three White Soldiers',
                            detected=True,
                            strength=0.85,
                            direction='bullish'
                        ))
                        break
    
    def detect_three_black_crows(self) -> None:
        """اكتشاف نموذج الغربان السوداء الثلاثة"""
        if len(self.data) < 3:
            return
            
        for i in range(2, len(self.data)):
            if all([
                self.data['close'].iloc[i-j] < self.data['open'].iloc[i-j] for j in range(3)
            ]):
                if all([
                    self.data['close'].iloc[i-j] < self.data['close'].iloc[i-j-1]
                    for j in range(1, 3)
                ]):
                    if all([
                        self.data['open'].iloc[i-j] < self.data['open'].iloc[i-j-1]
                        for j in range(1, 3)
                    ]):
                        self.patterns.append(PatternResult(
                            name='Three Black Crows',
                            detected=True,
                            strength=0.85,
                            direction='bearish'
                        ))
                        break
    
    def detect_flags_pennants(self) -> None:
        """اكتشاف نموذج العلم والرايات"""
        # تبسيط: البحث عن حركة سعرية سريعة متبوعة بتصحيح ضيق
        window = 20
        if len(self.data) > window:
            for i in range(window, len(self.data)):
                segment = self.data.iloc[i-window:i]
                price_range = segment['high'].max() - segment['low'].min()
                price_change = (segment['close'].iloc[-1] - segment['close'].iloc[0]) / segment['close'].iloc[0]
                
                # علم صاعد (حركة سريعة صاعدة ثم تصحيح ضيق)
                if price_change > 0.05 and price_range / segment['close'].iloc[0] < 0.1:
                    self.patterns.append(PatternResult(
                        name='Bullish Flag',
                        detected=True,
                        strength=0.65,
                        direction='bullish'
                    ))
                
                # علم هابط (حركة سريعة هابطة ثم تصحيح ضيق)
                if price_change < -0.05 and price_range / segment['close'].iloc[0] < 0.1:
                    self.patterns.append(PatternResult(
                        name='Bearish Flag',
                        detected=True,
                        strength=0.65,
                        direction='bearish'
                    ))
    
    def detect_triangles(self) -> None:
        """اكتشاف نموذج المثلثات"""
        window = 30
        if len(self.data) > window:
            for i in range(window, len(self.data)):
                segment = self.data.iloc[i-window:i]
                
                # مثلث متماثل (تقارب القمم والقيعان)
                highs = segment['high'].values
                lows = segment['low'].values
                x = np.arange(len(highs))
                
                # انحدار القمم
                high_slope = np.polyfit(x, highs, 1)[0]
                low_slope = np.polyfit(x, lows, 1)[0]
                
                if high_slope < 0 and low_slope > 0:
                    self.patterns.append(PatternResult(
                        name='Symmetrical Triangle',
                        detected=True,
                        strength=0.7,
                        direction='neutral'
                    ))
                
                # مثلث صاعد (قيعان صاعدة، قمم أفقية)
                elif low_slope > 0 and abs(high_slope) < 0.01:
                    self.patterns.append(PatternResult(
                        name='Ascending Triangle',
                        detected=True,
                        strength=0.75,
                        direction='bullish'
                    ))
                
                # مثلث هابط (قمم هابطة، قيعان أفقية)
                elif high_slope < 0 and abs(low_slope) < 0.01:
                    self.patterns.append(PatternResult(
                        name='Descending Triangle',
                        detected=True,
                        strength=0.75,
                        direction='bearish'
                    ))
    
    def detect_wedges(self) -> None:
        """اكتشاف نموذج الأوتاد"""
        window = 25
        if len(self.data) > window:
            for i in range(window, len(self.data)):
                segment = self.data.iloc[i-window:i]
                highs = segment['high'].values
                lows = segment['low'].values
                x = np.arange(len(highs))
                
                high_slope = np.polyfit(x, highs, 1)[0]
                low_slope = np.polyfit(x, lows, 1)[0]
                
                # وتد صاعد (كلا الخطين صاعدين لكن أحدهما أكثر حدة)
                if high_slope > 0 and low_slope > 0 and high_slope > low_slope:
                    self.patterns.append(PatternResult(
                        name='Rising Wedge',
                        detected=True,
                        strength=0.6,
                        direction='bearish'  # وتد صاعد عادة ما يكون هابط
                    ))
                
                # وتد هابط (كلا الخطين هابطين لكن أحدهما أكثر حدة)
                elif high_slope < 0 and low_slope < 0 and high_slope < low_slope:
                    self.patterns.append(PatternResult(
                        name='Falling Wedge',
                        detected=True,
                        strength=0.6,
                        direction='bullish'  # وتد هابط عادة ما يكون صاعد
                    ))
    
    def detect_rectangles(self) -> None:
        """اكتشاف نموذج المستطيلات"""
        window = 30
        if len(self.data) > window:
            for i in range(window, len(self.data)):
                segment = self.data.iloc[i-window:i]
                
                high_range = segment['high'].max() - segment['high'].min()
                low_range = segment['low'].max() - segment['low'].min()
                avg_price = segment['close'].mean()
                
                # إذا كان المدى ضيقًا نسبيًا (مستطيل)
                if high_range / avg_price < 0.05 and low_range / avg_price < 0.05:
                    self.patterns.append(PatternResult(
                        name='Rectangle',
                        detected=True,
                        strength=0.55,
                        direction='neutral'
                    ))
    
    def detect_cup_and_handle(self) -> None:
        """اكتشاف نموذج الكأس والعروة"""
        window = 40
        if len(self.data) > window:
            for i in range(window, len(self.data)):
                segment = self.data.iloc[i-window:i]
                
                # البحث عن شكل كأس (انخفاض ثم ارتفاع)
                min_idx = segment['close'].idxmin()
                min_pos = segment.index.get_loc(min_idx)
                
                if 0.2 < min_pos / window < 0.8:
                    left_price = segment['close'].iloc[0]
                    right_price = segment['close'].iloc[-1]
                    
                    # التأكد من أن الكأس متماثل
                    if abs(left_price - right_price) / left_price < 0.05:
                        # البحث عن العروة (تصحيح صغير بعد الكأس)
                        if i + 5 < len(self.data):
                            handle = self.data.iloc[i:i+5]
                            handle_range = (handle['high'].max() - handle['low'].min()) / handle['low'].min()
                            if handle_range < 0.03:
                                self.patterns.append(PatternResult(
                                    name='Cup and Handle',
                                    detected=True,
                                    strength=0.85,
                                    direction='bullish'
                                ))
    
    def detect_candle_patterns(self) -> None:
        """اكتشاف أنماط الشموع اليابانية باستخدام TA-Lib"""
        try:
            import talib
            
            patterns = {
                'CDL2CROWS': 'Two Crows',
                'CDL3BLACKCROWS': 'Three Black Crows',
                'CDL3INSIDE': 'Three Inside',
                'CDL3LINESTRIKE': 'Three Line Strike',
                'CDL3OUTSIDE': 'Three Outside',
                'CDL3STARSINSOUTH': 'Three Stars in the South',
                'CDL3WHITESOLDIERS': 'Three White Soldiers',
                'CDLABANDONEDBABY': 'Abandoned Baby',
                'CDLADVANCEBLOCK': 'Advance Block',
                'CDLBELTHOLD': 'Belt Hold',
                'CDLBREAKAWAY': 'Breakaway',
                'CDLCLOSINGMARUBOZU': 'Closing Marubozu',
                'CDLCONCEALBABYSWALL': 'Concealing Baby Swallow',
                'CDLCOUNTERATTACK': 'Counterattack',
                'CDLDARKCLOUDCOVER': 'Dark Cloud Cover',
                'CDLDOJI': 'Doji',
                'CDLDOJISTAR': 'Doji Star',
                'CDLDRAGONFLYDOJI': 'Dragonfly Doji',
                'CDLENGULFING': 'Engulfing',
                'CDLEVENINGDOJISTAR': 'Evening Doji Star',
                'CDLEVENINGSTAR': 'Evening Star',
                'CDLGAPSIDESIDEWHITE': 'Gap Side-by-Side White',
                'CDLGRAVESTONEDOJI': 'Gravestone Doji',
                'CDLHAMMER': 'Hammer',
                'CDLHANGINGMAN': 'Hanging Man',
                'CDLHARAMI': 'Harami',
                'CDLHARAMICROSS': 'Harami Cross',
                'CDLHIGHWAVE': 'High Wave',
                'CDLHIKKAKE': 'Hikkake',
                'CDLHIKKAKEMOD': 'Hikkake Modified',
                'CDLHOMINGPIGEON': 'Homing Pigeon',
                'CDLIDENTICAL3CROWS': 'Identical Three Crows',
                'CDLINNECK': 'In Neck',
                'CDLINVERTEDHAMMER': 'Inverted Hammer',
                'CDLKICKING': 'Kicking',
                'CDLKICKINGBYLENGTH': 'Kicking by Length',
                'CDLLADDERBOTTOM': 'Ladder Bottom',
                'CDLLONGLEGGEDDOJI': 'Long Legged Doji',
                'CDLLONGLINE': 'Long Line',
                'CDLMARUBOZU': 'Marubozu',
                'CDLMATCHINGLOW': 'Matching Low',
                'CDLMATHOLD': 'Mat Hold',
                'CDLMORNINGDOJISTAR': 'Morning Doji Star',
                'CDLMORNINGSTAR': 'Morning Star',
                'CDLONNECK': 'On Neck',
                'CDLPIERCING': 'Piercing',
                'CDLRICKSHAWMAN': 'Rickshaw Man',
                'CDLRISEFALL3METHODS': 'Rise/Fall 3 Methods',
                'CDLSEPARATINGLINES': 'Separating Lines',
                'CDLSHOOTINGSTAR': 'Shooting Star',
                'CDLSHORTLINE': 'Short Line',
                'CDLSPINNINGTOP': 'Spinning Top',
                'CDLSTALLEDPATTERN': 'Stalled Pattern',
                'CDLSTICKSANDWICH': 'Stick Sandwich',
                'CDLTAKURI': 'Takuri',
                'CDLTASUKIGAP': 'Tasuki Gap',
                'CDLTHRUSTING': 'Thrusting',
                'CDLTRISTAR': 'Tristar',
                'CDLUNIQUE3RIVER': 'Unique 3 River',
                'CDLUPSIDEGAP2CROWS': 'Upside Gap 2 Crows',
                'CDLXSIDEGAP3METHODS': 'X-Side Gap 3 Methods'
            }
            
            for func_name, pattern_name in patterns.items():
                func = getattr(talib, func_name)
                result = func(self.data['open'], self.data['high'], self.data['low'], self.data['close'])
                last_value = result.iloc[-1]
                
                if last_value > 0:
                    self.patterns.append(PatternResult(
                        name=pattern_name,
                        detected=True,
                        strength=0.7,
                        direction='bullish'
                    ))
                elif last_value < 0:
                    self.patterns.append(PatternResult(
                        name=pattern_name,
                        detected
