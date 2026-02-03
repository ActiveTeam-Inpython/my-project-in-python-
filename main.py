#!/usr/bin/env python3
"""
الملف الرئيسي لتشغيل مدير كلمات المرور الآمن
"""
import sys
import os

# إضافة المسار الحالي إلى مسار البحث
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui import SecurePasswordManagerGUI


def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    print("🚀 تشغيل مدير كلمات المرور الآمن...")
    print("📋 الإصدار: 1.0")
    print("⚙️  Python: 3.13.7")
    print("🔒 التشفير: AES-256-GCM مع PBKDF2")
    print("-" * 50)

    try:
        # التحقق من المكتبات المطلوبة
        import cryptography
        import pyperclip

        # تشغيل الواجهة الرسومية
        app = SecurePasswordManagerGUI()
        app.run()

    except ImportError as e:
        print(f"❌ خطأ: المكتبة {e.name} غير مثبتة")
        print("📦 يرجى تثبيت المتطلبات باستخدام:")
        print("   pip install -r requirements.txt")
        input("اضغط Enter للخروج...")
        sys.exit(1)
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        input("اضغط Enter للخروج...")
        sys.exit(1)


if __name__ == "__main__":
    main()