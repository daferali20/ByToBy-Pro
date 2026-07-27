"""
حزمة التحليل الفني والتعلم الآلي للتداول
=====================================

هذه الحزمة توفر أدوات متكاملة للتحليل الفني، اكتشاف النماذج،
والتنبؤ بأسعار الأسهم باستخدام تقنيات التعلم الآلي.

المكونات الرئيسية:
------------------
- features: استخراج المؤشرات الفنية
- pattern_detector: اكتشاف النماذج الفنية
- score: حساب النتائج الفنية
- recommendation: توليد التوصيات
- ranking: ترتيب الصفقات
- random_forest: نموذج الغابة العشوائية
- xgboost_model: نموذج XGBoost
- lightgbm_model: نموذج LightGBM
- tensorflow_model: نموذج الشبكات العصبية
- predict: نظام التنبؤ
- train: نظام التدريب

الاستخدام الأساسي:
------------------
from trading_system import PredictionSystem, TrainingSystem
import pandas as pd

# تحميل البيانات
data = pd.read_csv('stock_data.csv')

# إنشاء نظام التنبؤ
predictor = PredictionSystem(data, model_type='ensemble')

# تشغيل التنبؤ
prediction = predictor.run_prediction()
print(prediction)

# تدريب النماذج
trainer = TrainingSystem(data, model_type='ensemble')
results = trainer.run_full_training()

المتطلبات:
----------
- pandas, numpy
- scikit-learn
- xgboost, lightgbm
- tensorflow
- TA-Lib (اختياري)

"""
from .features import TechnicalFeatures
from .pattern_detector import PatternDetector, PatternResult
from .pattern_score import PatternScorer
from .score import ScoreCalculator
from .recommendation import RecommendationSystem
from .ranking import RankingSystem
from .random_forest import RandomForestModel
from .xgboost_model import XGBoostModel
from .lightgbm_model import LightGBMModel
from .tensorflow_model import TensorFlowModel
from .predict import PredictionSystem
from .train import TrainingSystem

__version__ = '1.0.0'
__author__ = 'Trading Analysis System'

__all__ = [
    'TechnicalFeatures',
    'PatternDetector',
    'PatternResult',
    'PatternScorer',
    'ScoreCalculator',
    'RecommendationSystem',
    'RankingSystem',
    'RandomForestModel',
    'XGBoostModel',
    'LightGBMModel',
    'TensorFlowModel',
    'PredictionSystem',
    'TrainingSystem'
]

def create_trading_system(data, model_type='ensemble'):
    """
    إنشاء نظام تداول كامل
    
    Args:
        data: DataFrame مع بيانات OHLCV
        model_type: نوع النموذج
    
    Returns:
        tuple: (prediction_system, training_system)
    """
    prediction_system = PredictionSystem(data, model_type)
    training_system = TrainingSystem(data, model_type)
    
    return prediction_system, training_system
