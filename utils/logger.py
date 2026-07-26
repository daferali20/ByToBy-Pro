# utils/logger.py
"""
نظام التسجيل الاحترافي للمشروع
Professional Logging System
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

# إعدادات الألوان للطباعة في الكونسول (اختياري)
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

class ColoredFormatter(logging.Formatter):
    """تنسيق السجلات بالألوان"""
    
    COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.MAGENTA,
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Colors.WHITE)
        record.levelname = f"{log_color}{record.levelname}{Colors.RESET}"
        record.name = f"{Colors.BLUE}{record.name}{Colors.RESET}"
        
        # إضافة وقت محلي
        record.asctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return super().format(record)

class Logger:
    """
    نظام تسجيل متقدم مع:
    - كتابة في ملف مع تدوير تلقائي
    - طباعة في الكونسول بألوان
    - مستويات متعددة (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - تنسيق احترافي
    """
    
    _instances = {}
    
    def __new__(cls, name: str = "ByToBy", log_dir: str = "logs", 
                level: str = "INFO", max_bytes: int = 10_485_760, 
                backup_count: int = 5):
        """
        Singleton pattern لتجنب إنشاء عدة loggers لنفس الاسم
        
        Args:
            name: اسم الـ logger
            log_dir: مجلد حفظ الملفات
            level: مستوى التسجيل
            max_bytes: الحد الأقصى لحجم الملف (10 ميجابايت)
            backup_count: عدد نسخ الاحتياط
        """
        if name not in cls._instances:
            cls._instances[name] = super(Logger, cls).__new__(cls)
            cls._instances[name]._initialize(name, log_dir, level, max_bytes, backup_count)
        return cls._instances[name]
    
    def _initialize(self, name: str, log_dir: str, level: str, 
                    max_bytes: int, backup_count: int):
        """تهيئة الـ logger"""
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.logger.handlers.clear()  # مسح المعالجات السابقة
        
        # إنشاء مجلد السجلات إذا لم يكن موجوداً
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # تنسيق السجلات
        formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)-10s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. معالج الملف - تدوير تلقائي
        file_handler = RotatingFileHandler(
            log_path / f"{name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 2. معالج ملف الأخطاء فقط
        error_handler = RotatingFileHandler(
            log_path / f"{name}_errors.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # 3. معالج الكونسول
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """إرجاع كائن logger"""
        return self.logger
    
    # طرق مختصرة للاستخدام السهل
    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """تسجيل استثناء مع تفاصيل كاملة"""
        self.logger.exception(message, *args, **kwargs)

# إنشاء logger افتراضي للمشروع
default_logger = Logger("ByToBy").get_logger()

# دوال مساعدة للاستخدام السريع
def get_logger(name: str = "ByToBy") -> logging.Logger:
    """الحصول على logger باسم محدد"""
    return Logger(name).get_logger()

def log_function_call(func):
    """ديكوراتور لتسجيل استدعاء الدوال"""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

# مثال للاستخدام
if __name__ == "__main__":
    # اختبار الـ logger
    logger = get_logger("Test")
    logger.debug("هذا رسالة تصحيح")
    logger.info("هذا رسالة معلومات")
    logger.warning("هذا رسالة تحذير")
    logger.error("هذا رسالة خطأ")
    
    @log_function_call
    def test_function(x, y):
        return x / y
    
    try:
        test_function(10, 0)
    except:
        pass
