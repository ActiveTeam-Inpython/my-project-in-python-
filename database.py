"""
وحدة قاعدة البيانات باستخدام SQLite مع تشفير
"""
import sqlite3
import json
import base64
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional, Tuple


class PasswordDatabase:
    """قاعدة بيانات آمنة لكلمات المرور"""

    def __init__(self, db_path="passwords.db"):
        """تهيئة قاعدة البيانات"""
        self.db_path = db_path
        self.conn = None
        self.setup_database()

    def setup_database(self):
        """إنشاء الجداول المطلوبة"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # جدول المستخدم الرئيسي
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS master_user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول كلمات المرور المشفرة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                username TEXT,
                email TEXT,
                password_cipher TEXT NOT NULL,
                password_tag TEXT NOT NULL,
                iv TEXT NOT NULL,
                url TEXT,
                category TEXT,
                notes_cipher TEXT,
                notes_tag TEXT,
                notes_iv TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES master_user (id)
            )
        ''')

        # جدول لسجل العمليات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES master_user (id)
            )
        ''')

        # جدول للمحاولات الفاشلة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failed_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول للإعدادات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                clipboard_timeout INTEGER DEFAULT 30,
                auto_lock_timeout INTEGER DEFAULT 300,
                theme TEXT DEFAULT 'dark',
                language TEXT DEFAULT 'ar',
                FOREIGN KEY (user_id) REFERENCES master_user (id)
            )
        ''')

        self.conn.commit()

    def create_master_user(self, username, password_hash, salt):
        """إنشاء مستخدم رئيسي جديد"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO master_user (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, password_hash, salt)
            )

            # إنشاء إعدادات افتراضية للمستخدم
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO settings (user_id) VALUES (?)",
                (user_id,)
            )

            self.conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None

    def verify_master_user(self, username, password_hash, salt):
        """التحقق من بيانات المستخدم الرئيسي"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, password_hash, salt FROM master_user WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()

        if user:
            return user['id']
        return None

    def get_user_settings(self, user_id):
        """الحصول على إعدادات المستخدم"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM settings WHERE user_id = ?",
            (user_id,)
        )
        settings = cursor.fetchone()
        return dict(settings) if settings else None

    def update_user_settings(self, user_id, settings):
        """تحديث إعدادات المستخدم"""
        cursor = self.conn.cursor()

        # التحقق من وجود إعدادات
        cursor.execute("SELECT 1 FROM settings WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            # تحديث الإعدادات الموجودة
            cursor.execute('''
                UPDATE settings SET 
                clipboard_timeout = ?,
                auto_lock_timeout = ?,
                theme = ?,
                language = ?
                WHERE user_id = ?
            ''', (
                settings.get('clipboard_timeout', 30),
                settings.get('auto_lock_timeout', 300),
                settings.get('theme', 'dark'),
                settings.get('language', 'ar'),
                user_id
            ))
        else:
            # إنشاء إعدادات جديدة
            cursor.execute('''
                INSERT INTO settings (user_id, clipboard_timeout, auto_lock_timeout, theme, language)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                settings.get('clipboard_timeout', 30),
                settings.get('auto_lock_timeout', 300),
                settings.get('theme', 'dark'),
                settings.get('language', 'ar')
            ))

        self.conn.commit()

    def add_password_entry(self, user_id, entry_data, encrypted_password, notes_encrypted=None):
        """إضافة مدخل كلمة مرور جديد"""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO passwords (
                user_id, title, username, email, password_cipher, password_tag, iv,
                url, category, notes_cipher, notes_tag, notes_iv
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            entry_data.get('title'),
            entry_data.get('username'),
            entry_data.get('email'),
            base64.b64encode(encrypted_password['ciphertext']).decode('utf-8'),
            base64.b64encode(encrypted_password['tag']).decode('utf-8'),
            base64.b64encode(encrypted_password['iv']).decode('utf-8'),
            entry_data.get('url'),
            entry_data.get('category', 'عام'),
            base64.b64encode(notes_encrypted['ciphertext']).decode('utf-8') if notes_encrypted else None,
            base64.b64encode(notes_encrypted['tag']).decode('utf-8') if notes_encrypted else None,
            base64.b64encode(notes_encrypted['iv']).decode('utf-8') if notes_encrypted else None
        ))

        entry_id = cursor.lastrowid

        # تسجيل العملية في سجل التدقيق
        self.add_audit_log(user_id, "ADD_PASSWORD", f"Added entry: {entry_data.get('title')}")

        self.conn.commit()
        return entry_id

    def get_password_entry(self, user_id, entry_id):
        """الحصول على مدخل كلمة مرور"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM passwords 
            WHERE id = ? AND user_id = ?
        ''', (entry_id, user_id))

        entry = cursor.fetchone()
        if entry:
            # تحديث وقت آخر وصول
            cursor.execute('''
                UPDATE passwords SET last_accessed = CURRENT_TIMESTAMP 
                WHERE id = ? AND user_id = ?
            ''', (entry_id, user_id))
            self.conn.commit()

            return dict(entry)
        return None

    def get_all_entries(self, user_id, category=None):
        """الحصول على جميع المدخلات"""
        cursor = self.conn.cursor()

        if category:
            cursor.execute('''
                SELECT id, title, username, email, url, category, created_at, updated_at
                FROM passwords 
                WHERE user_id = ? AND category = ?
                ORDER BY title
            ''', (user_id, category))
        else:
            cursor.execute('''
                SELECT id, title, username, email, url, category, created_at, updated_at
                FROM passwords 
                WHERE user_id = ?
                ORDER BY title
            ''', (user_id,))

        entries = cursor.fetchall()
        return [dict(entry) for entry in entries]

    def update_password_entry(self, user_id, entry_id, entry_data, encrypted_password=None, notes_encrypted=None):
        """تحديث مدخل كلمة مرور"""
        cursor = self.conn.cursor()

        # بناء استعلام التحديث الديناميكي
        update_fields = []
        params = []

        if 'title' in entry_data:
            update_fields.append("title = ?")
            params.append(entry_data['title'])

        if 'username' in entry_data:
            update_fields.append("username = ?")
            params.append(entry_data['username'])

        if 'email' in entry_data:
            update_fields.append("email = ?")
            params.append(entry_data['email'])

        if 'url' in entry_data:
            update_fields.append("url = ?")
            params.append(entry_data['url'])

        if 'category' in entry_data:
            update_fields.append("category = ?")
            params.append(entry_data['category'])

        if encrypted_password:
            update_fields.append("password_cipher = ?")
            update_fields.append("password_tag = ?")
            update_fields.append("iv = ?")
            params.extend([
                base64.b64encode(encrypted_password['ciphertext']).decode('utf-8'),
                base64.b64encode(encrypted_password['tag']).decode('utf-8'),
                base64.b64encode(encrypted_password['iv']).decode('utf-8')
            ])

        if notes_encrypted:
            update_fields.append("notes_cipher = ?")
            update_fields.append("notes_tag = ?")
            update_fields.append("notes_iv = ?")
            params.extend([
                base64.b64encode(notes_encrypted['ciphertext']).decode('utf-8'),
                base64.b64encode(notes_encrypted['tag']).decode('utf-8'),
                base64.b64encode(notes_encrypted['iv']).decode('utf-8')
            ])

        # إضافة وقت التحديث
        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        if not update_fields:
            return False

        # بناء الاستعلام النهائي
        query = f'''
            UPDATE passwords SET 
            {', '.join(update_fields)}
            WHERE id = ? AND user_id = ?
        '''

        params.extend([entry_id, user_id])

        cursor.execute(query, params)
        affected = cursor.rowcount

        if affected > 0:
            # تسجيل العملية في سجل التدقيق
            self.add_audit_log(user_id, "UPDATE_PASSWORD", f"Updated entry ID: {entry_id}")

        self.conn.commit()
        return affected > 0

    def delete_password_entry(self, user_id, entry_id):
        """حذف مدخل كلمة مرور"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM passwords 
            WHERE id = ? AND user_id = ?
        ''', (entry_id, user_id))

        affected = cursor.rowcount

        if affected > 0:
            # تسجيل العملية في سجل التدقيق
            self.add_audit_log(user_id, "DELETE_PASSWORD", f"Deleted entry ID: {entry_id}")

        self.conn.commit()
        return affected > 0

    def add_audit_log(self, user_id, action, details=None, ip_address=None):
        """إضافة سجل تدقيق"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO audit_log (user_id, action, details, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, details, ip_address))
        self.conn.commit()

    def get_audit_logs(self, user_id, limit=50):
        """الحصول على سجلات التدقيق"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM audit_log 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))

        logs = cursor.fetchall()
        return [dict(log) for log in logs]

    def clear_old_failed_attempts(self, hours=24):
        """مسح محاولات الدخول الفاشلة القديمة"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM failed_attempts 
            WHERE timestamp < datetime('now', ?)
        ''', (f'-{hours} hours',))
        self.conn.commit()

    def close(self):
        """إغلاق اتصال قاعدة البيانات"""
        if self.conn:
            self.conn.close()