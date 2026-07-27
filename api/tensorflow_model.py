import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import joblib
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class TensorFlowModel:
    """نموذج TensorFlow للتنبؤ بالأسعار"""
    
    def __init__(self, model_type: str = 'classifier', input_shape: int = None,
                 hidden_layers: List[int] = [128, 64, 32], random_state: int = 42):
        """
        تهيئة نموذج TensorFlow
        
        Args:
            model_type: 'classifier' أو 'regressor'
            input_shape: عدد الميزات المدخلة
            hidden_layers: قائمة بعدد الخلايا في كل طبقة مخفية
            random_state: بذرة العشوائية
        """
        self.model_type = model_type
        self.input_shape = input_shape
        self.hidden_layers = hidden_layers
        self.random_state = random_state
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.history = None
        
    def build_model(self) -> keras.Model:
        """بناء نموذج الشبكة العصبية"""
        if self.input_shape is None:
            raise ValueError("يجب تحديد input_shape قبل بناء النموذج")
        
        model = models.Sequential()
        
        # طبقة الإدخال
        model.add(layers.Input(shape=(self.input_shape,)))
        
        # طبقات مخفية مع Dropout
        for i, units in enumerate(self.hidden_layers):
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.Dropout(0.3 if i < len(self.hidden_layers) - 1 else 0.2))
            model.add(layers.BatchNormalization())
        
        # طبقة الإخراج
        if self.model_type == 'classifier':
            model.add(layers.Dense(1, activation='sigmoid'))
            model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy', 'AUC']
            )
        else:
            model.add(layers.Dense(1, activation='linear'))
            model.compile(
                optimizer='adam',
                loss='mse',
                metrics=['mae']
            )
        
        return model
    
    def prepare_data(self, features: pd.DataFrame, target: pd.Series, 
                    test_size: float = 0.2, validation_size: float = 0.2) -> Tuple:
        """تجهيز البيانات للتدريب"""
        X_train, X_temp, y_train, y_temp = train_test_split(
            features, target, test_size=test_size, random_state=self.random_state
        )
        
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=self.random_state
        )
        
        # تطبيق التطبيع
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              epochs: int = 100, batch_size: int = 32,
              use_early_stopping: bool = True) -> Dict:
        """تدريب النموذج"""
        # تعيين input_shape إذا لم يتم تعيينه مسبقًا
        if self.input_shape is None:
            self.input_shape = X_train.shape[1]
        
        # بناء النموذج إذا لم يتم بناؤه
        if self.model is None:
            self.model = self.build_model()
        
        # إعداد استدعاءات التدريب
        callbacks_list = []
        
        if use_early_stopping and X_val is not None:
            callbacks_list.append(
                callbacks.EarlyStopping(
                    monitor='val_loss' if X_val is not None else 'loss',
                    patience=15,
                    restore_best_weights=True
                )
            )
        
        callbacks_list.append(
            callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=7,
                min_lr=0.0001
            )
        )
        
        # تدريب النموذج
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val) if X_val is not None else None,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks_list,
            verbose=1
        )
        
        self.is_fitted = True
        self.history = history.history
        
        return {
            'history': history.history,
            'final_loss': history.history['loss'][-1],
            'final_accuracy': history.history.get('accuracy', [0])[-1] if self.model_type == 'classifier' else None
        }
    
    def predict(self, X_test: np.ndarray) -> np.ndarray:
        """إجراء التنبؤات"""
        if not self.is_fitted or self.model is None:
            raise ValueError("النموذج لم يتم تدريبه بعد")
        
        predictions = self.model.predict(X_test)
        
        if self.model_type == 'classifier':
            return (predictions > 0.5).astype(int).flatten()
        else:
            return predictions.flatten()
    
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
    
    def predict_proba(self, X_test: np.ndarray) -> np.ndarray:
        """الحصول على احتمالات التنبؤ (للتصنيف)"""
        if self.model_type != 'classifier' or self.model is None:
            raise ValueError("النتائج الاحتمالية متاحة فقط لنماذج التصنيف المدربة")
        
        probabilities = self.model.predict(X_test)
        return probabilities.flatten()
    
    def save_model(self, filepath: str):
        """حفظ النموذج"""
        model_data = {
            'scaler': self.scaler,
            'model_type': self.model_type,
            'input_shape': self.input_shape,
            'hidden_layers': self.hidden_layers,
            'random_state': self.random_state,
            'history': self.history
        }
        
        # حفظ النموذج بالكامل
        if self.model is not None:
            self.model.save(f"{filepath}_weights.h5")
            model_data['model_weights_path'] = f"{filepath}_weights.h5"
        
        joblib.dump(model_data, f"{filepath}_config.pkl")
    
    def load_model(self, filepath: str):
        """تحميل النموذج"""
        # تحميل التكوين
        model_data = joblib.load(f"{filepath}_config.pkl")
        
        self.scaler = model_data['scaler']
        self.model_type = model_data['model_type']
        self.input_shape = model_data['input_shape']
        self.hidden_layers = model_data['hidden_layers']
        self.random_state = model_data.get('random_state', 42)
        self.history = model_data.get('history')
        
        # تحميل النموذج
        self.model = self.build_model()
        self.model.load_weights(f"{filepath}_weights.h5")
        self.is_fitted = True
