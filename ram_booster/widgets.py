"""
widgets.py - Premium Monochrome UI Widgets for RamBooster.
Professional black & white design with subtle accents.
"""

import math
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk


# ─────────────────────────────────────────────
# Color Palette - Premium Monochrome
# ─────────────────────────────────────────────
class Colors:
    """Monochrome professional color scheme."""

    # Backgrounds - deep blacks
    BG_DARK = "#09090b"
    BG_PRIMARY = "#0c0c0f"
    BG_CARD = "#131316"
    BG_CARD_HOVER = "#1a1a1f"
    BG_ELEVATED = "#18181b"
    BG_INPUT = "#0f0f12"

    # Borders
    BORDER = "#27272a"
    BORDER_LIGHT = "#3f3f46"
    BORDER_SUBTLE = "#1e1e22"

    # White spectrum
    WHITE = "#fafafa"
    WHITE_DIM = "#e4e4e7"
    WHITE_MUTED = "#a1a1aa"
    WHITE_FAINT = "#71717a"
    WHITE_GHOST = "#52525b"
    WHITE_MICRO = "#3f3f46"

    # Single accent - cold white-blue glow
    ACCENT = "#e4e4e7"
    ACCENT_DIM = "#a1a1aa"

    # Status - muted, professional
    SUCCESS = "#a3e635"
    SUCCESS_DIM = "#65a30d"
    WARNING = "#fbbf24"
    WARNING_DIM = "#d97706"
    DANGER = "#f87171"
    DANGER_DIM = "#dc2626"

    # Gauge colors
    GAUGE_GOOD = "#a3e635"
    GAUGE_OK = "#fbbf24"
    GAUGE_BAD = "#f87171"
    GAUGE_TRACK = "#1e1e22"

    @staticmethod
    def get_usage_color(percent: float) -> str:
        if percent < 50:
            return Colors.SUCCESS
        elif percent < 75:
            return Colors.WARNING
        else:
            return Colors.DANGER

    @staticmethod
    def get_usage_dim(percent: float) -> str:
        if percent < 50:
            return Colors.SUCCESS_DIM
        elif percent < 75:
            return Colors.WARNING_DIM
        else:
            return Colors.DANGER_DIM


# ─────────────────────────────────────────────
# Fonts
# ─────────────────────────────────────────────
class Fonts:
    FAMILY = "Segoe UI"
    MONO = "Cascadia Code"
    MONO_FALLBACK = "Consolas"

    @staticmethod
    def heading(size=18):
        return ctk.CTkFont(family=Fonts.FAMILY, size=size, weight="bold")

    @staticmethod
    def subheading(size=13):
        return ctk.CTkFont(family=Fonts.FAMILY, size=size, weight="bold")

    @staticmethod
    def body(size=12):
        return ctk.CTkFont(family=Fonts.FAMILY, size=size)

    @staticmethod
    def mono(size=11):
        return ctk.CTkFont(family=Fonts.MONO, size=size)

    @staticmethod
    def caption(size=10):
        return ctk.CTkFont(family=Fonts.FAMILY, size=size)

    @staticmethod
    def display(size=36):
        return ctk.CTkFont(family=Fonts.FAMILY, size=size, weight="bold")


# ─────────────────────────────────────────────
# Premium Circular Gauge
# ─────────────────────────────────────────────
class CircularGauge(tk.Canvas):
    """
    Minimalist circular gauge with clean arc and typography.
    """

    def __init__(self, master, size=240, line_width=10, **kwargs):
        bg = kwargs.pop("bg_color", Colors.BG_CARD)
        super().__init__(master, width=size, height=size, bg=bg, highlightthickness=0, **kwargs)

        self.size = size
        self.line_width = line_width
        self.cx = size // 2
        self.cy = size // 2
        self.radius = (size // 2) - line_width - 16
        self._current = 0.0
        self._target = 0.0
        self._sub_text = ""
        self._anim_id = None
        self._draw()

    def _get_color_for_value(self, val):
        if val < 50:
            return Colors.GAUGE_GOOD
        elif val < 75:
            return Colors.GAUGE_OK
        else:
            return Colors.GAUGE_BAD

    def _draw(self):
        self.delete("all")
        cx, cy, r, lw = self.cx, self.cy, self.radius, self.line_width

        # ── Background track ──
        self.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=225, extent=-270,
            outline=Colors.GAUGE_TRACK, width=lw, style="arc",
        )

        # ── Thin outer ring (decorative) ──
        ro = r + lw // 2 + 6
        self.create_arc(
            cx - ro, cy - ro, cx + ro, cy + ro,
            start=225, extent=-270,
            outline=Colors.BORDER_SUBTLE, width=1, style="arc",
        )

        # ── Progress arc ──
        if self._current > 0.3:
            extent = -(self._current / 100) * 270
            color = self._get_color_for_value(self._current)

            # Main arc
            self.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=225, extent=extent,
                outline=color, width=lw, style="arc",
            )

            # Glow arc (wider, transparent feel)
            self.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=225, extent=extent,
                outline=self._get_color_for_value(self._current),
                width=lw + 6, style="arc",
            )
            # Overlay to fake glow (draw main arc on top)
            self.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=225, extent=extent,
                outline=color, width=lw, style="arc",
            )

        # ── Scale ticks ──
        for i in range(0, 28):
            angle_deg = 225 - i * (270 / 27)
            angle = math.radians(angle_deg)
            is_major = i % 9 == 0

            tick_out = r - lw // 2 - 4
            tick_in = tick_out - (8 if is_major else 4)

            x1 = cx + tick_in * math.cos(angle)
            y1 = cy - tick_in * math.sin(angle)
            x2 = cx + tick_out * math.cos(angle)
            y2 = cy - tick_out * math.sin(angle)

            pct_at = (i / 27) * 100
            if pct_at <= self._current:
                c = self._get_color_for_value(pct_at)
            else:
                c = Colors.WHITE_MICRO

            self.create_line(x1, y1, x2, y2, fill=c, width=2 if is_major else 1)

        # ── Percentage text ──
        val_str = f"{self._current:.0f}"
        self.create_text(
            cx, cy - 14,
            text=val_str,
            fill=Colors.WHITE,
            font=("Segoe UI", 42, "bold"),
        )
        # Percent sign (smaller, offset)
        self.create_text(
            cx + len(val_str) * 14 + 8, cy - 22,
            text="%",
            fill=Colors.WHITE_MUTED,
            font=("Segoe UI", 14),
        )

        # ── Sub text ──
        if self._sub_text:
            self.create_text(
                cx, cy + 22,
                text=self._sub_text,
                fill=Colors.WHITE_FAINT,
                font=("Segoe UI", 10),
            )

        # ── Status label ──
        if self._current < 40:
            label, lc = "OPTIMAL", Colors.SUCCESS
        elif self._current < 65:
            label, lc = "NORMAL", Colors.WARNING
        elif self._current < 85:
            label, lc = "HIGH", Colors.DANGER
        else:
            label, lc = "CRITICAL", Colors.DANGER

        # Status badge
        badge_y = cy + 48
        tw = len(label) * 6 + 16
        self.create_rectangle(
            cx - tw // 2, badge_y - 9, cx + tw // 2, badge_y + 9,
            fill=Colors.BG_DARK, outline=lc, width=1,
        )
        self.create_text(
            cx, badge_y,
            text=label,
            fill=lc,
            font=("Segoe UI", 8, "bold"),
        )

        # ── Bottom scale labels ──
        # 0%
        a0 = math.radians(225)
        self.create_text(
            cx + (r + lw + 14) * math.cos(a0),
            cy - (r + lw + 14) * math.sin(a0),
            text="0", fill=Colors.WHITE_MICRO, font=("Segoe UI", 8),
        )
        # 100%
        a100 = math.radians(225 - 270)
        self.create_text(
            cx + (r + lw + 14) * math.cos(a100),
            cy - (r + lw + 14) * math.sin(a100),
            text="100", fill=Colors.WHITE_MICRO, font=("Segoe UI", 8),
        )

    def set_value(self, value: float, sub_text: str = "", animate: bool = True):
        self._target = max(0, min(100, value))
        self._sub_text = sub_text
        if animate and abs(self._target - self._current) > 0.5:
            self._animate()
        else:
            self._current = self._target
            self._draw()

    def _animate(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
        diff = self._target - self._current
        if abs(diff) < 0.3:
            self._current = self._target
            self._draw()
            return
        step = diff * 0.1
        if abs(step) < 0.2:
            step = 0.2 if diff > 0 else -0.2
        self._current += step
        self._draw()
        self._anim_id = self.after(16, self._animate)


# ─────────────────────────────────────────────
# Premium Button
# ─────────────────────────────────────────────
class PremiumButton(ctk.CTkButton):
    """Clean monochrome button with subtle hover effect."""

    def __init__(self, master, text="", icon="", variant="primary",
                 command=None, width=200, height=44, **kwargs):

        styles = {
            "primary": {
                "fg": Colors.WHITE,
                "bg": Colors.BG_DARK,
                "hover": Colors.BG_ELEVATED,
                "text": Colors.BG_DARK,
                "border": Colors.BORDER,
            },
            "secondary": {
                "fg": Colors.BG_ELEVATED,
                "bg": "transparent",
                "hover": Colors.BG_CARD_HOVER,
                "text": Colors.WHITE_DIM,
                "border": Colors.BORDER,
            },
            "danger": {
                "fg": Colors.DANGER_DIM,
                "bg": "transparent",
                "hover": "#1a0a0a",
                "text": Colors.DANGER,
                "border": Colors.DANGER_DIM,
            },
        }

        s = styles.get(variant, styles["primary"])
        display = f"  {icon}   {text}" if icon else text

        super().__init__(
            master,
            text=display,
            command=command,
            width=width,
            height=height,
            corner_radius=10,
            fg_color=s["fg"],
            hover_color=s["hover"],
            text_color=s["text"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            border_width=1,
            border_color=s["border"],
            anchor="center",
            **kwargs,
        )


# ─────────────────────────────────────────────
# Stat Card
# ─────────────────────────────────────────────
class StatCard(ctk.CTkFrame):
    """Minimal stat card with label, value, and subtle accent."""

    def __init__(self, master, label="", value="—", icon="", width=155, **kwargs):
        super().__init__(
            master, width=width, height=88,
            corner_radius=14,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            **kwargs,
        )
        self.pack_propagate(False)

        # Top row: icon + label
        top = ctk.CTkFrame(self, fg_color="transparent", height=18)
        top.pack(fill="x", padx=14, pady=(12, 0))

        if icon:
            ctk.CTkLabel(
                top, text=icon, font=ctk.CTkFont(size=12),
                text_color=Colors.WHITE_FAINT,
            ).pack(side="right")

        ctk.CTkLabel(
            top, text=label,
            font=Fonts.caption(10),
            text_color=Colors.WHITE_FAINT,
            anchor="e",
        ).pack(side="right", padx=(0, 5))

        # Value
        self._val = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=Colors.WHITE,
            anchor="w",
        )
        self._val.pack(padx=14, pady=(2, 0), anchor="w")

        # Bottom thin line
        self._line = ctk.CTkFrame(self, height=2, corner_radius=1, fg_color=Colors.BORDER)
        self._line.pack(fill="x", padx=14, pady=(0, 10), side="bottom")

    def set_value(self, value: str, color: str = None):
        self._val.configure(text=value)
        if color:
            self._val.configure(text_color=color)
            self._line.configure(fg_color=color)


# ─────────────────────────────────────────────
# Process List
# ─────────────────────────────────────────────
class ProcessList(ctk.CTkScrollableFrame):
    """Clean process list with monochrome styling."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=14,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.BORDER_SUBTLE,
            scrollbar_button_color=Colors.WHITE_MICRO,
            scrollbar_button_hover_color=Colors.WHITE_GHOST,
            **kwargs,
        )

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=28)
        hdr.pack(fill="x", padx=10, pady=(6, 0))

        ctk.CTkLabel(
            hdr, text="PROCESS",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=Colors.WHITE_MICRO,
        ).pack(side="left")

        ctk.CTkLabel(
            hdr, text="MEMORY",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=Colors.WHITE_MICRO,
        ).pack(side="right")

        sep = ctk.CTkFrame(self, height=1, fg_color=Colors.BORDER_SUBTLE)
        sep.pack(fill="x", padx=10, pady=(2, 4))

        self._rows = []

    def update_processes(self, processes: list[dict]):
        for row in self._rows:
            row.destroy()
        self._rows.clear()

        for i, proc in enumerate(processes):
            row = ctk.CTkFrame(
                self,
                fg_color="transparent",
                corner_radius=6,
                height=30,
            )
            row.pack(fill="x", padx=6, pady=1)
            row.pack_propagate(False)

            # Rank number
            ctk.CTkLabel(
                row,
                text=f"{i+1:2d}",
                font=ctk.CTkFont(family="Consolas", size=10),
                text_color=Colors.WHITE_MICRO,
                width=20,
            ).pack(side="left", padx=(6, 4))

            # Indicator dot
            mem_mb = proc.get("memory_mb", 0)
            if mem_mb > 500:
                dot_c = Colors.DANGER
            elif mem_mb > 200:
                dot_c = Colors.WARNING
            elif mem_mb > 50:
                dot_c = Colors.WHITE_FAINT
            else:
                dot_c = Colors.WHITE_MICRO

            dot = ctk.CTkFrame(row, width=4, height=4, corner_radius=2, fg_color=dot_c)
            dot.pack(side="left", padx=(0, 6), pady=13)

            # Process name
            name = proc.get("name", "") or ""
            if not name or name.strip() == "":
                name = f"PID:{proc.get('pid', '?')}"
            if len(name) > 28:
                name = name[:25] + "..."

            ctk.CTkLabel(
                row,
                text=name,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=Colors.WHITE_DIM if mem_mb > 100 else Colors.WHITE_FAINT,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            # Memory value
            if mem_mb >= 1024:
                mem_str = f"{mem_mb/1024:.1f} GB"
            else:
                mem_str = f"{mem_mb:.0f} MB"

            ctk.CTkLabel(
                row,
                text=mem_str,
                font=ctk.CTkFont(family="Consolas", size=11),
                text_color=dot_c,
                width=65,
                anchor="e",
            ).pack(side="right", padx=(4, 10))

            # Thin mini bar
            bar_w = min(40, max(2, int(proc.get("memory_percent", 0) * 4)))
            bar_bg = ctk.CTkFrame(row, width=40, height=3, corner_radius=1, fg_color=Colors.BG_DARK)
            bar_bg.pack(side="right", padx=(0, 4), pady=13)
            bar_bg.pack_propagate(False)
            ctk.CTkFrame(bar_bg, width=bar_w, height=3, corner_radius=1, fg_color=dot_c).pack(side="left")

            self._rows.append(row)


# ─────────────────────────────────────────────
# Status Toast
# ─────────────────────────────────────────────
class StatusToast(ctk.CTkFrame):
    """Minimal status notification."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master, height=44, corner_radius=10,
            fg_color=Colors.BG_ELEVATED,
            border_width=1,
            border_color=Colors.BORDER,
            **kwargs,
        )
        self.pack_propagate(False)

        self._icon = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=14))
        self._icon.pack(side="left", padx=(14, 6))

        self._msg = ctk.CTkLabel(
            self, text="",
            font=Fonts.body(12),
            text_color=Colors.WHITE_DIM,
            anchor="w",
        )
        self._msg.pack(side="left", fill="x", expand=True, padx=(0, 14))

        self._hide_id = None

    def show(self, message, icon="●", color=Colors.WHITE_FAINT, duration=4000):
        if self._hide_id:
            self.after_cancel(self._hide_id)
        self._icon.configure(text=icon, text_color=color)
        self._msg.configure(text=message)
        self.configure(border_color=Colors.BORDER_LIGHT)
        self.pack(fill="x", padx=20, pady=(0, 12), side="bottom")
        if duration > 0:
            self._hide_id = self.after(duration, self.hide)

    def hide(self):
        self.pack_forget()
