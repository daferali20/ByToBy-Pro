# إنشاء ملف test.py في نفس المجلد

import pandas as pd
import numpy as np
from trading_system import PredictionSystem, TrainingSystem, ScoreCalculator

# إنشاء بيانات تجريبية
dates = pd.date_range('2020-01-01', periods=500, freq='D')
data = pd.DataFrame({
    'open': np.random.randn(500).cumsum() + 100,
    'high': np.random.randn(500).cumsum() + 102,
    'low': np.random.randn(500).cumsum() + 98,
    'close': np.random.randn(500).cumsum() + 100,
    'volume': np.random.randint(1000, 10000, 500)
}, index=dates)

# استخدام النظام
print("=== نظام التداول ===\n")

# 1. حساب النتائج
score_calc = ScoreCalculator(data)
scores = score_calc.calculate_all_scores()
print("النتائج الفنية:", scores)

# 2. التنبؤ
predictor = PredictionSystem(data, model_type='ensemble')
prediction = predictor.run_prediction()
print("\nالتنبؤ:", prediction)

# 3. التدريب
trainer = TrainingSystem(data, model_type='ensemble')
results = trainer.run_full_training()
print("\nنتائج التدريب:", results['report'])
