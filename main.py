#auto-py-to-exe
import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageTk, ImageGrab
from cryptography.fernet import Fernet
import hashlib
import threading
import base64
import io
import uuid
import time
from tkinterdnd2 import TkinterDnD, DND_FILES
import stat

# ===================== 常數設定 =====================
CONFIG_FILE = "config.json"
NOTES_DIR = "notes"
IMAGES_DIR = "images"
SHORTCUTS_DIR = "shortcuts"  # 新增：儲存捷徑資訊的目錄
KEY_FILE = "key.key"
LOGO_PATH = "assets/logo.png"
DEFAULT_PASSWORD = "1234"
MAX_LOGIN_ATTEMPTS = 3  # 最大登入嘗試次數
LOCKOUT_TIME = 3600  # 一小時(秒)
LOCKOUT_FILE = "lockout.json"
ENABLE_EMAIL_NOTIFICATION = True  # 新增：控制是否開啟傳送郵件功能


# 主題設定
THEMES = {
    "dark": {
        "bg": "#2d2d2d",
        "fg": "#e0e0e0",
        "select_bg": "#4a98f7",
        "select_fg": "white",
        "button_bg": "#3d3d3d",
        "button_fg": "#e0e0e0",
        "button_active_bg": "#4d4d4d",
        "button_active_fg": "white",
        "entry_bg": "#3d3d3d",
        "entry_fg": "white",
        "highlight": "#4a98f7",
        "menu_bg": "#2d2d2d",
        "menu_fg": "#e0e0e0",
        "error_bg": "#4a1a1a",  # 深紅色背景
        "error_fg": "#ffcccc",  # 淺紅色文字
        "error_highlight": "#ff6666"  # 邊框高亮  
    },
    "modern": {
        "bg": "#f0f2f5",
        "fg": "#333333",
        "select_bg": "#6c5ce7",
        "select_fg": "white",
        "button_bg": "#6c5ce7",
        "button_fg": "white",
        "button_active_bg": "#5d4aec",
        "button_active_fg": "white",
        "entry_bg": "white",
        "entry_fg": "#333333",
        "highlight": "#6c5ce7",
        "menu_bg": "#f0f2f5",
        "menu_fg": "#333333",
        "error_bg": "#ffeeee",  # 淺紅色背景
        "error_fg": "#cc0000",  # 深紅色文字
        "error_highlight": "#ff6666"  # 邊框高亮
    },
    "pink": {  # 新增淡粉紅主題
        "bg": "#fff0f5",
        "fg": "#5a3a4a",
        "select_bg": "#ff85a2",
        "select_fg": "white",
        "button_bg": "#ff85a2",
        "button_fg": "white",
        "button_active_bg": "#ff6b8b",
        "button_active_fg": "white",
        "entry_bg": "#fff0f5",
        "entry_fg": "#5a3a4a",
        "highlight": "#ff85a2",
        "menu_bg": "#fff0f5",
        "menu_fg": "#5a3a4a",
        "error_bg": "#ffebee",
        "error_fg": "#c62828",
        "error_highlight": "#ff6b8b"
    },
    "yellow": {  # 新增淡黃主題
        "bg": "#fffde7",
        "fg": "#5a4a3a",
        "select_bg": "#ffd54f",
        "select_fg": "white",
        "button_bg": "#ffd54f",
        "button_fg": "white",
        "button_active_bg": "#ffc107",
        "button_active_fg": "white",
        "entry_bg": "#fffde7",
        "entry_fg": "#5a4a3a",
        "highlight": "#ffd54f",
        "menu_bg": "#fffde7",
        "menu_fg": "#5a4a3a",
        "error_bg": "#fff8e1",
        "error_fg": "#e65100",
        "error_highlight": "#ffc107"
    }
}

DEFAULT_THEME = "modern"

# ===================== 加解密工具 =====================
def generate_key():
    """生成加密金鑰並儲存到檔案"""
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as f:
        f.write(key)

def load_key():
    """載入加密金鑰，若不存在則生成"""
    if not os.path.exists(KEY_FILE):
        generate_key()
    with open(KEY_FILE, 'rb') as f:
        return f.read()

def encrypt(text):
    """加密文字"""
    try:
        fernet = Fernet(load_key())
        return fernet.encrypt(text.encode()).decode()
    except Exception as e:
        print(f"加密失敗: {e}")
        return None

def decrypt(token):
    """解密文字"""
    try:
        fernet = Fernet(load_key())
        return fernet.decrypt(token.encode()).decode()
    except Exception as e:
        print(f"解密失敗: {e}")
        return None

# ===================== 密碼處理 =====================
def hash_password(password):
    """將密碼進行 SHA-256 雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()

# 修改 load_config 函數，新增解鎖密碼的雜湊值
def load_config():
    """載入設定檔，若不存在則建立預設設定"""
    if not os.path.exists(CONFIG_FILE):
        default = {
            "password": hash_password(DEFAULT_PASSWORD), 
            "unlock_password_hash": 'c0b19ffd9040685d2953a9ba305cffdd02ebf4184a190258a12a693cbae8c1a9',  # 儲存解鎖密碼的雜湊值
            "theme": DEFAULT_THEME,
            "font": "標楷體",
            "font_size": 20,
            "note_order": []  # 預設空的筆記順序
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default, f)
        return default
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """儲存設定檔"""
    config['note_order'] = list(app.notes.keys())  # 儲存筆記順序
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

# ===================== 圖片處理 =====================
def save_image_to_file(image_data, filename=None):
    """將圖片儲存到檔案並返回檔案名"""
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    
    # 生成唯一檔案名
    if not filename:
        filename = str(uuid.uuid4()) + ".png"
    filepath = os.path.join(IMAGES_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    return filename

def load_image_from_file(filename):
    """從檔案載入圖片"""
    filepath = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None

def delete_image_file(filename):
    """刪除圖片檔案"""
    try:
        filepath = os.path.join(IMAGES_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        print(f"刪除圖片檔案失敗: {e}")
    return False

def resize_image(image_data, max_width=None):
    """調整圖片大小"""
    try:
        image = Image.open(io.BytesIO(image_data))
        if max_width and image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.LANCZOS)
        
        # 轉換為bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except Exception as e:
        print(f"調整圖片大小失敗: {e}")
        return image_data

# ===================== 筆記管理 =====================
def load_notes(config):
    """載入所有筆記"""
    notes = {}
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)
    for fname in os.listdir(NOTES_DIR):
        file_path = os.path.join(NOTES_DIR, fname)
        if os.path.isfile(file_path) and fname.endswith('.txt'):
            with open(file_path, 'r') as f:
                try:
                    content = decrypt(f.read())
                    notes[fname[:-4]] = content if content else "[解密失敗]"
                except Exception as e:
                    print(f"載入筆記失敗: {e}")
                    notes[fname[:-4]] = "[解密失敗]"
    
    # 按設定檔中的順序排列筆記
    note_order = config.get('note_order', [])
    ordered_notes = {title: notes[title] for title in note_order if title in notes}
    unordered_notes = {title: notes[title] for title in notes if title not in note_order}
    ordered_notes.update(unordered_notes)  # 將未排序的筆記追加到後面
    return ordered_notes

def save_note(title, content):
    """儲存筆記"""
    encrypted = encrypt(content)
    if encrypted:
        with open(os.path.join(NOTES_DIR, title + ".txt"), 'w') as f:
            f.write(encrypted)

def delete_note(title):
    """刪除筆記"""
    try:
        os.remove(os.path.join(NOTES_DIR, title + ".txt"))
    except FileNotFoundError:
        print(f"筆記 {title} 不存在，無法刪除。")

# ===================== 主視窗 =====================
class NotesApp:
    def __init__(self, master):
        """初始化應用程式"""
        self.master = master
        self.master.withdraw()  # 隱藏主視窗
        self.master.title("🔐 沒人看的到的筆記")
        self.config = load_config()
        self.login_attempts = 0
        self.lockout_until = 0
        self.load_lockout_status()

        # 設定視窗初始大小為螢幕的80%
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        self.master.geometry(f"{window_width}x{window_height}+{int((screen_width - window_width)/2)}+{int((screen_height - window_height)/2)}")

        self.notes = load_notes(self.config)  # 傳遞 config
        self.current_note = None
        self.image_references = {}  # 用於保存圖片參考，防止被垃圾回收
        self.image_tags = {}  # 用於保存圖片標籤
        self.shortcut_references = {}  # 用於保存捷徑參考
        self.undo_stack = []  # 初始化 undo 堆疊
        self.redo_stack = []  # 初始化 redo 堆疊

        # 確保 shortcuts 目錄存在
        if not os.path.exists(SHORTCUTS_DIR):
            os.makedirs(SHORTCUTS_DIR)
        hide_folder(SHORTCUTS_DIR)  # 隱藏 shortcuts 目錄

        if not os.path.exists(NOTES_DIR):
            os.makedirs(NOTES_DIR)
        hide_folder(NOTES_DIR)  # 隱藏 notes 目錄

        if not os.path.exists(IMAGES_DIR):
            os.makedirs(IMAGES_DIR)
        hide_folder(IMAGES_DIR)  # 隱藏 images 目錄

        self.init_login()  # 初始化登入畫面

    def init_login(self):
        """初始化登入畫面"""
        login_window = tk.Toplevel(self.master)
        login_window.title("登入")
        login_window.geometry("400x450")  # 增加高度以容納 Logo
        login_window.resizable(False, False)
        login_window.grab_set()

        # 當登入視窗被關閉時，退出程式
        def on_close():
            self.master.destroy() 

        login_window.protocol("WM_DELETE_WINDOW", on_close)

        # 添加背景框架
        main_frame = tk.Frame(
            login_window, 
            bg=self.get_theme_color("bg"),
            padx=20,
            pady=20
        )
        main_frame.pack(fill="both", expand=True)

        # 顯示 Logo
        if os.path.exists(LOGO_PATH):
            logo_img = Image.open(LOGO_PATH).resize((128, 128), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            tk.Label(
                main_frame,
                image=self.logo,
                bg=self.get_theme_color("bg")
            ).pack(pady=10)

        # 標題
        tk.Label(
            main_frame,
            text="沒人看的到的筆記登入",
            font=("標楷體", 16, "bold"),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("highlight"),
            pady=10
        ).pack()

        # 密碼輸入框
        input_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        input_frame.pack(pady=10)

        tk.Label(
            input_frame,
            text="請輸入密碼：\n(預設密碼: 1234)",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg"),
            pady=10
        ).pack()

        password_entry = tk.Entry(
            input_frame, 
            show="*", 
            font=("標楷體", 12),
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("entry_fg"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight")
        )
        password_entry.pack(pady=5, ipady=5)
        self.password_entry = password_entry

        # 按鈕框架
        btn_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        btn_frame.pack(pady=10)

        def confirm_password():
            if app.check_lockout():
                # 如果輸入的密碼雜湊值匹配解鎖密碼的雜湊值，則立即解鎖
                if hash_password(password_entry.get()) == app.config.get("unlock_password_hash"):
                    app.lockout_until = 0
                    app.save_lockout_status()
                    self.show_success("成功", "已解除鎖定！", parent=login_window)
                    return
                return  # 如果處於鎖定狀態且不是解鎖密碼，直接返回

            pw = password_entry.get()
            if not pw or hash_password(pw) != app.config['password']:
                app.login_attempts += 1
                if app.login_attempts >= MAX_LOGIN_ATTEMPTS:
                    app.lockout_until = time.time() + LOCKOUT_TIME
                    app.save_lockout_status()
                    app.send_email_notification()
                    self.show_error("錯誤", 
                        "密碼錯誤次數過多，帳戶已鎖定一小時\n"
                        "若有問題或想提前解鎖請聯繫我\n"
                        "0989982760", 
                        parent=login_window)
                else:
                    self.show_error("錯誤", 
                        f"密碼錯誤！剩餘嘗試次數: {MAX_LOGIN_ATTEMPTS - app.login_attempts}", 
                        parent=login_window)
            else:
                app.login_attempts = 0
                login_window.destroy()
                app.master.deiconify()
                app.init_ui()

        # 登入按鈕
        login_btn = tk.Button(
            btn_frame,
            text="登入",
            font=("標楷體", 15, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground=self.get_theme_color("button_active_fg"),
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=confirm_password
        )
        login_btn.pack()

        # 添加懸停效果
        def on_enter(e):
            login_btn.config(bg=self.get_theme_color("button_active_bg"))

        def on_leave(e):
            login_btn.config(bg=self.get_theme_color("highlight"))

        login_btn.bind("<Enter>", on_enter)
        login_btn.bind("<Leave>", on_leave)

        # 綁定Enter鍵
        password_entry.bind("<Return>", lambda e: confirm_password())
        password_entry.focus_set()

    def init_ui(self):
        """初始化主介面"""
        # 確保筆記資料已載入
        if not self.notes:
            self.notes = load_notes(self.config)
            
        # 清除舊的框架
        for widget in self.master.winfo_children():
            widget.destroy()
        
        # 主區塊 - 使用 grid 佈局
        self.frame = tk.Frame(self.master, bg=self.get_theme_color("bg"))
        self.frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置 grid 權重
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        
        # 選單區域 (保持不變)
        menu_bar = tk.Menu(self.master, tearoff=0, bg=self.get_theme_color("menu_bg"), fg=self.get_theme_color("menu_fg"))
        self.master.config(menu=menu_bar)
        
        # 檔案選單
        file_menu = tk.Menu(menu_bar, tearoff=0, bg=self.get_theme_color("menu_bg"), fg=self.get_theme_color("menu_fg"))
        menu_bar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="新增筆記", command=self.new_note, accelerator="Ctrl+N")
        file_menu.add_command(label="刪除筆記", command=self.delete_current, accelerator="Ctrl+D")
        file_menu.add_command(label="儲存筆記", command=self.save_current, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="插入圖片", command=self.insert_image, accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.master.quit, accelerator="Ctrl+Q")
        
        # 設定選單
        settings_menu = tk.Menu(menu_bar, tearoff=0, bg=self.get_theme_color("menu_bg"), fg=self.get_theme_color("menu_fg"))
        menu_bar.add_cascade(label="設定", menu=settings_menu)
        settings_menu.add_command(label="更改密碼", command=self.change_password)
        settings_menu.add_command(label="切換主題", command=self.toggle_theme)
        settings_menu.add_separator()
        settings_menu.add_command(label="清理未使用圖片和捷徑", command=self.delete_unused_images)
        settings_menu.add_separator()
        email_menu = tk.Menu(settings_menu, tearoff=0, bg=self.get_theme_color("menu_bg"), fg=self.get_theme_color("menu_fg"))
        settings_menu.add_cascade(label="電子郵件設定", menu=email_menu)
        email_menu.add_command(label="設定通知郵箱", command=self.set_notification_email)

        
        # 字體子選單
        font_menu = tk.Menu(settings_menu, tearoff=0, bg=self.get_theme_color("menu_bg"), fg=self.get_theme_color("menu_fg"))
        settings_menu.add_cascade(label="字體設定", menu=font_menu)
        font_menu.add_command(label="選擇字體", command=self.select_font)
        font_menu.add_command(label="選擇文字大小", command=self.select_font_size)

        # 添加復原和重做按鈕到選單欄
        menu_bar.add_command(label="⬅上一步", command=self.undo)
        menu_bar.add_command(label="⮕ 下一步", command=self.redo)
        
        # 左側清單區域 - 使用 grid
        list_frame = tk.Frame(
            self.frame, 
            bg=self.get_theme_color("bg"),
            padx=10,
            pady=10
        )
        list_frame.grid(row=0, column=0, sticky="ns")
        
        # 清單標題卡片
        title_card = tk.Frame(
            list_frame,
            bg=self.get_theme_color("highlight"),
            padx=10,
            pady=5,
            relief="flat",
            bd=0
        )
        title_card.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            title_card,
            text="筆記清單",
            font=("標楷體", 14, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white"
        ).pack()
        
        # 清單滾動條
        list_scroll = tk.Scrollbar(list_frame)
        list_scroll.pack(side="right", fill="y")
        
        # 筆記清單
        self.listbox = tk.Listbox(
            list_frame,
            width=25,
            height=25,
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("fg"),
            selectbackground=self.get_theme_color("select_bg"),
            selectforeground=self.get_theme_color("select_fg"),
            font=("標楷體", 20),
            yscrollcommand=list_scroll.set,
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight")
        )
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.load_selected_note)
        self.listbox.bind("<Button-3>", self.show_list_context_menu)  # 綁定右鍵選單
        self.listbox.bind("<Button-1>", self.start_drag)
        self.listbox.bind("<B1-Motion>", self.do_drag)
        self.listbox.bind("<ButtonRelease-1>", self.end_drag)
        list_scroll.config(command=self.listbox.yview)
        
        # 右側編輯區域 - 使用 grid
        editor_frame = tk.Frame(
            self.frame, 
            bg=self.get_theme_color("bg"),
            padx=10,
            pady=10
        )
        editor_frame.grid(row=0, column=1, sticky="nsew")
        
        # 配置框架權重
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        
        # 編輯區標題卡片
        editor_title_card = tk.Frame(
            editor_frame,
            bg=self.get_theme_color("highlight"),
            padx=10,
            pady=5,
            relief="flat",
            bd=0
        )
        editor_title_card.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            editor_title_card,
            text="筆記內容",
            font=("標楷體", 14, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white"
        ).pack()
        
        # 編輯區滾動條
        text_scroll = tk.Scrollbar(editor_frame, width=20)  # 將寬度設為 20
        text_scroll.pack(side="right", fill="y")
        
        # 編輯區
        self.text = tk.Text(
            editor_frame,
            wrap="word",
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("fg"),
            insertbackground=self.get_theme_color("fg"),
            font=(self.config.get("font", "標楷體"), self.config.get("font_size", 12)),
            yscrollcommand=text_scroll.set,
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight"),
            padx=10,
            pady=10
        )
        self.text.pack(fill="both", expand=True)
        text_scroll.config(command=self.text.yview)
        self.text.bind("<Button-3>", self.show_text_context_menu)  # 綁定右鍵選單
        self.text.bind("<Key>", self.record_state)  # 綁定按鍵事件以記錄狀態
        
        # 啟用拖放功能
        self.text.drop_target_register(DND_FILES)
        self.text.dnd_bind('<<Drop>>', self.handle_dropped_shortcut)
        
        # 底部按鈕區域 - 使用 grid
        btn_frame = tk.Frame(
            self.master, 
            bg=self.get_theme_color("bg"),
            padx=10,
            pady=10
        )
        btn_frame.grid(row=1, column=0, sticky="ew", columnspan=2)
        
        # 配置底部按鈕區域權重
        self.master.grid_rowconfigure(1, weight=0)  # 固定高度
        self.master.grid_columnconfigure(0, weight=1)
        
        # 按鈕樣式
        btn_style = {
            "font": ("標楷體", 12, "bold"),
            "bg": self.get_theme_color("highlight"),
            "fg": "white",
            "activebackground": self.get_theme_color("button_active_bg"),
            "activeforeground": "white",
            "relief": "flat",
            "bd": 0,
            "width": 15,
            "padx": 10,
            "pady": 8
        }
        
        # 按鈕
        buttons = [
            ("新增 (Ctrl+N)", self.new_note),
            ("刪除 (Ctrl+D)", self.delete_current),
            ("儲存 (Ctrl+S)", self.save_current),
            ("插入圖片 (Ctrl+I)", self.insert_image),
            ("更改密碼", self.change_password),
            ("切換主題", self.toggle_theme)
        ]
        
        for text, command in buttons:
            btn = tk.Button(btn_frame, text=text, command=command, **btn_style)
            btn.pack(side="left", padx=5)
            
            # 添加懸停效果
            def on_enter(e, btn=btn):
                btn.config(bg=self.get_theme_color("button_active_bg"))
            
            def on_leave(e, btn=btn):
                btn.config(bg=self.get_theme_color("highlight"))
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # 快捷鍵提示 - 使用 grid
        shortcut_frame = tk.Frame(
            self.master,
            bg=self.get_theme_color("bg"),
            padx=10,
            pady=5
        )
        shortcut_frame.grid(row=2, column=0, sticky="ew", columnspan=2)
        
        # 快捷鍵提示
        tk.Label(
            shortcut_frame,
            text="常用快捷鍵: Ctrl+S=儲存 |  Ctrl+Z=上一步 |  Ctrl+Sfhit+Z=下一步 |  Ctrl+Q=退出",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg")
        ).pack(side="left")
        
        # 綁定快捷鍵
        self.master.bind("<Control-n>", lambda e: self.new_note())
        self.master.bind("<Control-s>", lambda e: self.save_current())
        self.master.bind("<Control-d>", lambda e: self.delete_current())
        self.master.bind("<Control-i>", lambda e: self.insert_image())
        self.master.bind("<Control-q>", lambda e: self.master.quit())
        self.master.bind("<Control-z>", lambda e: self.undo())  # 綁定 Ctrl+Z
        self.master.bind("<Control-Shift-Z>", lambda e: self.redo())  # 綁定 Ctrl+Shift+Z
        
        self.refresh_list()
        self.apply_theme()

    def get_theme_color(self, element):
        """取得主題顏色"""
        return THEMES[self.config["theme"]].get(element, "white")

    def select_font(self):
        """選擇字體"""
        font = simpledialog.askstring("選擇字體", "請輸入字體名稱（例如 Arial）：")
        if font:
            try:
                self.text.config(font=(font, self.config.get("font_size", 12)))
                self.config["font"] = font
                save_config(self.config)
            except Exception as e:
                self.show_error("錯誤", f"無法套用字體：{e}")

    def select_font_size(self):
        """選擇文字大小"""
        size = simpledialog.askinteger("選擇文字大小", "請輸入文字大小（例如 12）：")
        if size:
            try:
                current_font = self.config.get("font", "標楷體")
                self.text.config(font=(current_font, size))
                self.listbox.config(font=(current_font, size))  # 設定 Listbox 的字體大小
                self.config["font_size"] = size
                save_config(self.config)
                
                # 強制重新計算佈局
                self.master.update_idletasks()
                self.master.geometry("")  # 重置視窗大小
            except Exception as e:
                self.show_error("錯誤", f"無法套用文字大小：{e}")

    def refresh_list(self):
        """刷新筆記清單"""
        self.listbox.delete(0, tk.END)
        for title in self.notes.keys():
            self.listbox.insert(tk.END, title)

    def load_selected_note(self, event):
        """載入選中的筆記"""
        sel = self.listbox.curselection()
        if sel:
            title = self.listbox.get(sel)
            self.current_note = title
            self.text.delete(1.0, tk.END)
            
            # 先載入純文字內容
            content = self.notes[title]
            self.text.insert(tk.END, content)
            
            # 檢查是否有圖片或捷徑標記並載入
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('IMAGE::'):
                    img_name = line[7:]
                    self.insert_image_at_position(img_name, f"{i+1}.0")
                elif line.startswith('SHORTCUT::'):
                    shortcut_id = line[10:]
                    shortcut_file = os.path.join(SHORTCUTS_DIR, shortcut_id + '.txt')
                    if os.path.exists(shortcut_file):
                        with open(shortcut_file, 'r') as f:
                            filepath = f.read().strip()
                            self.insert_shortcut_at_position(shortcut_id, filepath, f"{i+1}.0")

    def save_current(self):
        """儲存當前筆記"""
        if self.current_note:
            content = self.text.get(1.0, tk.END).strip()
            self.notes[self.current_note] = content
            save_note(self.current_note, content)
            self.show_success("已儲存", f"{self.current_note} 已儲存。")

    def new_note(self):
        """新增筆記"""
        new_note_window = tk.Toplevel(self.master)
        new_note_window.title("新增筆記")
        new_note_window.geometry("400x300")
        new_note_window.resizable(False, False)
        new_note_window.grab_set()
        
        main_frame = tk.Frame(
            new_note_window, 
            bg=self.get_theme_color("bg"),
            padx=20,
            pady=20
        )
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(
            main_frame,
            text="新增筆記",
            font=("標楷體", 14, "bold"),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("highlight"),
            pady=10
        ).pack()
        
        tk.Label(
            main_frame,
            text="請輸入筆記標題：",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg"),
            pady=5
        ).pack()
        
        title_entry = tk.Entry(
            main_frame, 
            font=("標楷體", 12),
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("entry_fg"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight")
        )
        title_entry.pack(pady=5, ipady=5)
        
        btn_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        btn_frame.pack(pady=10)
        
        def confirm_title():
            title = title_entry.get()
            if not title:
                self.show_error("錯誤", "標題不能為空！", parent=new_note_window)
                return
            if title in self.notes:
                self.show_error("錯誤", "筆記已存在！", parent=new_note_window)
                return
            self.notes[title] = ""
            self.current_note = title
            self.refresh_list()
            self.listbox.selection_set(tk.END)
            self.text.delete(1.0, tk.END)
            new_note_window.destroy()
        
        confirm_btn = tk.Button(
            btn_frame,
            text="確認",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=confirm_title
        )
        confirm_btn.pack()
        
        # 添加懸停效果
        def on_enter(e):
            confirm_btn.config(bg=self.get_theme_color("button_active_bg"))
        
        def on_leave(e):
            confirm_btn.config(bg=self.get_theme_color("highlight"))
        
        confirm_btn.bind("<Enter>", on_enter)
        confirm_btn.bind("<Leave>", on_leave)
        
        # 綁定Enter鍵
        title_entry.bind("<Return>", lambda e: confirm_title())
        title_entry.focus_set()

    def delete_current(self):
        """刪除當前筆記"""
        if self.current_note:
            if self.show_confirm("確認", f"確定刪除 {self.current_note}？"):
                # 刪除所有相關圖片和捷徑
                content = self.notes[self.current_note]
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('IMAGE::'):
                        img_name = line[7:]
                        delete_image_file(img_name)
                    elif line.startswith('SHORTCUT::'):
                        shortcut_id = line[10:]
                        shortcut_file = os.path.join(SHORTCUTS_DIR, shortcut_id + '.txt')
                        if os.path.exists(shortcut_file):
                            os.remove(shortcut_file)
                
                delete_note(self.current_note)
                del self.notes[self.current_note]
                self.current_note = None
                self.text.delete(1.0, tk.END)
                self.refresh_list()

    def change_password(self):
        """更改密碼"""
        change_pw_window = tk.Toplevel(self.master)
        change_pw_window.title("更改密碼")
        change_pw_window.geometry("400x300")
        change_pw_window.resizable(False, False)
        change_pw_window.grab_set()
        
        main_frame = tk.Frame(
            change_pw_window, 
            bg=self.get_theme_color("bg"),
            padx=20,
            pady=20
        )
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(
            main_frame,
            text="更改密碼",
            font=("標楷體", 14, "bold"),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("highlight"),
            pady=10
        ).pack()
        
        # 新密碼輸入框
        input_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        input_frame.pack(pady=5)
        
        tk.Label(
            input_frame,
            text="請輸入新密碼：",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg")
        ).pack()
        
        new_pw_entry = tk.Entry(
            input_frame, 
            show="*", 
            font=("標楷體", 12),
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("entry_fg"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight")
        )
        new_pw_entry.pack(pady=5, ipady=5)
        
        # 確認密碼輸入框
        tk.Label(
            input_frame,
            text="再次輸入新密碼：",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg")
        ).pack()
        
        confirm_pw_entry = tk.Entry(
            input_frame, 
            show="*", 
            font=("標楷體", 12),
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("entry_fg"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight")
        )
        confirm_pw_entry.pack(pady=5, ipady=5)
        
        # 按鈕框架
        btn_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        btn_frame.pack(pady=10)
        
        def confirm_new_password():
            new_pw = new_pw_entry.get()
            confirm_pw = confirm_pw_entry.get()
            if not new_pw or not confirm_pw:
                self.show_error("錯誤", "密碼不能為空！", parent=change_pw_window)
                return
            if new_pw != confirm_pw:
                self.show_error("錯誤", "兩次密碼輸入不一致！", parent=change_pw_window)
                return
            self.config['password'] = hash_password(new_pw)
            save_config(self.config)
            self.show_success("成功", "密碼已更改", parent=change_pw_window)
            change_pw_window.destroy()
        
        confirm_btn = tk.Button(
            btn_frame,
            text="確認",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=confirm_new_password
        )
        confirm_btn.pack()
        
        # 添加懸停效果
        def on_enter(e):
            confirm_btn.config(bg=self.get_theme_color("button_active_bg"))
        
        def on_leave(e):
            confirm_btn.config(bg=self.get_theme_color("highlight"))
        
        confirm_btn.bind("<Enter>", on_enter)
        confirm_btn.bind("<Leave>", on_leave)
        
        # 綁定Enter鍵
        new_pw_entry.bind("<Return>", lambda e: confirm_new_password())
        confirm_pw_entry.bind("<Return>", lambda e: confirm_new_password())
        new_pw_entry.focus_set()

    def toggle_theme(self):
        """顯示主題選擇對話框"""
        theme_window = tk.Toplevel(self.master)
        theme_window.title("選擇主題")
        theme_window.geometry("500x400")
        theme_window.resizable(False, False)
        theme_window.grab_set()
        
        # 將窗口顯示在螢幕中央
        theme_window.update_idletasks()
        window_width = theme_window.winfo_width()
        window_height = theme_window.winfo_height()
        screen_width = theme_window.winfo_screenwidth()
        screen_height = theme_window.winfo_screenheight()

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        theme_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 主框架
        main_frame = tk.Frame(
            theme_window,
            bg=self.get_theme_color("bg"),
            padx=20,
            pady=20,
            relief="solid",
            bd=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightthickness=1
        )
        main_frame.pack(fill="both", expand=True)
        
        # 標題
        tk.Label(
            main_frame,
            text="請選擇主題",
            font=("標楷體", 18, "bold"),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("highlight"),
            pady=10
        ).pack()
        
        # 主題預覽框架
        preview_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        preview_frame.pack(fill="both", expand=True, pady=10)
        
        # 創建主題按鈕
        themes = [
            ("白晝", "modern"),
            ("深色", "dark"),
            ("淡粉", "pink"),
            ("淡黃", "yellow")
        ]
        
        for theme_name, theme_key in themes:
            btn = tk.Button(
                preview_frame,
                text=theme_name,
                font=("標楷體", 14),
                bg=THEMES[theme_key]["highlight"],
                fg="white",
                activebackground=THEMES[theme_key]["button_active_bg"],
                activeforeground="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=10,
                width=15,
                command=lambda key=theme_key: self.apply_selected_theme(key, theme_window)
            )
            btn.pack(pady=5)
            
            # 添加懸停效果
            def on_enter(e, btn=btn, key=theme_key):
                btn.config(bg=THEMES[key]["button_active_bg"])
            
            def on_leave(e, btn=btn, key=theme_key):
                btn.config(bg=THEMES[key]["highlight"])
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # 綁定ESC鍵關閉窗口
        theme_window.bind("<Escape>", lambda e: theme_window.destroy())

    def apply_selected_theme(self, theme_key, window):
        """應用選擇的主題"""
        self.config['theme'] = theme_key
        save_config(self.config)
        self.apply_theme()
        window.destroy()
        self.show_success("主題已切換", f"已切換至 {theme_key} 主題")

    def apply_theme(self):
        """套用主題（完整且正確版，切主題時同步所有元件）"""
        theme = self.config['theme']
        colors = THEMES.get(theme, THEMES["modern"])

        # 更新主視窗
        self.master.config(bg=colors["bg"])

        # 更新大Frame
        if hasattr(self, 'frame'):
            self.frame.config(bg=colors["bg"])
            
            # 更新所有子框架的背景色
            for widget in self.frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.config(bg=colors["bg"])
                    
                    # 更新標題卡片
                    for subwidget in widget.winfo_children():
                        if isinstance(subwidget, tk.Frame):
                            subwidget.config(bg=colors["highlight"])
                            for label in subwidget.winfo_children():
                                if isinstance(label, tk.Label):
                                    label.config(
                                        bg=colors["highlight"],
                                        fg="white"  # 標題文字固定為白色
                                    )

        # 更新筆記清單 Listbox
        if hasattr(self, 'listbox'):
            self.listbox.config(
                bg=colors["entry_bg"],
                fg=colors["fg"],
                selectbackground=colors["select_bg"],
                selectforeground=colors["select_fg"],
                highlightbackground=colors["highlight"],
                highlightcolor=colors["highlight"]
            )

        # 更新筆記內容 Text
        if hasattr(self, 'text'):
            self.text.config(
                bg=colors["entry_bg"],
                fg=colors["fg"],
                insertbackground=colors["fg"],
                highlightbackground=colors["highlight"],
                highlightcolor=colors["highlight"]
            )

        # 更新底部 Frame（按鈕區 + 快捷提示區）
        if hasattr(self, 'master'):
            for widget in self.master.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.config(bg=colors["bg"])
                    for subwidget in widget.winfo_children():
                        # 更新底部按鈕
                        if isinstance(subwidget, tk.Button):
                            subwidget.config(
                                bg=colors["highlight"],
                                fg="white",
                                activebackground=colors["button_active_bg"],
                                activeforeground="white",
                                relief="flat",
                                bd=0
                            )
                        # 更新快捷提示 Label
                        elif isinstance(subwidget, tk.Label):
                            subwidget.config(
                                bg=colors["bg"],
                                fg=colors["fg"]
                            )

        # 更新選單
        if hasattr(self, 'master') and self.master.children.get('!menu'):
            menu = self.master.children['!menu']
            menu.config(
                bg=colors["menu_bg"],
                fg=colors["menu_fg"],
                activebackground=colors["select_bg"],
                activeforeground=colors["select_fg"]
            )
            # 更新所有子選單
            for item in menu.winfo_children():
                if isinstance(item, tk.Menu):
                    item.config(
                        bg=colors["menu_bg"],
                        fg=colors["menu_fg"],
                        activebackground=colors["select_bg"],
                        activeforeground=colors["select_fg"]
                    )

        # 更新子視窗 (Toplevel)
        for child in self.master.winfo_children():
            if isinstance(child, tk.Toplevel):
                child.config(
                    bg=colors["bg"],
                    highlightbackground=colors["highlight"],
                    highlightcolor=colors["highlight"],
                    bd=1,
                    relief="solid"
                )
                self.update_window_theme(child, colors)

    def update_window_theme(self, window, colors):
        """更新子視窗內所有小元件"""
        for widget in window.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.config(bg=colors["bg"])
            elif isinstance(widget, tk.Label):
                widget.config(bg=colors["bg"], fg=colors["fg"])
            elif isinstance(widget, tk.Entry):
                widget.config(
                    bg=colors["entry_bg"],
                    fg=colors["entry_fg"],
                    highlightbackground=colors["highlight"],
                    highlightcolor=colors["highlight"]
                )
            elif isinstance(widget, tk.Button):
                widget.config(
                    bg=colors["highlight"],
                    fg="white",
                    activebackground=colors["button_active_bg"],
                    activeforeground="white"
                )
            elif isinstance(widget, tk.Text):
                widget.config(
                    bg=colors["entry_bg"],
                    fg=colors["fg"],
                    insertbackground=colors["fg"],
                    highlightbackground=colors["highlight"],
                    highlightcolor=colors["highlight"]
                )
            elif isinstance(widget, tk.Listbox):
                widget.config(
                    bg=colors["entry_bg"],
                    fg=colors["fg"],
                    selectbackground=colors["select_bg"],
                    selectforeground=colors["select_fg"],
                    highlightbackground=colors["highlight"],
                    highlightcolor=colors["highlight"]
                )
            # 遞迴處理更深層小元件
            self.update_window_theme(widget, colors)
    

    def insert_image(self):
        """插入圖片到筆記中"""
        if not self.current_note:
            messagebox.showwarning("警告", "請先選擇或創建一個筆記")
            return
        
        file_path = filedialog.askopenfilename(
            title="選擇圖片",
            filetypes=[("圖片文件", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if file_path:
            try:
                # 讀取圖片並轉換為base64
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                
                # 調整圖片大小
                image_data = resize_image(image_data, max_width=self.text.winfo_width() - 30)
                
                # 儲存圖片到images目錄
                img_name = save_image_to_file(image_data)
                
                # 在當前游標位置插入圖片
                self.insert_image_at_position(img_name, tk.INSERT)
                
                # 在文字內容中添加圖片標記
                self.text.insert(tk.INSERT, f"\nIMAGE::{img_name}\n")
                
            except Exception as e:
                self.show_error("錯誤", f"無法插入圖片: {e}")

    def insert_image_at_position(self, img_name, position):
        """在指定位置插入圖片，並綁定右鍵刪除功能"""
        try:
            # 從檔案載入圖片
            image_data = load_image_from_file(img_name)
            if not image_data:
                return

            # 轉換為 PIL Image
            image = Image.open(io.BytesIO(image_data))

            # 轉換為 Tkinter 相容格式
            photo = ImageTk.PhotoImage(image)

            # 儲存圖片參考，防止被垃圾回收
            self.image_references[img_name] = photo

            # 在指定位置插入圖片
            image_id = self.text.image_create(position, image=photo)

            # 綁定右鍵點擊事件
            def on_right_click(event):
                self.show_image_context_menu(event, img_name, image_id)

            # 為圖片添加標籤
            tag_name = f"img_{img_name}"
            self.text.tag_add(tag_name, position)
            self.text.tag_bind(tag_name, "<Button-3>", on_right_click)
            self.image_tags[img_name] = tag_name

        except Exception as e:
            print(f"載入圖片失敗: {e}")

    def show_image_context_menu(self, event, img_name, image_id):
        """顯示圖片右鍵選單"""
        menu = tk.Menu(self.text, tearoff=0)
        menu.add_command(label="調整大小", command=lambda: self.resize_image_dialog(img_name, image_id))
        menu.add_command(label="刪除圖片", command=lambda: self.delete_image(img_name, image_id))
        menu.post(event.x_root, event.y_root)

    def resize_image_dialog(self, img_name, image_id):
        """顯示調整圖片大小對話框"""
        dialog = tk.Toplevel(self.master)
        dialog.title("調整圖片大小")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        main_frame = tk.Frame(dialog, bg=self.get_theme_color("bg"), padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(
            main_frame,
            text="輸入放大倍數 (例如 1.5):",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg")
        ).pack(pady=5)
        
        scale_entry = tk.Entry(
            main_frame,
            font=("標楷體", 12),
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("entry_fg"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight")
        )
        scale_entry.pack(pady=5, ipady=5)
        
        def confirm_resize():
            try:
                scale_factor = float(scale_entry.get())
                if scale_factor <= 0:
                    raise ValueError("倍數必須大於0")
                
                # 載入原始圖片
                image_data = load_image_from_file(img_name)
                if not image_data:
                    return
                
                # 調整大小
                image = Image.open(io.BytesIO(image_data))
                new_width = int(image.width * scale_factor)
                new_height = int(image.height * scale_factor)
                resized_image = image.resize((new_width, new_height), Image.LANCZOS)
                
                # 儲存調整後的圖片
                img_byte_arr = io.BytesIO()
                resized_image.save(img_byte_arr, format='PNG')
                resized_data = img_byte_arr.getvalue()
                save_image_to_file(resized_data, img_name)
                
                # 重新載入圖片
                position = self.text.index(f"{image_id} linestart")  # 獲取圖片所在行的起始位置
                self.text.delete(image_id)  # 刪除舊圖片
                self.insert_image_at_position(img_name, position)  # 在原位置插入新圖片
                
                dialog.destroy()
                self.show_success("成功", "圖片大小已調整")
                
            except ValueError as e:
                self.show_error("錯誤", f"無效的倍數: {e}", parent=dialog)
            except Exception as e:
                self.show_error("錯誤", f"調整圖片大小失敗: {e}", parent=dialog)
        
        btn_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        btn_frame.pack(pady=10)
        
        confirm_btn = tk.Button(
            btn_frame,
            text="確認",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=confirm_resize
        )
        confirm_btn.pack()
        
        # 添加懸停效果
        def on_enter(e):
            confirm_btn.config(bg=self.get_theme_color("button_active_bg"))
        
        def on_leave(e):
            confirm_btn.config(bg=self.get_theme_color("highlight"))
        
        confirm_btn.bind("<Enter>", on_enter)
        confirm_btn.bind("<Leave>", on_leave)
        
        # 綁定Enter鍵
        scale_entry.bind("<Return>", lambda e: confirm_resize())
        scale_entry.focus_set()

    def delete_image(self, img_name, image_id):
        """刪除圖片"""
        if messagebox.askyesno("確認", "確定要刪除此圖片嗎？"):
            try:
                # 刪除圖片標籤和內容
                self.text.delete(image_id)
                if img_name in self.image_references:
                    del self.image_references[img_name]
                if img_name in self.image_tags:
                    self.text.tag_delete(self.image_tags[img_name])
                    del self.image_tags[img_name]
                
                # 刪除圖片檔案
                delete_image_file(img_name)
                
                self.show_success("成功", "圖片已刪除")
            except Exception as e:
                self.show_error("錯誤", f"無法刪除圖片: {e}")
    
    def show_list_context_menu(self, event):
        """顯示筆記清單右鍵選單"""
        try:
            # 獲取選中的項目
            index = self.listbox.nearest(event.y)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            selected_note = self.listbox.get(index)

            # 建立右鍵選單
            menu = tk.Menu(self.listbox, tearoff=0)
            menu.add_command(label="修改標題", command=lambda: self.rename_note_dialog(selected_note))
            menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"右鍵選單錯誤: {e}")

    def rename_note_dialog(self, old_title):
        """顯示修改標題對話框"""
        rename_window = tk.Toplevel(self.master)
        rename_window.title("修改標題")
        rename_window.geometry("300x150")
        rename_window.resizable(False, False)
        rename_window.grab_set()

        main_frame = tk.Frame(rename_window, bg=self.get_theme_color("bg"), padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(
            main_frame,
            text="請輸入新標題：",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg")
        ).pack(pady=5)

        title_entry = tk.Entry(
            main_frame,
            font=("標楷體", 12),
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("entry_fg"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight")
        )
        title_entry.insert(0, old_title)
        title_entry.pack(pady=5, ipady=5)

        def confirm_rename():
            new_title = title_entry.get().strip()
            if not new_title:
                self.show_error("錯誤", "標題不能為空！", parent=rename_window)
                return
            if new_title in self.notes:
                self.show_error("錯誤", "標題已存在！", parent=rename_window)
                return
            # 更新筆記標題
            self.notes[new_title] = self.notes.pop(old_title)
            os.rename(
                os.path.join(NOTES_DIR, old_title + ".txt"),
                os.path.join(NOTES_DIR, new_title + ".txt")
            )
            self.refresh_list()
            rename_window.destroy()

        confirm_btn = tk.Button(
            main_frame,
            text="確認",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=confirm_rename
        )
        confirm_btn.pack(pady=10)

        # 添加懸停效果
        def on_enter(e):
            confirm_btn.config(bg=self.get_theme_color("button_active_bg"))

        def on_leave(e):
            confirm_btn.config(bg=self.get_theme_color("highlight"))

        confirm_btn.bind("<Enter>", on_enter)
        confirm_btn.bind("<Leave>", on_leave)

        # 綁定Enter鍵
        title_entry.bind("<Return>", lambda e: confirm_rename())
        title_entry.focus_set()

    def start_drag(self, event):
        """開始拖放"""
        self.drag_start_index = self.listbox.nearest(event.y)

    def do_drag(self, event):
        """拖放過程中"""
        self.listbox.selection_clear(0, tk.END)
        current_index = self.listbox.nearest(event.y)
        self.listbox.selection_set(current_index)

    def end_drag(self, event):
        """結束拖放"""
        drag_end_index = self.listbox.nearest(event.y)
        if self.drag_start_index != drag_end_index:
            # 調整筆記順序
            titles = list(self.notes.keys())
            dragged_item = titles.pop(self.drag_start_index)
            titles.insert(drag_end_index, dragged_item)
            
            # 重新排序 self.notes
            self.notes = {title: self.notes[title] for title in titles}
            self.refresh_list()

            # 更新設定檔中的順序
            self.config['note_order'] = titles
            save_config(self.config)

    def record_state(self, event=None):
        """記錄文字編輯器的狀態"""
        if event and (event.state & 0x4):  # 檢查是否按下 Ctrl 鍵
            return
        if event and event.keysym in ("Control_L", "Control_R", "Shift_L", "Shift_R"):
            return
        content = self.text.get("1.0", tk.END)
        if not self.undo_stack or content != self.undo_stack[-1][0]:
            self.undo_stack.append((content, self.text.index(tk.INSERT)))
            self.redo_stack = []  # 清空 redo 堆疊

    def undo(self):
        """返回上一步"""
        if self.undo_stack:
            content, pos = self.undo_stack.pop()
            current_content = self.text.get("1.0", tk.END)
            current_pos = self.text.index(tk.INSERT)
            self.redo_stack.append((current_content, current_pos))
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.text.mark_set(tk.INSERT, pos)
            self.text.see(tk.INSERT)

    def redo(self):
        """重做下一步"""
        if self.redo_stack:
            content, pos = self.redo_stack.pop()
            current_content = self.text.get("1.0", tk.END)
            current_pos = self.text.index(tk.INSERT)
            self.undo_stack.append((current_content, current_pos))
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content)
            self.text.mark_set(tk.INSERT, pos)
            self.text.see(tk.INSERT)

    def show_text_context_menu(self, event):
        """顯示文字編輯區右鍵選單"""
        menu = tk.Menu(self.text, tearoff=0)
        menu.add_command(label="複製", command=self.copy_text)
        menu.add_command(label="很強的貼上", command=self.paste_text_or_image)
        menu.post(event.x_root, event.y_root)

    def copy_text(self):
        """複製選取的文字"""
        try:
            selected_text = self.text.selection_get()
            self.master.clipboard_clear()
            self.master.clipboard_append(selected_text)
            self.master.update()  # 更新剪貼簿
        except tk.TclError:
            pass  # 如果沒有選取文字，忽略錯誤

    def paste_text_or_image(self):
        """貼上文字或圖片"""
        try:
            # 嘗試貼上文字
            clipboard_data = self.master.clipboard_get()
            self.text.insert(tk.INSERT, clipboard_data)
        except tk.TclError:
            # 如果不是文字，試著貼上圖片
            try:
                image = ImageGrab.grabclipboard()
                if image:
                    # 將圖片轉為 bytes
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    image_data = img_byte_arr.getvalue()

                    # 儲存圖片並插入
                    img_name = save_image_to_file(image_data)
                    self.insert_image_at_position(img_name, tk.INSERT)
                    self.text.insert(tk.INSERT, f"\nIMAGE::{img_name}\n")
                else:
                    raise ValueError("剪貼簿中沒有圖片")
            except Exception as e:
                self.show_error("錯誤", f"無法貼上圖片: {e}")

    def delete_unused_images(self):
        """刪除未被任何筆記使用的圖片和捷徑"""
        try:
            # 收集所有筆記中使用的圖片和捷徑名稱
            used_images = set()
            used_shortcuts = set()
            for content in self.notes.values():
                lines = content.split('\n')
                for line in lines:
                    if line.startswith('IMAGE::'):
                        used_images.add(line[7:])
                    elif line.startswith('SHORTCUT::'):
                        used_shortcuts.add(line[10:])

            # 刪除 images 資料夾中未被使用的圖片
            if os.path.exists(IMAGES_DIR):
                for filename in os.listdir(IMAGES_DIR):
                    if filename not in used_images:
                        filepath = os.path.join(IMAGES_DIR, filename)
                        os.remove(filepath)
                        print(f"已刪除未使用的圖片: {filename}")

            # 刪除 shortcuts 資料夾中未被使用的捷徑
            if os.path.exists(SHORTCUTS_DIR):
                for filename in os.listdir(SHORTCUTS_DIR):
                    if filename.endswith('.txt'):
                        shortcut_id = filename[:-4]
                        if shortcut_id not in used_shortcuts:
                            filepath = os.path.join(SHORTCUTS_DIR, filename)
                            os.remove(filepath)
                            print(f"已刪除未使用的捷徑: {filename}")

            self.show_success("完成", "未使用的圖片和捷徑已刪除")
        except Exception as e:
            self.show_error("錯誤", f"刪除未使用的圖片和捷徑失敗: {e}")
            
    def load_lockout_status(self):
        """載入鎖定狀態"""
        if os.path.exists(LOCKOUT_FILE):
            with open(LOCKOUT_FILE, 'r') as f:
                data = json.load(f)
                self.lockout_until = data.get('lockout_until', 0)
                self.config['email'] = data.get('email', '')  # 載入保存的email

    def save_lockout_status(self):
        """儲存鎖定狀態"""
        with open(LOCKOUT_FILE, 'w') as f:
            json.dump({
                'lockout_until': self.lockout_until,
                'email': self.config.get('email', '')
            }, f)

    def check_lockout(self):
        """檢查是否處於鎖定狀態"""
        if time.time() < self.lockout_until :
            unlock_hash = self.config.get("unlock_password_hash")
            if unlock_hash and hash_password(self.password_entry.get()) == unlock_hash:
                return True
            remaining = int(self.lockout_until - time.time())
            self.show_error("帳戶鎖定", 
                f"密碼錯誤次數過多，請等待 {remaining//60} 分 {remaining%60} 秒後再試")
            return True
        return False

    def send_email_notification(self):
        """發送電子郵件通知"""
        if not ENABLE_EMAIL_NOTIFICATION:  # 檢查是否啟用郵件通知
            print("郵件通知功能已關閉")
            return
        email = self.config.get('email', '')
        if not email:
            return
            
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            # 這裡使用Gmail SMTP伺服器，你需要替換為自己的SMTP設置
            msg = MIMEText(f"你電腦上的的筆記檢測到多次登入失敗，帳戶已暫時鎖定，建議看看有沒有人在亂玩你的電腦")
            msg['Subject'] = '沒人看的到的筆記 登入異常通知'
            msg['From'] = 'cheny0976@gmail.com'  # 替換為你的發件郵箱
            msg['To'] = email
            
            # 注意：這需要啟用Gmail的"允許安全性較低的應用程式"或使用應用程式專用密碼
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login('cheny0976@gmail.com', 'ecak yeek pada stwx')  # 替換為你的憑證
                server.send_message(msg)
        except Exception as e:
            print(f"發送郵件失敗: {e}")
            
    def set_notification_email(self):
        """設定通知郵箱"""
        email_window = tk.Toplevel(self.master)
        email_window.title("設定通知郵箱")
        email_window.geometry("500x300")
        email_window.resizable(False, False)
        email_window.grab_set()
        
        main_frame = tk.Frame(
            email_window, 
            bg=self.get_theme_color("bg"),
            padx=20,
            pady=20
        )
        main_frame.pack(fill="both", expand=True)
        
        # 標題
        tk.Label(
            main_frame,
            text="設定通知郵箱",
            font=("標楷體", 16, "bold"),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("highlight"),
            pady=10
        ).pack()
        
        # 說明文字
        tk.Label(
            main_frame,
            text="當密碼錯誤次數過多時，系統將發送通知到此郵箱",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg"),
            pady=5
        ).pack()
        
        # 郵箱輸入框
        input_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        input_frame.pack(pady=20)
        
        tk.Label(
            input_frame,
            text="電子郵件地址：",
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg")
        ).pack(side="left")
        
        email_entry = tk.Entry(
            input_frame, 
            font=("標楷體", 12),
            width=30,
            bg=self.get_theme_color("entry_bg"),
            fg=self.get_theme_color("entry_fg"),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightcolor=self.get_theme_color("highlight")
        )
        email_entry.pack(side="left", padx=10)
        email_entry.insert(0, self.config.get('email', ''))
        
        # 按鈕框架
        btn_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        btn_frame.pack(pady=10)
        
        def save_email():
            email = email_entry.get().strip()
            if email and '@' not in email:
                self.show_error("錯誤", "請輸入有效的電子郵件地址", parent=email_window)
                return
                
            self.config['email'] = email
            save_config(self.config)
            self.save_lockout_status()  # 同時更新鎖定文件中的email
            self.show_success("成功", "電子郵件已保存", parent=email_window)
            email_window.destroy()
        
        save_btn = tk.Button(
            btn_frame,
            text="保存",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=save_email
        )
        save_btn.pack()
        
        # 添加懸停效果
        def on_enter(e):
            save_btn.config(bg=self.get_theme_color("button_active_bg"))
        
        def on_leave(e):
            save_btn.config(bg=self.get_theme_color("highlight"))
        
        save_btn.bind("<Enter>", on_enter)
        save_btn.bind("<Leave>", on_leave)
        
        # 綁定Enter鍵
        email_entry.bind("<Return>", lambda e: save_email())
        email_entry.focus_set()

    def handle_dropped_shortcut(self, event):
        """處理拖放的捷徑"""
        if not self.current_note:
            messagebox.showwarning("警告", "請先選擇或創建一個筆記")
            return
        
        # 獲取拖放的檔案路徑
        filepath = event.data.strip('{}')  # 去除可能的花括號
        if not os.path.exists(filepath):
            return
        
        # 如果是捷徑 (.lnk)，解析實際路徑
        if filepath.lower().endswith('.lnk'):
            try:
                from win32com.client import Dispatch
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(filepath)
                filepath = shortcut.Targetpath
            except:
                self.show_error("錯誤", "無法解析捷徑")
                return
        
        # 儲存捷徑資訊
        shortcut_id = str(uuid.uuid4())
        shortcut_file = os.path.join(SHORTCUTS_DIR, shortcut_id + '.txt')
        with open(shortcut_file, 'w') as f:
            f.write(filepath)
        
        # 在筆記中插入捷徑標記
        self.insert_shortcut_at_position(shortcut_id, filepath, tk.INSERT)
        self.text.insert(tk.INSERT, f"\nSHORTCUT::{shortcut_id}\n")

    def insert_shortcut_at_position(self, shortcut_id, filepath, position):
        """在指定位置插入捷徑圖示"""
        try:
            # 根據檔案類型選擇圖示
            icon = self.get_file_icon(filepath)
            if icon:
                # 轉換為 Tkinter 相容格式
                photo = ImageTk.PhotoImage(icon)
                
                # 儲存圖片參考，防止被垃圾回收
                self.shortcut_references[shortcut_id] = photo
                
                # 在指定位置插入圖片
                image_id = self.text.image_create(position, image=photo)
                
                # 綁定雙擊事件
                def on_double_click(event):
                    self.open_shortcut(shortcut_id)

                # 為圖片添加標籤
                tag_name = f"shortcut_{shortcut_id}"
                self.text.tag_add(tag_name, position)
                self.text.tag_bind(tag_name, "<Double-Button-1>", on_double_click)

                # 更改滑鼠游標樣式
                def on_enter(event):
                    self.text.config(cursor="hand2")  # 或 "grabbing"

                def on_leave(event):
                    self.text.config(cursor="")  # 恢復預設游標

                self.text.tag_bind(tag_name, "<Enter>", on_enter)
                self.text.tag_bind(tag_name, "<Leave>", on_leave)
        except Exception as e:
            print(f"插入捷徑圖示失敗: {e}")

    def get_file_icon(self, filepath):
        """獲取檔案圖示"""
        try:
            import win32ui
            import win32con
            import win32gui
            from PIL import Image

            # 獲取系統圖示
            SHGFI_ICON = 0x000000100
            SHGFI_SMALLICON = 0x000000001

            if os.path.isdir(filepath):
                # 資料夾圖示
                flags = win32con.SHGFI_ICON | win32con.SHGFI_SMALLICON
                file_info = win32gui.SHGetFileInfo(filepath, 0, flags)
            else:
                # 檔案圖示
                flags = win32con.SHGFI_ICON | win32con.SHGFI_SMALLICON | win32con.SHGFI_USEFILEATTRIBUTES
                file_info = win32gui.SHGetFileInfo(filepath, win32con.FILE_ATTRIBUTE_NORMAL, flags)

            hicon = file_info[0]

            # 將圖示轉換為 PIL Image
            icon = win32ui.GetBitmapFromHICON(hicon)
            bmpstr = icon.GetBitmapBits(True)
            image = Image.frombuffer(
                'RGBA',
                (icon.GetWidth(), icon.GetHeight()),
                bmpstr, 'raw', 'BGRA', 0, 1
            )

            # 調整圖片大小
            max_size = (48, 48)  # 設定最大尺寸
            image.thumbnail(max_size, Image.LANCZOS)

            return image
        except:
            # 如果無法獲取系統圖示，使用預設圖示
            try:
                default_icon = Image.open("assets/default_icon.png")  # 你需要提供一個預設圖示
                default_icon.thumbnail((48, 48), Image.LANCZOS)
                return default_icon
            except:
                return None

    def open_shortcut(self, shortcut_id):
        """開啟捷徑對應的檔案"""
        try:
            shortcut_file = os.path.join(SHORTCUTS_DIR, shortcut_id + '.txt')
            if os.path.exists(shortcut_file):
                with open(shortcut_file, 'r') as f:
                    filepath = f.read().strip()
                    if os.path.exists(filepath):
                        os.startfile(filepath)
                    else:
                        self.show_error("錯誤", "檔案不存在或已被移動")
        except Exception as e:
            self.show_error("錯誤", f"無法開啟檔案: {e}")
            
    def show_error(self, title, message, parent=None):
        """顯示美化的錯誤訊息"""
        error_window = tk.Toplevel(parent if parent else self.master)
        error_window.title(title)
        error_window.resizable(False, False)
        error_window.grab_set()
        
        # 設定視窗大小和位置
        error_window.geometry("500x400")
        error_window.update_idletasks()
        x = (error_window.winfo_screenwidth() - error_window.winfo_width()) // 2
        y = (error_window.winfo_screenheight() - error_window.winfo_height()) // 2
        error_window.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = tk.Frame(
            error_window,
            bg=self.get_theme_color("error_bg"),
            padx=20,
            pady=20,
            relief="solid",
            bd=1,
            highlightbackground=self.get_theme_color("error_highlight"),
            highlightthickness=1
        )
        main_frame.pack(fill="both", expand=True)
        
        # 錯誤圖標
        if os.path.exists("assets/error_icon.png"):
            error_img = Image.open("assets/error_icon.png").resize((90, 90), Image.LANCZOS)
            self.error_icon = ImageTk.PhotoImage(error_img)
            tk.Label(
                main_frame,
                image=self.error_icon,
                bg=self.get_theme_color("error_bg")
            ).pack(pady=(0, 10))
        
        # 錯誤標題
        tk.Label(
            main_frame,
            text=title,
            font=("標楷體", 20, "bold"),
            bg=self.get_theme_color("error_bg"),
            fg=self.get_theme_color("error_fg"),
            pady=5
        ).pack()
        
        # 錯誤訊息（自動換行）
        message_label = tk.Label(
            main_frame,
            text=message,
            font=("標楷體", 16),
            bg=self.get_theme_color("error_bg"),
            fg=self.get_theme_color("error_fg"),
            wraplength=400,  # 設定自動換行的寬度
            justify="center"  # 文字置中
        )
        message_label.pack(pady=10, fill="both", expand=True)
        
        # 確認按鈕
        btn_frame = tk.Frame(main_frame, bg=self.get_theme_color("error_bg"))
        btn_frame.pack(pady=(10, 0))
        
        confirm_btn = tk.Button(
            btn_frame,
            text="確定",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=error_window.destroy
        )
        confirm_btn.pack()
        
        # 添加懸停效果
        def on_enter(e):
            confirm_btn.config(bg=self.get_theme_color("button_active_bg"))
        
        def on_leave(e):
            confirm_btn.config(bg=self.get_theme_color("highlight"))
        
        confirm_btn.bind("<Enter>", on_enter)
        confirm_btn.bind("<Leave>", on_leave)
        
        # 綁定Enter鍵
        error_window.bind("<Return>", lambda e: error_window.destroy())
        confirm_btn.focus_set()
        
    def show_confirm(self, title, message, parent=None):
        """顯示美化的確認對話框"""
        confirm_window = tk.Toplevel(parent if parent else self.master)
        confirm_window.title(title)
        confirm_window.resizable(False, False)
        confirm_window.grab_set()
        
        # 設定視窗大小和位置
        confirm_window.geometry("400x200")
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() - confirm_window.winfo_width()) // 2
        y = (confirm_window.winfo_screenheight() - confirm_window.winfo_height()) // 2
        confirm_window.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = tk.Frame(
            confirm_window,
            bg=self.get_theme_color("bg"),
            padx=20,
            pady=20,
            relief="solid",
            bd=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightthickness=1
        )
        main_frame.pack(fill="both", expand=True)
        
        # 訊息標題
        tk.Label(
            main_frame,
            text=title,
            font=("標楷體", 14, "bold"),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("highlight"),
            pady=5
        ).pack()
        
        # 訊息內容（自動換行）
        message_label = tk.Label(
            main_frame,
            text=message,
            font=("標楷體", 12),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg"),
            wraplength=350,
            justify="center"
        )
        message_label.pack(pady=10, fill="both", expand=True)
        
        # 按鈕框架
        btn_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        btn_frame.pack(pady=(10, 0))
        
        result = [False]  # 使用列表以便在嵌套函數中修改
        
        def set_result(value):
            result[0] = value
            confirm_window.destroy()
        
        # 是/否按鈕
        yes_btn = tk.Button(
            btn_frame,
            text="是",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=lambda: set_result(True)
        )
        yes_btn.pack(side="left", padx=10)
        
        no_btn = tk.Button(
            btn_frame,
            text="否",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=lambda: set_result(False)
        )
        no_btn.pack(side="left", padx=10)
        
        # 添加懸停效果
        def on_enter_yes(e):
            yes_btn.config(bg=self.get_theme_color("button_active_bg"))
        
        def on_leave_yes(e):
            yes_btn.config(bg=self.get_theme_color("highlight"))
        
        def on_enter_no(e):
            no_btn.config(bg=self.get_theme_color("button_active_bg"))
        
        def on_leave_no(e):
            no_btn.config(bg=self.get_theme_color("button_bg"))
        
        yes_btn.bind("<Enter>", on_enter_yes)
        yes_btn.bind("<Leave>", on_leave_yes)
        no_btn.bind("<Enter>", on_enter_no)
        no_btn.bind("<Leave>", on_leave_no)
        
        # 綁定Enter/Esc鍵
        confirm_window.bind("<Return>", lambda e: set_result(True))
        confirm_window.bind("<Escape>", lambda e: set_result(False))
        yes_btn.focus_set()
        
        confirm_window.wait_window()
        return result[0]
    
    def show_success(self, title, message, parent=None):
        """顯示美化的成功訊息"""
        success_window = tk.Toplevel(parent if parent else self.master)
        success_window.title(title)
        success_window.resizable(False, False)
        success_window.grab_set()
        
        # 設定視窗大小和位置
        success_window.geometry("400x400")
        success_window.update_idletasks()
        x = (success_window.winfo_screenwidth() - success_window.winfo_width()) // 2
        y = (success_window.winfo_screenheight() - success_window.winfo_height()) // 2
        success_window.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = tk.Frame(
            success_window,
            bg=self.get_theme_color("bg"),
            padx=20,
            pady=20,
            relief="solid",
            bd=1,
            highlightbackground=self.get_theme_color("highlight"),
            highlightthickness=1
        )
        main_frame.pack(fill="both", expand=True)
        
        # 成功圖標
        if os.path.exists("assets/success_icon.png"):
            success_img = Image.open("assets/success_icon.png").resize((150, 150), Image.LANCZOS)
            self.success_icon = ImageTk.PhotoImage(success_img)
            tk.Label(
                main_frame,
                image=self.success_icon,
                bg=self.get_theme_color("bg")
            ).pack(pady=(0, 10))
        
        # 成功標題
        tk.Label(
            main_frame,
            text=title,
            font=("標楷體", 20, "bold"),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("highlight"),
            pady=5
        ).pack()
        
        # 成功訊息（自動換行）
        message_label = tk.Label(
            main_frame,
            text=message,
            font=("標楷體", 16),
            bg=self.get_theme_color("bg"),
            fg=self.get_theme_color("fg"),
            wraplength=350,  # 設定自動換行的寬度
            justify="center"  # 文字置中
        )
        message_label.pack(pady=10, fill="both", expand=True)
        
        # 確認按鈕
        btn_frame = tk.Frame(main_frame, bg=self.get_theme_color("bg"))
        btn_frame.pack(pady=(10, 0))
        
        confirm_btn = tk.Button(
            btn_frame,
            text="確定",
            font=("標楷體", 12, "bold"),
            bg=self.get_theme_color("highlight"),
            fg="white",
            activebackground=self.get_theme_color("button_active_bg"),
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=5,
            command=success_window.destroy
        )
        confirm_btn.pack()
        
        # 添加懸停效果
        def on_enter(e):
            confirm_btn.config(bg=self.get_theme_color("button_active_bg"))
        
        def on_leave(e):
            confirm_btn.config(bg=self.get_theme_color("highlight"))
        
        confirm_btn.bind("<Enter>", on_enter)
        confirm_btn.bind("<Leave>", on_leave)
        
        # 綁定Enter鍵
        success_window.bind("<Return>", lambda e: success_window.destroy())
        success_window.bind("<Escape>", lambda e: success_window.destroy())
        confirm_btn.focus_set()

def hide_folder(folder_path):
    """使資料夾在檔案總管中隱藏"""
    try:
        # Windows
        if os.name == 'nt':
            import win32con, win32api
            win32api.SetFileAttributes(folder_path, win32con.FILE_ATTRIBUTE_HIDDEN)
        # Linux/macOS
        else:
            os.chmod(folder_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
            os.rename(folder_path, os.path.join(os.path.dirname(folder_path), '.' + os.path.basename(folder_path)))
    except Exception as e:
        print(f"隱藏資料夾失敗: {e}")

# ===================== 啟動 =====================

if __name__ == '__main__':
    root = TkinterDnD.Tk()  # 使用 TkinterDnD 的 Tk
    app = NotesApp(root)
    root.mainloop()
