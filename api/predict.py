import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .features import TechnicalFeatures
from .score import ScoreCalculator
from .random_forest import RandomForestModel
from .xgboost_model import XGBoostModel
from .lightgbm_model import LightGBMModel

class PredictionSystem:
    """نظام التنبؤ بالأسعار باستخدام نماذج متعددة"""
    
    def __init__(self, data: pd.DataFrame, model_type: str = 'ensemble'):
        self.data = data
        self.model_type = model_type
        self.models = {}
        self.predictions = {}
        
        self._initialize_models()
        
    def _initialize_models(self):
        """تهيئة جميع النماذج"""
        if self.model_type == 'ensemble' or self.model_type == 'random_forest':
            self.models['random_forest'] = RandomForestModel('classifier')
        if self.model_type == 'ensemble' or self.model_type == 'xgboost':
            self.models['xgboost'] = XGBoostModel('classifier')
        if self.model_type == 'ensemble' or self.model_type == 'lightgbm':
            self.models['lightgbm'] = LightGBMModel('classifier')
        
        # محاولة تحميل TensorFlow إذا كان موجودًا
        try:
            from .tensorflow_model import TensorFlowModel
            if self.model_type == 'ensemble' or self.model_type == 'tensorflow':
                self.models['tensorflow'] = TensorFlowModel('classifier')
        except ImportError:
            print("TensorFlow غير متوفر. سيتم استخدام النماذج المتاحة فقط.")
    
    def prepare_features(self) -> pd.DataFrame:
        """تجهيز الميزات للتنبؤ"""
        tech_features = TechnicalFeatures(self.data)
        features = tech_features.extract_all_features()
        features = features.dropna()
        return features
    
    def prepare_target(self, horizon: int = 5) -> pd.Series:
        """تجهيز الهدف للتنبؤ"""
        future_prices = self.data['close'].shift(-horizon)
        current_prices = self.data['close']
        target = (future_prices > current_prices).astype(int)
        return target.iloc[:-horizon]
    
    def train_models(self, features: pd.DataFrame, target: pd.Series) -> Dict:
        """تدريب جميع النماذج"""
        training_results = {}
        
        for model_name, model in self.models.items():
            try:
                print(f"Training {model_name}...")
                
                X_train, X_test, y_train, y_test = model.prepare_data(features, target)
                
                training_results[model_name] = model.train(X_train, y_train)
                
                eval_results = model.evaluate(X_test, y_test)
                training_results[model_name]['evaluation'] = eval_results
                
            except Exception as e:
                print(f"خطأ في تدريب {model_name}: {e}")
                training_results[model_name] = {'error': str(e)}
        
        return training_results
    
    def predict_future(self, features: pd.DataFrame) -> Dict:
        """التنبؤ بالاتجاه المستقبلي"""
        predictions = {}
        
        for model_name, model in self.models.items():
            if hasattr(model, 'is_fitted') and model.is_fitted:
                try:
                    latest_features = features.iloc[-1:].values
                    if hasattr(model, 'scaler'):
                        scaled_features = model.scaler.transform(latest_features)
                    else:
                        scaled_features = latest_features
                    
                    pred = model.predict(scaled_features)[0]
                    proba = model.predict_proba(scaled_features)[0] if hasattr(model, 'predict_proba') else None
                    
                    predictions[model_name] = {
                        'prediction': int(pred),
                        'confidence': float(proba) if proba is not None else 0.5,
                        'signal': 'BUY' if pred == 1 else 'SELL'
                    }
                except Exception as e:
                    print(f"خطأ في التنبؤ باستخدام {model_name}: {e}")
        
        return predictions
    
    def ensemble_predict(self, predictions: Dict) -> Dict:
        """الجمع بين تنبؤات النماذج المختلفة"""
        if not predictions:
            return {'signal': 'NEUTRAL', 'confidence': 0.0}
        
        avg_prediction = np.mean([p['prediction'] for p in predictions.values()])
        avg_confidence = np.mean([p['confidence'] for p in predictions.values()])
        
        vote_count = sum([p['prediction'] for p in predictions.values()])
        consensus = vote_count / len(predictions)
        
        return {
            'signal': 'BUY' if avg_prediction >= 0.5 else 'SELL',
            'confidence': avg_confidence,
            'consensus': consensus,
            'model_predictions': predictions
        }
    
    def run_prediction(self) -> Dict:
        """تشغيل نظام التنبؤ الكامل"""
        features = self.prepare_features()
        
        if len(features) > 0:
            predictions = self.predict_future(features)
            
            if len(predictions) > 1:
                result = self.ensemble_predict(predictions)
            else:
                result = list(predictions.values())[0] if predictions else {}
            
            result['market_analysis'] = self._analyze_market()
            
            return result
        else:
            return {
                'signal': 'NEUTRAL',
                'confidence': 0.0,
                'error': 'لا توجد بيانات كافية للتنبؤ'
            }
    
    def _analyze_market(self) -> Dict:
        """تحليل السوق الإضافي"""
        score_calc = ScoreCalculator(self.data)
        scores = score_calc.calculate_all_scores()
        
        return {
            'overall_score': scores['overall_score'],
            'technical_score': scores['technical_score'],
            'pattern_score': scores['pattern_score'],
            'volume_score': scores['volume_score'],
            'momentum_score': scores['momentum_score'],
            'recommendation': 'BUY' if scores['overall_score'] > 50 else 'SELL'
        }
    
    def save_models(self, base_path: str = 'models/'):
        """حفظ جميع النماذج"""
        import os
        os.makedirs(base_path, exist_ok=True)
        
        for model_name, model in self.models.items():
            if hasattr(model, 'is_fitted') and model.is_fitted:
                try:
                    model.save_model(f"{base_path}{model_name}")
                except Exception as e:
                    print(f"خطأ في حفظ {model_name}: {e}")
    
    def load_models(self, base_path: str = 'models/'):
        """تحميل النماذج المحفوظة"""
        for model_name, model in self.models.items():
            try:
                model.load_model(f"{base_path}{model_name}")
                print(f"Loaded {model_name}")
            except Exception as e:
                print(f"Could not load {model_name}: {e}")
