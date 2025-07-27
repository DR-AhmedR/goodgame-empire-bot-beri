"""
GoodGame Empire Bot - بوت مملكة بيرموند
المطور: Ahmed.R
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import os
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import pyautogui
from PIL import Image, ImageTk
import logging
import webbrowser
import base64
from io import BytesIO
from selenium.webdriver.common.action_chains import ActionChains
import win32api
import win32con
import win32gui

# إعداد pyautogui
pyautogui.FAILSAFE = False  # تعطيل الحماية
pyautogui.PAUSE = 0.1  # تقليل التأخير

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
#   مهم مهم مهم مهم لتخطي الاعلانااات يرجي تجربه مانع اعلانات للكمبيوتر نفسه
class GoodGameEmpireBot:
    def __init__(self):
        """تهيئة البوت"""
        # إعدادات البوت - يجب أن تكون أولاً
        self.config = {
            'commanders_count': 1,
            'game_url': 'https://empire.goodgamestudios.com', # رابط اساسي ممكن تغيره من هنا او من الواجهه نفسها مش لازم يعني
            'telegram_bot_token': '', # حذفت التوكن ممكن تعمل بوت تيليجرام خاص بيك وتعمل توكن مخصوص ايزي او اتواصل معايا
            'telegram_chat_id': '',  # سيتم تعبئته من المستخدم في الواجهه نفسها
            'image_threshold': 0.7, 
            'click_delay': 0.5, # دي سرعه التأخير في الضغط علي الصوره بعد المطابقه
            'phase_delay': 120.0, # دا الانتظار دقيقتين بعد الهجمات كلها ممكن تعدلها بحرص
            'cycle_delay': 80.0, # دا التأخير في الدوره كلها
            'embedded_browser': True
        }
        # لو اتي اليوم الي نشرت فيه الملف اوبن سورس متنساش تشكر المطور وياريت متزلش معلومات المطور
        # معلومات المطور
        self.developer_info = {
            'name': 'Ahmed.R',
            'facebook': 'https://www.facebook.com/ahmed.r.el.shrief/',  # يمكن تحديث الرابط
            'whatsapp': '+201098662418',
            'version': '1.0.1'  # تحديث الإصدار
        }
        # المتغيرات دي مهمه متعلبش فيها خااالص!!
        # متغيرات البوت
        self.is_running = False
        self.driver = None
        self.embedded_driver = None
        self.current_phase = "منتظر"
        self.current_step = ""
        self.completed_cycles = 0
        self.errors = []
        self.last_action = ""
        self.game_loaded = False
        self.browser_window_handle = None
        self.paused_for_alert = False
        self.pause_start_time = None
        self.auto_resume_minutes = 30
        self.telegram_commands_enabled = True
        
        # تحميل الإعدادات المحفوظة
        self.load_settings()
        # الصور مقسمه لأربع مجموعات واحده هجوم والتانيه الهدايا والتالته ارسال قوات والرابع التحذيرات لو جه عرض ذروه مباشره او غيره
        # مجموعات الصور المحدثة
        self.image_groups = {
            'attack': [
                'to-tower.png',
                'attack-tower.png', 
                'attack-agree.png',
                'present.png',
                'attack.png',
                'horse.png',
                'horse-yes.png'
            ],
            'gifts': ['collect.png'],
            'send_troops': [
                'bermond-kingdom.png',
                'send-troops.png',
                'next.png',
                'solders.png',
                'select-all.png',
                'selected-yes.png',
                'skip.png',
                'watch-this.png',
                'click-twice.png',
                'send-exit.png',
                'return-to-camp-map.png'
            ],
            'alerts': [
                'zarwa.png',
                'zarwa2.png',
                'zarwa-exit.png',
                'zarwa2-exit.png'
            ]
        }
        
        # إنشاء واجهة المستخدم
        self.root = tk.Tk()
        self.setup_ui()
        
        # تحميل الصور
        self.load_images()
        
        # بدء واجهة المستخدم
        self.update_status_display()
    
    def load_settings(self):
        """تحميل الإعدادات المحفوظة"""
        try:
            if os.path.exists('bot_settings.json'):
                with open('bot_settings.json', 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # تحديث الإعدادات مع الحفاظ على القيم الافتراضية
                    for key, value in saved_settings.items():
                        if key in self.config:
                            self.config[key] = value
                print("✅ تم تحميل الإعدادات المحفوظة")
        except Exception as e:
            print(f"تعذر تحميل الإعدادات: {str(e)}")
    
    def save_settings(self):
        """حفظ الإعدادات"""
        try:
            # تحديث الإعدادات من واجهة المستخدم
            if hasattr(self, 'commanders_var'):
                self.config['commanders_count'] = int(self.commanders_var.get())
            if hasattr(self, 'game_url_var'):
                self.config['game_url'] = self.game_url_var.get().strip()
            if hasattr(self, 'telegram_chat_var'):
                self.config['telegram_chat_id'] = self.telegram_chat_var.get().strip()
            if hasattr(self, 'embedded_browser_var'):
                self.config['embedded_browser'] = self.embedded_browser_var.get()
            
            # حفظ في ملف
            with open('bot_settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.add_log("✅ تم حفظ الإعدادات", "success")
        except Exception as e:
            self.add_log(f"خطأ في حفظ الإعدادات: {str(e)}", "error")
    
    def get_chat_id_automatically(self):
        """الحصول على Chat ID تلقائياً من آخر رسالة"""
        try:
            if not self.config['telegram_bot_token']:
                return None
            
            url = f"https://api.telegram.org/bot{self.config['telegram_bot_token']}/getUpdates"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['ok'] and data['result']:
                    # الحصول على آخر رسالة
                    last_update = data['result'][-1]
                    if 'message' in last_update:
                        chat_id = str(last_update['message']['chat']['id'])
                        return chat_id
            return None
        except Exception as e:
            self.add_log(f"خطأ في الحصول على Chat ID: {str(e)}", "error")
            return None
    
    def auto_detect_chat_id(self):
        """كشف Chat ID تلقائياً"""
        self.add_log("🔍 جاري البحث عن Chat ID تلقائياً...", "info")
        
        def detect_thread():
            chat_id = self.get_chat_id_automatically()
            if chat_id:
                def update_ui():
                    self.telegram_chat_var.set(chat_id)
                    self.config['telegram_chat_id'] = chat_id
                    self.save_settings()
                    self.add_log(f"✅ تم العثور على Chat ID: {chat_id}", "success")
                    messagebox.showinfo("نجح!", f"تم العثور على Chat ID تلقائياً: {chat_id}")
                
                self.root.after(0, update_ui)
            else:
                def show_error():
                    self.add_log("❌ لم يتم العثور على Chat ID", "error")
                    messagebox.showwarning(
                        "لم يتم العثور على Chat ID", 
                        "يرجى إرسال أي رسالة للبوت في التليجرام أولاً، ثم المحاولة مرة أخرى"
                    )
                
                self.root.after(0, show_error)
        
        threading.Thread(target=detect_thread, daemon=True).start()
        
    def create_icon(self):
        """إنشاء أيقونة البوت"""
        try:
            if not os.path.exists("icon.ico"):
                from PIL import Image, ImageDraw
                
                img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # رسم دائرة زرقاء
                draw.ellipse([8, 8, 56, 56], fill=(52, 152, 219, 255), outline=(41, 128, 185, 255), width=2)
                
                # رسم حرف G في المنتصف
                draw.text((24, 20), "G", fill=(255, 255, 255, 255))
                
                img.save("icon.ico", format='ICO')
                
            self.root.iconbitmap("icon.ico")
            
        except Exception as e:
            print(f"تعذر إنشاء الأيقونة: {e}")
    
    def create_logo_image(self):
        """إنشاء صورة الشعار"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # رسم خلفية دائرية
            draw.ellipse([10, 10, 90, 90], fill=(52, 152, 219, 255), outline=(41, 128, 185, 255), width=3)
            
            # رسم تاج صغير
            crown_points = [(35, 25), (40, 15), (45, 20), (50, 15), (55, 20), (60, 15), (65, 25), (35, 25)]
            draw.polygon(crown_points, fill=(241, 196, 15, 255))
            
            # رسم حرف G
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            draw.text((42, 45), "G", fill=(255, 255, 255, 255), font=font)
            
            return ImageTk.PhotoImage(img)
            
        except Exception as e:
            print(f"تعذر إنشاء الشعار: {e}")
            return None
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.root.title("🎮 GoodGame Empire Bot - بوت مملكة بيرموند | المطور: Ahmed.R")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        self.root.resizable(True, True)
        
        # إنشاء وتطبيق الأيقونة
        self.create_icon()
        
        # إعداد الأنماط
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), background='#2c3e50', foreground='white')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#34495e', foreground='white')
        style.configure('Status.TLabel', font=('Arial', 10), background='#34495e', foreground='#ecf0f1')
        style.configure('Developer.TLabel', font=('Arial', 9), background='#2c3e50', foreground='#bdc3c7')
        
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # إطار العنوان والشعار
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # إطار الشعار والعنوان
        logo_title_frame = ttk.Frame(header_frame)
        logo_title_frame.pack(side=tk.LEFT)
        
        # الشعار
        logo_image = self.create_logo_image()
        if logo_image:
            logo_label = ttk.Label(logo_title_frame, image=logo_image, background='#2c3e50')
            logo_label.image = logo_image
            logo_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # العنوان
        title_info_frame = ttk.Frame(logo_title_frame)
        title_info_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = ttk.Label(
            title_info_frame, 
            text="🎮 بوت GoodGame Empire",
            style='Title.TLabel'
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(
            title_info_frame, 
            text="🏰 مملكة بيرموند - نظام التحكم الذكي",
            font=('Arial', 12),
            background='#2c3e50', 
            foreground='#ecf0f1'
        )
        subtitle_label.pack(anchor=tk.W)
        
        # معلومات المطور
        developer_frame = ttk.Frame(header_frame)
        developer_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        dev_title = ttk.Label(
            developer_frame,
            text="👨‍💻 المطور: Ahmed.R",
            font=('Arial', 11, 'bold'),
            background='#2c3e50',
            foreground='#3498db'
        )
        dev_title.pack(anchor=tk.E)
        
        # روابط التواصل
        contact_frame = ttk.Frame(developer_frame)
        contact_frame.pack(anchor=tk.E, pady=(5, 0))
        
        # رابط الفيسبوك
        fb_button = tk.Button(
            contact_frame,
            text="📘 Facebook",
            command=lambda: self.open_link(self.developer_info['facebook']),
            bg='#3b5998',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            padx=10,
            cursor='hand2'
        )
        fb_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # رابط الواتساب
        wa_button = tk.Button(
            contact_frame,
            text="📱 WhatsApp",
            command=lambda: self.open_whatsapp(),
            bg='#25d366',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            padx=10,
            cursor='hand2'
        )
        wa_button.pack(side=tk.LEFT)
        
        # إصدار البوت
        version_label = ttk.Label(
            developer_frame,
            text=f"الإصدار: {self.developer_info['version']}",
            style='Developer.TLabel'
        )
        version_label.pack(anchor=tk.E, pady=(2, 0))
        
        # فاصل
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 10))
        
        # إطار التحكم الرئيسي
        control_main_frame = ttk.Frame(main_frame)
        control_main_frame.pack(fill=tk.X, pady=(0, 10))
        
        # لوحة الإعدادات
        settings_frame = ttk.LabelFrame(control_main_frame, text="⚙️ إعدادات البوت", padding=10)
        settings_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # عدد القادة
        ttk.Label(settings_frame, text="عدد القادة:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.commanders_var = tk.StringVar(value=str(self.config['commanders_count']))
        commanders_spin = ttk.Spinbox(
            settings_frame, 
            from_=1, to=50, 
            textvariable=self.commanders_var,
            width=10
        )
        commanders_spin.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # رابط اللعبة
        ttk.Label(settings_frame, text="رابط اللعبة:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.game_url_var = tk.StringVar(value=self.config['game_url'])
        game_url_entry = ttk.Entry(settings_frame, textvariable=self.game_url_var, width=40)
        game_url_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # خيار المتصفح المدمج
        self.embedded_browser_var = tk.BooleanVar(value=self.config['embedded_browser'])
        embedded_check = ttk.Checkbutton(
            settings_frame,
            text="🌐 تشغيل اللعبة داخل البرنامج",
            variable=self.embedded_browser_var,
            command=self.toggle_embedded_browser
        )
        embedded_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # إعدادات التليجرام - Chat ID مع كشف تلقائي
        telegram_frame = ttk.Frame(settings_frame)
        telegram_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(telegram_frame, text="📱 Telegram Chat ID:").pack(side=tk.LEFT)
        self.telegram_chat_var = tk.StringVar(value=self.config['telegram_chat_id'])
        telegram_chat_entry = ttk.Entry(telegram_frame, textvariable=self.telegram_chat_var, width=25)
        telegram_chat_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        # زر الكشف التلقائي
        """auto_detect_button = ttk.Button(
            telegram_frame,
            text="🔍 كشف تلقائي",
            command=self.auto_detect_chat_id,
            width=12
        )
        auto_detect_button.pack(side=tk.LEFT)
     """
        # إضافة تسمية توضيحية محسنة
        help_label = ttk.Label(
            settings_frame, 
            text="💡 للحصول على Chat ID: ابحث عن @userinfobot في تليجرام وأرسل /start\n"
                 "أو أرسل أي رسالة للبوت ثم اضغط 'كشف تلقائي'",
            font=('Arial', 8),
            foreground='#7f8c8d'
        )
        help_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # أزرار التحكم
        buttons_frame = ttk.Frame(settings_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        # زر حفظ الإعدادات
        save_settings_button = ttk.Button(
            buttons_frame,
            text="💾 حفظ الإعدادات",
            command=self.save_settings
        )
        save_settings_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # زر تحميل اللعبة
        self.load_game_button = ttk.Button(
            buttons_frame,
            text="🌐 تحميل اللعبة",
            command=self.load_embedded_game,
            style='Accent.TButton'
        )
        self.load_game_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.start_button = ttk.Button(
            buttons_frame,
            text="🚀 تشغيل البوت",
            command=self.start_bot,
            style='Accent.TButton',
            state=tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(
            buttons_frame,
            text="⏹️ إيقاف البوت", 
            command=self.stop_bot,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.test_telegram_button = ttk.Button(
            buttons_frame,
            text="📱 اختبار التليجرام",
            command=self.test_telegram
        )
        self.test_telegram_button.pack(side=tk.LEFT)
        
        # الصف الثاني من الأزرار
        buttons_frame2 = ttk.Frame(settings_frame)
        buttons_frame2.grid(row=6, column=0, columnspan=2, pady=5)
        
        # زر اختبار النقر
        self.test_click_button = ttk.Button(
            buttons_frame2,
            text="🖱️ اختبار النقر",
            command=self.test_mouse_click
        )
        self.test_click_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # زر استئناف يدوي
        self.resume_button = ttk.Button(
            buttons_frame2,
            text="▶️ استئناف",
            command=self.manual_resume,
            state=tk.DISABLED
        )
        self.resume_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # لوحة الحالة
        status_frame = ttk.LabelFrame(control_main_frame, text="📊 حالة البوت", padding=10)
        status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # معلومات الحالة
        self.status_labels = {}
        status_info = [
            ("الحالة:", "status"),
            ("حالة اللعبة:", "game_status"),
            ("المرحلة الحالية:", "phase"),
            ("الخطوة:", "step"),
            ("الدورات المكتملة:", "cycles"),
            ("آخر إجراء:", "last_action")
        ]
        
        for i, (label_text, key) in enumerate(status_info):
            ttk.Label(status_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=2)
            self.status_labels[key] = ttk.Label(status_frame, text="--", style='Status.TLabel')
            self.status_labels[key].grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # شريط التقدم
        ttk.Label(status_frame, text="التقدم:").grid(row=len(status_info), column=0, sticky=tk.W, pady=2)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame, 
            variable=self.progress_var,
            maximum=100,
            length=200
        )
        self.progress_bar.grid(row=len(status_info), column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # الإطار الرئيسي للمحتوى
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # إنشاء PanedWindow للتقسيم
        paned_window = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # إطار اللعبة المدمجة
        self.game_frame = ttk.LabelFrame(paned_window, text="🎮 اللعبة", padding=5)
        paned_window.add(self.game_frame, weight=3)
        
        # رسالة تحميل اللعبة
        self.game_status_label = ttk.Label(
            self.game_frame,
            text="🌐 اضغط على 'تحميل اللعبة' لبدء تشغيل اللعبة داخل البرنامج",
            font=('Arial', 12),
            anchor=tk.CENTER
        )
        self.game_status_label.pack(expand=True)
        
        # إطار السجلات والمراقبة
        logs_frame = ttk.LabelFrame(paned_window, text="📊 المراقبة والسجلات", padding=5)
        paned_window.add(logs_frame, weight=2)
        
        # دفتر التبويبات
        notebook = ttk.Notebook(logs_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # تبويب السجلات
        logs_tab = ttk.Frame(notebook)
        notebook.add(logs_tab, text="📝 سجل العمليات")
        
        self.logs_text = scrolledtext.ScrolledText(
            logs_tab,
            height=15,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#ffffff',
            insertbackground='white'
        )
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # تبويب مجموعات الصور
        images_tab = ttk.Frame(notebook)
        notebook.add(images_tab, text="🖼️ مجموعات الصور")
        
        images_text = scrolledtext.ScrolledText(
            images_tab,
            height=15,
            font=('Arial', 9),
            state=tk.DISABLED
        )
        images_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # عرض مجموعات الصور
        images_info = self.get_images_info()
        images_text.config(state=tk.NORMAL)
        images_text.insert(tk.END, images_info)
        images_text.config(state=tk.DISABLED)
        
        # تبويب الأخطاء
        errors_tab = ttk.Frame(notebook)
        notebook.add(errors_tab, text="⚠️ الأخطاء")
        
        self.errors_text = scrolledtext.ScrolledText(
            errors_tab,
            height=15,
            font=('Consolas', 9),
            bg='#2c1810',
            fg='#ff6b6b'
        )
        self.errors_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def add_log(self, message, log_type="info"):
        """إضافة رسالة إلى السجل"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # رموز الرسائل
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️", 
            "error": "❌"
        }
        
        log_message = f"[{timestamp}] {icons.get(log_type, 'ℹ️')} {message}\n"
        
        # إضافة إلى واجهة المستخدم
        def update_ui():
            if hasattr(self, 'logs_text'):
                self.logs_text.config(state=tk.NORMAL)
                self.logs_text.insert(tk.END, log_message)
                self.logs_text.see(tk.END)
                self.logs_text.config(state=tk.DISABLED)
                
                # إضافة الأخطاء إلى تبويب الأخطاء
                if log_type == "error" and hasattr(self, 'errors_text'):
                    self.errors_text.config(state=tk.NORMAL)
                    self.errors_text.insert(tk.END, log_message)
                    self.errors_text.see(tk.END)
                    self.errors_text.config(state=tk.DISABLED)
                    self.errors.append(message)
        
        if threading.current_thread() == threading.main_thread():
            update_ui()
        else:
            self.root.after(0, update_ui)
        
        # تسجيل في ملف السجل
        logging.info(f"{log_type.upper()}: {message}")
    
    def open_link(self, url):
        """فتح رابط في المتصفح"""
        if url and url != '#':
            webbrowser.open(url)
        else:
            messagebox.showinfo("معلومات", "رابط الفيسبوك متاح الآن!")
    
    def open_whatsapp(self):
        """فتح رابط الواتساب"""
        whatsapp_url = f"https://wa.me/{self.developer_info['whatsapp'].replace('+', '')}"
        webbrowser.open(whatsapp_url)
    
    def toggle_embedded_browser(self):
        """تبديل حالة المتصفح المدمج"""
        self.config['embedded_browser'] = self.embedded_browser_var.get()
        
        if self.config['embedded_browser']:
            self.load_game_button.config(state=tk.NORMAL)
            self.game_status_label.config(text="🌐 اضغط على 'تحميل اللعبة' لبدء تشغيل اللعبة داخل البرنامج")
        else:
            self.load_game_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            self.game_status_label.config(text="🌐 المتصفح المدمج معطل - سيتم استخدام متصفح منفصل")
    
    def get_browser_window_position(self):
        """الحصول على موقع نافذة المتصفح"""
        try:
            if not self.driver:
                return None
                
            # البحث عن النافذة
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "Chrome" in title or "GoodGame" in title:
                        windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                hwnd = windows[0]
                rect = win32gui.GetWindowRect(hwnd)
                return {
                    'x': rect[0],
                    'y': rect[1],
                    'width': rect[2] - rect[0],
                    'height': rect[3] - rect[1]
                }
            
            return None
            
        except Exception as e:
            self.add_log(f"خطأ في الحصول على موقع النافذة: {str(e)}", "error")
            return None
    
    def test_mouse_click(self):
        """اختبار النقر بالماوس"""
        self.add_log("🖱️ اختبار النقر - ضع الماوس في المكان المطلوب خلال 3 ثوان...", "info")
        
        def test_click():
            time.sleep(3)
            
            current_pos = pyautogui.position()
            self.add_log(f"📍 موقع الماوس: ({current_pos.x}, {current_pos.y})", "info")
            
            self.mouse_click(current_pos.x, current_pos.y)
            
        threading.Thread(target=test_click, daemon=True).start()
    
    def mouse_click(self, x, y):
        """النقر بالماوس مع طرق متعددة"""
        try:
            self.add_log(f"🖱️ محاولة النقر على: ({x}, {y})", "info")
            
            # الطريقة الأولى: pyautogui
            try:
                original_pos = pyautogui.position()
                pyautogui.moveTo(x, y, duration=0.2)
                time.sleep(0.1)
                pyautogui.click(x, y)
                self.add_log(f"✅ تم النقر بـ pyautogui على: ({x}, {y})", "success")
                return True
                
            except Exception as e:
                self.add_log(f"فشل النقر بـ pyautogui: {str(e)}", "warning")
            
            # الطريقة الثانية: win32api
            try:
                screen_x = int(x)
                screen_y = int(y)
                
                win32api.SetCursorPos((screen_x, screen_y))
                time.sleep(0.1)
                
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
                
                self.add_log(f"✅ تم النقر بـ win32api على: ({screen_x}, {screen_y})", "success")
                return True
                
            except Exception as e:
                self.add_log(f"فشل النقر بـ win32api: {str(e)}", "warning")
            
            return False
            
        except Exception as e:
            self.add_log(f"خطأ عام في النقر: {str(e)}", "error")
            return False
    
    def double_mouse_click(self, x, y, delay=1.0):
        """النقر المزدوج بالماوس"""
        try:
            self.add_log(f"👆👆 النقر المزدوج على: ({x}, {y})", "info")
            
            success1 = self.mouse_click(x, y)
            time.sleep(delay)
            success2 = self.mouse_click(x, y)
            
            if success1 and success2:
                self.add_log("✅ تم النقر المزدوج بنجاح", "success")
                return True
            else:
                self.add_log("❌ فشل في النقر المزدوج", "error")
                return False
                
        except Exception as e:
            self.add_log(f"خطأ في النقر المزدوج: {str(e)}", "error")
            return False
    
    def load_embedded_game(self):
        """تحميل اللعبة في المتصفح المدمج"""
        if not self.config['embedded_browser']:
            return
            
        self.add_log("🌐 جاري تحميل اللعبة في المتصفح المدمج...", "info")
        self.game_status_label.config(text="⏳ جاري تحميل اللعبة...")
        self.load_game_button.config(state=tk.DISABLED)
        
        def load_game_thread():
            try:
                chrome_options = Options()
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument("--window-size=1200,800")
                chrome_options.add_argument("--window-position=100,100")
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                self.embedded_driver = webdriver.Chrome(options=chrome_options)
                self.embedded_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                game_url = self.game_url_var.get().strip()
                self.embedded_driver.get(game_url)
                
                time.sleep(5)
                
                self.game_loaded = True
                self.add_log("✅ تم تحميل اللعبة بنجاح!", "success")
                
                def update_ui():
                    self.game_status_label.config(text="✅ اللعبة محملة وجاهزة - يمكنك الآن تشغيل البوت")
                    self.start_button.config(state=tk.NORMAL)
                    self.load_game_button.config(text="🔄 إعادة تحميل اللعبة", state=tk.NORMAL)
                    self.status_labels["game_status"].config(text="✅ محملة")
                
                self.root.after(0, update_ui)
                
            except Exception as e:
                error_msg = f"خطأ في تحميل اللعبة: {str(e)}"
                self.add_log(error_msg, "error")
                
                def update_error_ui():
                    self.game_status_label.config(text="❌ فشل في تحميل اللعبة - تحقق من الاتصال")
                    self.load_game_button.config(state=tk.NORMAL)
                    self.status_labels["game_status"].config(text="❌ فشل التحميل")
                
                self.root.after(0, update_error_ui)
        
        threading.Thread(target=load_game_thread, daemon=True).start()
    
    def get_images_info(self):
        """الحصول على معلومات مجموعات الصور"""
        info = "📋 مجموعات الصور المطلوبة:\n\n"
        
        groups_info = {
            'attack': ('⚔️ مجموعة الهجوم', 'تنفذ بالترتيب مع تكرار حسب عدد القادة'),
            'gifts': ('🎁 مجموعة الهدايا', 'تظهر أحياناً بعد الهجوم'),
            'send_troops': ('👥 مجموعة إرسال الجنود', 'إرسال الجنود إلى مملكة بيرموند'),
            'alerts': ('🚨 مجموعة التحذيرات', 'مراقبة التحذيرات وأزرار الخروج')
        }
        
        for group_key, (group_title, group_desc) in groups_info.items():
            info += f"{group_title}:\n"
            info += f"الوصف: {group_desc}\n"
            info += "الصور:\n"
            
            for i, image_name in enumerate(self.image_groups[group_key], 1):
                status = "✅" if os.path.exists(f"objects/{image_name}") else "❌"
                info += f"  {i}. {status} {image_name}\n"
            
            info += "\n"
        
        return info
        
    def load_images(self):
        """تحميل جميع الصور المطلوبة"""
        self.images = {}
        objects_dir = "objects"
        
        if not os.path.exists(objects_dir):
            os.makedirs(objects_dir)
            self.add_log("تم إنشاء مجلد objects", "warning")
        
        total_images = sum(len(group) for group in self.image_groups.values())
        loaded_images = 0
        
        for group_name, image_list in self.image_groups.items():
            self.images[group_name] = {}
            
            for image_name in image_list:
                image_path = os.path.join(objects_dir, image_name)
                
                if os.path.exists(image_path):
                    try:
                        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
                        if image is not None:
                            self.images[group_name][image_name] = image
                            loaded_images += 1
                            self.add_log(f"✅ تم تحميل: {image_name}", "success")
                        else:
                            self.add_log(f"❌ فشل في قراءة: {image_name}", "error")
                    except Exception as e:
                        self.add_log(f"❌ خطأ في تحميل {image_name}: {str(e)}", "error")
                else:
                    self.add_log(f"❌ الصورة مفقودة: {image_name}", "error")
        
        self.add_log(f"📊 تم تحميل {loaded_images}/{total_images} صورة", "info")
        
    def update_status_display(self):
        """تحديث عرض الحالة"""
        def update():
            if hasattr(self, 'status_labels'):
                status_text = "🟢 يعمل" if self.is_running else "🔴 متوقف"
                self.status_labels["status"].config(text=status_text)
                
                game_status = "✅ محملة" if self.game_loaded else "⏳ غير محملة"
                self.status_labels["game_status"].config(text=game_status)
                
                self.status_labels["phase"].config(text=self.current_phase)
                self.status_labels["step"].config(text=self.current_step)
                self.status_labels["cycles"].config(text=str(self.completed_cycles))
                self.status_labels["last_action"].config(text=self.last_action)
                
                # تحديث زر الاستئناف
                if hasattr(self, 'resume_button'):
                    if self.paused_for_alert:
                        self.resume_button.config(state=tk.NORMAL)
                    else:
                        self.resume_button.config(state=tk.DISABLED)
        
        if threading.current_thread() == threading.main_thread():
            update()
        else:
            self.root.after(0, update)
            
    def update_progress(self, value):
        """تحديث شريط التقدم"""
        def update():
            if hasattr(self, 'progress_var'):
                self.progress_var.set(value)
        
        if threading.current_thread() == threading.main_thread():
            update()
        else:
            self.root.after(0, update)
    
    def send_telegram_message(self, message, message_type="info"):
        """إرسال رسالة تليجرام"""
        if not self.config['telegram_bot_token'] or not self.config['telegram_chat_id']:
            return False
            
        try:
            icons = {
                "info": "ℹ️",
                "success": "✅", 
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨"
            }
            
            telegram_message = f"{icons.get(message_type, 'ℹ️')} <b>بوت GoodGame Empire</b>\n\n"
            telegram_message += f"{message}\n\n"
            telegram_message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            telegram_message += f"\n👨‍💻 المطور: Ahmed.R"
            
            url = f"https://api.telegram.org/bot{self.config['telegram_bot_token']}/sendMessage"
            data = {
                'chat_id': self.config['telegram_chat_id'],
                'text': telegram_message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.add_log(f"خطأ في إرسال رسالة تليجرام: {str(e)}", "error")
            return False
    
    def test_telegram(self):
        """اختبار اتصال التليجرام"""
        # حفظ الإعدادات أولاً
        self.save_settings()
        
        if not self.config['telegram_chat_id']:
            messagebox.showwarning("تحذير", "يرجى إدخال Chat ID للتليجرام أو استخدام الكشف التلقائي")
            return
        
        self.add_log("جاري اختبار اتصال التليجرام...", "info")
        
        def test_connection():
            success = self.send_telegram_message(
                "🎮 اختبار اتصال البوت - البوت متصل بنجاح!\n\n"
                "✅ يمكنك الآن تشغيل البوت وستصلك جميع الإشعارات\n"
                "🤖 نظام zarwa الذكي مفعل للتعامل مع التحذيرات تلقائياً", 
                "success"
            )
        
            if success:
                self.add_log("✅ تم اختبار التليجرام بنجاح!", "success")
                messagebox.showinfo("نجح", "تم إرسال رسالة اختبار بنجاح!")
            else:
                self.add_log("❌ فشل في اختبار التليجرام", "error")
                messagebox.showerror("خطأ", "فشل في إرسال رسالة الاختبار\nتأكد من صحة Chat ID")
        
        threading.Thread(target=test_connection, daemon=True).start()
    
    def setup_browser(self):
        """إعداد المتصفح"""
        try:
            if self.config['embedded_browser'] and self.embedded_driver:
                self.driver = self.embedded_driver
                self.add_log("✅ استخدام المتصفح المدمج للبوت", "success")
                return True
            
            self.add_log("جاري إعداد المتصفح المنفصل...", "info")
            
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--window-size=1366,768")
            chrome_options.add_argument("--window-position=200,100")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.get(self.config['game_url'])
            self.add_log("✅ تم فتح المتصفح واللعبة بنجاح", "success")
            
            time.sleep(5)
            return True
            
        except Exception as e:
            self.add_log(f"❌ خطأ في إعداد المتصفح: {str(e)}", "error")
            return False
    
    def take_screenshot(self):
        """التقاط لقطة شاشة من المتصفح"""
        try:
            if not self.driver:
                return None
                
            screenshot = self.driver.get_screenshot_as_png()
            nparr = np.frombuffer(screenshot, np.uint8)
            screenshot_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return screenshot_cv
            
        except Exception as e:
            self.add_log(f"خطأ في التقاط الشاشة: {str(e)}", "error")
            return None
    
    def find_image_on_screen(self, image_name, group_name):
        """البحث عن صورة على الشاشة مع تحسينات"""
        try:
            if group_name not in self.images or image_name not in self.images[group_name]:
                self.add_log(f"الصورة غير موجودة: {image_name}", "error")
                return None
            
            screenshot = self.take_screenshot()
            if screenshot is None:
                return None
            
            template = self.images[group_name][image_name]
            
            methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED, cv2.TM_SQDIFF_NORMED]
            best_match = None
            best_confidence = 0
            
            for method in methods:
                result = cv2.matchTemplate(screenshot, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if method == cv2.TM_SQDIFF_NORMED:
                    confidence = 1 - min_val
                    loc = min_loc
                else:
                    confidence = max_val
                    loc = max_loc
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = loc
            
            if best_confidence >= self.config['image_threshold']:
                h, w = template.shape[:2]
                center_x = best_match[0] + w // 2
                center_y = best_match[1] + h // 2
                
                browser_pos = self.get_browser_window_position()
                if browser_pos:
                    screen_x = browser_pos['x'] + center_x
                    screen_y = browser_pos['y'] + center_y + 80
                else:
                    screen_x = center_x + 100
                    screen_y = center_y + 180
                
                self.add_log(f"✅ تم العثور على {image_name} - الثقة: {best_confidence:.2f}", "success")
                return (screen_x, screen_y, best_confidence)
            else:
                self.add_log(f"❌ لم يتم العثور على {image_name} - أعلى ثقة: {best_confidence:.2f}", "warning")
                return None
                
        except Exception as e:
            self.add_log(f"خطأ في البحث عن الصورة {image_name}: {str(e)}", "error")
            return None
    
    def execute_attack_sequence(self):
        """تنفيذ مجموعة الهجوم"""
        self.current_phase = "مجموعة الهجوم"
        self.update_status_display()
        
        commanders_count = int(self.commanders_var.get())
        total_steps = len(self.image_groups['attack']) * commanders_count
        current_step = 0
        
        for commander in range(commanders_count):
            if not self.is_running:
                break
                
            self.add_log(f"🏹 بدء هجوم القائد {commander + 1}/{commanders_count}", "info")
            
            for i, image_name in enumerate(self.image_groups['attack']):
                if not self.is_running:
                    break
                    
                self.current_step = f"القائد {commander + 1}: البحث عن {image_name}"
                self.update_status_display()
                
                result = None
                for attempt in range(3):
                    result = self.find_image_on_screen(image_name, 'attack')
                    if result:
                        break
                    time.sleep(0.5)
                
                if result:
                    x, y, confidence = result
                    
                    if image_name == "horse.png":
                        watch_result = self.find_image_on_screen("watch-this.png", 'send_troops')
                        if watch_result:
                            wx, wy, _ = watch_result
                            self.add_log("🎬 تم العثور على watch-this، تنفيذ النقر المزدوج", "warning")
                            self.double_mouse_click(wx, wy, 1.0)
                    
                    if self.mouse_click(x, y):
                        self.last_action = f"نقر على {image_name}"
                        self.update_status_display()
                        time.sleep(self.config['click_delay'])
                    else:
                        self.add_log(f"⚠️ فشل النقر على {image_name}", "warning")
                
                else:
                    self.add_log(f"⏭️ تخطي {image_name} - غير موجود بعد 3 محاولات", "warning")
                    time.sleep(1.5)
                
                current_step += 1
                progress = (current_step / total_steps) * 33
                self.update_progress(progress)
                
                if not self.is_running:
                    break
            
            self.add_log(f"✅ تم إكمال هجوم القائد {commander + 1}", "success")
            
            if commander < commanders_count - 1:
                self.add_log("⏳ انتظار 3 ثوان قبل القائد التالي...", "info")
                time.sleep(3.0)
        
        if self.is_running:
            self.add_log("⏳ انتظار دقيقتين قبل المرحلة التالية...", "info")
            time.sleep(self.config['phase_delay'])
    
    def execute_gifts_sequence(self):
        """تنفيذ مجموعة الهدايا"""
        if not self.is_running:
            return
            
        self.current_phase = "مجموعة الهدايا"
        self.current_step = "البحث عن الهدايا"
        self.update_status_display()
        
        self.add_log("🎁 فحص الهدايا المتاحة...", "info")
        
        result = self.find_image_on_screen("collect.png", 'gifts')
        
        if result:
            x, y, confidence = result
            self.add_log("🎉 تم العثور على هدية! جاري الجمع...", "success")
            self.mouse_click(x, y)
            self.last_action = "جمع هدية"
            time.sleep(self.config['click_delay'])
        else:
            self.add_log("📭 لا توجد هدايا متاحة حالياً", "info")
        
        self.update_progress(66)
    
    def execute_send_troops_sequence(self):
        """تنفيذ مجموعة إرسال الجنود"""
        if not self.is_running:
            return
            
        self.current_phase = "إرسال الجنود"
        self.update_status_display()
        
        self.add_log("👥 بدء إرسال الجنود إلى مملكة بيرموند...", "info")
        
        total_steps = len(self.image_groups['send_troops'])
        
        for i, image_name in enumerate(self.image_groups['send_troops']):
            if not self.is_running:
                break
                
            self.current_step = f"البحث عن: {image_name}"
            self.update_status_display()
            
            result = None
            for attempt in range(3):
                result = self.find_image_on_screen(image_name, 'send_troops')
                if result:
                    break
                time.sleep(0.5)
        
            if result:
                x, y, confidence = result
            
                if image_name == "watch-this.png":
                    self.add_log("👆👆 تنفيذ النقر المزدوج لـ click-twice...", "info")
                    self.double_mouse_click(x, y, 1.0)
                elif image_name == "click-twice.png":
                    self.add_log("🎬 تنفيذ النقر المزدوج لـ watch-this...", "info")
                    self.double_mouse_click(x, y, 1.0)
                else:
                    if self.mouse_click(x, y):
                        self.last_action = f"نقر على {image_name}"
                        self.update_status_display()
                        time.sleep(self.config['click_delay'])
            
            else:
                self.add_log(f"⏭️ تخطي {image_name} - غير موجود بعد 3 محاولات", "warning")
                time.sleep(1.5)
        
            progress = 66 + ((i + 1) / total_steps) * 34
            self.update_progress(progress)
        
            if not self.is_running:
                break
    
        if self.is_running:
            self.add_log("✅ تم إكمال إرسال الجنود", "success")
    
    def monitor_alerts(self):
        """مراقبة التحذيرات مع نظام الاستئناف التلقائي"""
        if not self.is_running:
            return False

        # التحقق من الإيقاف المؤقت
        if self.paused_for_alert:
            return self.handle_pause_state()

        # البحث عن zarwa أولاً
        zarwa_result = self.find_image_on_screen("zarwa.png", 'alerts')
        if zarwa_result:
            x, y, confidence = zarwa_result
        
            # التحقق من دقة أعلى لتجنب الإنذارات الكاذبة
            if confidence >= 0.85:
                self.add_log(f"🚨 تم اكتشاف zarwa! الثقة: {confidence:.2f}", "warning")
            
                # البحث عن zarwa-exit والنقر عليه
                exit_result = self.find_image_on_screen("zarwa-exit.png", 'alerts')
                if exit_result:
                    ex, ey, exit_confidence = exit_result
                    self.add_log(f"🎯 تم العثور على zarwa-exit! جاري النقر...", "success")
            
                    if self.mouse_click(ex, ey):
                        self.last_action = "نقر على zarwa-exit"
                        self.update_status_display()
                
                        # إرسال تحديث تليجرام
                        self.send_telegram_message(
                            f"✅ تم التعامل مع zarwa تلقائياً!\n"
                            f"تم النقر على zarwa-exit بنجاح\n"
                            f"دقة zarwa: {confidence:.2f}\n"
                            f"دقة zarwa-exit: {exit_confidence:.2f}\n"
                            f"🔄 البوت يكمل العمل تلقائياً",
                            "success"
                        )
                
                        time.sleep(3)
                        return False
                    else:
                        self.add_log("❌ فشل في النقر على zarwa-exit", "error")
                else:
                    self.add_log("❌ لم يتم العثور على zarwa-exit", "error")
            
                # إذا فشل في العثور على zarwa-exit أو النقر عليه، محاولة استئناف تلقائي
                self.add_log("🔄 محاولة استئناف تلقائي بعد 10 ثوان...", "warning")
                self.send_telegram_message(
                    f"⚠️ تحذير zarwa - فشل في العثور على زر الخروج\n"
                    f"الثقة: {confidence:.2f}\n"
                    f"🔄 سيتم المحاولة مرة أخرى خلال 10 ثوان",
                    "warning"
                )
            
                time.sleep(10)
                return False
            else:
                # إنذار كاذب محتمل
                self.add_log(f"⚠️ إنذار zarwa محتمل كاذب - ثقة منخفضة: {confidence:.2f}", "warning")

        # البحث عن zarwa2
        zarwa2_result = self.find_image_on_screen("zarwa2.png", 'alerts')
        if zarwa2_result:
            x, y, confidence = zarwa2_result
        
            # التحقق من دقة أعلى لتجنب الإنذارات الكاذبة
            if confidence >= 0.85:
                self.add_log(f"🚨 تم اكتشاف zarwa2! الثقة: {confidence:.2f}", "warning")
            
                # البحث عن zarwa2-exit والنقر عليه
                exit_result = self.find_image_on_screen("zarwa2-exit.png", 'alerts')
                if exit_result:
                    ex, ey, exit_confidence = exit_result
                    self.add_log(f"🎯 تم العثور على zarwa2-exit! جاري النقر...", "success")
            
                    if self.mouse_click(ex, ey):
                        self.last_action = "نقر على zarwa2-exit"
                        self.update_status_display()
                
                        # إرسال تحديث تليجرام
                        self.send_telegram_message(
                            f"✅ تم التعامل مع zarwa2 تلقائياً!\n"
                            f"تم النقر على zarwa2-exit بنجاح\n"
                            f"دقة zarwa2: {confidence:.2f}\n"
                            f"دقة zarwa2-exit: {exit_confidence:.2f}\n"
                            f"🔄 البوت يكمل العمل تلقائياً",
                            "success"
                        )
                
                        time.sleep(3)
                        return False
                    else:
                        self.add_log("❌ فشل في النقر على zarwa2-exit", "error")
                else:
                    self.add_log("❌ لم يتم العثور على zarwa2-exit", "error")
            
                # إذا فشل في العثور على zarwa2-exit أو النقر عليه، محاولة استئناف تلقائي
                self.add_log("🔄 محاولة استئناف تلقائي بعد 10 ثوان...", "warning")
                self.send_telegram_message(
                    f"⚠️ تحذير zarwa2 - فشل في العثور على زر الخروج\n"
                    f"الثقة: {confidence:.2f}\n"
                    f"🔄 سيتم المحاولة مرة أخرى خلال 10 ثوان",
                    "warning"
                )
            
                time.sleep(10)
                return False
            else:
                # إنذار كاذب محتمل
                self.add_log(f"⚠️ إنذار zarwa2 محتمل كاذب - ثقة منخفضة: {confidence:.2f}", "warning")

        return False

    def handle_pause_state(self):
        """التعامل مع حالة الإيقاف المؤقت"""
        if not self.pause_start_time:
            return False
    
        # حساب الوقت المنقضي
        elapsed_minutes = (time.time() - self.pause_start_time) / 60
        remaining_minutes = self.auto_resume_minutes - elapsed_minutes
    
        if remaining_minutes > 0:
            self.current_step = f"استئناف تلقائي خلال {remaining_minutes:.1f} دقيقة"
            self.update_status_display()
            time.sleep(30)  # فحص كل 30 ثانية
            return True
        else:
            # استئناف تلقائي
            self.resume_from_alert()
            return False

    def resume_from_alert(self):
        """استئناف البوت من الإيقاف المؤقت"""
        self.paused_for_alert = False
        self.pause_start_time = None
        self.current_phase = "مستأنف"
        self.current_step = "العودة للعمل"
        self.update_status_display()
    
        resume_message = "✅ تم استئناف البوت من الإيقاف المؤقت"
        self.add_log(resume_message, "success")
        self.send_telegram_message(resume_message, "success")

    def manual_resume(self):
        """استئناف يدوي من الواجهة"""
        if self.paused_for_alert:
            self.resume_from_alert()
            self.resume_button.config(state=tk.DISABLED)
        else:
            messagebox.showinfo("معلومات", "البوت غير متوقف مؤقتاً")
    
    def main_bot_loop(self):
        """الحلقة الرئيسية للبوت مع استئناف تلقائي"""
        try:
            while self.is_running:
                cycle_start_time = time.time()
            
                self.add_log(f"🔄 بدء الدورة رقم {self.completed_cycles + 1}", "info")
            
                # مراقبة التحذيرات مع استئناف تلقائي
                self.monitor_alerts()
            
                # تنفيذ مجموعة الهجوم
                if self.is_running:
                    self.execute_attack_sequence()
            
                # مراقبة التحذيرات
                self.monitor_alerts()
            
                # تنفيذ مجموعة الهدايا
                if self.is_running:
                    self.execute_gifts_sequence()
            
                # مراقبة التحذيرات
                self.monitor_alerts()
            
                # تنفيذ مجموعة إرسال الجنود
                if self.is_running:
                    self.execute_send_troops_sequence()
            
                # إكمال الدورة
                if self.is_running:
                    self.completed_cycles += 1
                    self.update_progress(100)
                
                    cycle_time = time.time() - cycle_start_time
                    self.add_log(f"✅ تم إكمال الدورة {self.completed_cycles} في {cycle_time:.1f} ثانية", "success")
                
                    # إرسال تحديث تليجرام
                    self.send_telegram_message(
                        f"تم إكمال الدورة رقم {self.completed_cycles} بنجاح!\n"
                        f"الوقت المستغرق: {cycle_time:.1f} ثانية\n"
                        f"🤖 الاستئناف التلقائي: مفعل",
                        "success"
                    )
                
                    self.last_action = f"إكمال الدورة {self.completed_cycles}"
                    self.update_status_display()
                
                    # انتظار قبل الدورة التالية
                    if self.is_running:
                        self.add_log(f"⏳ انتظار {self.config['cycle_delay']} ثانية قبل الدورة التالية...", "info")
                        time.sleep(self.config['cycle_delay'])
            
        except Exception as e:
            error_msg = f"خطأ في الحلقة الرئيسية: {str(e)}"
            self.add_log(error_msg, "error")
            self.send_telegram_message(f"خطأ حرج في البوت: {error_msg}", "error")
    
        finally:
            if self.is_running:
                self.stop_bot()
    
    def start_bot(self):
        """بدء تشغيل البوت"""
        if self.is_running:
            return
        
        # التحقق من تحميل اللعبة في المتصفح المدمج
        if self.config['embedded_browser'] and not self.game_loaded:
            messagebox.showwarning("تحذير", "يرجى تحميل اللعبة أولاً قبل تشغيل البوت")
            return
        
        # حفظ الإعدادات
        self.save_settings()
        
        # التحقق من الصور
        missing_images = []
        for group_name, image_list in self.image_groups.items():
            for image_name in image_list:
                if group_name not in self.images or image_name not in self.images[group_name]:
                    missing_images.append(image_name)
        
        if missing_images:
            messagebox.showerror(
                "خطأ", 
                f"الصور التالية مفقودة:\n" + "\n".join(missing_images[:10]) + 
                ("\n..." if len(missing_images) > 10 else "")
            )
            return
        
        self.add_log("🚀 بدء تشغيل البوت...", "info")
        
        # إرسال إشعار بدء التشغيل
        self.send_telegram_message(
            f"تم بدء تشغيل البوت!\n"
            f"عدد القادة: {self.config['commanders_count']}\n"
            f"رابط اللعبة: {self.config['game_url']}\n"
            f"المتصفح المدمج: {'نعم' if self.config['embedded_browser'] else 'لا'}\n"
            f"نظام zarwa الذكي: مفعل ✅",
            "success"
        )
        
        # تحديث واجهة المستخدم
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.current_phase = "التحضير"
        self.current_step = "إعداد المتصفح"
        self.update_status_display()
        
        # بدء البوت في thread منفصل
        def start_bot_thread():
            if self.setup_browser():
                self.main_bot_loop()
            else:
                self.add_log("❌ فشل في إعداد المتصفح", "error")
                self.stop_bot()
        
        bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
        bot_thread.start()
    
    def stop_bot(self):
        """إيقاف البوت"""
        if not self.is_running:
            return
        
        self.add_log("⏹️ جاري إيقاف البوت...", "info")
        
        self.is_running = False
        self.paused_for_alert = False
        self.current_phase = "متوقف"
        self.current_step = ""
        
        # إغلاق المتصفح المنفصل فقط (ليس المدمج)
        if self.driver and self.driver != self.embedded_driver:
            try:
                self.driver.quit()
                self.driver = None
                self.add_log("✅ تم إغلاق المتصفح المنفصل", "success")
            except Exception as e:
                self.add_log(f"خطأ في إغلاق المتصفح: {str(e)}", "error")
        
        # تحديث واجهة المستخدم
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status_display()
        self.update_progress(0)
        
        # إرسال إشعار الإيقاف
        self.send_telegram_message(
            f"تم إيقاف البوت\n"
            f"الدورات المكتملة: {self.completed_cycles}\n"
            f"الأخطاء: {len(self.errors)}",
            "info"
        )
        
        self.add_log("✅ تم إيقاف البوت بنجاح", "success")
    
    def run(self):
        """تشغيل التطبيق"""
        try:
            self.add_log("🎮 مرحباً بك في بوت GoodGame Empire!", "success")
            self.add_log("👨‍💻 المطور: Ahmed.R", "info")
            self.add_log("📋 تأكد من وضع جميع الصور في مجلد objects", "info")
            self.add_log("🌐 اختر تشغيل اللعبة داخل البرنامج أو في متصفح منفصل", "info")
            self.add_log("⚙️ قم بإعداد البوت ثم اضغط على تشغيل", "info")
            self.add_log("🖱️ يمكنك اختبار النقر باستخدام زر 'اختبار النقر'", "info")
            self.add_log("🚨 نظام zarwa الذكي مفعل - سيتم التعامل مع التحذيرات تلقائياً", "info")
            self.add_log("💾 الإعدادات تُحفظ تلقائياً", "info")
            
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
            
        except Exception as e:
            self.add_log(f"خطأ في تشغيل التطبيق: {str(e)}", "error")
    
    def on_closing(self):
        """عند إغلاق التطبيق"""
        if self.is_running:
            if messagebox.askokcancel("تأكيد الإغلاق", "البوت يعمل حالياً. هل تريد إيقافه وإغلاق التطبيق؟"):
                self.stop_bot()
                time.sleep(2)
                
                # إغلاق المتصفح المدمج
                if self.embedded_driver:
                    try:
                        self.embedded_driver.quit()
                    except:
                        pass
                
                self.root.destroy()
        else:
            # حفظ الإعدادات عند الإغلاق
            self.save_settings()
            
            # إغلاق المتصفح المدمج
            if self.embedded_driver:
                try:
                    self.embedded_driver.quit()
                except:
                    pass
            
            self.root.destroy()

def main():
    """الدالة الرئيسية"""
    try:
        # التحقق من وجود مجلد objects
        if not os.path.exists("objects"):
            os.makedirs("objects")
            print("تم إنشاء مجلد objects - يرجى وضع الصور فيه")
        
        # إنشاء وتشغيل البوت
        bot = GoodGameEmpireBot()
        bot.run()
        
    except Exception as e:
        print(f"خطأ في تشغيل البوت: {str(e)}")
        input("اضغط Enter للخروج...")

if __name__ == "__main__":
    main()
