import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import joblib
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class LightGBMModel:
    """نموذج LightGBM للتنبؤ بالأسعار"""
    
    def __init__(self, model_type: str = 'classifier', random_state: int = 42):
        """
        تهيئة نموذج LightGBM
        
        Args:
            model_type: 'classifier' أو 'regressor'
            random_state: بذرة العشوائية
        """
        self.model_type = model_type
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # إنشاء النموذج المناسب
        if model_type == 'classifier':
            self.model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=-1,
                learning_rate=0.1,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=random_state,
                verbose=-1
            )
        else:
            self.model = lgb.LGBMRegressor(
                n_estimators=100,
                max_depth=-1,
                learning_rate=0.1,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=random_state,
                verbose=-1
            )
    
    def prepare_data(self, features: pd.DataFrame, target: pd.Series, 
                    test_size: float = 0.2) -> Tuple:
        """تجهيز البيانات للتدريب"""
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=test_size, random_state=self.random_state
        )
        
        # تطبيق التطبيع
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              use_grid_search: bool = False) -> Dict:
        """تدريب النموذج"""
        if use_grid_search:
            # بحث الشبكة لتحسين المعلمات
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [-1, 5, 10],
                'learning_rate': [0.01, 0.1, 0.3],
                'num_leaves': [15, 31, 63],
                'subsample': [0.6, 0.8, 1.0],
                'colsample_bytree': [0.6, 0.8, 1.0],
                'min_child_samples': [5, 10, 20]
            }
            
            grid_search = GridSearchCV(
                self.model, param_grid, cv=5, scoring='accuracy' if self.model_type == 'classifier' else 'neg_mean_squared_error',
                n_jobs=-1, verbose=1
            )
            
            grid_search.fit(X_train, y_train)
            self.model = grid_search.best_estimator_
            best_params = grid_search.best_params_
        else:
            # تدريب النموذج
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_train, y_train)],
                eval_metric='logloss' if self.model_type == 'classifier' else 'rmse',
                callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
            )
            best_params = self.model.get_params()
        
        self.is_fitted = True
        
        return {
            'best_params': best_params,
            'feature_importance': self.get_feature_importance()
        }
    
    def predict(self, X_test: np.ndarray) -> np.ndarray:
        """إجراء التنبؤات"""
        if not self.is_fitted:
            raise ValueError("النموذج لم يتم تدريبه بعد")
        
        return self.model.predict(X_test)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """تقييم أداء النموذج"""
        predictions = self.predict(X_test)
        
        if self.model_type == 'classifier':
            accuracy = accuracy_score(y_test, predictions)
            return {
                'accuracy': accuracy,
                'classification_report': classification_report(y_test, predictions, output_dict=True)
            }
        else:
            mse = mean_squared_error(y_test, predictions)
            r2 = r2_score(y_test, predictions)
            return {
                'mse': mse,
                'rmse': np.sqrt(mse),
                'r2': r2,
                'mae': np.mean(np.abs(y_test - predictions))
            }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """الحصول على أهمية الميزات"""
        if not hasattr(self.model, 'feature_importances_'):
            return {}
        
        importances = self.model.feature_importances_
        return {f'feature_{i}': importance for i, importance in enumerate(importances)}
    
    def save_model(self, filepath: str):
        """حفظ النموذج"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'random_state': self.random_state
        }, filepath)
    
    def load_model(self, filepath: str):
        """تحميل النموذج"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.model_type = data['model_type']
        self.random_state = data.get('random_state', 42)
        self.is_fitted = True
    
    def predict_proba(self, X_test: np.ndarray) -> np.ndarray:
        """الحصول على احتمالات التنبؤ (للتصنيف)"""
        if self.model_type != 'classifier':
            raise ValueError("النتائج الاحتمالية متاحة فقط لنماذج التصنيف")
        
        return self.model.predict_proba(X_test)
