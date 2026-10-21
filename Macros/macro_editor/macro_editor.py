"""Macro editor window. Pieces: widgets.py (lists/theme), macro_form.py + macro_fields.py (form),
function_editor.py (scripts page), profile_store.py (config.json)."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from . import clipboard
from .function_editor import FunctionEditor
from .macro_fields import KNOWN_KEYS
from .macro_form import MacroForm
from .profile_store import Store
from .widgets import BG, Action, ListPanel, apply_style

NEW_MACRO = {"name": "new_macro", "key": "f6", "type": "keyboard_press",
             "key_to_press": "a", "Interval": 0.001, "run_once": False}
NEW_ONBOOT_MACRO = {"name": "new_function", "type": "function", "function_name": ""}


class MacroEditor:
    def __init__(self, root):
        self.root = root
        root.title("Macro Editor")
        root.geometry("1180x660")
        root.minsize(1180, 660)
        root.configure(bg=BG)
        apply_style(root)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.store = Store()
        self.profile = None      # selected profile name
        self.macro_idx = None    # selected macro index (None = editing the profile itself)

        self.main = self._build_main()
        self.funcs = FunctionEditor(root, on_back=self.show_main)
        for page in (self.funcs, self.main):    # stacked; tkraise() switches page
            page.grid(row=0, column=0, sticky="nsew")
        self.main.tkraise()

        self.refresh_profiles()

    # --- UI ---------------------------------------------------------------
    def _build_main(self):
        main = ttk.Frame(self.root, style="Root.TFrame")
        main.columnconfigure(0, weight=1, uniform="a")
        main.columnconfigure(2, weight=2, uniform="a")
        main.rowconfigure(0, weight=1)

        # Add a button / menu entry / shortcut here = one Action line.
        self.profile_panel = ListPanel(main, "Profiles", [
            Action("Copy Profile", self.copy_profile, "<Control-c>", False),
            Action("Paste Profile", self.paste_profile, "<Control-v>", False),
            Action("Add Profile", self.add_profile),
            Action("Remove Profile", self.remove_profile, "<Delete>"),
        ], self.on_profile_select, self.reorder_profiles)
        self.profile_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)

        ttk.Separator(main, orient="vertical").grid(row=0, column=1, sticky="ns", pady=20)

        right = ttk.Frame(main)
        right.grid(row=0, column=2, sticky="nsew", padx=(10, 20), pady=20)
        right.columnconfigure(0, weight=1)
        right.columnconfigure(1, weight=2)
        right.rowconfigure(0, weight=1)

        self.macro_panel = ListPanel(right, "Macros", [
            Action("Copy Macro", self.copy_macro, "<Control-c>", False),
            Action("Paste Macro", self.paste_macro, "<Control-v>", False),
            Action("Add Macro", self.add_macro),
            Action("Remove Macro", self.remove_macro, "<Delete>"),
        ], self.on_macro_select, self.reorder_macros)
        self.macro_panel.grid(row=0, column=0, sticky="nsew")

        self.form = MacroForm(right, self.save)
        self.form.grid(row=0, column=1, sticky="nsew", padx=(20, 0))

        tk.Button(main, text="⚙️", command=self.open_functions, font=("Segoe UI", 12), bd=0,
                  highlightthickness=0, bg=BG, activebackground=BG, relief="flat").place(x=5, y=5)
        return main

    def open_functions(self):
        self.funcs.refresh()
        self.funcs.tkraise()

    def show_main(self):
        self.main.tkraise()
        self.form.layout()   # picks up new/removed function files

    # --- selection / refresh ---------------------------------------------
    @property
    def macros(self):
        return self.store.macros(self.profile) if self.profile else []

    def refresh_profiles(self, select=None):
        names = self.store.names()
        self.profile = select or self.profile
        if self.profile not in names:
            self.profile = names[0] if names else None
        self.profile_panel.set_items(names, names.index(self.profile) if self.profile else None)
        self.refresh_macros()

    def refresh_macros(self, select=None):
        macros = self.macros
        self.macro_idx = select if select is not None and select < len(macros) else None
        self.macro_panel.set_items([m.get("name", "unnamed") for m in macros], self.macro_idx)
        self.show_form()

    def show_form(self):
        if self.profile is None:
            self.form.show("none")
        elif self.macro_idx is None:
            self.form.show("profile", self.profile,
                           {"name": self.profile, "exe": self.store.exe(self.profile) or ""})
        else:
            self.form.show("macro", self.profile, {"type": "keyboard_press", **self.macros[self.macro_idx]})

    def on_profile_select(self, idx):
        self.profile = self.store.names()[idx]
        self.refresh_macros()

    def on_macro_select(self, idx):
        self.macro_idx = idx
        self.show_form()

    # --- profiles ---------------------------------------------------------
    def add_profile(self):
        name = (simpledialog.askstring("New Profile", "Enter profile name:") or "").strip()
        if not name:
            return
        if name in self.store.profiles:
            return messagebox.showerror("Error", "Profile already exists.")
        exe = (simpledialog.askstring("File Path", "Enter executable file path (optional):") or "").strip()
        self.store.put(name, {exe: {"macros": []}} if exe else {"macros": []})
        self.refresh_profiles(select=name)

    def remove_profile(self):
        if not self.profile:
            return messagebox.showwarning("Warning", "No profile selected to delete.")
        if messagebox.askyesno("Confirm", f"Delete profile '{self.profile}'?"):
            self.store.remove(self.profile)
            self.profile = None
            self.refresh_profiles()

    def copy_profile(self):
        if not self.profile:
            return messagebox.showwarning("Warning", "No profile selected to copy.")
        clipboard.copy(self.root, "profile", {"name": self.profile, "profile": self.store.profiles[self.profile]})

    def paste_profile(self):
        pasted = clipboard.read_profile(self.root)
        if not pasted:
            return print("[Info] Clipboard doesn't hold a copied profile; ignoring paste.")
        old, data = pasted
        name = (simpledialog.askstring("Paste Profile", "Enter name for pasted profile:",
                                       initialvalue=f"{old}_copy") or "").strip()
        if not name:
            return
        if name in self.store.profiles:
            return messagebox.showerror("Error", "Profile name already exists.")
        self.store.put(name, data)
        self.refresh_profiles(select=name)

    def reorder_profiles(self, start, end):
        name = self.store.names()[start]
        self.store.move(start, end)
        self.refresh_profiles(select=name)

    # --- macros -----------------------------------------------------------
    def add_macro(self):
        if not self.profile:
            return
        self.macros.append(dict(NEW_ONBOOT_MACRO if self.profile == "OnBoot" else NEW_MACRO))
        self.store.save()
        self.refresh_macros(select=len(self.macros) - 1)

    def remove_macro(self):
        if self.macro_idx is None:
            return messagebox.showwarning("Warning", "No macro selected to delete.")
        if messagebox.askyesno("Confirm", "Delete selected macro?"):
            del self.macros[self.macro_idx]
            self.store.save()
            self.refresh_macros()

    def copy_macro(self):
        if self.macro_idx is None:
            return messagebox.showwarning("Warning", "No macro selected to copy.")
        clipboard.copy(self.root, "macro", self.macros[self.macro_idx])

    def paste_macro(self):
        macro = clipboard.read_macro(self.root)
        if not macro:
            return print("[Info] Clipboard doesn't hold a macro; ignoring paste.")
        if not self.profile:
            return messagebox.showwarning("Warning", "No profile selected. Please select a profile first.")
        name = (simpledialog.askstring("Paste Macro", "Enter name for pasted macro:",
                                       initialvalue=f"{macro['name']}_copy") or "").strip()
        if not name:
            return
        self.macros.append({**macro, "name": name})
        self.store.save()
        self.refresh_macros(select=len(self.macros) - 1)

    def reorder_macros(self, start, end):
        macros = self.macros
        macros.insert(end, macros.pop(start))
        self.store.save()
        self.refresh_macros(select=end)

    # --- saving the form --------------------------------------------------
    def save(self):
        try:
            vals = self.form.values()
        except ValueError as e:
            return messagebox.showerror("Invalid Input", str(e))
        if not vals.get("name"):
            return messagebox.showerror("Error", "Name can't be empty.")
        if self.macro_idx is None:
            self._save_profile(vals)
        else:
            self._save_macro(vals)

    def _save_profile(self, vals):
        name = vals["name"]
        if name != self.profile:
            if name in self.store.profiles:
                return messagebox.showerror("Error", "Profile name already exists.")
            self.store.rename(self.profile, name)
            self.profile = name
        if "exe" in vals:
            self.store.set_exe(name, vals["exe"])
        self.refresh_profiles()

    def _save_macro(self, vals):
        macro = self.macros[self.macro_idx]
        for key in KNOWN_KEYS - vals.keys():    # drop keys that belong to hidden fields
            macro.pop(key, None)
        macro.update(vals)
        if self.profile == "OnBoot":
            macro["type"] = "function"
        self.store.save()
        self.refresh_macros(select=self.macro_idx)


def run():
    root = tk.Tk()
    MacroEditor(root)
    root.mainloop()

