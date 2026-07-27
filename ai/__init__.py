# ai/__init__.py
"""
ByToBy Pro - AI Module
وحدة الذكاء الاصطناعي لتحليل الأسهم
"""

from .predict import (
    StockPredictor,
    predict_stock,
    predict_batch,
    analyze_sector,
    get_module_info,
    get_predictor
)

__version__ = "1.0.0"
__all__ = [
    "StockPredictor",
    "predict_stock",
    "predict_batch",
    "analyze_sector",
    "get_module_info",
    "get_predictor"
]

print("✅ AI Module loaded successfully")
