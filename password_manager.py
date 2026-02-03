"""
النواة الرئيسية لمدير كلمات المرور
"""
import os
import time
import threading
import pyperclip
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import base64

from crypto_utils import CryptoManager
from database import PasswordDatabase

class PasswordManager:
    """الفئة الرئيسية لإدارة كلمات المرور"""

    def __init__(self, db_path="passwords.db"):
        """تهيئة مدير كلمات المرور"""
        self.db = PasswordDatabase(db_path)
        self.crypto = CryptoManager()
        self.current_user = None
        self.current_user_id = None
        self.master_key = None
        self.session_start = None
        self.lock_timer = None
        self.auto_lock_timeout = 300  # 5 دقائق افتراضياً

        # خيط لمسح الحافظة تلقائياً
        self.clipboard_clear_thread = None
        self.clipboard_timeout = 30  # 30 ثانية افتراضياً

    def register_user(self, username: str, master_password: str) -> Tuple[bool, str]:
        """تسجيل مستخدم جديد"""
        try:
            # التحقق من وجود المستخدم
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id FROM master_user WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "اسم المستخدم موجود بالفعل"

            # تجزئة كلمة المرور الرئيسية
            hashed_data = self.crypto.hash_password(master_password)

            # إنشاء المستخدم
            user_id = self.db.create_master_user(username, hashed_data['hash'], hashed_data['salt'])

            if user_id:
                return True, "تم التسجيل بنجاح"
            else:
                return False, "فشل في إنشاء المستخدم"

        except Exception as e:
            return False, f"خطأ في التسجيل: {str(e)}"

    def login(self, username: str, master_password: str) -> Tuple[bool, str]:
        """تسجيل الدخول"""
        try:
            # التحقق من المحاولات الفاشلة
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as attempts 
                FROM failed_attempts 
                WHERE username = ? AND timestamp > datetime('now', '-1 hour')
            ''', (username,))

            attempts = cursor.fetchone()['attempts']
            if attempts >= 5:
                return False, "تم تجاوز عدد المحاولات المسموح بها. حاول لاحقاً"

            # البحث عن المستخدم
            cursor.execute('''
                SELECT id, password_hash, salt FROM master_user WHERE username = ?
            ''', (username,))

            user = cursor.fetchone()
            if not user:
                # تسجيل محاولة فاشلة
                cursor.execute(
                    "INSERT INTO failed_attempts (username) VALUES (?)",
                    (username,)
                )
                self.db.conn.commit()
                return False, "اسم المستخدم أو كلمة المرور غير صحيحة"

            # التحقق من كلمة المرور
            is_valid = self.crypto.verify_password(
                master_password,
                user['password_hash'],
                user['salt']
            )

            if is_valid:
                # تهيئة الجلسة
                self.current_user = username
                self.current_user_id = user['id']
                self.session_start = datetime.now()

                # اشتقاق المفتاح الرئيسي
                salt_bytes = base64.b64decode(user['salt'])
                self.master_key = self.crypto.derive_key(master_password, salt_bytes)

                # الحصول على الإعدادات
                settings = self.db.get_user_settings(user['id'])
                if settings:
                    self.auto_lock_timeout = settings.get('auto_lock_timeout', 300)
                    self.clipboard_timeout = settings.get('clipboard_timeout', 30)

                # بدء مؤتمر القفل التلقائي
                self.start_auto_lock_timer()

                # مسح المحاولات الفاشلة للمستخدم
                cursor.execute("DELETE FROM failed_attempts WHERE username = ?", (username,))
                self.db.conn.commit()

                # تسجيل الدخول الناجح
                self.db.add_audit_log(user['id'], "LOGIN", "تم تسجيل الدخول بنجاح")

                return True, "تم تسجيل الدخول بنجاح"
            else:
                # تسجيل محاولة فاشلة
                cursor.execute(
                    "INSERT INTO failed_attempts (username) VALUES (?)",
                    (username,)
                )
                self.db.conn.commit()
                return False, "اسم المستخدم أو كلمة المرور غير صحيحة"

        except Exception as e:
            return False, f"خطأ في تسجيل الدخول: {str(e)}"

    def logout(self):
        """تسجيل الخروج"""
        if self.current_user_id:
            self.db.add_audit_log(self.current_user_id, "LOGOUT", "تم تسجيل الخروج")

        self.clear_clipboard()
        self.stop_auto_lock_timer()

        self.current_user = None
        self.current_user_id = None
        self.master_key = None
        self.session_start = None

    def start_auto_lock_timer(self):
        """بدء مؤقت القفل التلقائي"""
        self.stop_auto_lock_timer()

        def lock_session():
            time.sleep(self.auto_lock_timeout)
            if self.current_user:
                self.logout()

        self.lock_timer = threading.Thread(target=lock_session, daemon=True)
        self.lock_timer.start()

    def stop_auto_lock_timer(self):
        """إيقاف مؤقت القفل التلقائي"""
        if self.lock_timer and self.lock_timer.is_alive():
            # لا يمكن إيقاف الخيط مباشرة، سنعيد تعيين المرجع
            self.lock_timer = None

    def reset_auto_lock_timer(self):
        """إعادة تعيين مؤقت القفل التلقائي"""
        self.stop_auto_lock_timer()
        self.start_auto_lock_timer()

    def add_password(self, entry_data: Dict) -> Tuple[bool, str]:
        """إضافة كلمة مرور جديدة"""
        if not self.current_user_id or not self.master_key:
            return False, "يجب تسجيل الدخول أولاً"

        try:
            # التحقق من البيانات المطلوبة
            if 'title' not in entry_data or not entry_data['title']:
                return False, "العنوان مطلوب"

            if 'password' not in entry_data or not entry_data['password']:
                return False, "كلمة المرور مطلوبة"

            # تشفير كلمة المرور
            encrypted_password = self.crypto.encrypt_data(
                entry_data['password'],
                self.master_key
            )

            # تشفير الملاحظات إذا وجدت
            notes_encrypted = None
            if 'notes' in entry_data and entry_data['notes']:
                notes_encrypted = self.crypto.encrypt_data(
                    entry_data['notes'],
                    self.master_key
                )

            # إضافة المدخل إلى قاعدة البيانات
            entry_id = self.db.add_password_entry(
                self.current_user_id,
                entry_data,
                encrypted_password,
                notes_encrypted
            )

            if entry_id:
                return True, f"تمت الإضافة بنجاح (ID: {entry_id})"
            else:
                return False, "فشل في إضافة المدخل"

        except Exception as e:
            return False, f"خطأ في الإضافة: {str(e)}"

    def get_password(self, entry_id: int) -> Tuple[bool, Dict, str]:
        """الحصول على كلمة مرور"""
        if not self.current_user_id or not self.master_key:
            return False, {}, "يجب تسجيل الدخول أولاً"

        try:
            # الحصول على المدخل من قاعدة البيانات
            entry = self.db.get_password_entry(self.current_user_id, entry_id)

            if not entry:
                return False, {}, "المدخل غير موجود"

            # فك تشفير كلمة المرور
            password_encrypted = {
                'ciphertext': base64.b64decode(entry['password_cipher']),
                'tag': base64.b64decode(entry['password_tag']),
                'iv': base64.b64decode(entry['iv'])
            }

            decrypted_password = self.crypto.decrypt_data(password_encrypted, self.master_key)

            # فك تشفير الملاحظات إذا وجدت
            decrypted_notes = None
            if entry['notes_cipher'] and entry['notes_tag'] and entry['notes_iv']:
                notes_encrypted = {
                    'ciphertext': base64.b64decode(entry['notes_cipher']),
                    'tag': base64.b64decode(entry['notes_tag']),
                    'iv': base64.b64decode(entry['notes_iv'])
                }
                decrypted_notes = self.crypto.decrypt_data(notes_encrypted, self.master_key)

            # بناء بيانات الإرجاع
            entry_data = {
                'id': entry['id'],
                'title': entry['title'],
                'username': entry['username'],
                'email': entry['email'],
                'password': decrypted_password,
                'url': entry['url'],
                'category': entry['category'],
                'notes': decrypted_notes,
                'created_at': entry['created_at'],
                'updated_at': entry['updated_at']
            }

            return True, entry_data, "تم الاسترجاع بنجاح"

        except Exception as e:
            return False, {}, f"خطأ في الاسترجاع: {str(e)}"

    def update_password(self, entry_id: int, entry_data: Dict) -> Tuple[bool, str]:
        """تحديث كلمة مرور"""
        if not self.current_user_id or not self.master_key:
            return False, "يجب تسجيل الدخول أولاً"

        try:
            # إعداد بيانات التشفير
            encrypted_password = None
            if 'password' in entry_data and entry_data['password']:
                encrypted_password = self.crypto.encrypt_data(
                    entry_data['password'],
                    self.master_key
                )
                # إزالة كلمة المرور من البيانات المرسلة للقاعدة
                entry_data.pop('password')

            notes_encrypted = None
            if 'notes' in entry_data and entry_data['notes'] is not None:
                if entry_data['notes']:  # إذا كانت الملاحظات غير فارغة
                    notes_encrypted = self.crypto.encrypt_data(
                        entry_data['notes'],
                        self.master_key
                    )
                # إزالة الملاحظات من البيانات المرسلة للقاعدة
                entry_data.pop('notes')

            # تحديث المدخل
            success = self.db.update_password_entry(
                self.current_user_id,
                entry_id,
                entry_data,
                encrypted_password,
                notes_encrypted
            )

            if success:
                return True, "تم التحديث بنجاح"
            else:
                return False, "فشل في التحديث أو المدخل غير موجود"

        except Exception as e:
            return False, f"خطأ في التحديث: {str(e)}"

    def delete_password(self, entry_id: int) -> Tuple[bool, str]:
        """حذف كلمة مرور"""
        if not self.current_user_id:
            return False, "يجب تسجيل الدخول أولاً"

        try:
            success = self.db.delete_password_entry(self.current_user_id, entry_id)

            if success:
                return True, "تم الحذف بنجاح"
            else:
                return False, "فشل في الحذف أو المدخل غير موجود"

        except Exception as e:
            return False, f"خطأ في الحذف: {str(e)}"

    def get_all_passwords(self, category: str = None) -> List[Dict]:
        """الحصول على جميع كلمات المرور"""
        if not self.current_user_id:
            return []

        return self.db.get_all_entries(self.current_user_id, category)

    def get_categories(self) -> List[str]:
        """الحصول على التصنيفات المتاحة"""
        if not self.current_user_id:
            return []

        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT DISTINCT category FROM passwords 
            WHERE user_id = ? ORDER BY category
        ''', (self.current_user_id,))

        categories = [row['category'] for row in cursor.fetchall()]
        return categories

    def copy_to_clipboard(self, text: str) -> Tuple[bool, str]:
        """نسخ النص إلى الحافظة مع المسح التلقائي"""
        try:
            pyperclip.copy(text)

            # بدء خيط مسح الحافظة
            def clear_clipboard_after_timeout():
                time.sleep(self.clipboard_timeout)
                current_clipboard = pyperclip.paste()
                if current_clipboard == text:
                    pyperclip.copy('')

            self.clipboard_clear_thread = threading.Thread(
                target=clear_clipboard_after_timeout,
                daemon=True
            )
            self.clipboard_clear_thread.start()

            # تسجيل العملية
            if self.current_user_id:
                self.db.add_audit_log(
                    self.current_user_id,
                    "COPY_TO_CLIPBOARD",
                    f"Copied text (will clear in {self.clipboard_timeout}s)"
                )

            return True, f"تم النسخ إلى الحافظة (سيتم المسح بعد {self.clipboard_timeout} ثانية)"

        except Exception as e:
            return False, f"خطأ في النسخ: {str(e)}"

    def clear_clipboard(self):
        """مسح الحافظة"""
        try:
            pyperclip.copy('')
        except:
            pass

    def generate_secure_password(self, length: int = 16) -> str:
        """إنشاء كلمة مرور آمنة"""
        return self.crypto.generate_secure_password(length)

    def export_passwords(self, file_path: str, password: str) -> Tuple[bool, str]:
        """تصدير كلمات المرور"""
        if not self.current_user_id or not self.master_key:
            return False, "يجب تسجيل الدخول أولاً"

        try:
            # الحصول على جميع المدخلات
            entries = self.get_all_passwords()
            export_data = []

            for entry_summary in entries:
                success, entry_data, _ = self.get_password(entry_summary['id'])
                if success:
                    export_data.append(entry_data)

            # تشفير بيانات التصدير
            export_json = json.dumps(export_data, ensure_ascii=False, indent=2)

            # إنشاء مفتاح تصدير من كلمة المرور المقدمة
            export_salt = self.crypto.generate_salt()
            export_key = self.crypto.derive_key(password, export_salt)

            # تشفير البيانات
            encrypted_export = self.crypto.encrypt_data(export_json, export_key)

            # حفظ البيانات المشفرة
            export_package = {
                'version': '1.0',
                'salt': base64.b64encode(export_salt).decode('utf-8'),
                'ciphertext': base64.b64encode(encrypted_export['ciphertext']).decode('utf-8'),
                'tag': base64.b64encode(encrypted_export['tag']).decode('utf-8'),
                'iv': base64.b64encode(encrypted_export['iv']).decode('utf-8'),
                'export_date': datetime.now().isoformat(),
                'entries_count': len(export_data)
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_package, f, ensure_ascii=False, indent=2)

            # تسجيل العملية
            self.db.add_audit_log(
                self.current_user_id,
                "EXPORT",
                f"Exported {len(export_data)} entries to {file_path}"
            )

            return True, f"تم التصدير بنجاح ({len(export_data)} مدخل)"

        except Exception as e:
            return False, f"خطأ في التصدير: {str(e)}"

    def import_passwords(self, file_path: str, password: str) -> Tuple[bool, str]:
        """استيراد كلمات المرور"""
        if not self.current_user_id or not self.master_key:
            return False, "يجب تسجيل الدخول أولاً"

        try:
            # قراءة ملف التصدير
            with open(file_path, 'r', encoding='utf-8') as f:
                import_package = json.load(f)

            # التحقق من الإصدار
            if import_package.get('version') != '1.0':
                return False, "إصدار ملف غير مدعوم"

            # فك تشفير البيانات
            export_salt = base64.b64decode(import_package['salt'])
            export_key = self.crypto.derive_key(password, export_salt)

            encrypted_data = {
                'ciphertext': base64.b64decode(import_package['ciphertext']),
                'tag': base64.b64decode(import_package['tag']),
                'iv': base64.b64decode(import_package['iv'])
            }

            decrypted_json = self.crypto.decrypt_data(encrypted_data, export_key)
            import_data = json.loads(decrypted_json)

            # استيراد المدخلات
            imported_count = 0
            for entry_data in import_data:
                # إضافة المدخل
                success, message = self.add_password(entry_data)
                if success:
                    imported_count += 1

            # تسجيل العملية
            self.db.add_audit_log(
                self.current_user_id,
                "IMPORT",
                f"Imported {imported_count} entries from {file_path}"
            )

            return True, f"تم الاستيراد بنجاح ({imported_count} مدخل)"

        except Exception as e:
            return False, f"خطأ في الاستيراد: {str(e)}"

    def update_settings(self, settings: Dict) -> Tuple[bool, str]:
        """تحديث إعدادات المستخدم"""
        if not self.current_user_id:
            return False, "يجب تسجيل الدخول أولاً"

        try:
            self.db.update_user_settings(self.current_user_id, settings)

            # تحديث الإعدادات المحلية
            if 'clipboard_timeout' in settings:
                self.clipboard_timeout = settings['clipboard_timeout']

            if 'auto_lock_timeout' in settings:
                self.auto_lock_timeout = settings['auto_lock_timeout']
                self.reset_auto_lock_timer()

            return True, "تم تحديث الإعدادات بنجاح"

        except Exception as e:
            return False, f"خطأ في تحديث الإعدادات: {str(e)}"

    def get_audit_logs(self, limit: int = 50) -> List[Dict]:
        """الحصول على سجلات التدقيق"""
        if not self.current_user_id:
            return []

        return self.db.get_audit_logs(self.current_user_id, limit)

    def change_master_password(self, current_password: str, new_password: str) -> Tuple[bool, str]:
        """تغيير كلمة المرور الرئيسية"""
        if not self.current_user_id or not self.master_key:
            return False, "يجب تسجيل الدخول أولاً"

        try:
            # التحقق من كلمة المرور الحالية
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT password_hash, salt FROM master_user WHERE id = ?
            ''', (self.current_user_id,))

            user = cursor.fetchone()
            if not user:
                return False, "المستخدم غير موجود"

            is_valid = self.crypto.verify_password(
                current_password,
                user['password_hash'],
                user['salt']
            )

            if not is_valid:
                return False, "كلمة المرور الحالية غير صحيحة"

            # تجزئة كلمة المرور الجديدة
            new_hashed_data = self.crypto.hash_password(new_password)

            # تحديث كلمة المرور في قاعدة البيانات
            cursor.execute('''
                UPDATE master_user 
                SET password_hash = ?, salt = ? 
                WHERE id = ?
            ''', (
                new_hashed_data['hash'],
                new_hashed_data['salt'],
                self.current_user_id
            ))

            # إعادة تشفير جميع كلمات المرور بالمفتاح الجديد
            # (في تطبيق حقيقي، قد تحتاج إلى إعادة تشفير جميع البيانات)

            self.db.conn.commit()

            # تسجيل العملية
            self.db.add_audit_log(
                self.current_user_id,
                "CHANGE_MASTER_PASSWORD",
                "تم تغيير كلمة المرور الرئيسية"
            )

            return True, "تم تغيير كلمة المرور بنجاح"

        except Exception as e:
            return False, f"خطأ في تغيير كلمة المرور: {str(e)}"

    def close(self):
        """إغلاق مدير كلمات المرور"""
        self.logout()
        self.db.close()