import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime
import json
from .predict import PredictionSystem
from .score import ScoreCalculator

class TrainingSystem:
    """نظام تدريب النماذج وتقييم الأداء"""
    
    def __init__(self, data: pd.DataFrame, model_type: str = 'ensemble'):
        self.data = data
        self.model_type = model_type
        self.prediction_system = PredictionSystem(data, model_type)
        self.training_history = {}
        
    def train_all_models(self, test_size: float = 0.2) -> Dict:
        """تدريب جميع النماذج"""
        print("بدء تدريب النماذج...")
        
        features = self.prediction_system.prepare_features()
        target = self.prediction_system.prepare_target()
        
        min_len = min(len(features), len(target))
        features = features.iloc[:min_len]
        target = target.iloc[:min_len]
        
        training_results = self.prediction_system.train_models(features, target)
        
        self.training_history = {
            'timestamp': datetime.now().isoformat(),
            'model_type': self.model_type,
            'data_shape': features.shape,
            'test_size': test_size,
            'results': training_results
        }
        
        print("انتهى تدريب النماذج")
        return training_results
    
    def evaluate_models(self) -> Dict:
        """تقييم أداء النماذج المدربة"""
        evaluation_results = {}
        
        for model_name, model in self.prediction_system.models.items():
            if model.is_fitted:
                features = self.prediction_system.prepare_features()
                target = self.prediction_system.prepare_target()
                
                min_len = min(len(features), len(target))
                features = features.iloc[:min_len]
                target = target.iloc[:min_len]
                
                X_train, X_test, y_train, y_test = model.prepare_data(features, target)
                eval_results = model.evaluate(X_test, y_test)
                
                eval_results['model_name'] = model_name
                eval_results['is_fitted'] = model.is_fitted
                if hasattr(model, 'history') and model.history:
                    eval_results['training_history'] = model.history
                
                evaluation_results[model_name] = eval_results
        
        return evaluation_results
    
    def backtest_models(self, window_size: int = 100, step_size: int = 20) -> Dict:
        """اختبار النماذج على بيانات تاريخية"""
        backtest_results = {}
        
        for model_name, model in self.prediction_system.models.items():
            if not model.is_fitted:
                continue
                
            print(f"تنفيذ backtest للنموذج {model_name}...")
            
            predictions = []
            actuals = []
            
            features = self.prediction_system.prepare_features()
            target = self.prediction_system.prepare_target()
            
            min_len = min(len(features), len(target))
            features = features.iloc[:min_len]
            target = target.iloc[:min_len]
            
            for i in range(0, len(features) - window_size, step_size):
                train_idx = i
                test_idx = i + window_size
                
                X_train = features.iloc[train_idx:test_idx]
                y_train = target.iloc[train_idx:test_idx]
                X_test = features.iloc[test_idx:test_idx+1]
                y_test = target.iloc[test_idx:test_idx+1]
                
                if len(X_train) < 10 or len(X_test) == 0:
                    continue
                
                X_train_scaled = model.scaler.fit_transform(X_train)
                X_test_scaled = model.scaler.transform(X_test)
                
                model.train(X_train_scaled, y_train, use_grid_search=False)
                
                pred = model.predict(X_test_scaled)[0]
                actual = y_test.iloc[0]
                
                predictions.append(pred)
                actuals.append(actual)
            
            if predictions and actuals:
                accuracy = np.mean(np.array(predictions) == np.array(actuals))
                precision = np.sum((np.array(predictions) == 1) & (np.array(actuals) == 1)) / max(np.sum(np.array(predictions) == 1), 1)
                recall = np.sum((np.array(predictions) == 1) & (np.array(actuals) == 1)) / max(np.sum(np.array(actuals) == 1), 1)
                f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
                
                backtest_results[model_name] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1_score,
                    'num_predictions': len(predictions)
                }
        
        return backtest_results
    
    def compare_models(self) -> pd.DataFrame:
        """مقارنة أداء النماذج المختلفة"""
        evaluation = self.evaluate_models()
        
        comparison_data = []
        
        for model_name, results in evaluation.items():
            if 'accuracy' in results:
                comparison_data.append({
                    'Model': model_name,
                    'Accuracy': results['accuracy'],
                    'Precision': results.get('precision', results.get('accuracy')),
                    'Recall': results.get('recall', results.get('accuracy')),
                    'F1 Score': results.get('f1_score', results.get('accuracy')),
                    'Type': self.model_type
                })
            elif 'r2' in results:
                comparison_data.append({
                    'Model': model_name,
                    'R2 Score': results['r2'],
                    'RMSE': results['rmse'],
                    'MAE': results['mae'],
                    'Type': self.model_type
                })
        
        return pd.DataFrame(comparison_data)
    
    def save_training_results(self, filepath: str = 'training_results.json'):
        """حفظ نتائج التدريب"""
        backtest_results = self.backtest_models()
        self.training_history['backtest_results'] = backtest_results
        
        with open(filepath, 'w') as f:
            json.dump(self.training_history, f, default=str, indent=2)
        
        print(f"تم حفظ نتائج التدريب في {filepath}")
    
    def load_training_results(self, filepath: str = 'training_results.json'):
        """تحميل نتائج التدريب"""
        try:
            with open(filepath, 'r') as f:
                self.training_history = json.load(f)
            print(f"تم تحميل نتائج التدريب من {filepath}")
            return True
        except FileNotFoundError:
            print(f"لم يتم العثور على ملف {filepath}")
            return False
    
    def generate_training_report(self) -> str:
        """إنشاء تقرير التدريب"""
        report = f"""
        ========================================
        تقرير تدريب النماذج
        ========================================
        
        نوع النموذج: {self.model_type}
        تاريخ التدريب: {self.training_history.get('timestamp', 'غير معروف')}
        
        حجم البيانات: {self.training_history.get('data_shape', 'غير معروف')}
        
        نتائج التقييم:
        """
        
        for model_name, results in self.training_history.get('results', {}).items():
            report += f"""
            ----------------------------------------
            النموذج: {model_name}
            """
            
            if 'evaluation' in results:
                eval_results = results['evaluation']
                if 'accuracy' in eval_results:
                    report += f"""
                    الدقة: {eval_results['accuracy']:.4f}
                    """
                elif 'r2' in eval_results:
                    report += f"""
                    R² Score: {eval_results['r2']:.4f}
                    RMSE: {eval_results['rmse']:.4f}
                    MAE: {eval_results['mae']:.4f}
                    """
            
            if 'best_params' in results:
                report += f"""
                أفضل المعلمات: {results['best_params']}
                """
        
        backtest = self.training_history.get('backtest_results', {})
        if backtest:
            report += """
            ========================================
            نتائج Backtest
            ========================================
            """
            for model_name, results in backtest.items():
                report += f"""
                {model_name}:
                الدقة: {results['accuracy']:.4f}
                الدقة الإيجابية: {results['precision']:.4f}
                الحساسية: {results['recall']:.4f}
                F1 Score: {results['f1_score']:.4f}
                عدد التنبؤات: {results['num_predictions']}
                """
        
        return report
    
    def run_full_training(self) -> Dict:
        """تشغيل عملية التدريب الكاملة"""
        train_results = self.train_all_models()
        
        eval_results = self.evaluate_models()
        
        backtest_results = self.backtest_models()
        
        self.save_training_results()
        
        self.prediction_system.save_models()
        
        report = self.generate_training_report()
        
        return {
            'training_results': train_results,
            'evaluation_results': eval_results,
            'backtest_results': backtest_results,
            'report': report,
            'timestamp': datetime.now().isoformat()
        }
