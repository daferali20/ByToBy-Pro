import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import talib

class TechnicalFeatures:
    """استخراج المؤشرات الفنية من بيانات السوق"""
    
    def __init__(self, data: pd.DataFrame):
        """
        تهيئة الكائن مع بيانات OHLCV
        
        Args:
            data: DataFrame يحتوي على أعمدة ['open', 'high', 'low', 'close', 'volume']
        """
        self.data = data
        self.features = pd.DataFrame(index=data.index)
        
    def extract_all_features(self) -> pd.DataFrame:
        """استخراج جميع المؤشرات الفنية"""
        # مؤشرات الاتجاه
        self.add_sma()
        self.add_ema()
        self.add_macd()
        self.add_adx()
        self.add_ichimoku()
        
        # مؤشرات التذبذب
        self.add_rsi()
        self.add_stochastic()
        self.add_williams_r()
        self.add_cci()
        self.add_mfi()
        
        # مؤشرات الحجم
        self.add_obv()
        self.add_vwap()
        self.add_ad()
        
        # مؤشرات التقلب
        self.add_bollinger_bands()
        self.add_atr()
        self.add_keltner()
        
        # مؤشرات أخرى
        self.add_aroon()
        self.add_psar()
        self.add_trix()
        self.add_ultrasonic()
        
        # المؤشرات المخصصة
        self.add_price_patterns()
        self.add_volume_patterns()
        
        return self.features
    
    def add_sma(self, periods: List[int] = [10, 20, 30, 50, 100, 200]):
        """إضافة المتوسطات المتحركة البسيطة"""
        for period in periods:
            self.features[f'sma_{period}'] = talib.SMA(self.data['close'], timeperiod=period)
            
    def add_ema(self, periods: List[int] = [9, 12, 20, 26, 50]):
        """إضافة المتوسطات المتحركة الأسية"""
        for period in periods:
            self.features[f'ema_{period}'] = talib.EMA(self.data['close'], timeperiod=period)
            
    def add_macd(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """إضافة مؤشر MACD"""
        macd, macd_signal, macd_hist = talib.MACD(
            self.data['close'], fastperiod=fast, slowperiod=slow, signalperiod=signal
        )
        self.features['macd'] = macd
        self.features['macd_signal'] = macd_signal
        self.features['macd_histogram'] = macd_hist
        
    def add_rsi(self, period: int = 14):
        """إضافة مؤشر القوة النسبية"""
        self.features['rsi'] = talib.RSI(self.data['close'], timeperiod=period)
        
    def add_bollinger_bands(self, period: int = 20, nbdev: float = 2):
        """إضافة شرائط بولينجر"""
        upper, middle, lower = talib.BBANDS(
            self.data['close'], timeperiod=period, nbdevup=nbdev, nbdevdn=nbdev
        )
        self.features['bb_upper'] = upper
        self.features['bb_middle'] = middle
        self.features['bb_lower'] = lower
        self.features['bb_width'] = (upper - lower) / middle
        self.features['bb_position'] = (self.data['close'] - lower) / (upper - lower)
        
    def add_stochastic(self, fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3):
        """إضافة مؤشر الاستوكاستيك"""
        slowk, slowd = talib.STOCH(
            self.data['high'], self.data['low'], self.data['close'],
            fastk_period=fastk_period, slowk_period=slowk_period, slowd_period=slowd_period
        )
        self.features['stoch_k'] = slowk
        self.features['stoch_d'] = slowd
        
    def add_adx(self, period: int = 14):
        """إضافة مؤشر ADX"""
        self.features['adx'] = talib.ADX(self.data['high'], self.data['low'], self.data['close'], timeperiod=period)
        self.features['plus_di'] = talib.PLUS_DI(self.data['high'], self.data['low'], self.data['close'], timeperiod=period)
        self.features['minus_di'] = talib.MINUS_DI(self.data['high'], self.data['low'], self.data['close'], timeperiod=period)
        
    def add_atr(self, period: int = 14):
        """إضافة متوسط المدى الحقيقي"""
        self.features['atr'] = talib.ATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=period)
        
    def add_obv(self):
        """إضافة مؤشر الحجم المتوازن"""
        self.features['obv'] = talib.OBV(self.data['close'], self.data['volume'])
        
    def add_vwap(self):
        """إضافة متوسط السعر المرجح بالحجم"""
        self.features['vwap'] = (self.data['volume'] * (self.data['high'] + self.data['low'] + self.data['close']) / 3).cumsum() / self.data['volume'].cumsum()
        
    def add_ad(self):
        """إضافة مؤشر التراكم/التوزيع"""
        self.features['ad'] = talib.AD(self.data['high'], self.data['low'], self.data['close'], self.data['volume'])
        
    def add_cci(self, period: int = 20):
        """إضافة مؤشر قناة السلع"""
        self.features['cci'] = talib.CCI(self.data['high'], self.data['low'], self.data['close'], timeperiod=period)
        
    def add_williams_r(self, period: int = 14):
        """إضافة مؤشر ويليامز %R"""
        self.features['williams_r'] = talib.WILLR(self.data['high'], self.data['low'], self.data['close'], timeperiod=period)
        
    def add_mfi(self, period: int = 14):
        """إضافة مؤشر تدفق المال"""
        self.features['mfi'] = talib.MFI(self.data['high'], self.data['low'], self.data['close'], self.data['volume'], timeperiod=period)
        
    def add_ichimoku(self):
        """إضافة مؤشر إيشيموكو"""
        high9 = self.data['high'].rolling(9).max()
        low9 = self.data['low'].rolling(9).min()
        high26 = self.data['high'].rolling(26).max()
        low26 = self.data['low'].rolling(26).min()
        high52 = self.data['high'].rolling(52).max()
        low52 = self.data['low'].rolling(52).min()
        
        self.features['tenkan_sen'] = (high9 + low9) / 2
        self.features['kijun_sen'] = (high26 + low26) / 2
        self.features['senkou_span_a'] = ((self.features['tenkan_sen'] + self.features['kijun_sen']) / 2).shift(26)
        self.features['senkou_span_b'] = ((high52 + low52) / 2).shift(26)
        self.features['chikou_span'] = self.data['close'].shift(-26)
        
    def add_aroon(self, period: int = 25):
        """إضافة مؤشر أرون"""
        aroon_down, aroon_up = talib.AROON(self.data['high'], self.data['low'], timeperiod=period)
        self.features['aroon_up'] = aroon_up
        self.features['aroon_down'] = aroon_down
        self.features['aroon_osc'] = aroon_up - aroon_down
        
    def add_psar(self, acceleration: float = 0.02, maximum: float = 0.2):
        """إضافة مؤشر وقف الانعكاس المكافئ"""
        self.features['psar'] = talib.SAR(self.data['high'], self.data['low'], acceleration=acceleration, maximum=maximum)
        
    def add_trix(self, period: int = 15):
        """إضافة مؤشر Trix"""
        self.features['trix'] = talib.TRIX(self.data['close'], timeperiod=period)
        
    def add_ultrasonic(self, period: int = 14):
        """إضافة مؤشر الموجات فوق الصوتية"""
        self.features['ultrasonic'] = talib.ULTOSC(
            self.data['high'], self.data['low'], self.data['close'],
            timeperiod1=7, timeperiod2=14, timeperiod3=28
        )
        
    def add_keltner(self, period: int = 20, atr_multiplier: float = 2):
        """إضافة قنوات كيلتنر"""
        ema = talib.EMA(self.data['close'], timeperiod=period)
        atr = talib.ATR(self.data['high'], self.data['low'], self.data['close'], timeperiod=period)
        self.features['keltner_upper'] = ema + (atr * atr_multiplier)
        self.features['keltner_lower'] = ema - (atr * atr_multiplier)
        self.features['keltner_middle'] = ema
        
    def add_price_patterns(self):
        """إضافة أنماط السعر"""
        self.features['price_range'] = self.data['high'] - self.data['low']
        self.features['price_change'] = self.data['close'].pct_change()
        self.features['high_low_ratio'] = self.data['high'] / self.data['low']
        self.features['close_open_ratio'] = self.data['close'] / self.data['open']
        
    def add_volume_patterns(self):
        """إضافة أنماط الحجم"""
        self.features['volume_change'] = self.data['volume'].pct_change()
        self.features['volume_ma_ratio'] = self.data['volume'] / self.data['volume'].rolling(20).mean()
        
    def get_feature_importance(self) -> Dict[str, float]:
        """تقييم أهمية المؤشرات (يمكن توسيعه لاحقًا)"""
        return {col: 1.0 for col in self.features.columns}
