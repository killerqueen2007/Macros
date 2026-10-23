"""Recorder theme: the editor's base theme plus the recorder's extra styles."""
from tkinter import ttk

from ..widgets import ACCENT, BG, BOLD, CARD, FG, FONT, apply_style as _base_style

RED, GREEN = "#d13438", "#107c10"


def apply_style(root):
    _base_style(root)
    s = ttk.Style(root)
    s.configure("Hint.TLabel", font=("Segoe UI", 9), background=CARD, foreground="#777777")
    s.configure("Status.TLabel", font=BOLD, background=CARD, foreground=FG)
    s.map("TButton", background=[("active", ACCENT), ("pressed", "#005a9e"), ("disabled", "#a0a0a0")])
    s.configure("Rec.TButton", background=RED)
    s.map("Rec.TButton", background=[("active", RED), ("pressed", "#a4262c"), ("disabled", "#a0a0a0")])
    s.configure("Treeview", font=FONT, rowheight=26, background=CARD, fieldbackground=CARD, foreground=FG)
    s.configure("Treeview.Heading", font=BOLD, background="#e6e6e6", foreground=FG, padding=6)
    s.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])
    # compact inputs: they are also used for in-table cell editing
    s.configure("TEntry", foreground=FG, fieldbackground="#f9f9f9", padding=2, font=FONT)
    s.configure("TCombobox", foreground=FG, fieldbackground="#f9f9f9", padding=2, font=FONT)
