"""The detail form on the right. Built entirely from macro_fields.FIELDS."""
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

from .macro_fields import CLICKS, FIELDS
from .widgets import FONT


class MacroForm(ttk.Frame):
    def __init__(self, master, on_save):
        super().__init__(master, padding=15)
        self.columnconfigure(1, weight=1)
        self.mode, self.profile = "none", None   # mode: none | profile | macro
        self.vars, self.rows = {}, {}

        for f in FIELDS:
            if f.kind == "check":
                self.vars[f.id] = var = tk.BooleanVar()
                self.rows[f.id] = (None, ttk.Checkbutton(self, variable=var))
                continue
            self.vars[f.id] = var = tk.StringVar()
            label = ttk.Label(self, style="Section.TLabel")
            if f.kind == "combo":
                w = ttk.Combobox(self, textvariable=var, state="readonly", font=FONT, width=27,
                                 values=() if callable(f.values) else f.values)
                w.bind("<<ComboboxSelected>>", self._on_pick)
                if callable(f.values):   # re-read the list (new recordings / scripts) every time the dropdown opens
                    w.config(postcommand=lambda w=w, f=f: w.config(values=f.values()))
            else:
                w = ttk.Entry(self, textvariable=var, font=FONT, width=30)
            self.rows[f.id] = (label, w)

        self.save_btn = ttk.Button(self, command=on_save)

    # --- state ------------------------------------------------------------
    def ctx(self):
        return SimpleNamespace(
            mode=self.mode,
            onboot=self.profile == "OnBoot",
            exe_allowed=self.profile not in ("OnBoot", "Desktop"),
            type=self.vars["type"].get(),
        )

    def show(self, mode, profile=None, data=None):
        self.mode, self.profile = mode, profile
        if data is not None:
            self.fill(data)
        self.layout()

    def fill(self, data):
        for f in FIELDS:
            v = data.get(f.key)
            self.vars[f.id].set(bool(v) if f.kind == "check" else "" if v is None else str(v))

    def values(self):
        """{config_key: value} for every visible field. Raises ValueError on bad input."""
        c, out = self.ctx(), {}
        for f in FIELDS:
            if not f.show(c):
                continue
            raw = self.vars[f.id].get()
            if f.kind == "check":
                out[f.key] = raw
            elif f.omit_blank and not raw.strip():
                continue
            else:
                try:
                    out[f.key] = f.conv(raw) if f.conv else raw
                except ValueError:
                    raise ValueError(f"'{self._text(f, c)}' is not valid.") from None
        return out

    # --- layout -----------------------------------------------------------
    @staticmethod
    def _text(f, c):
        return f.label(c) if callable(f.label) else f.label

    def _on_pick(self, _=None):
        if self.vars["button"].get() not in CLICKS:
            self.vars["button"].set(CLICKS[0])
        self.layout()

    def layout(self):
        """Grid every visible field top-to-bottom; hide the rest."""
        c, row = self.ctx(), 0
        for f in FIELDS:
            label, w = self.rows[f.id]
            if not f.show(c):
                w.grid_remove()
                if label:
                    label.grid_remove()
                continue
            text = self._text(f, c)
            if label is None:   # checkbox
                w.config(text=text)
                w.grid(row=row, column=1, sticky="w", pady=(10, 0))
            else:
                label.config(text=text + ":")
                label.grid(row=row, column=0, sticky="e", pady=8, padx=(0, 15))
                if callable(f.values):
                    w["values"] = f.values()
                w.grid(row=row, column=1, sticky="ew", pady=8)
            row += 1

        if self.mode == "none":
            self.save_btn.grid_remove()
        else:
            self.save_btn.config(text="Save Profile" if self.mode == "profile" else "Save Macro")
            self.save_btn.grid(row=row, column=1, sticky="e", pady=(15, 0))
