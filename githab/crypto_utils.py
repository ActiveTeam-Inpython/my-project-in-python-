"""
وحدات التشفير الآمنة للتعامل مع كلمات المرور
"""
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC # type: ignore
from cryptography.hazmat.primitives import hashes # type: ignore
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes # type: ignore
from cryptography.hazmat.backends import default_backend # type: ignore
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt # type: ignore
import hashlib


class CryptoManager:
    """مدير التشفير المركزي"""

    # إعدادات التشفير
    SALT_SIZE = 32
    IV_SIZE = 16
    KEY_SIZE = 32  # 256-bit for AES
    PBKDF2_ITERATIONS = 1000000  # عدد التكرارات عالي للأمان

    @staticmethod
    def generate_salt(size=SALT_SIZE):
        """إنشاء رمز ملح عشوائي"""
        return os.urandom(size)

    @staticmethod
    def generate_iv(size=IV_SIZE):
        """إنشاء متجه تهيئة عشوائي"""
        return os.urandom(size)

    @staticmethod
    def derive_key(password, salt, iterations=PBKDF2_ITERATIONS):
        """اشتقاق مفتاح من كلمة المرور باستخدام PBKDF2"""
        password_bytes = password.encode('utf-8')

        # استخدام Scrypt بدلاً من PBKDF2HMAC للأفضلية الأمنية
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2 ** 14,  # عامل التكلفة
            r=8,
            p=1,
            backend=default_backend()
        )

        key = kdf.derive(password_bytes)
        return key

    @staticmethod
    def encrypt_data(plaintext, key, iv=None):
        """تشفير البيانات باستخدام AES-GCM"""
        if iv is None:
            iv = CryptoManager.generate_iv()

        # تحويل النص إلى بايتات
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')

        # استخدام AES-GCM للتحقق من النزاهة والأصالة
        encryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        ).encryptor()

        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        # إرجاع النص المشفر ووسم GCM و IV
        return {
            'ciphertext': ciphertext,
            'tag': encryptor.tag,
            'iv': iv
        }

    @staticmethod
    def decrypt_data(encrypted_data, key):
        """فك تشفير البيانات باستخدام AES-GCM"""
        ciphertext = encrypted_data['ciphertext']
        tag = encrypted_data['tag']
        iv = encrypted_data['iv']

        # استخدام AES-GCM لفك التشفير مع التحقق
        decryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        ).decryptor()

        decrypted = decryptor.update(ciphertext) + decryptor.finalize()

        try:
            return decrypted.decode('utf-8')
        except UnicodeDecodeError:
            return decrypted

    @staticmethod
    def hash_password(password, salt=None):
        """تجزئة كلمة المرور باستخدام خوارزمية آمنة"""
        if salt is None:
            salt = CryptoManager.generate_salt()

        # استخدام PBKDF2 مع SHA-512
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=64,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        password_bytes = password.encode('utf-8')
        hashed = kdf.derive(password_bytes)

        return {
            'hash': base64.b64encode(hashed).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8')
        }

    @staticmethod
    def verify_password(password, hashed_password, salt):
        """التحقق من صحة كلمة المرور"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=64,
            salt=base64.b64decode(salt),
            iterations=100000,
            backend=default_backend()
        )

        try:
            kdf.verify(password.encode('utf-8'), base64.b64decode(hashed_password))
            return True
        except Exception:
            return False

    @staticmethod
    def generate_secure_password(length=16):
        """إنشاء كلمة مرور عشوائية قوية"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_-+=<>?"
        password = ''.join(chars[os.urandom(1)[0] % len(chars)] for _ in range(length))
        return password