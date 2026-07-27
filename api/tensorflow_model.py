import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class TensorFlowModel:
    """نموذج TensorFlow للتنبؤ بالأسعار (مع دعم البدائل)"""
    
    def __init__(self, model_type: str = 'classifier', input_shape: int = None,
                 hidden_layers: List[int] = [128, 64, 32], random_state: int = 42):
        self.model_type = model_type
        self.input_shape = input_shape
        self.hidden_layers = hidden_layers
        self.random_state = random_state
        self.model = None
        self.is_fitted = False
        self.history = None
        self.use_tensorflow = False
        
        # محاولة استيراد TensorFlow
        try:
            import tensorflow as tf
            from tensorflow import keras
            from tensorflow.keras import layers, models, callbacks
            self.tf = tf
            self.keras = keras
            self.layers = layers
            self.models = models
            self.callbacks = callbacks
            self.use_tensorflow = True
            print("TensorFlow تم تحميله بنجاح")
        except ImportError:
            print("TensorFlow غير مثبت. سيتم استخدام Scikit-Learn كبديل.")
            from sklearn.neural_network import MLPClassifier, MLPRegressor
            self.MLPClassifier = MLPClassifier
            self.MLPRegressor = MLPRegressor
            
    def build_model(self):
        """بناء نموذج الشبكة العصبية"""
        if self.use_tensorflow:
            return self._build_tensorflow_model()
        else:
            return self._build_sklearn_model()
    
    def _build_tensorflow_model(self):
        """بناء نموذج TensorFlow"""
        if self.input_shape is None:
            raise ValueError("يجب تحديد input_shape قبل بناء النموذج")
        
        model = self.models.Sequential()
        
        # طبقة الإدخال
        model.add(self.layers.Input(shape=(self.input_shape,)))
        
        # طبقات مخفية مع Dropout
        for i, units in enumerate(self.hidden_layers):
            model.add(self.layers.Dense(units, activation='relu'))
            model.add(self.layers.Dropout(0.3 if i < len(self.hidden_layers) - 1 else 0.2))
            model.add(self.layers.BatchNormalization())
        
        # طبقة الإخراج
        if self.model_type == 'classifier':
            model.add(self.layers.Dense(1, activation='sigmoid'))
            model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy', 'AUC']
            )
        else:
            model.add(self.layers.Dense(1, activation='linear'))
            model.compile(
                optimizer='adam',
                loss='mse',
                metrics=['mae']
            )
        
        return model
    
    def _build_sklearn_model(self):
        """بناء نموذج Scikit-Learn كبديل"""
        if self.model_type == 'classifier':
            return self.MLPClassifier(
                hidden_layer_sizes=tuple(self.hidden_layers),
                activation='relu',
                solver='adam',
                max_iter=1000,
                random_state=self.random_state,
                early_stopping=True,
                validation_fraction=0.1
            )
        else:
            return self.MLPRegressor(
                hidden_layer_sizes=tuple(self.hidden_layers),
                activation='relu',
                solver='adam',
                max_iter=1000,
                random_state=self.random_state,
                early_stopping=True,
                validation_fraction=0.1
            )
    
    def prepare_data(self, features: pd.DataFrame, target: pd.Series, 
                    test_size: float = 0.2) -> Tuple:
        """تجهيز البيانات للتدريب"""
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        
        X_train, X_test, y_train, y_test = train_test_split(
            features, target, test_size=test_size, random_state=self.random_state
        )
        
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              epochs: int = 100, batch_size: int = 32,
              use_early_stopping: bool = True) -> Dict:
        """تدريب النموذج"""
        if self.input_shape is None:
            self.input_shape = X_train.shape[1]
        
        if self.model is None:
            self.model = self.build_model()
        
        if self.use_tensorflow:
            return self._train_tensorflow(X_train, y_train, X_val, y_val, epochs, batch_size, use_early_stopping)
        else:
            return self._train_sklearn(X_train, y_train)
    
    def _train_tensorflow(self, X_train, y_train, X_val, y_val, epochs, batch_size, use_early_stopping):
        """تدريب نموذج TensorFlow"""
        callbacks_list = []
        
        if use_early_stopping and X_val is not None:
            callbacks_list.append(
                self.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=15,
                    restore_best_weights=True
                )
            )
        
        callbacks_list.append(
            self.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=7,
                min_lr=0.0001
            )
        )
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val) if X_val is not None else None,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks_list,
            verbose=0
        )
        
        self.is_fitted = True
        self.history = history.history
        
        return {
            'history': history.history,
            'final_loss': history.history['loss'][-1],
        }
    
    def _train_sklearn(self, X_train, y_train):
        """تدريب نموذج Scikit-Learn"""
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        
        return {
            'final_loss': 0,
            'n_iter': self.model.n_iter_
        }
    
    def predict(self, X_test: np.ndarray) -> np.ndarray:
        """إجراء التنبؤات"""
        if not self.is_fitted or self.model is None:
            raise ValueError("النموذج لم يتم تدريبه بعد")
        
        if self.use_tensorflow:
            predictions = self.model.predict(X_test, verbose=0)
            if self.model_type == 'classifier':
                return (predictions > 0.5).astype(int).flatten()
            else:
                return predictions.flatten()
        else:
            predictions = self.model.predict(X_test)
            return predictions
    
    def predict_proba(self, X_test: np.ndarray) -> np.ndarray:
        """الحصول على احتمالات التنبؤ (للتصنيف)"""
        if self.model_type != 'classifier':
            raise ValueError("النتائج الاحتمالية متاحة فقط لنماذج التصنيف")
        
        if not self.is_fitted or self.model is None:
            raise ValueError("النموذج لم يتم تدريبه بعد")
        
        if self.use_tensorflow:
            probabilities = self.model.predict(X_test, verbose=0)
            return probabilities.flatten()
        else:
            return self.model.predict_proba(X_test)[:, 1]
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """تقييم أداء النموذج"""
        from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
        
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
    
    def save_model(self, filepath: str):
        """حفظ النموذج"""
        import joblib
        
        if self.use_tensorflow and self.model is not None:
            self.model.save(f"{filepath}_weights.h5")
            model_data = {
                'scaler': getattr(self, 'scaler', None),
                'model_type': self.model_type,
                'input_shape': self.input_shape,
                'hidden_layers': self.hidden_layers,
                'random_state': self.random_state,
                'history': self.history,
                'use_tensorflow': self.use_tensorflow
            }
            joblib.dump(model_data, f"{filepath}_config.pkl")
        else:
            joblib.dump({
                'model': self.model,
                'scaler': getattr(self, 'scaler', None),
                'model_type': self.model_type,
                'input_shape': self.input_shape,
                'hidden_layers': self.hidden_layers,
                'random_state': self.random_state,
                'use_tensorflow': self.use_tensorflow
            }, filepath)
    
    def load_model(self, filepath: str):
        """تحميل النموذج"""
        import joblib
        
        if self.use_tensorflow:
            data = joblib.load(f"{filepath}_config.pkl")
            self.model_type = data['model_type']
            self.input_shape = data['input_shape']
            self.hidden_layers = data['hidden_layers']
            self.random_state = data.get('random_state', 42)
            self.history = data.get('history')
            self.scaler = data.get('scaler')
            self.model = self.build_model()
            self.model.load_weights(f"{filepath}_weights.h5")
        else:
            data = joblib.load(filepath)
            self.model = data['model']
            self.scaler = data.get('scaler')
            self.model_type = data['model_type']
            self.input_shape = data.get('input_shape')
            self.hidden_layers = data.get('hidden_layers', [128, 64, 32])
            self.random_state = data.get('random_state', 42)
        
        self.is_fitted = True
