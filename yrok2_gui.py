import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
from groq import Groq
import json
from datetime import datetime
import os
import io
import speech_recognition as sr

# --- ІНТЕГРАЦІЯ gTTS ТА PYGAME ---
try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    print("УВАГА: Для українського голосу встановіть: pip install gTTS pygame")

from PIL import Image, ImageTk, ImageDraw

# --- КОНФІГУРАЦІЯ ---
API_KEY = ""
APP_TITLE = "SANCHESI AI"

COLORS = {
    "gradient_start": "#ff9a9e",
    "gradient_end": "#a18cd1",
    "glass_panel": (42, 27, 61, 140),  
    "accent": "#E980FC",              
    "text_main": "#ffffff",
    "text_dim": "#b8b8d9",
    "btn_bg": "#44318D",
    "success": "#10b981",
    "error": "#ef4444"
}
CHAT_BG = "#130a1e"  

try: 
    client = Groq(api_key=API_KEY)
except: 
    client = None

recognizer = sr.Recognizer()
microphone = sr.Microphone()

voice_mode_enabled = False
SPEECH_LOG_FILE = "log_speech.txt"

EMOTIONS = {"neutral": "😊", "happy": "😄", "thinking": "🤔", "excited": "🤩", "confused": "😕", "sad": "😢", "angry": "😠", "surprised": "😲", "cool": "😎", "love": "😍"}
EMOTION_MAP = {"дякую": "happy", "спасибі": "happy", "чудово": "excited", "супер": "excited", "класно": "cool", "помилка": "sad", "error": "sad", "не працює": "confused", "привіт": "happy", "hello": "happy", "допоможи": "thinking", "код": "thinking", "люблю": "love", "злий": "angry", "вау": "surprised"}
PERSONALITIES = {"Енергійний вчитель": "Ти енергійний вчитель, пояснюєш просто.", "Мудрий філософ": "Ти мудрий філософ.", "Веселий друг": "Ти веселий друг, жартуєш.", "Строгий професор": "Ти строгий професор.", "Креативний митець": "Ти креативний митець.", "Технічний експерт": "Ти технічний експерт.", "Дитячий аніматор": "Ти дитячий аніматор."}


# =====================================================================
# НОВИЙ КЛАС: GLASS BUTTON (Ідеальна прозорість для Головного Вікна)
# =====================================================================
class GlassButton:
    def __init__(self, canvas, w, h, text, color, command, state="normal"):
        self.canvas = canvas
        self.w, self.h = w, h
        self.command = command
        self.state = state
        self.tag = f"btn_{id(self)}"
        
        self.img_normal = self.create_img(w, h, color, 140, 80, 15)
        self.img_hover = self.create_img(w, h, color, 200, 180, 40)
        self.img_click = self.create_img(w, h, color, 255, 255, 0)
        self.img_disabled = self.create_img(w, h, "#444444", 60, 30, 5)
        
        img_use = self.img_normal if state == "normal" else self.img_disabled
        txt_col = "white" if state == "normal" else "#888888"
        
        self.item = canvas.create_image(-1000, -1000, image=img_use, anchor="nw", tags=(self.tag, "glass_btn"))
        self.text_item = canvas.create_text(-1000, -1000, text=text, fill=txt_col, font=("Segoe UI", 10, "bold"), tags=(self.tag, "glass_btn_txt"))
        
        self.canvas.tag_bind(self.tag, "<Enter>", self.on_enter)
        self.canvas.tag_bind(self.tag, "<Leave>", self.on_leave)
        self.canvas.tag_bind(self.tag, "<Button-1>", self.on_click)
        self.canvas.tag_bind(self.tag, "<ButtonRelease-1>", self.on_release)
        
    def create_img(self, w, h, hex_color, bg_alpha, out_alpha, gloss_alpha):
        img = Image.new('RGBA', (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        c = hex_color.lstrip('#')
        fill = tuple(int(c[i:i+2], 16) for i in (0, 2, 4)) + (bg_alpha,)
        draw.rounded_rectangle((0, 0, w-1, h-1), radius=h//4, fill=fill, outline=(255,255,255,out_alpha), width=1)
        if gloss_alpha > 0:
            draw.rounded_rectangle((1, 1, w-2, h//2), radius=(h//4)-1, fill=(255,255,255,gloss_alpha))
        return ImageTk.PhotoImage(img)
        
    def place(self, x, y):
        self.canvas.coords(self.item, x, y)
        self.canvas.coords(self.text_item, x + self.w//2, y + self.h//2)

    def config(self, text=None, state=None):
        if text: self.canvas.itemconfig(self.text_item, text=text)
        if state:
            self.state = state
            self.canvas.itemconfig(self.item, image=self.img_normal if state=="normal" else self.img_disabled)
            self.canvas.itemconfig(self.text_item, fill="white" if state=="normal" else "#888888")
            
    def on_enter(self, e):
        if self.state == "normal": self.canvas.itemconfig(self.item, image=self.img_hover)
    def on_leave(self, e):
        if self.state == "normal": self.canvas.itemconfig(self.item, image=self.img_normal)
    def on_click(self, e):
        if self.state == "normal": self.canvas.itemconfig(self.item, image=self.img_click)
    def on_release(self, e):
        if self.state == "normal":
            self.canvas.itemconfig(self.item, image=self.img_hover)
            if self.command: self.command()


# =====================================================================
# НОВИЙ КЛАС: SOLID BUTTON (Для діалогових вікон)
# =====================================================================
class SolidButton(tk.Canvas):
    def __init__(self, parent, text, color="#44318D", command=None, height=35):
        super().__init__(parent, height=height, bg=CHAT_BG, highlightthickness=0)
        self.text_val = text
        self.base_color = color
        self.command = command
        self.state = "normal"
        self.hover = False
        self.clicked = False

        self.bind("<Configure>", lambda e: self.draw_button())
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_enter(self, e):
        if self.state != "disabled": self.hover = True; self.draw_button()
    def on_leave(self, e):
        self.hover = False; self.clicked = False; self.draw_button()
    def on_click(self, e):
        if self.state != "disabled": self.clicked = True; self.draw_button()
    def on_release(self, e):
        if self.state != "disabled" and self.clicked:
            self.clicked = False; self.draw_button()
            if self.command: self.command()

    def draw_button(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10: return
        img = Image.new('RGBA', (w, h), CHAT_BG)
        overlay = Image.new('RGBA', (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(overlay)

        bg_alpha = 255 if self.clicked else (220 if self.hover else 160)
        outline_alpha = 200 if self.hover else 80
        gloss_alpha = 40 if self.hover else 15
        txt_col = "#ffffff"

        c = self.base_color.lstrip('#')
        fill_color = tuple(int(c[i:i+2], 16) for i in (0, 2, 4)) + (bg_alpha,)
        outline_color = (255, 255, 255, outline_alpha)
        rad = h // 4

        draw.rounded_rectangle((1, 1, w-2, h-2), radius=rad, fill=fill_color, outline=outline_color, width=1)
        if not self.clicked:
            draw.rounded_rectangle((2, 2, w-3, h//2), radius=rad-1, fill=(255, 255, 255, gloss_alpha))

        final = Image.alpha_composite(img, overlay)
        self.image_ref = ImageTk.PhotoImage(final)
        self.delete("all")
        self.create_image(0, 0, image=self.image_ref, anchor="nw")
        self.create_text(w//2, h//2 + (1 if self.clicked else 0), text=self.text_val, fill=txt_col, font=("Segoe UI", 10, "bold"))


# --- СТИЛІЗОВАНІ ДІАЛОГОВІ ВІКНА ---
class StyledToplevel(tk.Toplevel):
    def __init__(self, app, title, w, h):
        super().__init__(app.root)
        self.app = app
        self.title(title)
        self.geometry(f"{w}x{h}")
        self.configure(bg=CHAT_BG)
        
        x = app.root.winfo_x() + (app.root.winfo_width() // 2) - (w // 2)
        y = app.root.winfo_y() + (app.root.winfo_height() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

        self.master_image = self._generate_bg(max(w, 800), max(h, 600))
        self.bg_canvas = tk.Canvas(self, highlightthickness=0, bg=CHAT_BG)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        self.bind("<Configure>", self._on_resize)
        self.content = tk.Frame(self.bg_canvas, bg=CHAT_BG)

    def _generate_bg(self, w, h):
        base = Image.new('RGB', (1, 2))
        c1 = tuple(int(COLORS["gradient_start"].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        c2 = tuple(int(COLORS["gradient_end"].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        base.putpixel((0, 0), c1)
        base.putpixel((0, 1), c2)
        return base.resize((w, h), resample=Image.Resampling.BILINEAR).convert("RGBA")

    def _on_resize(self, e):
        if e.widget != self: return
        w, h = e.width, e.height
        if w < 10 or h < 10: return
        if w > self.master_image.width or h > self.master_image.height:
            self.master_image = self._generate_bg(w, h)
            
        bg = self.master_image.crop((0, 0, w, h))
        overlay = Image.new('RGBA', (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        draw.rounded_rectangle((10, 10, w-10, h-10), radius=15, fill=COLORS["glass_panel"], outline=COLORS["accent"])
        inner_rgb = tuple(int(CHAT_BG.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (255,)
        draw.rounded_rectangle((20, 50, w-20, h-20), radius=12, fill=inner_rgb)
        
        final = Image.alpha_composite(bg, overlay)
        self.bg_tk = ImageTk.PhotoImage(final)
        self.bg_canvas.delete("bg")
        self.bg_canvas.create_image(0,0, image=self.bg_tk, anchor="nw", tags="bg")
        self.bg_canvas.tag_lower("bg")
        
        self.bg_canvas.delete("title")
        self.bg_canvas.create_text(25, 30, text=self.title(), fill=COLORS["accent"], font=("Segoe UI", 12, "bold"), anchor="w", tags="title")
        self.content.place(x=25, y=55, width=w-50, height=h-80)


# --- ГОЛОВНИЙ ДОДАТОК ---
class SanchesiFullGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} - Ultimate Native Glass")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)
        self.root.configure(bg=CHAT_BG) 
        
        self.current_emotion = "neutral"
        self.last_assistant_message = "" 
        self.was_voice_input = False 
        
        # Завантаження пам'яті
        self.load_history()
        
        self._generate_master()
        self.bg_canvas = tk.Canvas(root, highlightthickness=0, bg=CHAT_BG)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)

        self.setup_styles()
        self.create_widgets()
        
        self.resize_job = None
        self.root.bind("<Configure>", self._on_resize)
        self.refresh_chat_display()

    # --- ЗБЕРЕЖЕННЯ ТА ВІДНОВЛЕННЯ ---
    def load_history(self):
        if not os.path.exists("sessions"): os.makedirs("sessions")
        self.history_file = "sessions/chat_history.json"
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.chats = json.load(f)
                if not self.chats: raise ValueError
                
                max_num = 1
                for cid in self.chats.keys():
                    if cid.startswith("Чат "):
                        try:
                            num = int(cid.split(" ")[1])
                            if num > max_num: max_num = num
                        except: pass
                self.chat_counter = max_num
                self.current_chat_id = list(self.chats.keys())[-1] 
            else:
                self._init_default_chat()
        except:
            self._init_default_chat()

    def _init_default_chat(self):
        self.chat_counter = 1
        self.current_chat_id = f"Чат {self.chat_counter}"
        self.chats = {
            self.current_chat_id: {
                "api": [{"role": "system", "content": PERSONALITIES["Енергійний вчитель"]}],
                "ui": [] 
            }
        }

    def auto_save(self):
        try:
            os.makedirs("sessions", exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.chats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("ПОМИЛКА ЗБЕРЕЖЕННЯ:", e)

    # --- ІНШЕ ---
    def _generate_master(self):
        w, h = 2500, 1500
        base = Image.new('RGB', (1, 2))
        c1 = tuple(int(COLORS["gradient_start"].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        c2 = tuple(int(COLORS["gradient_end"].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        base.putpixel((0, 0), c1)
        base.putpixel((0, 1), c2)
        self.master_image = base.resize((w, h), resample=Image.Resampling.BILINEAR).convert("RGBA")

    def fix_paste(self, widget):
        def _paste(event):
            try:
                widget.insert(tk.INSERT, widget.clipboard_get())
                return 'break'
            except: pass
        widget.bind('<Control-v>', _paste)
        widget.bind('<Command-v>', _paste)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        # Робимо Combobox красивим і темним, щоб він гармоніював зі склом
        style.configure("Modern.TCombobox", fieldbackground="#211533", background="#211533", foreground="white", arrowcolor="white", borderwidth=0)
        self.root.option_add('*TCombobox*Listbox.background', '#211533')
        self.root.option_add('*TCombobox*Listbox.foreground', 'white')
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLORS["accent"])
        style.configure("TScrollbar", gripcount=0, background=COLORS["btn_bg"], troughcolor="#1a1125", bordercolor="#1a1125", arrowcolor="white")

    def create_widgets(self):
        self.inp = tk.Text(self.bg_canvas, bg=CHAT_BG, fg="white", font=("Segoe UI", 12), bd=0, insertbackground="white", padx=10, pady=10)
        self.inp.bind("<Return>", self.send_message)
        self.fix_paste(self.inp)
        
        self.chat = scrolledtext.ScrolledText(self.bg_canvas, wrap=tk.WORD, bg=CHAT_BG, fg="white", font=("Segoe UI", 11), bd=0, padx=10, pady=10, insertbackground="white")
        
        # --- ТЕГИ ДЛЯ MARKDOWN ---
        self.chat.tag_config("user", foreground="#5eead4", font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("assistant", foreground=COLORS["text_dim"], font=("Segoe UI", 11))
        self.chat.tag_config("system", foreground="#f87171", font=("Segoe UI", 10, "italic"))
        self.chat.tag_config("md_h1", font=("Segoe UI", 16, "bold"), foreground=COLORS["accent"])
        self.chat.tag_config("md_h2", font=("Segoe UI", 14, "bold"), foreground="white")
        self.chat.tag_config("md_h3", font=("Segoe UI", 12, "bold"), foreground=COLORS["text_dim"])
        self.chat.tag_config("md_bold", font=("Segoe UI", 11, "bold"), foreground="white")
        self.chat.tag_config("md_italic", font=("Segoe UI", 11, "italic"), foreground="white")
        self.chat.tag_config("md_code", font=("Consolas", 11), background="#0f0914", foreground="#a6e3a1")

        # Основні кнопки на фоні (Help, Send)
        self.btn_help = GlassButton(self.bg_canvas, 40, 40, "?", COLORS["btn_bg"], self.show_help)
        self.btn_send = GlassButton(self.bg_canvas, 150, 40, "📤 Відправити", COLORS["accent"], lambda: self.send_message(None))

        # ПРОЗОРЕ МЕНЮ
        self.menu_scroll = tk.Canvas(self.bg_canvas, highlightthickness=0, bg="#111") 
        # bg=#111 тут тимчасове, воно повністю перекриється картинкою градієнта
        
        self.menu_scroll.bind("<MouseWheel>", self._on_menu_scroll)
        self.menu_scr_bar = ttk.Scrollbar(self.bg_canvas, orient="vertical", command=self.menu_scroll_yview)
        
        self.build_menu_content()

    def _on_menu_scroll(self, event):
        self.menu_scroll.yview_scroll(int(-1*(event.delta/120)), "units")
        self.update_menu_bg_pos()

    def menu_scroll_yview(self, *args):
        self.menu_scroll.yview(*args)
        self.update_menu_bg_pos()

    def update_menu_bg_pos(self):
        """Фіксує фон меню на місці під час скролу!"""
        self.menu_scroll.coords("menu_bg_img", 0, self.menu_scroll.canvasy(0))

    def build_menu_content(self):
        self.menu_scroll.delete("all")
        self.menu_scroll.create_image(0, 0, image="", anchor="nw", tags="menu_bg_img")
        
        y = 10
        self.menu_btns = []

        def add_title(txt):
            nonlocal y
            self.menu_scroll.create_text(15, y, text=txt, fill=COLORS["text_dim"], font=("Segoe UI", 10, "bold"), anchor="nw")
            y += 30
            
        def add_cb(var, values, command):
            nonlocal y
            cb = ttk.Combobox(self.menu_scroll, textvariable=var, values=values, state="readonly", style="Modern.TCombobox")
            cb.bind("<<ComboboxSelected>>", command)
            self.menu_scroll.create_window(15, y, window=cb, width=250, height=30, anchor="nw")
            y += 40
            return cb

        def add_btn(txt, color, cmd, state="normal"):
            nonlocal y
            btn = GlassButton(self.menu_scroll, 250, 35, txt, color, cmd, state)
            btn.place(15, y)
            self.menu_btns.append(btn)
            y += 40
            return btn

        add_title("🎭 Характер")
        self.p_var = tk.StringVar(value="Енергійний вчитель")
        add_cb(self.p_var, list(PERSONALITIES.keys()), self.change_personality)

        add_title("🗂 Чати")
        self.chat_var = tk.StringVar(value=self.current_chat_id)
        self.chat_cb = add_cb(self.chat_var, list(self.chats.keys()), self.on_chat_selected)
        add_btn("➕ Новий чат", COLORS["success"], self.create_new_chat)
        add_btn("✏️ Перейменувати", "#f59e0b", self.rename_chat)

        add_title("🎤 Голос")
        self.voice_btn = add_btn("🔇 Авто-озвучка (Вимк)", "#5b86e5", self.toggle_voice)
        self.listen_btn = add_btn("🎤 Слухати зараз", COLORS["success"], self.start_listening)
        self.read_btn = add_btn("🔊 Озвучити відповідь", "#8b5cf6", self.read_last_response)

        add_title("✨ Інструменти")
        funcs = [("📜 Вірш", self.generate_poem, "#8b5cf6"), ("📚 Історія", self.generate_story, "#ec4899"), ("🌍 Переклад", self.translate_text, "#3b82f6"), ("🧒 Просто", self.explain_simple, "#10b981"), ("💡 Ідеї", self.brainstorm, "#f59e0b"), ("💻 Код", self.code_helper, "#06b6d4"), ("✨ Мотивація", self.motivation, "#f43f5e")]
        for t, cmd, col in funcs: 
            add_btn(t, col, cmd)

        add_title("⚙️ Система")
        sys_funcs = [("📊 Статистика", self.show_stats, "#6366f1"), ("📝 Лог", self.show_log, "#8b5cf6"), ("🧹 Очистити поточний", self.clear_chat, "#ef4444"), ("💾 Зробити Бекап", self.save_backup, "#10b981")]
        for t, cmd, col in sys_funcs: 
            add_btn(t, col, cmd)

        self.menu_scroll.config(scrollregion=(0, 0, 280, y + 20))

    def _on_resize(self, e):
        if e.widget == self.root:
            if self.resize_job: self.root.after_cancel(self.resize_job)
            self.resize_job = self.root.after(30, self.redraw_all)

    def redraw_all(self):
        w, h = self.root.winfo_width(), self.root.winfo_height()
        if w < 10 or h < 10: return
        
        bg = self.master_image.crop((0, 0, w, h))
        overlay = Image.new('RGBA', (w, h), (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        chat_rgb = tuple(int(CHAT_BG.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (255,)
        
        P = 20
        M_W = 320 
        aw = w - P*3 - M_W
        
        draw.rounded_rectangle((P, P, w-P, P+70), radius=20, fill=COLORS["glass_panel"], outline=COLORS["accent"])
        draw.rounded_rectangle((P, P+85, P+aw, P+235), radius=20, fill=COLORS["glass_panel"], outline=COLORS["accent"])
        draw.rounded_rectangle((P, P+250, P+aw, h-P-105), radius=20, fill=COLORS["glass_panel"], outline=COLORS["accent"])
        draw.rounded_rectangle((P+15, P+290, P+aw-15, h-P-120), radius=10, fill=chat_rgb)
        
        # Меню - ТІЛЬКИ СКЛЯНА РАМКА!
        draw.rounded_rectangle((w-P-M_W, P+85, w-P, h-P-105), radius=20, fill=COLORS["glass_panel"], outline=COLORS["accent"])
        
        draw.rounded_rectangle((P, h-P-90, w-P, h-P), radius=20, fill=COLORS["glass_panel"], outline=COLORS["accent"])
        draw.rounded_rectangle((P+15, h-P-65, w-P-180, h-P-15), radius=10, fill=chat_rgb)

        final = Image.alpha_composite(bg, overlay)
        self.bg_tk = ImageTk.PhotoImage(final)
        self.bg_canvas.delete("bg_base")
        self.bg_canvas.create_image(0,0, image=self.bg_tk, anchor="nw", tags="bg_base")
        self.bg_canvas.tag_lower("bg_base")

        # Оновлюємо фон самого меню (ЩОБ БУВ ПРОЗОРИМ)
        menu_crop = final.crop((w-P-M_W+15, P+130, w-P-15, h-P-120))
        self.menu_bg_tk = ImageTk.PhotoImage(menu_crop)
        self.menu_scroll.itemconfig("menu_bg_img", image=self.menu_bg_tk)
        self.update_menu_bg_pos()

        self.bg_canvas.delete("static_txt")
        self.bg_canvas.create_text(P+20, P+35, text=APP_TITLE, fill="white", font=("Segoe UI", 22, "bold"), anchor="w", tags="static_txt")
        self.bg_canvas.create_text(P+20, P+270, text=f"💬 {self.current_chat_id}", fill="white", font=("Segoe UI", 12, "bold"), anchor="w", tags="static_txt")
        self.bg_canvas.create_text(w-P-M_W+20, P+108, text="🎨 Меню", fill="white", font=("Segoe UI", 14, "bold"), anchor="w", tags="static_txt")

        self.bg_canvas.delete("header_emo")
        self.bg_canvas.create_text(P+300, P+35, text=f"{EMOTIONS[self.current_emotion]} {self.current_emotion.title()}", fill=COLORS["accent"], font=("Segoe UI Emoji", 16, "bold"), anchor="w", tags="header_emo")
        
        self.bg_canvas.delete("status_txt")
        self.bg_canvas.create_text(P+20, h-P-75, text="✅ Готовий", fill=COLORS["success"], font=("Segoe UI", 9, "bold"), anchor="w", tags="status_txt")
        
        self.bg_canvas.delete("voice_txt")
        v_txt = "🔊 Авто-озвучка: УВІМК" if voice_mode_enabled else "🔇 Авто-озвучка: ВИМК"
        v_col = COLORS["success"] if voice_mode_enabled else COLORS["text_dim"]
        self.bg_canvas.create_text(w-P-180, h-P-75, text=v_txt, fill=v_col, font=("Segoe UI", 9), anchor="e", tags="voice_txt")

        self.update_avatar_only(P, w, aw)

        self.chat.place(x=P+20, y=P+295, width=aw-40, height=(h-P-120)-(P+295))
        self.menu_scroll.place(x=w-P-M_W+15, y=P+130, width=M_W-30, height=(h-P-120)-(P+130))
        self.menu_scr_bar.place(x=w-P-30, y=P+130, width=15, height=(h-P-120)-(P+130))
        self.inp.place(x=P+20, y=h-P-60, width=(w-P-180)-(P+30), height=40)

        # Розміщуємо головні кнопки
        self.btn_help.place(w-P-50, P+15)
        self.btn_send.place(w-P-165, h-P-75)

    def update_avatar_only(self, P=None, w=None, aw=None):
        if P is None:
            w, h = self.root.winfo_width(), self.root.winfo_height()
            P = 20; M_W = 320; aw = w - P*3 - M_W
        
        cx, cy = P + aw//2, P + 160
        self.bg_canvas.delete("avatar_gfx")
        self.bg_canvas.create_oval(cx-45, cy-45, cx+45, cy+45, outline=COLORS["accent"], width=2, tags="avatar_gfx")
        try:
            path = f"avatars/avatar_{self.current_emotion}.png"
            if not os.path.exists(path): path = "avatars/avatar_neutral.png"
            img = Image.open(path).resize((80, 80), Image.Resampling.LANCZOS)
            mask = Image.new("L", (80, 80), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 80, 80), fill=255)
            out = Image.new("RGBA", (80, 80), (0,0,0,0))
            out.paste(img, (0, 0), mask)
            self.tk_av = ImageTk.PhotoImage(out)
            self.bg_canvas.create_image(cx, cy, image=self.tk_av, tags="avatar_gfx")
        except:
            self.bg_canvas.create_text(cx, cy, text=EMOTIONS.get(self.current_emotion, "😊"), font=("Arial", 40), tags="avatar_gfx")

    # --- МУЛЬТИ-ЧАТ ЛОГІКА ---
    def create_new_chat(self):
        self.chat_counter += 1
        new_id = f"Чат {self.chat_counter}"
        self.chats[new_id] = {
            "api": [{"role": "system", "content": PERSONALITIES[self.p_var.get()]}],
            "ui": []
        }
        self.current_chat_id = new_id
        self.chat_cb.config(values=list(self.chats.keys()))
        self.chat_var.set(new_id)
        self.auto_save()
        self.refresh_chat_display()
        self.redraw_all()

    def rename_chat(self):
        new_name = simpledialog.askstring("Перейменування", "Введіть нову назву чату:", parent=self.root)
        if not new_name: return
        new_name = new_name.strip()
        if not new_name or new_name == self.current_chat_id: return
        if new_name in self.chats:
            messagebox.showerror("Помилка", "Чат з такою назвою вже існує.", parent=self.root)
            return

        self.chats[new_name] = self.chats.pop(self.current_chat_id)
        self.current_chat_id = new_name
        self.chat_cb.config(values=list(self.chats.keys()))
        self.chat_var.set(new_name)
        
        self.refresh_chat_display()
        self.redraw_all()
        self.auto_save()

    def on_chat_selected(self, event):
        self.current_chat_id = self.chat_var.get()
        self.refresh_chat_display()
        self.redraw_all() 

    def refresh_chat_display(self):
        self.chat.config(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        for sender, text, ts in self.chats[self.current_chat_id]["ui"]:
            tag = "user" if sender == "Ви" else "assistant" if sender == "Асистент" else "system"
            self.chat.insert(tk.END, f"\n{sender} [{ts}]:\n", tag)
            if sender == "Асистент": self.insert_markdown(text)
            else: self.chat.insert(tk.END, f"{text}\n", tag)
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    # --- ЛОГІКА, ПАРСЕР ТА gTTS ---
    def send_message(self, event):
        if event and event.state & 0x1: return
        msg = self.inp.get("1.0", tk.END).strip()
        if not msg: return "break"
        self.inp.delete("1.0", tk.END)
        self.add_message("Ви", msg, "#4ecca3")
        
        is_voice = self.was_voice_input
        self.was_voice_input = False 
        
        threading.Thread(target=self.process_message, args=(msg, is_voice), daemon=True).start()
        return "break"

    def _parse_inline(self, text, base_tag):
        b_parts = text.split("**")
        for j, b_part in enumerate(b_parts):
            if j % 2 == 1:
                self.chat.insert(tk.END, b_part, "md_bold")
            else:
                i_parts = b_part.split("*")
                for k, i_part in enumerate(i_parts):
                    if k % 2 == 1: self.chat.insert(tk.END, i_part, "md_italic")
                    else: self.chat.insert(tk.END, i_part, base_tag)

    def insert_markdown(self, text):
        blocks = text.split("```")
        for i, block in enumerate(blocks):
            if i % 2 == 1:
                lines = block.split('\n', 1)
                code_text = lines[1] if len(lines) > 1 else block
                self.chat.insert(tk.END, f"\n{code_text.strip()}\n\n", "md_code")
            else:
                lines = block.split('\n')
                for line in lines:
                    if line.startswith('### '): self._parse_inline(line[4:] + '\n', "md_h3")
                    elif line.startswith('## '): self._parse_inline(line[3:] + '\n', "md_h2")
                    elif line.startswith('# '): self._parse_inline(line[2:] + '\n', "md_h1")
                    elif line.startswith('- ') or line.startswith('* '): self._parse_inline(" • " + line[2:] + '\n', "assistant")
                    else: self._parse_inline(line + '\n', "assistant")

    def add_message(self, sender, text, col="#4a90e2", save=True):
        ts = datetime.now().strftime("%H:%M:%S")
        if save: 
            self.chats[self.current_chat_id]["ui"].append((sender, text, ts))
            self.auto_save() 

        self.chat.config(state=tk.NORMAL)
        tag = "user" if sender == "Ви" else "assistant" if sender == "Асистент" else "system"
        
        self.chat.insert(tk.END, f"\n{sender} [{ts}]:\n", tag)
        if sender == "Асистент": self.insert_markdown(text)
        else: self.chat.insert(tk.END, f"{text}\n", tag)
            
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def process_message(self, msg, was_spoken):
        self.update_status("🤖 Думаю...")
        self.change_emotion("thinking")
        try:
            api_msgs = self.chats[self.current_chat_id]["api"]
            api_msgs.append({"role": "user", "content": msg})
            
            if client:
                completion = client.chat.completions.create(model="openai/gpt-oss-120b", messages=api_msgs)
                ans = completion.choices[0].message.content
                api_msgs.append({"role": "assistant", "content": ans})
                self.last_assistant_message = ans 
                self.auto_save() 
            else:
                ans = "API ключ відсутній. Демо режим."
                self.last_assistant_message = ans

            self.add_message("Асистент", ans)
            self.detect_emotion(msg, ans)
            
            if voice_mode_enabled and was_spoken: 
                threading.Thread(target=self.speak_ukrainian, args=(ans,), daemon=True).start()
                
            self.update_status("✅ Готовий")
        except Exception as e:
            self.add_message("Система", f"Помилка: {e}")
            self.change_emotion("sad")
            self.update_status("❌ Помилка")

    def update_status(self, text):
        self.bg_canvas.itemconfig("status_txt", text=text)

    def read_last_response(self):
        if not self.last_assistant_message:
            self.add_message("Система", "Немає тексту для озвучення.", "system", save=False)
            return
        self.update_status("🔊 Озвучую...")
        threading.Thread(target=self.speak_ukrainian, args=(self.last_assistant_message,), daemon=True).start()

    def speak_ukrainian(self, text):
        if not HAS_GTTS:
            self.add_message("Система", "gTTS не встановлено. Озвучення недоступне.", "system", save=False)
            self.update_status("✅ Готовий")
            return
        try:
            tts = gTTS(text=text, lang='uk')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            pygame.mixer.music.load(fp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): pygame.time.Clock().tick(10)
            self.update_status("✅ Готовий")
        except Exception as e:
            print(f"Помилка gTTS: {e}")
            self.update_status("✅ Готовий")

    def detect_emotion(self, u_msg, a_msg):
        text = (u_msg + " " + a_msg).lower()
        found = False
        for k, v in EMOTION_MAP.items():
            if k in text:
                self.change_emotion(v)
                found = True
                break
        if not found: self.change_emotion("neutral")

    def change_emotion(self, emo):
        if emo not in EMOTIONS: emo = "neutral"
        self.current_emotion = emo
        self.bg_canvas.itemconfig("header_emo", text=f"{EMOTIONS[emo]} {emo.title()}")
        self.update_avatar_only()

    # --- ДІАЛОГИ ---
    def add_d_label(self, parent, text): 
        tk.Label(parent, text=text, bg=CHAT_BG, fg="white", font=("Segoe UI", 11)).pack(anchor="w", pady=(10, 5))
    
    def add_d_text(self, parent, height=5, font=("Segoe UI", 11)):
        txt = tk.Text(parent, bg="#1a1125", fg="white", font=font, bd=0, height=height)
        txt.pack(fill=tk.BOTH, expand=True, pady=5)
        self.fix_paste(txt) 
        return txt
        
    def add_d_entry(self, parent):
        e = tk.Entry(parent, bg="#1a1125", fg="white", font=("Segoe UI", 11), bd=0)
        e.pack(fill=tk.X, pady=5, ipady=4)
        self.fix_paste(e) 
        return e

    def generate_poem(self):
        d = StyledToplevel(self, "📜 Вірш", 450, 350)
        self.add_d_label(d.content, "Введіть тему або деталі для вірша:")
        txt = self.add_d_text(d.content, height=5)
        def act():
            t = txt.get("1.0", tk.END).strip() 
            d.destroy() 
            if t:
                self.inp.insert("1.0", f"Напиши вірш на тему: {t}")
                self.send_message(None)
        SolidButton(d.content, "Створити", COLORS["accent"], act).pack(fill=tk.X, pady=15)

    def generate_story(self):
        d = StyledToplevel(self, "📚 Історія", 450, 420)
        self.add_d_label(d.content, "Про кого або про що історія? (Деталі):")
        txt = self.add_d_text(d.content, height=6)
        def act():
            t = txt.get("1.0", tk.END).strip()
            d.destroy()
            if t:
                self.inp.insert("1.0", f"Напиши історію про:\n{t}")
                self.send_message(None)
        SolidButton(d.content, "Створити", COLORS["accent"], act).pack(fill=tk.X, pady=15)

    def translate_text(self):
        d = StyledToplevel(self, "🌍 Переклад", 500, 420)
        self.add_d_label(d.content, "Текст для перекладу:")
        txt = self.add_d_text(d.content, height=6)
        self.add_d_label(d.content, "Мова:")
        lang_var = tk.StringVar(value="англійську")
        ttk.Combobox(d.content, textvariable=lang_var, values=["англійську", "німецьку", "французьку", "польську"], state="readonly", style="Modern.TCombobox").pack(fill=tk.X, pady=5)
        def act():
            t = txt.get("1.0", tk.END).strip()
            lang = lang_var.get()
            d.destroy()
            if t:
                prompt = f"Зроби ТІЛЬКИ переклад наступного тексту на {lang}. Більше нічого не пиши. Після цього повертайся до свого звичайного характеру.\n\nТекст:\n{t}"
                self.inp.insert("1.0", prompt)
                self.send_message(None)
        SolidButton(d.content, "Перекласти", COLORS["accent"], act).pack(fill=tk.X, pady=15)

    def explain_simple(self):
        d = StyledToplevel(self, "🧒 Просто", 450, 350)
        self.add_d_label(d.content, "Що саме вам пояснити?")
        txt = self.add_d_text(d.content, height=5)
        def act():
            t = txt.get("1.0", tk.END).strip()
            d.destroy()
            if t:
                self.inp.insert("1.0", f"Поясни як для дитини наступне:\n{t}")
                self.send_message(None)
        SolidButton(d.content, "Пояснити", COLORS["accent"], act).pack(fill=tk.X, pady=15)

    def brainstorm(self):
        d = StyledToplevel(self, "💡 Ідеї", 450, 350)
        self.add_d_label(d.content, "Для якого проєкту потрібні ідеї?")
        txt = self.add_d_text(d.content, height=5)
        def act():
            t = txt.get("1.0", tk.END).strip()
            d.destroy()
            if t:
                self.inp.insert("1.0", f"Згенеруй креативні ідеї для:\n{t}")
                self.send_message(None)
        SolidButton(d.content, "Згенерувати", COLORS["accent"], act).pack(fill=tk.X, pady=15)

    def code_helper(self):
        d = StyledToplevel(self, "💻 Код", 600, 500)
        self.add_d_label(d.content, "Дія:")
        var = tk.StringVar(value="Пояснити код")
        ttk.Combobox(d.content, textvariable=var, values=["Пояснити код", "Знайти помилку", "Оптимізувати код", "Написати функцію"], state="readonly", style="Modern.TCombobox").pack(fill=tk.X, pady=5)
        self.add_d_label(d.content, "Код або завдання:")
        txt = self.add_d_text(d.content, height=10, font=("Consolas", 10))
        def act():
            code = txt.get("1.0", tk.END).strip()
            action = var.get()
            d.destroy()
            if code:
                self.inp.insert("1.0", f"{action}:\n{code}")
                self.send_message(None)
        SolidButton(d.content, "Виконати", COLORS["accent"], act).pack(fill=tk.X, pady=15)

    def motivation(self):
        d = StyledToplevel(self, "✨ Мотивація", 400, 240)
        self.add_d_label(d.content, "Опишіть ваш настрій коротко:")
        e = self.add_d_entry(d.content)
        e.insert(0, "звичайний")
        def act():
            mood = e.get()
            d.destroy() 
            self.inp.insert("1.0", f"Дай мотивацію. Мій настрій: {mood}")
            self.send_message(None)
        SolidButton(d.content, "Надихнути", COLORS["accent"], act).pack(fill=tk.X, pady=20)

    # --- СИСТЕМНІ ФУНКЦІЇ ---
    def show_stats(self): self.show_alert("Статистика", f"Чати: {len(self.chats)}\nПочаток: {session_history['start_time']}")
    def show_log(self):
        t = "".join(open(SPEECH_LOG_FILE, 'r', encoding='utf-8').readlines()[-20:]) if os.path.exists(SPEECH_LOG_FILE) else "Лог порожній"
        self.show_alert("Лог голосу", t)
    def show_help(self):
     self.show_alert(
        "Довідка",
        "SANCHESI AI vFinal\n\n"

        "SANCHESI AI — інтелектуальний AI-асистент з підтримкою мультичатів,\n"
        "зміни характерів та голосових функцій.\n\n"

        "ЯК ПОЧАТИ РОБОТУ:\n"
        "1. Оберіть характер у правому меню.\n"
        "2. Створіть новий чат або виберіть існуючий.\n"
        "3. Введіть повідомлення або використайте голосовий ввід.\n"
        "4. Натисніть 'Відправити'.\n\n"

        "МОЖЛИВОСТІ:\n"
        "- Мультичатинг\n"
        "- Пам'ять чатів\n"
        "- Перейменування чатів\n"
        "- Повна підтримка Markdown\n"
        "- Liquid Glass інтерфейс\n"
        "- Голосовий ввід повідомлень\n"
        "- Озвучка відповіді асистента\n\n"

        "ІНСТРУМЕНТИ:\n"
        "- Вірш — генерація поезії\n"
        "- Історія — створення історій\n"
        "- Переклад — переклад тексту\n"
        "- Просто — спрощене пояснення\n"
        "- Ідеї — генерація ідей\n\n"

        "ГАРЯЧІ КЛАВІШІ:\n"
        "Enter — відправити повідомлення\n"
        "Shift + Enter — новий рядок\n"
        "Ctrl + V — вставити текст\n\n"

        "Розробник: SANCHESI\n"
        "Ліцензія: MIT License"
    )
    
    def show_alert(self, title, message):
        d = StyledToplevel(self, title, 500, 340)
        txt = scrolledtext.ScrolledText(d.content, bg="#1a1125", fg="#ddd", font=("Consolas", 10), bd=0)
        txt.insert("1.0", message); txt.config(state="disabled")
        txt.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        SolidButton(d.content, "Закрити", COLORS["btn_bg"], d.destroy).pack(fill=tk.X, pady=10)

    def clear_chat(self):
        if messagebox.askyesno("Clear", "Очистити історію поточного чату?"):
            self.chats[self.current_chat_id]["api"] = [{"role": "system", "content": PERSONALITIES[self.p_var.get()]}]
            self.chats[self.current_chat_id]["ui"] = []
            self.auto_save()
            self.refresh_chat_display()
            self.add_message("Система", "Поточний чат очищено")

    def save_backup(self):
        try:
            fn = f"sessions/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(fn, 'w', encoding='utf-8') as f: json.dump(self.chats, f, ensure_ascii=False, indent=2)
            self.show_alert("Резервна копія", f"Усі чати збережено як бекап у файл:\n{fn}")
        except Exception as e:
            messagebox.showerror("Помилка", f"{e}")

    # --- ГОЛОСОВИЙ ВВІД ---
    def change_personality(self, e):
        new_pers = PERSONALITIES[self.p_var.get()]
        self.chats[self.current_chat_id]["api"][0]["content"] = new_pers
        self.auto_save()
        self.add_message("Система", f"Характер змінено на: {self.p_var.get()}")

    def toggle_voice(self):
        global voice_mode_enabled
        voice_mode_enabled = not voice_mode_enabled
        if voice_mode_enabled:
            self.voice_btn.config(text="🔊 Авто-озвучка (Увімк)", state="normal") # Fix state param for config
        else:
            self.voice_btn.config(text="🔇 Авто-озвучка (Вимк)", state="normal")

    def start_listening(self): threading.Thread(target=self.listen_thread, daemon=True).start()

    def listen_thread(self):
        self.update_status("🎤 Слухаю...")
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            self.update_status("🔄 Обробка...")
            try: txt = recognizer.recognize_google(audio, language='uk-UA')
            except: txt = recognizer.recognize_google(audio, language='ru-RU')
            
            with open(SPEECH_LOG_FILE, 'a', encoding='utf-8') as f: f.write(f"{txt}\n")
            
            self.inp.delete("1.0", tk.END)
            self.inp.insert("1.0", txt)
            self.was_voice_input = True 
            self.update_status("✅ Розпізнано")
            self.send_message(None)
        except Exception as e:
            self.update_status("❌ Помилка мікрофона")
            print(e)

if __name__ == "__main__":
    root = tk.Tk()
    app = SanchesiFullGUI(root)
    root.mainloop()