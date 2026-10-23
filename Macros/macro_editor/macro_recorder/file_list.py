"""Left-hand list of saved recordings. Click one to open it."""
import tkinter as tk
from tkinter import ttk

from recordings import list_recording_names

from .theme import ACCENT, CARD, FG, FONT


class FileList(ttk.Frame):
    def __init__(self, master, on_pick):
        super().__init__(master)
        self.on_pick = on_pick     # on_pick(name) when the user clicks a file
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Recordings", style="Header.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.listbox = tk.Listbox(
            self, width=24, font=FONT, bg=CARD, fg=FG, selectbackground=ACCENT, selectforeground="white",
            relief="flat", activestyle="none", exportselection=False,
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground="#ccc")
        self.listbox.grid(row=1, column=0, sticky="ns")
        bar = ttk.Scrollbar(self, command=self.listbox.yview)
        bar.grid(row=1, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=bar.set)
        self.listbox.bind("<<ListboxSelect>>", self._picked)

    def refresh(self, current=None):
        """Re-read the folder and highlight `current` (nothing is highlighted if it isn't saved)."""
        names = list_recording_names()
        self.listbox.delete(0, "end")
        self.listbox.insert("end", *names)
        self.listbox.selection_clear(0, "end")
        if current in names:
            idx = names.index(current)
            self.listbox.selection_set(idx)
            self.listbox.see(idx)

    def clear_selection(self):
        self.listbox.selection_clear(0, "end")

    def _picked(self, _event=None):
        sel = self.listbox.curselection()
        if sel:
            self.on_pick(self.listbox.get(sel[0]))
