"""
app.py - RamBooster Main Application Window.
Premium monochrome dashboard - professional black & white design.
"""

import logging
import os
import sys
import threading
from datetime import datetime

import customtkinter as ctk
from PIL import Image

from ram_booster.memory import (
    get_memory_info,
    get_top_memory_processes,
    is_admin,
    request_admin_restart,
    smart_clean,
)
from ram_booster.optimizer import get_disk_usage, system_boost
from ram_booster.widgets import (
    CircularGauge,
    Colors,
    Fonts,
    PremiumButton,
    ProcessList,
    StatCard,
    StatusToast,
)

logger = logging.getLogger("RamBooster.app")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class RamBoosterApp(ctk.CTk):
    """Main application - premium monochrome dashboard."""

    WIDTH = 1020
    HEIGHT = 700
    UPDATE_MS = 2000

    def __init__(self):
        super().__init__()

        self.title("RamBooster")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(900, 640)
        self.configure(fg_color=Colors.BG_DARK)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.WIDTH) // 2
        y = (self.winfo_screenheight() - self.HEIGHT) // 2 - 20
        self.geometry(f"+{x}+{y}")

        # Icon
        try:
            base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            ico = os.path.join(base, "icon.ico")
            if os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

        # State
        self._cleaning = False
        self._boosting = False
        self._update_id = None
        self._history = []
        self._proc_tick = 0

        # Build UI
        self._build()
        self._start_updates()
        self.after(500, self._check_admin)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════════════════════════════════
    # BUILD UI
    # ═══════════════════════════════════════════

    def _build(self):
        # ── Top Bar ──
        self._build_topbar()

        # ── Main Layout ──
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=(12, 16))

        # Left column
        left = ctk.CTkFrame(main, fg_color="transparent", width=340)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)
        self._build_left(left)

        # Right column
        right = ctk.CTkFrame(main, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))
        self._build_right(right)

        # Toast
        self._toast = StatusToast(self)

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, height=68, corner_radius=0, fg_color=Colors.BG_PRIMARY,
                           border_width=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # ── Left: Logo + Brand ──
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=20, pady=8)

        # Logo frame with border
        logo_frame = ctk.CTkFrame(left, width=48, height=48, corner_radius=12,
                                   fg_color=Colors.BG_CARD, border_width=2,
                                   border_color=Colors.BORDER_LIGHT)
        logo_frame.pack(side="left", padx=(0, 14))
        logo_frame.pack_propagate(False)

        try:
            base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            icon_png = os.path.join(base, "icon.png")
            if os.path.exists(icon_png):
                logo_img = ctk.CTkImage(
                    light_image=Image.open(icon_png),
                    dark_image=Image.open(icon_png),
                    size=(44, 44),
                )
                ctk.CTkLabel(logo_frame, image=logo_img, text="",
                             fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
                self._logo_ref = logo_img  # Keep reference to prevent GC
            else:
                ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(size=20),
                             text_color=Colors.WHITE).place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            pass

        # Brand text stack
        brand = ctk.CTkFrame(left, fg_color="transparent")
        brand.pack(side="left")

        # Title row
        title_row = ctk.CTkFrame(brand, fg_color="transparent")
        title_row.pack(anchor="w")

        ctk.CTkLabel(
            title_row, text="RAMBOOSTER",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=Colors.WHITE,
        ).pack(side="left")

        # PRO badge
        pro_badge = ctk.CTkFrame(title_row, corner_radius=4, fg_color=Colors.WHITE,
                                  width=32, height=16)
        pro_badge.pack(side="left", padx=(10, 0), pady=(2, 0))
        pro_badge.pack_propagate(False)
        ctk.CTkLabel(pro_badge, text="PRO", font=ctk.CTkFont(size=8, weight="bold"),
                     text_color=Colors.BG_DARK).place(relx=0.5, rely=0.5, anchor="center")

        # Subtitle
        ctk.CTkLabel(
            brand, text="Memory Optimizer  ·  v1.0",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=Colors.WHITE_GHOST,
        ).pack(anchor="w", pady=(1, 0))

        # ── Right: Status ──
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=20)

        self._time_lbl = ctk.CTkLabel(
            right, text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=Colors.WHITE_GHOST,
        )
        self._time_lbl.pack(side="right", padx=(16, 0))

        ctk.CTkLabel(right, text="│", text_color=Colors.BORDER,
                     font=ctk.CTkFont(size=14)).pack(side="right", padx=8)

        self._admin_lbl = ctk.CTkLabel(
            right, text="",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=Colors.WHITE_FAINT,
        )
        self._admin_lbl.pack(side="right")

        # Bottom border line
        ctk.CTkFrame(self, height=1, corner_radius=0,
                     fg_color=Colors.BORDER_SUBTLE).pack(fill="x")

    def _build_left(self, parent):
        # ── Gauge Card ──
        gauge_card = ctk.CTkFrame(
            parent, corner_radius=18,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
        )
        gauge_card.pack(fill="x", pady=(0, 12))

        # Card header
        hdr = ctk.CTkFrame(gauge_card, fg_color="transparent", height=36)
        hdr.pack(fill="x", padx=18, pady=(14, 0))

        ctk.CTkLabel(
            hdr, text="MEMORY USAGE",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=Colors.WHITE_GHOST,
        ).pack(side="left")

        # Live indicator
        live_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        live_frame.pack(side="right")
        self._live_dot = ctk.CTkFrame(live_frame, width=6, height=6,
                                       corner_radius=3, fg_color=Colors.SUCCESS)
        self._live_dot.pack(side="left", padx=(0, 4), pady=1)
        ctk.CTkLabel(live_frame, text="LIVE", font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=Colors.WHITE_MICRO).pack(side="left")

        # Gauge
        self._gauge = CircularGauge(gauge_card, size=240, line_width=10,
                                     bg_color=Colors.BG_CARD)
        self._gauge.pack(pady=(4, 14))

        # ── Stats Grid ──
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", pady=(0, 12))

        row1 = ctk.CTkFrame(grid, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 6))

        self._c_total = StatCard(row1, label="TOTAL", icon="◉", width=158)
        self._c_total.pack(side="left", padx=(0, 6), fill="x", expand=True)

        self._c_used = StatCard(row1, label="USED", icon="▲", width=158)
        self._c_used.pack(side="left", fill="x", expand=True)

        row2 = ctk.CTkFrame(grid, fg_color="transparent")
        row2.pack(fill="x")

        self._c_free = StatCard(row2, label="FREE", icon="▼", width=158)
        self._c_free.pack(side="left", padx=(0, 6), fill="x", expand=True)

        self._c_disk = StatCard(row2, label="DISK C:", icon="◆", width=158)
        self._c_disk.pack(side="left", fill="x", expand=True)

        # ── Action Buttons ──
        btns = ctk.CTkFrame(parent, fg_color="transparent")
        btns.pack(fill="x", side="bottom", pady=(8, 0))

        self._btn_clean = PremiumButton(
            btns, text="SMART CLEAN", icon="⚡",
            variant="primary", command=self._do_clean, height=46,
        )
        self._btn_clean.pack(fill="x", pady=(0, 6))

        self._btn_boost = PremiumButton(
            btns, text="SYSTEM BOOST", icon="◈",
            variant="secondary", command=self._do_boost, height=46,
        )
        self._btn_boost.pack(fill="x")

    def _build_right(self, parent):
        # ── Section Header ──
        hdr = ctk.CTkFrame(parent, fg_color="transparent", height=32)
        hdr.pack(fill="x", pady=(0, 8))
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="TOP PROCESSES",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=Colors.WHITE_GHOST,
        ).pack(side="left")

        self._proc_count_lbl = ctk.CTkLabel(
            hdr, text="",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=Colors.WHITE_MICRO,
        )
        self._proc_count_lbl.pack(side="left", padx=(8, 0))

        # Refresh button
        ctk.CTkButton(
            hdr, text="↻", width=28, height=28, corner_radius=7,
            fg_color="transparent", hover_color=Colors.BG_CARD_HOVER,
            text_color=Colors.WHITE_FAINT,
            font=ctk.CTkFont(size=14),
            border_width=1, border_color=Colors.BORDER_SUBTLE,
            command=self._refresh_procs,
        ).pack(side="right")

        # ── Process List ──
        self._proc_list = ProcessList(parent, height=340)
        self._proc_list.pack(fill="both", expand=True, pady=(0, 12))

        # ── History Panel ──
        hist_card = ctk.CTkFrame(
            parent, corner_radius=14,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            height=140,
        )
        hist_card.pack(fill="x")
        hist_card.pack_propagate(False)

        # History header
        h_hdr = ctk.CTkFrame(hist_card, fg_color="transparent", height=30)
        h_hdr.pack(fill="x", padx=16, pady=(10, 0))

        ctk.CTkLabel(
            h_hdr, text="ACTIVITY LOG",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=Colors.WHITE_MICRO,
        ).pack(side="left")

        ctk.CTkFrame(hist_card, height=1, fg_color=Colors.BORDER_SUBTLE).pack(
            fill="x", padx=16, pady=(4, 6))

        self._hist_lbl = ctk.CTkLabel(
            hist_card, text="No operations performed yet.",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=Colors.WHITE_MICRO,
            justify="left", anchor="nw",
        )
        self._hist_lbl.pack(fill="both", expand=True, padx=16, pady=(0, 10), anchor="nw")

    # ═══════════════════════════════════════════
    # REAL-TIME UPDATES
    # ═══════════════════════════════════════════

    def _start_updates(self):
        self._update()

    def _update(self):
        try:
            mem = get_memory_info()

            self._gauge.set_value(
                mem.percent,
                sub_text=f"{mem.used_gb:.1f} / {mem.total_gb:.1f} GB",
            )

            self._c_total.set_value(f"{mem.total_gb:.1f} GB")
            self._c_used.set_value(
                f"{mem.used_gb:.1f} GB",
                color=Colors.get_usage_color(mem.percent),
            )
            self._c_free.set_value(
                f"{mem.available_gb:.1f} GB",
                color=Colors.SUCCESS if mem.available_gb > 2 else Colors.WARNING,
            )

            disk = get_disk_usage("C:\\")
            self._c_disk.set_value(
                f"{disk['free_gb']:.0f} GB",
                color=Colors.get_usage_color(disk["percent"]),
            )

            now = datetime.now().strftime("%H:%M:%S")
            self._time_lbl.configure(text=now)

            # Blink live dot
            self._live_dot.configure(
                fg_color=Colors.SUCCESS if self._proc_tick % 2 == 0 else Colors.SUCCESS_DIM
            )

            # Update processes every other tick
            self._proc_tick += 1
            if self._proc_tick % 2 == 0:
                self._refresh_procs()

        except Exception as e:
            logger.error(f"Update error: {e}")

        self._update_id = self.after(self.UPDATE_MS, self._update)

    def _refresh_procs(self):
        try:
            procs = get_top_memory_processes(20)
            self._proc_list.update_processes(procs)
            self._proc_count_lbl.configure(text=f"({len(procs)} shown)")
        except Exception as e:
            logger.error(f"Process refresh error: {e}")

    # ═══════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════

    def _do_clean(self):
        if self._cleaning:
            return
        self._cleaning = True
        self._btn_clean.configure(state="disabled", text="  ⏳   CLEANING...")
        self._toast.show("Cleaning memory — please wait...", "⏳", Colors.WHITE_FAINT, 0)

        def _run():
            try:
                r = smart_clean()
                self.after(0, lambda: self._clean_done(r))
            except Exception as e:
                self.after(0, lambda: self._clean_err(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _clean_done(self, r):
        self._cleaning = False
        self._btn_clean.configure(state="normal", text="  ⚡   SMART CLEAN")

        freed = r.get("freed_mb", 0)
        trimmed = r.get("processes_trimmed", 0)
        before_pct = r.get("before_percent", 0)
        after_pct = r.get("after_percent", 0)

        if freed > 0:
            msg = f"Freed {freed:.0f} MB — {trimmed} processes trimmed"
            self._toast.show(msg, "✓", Colors.SUCCESS, 5000)
        else:
            msg = f"Memory is clean — {trimmed} processes checked"
            self._toast.show(msg, "✓", Colors.WHITE_FAINT, 5000)

        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}]  CLEAN  ▸  {freed:.0f} MB freed  |  {before_pct:.0f}% → {after_pct:.0f}%"
        self._history.insert(0, entry)
        self._history = self._history[:6]
        self._update_history()
        self._refresh_procs()

    def _clean_err(self, err):
        self._cleaning = False
        self._btn_clean.configure(state="normal", text="  ⚡   SMART CLEAN")
        self._toast.show(f"Error: {err}", "✕", Colors.DANGER, 5000)

    def _do_boost(self):
        if self._boosting:
            return
        self._boosting = True
        self._btn_boost.configure(state="disabled", text="  ◈   BOOSTING...")
        self._toast.show("Cleaning temp files & optimizing...", "⏳", Colors.WHITE_FAINT, 0)

        def _run():
            try:
                r = system_boost()
                self.after(0, lambda: self._boost_done(r))
            except Exception as e:
                self.after(0, lambda: self._boost_err(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _boost_done(self, r):
        self._boosting = False
        self._btn_boost.configure(state="normal", text="  ◈   SYSTEM BOOST")

        files = r.get("total_files_deleted", 0)
        freed = r.get("total_freed_mb", 0)

        msg = f"Deleted {files} files — freed {freed:.0f} MB"
        self._toast.show(msg, "✓", Colors.SUCCESS, 5000)

        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}]  BOOST  ▸  {files} files deleted  |  {freed:.0f} MB freed"
        self._history.insert(0, entry)
        self._history = self._history[:6]
        self._update_history()

    def _boost_err(self, err):
        self._boosting = False
        self._btn_boost.configure(state="normal", text="  ◈   SYSTEM BOOST")
        self._toast.show(f"Error: {err}", "✕", Colors.DANGER, 5000)

    # ═══════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════

    def _update_history(self):
        if self._history:
            self._hist_lbl.configure(
                text="\n".join(self._history),
                text_color=Colors.WHITE_FAINT,
            )

    def _check_admin(self):
        if is_admin():
            self._admin_lbl.configure(text="● ADMIN", text_color=Colors.SUCCESS_DIM)
        else:
            self._admin_lbl.configure(text="○ USER", text_color=Colors.WHITE_MICRO)
            self._admin_lbl.configure(cursor="hand2")
            self._admin_lbl.bind("<Button-1>", lambda e: self._elevate())

    def _elevate(self):
        from tkinter import messagebox
        if messagebox.askyesno(
            "Administrator",
            "RamBooster needs admin privileges for deep cleaning.\n\n"
            "Restart as Administrator?",
        ):
            request_admin_restart()

    def _on_close(self):
        if self._update_id:
            self.after_cancel(self._update_id)
        self.destroy()
