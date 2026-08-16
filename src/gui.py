import os
import sys
import json
import threading
import queue
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional

# Enable High DPI Awareness on Windows to fix blurry text and fuzzy controls
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from .crawler.downloader import NovelDownloader

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".novel_crawler_config.json")
OLD_CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".wikicv_crawler_config.json")

# Migration check from old config
if not os.path.exists(CONFIG_FILE) and os.path.exists(OLD_CONFIG_FILE):
    try:
        import shutil
        shutil.copy(OLD_CONFIG_FILE, CONFIG_FILE)
    except Exception:
        pass

class NovelCrawlerGUI:
    """
    Sharp High-Contrast GUI - Crisp typography, Windows DPI Scaling, Elapsed Time, ETA, 1000-line Log cap.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Novel Crawler - Download Manager")
        self.root.geometry("960x720")
        self.root.minsize(880, 640)

        # Set App Window Icon
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
        ico_path = os.path.join(assets_dir, "icon.ico")
        png_path = os.path.join(assets_dir, "icon.png")

        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass
        elif os.path.exists(png_path):
            try:
                img = tk.PhotoImage(file=png_path)
                self.root.wm_iconphoto(True, img)
            except Exception:
                pass

        # Sharp high-contrast palette
        self.bg_color = "#f8fafc"        # Clean light background
        self.card_bg = "#ffffff"        # Crisp white card background
        self.fg_color = "#0f172a"        # Deep charcoal text
        self.muted_fg = "#475569"       # Slate secondary text
        self.accent_teal = "#0d9488"     # Mint teal accent
        self.accent_hover = "#0f766e"    # Dark teal hover
        self.border_color = "#cbd5e1"    # Sharp border
        self.badge_bg = "#f0fdf4"        # Soft mint badge
        self.badge_fg = "#047857"        # Mint badge text

        self.start_time: Optional[float] = None

        self.root.configure(bg=self.bg_color)
        self.setup_menu()
        self.setup_styles()

        self.downloader: Optional[NovelDownloader] = None
        self.download_thread: Optional[threading.Thread] = None
        self.ui_queue = queue.Queue()

        self.create_widgets()
        self.load_app_config()
        self.process_queue()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Mở thư mục lưu", command=self.open_output_dir)
        settings_menu.add_separator()
        settings_menu.add_command(label="Thoát", command=self.on_close)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hướng dẫn sử dụng", command=self.show_help)
        help_menu.add_command(label="Thông tin ứng dụng", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))

        # Progressbar
        style.configure("Horizontal.TProgressbar", troughcolor="#e2e8f0", background=self.accent_teal, bordercolor=self.bg_color, thickness=20)

    def create_widgets(self):
        main_container = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=15)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 1. App Header Section
        header_frame = tk.Frame(main_container, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        title_box = tk.Frame(header_frame, bg=self.bg_color)
        title_box.pack(side=tk.LEFT)

        app_title = tk.Label(
            title_box, text="Novel Crawler", font=("Segoe UI", 16, "bold"),
            bg=self.bg_color, fg="#0f172a"
        )
        app_title.pack(anchor=tk.W)

        app_sub = tk.Label(
            title_box, text="Universal Novel Downloader | v1.1.0 | Build 2026-08-16",
            font=("Segoe UI", 9), bg=self.bg_color, fg=self.muted_fg
        )
        app_sub.pack(anchor=tk.W, pady=(1, 0))

        # Right Status Badge
        self.badge_lbl = tk.Label(
            header_frame, text="Ready", font=("Segoe UI", 9, "bold"),
            bg=self.badge_bg, fg=self.badge_fg, bd=1, relief="solid",
            padx=14, pady=4
        )
        self.badge_lbl.pack(side=tk.RIGHT)

        # 2. Input Form Fields
        form_frame = tk.Frame(main_container, bg=self.bg_color)
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # Row 1: Links (URL Truyện)
        r1 = tk.Frame(form_frame, bg=self.bg_color)
        r1.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(r1, text="Links", font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg=self.fg_color, width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.url_entry = tk.Entry(
            r1, font=("Segoe UI", 10), bg="#ffffff", fg="#0f172a",
            insertbackground="#000000", relief="solid", bd=1, highlightthickness=0
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)
        self.url_entry.insert(0, "https://wikicv.org/truyen/he-thong-cang-ngay-cang-quy-di-quan-ta-m-aJ875FS4CGOdA_FN")

        btn_browse_url = tk.Button(
            r1, text="Paste URL", font=("Segoe UI", 9), bg="#ffffff", fg="#1e293b",
            relief="solid", bd=1, padx=12, pady=2, cursor="hand2", command=self.paste_url
        )
        btn_browse_url.pack(side=tk.RIGHT)

        # Row 2: Download folder
        r2 = tk.Frame(form_frame, bg=self.bg_color)
        r2.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(r2, text="Download folder", font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg=self.fg_color, width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.dir_entry = tk.Entry(
            r2, font=("Segoe UI", 10), bg="#ffffff", fg="#0f172a",
            insertbackground="#000000", relief="solid", bd=1, highlightthickness=0
        )
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)
        self.dir_entry.insert(0, os.path.abspath("downloads"))

        self.btn_browse_dir = tk.Button(
            r2, text="Browse...", font=("Segoe UI", 9), bg="#ffffff", fg="#1e293b",
            relief="solid", bd=1, padx=16, pady=2, cursor="hand2", command=self.browse_directory
        )
        self.btn_browse_dir.pack(side=tk.RIGHT)

        # Row 3: Cookies (Tùy chọn) - Supports paste & file selection
        r3_cookie = tk.Frame(form_frame, bg=self.bg_color)
        r3_cookie.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(r3_cookie, text="Cookies (Tùy chọn)", font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg=self.fg_color, width=15, anchor=tk.W).pack(side=tk.LEFT)
        self.cookie_entry = tk.Entry(
            r3_cookie, font=("Segoe UI", 10), bg="#ffffff", fg="#0f172a",
            insertbackground="#000000", relief="solid", bd=1, highlightthickness=0
        )
        self.cookie_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)

        self.btn_browse_cookie = tk.Button(
            r3_cookie, text="📁 Chọn từ File...", font=("Segoe UI", 9), bg="#ffffff", fg="#1e293b",
            relief="solid", bd=1, padx=10, pady=2, cursor="hand2", command=self.browse_cookie_file
        )
        self.btn_browse_cookie.pack(side=tk.RIGHT, padx=(6, 0))

        self.btn_paste_cookie = tk.Button(
            r3_cookie, text="Paste Cookie", font=("Segoe UI", 9), bg="#ffffff", fg="#1e293b",
            relief="solid", bd=1, padx=10, pady=2, cursor="hand2", command=self.paste_cookie
        )
        self.btn_paste_cookie.pack(side=tk.RIGHT)

        # Row 4: Parameters Row
        r3 = tk.Frame(form_frame, bg=self.bg_color)
        r3.pack(fill=tk.X, pady=(0, 4))

        tk.Label(r3, text="Nghỉ/chương (s)", font=("Segoe UI", 9), bg=self.bg_color, fg=self.muted_fg).pack(side=tk.LEFT, padx=(0, 4))
        self.delay_min_sp = tk.Spinbox(r3, from_=0.5, to=10.0, increment=0.5, width=5, font=("Segoe UI", 9), bg="#ffffff", fg="#0f172a", relief="solid", bd=1, command=self.sync_live_config)
        self.delay_min_sp.delete(0, tk.END); self.delay_min_sp.insert(0, "1.0")
        self.delay_min_sp.pack(side=tk.LEFT, padx=(0, 4))
        self.delay_min_sp.bind("<KeyRelease>", self.sync_live_config)

        tk.Label(r3, text="-", font=("Segoe UI", 9), bg=self.bg_color, fg=self.muted_fg).pack(side=tk.LEFT, padx=(0, 4))
        self.delay_max_sp = tk.Spinbox(r3, from_=1.0, to=30.0, increment=0.5, width=5, font=("Segoe UI", 9), bg="#ffffff", fg="#0f172a", relief="solid", bd=1, command=self.sync_live_config)
        self.delay_max_sp.delete(0, tk.END); self.delay_max_sp.insert(0, "2.5")
        self.delay_max_sp.pack(side=tk.LEFT, padx=(0, 16))
        self.delay_max_sp.bind("<KeyRelease>", self.sync_live_config)

        tk.Label(r3, text="Nghỉ dài sau", font=("Segoe UI", 9), bg=self.bg_color, fg=self.muted_fg).pack(side=tk.LEFT, padx=(0, 4))
        self.batch_size_sp = tk.Spinbox(r3, from_=10, to=500, increment=10, width=5, font=("Segoe UI", 9), bg="#ffffff", fg="#0f172a", relief="solid", bd=1, command=self.sync_live_config)
        self.batch_size_sp.delete(0, tk.END); self.batch_size_sp.insert(0, "50")
        self.batch_size_sp.pack(side=tk.LEFT, padx=(0, 4))
        self.batch_size_sp.bind("<KeyRelease>", self.sync_live_config)
        tk.Label(r3, text="chương", font=("Segoe UI", 9), bg=self.bg_color, fg=self.muted_fg).pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(r3, text="Thời gian nghỉ dài (s)", font=("Segoe UI", 9), bg=self.bg_color, fg=self.muted_fg).pack(side=tk.LEFT, padx=(0, 4))
        self.batch_delay_sp = tk.Spinbox(r3, from_=5.0, to=120.0, increment=5.0, width=5, font=("Segoe UI", 9), bg="#ffffff", fg="#0f172a", relief="solid", bd=1, command=self.sync_live_config)
        self.batch_delay_sp.delete(0, tk.END); self.batch_delay_sp.insert(0, "15.0")
        self.batch_delay_sp.pack(side=tk.LEFT)
        self.batch_delay_sp.bind("<KeyRelease>", self.sync_live_config)

        self.warp_var = tk.BooleanVar(value=True)
        self.warp_cb = tk.Checkbutton(
            r3, text="⚡ Tự động Reset Cloudflare WARP khi lỗi", variable=self.warp_var,
            font=("Segoe UI", 9, "bold"), bg=self.bg_color, fg="#0f766e",
            activebackground=self.bg_color, selectcolor="#ffffff", command=self.sync_live_config
        )
        self.warp_cb.pack(side=tk.LEFT, padx=(16, 0))

        # 3. Action Buttons Bar
        action_bar = tk.Frame(main_container, bg=self.bg_color)
        action_bar.pack(fill=tk.X, pady=(6, 12))

        self.start_btn = tk.Button(
            action_bar, text="Start download", bg=self.accent_teal, fg="#ffffff",
            activebackground=self.accent_hover, activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=18, pady=5, cursor="hand2",
            command=self.start_download
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = tk.Button(
            action_bar, text="Stop", bg="#ffffff", fg="#64748b",
            activebackground="#f1f5f9", activeforeground="#0f172a",
            font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=16, pady=4,
            state=tk.DISABLED, cursor="hand2", command=self.toggle_pause
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.clear_btn = tk.Button(
            action_bar, text="Clear log", bg="#ffffff", fg="#1e293b",
            activebackground="#f1f5f9", activeforeground="#0f172a",
            font=("Segoe UI", 9), relief="solid", bd=1, padx=16, pady=4,
            cursor="hand2", command=self.clear_log
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.open_dir_btn = tk.Button(
            action_bar, text="Open download folder", bg="#ffffff", fg="#1e293b",
            activebackground="#f1f5f9", activeforeground="#0f172a",
            font=("Segoe UI", 9), relief="solid", bd=1, padx=16, pady=4,
            cursor="hand2", command=self.open_output_dir
        )
        self.open_dir_btn.pack(side=tk.LEFT)

        # 4. Status Dashboard Card (Progress, Elapsed Time, ETA, % Done)
        dashboard_card = tk.Frame(main_container, bg="#ffffff", bd=1, relief="solid", padx=14, pady=12)
        dashboard_card.pack(fill=tk.X, pady=(0, 12))

        # Progress bar on top of card
        self.progress_bar = ttk.Progressbar(dashboard_card, mode="determinate", style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        # Metrics Row
        metrics_frame = tk.Frame(dashboard_card, bg="#ffffff")
        metrics_frame.pack(fill=tk.X)

        self.pct_lbl = tk.Label(
            metrics_frame, text="Tiến độ: 0.0% (0/0 chương)", font=("Segoe UI", 10, "bold"),
            bg="#ffffff", fg="#0d9488"
        )
        self.pct_lbl.pack(side=tk.LEFT, padx=(0, 24))

        self.elapsed_lbl = tk.Label(
            metrics_frame, text="⏱️ Đã dùng: 00:00:00", font=("Segoe UI", 9),
            bg="#ffffff", fg="#0f172a"
        )
        self.elapsed_lbl.pack(side=tk.LEFT, padx=(0, 24))

        self.eta_lbl = tk.Label(
            metrics_frame, text="⏳ Còn lại (dự kiến): --:--:--", font=("Segoe UI", 9),
            bg="#ffffff", fg="#0f172a"
        )
        self.eta_lbl.pack(side=tk.LEFT)

        self.status_lbl = tk.Label(
            dashboard_card, text="Trạng thái: Sẵn sàng tải", font=("Segoe UI", 9, "italic"),
            bg="#ffffff", fg=self.muted_fg
        )
        self.status_lbl.pack(anchor=tk.W, pady=(6, 0))

        # 5. Main Log View Card (Auto Trimmed to Max 1000 Lines)
        log_card = tk.Frame(main_container, bg="#ffffff", bd=1, relief="solid", padx=10, pady=10)
        log_card.pack(fill=tk.BOTH, expand=True)

        log_title = tk.Label(
            log_card, text="📜 Bảng điều khiển & Log tiến trình (Tối đa 1000 dòng)",
            font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155"
        )
        log_title.pack(anchor=tk.W, pady=(0, 6))

        self.log_text = scrolledtext.ScrolledText(
            log_card, bg="#0f172a", fg="#38bdf8", insertbackground="#ffffff",
            font=("Consolas", 10), relief="flat"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def load_app_config(self):
        """Load saved config (cookies, output folder, delay params) on launch."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if "cookie" in cfg and cfg["cookie"]:
                        self.cookie_entry.delete(0, tk.END)
                        self.cookie_entry.insert(0, cfg["cookie"])
                    if "output_dir" in cfg and cfg["output_dir"]:
                        self.dir_entry.delete(0, tk.END)
                        self.dir_entry.insert(0, cfg["output_dir"])
                    if "delay_min" in cfg:
                        self.delay_min_sp.delete(0, tk.END); self.delay_min_sp.insert(0, str(cfg["delay_min"]))
                    if "delay_max" in cfg:
                        self.delay_max_sp.delete(0, tk.END); self.delay_max_sp.insert(0, str(cfg["delay_max"]))
                    if "batch_size" in cfg:
                        self.batch_size_sp.delete(0, tk.END); self.batch_size_sp.insert(0, str(cfg["batch_size"]))
                    if "batch_delay" in cfg:
                        self.batch_delay_sp.delete(0, tk.END); self.batch_delay_sp.insert(0, str(cfg["batch_delay"]))
                    if "enable_warp_reset" in cfg:
                        self.warp_var.set(bool(cfg["enable_warp_reset"]))
            except Exception:
                pass

    def save_app_config(self):
        """Save config parameters and cookie to CONFIG_FILE across launches."""
        cfg = {
            "cookie": self.cookie_entry.get().strip(),
            "output_dir": self.dir_entry.get().strip(),
            "delay_min": self.delay_min_sp.get().strip(),
            "delay_max": self.delay_max_sp.get().strip(),
            "batch_size": self.batch_size_sp.get().strip(),
            "batch_delay": self.batch_delay_sp.get().strip(),
            "enable_warp_reset": self.warp_var.get(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def on_close(self):
        self.save_app_config()
        self.root.destroy()

    def paste_url(self):
        try:
            txt = self.root.clipboard_get()
            if txt and "http" in txt:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, txt.strip())
        except Exception:
            pass

    def paste_cookie(self):
        try:
            txt = self.root.clipboard_get()
            if txt:
                self.cookie_entry.delete(0, tk.END)
                self.cookie_entry.insert(0, txt.strip())
                self.save_app_config()
        except Exception:
            pass

    def browse_cookie_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file chứa Cookie",
            filetypes=[("Text files", "*.txt;*.cookie;*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        self.cookie_entry.delete(0, tk.END)
                        self.cookie_entry.insert(0, content)
                        self.save_app_config()
                        messagebox.showinfo("Thành công", f"Đã nạp Cookie từ file:\n{os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Lỗi đọc file", f"Không thể đọc file Cookie: {e}")

    def browse_directory(self):
        chosen = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if chosen:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, os.path.abspath(chosen))
            self.save_app_config()

    def open_output_dir(self):
        folder = os.path.abspath(self.dir_entry.get().strip())
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        try:
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục: {e}")

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def append_log(self, text: str):
        self.log_text.insert(tk.END, text + "\n")
        # Auto trim lines if line count exceeds 1000
        try:
            end_idx = self.log_text.index('end-1c')
            line_count = int(end_idx.split('.')[0])
            if line_count > 1000:
                lines_to_delete = line_count - 1000
                self.log_text.delete("1.0", f"{lines_to_delete + 1}.0")
        except Exception:
            pass
        self.log_text.see(tk.END)

    def toggle_input_fields(self, is_downloading: bool):
        state = tk.DISABLED if is_downloading else tk.NORMAL
        self.url_entry.config(state=state)
        self.dir_entry.config(state=state)
        self.btn_browse_dir.config(state=state)
        self.cookie_entry.config(state=state)
        self.btn_browse_cookie.config(state=state)
        self.btn_paste_cookie.config(state=state)

    def sync_live_config(self, event=None):
        if hasattr(self, 'downloader') and self.downloader and self.is_downloading:
            try:
                d_min = float(self.delay_min_sp.get())
                d_max = float(self.delay_max_sp.get())
                b_size = int(self.batch_size_sp.get())
                b_delay = float(self.batch_delay_sp.get())

                self.downloader.delay_min = max(0.1, d_min)
                self.downloader.delay_max = max(d_min, d_max)
                self.downloader.batch_size = max(1, b_size)
                self.downloader.batch_delay_min = max(0.1, b_delay * 0.8)
                self.downloader.batch_delay_max = max(b_delay, b_delay * 1.2)
                self.downloader.enable_warp_reset = self.warp_var.get()
            except Exception:
                pass

    def set_status_badge(self, text: str, is_active: bool = False):
        if is_active:
            self.badge_lbl.config(text=text, bg="#fef3c7", fg="#b45309")
        else:
            self.badge_lbl.config(text=text, bg=self.badge_bg, fg=self.badge_fg)

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.ui_queue.get_nowait()
                if msg_type == "log":
                    self.append_log(data)
                elif msg_type == "progress":
                    cur, tot, title, volume, status = data
                    
                    if self.session_start_time is None:
                        self.session_start_time = time.time()

                    if self.session_start_idx is None and cur > 0:
                        # Set initial benchmark chapter index for THIS session
                        self.session_start_idx = cur if status.startswith("✅ Đã") else (cur - 1)

                    self.sync_live_config()

                    # Session-based ETA & elapsed calculation
                    session_downloaded = max(0, cur - self.session_start_idx)
                    session_elapsed = time.time() - self.session_start_time
                    elapsed_sec = int(session_elapsed)
                    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_sec))

                    if tot > 0:
                        pct = (cur / tot) * 100
                        self.progress_bar["value"] = pct
                        self.pct_lbl.config(text=f"Tiến độ: [{cur}/{tot}] ({pct:.1f}%)")

                        remaining_chaps = tot - cur
                        if session_downloaded > 0 and remaining_chaps > 0 and session_elapsed > 0:
                            avg_per_chap = session_elapsed / session_downloaded
                            eta_sec = int(remaining_chaps * avg_per_chap)
                            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_sec))
                        elif remaining_chaps <= 0:
                            eta_str = "00:00:00"
                        else:
                            eta_str = "--:--:--"

                        self.elapsed_lbl.config(text=f"⏱️ Đã dùng: {elapsed_str}")
                        self.eta_lbl.config(text=f"⏳ Còn lại (dự kiến): {eta_str}")
                        self.status_lbl.config(text=f"📖 [{cur}/{tot}] {title} ({status})")

                elif msg_type == "finished":
                    output_file, success, err_msg = data
                    self.is_downloading = False
                    self.toggle_input_fields(False)
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED, text="Stop", fg="#64748b")
                    self.set_status_badge("Ready", is_active=False)

                    if success:
                        self.status_lbl.config(text="Trạng thái: Hoàn thành 100%!")
                        ans = messagebox.askyesno(
                            "Hoàn thành",
                            f"Đã tải thành công bộ truyện!\nFile lưu tại:\n{output_file}\n\nBạn có muốn mở ngay thư mục chứa file không?"
                        )
                        if ans:
                            self.open_output_dir()
                    elif err_msg:
                        self.status_lbl.config(text=f"Lỗi: {err_msg}")
                        messagebox.showerror("Thất bại", f"Tải thất bại: {err_msg}")
        except queue.Empty:
            pass

        self.root.after(100, self.process_queue)

    def start_download(self):
        url = self.url_entry.get().strip()
        out_dir = self.dir_entry.get().strip()
        cookie_val = self.cookie_entry.get().strip()

        if not url.startswith("http"):
            messagebox.showwarning("Lỗi URL", "Vui lòng nhập đúng đường dẫn URL truyện (ví dụ wikicv.org)!")
            return

        try:
            d_min = float(self.delay_min_sp.get())
            d_max = float(self.delay_max_sp.get())
            b_size = int(self.batch_size_sp.get())
            b_delay = float(self.batch_delay_sp.get())
        except ValueError:
            messagebox.showwarning("Lỗi thông số", "Vui lòng nhập các thông số thời gian nghỉ dạng số hợp lệ!")
            return

        self.save_app_config()

        self.is_downloading = True
        self.session_start_time = None
        self.session_start_idx = None
        self.toggle_input_fields(True)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL, text="Stop", fg="#ef4444")
        self.set_status_badge("Downloading...", is_active=True)
        self.progress_bar["value"] = 0
        self.log_text.delete(1.0, tk.END)
        self.pct_lbl.config(text="Tiến độ: 0.0% (0/0 chương)")
        self.elapsed_lbl.config(text="⏱️ Đã dùng: 00:00:00")
        self.eta_lbl.config(text="⏳ Còn lại (dự kiến): --:--:--")

        self.downloader = NovelDownloader(
            novel_url=url,
            output_dir=out_dir,
            cookie=cookie_val,
            delay_min=d_min,
            delay_max=d_max,
            batch_size=b_size,
            batch_delay_min=b_delay * 0.8,
            batch_delay_max=b_delay * 1.2,
            enable_warp_reset=self.warp_var.get(),
            log_callback=lambda msg: self.ui_queue.put(("log", msg)),
            progress_callback=lambda cur, tot, title, volume, status: self.ui_queue.put(("progress", (cur, tot, title, volume, status)))
        )

        def worker():
            try:
                res_file = self.downloader.download()
                self.ui_queue.put(("finished", (res_file, True, None)))
            except Exception as e:
                self.ui_queue.put(("finished", ("", False, str(e))))

        self.download_thread = threading.Thread(target=worker, daemon=True)
        self.download_thread.start()

    def toggle_pause(self):
        if not self.downloader:
            return
        if self.downloader.is_paused():
            self.downloader.resume()
            self.stop_btn.config(text="Stop", fg="#ef4444")
            self.set_status_badge("Downloading...", is_active=True)
        else:
            self.downloader.pause()
            self.stop_btn.config(text="Resume", fg="#0d9488")
            self.set_status_badge("Paused", is_active=True)

    def show_help(self):
        messagebox.showinfo(
            "Hướng dẫn sử dụng - Novel Crawler",
            "1. Dán URL trắc nghiệm/truyện (ví dụ wikicv.org) vào ô 'Links'\n"
            "2. Chọn thư mục xuất file tại 'Download folder'\n"
            "3. Nạp Cookie (tùy chọn) để tải truyện giới hạn tài khoản\n"
            "4. Chọn '[x] ⚡ Tự động Reset Cloudflare WARP khi lỗi' để tự vượt lỗi kết nối/IP/403\n"
            "5. Bấm 'Start download' để cào truyện sắc nét & tự động nạp Resume."
        )

    def show_about(self):
        messagebox.showinfo("Về ứng dụng", "Novel Crawler - Universal Download Manager v1.1.0\nHỗ trợ cào truyện tự động đa nguồn, tự ngắt/bật Cloudflare WARP khi lỗi, ghi nhớ Cookie và nạp Resume nối tiếp.")

def run_gui():
    root = tk.Tk()
    app = NovelCrawlerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
