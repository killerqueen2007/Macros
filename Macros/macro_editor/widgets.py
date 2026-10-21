"""Theme + ListPanel (title, scrolling list, buttons, right-click menu, shortcuts, drag-to-reorder)."""
import tkinter as tk
from collections import namedtuple
from tkinter import ttk

BG, CARD, FG, ACCENT = "#f0f0f0", "#ffffff", "#222222", "#007acc"
FONT = ("Segoe UI", 11)
BOLD = ("Segoe UI", 11, "bold")

# label, command, keyboard shortcut (e.g. "<Delete>"), also show as a button under the list?
Action = namedtuple("Action", "label command key button", defaults=(None, True))


def apply_style(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("TFrame", background=CARD)
    s.configure("Root.TFrame", background=BG)
    s.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background=CARD, foreground=ACCENT)
    s.configure("Section.TLabel", font=BOLD, background=CARD, foreground=FG)
    s.configure("TLabel", font=FONT, background=CARD, foreground=FG)
    s.configure("TCheckbutton", font=FONT, background=CARD, foreground=FG)
    s.configure("TButton", font=BOLD, background=ACCENT, foreground="white", padding=8, relief="flat")
    s.map("TButton", background=[("active", ACCENT), ("pressed", "#005a9e")])
    s.configure("TEntry", foreground=FG, fieldbackground="#f9f9f9", padding=6, font=FONT)
    s.configure("TCombobox", foreground=FG, fieldbackground="#f9f9f9", padding=6, font=FONT)
    s.map("TCombobox", fieldbackground=[("readonly", "#f9f9f9")])


class ListPanel(ttk.Frame):
    """Pass a list of Actions: they become buttons, right-click menu entries and shortcuts."""

    def __init__(self, master, title, actions, on_select, on_reorder):
        super().__init__(master, padding=15)
        self.on_reorder = on_reorder
        self._start = None   # (x, y, index) of the mouse press
        self._ghost = None   # label that follows the cursor while dragging
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=title, style="Header.TLabel").grid(row=0, column=0, sticky="w")

        box = ttk.Frame(self)
        box.grid(row=1, column=0, sticky="nsew", pady=10)
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        lb = self.listbox = tk.Listbox(
            box, bg=CARD, fg=FG, font=FONT, selectbackground=ACCENT, selectforeground="#fff",
            relief="flat", activestyle="none", exportselection=False, borderwidth=0,
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground="#ccc")
        lb.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(box, command=lb.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        lb.config(yscrollcommand=scroll.set)
        lb.bind("<<ListboxSelect>>", lambda e: self.selected is not None and on_select(self.selected))

        # buttons
        buttons = [a for a in actions if a.button]
        row = ttk.Frame(self)
        row.grid(row=2, column=0, sticky="ew")
        for i, a in enumerate(buttons):
            row.columnconfigure(i, weight=1, uniform="b")
            ttk.Button(row, text=a.label, command=a.command).grid(row=0, column=i, sticky="ew", padx=3)

        # right-click menu (separator where button-less actions end)
        menu = tk.Menu(self, tearoff=0)
        for prev, a in zip([None] + list(actions), actions):
            if prev and prev.button != a.button:
                menu.add_separator()
            menu.add_command(label=a.label, command=a.command)

        def popup(e):
            try:
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                menu.grab_release()
        lb.bind("<Button-3>", popup)

        # keyboard shortcuts (only while this list has focus)
        for a in actions:
            if a.key:
                lb.bind(a.key, lambda e, cmd=a.command: cmd())

        lb.bind("<ButtonPress-1>", self._press, add="+")
        lb.bind("<B1-Motion>", self._motion, add="+")
        lb.bind("<ButtonRelease-1>", self._release, add="+")

    # --- public -----------------------------------------------------------
    @property
    def selected(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def select(self, idx):
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(idx)
        self.listbox.see(idx)

    def set_items(self, items, select=None):
        self.listbox.delete(0, "end")
        self.listbox.insert("end", *items)
        if select is not None:
            self.select(select)

    # --- drag to reorder --------------------------------------------------
    def _press(self, e):
        self._start = (e.x, e.y, self.listbox.nearest(e.y))

    def _motion(self, e):
        if not self._start or not self.listbox.size():
            return
        x0, y0, idx = self._start
        top = self.winfo_toplevel()
        if self._ghost is None:
            if abs(e.x - x0) <= 5 and abs(e.y - y0) <= 5:
                return
            self._ghost = tk.Label(top, text=self.listbox.get(idx), bg=ACCENT, fg="white", relief="raised")
        self._ghost.place(x=e.x_root - top.winfo_rootx(), y=e.y_root - top.winfo_rooty())

    def _release(self, e):
        if self._ghost is not None:
            self._ghost.destroy()
            self._ghost = None
            end = self.listbox.nearest(e.y)
            if end != self._start[2]:
                self.on_reorder(self._start[2], end)
        self._start = None
