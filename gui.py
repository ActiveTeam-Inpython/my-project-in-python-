"""
الواجهة الرسومية الاحترافية لمدير كلمات المرور
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
from datetime import datetime
from password_manager import PasswordManager
from PIL import Image, ImageTk
import os
import pyperclip


class SecurePasswordManagerGUI:
    """الواجهة الرسومية لمدير كلمات المرور"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("مدير كلمات المرور الآمن")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')

        # تهيئة مدير كلمات المرور
        self.pm = PasswordManager()
        self.current_user = None

        # متغيرات الواجهة
        self.theme = "dark"
        self.language = "ar"

        # إنشاء واجهة المستخدم
        self.setup_ui()

        # تعيين أيقونة البرنامج (اختياري)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        # حماية النافذة
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # بدء تحديث مؤشر القفل التلقائي
        self.update_lock_timer()

    def setup_ui(self):
        """إنشاء واجهة المستخدم"""
        # إنشاء القوائم
        self.create_menus()

        # إطار الصفحات الرئيسية
        self.main_frame = tk.Frame(self.root, bg='#1e1e1e')
        self.main_frame.pack(fill='both', expand=True)

        # صفوف الصفحات
        self.pages = {}
        self.create_login_page()
        self.create_main_page()
        self.create_settings_page()

        # عرض صفحة تسجيل الدخول أولاً
        self.show_page("login")

    def create_menus(self):
        """إنشاء قوائم التنقل"""
        menubar = tk.Menu(self.root, bg='#2d2d2d', fg='white')
        self.root.config(menu=menubar)

        # ملف
        file_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='white')
        menubar.add_cascade(label="ملف", menu=file_menu)
        file_menu.add_command(label="تصدير كلمات المرور", command=self.export_passwords)
        file_menu.add_command(label="استيراد كلمات المرور", command=self.import_passwords)
        file_menu.add_separator()
        file_menu.add_command(label="تسجيل الخروج", command=self.logout)
        file_menu.add_command(label="خروج", command=self.on_closing)

        # تحرير
        edit_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='white')
        menubar.add_cascade(label="تحرير", menu=edit_menu)
        edit_menu.add_command(label="إضافة كلمة مرور جديدة", command=lambda: self.show_add_password_dialog())
        edit_menu.add_command(label="تغيير كلمة المرور الرئيسية", command=self.change_master_password_dialog)

        # عرض
        view_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='white')
        menubar.add_cascade(label="عرض", menu=view_menu)
        view_menu.add_command(label="تغيير السمة", command=self.toggle_theme)
        view_menu.add_command(label="سجلات التدقيق", command=self.show_audit_logs)

        # مساعدة
        help_menu = tk.Menu(menubar, tearoff=0, bg='#2d2d2d', fg='white')
        menubar.add_cascade(label="مساعدة", menu=help_menu)
        help_menu.add_command(label="عن البرنامج", command=self.show_about)
        help_menu.add_command(label="دليل الاستخدام", command=self.show_help)

    def create_login_page(self):
        """إنشاء صفحة تسجيل الدخول والتسجيل"""
        page = tk.Frame(self.main_frame, bg='#1e1e1e')
        self.pages["login"] = page

        # العنوان
        title_label = tk.Label(
            page,
            text="🛡️ مدير كلمات المرور الآمن",
            font=("Arial", 28, "bold"),
            bg='#1e1e1e',
            fg='#4CAF50'
        )
        title_label.pack(pady=50)

        subtitle_label = tk.Label(
            page,
            text="تخزين آمن ومشفر لكلمات المرور",
            font=("Arial", 14),
            bg='#1e1e1e',
            fg='#888'
        )
        subtitle_label.pack(pady=(0, 50))

        # إطار النموذج
        form_frame = tk.Frame(page, bg='#2d2d2d', padx=30, pady=30, relief='ridge', bd=2)
        form_frame.pack(pady=20)

        # اسم المستخدم
        tk.Label(
            form_frame,
            text="اسم المستخدم:",
            font=("Arial", 12),
            bg='#2d2d2d',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=(0, 10))

        self.username_entry = tk.Entry(
            form_frame,
            font=("Arial", 12),
            width=30,
            bg='#3d3d3d',
            fg='white',
            insertbackground='white'
        )
        self.username_entry.grid(row=0, column=1, pady=(0, 10), padx=(10, 0))

        # كلمة المرور
        tk.Label(
            form_frame,
            text="كلمة المرور الرئيسية:",
            font=("Arial", 12),
            bg='#2d2d2d',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=(0, 20))

        self.password_entry = tk.Entry(
            form_frame,
            font=("Arial", 12),
            width=30,
            show="•",
            bg='#3d3d3d',
            fg='white',
            insertbackground='white'
        )
        self.password_entry.grid(row=1, column=1, pady=(0, 20), padx=(10, 0))

        # إطار الأزرار
        button_frame = tk.Frame(form_frame, bg='#2d2d2d')
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        # زر تسجيل الدخول
        login_btn = tk.Button(
            button_frame,
            text="تسجيل الدخول",
            font=("Arial", 12, "bold"),
            bg='#4CAF50',
            fg='white',
            padx=30,
            pady=10,
            command=self.login,
            cursor='hand2'
        )
        login_btn.pack(side='left', padx=10)

        # زر التسجيل
        register_btn = tk.Button(
            button_frame,
            text="تسجيل جديد",
            font=("Arial", 12),
            bg='#2196F3',
            fg='white',
            padx=30,
            pady=10,
            command=self.register,
            cursor='hand2'
        )
        register_btn.pack(side='left', padx=10)

        # مؤشر الحالة
        self.login_status = tk.Label(
            page,
            text="",
            font=("Arial", 10),
            bg='#1e1e1e',
            fg='#FF5252'
        )
        self.login_status.pack(pady=20)

        # نصائح الأمان
        tips_frame = tk.Frame(page, bg='#2d2d2d', padx=20, pady=20)
        tips_frame.pack(pady=30)

        tk.Label(
            tips_frame,
            text="💡 نصائح الأمان:",
            font=("Arial", 12, "bold"),
            bg='#2d2d2d',
            fg='#FFC107'
        ).pack(anchor='w')

        tips = [
            "• استخدم كلمة مرور رئيسية قوية وفريدة",
            "• لا تشارك كلمة المرور الرئيسية مع أحد",
            "• تأكد من تحديث البرنامج بانتظام",
            "• احتفظ بنسخة احتياطية من قاعدة البيانات"
        ]

        for tip in tips:
            tk.Label(
                tips_frame,
                text=tip,
                font=("Arial", 10),
                bg='#2d2d2d',
                fg='#aaa',
                justify='left'
            ).pack(anchor='w', pady=2)

    def create_main_page(self):
        """إنشاء الصفحة الرئيسية"""
        page = tk.Frame(self.main_frame, bg='#1e1e1e')
        self.pages["main"] = page

        # شريط العنوان
        header_frame = tk.Frame(page, bg='#2d2d2d', height=60)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)

        # عنوان الصفحة
        self.main_title = tk.Label(
            header_frame,
            text="القائمة الرئيسية",
            font=("Arial", 18, "bold"),
            bg='#2d2d2d',
            fg='white'
        )
        self.main_title.pack(side='left', padx=20)

        # معلومات المستخدم
        self.user_info = tk.Label(
            header_frame,
            text="",
            font=("Arial", 12),
            bg='#2d2d2d',
            fg='#4CAF50'
        )
        self.user_info.pack(side='right', padx=20)

        # زر إضافة جديد
        add_btn = tk.Button(
            header_frame,
            text="+ إضافة كلمة مرور جديدة",
            font=("Arial", 11, "bold"),
            bg='#4CAF50',
            fg='white',
            padx=15,
            pady=5,
            command=lambda: self.show_add_password_dialog(),
            cursor='hand2'
        )
        add_btn.pack(side='right', padx=10)

        # إطار المحتوى الرئيسي
        content_frame = tk.Frame(page, bg='#1e1e1e')
        content_frame.pack(fill='both', expand=True, padx=20)

        # الشريط الجانبي
        sidebar = tk.Frame(content_frame, bg='#2d2d2d', width=200)
        sidebar.pack(side='left', fill='y', padx=(0, 20))
        sidebar.pack_propagate(False)

        # تصفية التصنيفات
        tk.Label(
            sidebar,
            text="التصنيفات",
            font=("Arial", 12, "bold"),
            bg='#2d2d2d',
            fg='white'
        ).pack(pady=(20, 10))

        self.category_listbox = tk.Listbox(
            sidebar,
            bg='#3d3d3d',
            fg='white',
            selectbackground='#4CAF50',
            font=("Arial", 11),
            height=15,
            relief='flat'
        )
        self.category_listbox.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_select)

        # زر عرض الكل
        tk.Button(
            sidebar,
            text="عرض الكل",
            font=("Arial", 10),
            bg='#2196F3',
            fg='white',
            command=self.load_all_passwords,
            cursor='hand2'
        ).pack(pady=5, padx=10, fill='x')

        # زر تحديث القائمة
        tk.Button(
            sidebar,
            text="تحديث القائمة",
            font=("Arial", 10),
            bg='#607D8B',
            fg='white',
            command=self.refresh_password_list,
            cursor='hand2'
        ).pack(pady=5, padx=10, fill='x')

        # المنطقة الرئيسية
        main_content = tk.Frame(content_frame, bg='#1e1e1e')
        main_content.pack(side='right', fill='both', expand=True)

        # شريط البحث
        search_frame = tk.Frame(main_content, bg='#2d2d2d', height=40)
        search_frame.pack(fill='x', pady=(0, 10))
        search_frame.pack_propagate(False)

        tk.Label(
            search_frame,
            text="بحث:",
            font=("Arial", 11),
            bg='#2d2d2d',
            fg='white'
        ).pack(side='left', padx=(10, 5))

        self.search_entry = tk.Entry(
            search_frame,
            font=("Arial", 11),
            bg='#3d3d3d',
            fg='white',
            insertbackground='white',
            width=30
        )
        self.search_entry.pack(side='left', padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)

        # جدول كلمات المرور
        table_frame = tk.Frame(main_content, bg='#2d2d2d')
        table_frame.pack(fill='both', expand=True)

        # شريط التمرير
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')

        # إنشاء Treeview
        self.password_tree = ttk.Treeview(
            table_frame,
            columns=('ID', 'العنوان', 'اسم المستخدم', 'البريد الإلكتروني', 'التصنيف', 'آخر تحديث'),
            show='headings',
            yscrollcommand=scrollbar.set
        )

        # تعيين أسماء الأعمدة
        columns = [
            ('ID', 'ID', 50),
            ('العنوان', 'العنوان', 200),
            ('اسم المستخدم', 'اسم المستخدم', 150),
            ('البريد الإلكتروني', 'البريد الإلكتروني', 200),
            ('التصنيف', 'التصنيف', 100),
            ('آخر تحديث', 'آخر تحديث', 150)
        ]

        for col_id, col_text, width in columns:
            self.password_tree.heading(col_id, text=col_text)
            self.password_tree.column(col_id, width=width, minwidth=50)

        # تنسيق Treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background="#3d3d3d",
                        foreground="white",
                        fieldbackground="#3d3d3d",
                        rowheight=25)
        style.configure("Treeview.Heading",
                        background="#2d2d2d",
                        foreground="white",
                        relief="flat")
        style.map('Treeview', background=[('selected', '#4CAF50')])

        self.password_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.password_tree.yview)

        # ربط حدث النقر المزدوج
        self.password_tree.bind('<Double-Button-1>', self.on_password_double_click)

        # شريط الحالة
        self.status_bar = tk.Label(
            page,
            text="جاهز",
            font=("Arial", 10),
            bg='#2d2d2d',
            fg='#aaa',
            anchor='w',
            padx=10
        )
        self.status_bar.pack(side='bottom', fill='x', pady=(10, 0))

        # مؤشر القفل التلقائي
        self.lock_timer_label = tk.Label(
            page,
            text="",
            font=("Arial", 9),
            bg='#1e1e1e',
            fg='#FF9800'
        )
        self.lock_timer_label.pack(side='bottom', pady=(0, 5))

    def create_settings_page(self):
        """إنشاء صفحة الإعدادات"""
        page = tk.Frame(self.main_frame, bg='#1e1e1e')
        self.pages["settings"] = page

        # عنوان الصفحة
        tk.Label(
            page,
            text="الإعدادات",
            font=("Arial", 24, "bold"),
            bg='#1e1e1e',
            fg='white'
        ).pack(pady=30)

        # إطار الإعدادات
        settings_frame = tk.Frame(page, bg='#2d2d2d', padx=30, pady=30)
        settings_frame.pack(pady=20, padx=50)

        # إعدادات الأمان
        tk.Label(
            settings_frame,
            text="إعدادات الأمان",
            font=("Arial", 16, "bold"),
            bg='#2d2d2d',
            fg='#4CAF50'
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky='w')

        # وقت القفل التلقائي
        tk.Label(
            settings_frame,
            text="وقت القفل التلقائي (ثانية):",
            font=("Arial", 12),
            bg='#2d2d2d',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=10)

        self.auto_lock_var = tk.StringVar(value="300")
        auto_lock_entry = tk.Entry(
            settings_frame,
            textvariable=self.auto_lock_var,
            font=("Arial", 12),
            bg='#3d3d3d',
            fg='white',
            insertbackground='white',
            width=20
        )
        auto_lock_entry.grid(row=1, column=1, pady=10, padx=(10, 0))

        # وقت مسح الحافظة
        tk.Label(
            settings_frame,
            text="وقت مسح الحافظة (ثانية):",
            font=("Arial", 12),
            bg='#2d2d2d',
            fg='white'
        ).grid(row=2, column=0, sticky='w', pady=10)

        self.clipboard_timeout_var = tk.StringVar(value="30")
        clipboard_entry = tk.Entry(
            settings_frame,
            textvariable=self.clipboard_timeout_var,
            font=("Arial", 12),
            bg='#3d3d3d',
            fg='white',
            insertbackground='white',
            width=20
        )
        clipboard_entry.grid(row=2, column=1, pady=10, padx=(10, 0))

        # السمة
        tk.Label(
            settings_frame,
            text="السمة:",
            font=("Arial", 12),
            bg='#2d2d2d',
            fg='white'
        ).grid(row=3, column=0, sticky='w', pady=10)

        self.theme_var = tk.StringVar(value="dark")
        theme_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.theme_var,
            values=["dark", "light"],
            state="readonly",
            width=18
        )
        theme_combo.grid(row=3, column=1, pady=10, padx=(10, 0))

        # اللغة
        tk.Label(
            settings_frame,
            text="اللغة:",
            font=("Arial", 12),
            bg='#2d2d2d',
            fg='white'
        ).grid(row=4, column=0, sticky='w', pady=10)

        self.language_var = tk.StringVar(value="ar")
        language_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.language_var,
            values=["ar", "en"],
            state="readonly",
            width=18
        )
        language_combo.grid(row=4, column=1, pady=10, padx=(10, 0))

        # أزرار
        button_frame = tk.Frame(settings_frame, bg='#2d2d2d')
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))

        tk.Button(
            button_frame,
            text="حفظ الإعدادات",
            font=("Arial", 12, "bold"),
            bg='#4CAF50',
            fg='white',
            padx=30,
            pady=10,
            command=self.save_settings,
            cursor='hand2'
        ).pack(side='left', padx=10)

        tk.Button(
            button_frame,
            text="العودة للقائمة",
            font=("Arial", 12),
            bg='#607D8B',
            fg='white',
            padx=30,
            pady=10,
            command=lambda: self.show_page("main"),
            cursor='hand2'
        ).pack(side='left', padx=10)

    def show_page(self, page_name):
        """عرض صفحة محددة"""
        for page in self.pages.values():
            page.pack_forget()

        self.pages[page_name].pack(fill='both', expand=True)

        # إذا كانت الصفحة الرئيسية، قم بتحميل البيانات
        if page_name == "main" and self.current_user:
            self.load_user_data()
            self.refresh_password_list()

    def login(self):
        """تسجيل الدخول"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.login_status.config(text="يرجى إدخال اسم المستخدم وكلمة المرور")
            return

        # إظهار مؤشر الانتظار
        self.login_status.config(text="جاري تسجيل الدخول...", fg='#FFC107')
        self.root.update()

        # تسجيل الدخول في خيط منفصل
        def login_thread():
            success, message = self.pm.login(username, password)

            # تحديث الواجهة في الخيط الرئيسي
            self.root.after(0, lambda: self.handle_login_result(success, message, username))

        threading.Thread(target=login_thread, daemon=True).start()

    def handle_login_result(self, success, message, username):
        """معالجة نتيجة تسجيل الدخول"""
        if success:
            self.current_user = username
            self.login_status.config(text="", fg='#4CAF50')
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.show_page("main")
        else:
            self.login_status.config(text=message, fg='#FF5252')

    def register(self):
        """تسجيل مستخدم جديد"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.login_status.config(text="يرجى إدخال اسم المستخدم وكلمة المرور")
            return

        if len(password) < 8:
            self.login_status.config(text="كلمة المرور يجب أن تكون 8 أحرف على الأقل")
            return

        # إظهار مؤشر الانتظار
        self.login_status.config(text="جاري التسجيل...", fg='#FFC107')
        self.root.update()

        # التسجيل في خيط منفصل
        def register_thread():
            success, message = self.pm.register_user(username, password)

            # تحديث الواجهة في الخيط الرئيسي
            self.root.after(0, lambda: self.handle_register_result(success, message))

        threading.Thread(target=register_thread, daemon=True).start()

    def handle_register_result(self, success, message):
        """معالجة نتيجة التسجيل"""
        if success:
            self.login_status.config(text="تم التسجيل بنجاح! يمكنك تسجيل الدخول الآن", fg='#4CAF50')
        else:
            self.login_status.config(text=message, fg='#FF5252')

    def logout(self):
        """تسجيل الخروج"""
        self.pm.logout()
        self.current_user = None
        self.show_page("login")

    def load_user_data(self):
        """تحميل بيانات المستخدم"""
        if self.current_user:
            self.user_info.config(text=f"مرحباً، {self.current_user}")
            self.main_title.config(text=f"كلمات مرور {self.current_user}")

    def refresh_password_list(self):
        """تحديث قائمة كلمات المرور"""
        # مسح القائمة الحالية
        for item in self.password_tree.get_children():
            self.password_tree.delete(item)

        # تحميل التصنيفات
        categories = self.pm.get_categories()
        self.category_listbox.delete(0, tk.END)
        self.category_listbox.insert(tk.END, "الكل")
        for category in categories:
            self.category_listbox.insert(tk.END, category)

        # تحميل كلمات المرور
        passwords = self.pm.get_all_passwords()

        for pwd in passwords:
            self.password_tree.insert('', 'end', values=(
                pwd['id'],
                pwd['title'],
                pwd['username'] or '',
                pwd['email'] or '',
                pwd['category'],
                pwd['updated_at']
            ))

        self.status_bar.config(text=f"تم تحميل {len(passwords)} مدخل")

    def on_category_select(self, event):
        """عند اختيار تصنيف"""
        selection = self.category_listbox.curselection()
        if not selection:
            return

        category = self.category_listbox.get(selection[0])
        if category == "الكل":
            self.refresh_password_list()
        else:
            # مسح القائمة الحالية
            for item in self.password_tree.get_children():
                self.password_tree.delete(item)

            # تحميل كلمات المرور للتصنيف المحدد
            passwords = self.pm.get_all_passwords(category)

            for pwd in passwords:
                self.password_tree.insert('', 'end', values=(
                    pwd['id'],
                    pwd['title'],
                    pwd['username'] or '',
                    pwd['email'] or '',
                    pwd['category'],
                    pwd['updated_at']
                ))

            self.status_bar.config(text=f"تم تحميل {len(passwords)} مدخل في تصنيف {category}")

    def on_search(self, event):
        """عند البحث"""
        query = self.search_entry.get().lower()

        # إذا كان البحث فارغاً، أعد تحميل القائمة الكاملة
        if not query:
            return

        # تصفية العناصر
        for item in self.password_tree.get_children():
            values = self.password_tree.item(item, 'values')
            if any(query in str(value).lower() for value in values):
                self.password_tree.item(item, tags=('match',))
                self.password_tree.selection_set(item)
            else:
                self.password_tree.item(item, tags=('nomatch',))
                self.password_tree.selection_remove(item)

        # إخفاء العناصر غير المتطابقة
        self.password_tree.tag_configure('match', background='#3d3d3d')
        self.password_tree.tag_configure('nomatch', background='#2d2d2d')

    def on_password_double_click(self, event):
        """عند النقر المزدوج على عنصر"""
        selection = self.password_tree.selection()
        if not selection:
            return

        item = selection[0]
        entry_id = int(self.password_tree.item(item, 'values')[0])

        # الحصول على بيانات المدخل
        success, entry_data, message = self.pm.get_password(entry_id)

        if success:
            self.show_password_details(entry_data)
        else:
            messagebox.showerror("خطأ", message)

    def show_password_details(self, entry_data):
        """عرض تفاصيل كلمة المرور"""
        dialog = tk.Toplevel(self.root)
        dialog.title("تفاصيل كلمة المرور")
        dialog.geometry("600x500")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self.root)
        dialog.grab_set()

        # العنوان
        tk.Label(
            dialog,
            text="تفاصيل كلمة المرور",
            font=("Arial", 18, "bold"),
            bg='#2d2d2d',
            fg='white'
        ).pack(pady=20)

        # إطار النموذج
        form_frame = tk.Frame(dialog, bg='#3d3d3d', padx=20, pady=20)
        form_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # حقول العرض
        fields = [
            ("العنوان:", entry_data['title']),
            ("اسم المستخدم:", entry_data['username'] or ''),
            ("البريد الإلكتروني:", entry_data['email'] or ''),
            ("الرابط:", entry_data['url'] or ''),
            ("التصنيف:", entry_data['category']),
            ("الملاحظات:", entry_data['notes'] or '')
        ]
        for i, (label, value) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=("Arial", 11, "bold"),
                bg='#3d3d3d',
                fg='#4CAF50'
            ).grid(row=i, column=0, sticky='w', pady=5)

            if label == "الملاحظات:" and value:
                # استخدام ScrolledText للملاحظات الطويلة
                notes_text = scrolledtext.ScrolledText(
                    form_frame,
                    height=5,
                    font=("Arial", 10),
                    bg='#2d2d2d',
                    fg='white',
                    wrap='word'
                )
                notes_text.insert('1.0', value)
                notes_text.config(state='disabled')
                notes_text.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
            else:
                tk.Label(
                    form_frame,
                    text=value,
                    font=("Arial", 11),
                    bg='#3d3d3d',
                    fg='white'
                ).grid(row=i, column=1, sticky='w', pady=5, padx=(10, 0))

        # كلمة المرور (مع إمكانية إظهارها/إخفائها)
        tk.Label(
            form_frame,
            text="كلمة المرور:",
            font=("Arial", 11, "bold"),
            bg='#3d3d3d',
            fg='#4CAF50'
        ).grid(row=len(fields), column=0, sticky='w', pady=5)

        password_var = tk.StringVar(value="•" * len(entry_data['password']))
        password_entry = tk.Entry(
            form_frame,
            textvariable=password_var,
            font=("Arial", 11),
            bg='#2d2d2d',
            fg='white',
            show="•",
            width=30
        )
        password_entry.grid(row=len(fields), column=1, pady=5, padx=(10, 0), sticky='w')

        def toggle_password():
            if password_entry.cget('show') == "•":
                password_entry.config(show="")
                password_var.set(entry_data['password'])
                show_btn.config(text="إخفاء")
            else:
                password_entry.config(show="•")
                password_var.set("•" * len(entry_data['password']))
                show_btn.config(text="إظهار")

        show_btn = tk.Button(
            form_frame,
            text="إظهار",
            font=("Arial", 10),
            bg='#607D8B',
            fg='white',
            command=toggle_password,
            cursor='hand2'
        )
        show_btn.grid(row=len(fields), column=1, pady=5, padx=(10, 120), sticky='e')

        # أزرار الإجراءات
        button_frame = tk.Frame(form_frame, bg='#3d3d3d')
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=(20, 0))

        # زر النسخ
        copy_btn = tk.Button(
            button_frame,
            text="نسخ كلمة المرور",
            font=("Arial", 11, "bold"),
            bg='#2196F3',
            fg='white',
            padx=20,
            pady=8,
            command=lambda: self.copy_password(entry_data['password'], dialog),
            cursor='hand2'
        )
        copy_btn.pack(side='left', padx=5)

        # زر التعديل
        edit_btn = tk.Button(
            button_frame,
            text="تعديل",
            font=("Arial", 11),
            bg='#FF9800',
            fg='white',
            padx=20,
            pady=8,
            command=lambda: self.edit_password(entry_data, dialog),
            cursor='hand2'
        )
        edit_btn.pack(side='left', padx=5)

        # زر الحذف
        delete_btn = tk.Button(
            button_frame,
            text="حذف",
            font=("Arial", 11),
            bg='#F44336',
            fg='white',
            padx=20,
            pady=8,
            command=lambda: self.delete_password_confirmation(entry_data['id'], dialog),
            cursor='hand2'
        )
        delete_btn.pack(side='left', padx=5)

        # زر الإغلاق
        close_btn = tk.Button(
            button_frame,
            text="إغلاق",
            font=("Arial", 11),
            bg='#607D8B',
            fg='white',
            padx=20,
            pady=8,
            command=dialog.destroy,
            cursor='hand2'
        )
        close_btn.pack(side='left', padx=5)

    def show_add_password_dialog(self, edit_mode=False, entry_data=None):
        """عرض نافذة إضافة/تعديل كلمة مرور"""
        dialog = tk.Toplevel(self.root)
        dialog.title("إضافة كلمة مرور جديدة" if not edit_mode else "تعديل كلمة المرور")
        dialog.geometry("500x600")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self.root)
        dialog.grab_set()

        # العنوان
        title_text = "إضافة كلمة مرور جديدة" if not edit_mode else "تعديل كلمة المرور"
        tk.Label(
            dialog,
            text=title_text,
            font=("Arial", 18, "bold"),
            bg='#2d2d2d',
            fg='white'
        ).pack(pady=20)

        # إطار النموذج
        form_frame = tk.Frame(dialog, bg='#3d3d3d', padx=20, pady=20)
        form_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # حقول الإدخال
        fields = [
            ("العنوان *:", "title", "text"),
            ("اسم المستخدم:", "username", "text"),
            ("البريد الإلكتروني:", "email", "text"),
            ("الرابط:", "url", "text"),
            ("التصنيف:", "category", "text"),
            ("الملاحظات:", "notes", "multiline")
        ]

        entries = {}

        for i, (label, field_name, field_type) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=("Arial", 11, "bold"),
                bg='#3d3d3d',
                fg='white'
            ).grid(row=i, column=0, sticky='w', pady=5)

            if field_type == "multiline":
                widget = scrolledtext.ScrolledText(
                    form_frame,
                    height=5,
                    font=("Arial", 10),
                    bg='#2d2d2d',
                    fg='white',
                    wrap='word'
                )
                widget.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='ew')
                if edit_mode and entry_data and field_name in entry_data:
                    widget.insert('1.0', entry_data[field_name] or '')
            else:
                widget = tk.Entry(
                    form_frame,
                    font=("Arial", 11),
                    bg='#2d2d2d',
                    fg='white',
                    insertbackground='white',
                    width=30
                )
                widget.grid(row=i, column=1, pady=5, padx=(10, 0), sticky='w')
                if edit_mode and entry_data and field_name in entry_data:
                    widget.insert(0, entry_data[field_name] or '')

            entries[field_name] = widget

        # كلمة المرور
        tk.Label(
            form_frame,
            text="كلمة المرور *:",
            font=("Arial", 11, "bold"),
            bg='#3d3d3d',
            fg='white'
        ).grid(row=len(fields), column=0, sticky='w', pady=5)

        password_frame = tk.Frame(form_frame, bg='#3d3d3d')
        password_frame.grid(row=len(fields), column=1, pady=5, padx=(10, 0), sticky='w')

        password_var = tk.StringVar()
        if edit_mode and entry_data:
            password_var.set(entry_data['password'])

        password_entry = tk.Entry(
            password_frame,
            textvariable=password_var,
            font=("Arial", 11),
            bg='#2d2d2d',
            fg='white',
            show="•",
            width=25
        )
        password_entry.pack(side='left')

        def toggle_password_input():
            if password_entry.cget('show') == "•":
                password_entry.config(show="")
            else:
                password_entry.config(show="•")

        show_btn = tk.Button(
            password_frame,
            text="إظهار",
            font=("Arial", 9),
            bg='#607D8B',
            fg='white',
            command=toggle_password_input,
            cursor='hand2'
        )
        show_btn.pack(side='left', padx=(5, 0))

        def generate_password():
            new_password = self.pm.generate_secure_password()
            password_var.set(new_password)

        gen_btn = tk.Button(
            password_frame,
            text="إنشاء",
            font=("Arial", 9),
            bg='#4CAF50',
            fg='white',
            command=generate_password,
            cursor='hand2'
        )
        gen_btn.pack(side='left', padx=(5, 0))

        entries['password'] = password_entry

        # أزرار الإجراءات
        button_frame = tk.Frame(form_frame, bg='#3d3d3d')
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=(20, 0))

        def save_entry():
            # جمع البيانات
            entry_data = {}
            for field_name, widget in entries.items():
                if isinstance(widget, scrolledtext.ScrolledText):
                    value = widget.get('1.0', 'end-1c').strip()
                else:
                    value = widget.get().strip()

                entry_data[field_name] = value if value else None

            # التحقق من الحقول المطلوبة
            if not entry_data['title']:
                messagebox.showerror("خطأ", "العنوان مطلوب")
                return

            if not entry_data['password']:
                messagebox.showerror("خطأ", "كلمة المرور مطلوبة")
                return

            # تحديد الفئة الافتراضية
            if not entry_data['category']:
                entry_data['category'] = "عام"

            # الحفظ في قاعدة البيانات
            if not edit_mode:
                success, message = self.pm.add_password(entry_data)
            else:
                success, message = self.pm.update_password(entry_data['id'], entry_data)

            if success:
                messagebox.showinfo("نجاح", message)
                self.refresh_password_list()
                dialog.destroy()
            else:
                messagebox.showerror("خطأ", message)

        save_btn = tk.Button(
            button_frame,
            text="حفظ" if not edit_mode else "تحديث",
            font=("Arial", 12, "bold"),
            bg='#4CAF50',
            fg='white',
            padx=30,
            pady=10,
            command=save_entry,
            cursor='hand2'
        )
        save_btn.pack(side='left', padx=10)

        cancel_btn = tk.Button(
            button_frame,
            text="إلغاء",
            font=("Arial", 12),
            bg='#607D8B',
            fg='white',
            padx=30,
            pady=10,
            command=dialog.destroy,
            cursor='hand2'
        )
        cancel_btn.pack(side='left', padx=10)

    def edit_password(self, entry_data, parent_dialog):
        """تعديل كلمة مرور"""
        parent_dialog.destroy()
        self.show_add_password_dialog(edit_mode=True, entry_data=entry_data)

    def delete_password_confirmation(self, entry_id, parent_dialog):
        """طلب تأكيد الحذف"""
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف كلمة المرور هذه؟"):
            success, message = self.pm.delete_password(entry_id)

            if success:
                messagebox.showinfo("نجاح", message)
                self.refresh_password_list()
                parent_dialog.destroy()
            else:
                messagebox.showerror("خطأ", message)

    def copy_password(self, password, parent_dialog):
        """نسخ كلمة المرور إلى الحافظة"""
        success, message = self.pm.copy_to_clipboard(password)

        if success:
            messagebox.showinfo("نجاح", message, parent=parent_dialog)
        else:
            messagebox.showerror("خطأ", message, parent=parent_dialog)

    def load_all_passwords(self):
        """تحميل جميع كلمات المرور"""
        self.category_listbox.selection_clear(0, tk.END)
        self.refresh_password_list()

    def save_settings(self):
        """حفظ الإعدادات"""
        try:
            settings = {
                'clipboard_timeout': int(self.clipboard_timeout_var.get()),
                'auto_lock_timeout': int(self.auto_lock_var.get()),
                'theme': self.theme_var.get(),
                'language': self.language_var.get()
            }

            success, message = self.pm.update_settings(settings)

            if success:
                messagebox.showinfo("نجاح", message)
                self.theme = settings['theme']
                self.language = settings['language']
                self.apply_theme()
            else:
                messagebox.showerror("خطأ", message)

        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال قيم رقمية صحيحة")

    def apply_theme(self):
        """تطبيق السمة المحددة"""
        # يمكن توسيع هذه الوظيفة لتغيير ألوان الواجهة
        pass

    def toggle_theme(self):
        """تبديل السمة"""
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()
        messagebox.showinfo("السمة", f"تم تغيير السمة إلى {self.theme}")

    def export_passwords(self):
        """تصدير كلمات المرور"""
        if not self.current_user:
            messagebox.showerror("خطأ", "يجب تسجيل الدخول أولاً")
            return

        # طلب كلمة مرور التصدير
        password = self.ask_password("كلمة مرور التصدير", "أدخل كلمة مرور لحماية ملف التصدير:")
        if not password:
            return

        # اختيار موقع الحفظ
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not file_path:
            return

        # التصدير
        success, message = self.pm.export_passwords(file_path, password)

        if success:
            messagebox.showinfo("نجاح", message)
        else:
            messagebox.showerror("خطأ", message)

    def import_passwords(self):
        """استيراد كلمات المرور"""
        if not self.current_user:
            messagebox.showerror("خطأ", "يجب تسجيل الدخول أولاً")
            return

        # اختيار الملف
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not file_path:
            return

        # طلب كلمة مرور الاستيراد
        password = self.ask_password("كلمة مرور الاستيراد", "أدخل كلمة مرور ملف الاستيراد:")
        if not password:
            return

        # الاستيراد
        success, message = self.pm.import_passwords(file_path, password)

        if success:
            messagebox.showinfo("نجاح", message)
            self.refresh_password_list()
        else:
            messagebox.showerror("خطأ", message)

    def ask_password(self, title, prompt):
        """طلب كلمة مرور من المستخدم"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=prompt,
            font=("Arial", 11),
            bg='#2d2d2d',
            fg='white',
            wraplength=350
        ).pack(pady=20)

        password_var = tk.StringVar()
        password_entry = tk.Entry(
            dialog,
            textvariable=password_var,
            font=("Arial", 12),
            show="•",
            bg='#3d3d3d',
            fg='white',
            insertbackground='white',
            width=30
        )
        password_entry.pack(pady=10)
        password_entry.focus()

        result = {"password": None}

        def on_ok():
            result["password"] = password_var.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = tk.Frame(dialog, bg='#2d2d2d')
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="موافق",
            font=("Arial", 11),
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=5,
            command=on_ok,
            cursor='hand2'
        ).pack(side='left', padx=10)

        tk.Button(
            button_frame,
            text="إلغاء",
            font=("Arial", 11),
            bg='#607D8B',
            fg='white',
            padx=20,
            pady=5,
            command=on_cancel,
            cursor='hand2'
        ).pack(side='left', padx=10)

        dialog.wait_window()
        return result["password"]

    def change_master_password_dialog(self):
        """تغيير كلمة المرور الرئيسية"""
        if not self.current_user:
            messagebox.showerror("خطأ", "يجب تسجيل الدخول أولاً")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("تغيير كلمة المرور الرئيسية")
        dialog.geometry("400x300")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="تغيير كلمة المرور الرئيسية",
            font=("Arial", 16, "bold"),
            bg='#2d2d2d',
            fg='white'
        ).pack(pady=20)

        form_frame = tk.Frame(dialog, bg='#3d3d3d', padx=20, pady=20)
        form_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # كلمة المرور الحالية
        tk.Label(
            form_frame,
            text="كلمة المرور الحالية:",
            font=("Arial", 11),
            bg='#3d3d3d',
            fg='white'
        ).grid(row=0, column=0, sticky='w', pady=5)

        current_password_var = tk.StringVar()
        tk.Entry(
            form_frame,
            textvariable=current_password_var,
            font=("Arial", 11),
            show="•",
            bg='#2d2d2d',
            fg='white',
            insertbackground='white',
            width=25
        ).grid(row=0, column=1, pady=5, padx=(10, 0))

        # كلمة المرور الجديدة
        tk.Label(
            form_frame,
            text="كلمة المرور الجديدة:",
            font=("Arial", 11),
            bg='#3d3d3d',
            fg='white'
        ).grid(row=1, column=0, sticky='w', pady=5)

        new_password_var = tk.StringVar()
        tk.Entry(
            form_frame,
            textvariable=new_password_var,
            font=("Arial", 11),
            show="•",
            bg='#2d2d2d',
            fg='white',
            insertbackground='white',
            width=25
        ).grid(row=1, column=1, pady=5, padx=(10, 0))

        # تأكيد كلمة المرور الجديدة
        tk.Label(
            form_frame,
            text="تأكيد كلمة المرور الجديدة:",
            font=("Arial", 11),
            bg='#3d3d3d',
            fg='white'
        ).grid(row=2, column=0, sticky='w', pady=5)

        confirm_password_var = tk.StringVar()
        tk.Entry(
            form_frame,
            textvariable=confirm_password_var,
            font=("Arial", 11),
            show="•",
            bg='#2d2d2d',
            fg='white',
            insertbackground='white',
            width=25
        ).grid(row=2, column=1, pady=5, padx=(10, 0))

        def change_password():
            current = current_password_var.get()
            new = new_password_var.get()
            confirm = confirm_password_var.get()

            if not current or not new or not confirm:
                messagebox.showerror("خطأ", "جميع الحقول مطلوبة")
                return

            if new != confirm:
                messagebox.showerror("خطأ", "كلمتا المرور غير متطابقتين")
                return

            if len(new) < 8:
                messagebox.showerror("خطأ", "كلمة المرور الجديدة يجب أن تكون 8 أحرف على الأقل")
                return

            # تغيير كلمة المرور
            success, message = self.pm.change_master_password(current, new)

            if success:
                messagebox.showinfo("نجاح", message)
                dialog.destroy()
            else:
                messagebox.showerror("خطأ", message)

        button_frame = tk.Frame(form_frame, bg='#3d3d3d')
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        tk.Button(
            button_frame,
            text="تغيير",
            font=("Arial", 11, "bold"),
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=8,
            command=change_password,
            cursor='hand2'
        ).pack(side='left', padx=5)
        tk.Button(
            button_frame,
            text="إلغاء",
            font=("Arial", 11),
            bg='#607D8B',
            fg='white',
            padx=20,
            pady=8,
            command=dialog.destroy,
            cursor='hand2'
        ).pack(side='left', padx=5)
    def show_audit_logs(self):
        """عرض سجلات التدقيق"""
        if not self.current_user:
            messagebox.showerror("خطأ", "يجب تسجيل الدخول أولاً")
            return
        logs = self.pm.get_audit_logs()
        dialog = tk.Toplevel(self.root)
        dialog.title("سجلات التدقيق")
        dialog.geometry("800x500")
        dialog.configure(bg='#2d2d2d')
        dialog.transient(self.root)
        tk.Label(
            dialog,
            text="سجلات التدقيق",
            font=("Arial", 18, "bold"),
            bg='#2d2d2d',
            fg='white'
        ).pack(pady=20)
        # إنشاء Treeview للسجلات
        tree_frame = tk.Frame(dialog, bg='#2d2d2d')
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        log_tree = ttk.Treeview(
            tree_frame,
            columns=('التاريخ', 'الإجراء', 'التفاصيل'),
            show='headings',
            yscrollcommand=scrollbar.set
        )
        log_tree.heading('التاريخ', text='التاريخ')
        log_tree.heading('الإجراء', text='الإجراء')
        log_tree.heading('التفاصيل', text='التفاصيل')
        log_tree.column('التاريخ', width=150)
        log_tree.column('الإجراء', width=150)
        log_tree.column('التفاصيل', width=400)
        log_tree.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=log_tree.yview)
        # تنسيق Treeview
        style = ttk.Style()
        style.configure("Treeview",
                        background="#3d3d3d",
                        foreground="white",
                        fieldbackground="#3d3d3d")
        # إضافة السجلات
        for log in logs:
            log_tree.insert('', 'end', values=(
                log['timestamp'],
                log['action'],
                log['details'] or ''
            ))
        # زر الإغلاق
        tk.Button(
            dialog,
            text="إغلاق",
            font=("Arial", 11),
            bg='#607D8B',
            fg='white',
            padx=30,
            pady=10,
            command=dialog.destroy,
            cursor='hand2'
        ).pack(pady=10)
    def show_about(self):
        """عرض معلومات عن البرنامج"""
        about_text = """مدير كلمات المرور الآمن - الإصدار 1.0
برنامج آمن ومشفر لإدارة كلمات المرور.
تم التطوير باستخدام Python وcryptography.
المميزات:
• تشفير AES-256 لكلمات المرور
• مفتاح رئيسي مشتق باستخدام PBKDF2
• واجهة رسومية عربية احترافية
• مسح الحافظة تلقائياً
• تصدير واستيراد مشفر
• سجلات تدقيق للأمان
المطور: فريق الأمن السيبراني
© 2024 جميع الحقوق محفوظة"""
        messagebox.showinfo("عن البرنامج", about_text)
    def show_help(self):
        """عرض دليل الاستخدام"""
        help_text = """دليل استخدام مدير كلمات المرور الآمن
1. التسجيل والدخول:
   - أنشئ حساباً جديداً أو سجل الدخول بحساب موجود
   - استخدم كلمة مرور رئيسية قوية
2. إضافة كلمات المرور:
   - انقر على زر "إضافة كلمة مرور جديدة"
   - املأ التفاصيل المطلوبة
   - استخدم زر "إنشاء" لإنشاء كلمة مرور قوية
3. إدارة كلمات المرور:
   - انقر نقراً مزدوجاً على أي مدخل لعرض التفاصيل
   - استخدم زر "نسخ" لنسخ كلمة المرور
   - استخدم زر "تعديل" لتعديل المدخل
   - استخدم زر "حذف" لحذف المدخل
4. الإعدادات:
   - يمكنك تغيير وقت القفل التلقائي
   - يمكنك تغيير وقت مسح الحافظة
   - يمكنك تغيير السمة واللغة
5. التصدير والاستيراد:
   - استخدم قائمة "ملف" للتصدير والاستيراد
   - استخدم كلمة مرور قوية لحماية ملفات التصدير
نصائح الأمان:
   - لا تشارك كلمة المرور الرئيسية مع أحد
   - استخدم كلمات مرور مختلفة لكل حساب
   - احتفظ بنسخة احتياطية من قاعدة البيانات"""
        messagebox.showinfo("دليل الاستخدام", help_text)
    def update_lock_timer(self):
        """تحديث مؤشر القفل التلقائي"""
        if self.current_user and self.pm.session_start:
            elapsed = (datetime.now() - self.pm.session_start).seconds
            remaining = max(0, self.pm.auto_lock_timeout - elapsed)
            minutes = remaining // 60
            seconds = remaining % 60
            self.lock_timer_label.config(
                text=f"سيتم القفل التلقائي بعد: {minutes:02d}:{seconds:02d}"
            )
        # استدعاء الدالة كل ثانية
        self.root.after(1000, self.update_lock_timer)
    def on_closing(self):
        """عند إغلاق النافذة"""
        if messagebox.askokcancel("خروج", "هل تريد إغلاق البرنامج؟"):
            self.pm.close()
            self.root.destroy()
    def run(self):
        """تشغيل الواجهة"""
        self.root.mainloop()
if __name__ == "__main__":
    app = SecurePasswordManagerGUI()
    app.run()