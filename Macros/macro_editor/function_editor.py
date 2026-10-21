"""Editor page for the scripts in user_functions/."""
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from config import USER_FUNCTIONS_DIR
from user_functions import list_function_names


def _path(name):
    return os.path.join(USER_FUNCTIONS_DIR, name + ".py")


class FunctionEditor(ttk.Frame):
    def __init__(self, master, on_back):
        super().__init__(master, padding=15)
        self.current = None
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text="Function Files", style="Header.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.files = tk.Listbox(self, width=26, exportselection=False)
        self.files.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.files.bind("<<ListboxSelect>>", lambda e: self.load())

        box = ttk.Frame(self)
        box.grid(row=1, column=1, sticky="nsew")
        box.rowconfigure(0, weight=1)
        box.columnconfigure(0, weight=1)
        self.text = tk.Text(box, wrap="none", font=("Consolas", 11), undo=True)
        self.text.grid(row=0, column=0, sticky="nsew")
        ys = ttk.Scrollbar(box, command=self.text.yview)
        ys.grid(row=0, column=1, sticky="ns")
        xs = ttk.Scrollbar(box, orient="horizontal", command=self.text.xview)
        xs.grid(row=1, column=0, sticky="ew")
        self.text.config(yscrollcommand=ys.set, xscrollcommand=xs.set)

        # add a button here = one line
        buttons = (("⬅ Back", on_back), ("💾 Save", self.save),
                   ("➕ New Function", self.new), ("🗑 Remove Function", self.delete))
        row = ttk.Frame(self)
        row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for i, (label, cmd) in enumerate(buttons):
            row.columnconfigure(i, weight=1, uniform="b")
            ttk.Button(row, text=label, command=cmd).grid(row=0, column=i, sticky="ew", padx=3)

    def refresh(self, select=None):
        names = list_function_names()
        self.files.delete(0, "end")
        self.files.insert("end", *names)
        self.current = None
        self.text.delete("1.0", "end")
        if select in names:
            self.files.selection_set(names.index(select))
            self.load()

    def load(self):
        sel = self.files.curselection()
        if not sel:
            return
        self.current = self.files.get(sel[0])
        with open(_path(self.current), encoding="utf-8") as f:
            content = f.read()
        self.text.delete("1.0", "end")
        self.text.insert("end", content)

    def save(self):
        if not self.current:
            messagebox.showerror("Error", "No file selected.")
            return
        with open(_path(self.current), "w", encoding="utf-8") as f:
            f.write(self.text.get("1.0", "end-1c"))
        messagebox.showinfo("Saved", f"{self.current}.py saved!")

    def new(self):
        name = (simpledialog.askstring("Function Name", "Enter function name:") or "").strip()
        if not name:
            return
        if os.path.exists(_path(name)):
            messagebox.showerror("Error", "That file already exists.")
            return
        with open(_path(name), "w", encoding="utf-8") as f:
            f.write(f'print("{name}")\n')
        self.refresh(select=name)

    def delete(self):
        if not self.current:
            messagebox.showerror("Error", "No function selected.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete '{self.current}.py'?"):
            return
        try:
            os.remove(_path(self.current))
        except OSError as e:
            messagebox.showerror("Error", f"Could not delete file:\n{e}")
            return
        self.refresh()
