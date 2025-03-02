import os
import sys
import threading
import zipfile
import shutil
import webbrowser
from typing import Dict, List
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk  # Using newer customtkinter version
import requests
from PIL import Image, ImageTk
import json
import time
import traceback
import psutil
import vdf

# --- Settings ---
THEME = {
    "bg_primary": "#0f0f0f",
    "bg_secondary": "#181818",
    "accent": "#c14953",
    "hover_accent": "#9d3b44",
    "progress_color": "#c14953",
    "text_primary": "#e8e6e3",
    "text_secondary": "#a0a0a0",
    "success": "#5cb85c",
    "error": "#d9534f",
    "border": "#303030",
    "card_bg": "#121212",
    "button_secondary": "#2a2a2a"
}

# Steam paths
STEAM_PATHS = [
    "C:/Program Files (x86)/Steam/userdata",
    "C:/Program Files/Steam/userdata",
    "D:/Steam/userdata",
    os.path.expanduser("~/Steam/userdata")
]
DOTA_APP_ID = "570"
CONFIG_DIR = "cfg"
LOCAL_CFG_DIR = os.path.join("local", "cfg")
REMOTE_CFG_DIR = os.path.join("remote", "cfg")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

LANGUAGES = {
    "EN": {
        "loading": "Loading...",
        "no_internet": "No internet.",
        "warnings": "⚠️ Important:\n\n1. Dota 2 must be closed\n2. Internet required\n\nIf Dota 2 is not closed, it will automatically close 5 seconds after CBD2 is launched",
        "warnings2": "Before importing the config, make sure that:\n\n1. Dota 2 is closed\n2. During startup Dota 2, you are loading a local save, not a cloud save",
        "menu": "Menu",
        "language": "Language",
        "github": "GitHub",
        "telegram": "Telegram",
        "import_config": "Import",
        "export_config": "Export",
        "back": "Back",
        "select": "Select",
        "success": "Success",
        "error": "Error",
        "config_imported": "Imported",
        "config_exported": "Exported",
        "import_from_file": "Import from file",
        "import_from_account": "Import from account",
        "select_account": "Select account",
        "select_source": "Select source",
        "no_accounts_found": "No accounts found",
        "steam_not_found": "Steam folder not found",
        "no_config_files": "No config files",
        "empty_config_dir": "Config directory empty",
        "user_not_found": "User info not found",
        "dota_config_not_found": "Dota 2 config not found",
    },
    "RU": {
        "loading": "Загрузка...",
        "no_internet": "Нет интернета.",
        "warnings": "⚠️ Важно:\n\n1. Dota 2 должна быть закрыта\n2. Нужен интернет\n\nЕсли Dota 2 не закрыта - она автоматически закроется спустя 5 секунд после запуска CBD2",
        "warnings2": "Перед импортом конфига убедись, что:\n\n1. Dota 2 закрыта\n2. Во время запуска Dota 2 ты загружаешь локальное сохранение, а не облачное",
        "menu": "Меню",
        "language": "Язык",
        "github": "GitHub",
        "telegram": "Telegram",
        "import_config": "Импортировать",
        "export_config": "Экспортировать",
        "back": "Назад",
        "select": "Выбрать",
        "success": "Успех",
        "error": "Ошибка",
        "config_imported": "Импортировано",
        "config_exported": "Экспортировано",
        "import_from_file": "Импорт из файла",
        "import_from_account": "Импорт с аккаунта",
        "select_account": "Выберите аккаунт",
        "select_source": "Выберите источник",
        "no_accounts_found": "Аккаунты не найдены",
        "steam_not_found": "Папка Steam не найдена",
        "no_config_files": "Нет файлов",
        "empty_config_dir": "Папка пуста",
        "user_not_found": "Инфо не найдено",
        "dota_config_not_found": "Конфиг не найден",
    },
}


def kill_dota2(user_name=None, min_memory_mb=None):
    time.sleep(1)
    killed_pids = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_full_info']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == "dota2.exe":
                if user_name and proc.info['username'] != user_name:
                    continue

                if min_memory_mb is not None:
                    memory_mb = proc.info['memory_full_info'].rss / (1024 * 1024)
                    if memory_mb < min_memory_mb:
                        continue

                proc.kill()
                killed_pids.append(proc.info['pid'])
                print(f"dota2.exe (PID: {proc.info['pid']}) killed.")

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            print(f"Error processing: {e}")

    return killed_pids


# --- Utilities ---
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)


def check_internet():
    try:
        requests.get("http://google.com", timeout=3)
        return True
    except requests.RequestException:
        return False


def find_steam_userdata_path():
    for path in STEAM_PATHS:
        if os.path.exists(path) and os.path.isdir(path):
            return path
    return None


# --- Animations ---
def animate_progress_bar(progress_bar):
    current_value = progress_bar.get()
    if current_value < 1:
        progress_bar.set(current_value + 0.01)
    else:
        progress_bar.set(0)
    progress_bar.after(50, lambda: animate_progress_bar(progress_bar))


# --- Custom Widgets ---
class AnimatedButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("border_width", 0)
        kwargs.setdefault("border_color", THEME["border"])
        kwargs.setdefault("font", ("Inter", 12, "bold"))
        kwargs.setdefault("hover_color", THEME["hover_accent"])
        kwargs.setdefault("text_color", THEME["text_primary"])
        kwargs.setdefault("height", 40)
        super().__init__(master, **kwargs)

        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_hover(self, event):
        self.configure(fg_color=THEME["hover_accent"])

    def on_leave(self, event):
        self.configure(fg_color=THEME["accent"])

    def on_click(self, event):
        self.configure(fg_color=THEME["hover_accent"], border_width=1)

    def on_release(self, event):
        self.configure(fg_color=THEME["hover_accent"], border_width=0)


class SecondaryButton(AnimatedButton):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", THEME["button_secondary"])
        kwargs.setdefault("hover_color", "#3A5875")
        super().__init__(master, **kwargs)

    def on_leave(self, event):
        self.configure(fg_color=THEME["button_secondary"])

    def on_click(self, event):
        self.configure(fg_color="#3A5875", border_width=1)


class AccountCard(ctk.CTkFrame):
    def __init__(self, master, account: Dict, on_select, lang_code, **kwargs):
        super().__init__(
            master,
            fg_color=THEME["card_bg"],
            corner_radius=16,
            border_width=0,
            **kwargs
        )

        self.bind("<Enter>", lambda e: self.configure(border_width=1, border_color=THEME["accent"]))
        self.bind("<Leave>", lambda e: self.configure(border_width=0))

        padding_frame = ctk.CTkFrame(self, fg_color="transparent")
        padding_frame.pack(fill="x", padx=16, pady=16)

        content = ctk.CTkFrame(padding_frame, fg_color="transparent")
        content.pack(fill="x")

        # Avatar display (with rounding)
        avatar_frame = ctk.CTkFrame(content, width=50, height=50, corner_radius=25, fg_color=THEME["accent"])
        avatar_frame.pack(side="left", padx=(0, 16))
        avatar_frame.pack_propagate(False)

        if account.get('avatar'):
            try:
                # Создаём прозрачный фон для аватара вместо красного
                avatar_frame.configure(fg_color="transparent")

                # Загружаем и изменяем размер аватара
                avatar_image = Image.open(account['avatar']).resize((48, 48))

                # Преобразуем в RGBA если необходимо
                if avatar_image.mode != 'RGBA':
                    avatar_image = avatar_image.convert('RGBA')

                # Создаём круглую маску
                mask = Image.new('L', (48, 48), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 48, 48), fill=255)

                # Создаём новое изображение с прозрачным фоном
                circular_image = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
                # Применяем маску к аватару
                circular_image.paste(avatar_image, (0, 0), mask)

                photo_image = ImageTk.PhotoImage(circular_image)
                # Создаём метку с прозрачным фоном
                avatar_label = tk.Label(avatar_frame, image=photo_image, bg=THEME["bg_primary"],
                                        borderwidth=0, highlightthickness=0)
                avatar_label.image = photo_image  # Сохраняем ссылку
                avatar_label.place(relx=0.5, rely=0.5, anchor="center")
            except Exception as e:
                print(f"Error loading avatar: {e}")
                # Запасной вариант для инициалов
                initial_label = ctk.CTkLabel(avatar_frame,
                                             text=account['personaname'][0].upper() if account['personaname'] else "?",
                                             font=("Inter", 18, "bold"), text_color=THEME["text_primary"])
                initial_label.place(relx=0.5, rely=0.5, anchor="center")

        else:
            initial_label = ctk.CTkLabel(
                avatar_frame,
                text=account['personaname'][0].upper() if account['personaname'] else "?",
                font=("Inter", 18, "bold"),
                text_color=THEME["text_primary"],
            )
            initial_label.place(relx=0.5, rely=0.5, anchor="center")

        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        name_label = ctk.CTkLabel(
            info_frame,
            text=account['personaname'],
            font=("Inter", 14, "bold"),
            text_color=THEME["text_primary"]
        )
        name_label.pack(anchor="w")

        id_label = ctk.CTkLabel(
            info_frame,
            text=f"ID: {account['account_id']}",
            font=("Inter", 11),
            text_color=THEME["text_secondary"]
        )
        id_label.pack(anchor="w")

        select_btn = AnimatedButton(
            content,
            text=LANGUAGES[lang_code]["select"],
            fg_color=THEME["accent"],
            hover_color=THEME["hover_accent"],
            width=100,
            command=lambda: on_select(account)
        )
        select_btn.pack(side="right", padx=(8, 0))


# --- Main Application ---
class ConfigBridgeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ConfigBridge Dota 2")
        self.geometry("800x600")
        self.configure(fg_color=THEME["bg_primary"])
        self.minsize(600, 400)

        self.selected_account = None
        self.accounts: List[Dict] = []
        self.current_lang = "RU"
        self.console_mode = "-console" in sys.argv
        self.log_window = None
        self.steam_userdata_path = find_steam_userdata_path()
        self._popup_window = None  # Store the popup window

        if self.console_mode:
            self.create_log_window()
        self.log("Application started", console_only=True)

        try:
            icon_path = resource_path("assets/icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            self.log(f"Icon loading failed: {e}", is_error=True, console_only=True)

        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 14),
            text_color=THEME["text_primary"]
        )
        self.status_label.pack(side="bottom", pady=10)

        self.main_container = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_primary"]
        )
        self.main_container.pack(fill="both", expand=True, padx=16, pady=16)

        self.show_loading()
        threading.Thread(target=self.load_data, daemon=True).start()

        self.warnings_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 20),
            text_color=THEME["text_primary"],
        )

        self.countdown_label = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 12),
            text_color=THEME["text_secondary"]
        )
        self.countdown_label.place(x=10, y=self.winfo_screenheight() - 50)

    def create_log_window(self):
        self.log_window = tk.Toplevel(self)
        self.log_window.title("ConfigBridge Logs")
        self.log_window.geometry("600x400")
        self.log_window.configure(bg=THEME["bg_primary"])

        self.log_text = tk.Text(self.log_window, bg=THEME["bg_secondary"], fg=THEME["text_primary"])
        self.log_text.pack(expand=True, fill="both", padx=10, pady=10)

        self.log_text.tag_configure("error", foreground=THEME["error"])

    def log(self, message, is_error=False, console_only=False):
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {'Error' if is_error else 'Info'}: {message}"

        if self.console_mode:
            if self.log_window and self.log_window.winfo_exists():
                self.log_text.insert(tk.END, log_msg + "\n", "error" if is_error else "")
                self.log_text.see(tk.END)
            else:
                print(log_msg)
        elif not console_only:
            print(log_msg)
            if is_error:  # Show error messages even when not console only
                self.show_error_message(message)

    def show_loading(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        loading_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["bg_secondary"],
            corner_radius=12
        )
        loading_frame.pack(expand=True, fill="both", padx=20, pady=20)

        loading_label = ctk.CTkLabel(
            loading_frame,
            text=LANGUAGES[self.current_lang]["loading"],
            font=("Segoe UI", 16, "bold"),
            text_color=THEME["text_primary"]
        )
        loading_label.pack(expand=True)

        progress_bar = ctk.CTkProgressBar(
            loading_frame,
            progress_color=THEME["progress_color"],
            width=300
        )
        progress_bar.pack(expand=True)
        animate_progress_bar(progress_bar)

    def load_data(self):
        try:
            if not check_internet():
                self.show_error_message(LANGUAGES[self.current_lang]["no_internet"])
                self.log(LANGUAGES[self.current_lang]["no_internet"], is_error=True)

            if not self.steam_userdata_path:
                self.log("Steam userdata path not found", is_error=True)
                self.after(0, lambda: self.show_error_message(LANGUAGES[self.current_lang]["steam_not_found"]))
                self.after(1000, self.finish_initialization)
                return

            self.load_accounts()
            self.after(0, self.finish_initialization)
        except Exception as e:
            error_msg = f"Error loading data: {str(e)}"
            self.log(error_msg, is_error=True)
            self.log(traceback.format_exc(), is_error=True, console_only=True)
            self.after(0, lambda: self.show_error_message(error_msg))
            self.after(1000, self.finish_initialization)

    def show_error_message(self, message):
        self.status_label.configure(
            text=message,
            text_color=THEME["error"]
        )
        self.after(5000, lambda: self.status_label.configure(text=""))

    def finish_initialization(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        self.main_container.pack_forget()
        self.create_header()
        self.show_warnings_with_countdown()

    def show_warnings_with_countdown(self):
        self.warnings_label.configure(
            text=f"{LANGUAGES['EN']['warnings']}\n\n{LANGUAGES['RU']['warnings']}",
            font=("Segoe UI", 14),
            text_color=THEME["text_primary"]
        )
        self.warnings_label.place(relx=0.5, rely=0.5, anchor="center")
        self.start_countdown(3)

    def start_countdown(self, seconds):
        if seconds > 0:
            self.countdown_label.configure(text=f"{seconds}", text_color=THEME["text_primary"])
            self.countdown_label.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")
            self.after(1000, self.start_countdown, seconds - 1)
        else:
            self.warnings_label.place_forget()
            self.countdown_label.place_forget()
            self.main_container.pack(fill="both", expand=True, padx=16, pady=16)
            self.create_main_ui()

    def create_header(self):
        header = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["bg_secondary"],
            corner_radius=16,
            height=70
        )
        header.pack(fill="x", pady=(0, 16))
        header.pack_propagate(False)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20)

        try:
            icon_path = resource_path("assets/icon.ico")
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((32, 32))
                icon_photo = ImageTk.PhotoImage(icon_image)

                icon_label = tk.Label(
                    title_frame,
                    image=icon_photo,
                    bg=THEME["bg_secondary"],
                    borderwidth=0
                )
                icon_label.image = icon_photo
                icon_label.pack(side="left", padx=(0, 10))
        except Exception as e:
            self.log(f"Icon display error: {e}", is_error=True, console_only=True)

        title = ctk.CTkLabel(
            title_frame,
            text="ConfigBridge Dota 2",
            font=("Inter", 18, "bold"),
            text_color=THEME["text_primary"]
        )
        title.pack(side="left")

        control_frame = ctk.CTkFrame(header, fg_color="transparent")
        control_frame.pack(side="right", padx=10)

        lang_btn = SecondaryButton(
            control_frame,
            text=self.current_lang,
            width=50,
            command=self.show_language_menu
        )
        lang_btn.pack(side="right", padx=5)

        menu_btn = SecondaryButton(
            control_frame,
            text="☰",
            width=50,
            command=self.show_menu
        )
        menu_btn.pack(side="right", padx=5)

    def show_language_menu(self):
        if self._popup_window and self._popup_window.winfo_exists(): self._popup_window.destroy()
        style = ttk.Style();
        style.configure("Menu.TFrame", background=THEME["bg_secondary"]);
        style.configure("Menu.TLabel", background=THEME["bg_secondary"], foreground=THEME["text_primary"],
                        font=("Inter", 12));
        style.map("Menu.TLabel", background=[("active", THEME["hover_accent"])],
                  foreground=[("active", THEME["text_primary"])])
        self._popup_window = tk.Toplevel(self);
        self._popup_window.overrideredirect(True);
        self._popup_window.geometry(f"+{self.winfo_pointerx()}+{self.winfo_pointery()}")
        lang_menu_frame = ttk.Frame(self._popup_window, style="Menu.TFrame");
        lang_menu_frame.pack()
        lang_en_label = ttk.Label(lang_menu_frame, text="English", style="Menu.TLabel", padding=5, width=15);
        lang_en_label.grid(row=0, column=0, sticky="ew");
        lang_en_label.bind("<Button-1>", lambda event: self.change_language_with_menu("EN", lang_menu_frame))
        lang_ru_label = ttk.Label(lang_menu_frame, text="Русский", style="Menu.TLabel", padding=5, width=15);
        lang_ru_label.grid(row=1, column=0, sticky="ew");
        lang_ru_label.bind("<Button-1>", lambda event: self.change_language_with_menu("RU", lang_menu_frame))
        close_button_label = ttk.Label(lang_menu_frame, text="x", style="Menu.TLabel", padding=5, width=20)
        close_button_label.grid(row=2, column=0, sticky="ew")
        close_button_label.bind("<Button-1>",
                                lambda event: self._popup_window.destroy() if self._popup_window else None)
        lang_menu_frame.columnconfigure(0, weight=1);
        lang_menu_frame.rowconfigure(0, weight=1);
        lang_menu_frame.rowconfigure(1, weight=1)
        self.focus_set();
        self._popup_window.bind("<FocusOut>",
                                lambda event: self._popup_window.destroy() if self._popup_window else None)

    def change_language_with_menu(self, lang_code, menu_frame):
        self.change_language(lang_code)
        if self._popup_window and self._popup_window.winfo_exists(): self._popup_window.destroy()

    def show_menu(self):
        if self._popup_window and self._popup_window.winfo_exists(): self._popup_window.destroy()
        style = ttk.Style();
        style.configure("Menu.TFrame", background=THEME["bg_secondary"]);
        style.configure("Menu.TLabel", background=THEME["bg_secondary"], foreground=THEME["text_primary"],
                        font=("Inter", 12));
        style.map("Menu.TLabel", background=[("active", THEME["hover_accent"])],
                  foreground=[("active", THEME["text_primary"])])
        self._popup_window = tk.Toplevel(self);
        self._popup_window.overrideredirect(True);
        self._popup_window.geometry(f"+{self.winfo_pointerx()}+{self.winfo_pointery()}")
        menu_frame = ttk.Frame(self._popup_window, style="Menu.TFrame")
        menu_frame.pack()

        github_label = ttk.Label(menu_frame, text="GitHub", style="Menu.TLabel", padding=5, width=20)
        github_label.grid(row=0, column=0, sticky="ew")
        github_label.bind("<Button-1>", lambda event: self.open_link("https://github.com/infikot/cbd2", menu_frame))

        telegram_label = ttk.Label(menu_frame, text="Telegram", style="Menu.TLabel", padding=5, width=20)
        telegram_label.grid(row=1, column=0, sticky="ew")
        telegram_label.bind("<Button-1>", lambda event: self.open_link("https://t.me/infinite_edit", menu_frame))

        close_button_label = ttk.Label(menu_frame, text="x", style="Menu.TLabel", padding=5, width=20)
        close_button_label.grid(row=2, column=0, sticky="ew")
        close_button_label.bind("<Button-1>",
                                lambda event: self._popup_window.destroy() if self._popup_window else None)

        menu_frame.columnconfigure(0, weight=1);
        [menu_frame.rowconfigure(i, weight=1) for i in range(2)]
        self.focus_set();
        self._popup_window.bind("<FocusOut>",
                                lambda event: self._popup_window.destroy() if self._popup_window else None)


    def open_link(self, url, menu_frame):
        webbrowser.open(url)
        if self._popup_window:
            self._popup_window.destroy()

    def change_language(self, lang_code):
        self.current_lang = lang_code
        self.refresh_ui()

    def refresh_ui(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        self.create_header()
        if self.selected_account:
            self.create_options_ui()
        else:
            self.create_main_ui()

    def create_main_ui(self):
        kill_dota2()
        if not self.accounts:
            empty_frame = ctk.CTkFrame(
                self.main_container,
                fg_color=THEME["bg_secondary"],
                corner_radius=16
            )
            empty_frame.pack(fill="both", expand=True)

            empty_label = ctk.CTkLabel(
                empty_frame,
                text=LANGUAGES[self.current_lang]["no_accounts_found"],
                font=("Inter", 16, "bold"),
                text_color=THEME["text_primary"]
            )
            empty_label.pack(expand=True)
            return

        accounts_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["bg_secondary"],
            corner_radius=16
        )
        accounts_frame.pack(fill="both", expand=True)

        header = ctk.CTkFrame(accounts_frame, fg_color="transparent", height=50)
        header.pack(fill="x", padx=20, pady=10)

        title = ctk.CTkLabel(
            header,
            text=LANGUAGES[self.current_lang]["select_account"],
            font=("Inter", 16, "bold"),
            text_color=THEME["text_primary"]
        )
        title.pack(side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(
            accounts_frame,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for account in self.accounts:
            account_card = AccountCard(
                self.scroll_frame,
                account=account,
                on_select=self.select_account,
                lang_code=self.current_lang
            )
            account_card.pack(fill="x", pady=(0, 10))

    def get_steam_account_info(self, steam_id, account_path):
        vdf_path = os.path.join(account_path, "..", "config", "localconfig.vdf")
        try:
            with open(vdf_path, 'r', encoding='utf-8') as f:
                config_data = vdf.load(f)

            user_config = config_data.get('UserLocalConfigStore', {})
            if not user_config:
                self.log(f"UserLocalConfigStore not found in VDF for {steam_id}", is_error=True, console_only=True)
                return {'personaname': f"User {steam_id}", 'avatar_url': None}

            friends = user_config.get('friends', {})
            account_info = friends.get(steam_id, {})

            # Prefer 'PersonaName' at the top level of 'friends', then look inside the steam_id dict,
            # then use the name history, and finally fall back to "User {steam_id}".
            personaname = friends.get("PersonaName")  # Check for global PersonaName FIRST
            if not personaname:
                personaname = account_info.get('Name')  # Then check for 'Name' within the specific user data.

            if not personaname:
                # Fallback to name history if 'Name' is missing
                if 'NameHistory' in account_info:
                    name_history = account_info['NameHistory']
                    # NameHistory might be a dict (keys are numbers as strings) or a list.  Handle both.
                    if isinstance(name_history, dict):
                        # Get the first name in history (usually the most recent).
                        personaname = next(iter(name_history.values()), None)  # Get first value, or None
                    elif isinstance(name_history, list):
                        personaname = name_history[0] if name_history else None  # get first or None

            if not personaname:
                personaname = f"User {steam_id}"  # Fallback

            avatar_hash = account_info.get('avatar', '')
            avatar_url = f"https://avatars.cloudflare.steamstatic.com/{avatar_hash}_full.jpg" if avatar_hash else None
            return {'personaname': personaname, 'avatar_url': avatar_url}

        except FileNotFoundError:
            self.log(f"File not found: {vdf_path} for {steam_id}", is_error=True, console_only=True)
            return {'personaname': f"User {steam_id}", 'avatar_url': None}
        except (KeyError, AttributeError) as e:
            self.log(f"KeyError or AttributeError accessing VDF data for {steam_id}: {e}", is_error=True,
                     console_only=True)
            return {'personaname': f"User {steam_id}", 'avatar_url': None}
        except Exception as e:
            self.log(f"Error reading vdf for {steam_id}: {e}", is_error=True, console_only=True)
            return {'personaname': f"User {steam_id}", 'avatar_url': None}

    def get_account_folders(self):
        account_folders = []
        try:
            if not self.steam_userdata_path or not os.path.exists(self.steam_userdata_path):
                self.log(f"Steam userdata path not found: {self.steam_userdata_path}", is_error=True)
                return []

            for folder_name in os.listdir(self.steam_userdata_path):
                if folder_name.isdigit():
                    account_path = os.path.join(self.steam_userdata_path, folder_name)
                    dota_config_path = os.path.join(account_path, DOTA_APP_ID)

                    # Check for Dota 2 config directory AND if any config files exist
                    if os.path.isdir(dota_config_path):
                        config_files_exist = False
                        for cfg_dir in [CONFIG_DIR, LOCAL_CFG_DIR, REMOTE_CFG_DIR]:
                            full_cfg_path = os.path.join(dota_config_path, cfg_dir)
                            if os.path.exists(full_cfg_path) and any(os.listdir(full_cfg_path)):
                                config_files_exist = True
                                break  # No need to check further if we found files

                        if not config_files_exist:
                            self.log(f"No config files found for {folder_name}. Skipping.", is_error=False)
                            continue # Skip this account



                        vdf_path = os.path.join(account_path, "config", "localconfig.vdf")
                        if os.path.exists(vdf_path):
                            try:
                                with open(vdf_path, 'r', encoding='utf-8') as f:
                                    config_data = vdf.load(f)
                                    if "UserLocalConfigStore" in config_data and "friends" in config_data[
                                        "UserLocalConfigStore"]:
                                        account_folders.append((folder_name, dota_config_path))  # Use dota config path
                                    else:
                                        self.log(
                                            f"User information not found in localconfig.vdf for {folder_name}. Skipping.",
                                            is_error=False)
                            except Exception as e:
                                self.log(f"Error reading localconfig.vdf for {folder_name}: {e}. Skipping.",
                                         is_error=True)
                        else:
                            self.log(f"localconfig.vdf not found for {folder_name}. Skipping.", is_error=False)

        except Exception as e:
            self.log(f"Error accessing Steam userdata: {e}", is_error=True)
            self.log(traceback.format_exc(), is_error=True, console_only=True)

        return account_folders

    def load_accounts(self):
        account_folders = self.get_account_folders()
        self.accounts = []

        def load_account_data(steam_id, account_path):
            try:
                account_info = self.get_steam_account_info(steam_id, account_path)
                avatar_file_path = None

                if account_info.get('avatar_url'):
                    avatar_file_path = self.download_avatar(account_info['avatar_url'], steam_id)

                account_data = {
                    'account_id': steam_id,
                    'personaname': account_info.get('personaname', f"User {steam_id}"),
                    'avatar': avatar_file_path,  # Store the file path
                    'path': account_path
                }
                self.accounts.append(account_data)
            except Exception as e:
                self.log(f"Error loading account {steam_id}: {e}", is_error=True, console_only=True)

        threads = []
        for steam_id, account_path in account_folders:
            thread = threading.Thread(target=load_account_data, args=(steam_id, account_path))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def download_avatar(self, url, steam_id):
        """Downloads the avatar and saves it locally, returning the file path."""
        if not url:
            return None

        try:
            response = requests.get(url, stream=True, timeout=5)
            response.raise_for_status()

            # Create a directory for avatars if it doesn't exist
            avatar_dir = os.path.join(os.getcwd(), "avatars")
            os.makedirs(avatar_dir, exist_ok=True)

            # Save the avatar with the steam_id as the filename
            file_path = os.path.join(avatar_dir, f"{steam_id}.jpg")
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return file_path

        except Exception as e:
            self.log(f"Error downloading avatar for {steam_id}: {e}", is_error=True, console_only=True)
            return None


    def select_account(self, account):
        self.selected_account = account
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.create_header()
        self.create_options_ui()

    def create_options_ui(self):
        options_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["bg_secondary"],
            corner_radius=16
        )
        options_frame.pack(fill="both", expand=True)

        header = ctk.CTkFrame(
            options_frame,
            fg_color=THEME["card_bg"],
            corner_radius=16,
            height=80
        )
        header.pack(fill="x", padx=20, pady=20)
        header.pack_propagate(False)

        # Avatar display (with rounding)
        avatar_frame = ctk.CTkFrame(header, width=50, height=50, corner_radius=25, fg_color="transparent")
        avatar_frame.pack(side="left", padx=20)
        avatar_frame.pack_propagate(False)

        if self.selected_account.get('avatar'):
            try:
                # Загружаем и изменяем размер аватара
                avatar_image = Image.open(self.selected_account['avatar']).resize((48, 48))

                # Преобразуем в RGBA если необходимо
                if avatar_image.mode != 'RGBA':
                    avatar_image = avatar_image.convert('RGBA')

                # Создаём круглую маску
                mask = Image.new('L', (48, 48), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 48, 48), fill=255)

                # Создаём изображение с прозрачным фоном
                circular_image = Image.new('RGBA', (48, 48), (0, 0, 0, 0))
                circular_image.paste(avatar_image, (0, 0), mask)

                # Конвертируем в PhotoImage
                photo_image = ImageTk.PhotoImage(circular_image)

                # Создаём метку для аватара
                avatar_label = tk.Label(
                    avatar_frame, image=photo_image, bg=THEME["bg_primary"],
                    borderwidth=0, highlightthickness=0
                )
                avatar_label.image = photo_image  # Сохраняем ссылку
                avatar_label.place(relx=0.5, rely=0.5, anchor="center")

            except Exception as e:
                print(f"Ошибка загрузки аватара: {e}")

                # Показываем первую букву имени, если аватар не загрузился
                initial_label = ctk.CTkLabel(
                    avatar_frame,
                    text=self.selected_account['personaname'][0].upper() if self.selected_account[
                        'personaname'] else "?",
                    font=("Inter", 18, "bold"), text_color=THEME["text_primary"]
                )
                initial_label.place(relx=0.5, rely=0.5, anchor="center")

        else:
            # Если нет аватара, показываем первую букву имени
            initial_label = ctk.CTkLabel(
                avatar_frame,
                text=self.selected_account['personaname'][0].upper() if self.selected_account['personaname'] else "?",
                font=("Inter", 18, "bold"), text_color=THEME["text_primary"]
            )
            initial_label.place(relx=0.5, rely=0.5, anchor="center")

        name_label = ctk.CTkLabel(
            header,
            text=self.selected_account['personaname'],
            font=("Inter", 16, "bold"),
            text_color=THEME["text_primary"]
        )
        name_label.pack(side="left", padx=(10, 0))

        buttons_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        buttons_frame.pack(fill="both", expand=True, padx=20, pady=20)

        instruction_label = ctk.CTkLabel(
            buttons_frame,
            text=LANGUAGES[self.current_lang]["warnings2"],
            font=("Inter", 12),
            text_color=THEME["text_secondary"],
            justify="left"
        )
        instruction_label.pack(anchor="w", pady=(0, 20))

        import_btn = AnimatedButton(
            buttons_frame,
            text=LANGUAGES[self.current_lang]["import_config"],
            fg_color=THEME["accent"],
            command=self.show_import_options,
            height=50
        )
        import_btn.pack(fill="x", pady=(0, 10))

        export_btn = AnimatedButton(
            buttons_frame,
            text=LANGUAGES[self.current_lang]["export_config"],
            fg_color=THEME["accent"],
            command=self.export_config,
            height=50
        )
        export_btn.pack(fill="x", pady=(0, 10))

        back_btn = SecondaryButton(
            buttons_frame,
            text=LANGUAGES[self.current_lang]["back"],
            command=lambda: self.back_to_main(),
            height=40
        )
        back_btn.pack(fill="x", pady=(20, 0))

    def show_import_options(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        import_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["bg_secondary"],
            corner_radius=12
        )
        import_frame.pack(fill="both", expand=True)

        title = ctk.CTkLabel(
            import_frame,
            text=LANGUAGES[self.current_lang]["select_source"],
            font=("Segoe UI", 16, "bold"),
            text_color=THEME["text_primary"]
        )
        title.pack(pady=20)

        buttons_frame = ctk.CTkFrame(import_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=20)

        AnimatedButton(
            buttons_frame,
            text=LANGUAGES[self.current_lang]["import_from_file"],
            fg_color=THEME["accent"],
            command=self.import_from_file
        ).pack(fill="x", pady=(0, 8))

        AnimatedButton(
            buttons_frame,
            text=LANGUAGES[self.current_lang]["import_from_account"],
            fg_color=THEME["accent"],
            command=self.show_account_selection
        ).pack(fill="x", pady=(0, 8))

        AnimatedButton(
            buttons_frame,
            text=LANGUAGES[self.current_lang]["back"],
            fg_color=THEME["bg_secondary"],
            command=lambda: self.select_account(self.selected_account)
        ).pack(fill="x", pady=(20, 0))

    def show_account_selection(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

        selection_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["bg_secondary"],
            corner_radius=12
        )
        selection_frame.pack(fill="both", expand=True)

        title = ctk.CTkLabel(
            selection_frame,
            text=LANGUAGES[self.current_lang]["select_account"],
            font=("Segoe UI", 16, "bold"),
            text_color=THEME["text_primary"]
        )
        title.pack(pady=20)

        scroll_frame = ctk.CTkScrollableFrame(
            selection_frame,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        account_found = False
        for account in self.accounts:
            if account['account_id'] != self.selected_account['account_id']:
                AccountCard(
                    scroll_frame,
                    account=account,
                    on_select=lambda acc=account: self.import_from_account(acc),
                    lang_code=self.current_lang
                ).pack(fill="x", pady=(0, 8))
                account_found = True

        if not account_found:
            no_accounts_label = ctk.CTkLabel(
                scroll_frame,
                text=LANGUAGES[self.current_lang]["no_accounts_found"],
                font=("Segoe UI", 14),
                text_color=THEME["text_primary"]
            )
            no_accounts_label.pack(expand=True, pady=20)

        AnimatedButton(
            selection_frame,
            text=LANGUAGES[self.current_lang]["back"],
            fg_color=THEME["bg_secondary"],
            command=self.show_import_options
        ).pack(fill="x", padx=20, pady=20)

    def import_from_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("ConfigBridge Dota 2", "*.cbd2"), ("ZIP files", "*.zip"), ("All files", "*.*")],
            title=LANGUAGES[self.current_lang]["import_from_file"]
        )
        if file_path:
            try:
                self.import_config(self.selected_account['path'], file_path)
                self.show_success_message(LANGUAGES[self.current_lang]["config_imported"])
            except Exception as e:
                self.log(f"Error importing from file: {e}", is_error=True)
                self.log(traceback.format_exc(), is_error=True, console_only=True)
                self.show_error_message(str(e))
            finally:
                self.select_account(self.selected_account)

    def import_from_account(self, source_account):
        try:
            self.import_config(self.selected_account['path'], source_account['path'])
            self.show_success_message(LANGUAGES[self.current_lang]["config_imported"])
        except Exception as e:
            self.log(f"Error importing from account: {e}", is_error=True)
            self.log(traceback.format_exc(), is_error=True, console_only=True)
            self.show_error_message(str(e))
        finally:
            self.select_account(self.selected_account)

    def show_success_message(self, message):
        self.status_label.configure(
            text=message,
            text_color=THEME["success"]
        )
        self.after(3000, lambda: self.status_label.configure(text=""))

    def import_config(self, target_account_path, source_path):
        try:
            base_cfg_dir = os.path.join(target_account_path, CONFIG_DIR)
            local_cfg_dir = os.path.join(target_account_path, LOCAL_CFG_DIR)
            remote_cfg_dir = os.path.join(target_account_path, REMOTE_CFG_DIR)

            for cfg_dir in [base_cfg_dir, local_cfg_dir, remote_cfg_dir]:
                if not os.path.exists(cfg_dir):
                    os.makedirs(cfg_dir)
                    self.log(f"Created directory: {cfg_dir}")

            if os.path.isfile(source_path):
                try:
                    with zipfile.ZipFile(source_path, 'r') as zip_ref:
                        temp_extract_dir = os.path.join(os.path.dirname(source_path),
                                                        f"temp_extract_{int(time.time())}")
                        os.makedirs(temp_extract_dir, exist_ok=True)

                        try:
                            zip_ref.extractall(temp_extract_dir)
                            self._copy_config_files(temp_extract_dir, target_account_path)

                        finally:
                            if os.path.exists(temp_extract_dir):
                                shutil.rmtree(temp_extract_dir)

                    self.log(f"Imported config from file {source_path}")

                except zipfile.BadZipFile:
                    self.log(f"Invalid zip file: {source_path}", is_error=True)
                    raise ValueError("The selected file is not a valid archive")

            elif os.path.isdir(source_path):
                has_configs = self._copy_config_files(source_path, target_account_path)

                if not has_configs:
                    self.log(f"No configuration files found in source", is_error=True)
                    raise FileNotFoundError(LANGUAGES[self.current_lang]["no_config_files"])

                self.log(f"Imported config from account {source_path}")
            else:
                raise ValueError("Invalid source path")

        except Exception as e:
            self.log(f"Error during import: {e}", is_error=True)
            self.log(traceback.format_exc(), is_error=True, console_only=True)
            raise

    def _copy_config_files(self, source_path, target_path):
        has_copied_files = False

        source_dirs = [
            os.path.join(source_path, CONFIG_DIR),
            os.path.join(source_path, LOCAL_CFG_DIR),
            os.path.join(source_path, REMOTE_CFG_DIR)
        ]

        target_dirs = [
            os.path.join(target_path, CONFIG_DIR),
            os.path.join(target_path, LOCAL_CFG_DIR),
            os.path.join(target_path, REMOTE_CFG_DIR)
        ]

        for target_dir in target_dirs:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

        for i, source_dir in enumerate(source_dirs):
            if os.path.exists(source_dir) and os.path.isdir(source_dir):
                target_dir = target_dirs[i]

                for item in os.listdir(target_dir):
                    item_path = os.path.join(target_dir, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)

                for item in os.listdir(source_dir):
                    src_item = os.path.join(source_dir, item)
                    dst_item = os.path.join(target_dir, item)

                    if os.path.isfile(src_item):
                        shutil.copy2(src_item, dst_item)
                        has_copied_files = True
                    elif os.path.isdir(src_item):
                        shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                        has_copied_files = True

        return has_copied_files

    def export_config(self):
        try:
            base_cfg_dir = os.path.join(self.selected_account['path'], CONFIG_DIR)
            local_cfg_dir = os.path.join(self.selected_account['path'], LOCAL_CFG_DIR)
            remote_cfg_dir = os.path.join(self.selected_account['path'], REMOTE_CFG_DIR)

            has_config_files = False
            for cfg_dir in [base_cfg_dir, local_cfg_dir, remote_cfg_dir]:
                if os.path.exists(cfg_dir) and os.listdir(cfg_dir):
                    has_config_files = True
                    break

            if not has_config_files:
                self.log(LANGUAGES[self.current_lang]["no_config_files"], is_error=True)
                self.show_error_message(LANGUAGES[self.current_lang]["no_config_files"])
                return

            default_filename = f"dota2_config_{self.selected_account['personaname'].replace(' ', '_')}.cbd2"

            save_path = filedialog.asksaveasfilename(
                defaultextension=".cbd2",
                initialfile=default_filename,
                filetypes=[("ConfigBridge Dota 2", "*.cbd2"), ("ZIP files", "*.zip")]
            )

            if save_path:
                temp_dir = os.path.join(os.path.dirname(save_path), f"temp_export_{int(time.time())}")
                os.makedirs(temp_dir, exist_ok=True)

                try:
                    temp_cfg_dir = os.path.join(temp_dir, CONFIG_DIR)
                    temp_local_cfg_dir = os.path.join(temp_dir, LOCAL_CFG_DIR)
                    temp_remote_cfg_dir = os.path.join(temp_dir, REMOTE_CFG_DIR)

                    if os.path.exists(base_cfg_dir):
                        os.makedirs(temp_cfg_dir, exist_ok=True)
                        for item in os.listdir(base_cfg_dir):
                            src_path = os.path.join(base_cfg_dir, item)
                            dst_path = os.path.join(temp_cfg_dir, item)
                            if os.path.isfile(src_path):
                                shutil.copy2(src_path, dst_path)
                            elif os.path.isdir(src_path):
                                shutil.copytree(src_path, dst_path)

                    if os.path.exists(local_cfg_dir):
                        os.makedirs(os.path.dirname(temp_local_cfg_dir), exist_ok=True)
                        os.makedirs(temp_local_cfg_dir, exist_ok=True)
                        for item in os.listdir(local_cfg_dir):
                            src_path = os.path.join(local_cfg_dir, item)
                            dst_path = os.path.join(temp_local_cfg_dir, item)
                            if os.path.isfile(src_path):
                                shutil.copy2(src_path, dst_path)
                            elif os.path.isdir(src_path):
                                shutil.copytree(src_path, dst_path)

                    if os.path.exists(remote_cfg_dir):
                        os.makedirs(os.path.dirname(temp_remote_cfg_dir), exist_ok=True)
                        os.makedirs(temp_remote_cfg_dir, exist_ok=True)
                        for item in os.listdir(remote_cfg_dir):
                            src_path = os.path.join(remote_cfg_dir, item)
                            dst_path = os.path.join(temp_remote_cfg_dir, item)
                            if os.path.isfile(src_path):
                                shutil.copy2(src_path, dst_path)
                            elif os.path.isdir(src_path):
                                shutil.copytree(src_path, dst_path)

                    metadata = {
                        "exported_by": self.selected_account['personaname'],
                        "account_id": self.selected_account['account_id'],
                        "export_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "exporter_version": "2.0.1"
                    }

                    with open(os.path.join(temp_dir, "metadata.json"), 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)

                    with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(temp_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                zipf.write(
                                    file_path,
                                    os.path.relpath(file_path, temp_dir)
                                )

                    self.log(f"Configuration exported to {save_path}")
                    self.show_success_message(LANGUAGES[self.current_lang]["config_exported"])

                finally:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)

        except Exception as e:
            self.log(f"Error during export: {e}", is_error=True)
            self.log(traceback.format_exc(), is_error=True, console_only=True)
            self.show_error_message(str(e))

    def back_to_main(self):
        self.selected_account = None
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.create_header()
        self.create_main_ui()

    def on_closing(self):
        try:
            if self.log_window:
                self.log_window.destroy()
            if self._popup_window:
                self._popup_window.destroy()
            self.destroy()
        except Exception as e:
            print(f"Error during closing: {e}")
            self.destroy()

from PIL import Image, ImageTk, ImageDraw

if __name__ == "__main__":
    try:
        ctk.set_widget_scaling(1.0)
        ctk.set_appearance_mode("dark")
        app = ConfigBridgeApp()

        try:
            icon_path = resource_path("assets/icon.ico")
            if os.path.exists(icon_path):
                app.iconbitmap(icon_path)
        except Exception as e:
            print(f"Cannot set icon: {e}")

        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()

    except Exception as e:
        print(f"Fatal error: {e}")
        print(traceback.format_exc())

        try:
            messagebox.showerror("ConfigBridge Error", f"Fatal error:\n{e}")
        except:
            pass