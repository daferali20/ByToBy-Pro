"""
مساعد تثبيت المكتبات المطلوبة
"""

import subprocess
import sys
import platform

def check_python_version():
    """التحقق من إصدار Python"""
    version = sys.version_info
    print(f"إصدار Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 11:
        print("⚠️ تحذير: TensorFlow قد لا يعمل مع Python 3.11+")
        print("   يوصى باستخدام Python 3.8-3.10")
    return version

def install_packages():
    """تثبيت الحزم المطلوبة"""
    print("بدء تثبيت الحزم...")
    print("=" * 50)
    
    # الحزم الأساسية (دائماً تعمل)
    basic_packages = [
        "pandas>=1.3.0",
        "numpy>=1.21.0,<1.24.0",
        "scikit-learn>=1.0.0",
        "joblib>=1.1.0"
    ]
    
    # الحزم الاختيارية
    optional_packages = [
        "xgboost>=1.5.0",
        "lightgbm>=3.3.0"
    ]
    
    # تثبيت الحزم الأساسية
    for package in basic_packages:
        print(f"\nتثبيت {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ تم تثبيت {package}")
        except Exception as e:
            print(f"❌ خطأ في تثبيت {package}: {e}")
    
    # تثبيت الحزم الاختيارية
    for package in optional_packages:
        print(f"\nتثبيت {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ تم تثبيت {package}")
        except Exception as e:
            print(f"❌ خطأ في تثبيت {package}: {e}")
    
    # محاولة تثبيت TensorFlow
    print("\nمحاولة تثبيت TensorFlow...")
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor <= 10:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "tensorflow==2.10.0"])
            print("✅ تم تثبيت TensorFlow")
        except Exception as e:
            print(f"❌ خطأ في تثبيت TensorFlow: {e}")
            print("   يمكنك استخدام النظام بدون TensorFlow")
    else:
        print("⚠️ TensorFlow غير متوافق مع إصدار Python الحالي")
        print("   يمكنك استخدام النظام بدون TensorFlow")
    
    print("\n" + "=" * 50)
    print("اكتملت عملية التثبيت!")

def create_requirements_file():
    """إنشاء ملف requirements.txt"""
    requirements = """
pandas>=1.3.0
numpy>=1.21.0,<1.24.0
scikit-learn>=1.0.0
xgboost>=1.5.0
lightgbm>=3.3.0
joblib>=1.1.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements.strip())
    
    print("تم إنشاء ملف requirements.txt")

if __name__ == "__main__":
    print("مساعد تثبيت نظام التداول")
    print("=" * 50)
    
    # التحقق من إصدار Python
    check_python_version()
    
    # إنشاء ملف المتطلبات
    create_requirements_file()
    
    # تثبيت الحزم
    install_packages()
    
    print("\n✅ اكتمل التثبيت!")
    print("\nلتشغيل النظام:")
    print("  python test.py")
