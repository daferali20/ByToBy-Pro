# utils/cache.py
"""
نظام التخزين المؤقت المتقدم
Advanced Caching System
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable
from pathlib import Path
import pickle
import time
from functools import wraps

from .logger import get_logger

logger = get_logger("Cache")

class Cache:
    """
    نظام تخزين مؤقت متعدد المستويات:
    - الذاكرة (Memory) - أسرع
    - القرص (Disk) - أكبر مساحة
    - مع صلاحية محددة (TTL)
    """
    
    _instance = None
    
    def __new__(cls, cache_dir: str = ".cache", default_ttl: int = 300):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(Cache, cls).__new__(cls)
            cls._instance._initialize(cache_dir, default_ttl)
        return cls._instance
    
    def _initialize(self, cache_dir: str, default_ttl: int):
        """تهيئة نظام التخزين المؤقت"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl  # الثواني الافتراضية
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.max_memory_items = 1000  # الحد الأقصى للعناصر في الذاكرة
        
        logger.info(f"Cache initialized at {self.cache_dir}")
    
    def _get_cache_key(self, key: str) -> str:
        """إنشاء مفتاح موحد للتخزين"""
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def _get_file_path(self, key: str) -> Path:
        """الحصول على مسار ملف التخزين"""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.cache"
    
    def _is_expired(self, cache_data: Dict[str, Any]) -> bool:
        """التحقق من صلاحية البيانات"""
        if 'expires_at' not in cache_data:
            return True
        return datetime.now() > datetime.fromisoformat(cache_data['expires_at'])
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        تخزين بيانات في الذاكرة والقرص
        
        Args:
            key: المفتاح
            value: القيمة (أي نوع بيانات)
            ttl: مدة الصلاحية بالثواني (None = استخدام الافتراضي)
        
        Returns:
            bool: نجاح العملية
        """
        try:
            # حساب وقت الانتهاء
            ttl = ttl or self.default_ttl
            expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()
            
            # تجهيز البيانات
            cache_data = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now().isoformat(),
                'ttl': ttl
            }
            
            # 1. تخزين في الذاكرة
            if len(self.memory_cache) >= self.max_memory_items:
                # إزالة أقدم عنصر
                oldest_key = next(iter(self.memory_cache))
                del self.memory_cache[oldest_key]
            
            self.memory_cache[key] = cache_data
            
            # 2. تخزين على القرص
            file_path = self._get_file_path(key)
            with open(file_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.debug(f"Cache set: {key} (ttl={ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache for {key}: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        استرجاع بيانات من التخزين المؤقت
        
        Args:
            key: المفتاح
            default: القيمة الافتراضية في حالة عدم وجود البيانات
        
        Returns:
            القيمة المخزنة أو القيمة الافتراضية
        """
        try:
            # 1. البحث في الذاكرة أولاً
            if key in self.memory_cache:
                cache_data = self.memory_cache[key]
                if not self._is_expired(cache_data):
                    logger.debug(f"Cache hit (memory): {key}")
                    return cache_data['value']
                else:
                    # حذف من الذاكرة إذا انتهت الصلاحية
                    del self.memory_cache[key]
            
            # 2. البحث على القرص
            file_path = self._get_file_path(key)
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if not self._is_expired(cache_data):
                    # تخزين في الذاكرة للاستخدام السريع
                    self.memory_cache[key] = cache_data
                    logger.debug(f"Cache hit (disk): {key}")
                    return cache_data['value']
                else:
                    # حذف الملف إذا انتهت الصلاحية
                    file_path.unlink()
                    logger.debug(f"Cache expired: {key}")
            
            logger.debug(f"Cache miss: {key}")
            return default
            
        except Exception as e:
            logger.error(f"Error getting cache for {key}: {str(e)}")
            return default
    
    def delete(self, key: str) -> bool:
        """حذف بيانات من التخزين المؤقت"""
        try:
            # حذف من الذاكرة
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # حذف من القرص
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
            
            logger.debug(f"Cache deleted: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache {key}: {str(e)}")
            return False
    
    def clear(self, older_than_days: Optional[int] = None):
        """
        مسح التخزين المؤقت
        
        Args:
            older_than_days: حذف الملفات الأقدم من عدد معين من الأيام
        """
        try:
            if older_than_days:
                cutoff = datetime.now() - timedelta(days=older_than_days)
                for file_path in self.cache_dir.glob("*.cache"):
                    if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff:
                        file_path.unlink()
                        logger.debug(f"Deleted old cache: {file_path}")
            else:
                # حذف كل شيء
                self.memory_cache.clear()
                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink()
            
            logger.info(f"Cache cleared (older_than_days={older_than_days})")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    def stats(self) -> Dict[str, Any]:
        """إحصائيات التخزين المؤقت"""
        disk_files = list(self.cache_dir.glob("*.cache"))
        disk_size = sum(f.stat().st_size for f in disk_files)
        
        return {
            'memory_items': len(self.memory_cache),
            'disk_items': len(disk_files),
            'disk_size_mb': disk_size / (1024 * 1024),
            'default_ttl': self.default_ttl,
            'max_memory_items': self.max_memory_items
        }

# إنشاء نسخة واحدة من التخزين المؤقت
cache = Cache(default_ttl=300)

def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    ديكوراتور لتخزين نتائج الدوال مؤقتاً
    
    Args:
        ttl: مدة الصلاحية بالثواني
        key_prefix: بادئة للمفتاح
    
    مثال:
        @cached(ttl=60)
        def get_stock_price(symbol):
            return fetch_price(symbol)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # إنشاء مفتاح فريد بناءً على اسم الدالة والمعاملات
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = f"{key_prefix}_{'_'.join(key_parts)}"
            
            # محاولة استرجاع من التخزين المؤقت
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # تنفيذ الدالة وتخزين النتيجة
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
            
        return wrapper
    return decorator

# مثال للاستخدام
if __name__ == "__main__":
    # اختبار التخزين المؤقت
    
    @cached(ttl=10)
    def expensive_operation(x: int) -> int:
        print(f"تنفيذ العملية لـ {x}...")
        time.sleep(2)
        return x * x
    
    # أول استدعاء - سيتم التنفيذ
    result1 = expensive_operation(5)
    print(f"النتيجة 1: {result1}")
    
    # ثاني استدعاء - من التخزين المؤقت
    result2 = expensive_operation(5)
    print(f"النتيجة 2: {result2}")
    
    # إحصائيات
    print(f"الإحصائيات: {cache.stats()}")
