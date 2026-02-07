import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

CONFIG_PATH = "config.json"

script_dir = os.path.dirname(os.path.abspath(__file__))
user_functions_dir = os.path.join(script_dir, "user_functions")
os.makedirs(user_functions_dir, exist_ok=True)

class MacroEditor:
    def __init__(self, root):
        
        os.makedirs(user_functions_dir, exist_ok=True)
        self.root = root
        self.root.title("Macro Editor")
        self.root.geometry("1180x660")
        self.root.minsize(1180, 660)
        self.root.configure(bg="#f0f0f0")

        self.config = self.load_config()
        self.selected_profile = None
        self.selected_macro_index = None

        self.drag_label = None

        self.profile_drag_data = {"start_index": None}
        self.profile_dragging = False
        self.profile_drag_start_pos = None

        self.macro_drag_data = {"start_index": None}
        self.macro_dragging = False
        self.macro_drag_start_pos = None

        # Clipboard storage
        self.profile_clipboard = None
        self.macro_clipboard = None

        # State preservation variables
        self.main_ui_widgets = []
        self.function_editor_widgets = []
        self.current_view = "main"  # "main" or "function_editor"

        self.build_ui()
        self.refresh_profiles()
        self.setup_drag_and_drop()
        self.setup_keyboard_shortcuts()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        return {"profiles": {}, "global": {"loop_delay": 0.001}}

    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)

    def get_function_files(self):
        """Get list of Python files in user_functions directory without .py extension"""
        function_files = []
        if os.path.exists(user_functions_dir):
            for file in os.listdir(user_functions_dir):
                if file.endswith(".py"):
                    function_files.append(file[:-3])  # Remove .py extension
        return function_files

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for copy/paste/delete"""
        self.root.bind('<Control-c>', self.handle_copy)
        self.root.bind('<Control-v>', self.handle_paste)
        self.root.bind('<Delete>', self.handle_delete)
        # Also bind right-click context menus
        self.profile_listbox.bind('<Button-3>', self.show_profile_context_menu)
        self.macro_listbox.bind('<Button-3>', self.show_macro_context_menu)

    def handle_copy(self, event=None):
        """Handle Ctrl+C based on which listbox has focus"""
        focused_widget = self.root.focus_get()
        if focused_widget == self.profile_listbox:
            self.copy_profile()
        elif focused_widget == self.macro_listbox:
            self.copy_macro()

    def handle_paste(self, event=None):
        """Handle Ctrl+V based on which listbox has focus"""
        focused_widget = self.root.focus_get()
        if focused_widget == self.profile_listbox:
            self.paste_profile()
        elif focused_widget == self.macro_listbox:
            self.paste_macro()

    def handle_delete(self, event=None):
        """Handle DEL key based on which listbox has focus"""
        focused_widget = self.root.focus_get()
        if focused_widget == self.profile_listbox:
            self.remove_profile()
        elif focused_widget == self.macro_listbox:
            self.remove_macro()

    def show_profile_context_menu(self, event):
        """Show right-click context menu for profiles"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Copy Profile", command=self.copy_profile)
        context_menu.add_command(label="Paste Profile", command=self.paste_profile)
        context_menu.add_separator()
        context_menu.add_command(label="Add Profile", command=self.add_profile)
        context_menu.add_command(label="Remove Profile", command=self.remove_profile)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def show_macro_context_menu(self, event):
        """Show right-click context menu for macros"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Copy Macro", command=self.copy_macro)
        context_menu.add_command(label="Paste Macro", command=self.paste_macro)
        context_menu.add_separator()
        context_menu.add_command(label="Add Macro", command=self.add_macro)
        context_menu.add_command(label="Remove Macro", command=self.remove_macro)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def copy_profile(self):
        """Copy selected profile to clipboard"""
        if not self.selected_profile:
            messagebox.showwarning("Warning", "No profile selected to copy.")
            return
        
        # Deep copy the profile data
        profile_data = json.loads(json.dumps(self.config["profiles"][self.selected_profile]))
        self.profile_clipboard = {
            "name": self.selected_profile,
            "data": profile_data
        }
        messagebox.showinfo("Success", f"Profile '{self.selected_profile}' copied to clipboard.")

    def paste_profile(self):
        """Paste profile from clipboard"""
        if not self.profile_clipboard:
            messagebox.showwarning("Warning", "No profile in clipboard to paste.")
            return
        
        # Ask for new profile name
        original_name = self.profile_clipboard["name"]
        new_name = simpledialog.askstring("Paste Profile", 
                                        f"Enter name for pasted profile:", 
                                        initialvalue=f"{original_name}_copy")
        if not new_name:
            return
        
        if new_name in self.config["profiles"]:
            messagebox.showerror("Error", "Profile name already exists.")
            return
        
        # Paste the profile data
        self.config["profiles"][new_name] = json.loads(json.dumps(self.profile_clipboard["data"]))
        self.save_config()
        self.refresh_profiles()
        
        # Select the newly pasted profile
        profile_names = list(self.config["profiles"].keys())
        if new_name in profile_names:
            idx = profile_names.index(new_name)
            self.profile_listbox.selection_set(idx)
            self.profile_listbox.see(idx)
            self.selected_profile = new_name
            self.refresh_macros()
            self.show_profile_mode()
        
        messagebox.showinfo("Success", f"Profile pasted as '{new_name}'.")

    def copy_macro(self):
        """Copy selected macro to clipboard"""
        if not self.selected_profile or self.selected_macro_index is None:
            messagebox.showwarning("Warning", "No macro selected to copy.")
            return
        
        profile_data = self.config["profiles"][self.selected_profile]
        
        # Get the macro data
        macros = []
        if "macros" in profile_data:
            macros = profile_data["macros"]
        else:
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    macros = data["macros"]
                    break
        
        if self.selected_macro_index >= len(macros):
            messagebox.showerror("Error", "Selected macro index is invalid.")
            return
        
        # Deep copy the macro data
        macro_data = json.loads(json.dumps(macros[self.selected_macro_index]))
        self.macro_clipboard = macro_data
        
        messagebox.showinfo("Success", f"Macro '{macro_data.get('name', 'unnamed')}' copied to clipboard.")

    def paste_macro(self):
        """Paste macro from clipboard"""
        if not self.macro_clipboard:
            messagebox.showwarning("Warning", "No macro in clipboard to paste.")
            return
        
        if not self.selected_profile:
            messagebox.showwarning("Warning", "No profile selected. Please select a profile first.")
            return
        
        # Ask for new macro name
        original_name = self.macro_clipboard.get("name", "unnamed")
        new_name = simpledialog.askstring("Paste Macro", 
                                        f"Enter name for pasted macro:", 
                                        initialvalue=f"{original_name}_copy")
        if not new_name:
            return
        
        # Create new macro with copied data
        new_macro = json.loads(json.dumps(self.macro_clipboard))
        new_macro["name"] = new_name
        
        # Add to current profile
        profile_data = self.config["profiles"][self.selected_profile]
        
        if "macros" in profile_data:
            profile_data["macros"].append(new_macro)
        else:
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    data["macros"].append(new_macro)
                    break
            else:
                profile_data["macros"] = [new_macro]
        
        self.save_config()
        self.refresh_macros()
        
        # Select the newly pasted macro
        macro_count = len(self.get_current_macros())
        if macro_count > 0:
            self.macro_listbox.selection_set(macro_count - 1)
            self.macro_listbox.see(macro_count - 1)
            self.selected_macro_index = macro_count - 1
            self.on_macro_select(None)
        
        messagebox.showinfo("Success", f"Macro pasted as '{new_name}'.")

    def get_current_macros(self):
        """Get current macros list for the selected profile"""
        if not self.selected_profile:
            return []
        
        profile_data = self.config["profiles"][self.selected_profile]
        
        if "macros" in profile_data:
            return profile_data["macros"]
        else:
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    return data["macros"]
        return []

    # Profile drag handlers:
    def profile_drag_start(self, event):
        self.profile_drag_start_pos = (event.x, event.y)
        self.profile_dragging = False
        self.profile_drag_data["start_index"] = self.profile_listbox.nearest(event.y)

    def profile_drag_motion(self, event):
        if not self.profile_drag_start_pos:
            return

        dx = abs(event.x - self.profile_drag_start_pos[0])
        dy = abs(event.y - self.profile_drag_start_pos[1])

        # Start dragging if moved more than 5 pixels
        if not self.profile_dragging and (dx > 5 or dy > 5):
            self.profile_dragging = True
            idx = self.profile_drag_data["start_index"]
            if self.drag_label:
                self.drag_label.destroy()
            if idx is not None:
                name = self.profile_listbox.get(idx)
                self.drag_label = tk.Label(self.root, text=name, bg="#007acc", fg="white", relief="raised")
                x = event.x_root - self.root.winfo_rootx()
                y = event.y_root - self.root.winfo_rooty()
                self.drag_label.place(x=x, y=y)

        if self.profile_dragging and self.drag_label is not None:
            x = event.x_root - self.root.winfo_rootx()
            y = event.y_root - self.root.winfo_rooty()
            self.drag_label.place(x=x, y=y)

    def profile_drag_end(self, event):
        if self.profile_dragging:
            if self.drag_label:
                self.drag_label.destroy()
                self.drag_label = None

            end_index = self.profile_listbox.nearest(event.y)
            start_index = self.profile_drag_data["start_index"]

            if start_index is not None and end_index != start_index:
                keys = list(self.config["profiles"].keys())
                item = keys.pop(start_index)
                keys.insert(end_index, item)

                self.config["profiles"] = {k: self.config["profiles"][k] for k in keys}
                self.save_config()
                self.refresh_profiles()
                self.profile_listbox.selection_set(end_index)
                self.profile_listbox.see(end_index)

        self.profile_dragging = False
        self.profile_drag_start_pos = None
        self.profile_drag_data["start_index"] = None

    # Macro drag handlers:
    def macro_drag_start(self, event):
        self.macro_drag_start_pos = (event.x, event.y)
        self.macro_dragging = False
        self.macro_drag_data["start_index"] = self.macro_listbox.nearest(event.y)

    def macro_drag_motion(self, event):
        if not self.macro_drag_start_pos:
            return

        dx = abs(event.x - self.macro_drag_start_pos[0])
        dy = abs(event.y - self.macro_drag_start_pos[1])

        # Start dragging if moved more than 5 pixels
        if not self.macro_dragging and (dx > 5 or dy > 5):
            self.macro_dragging = True
            idx = self.macro_drag_data["start_index"]
            if self.drag_label:
                self.drag_label.destroy()
            if idx is not None:
                name = self.macro_listbox.get(idx)
                self.drag_label = tk.Label(self.root, text=name, bg="#007acc", fg="white", relief="raised")
                x = event.x_root - self.root.winfo_rootx()
                y = event.y_root - self.root.winfo_rooty()
                self.drag_label.place(x=x, y=y)

        if self.macro_dragging and self.drag_label is not None:
            x = event.x_root - self.root.winfo_rootx()
            y = event.y_root - self.root.winfo_rooty()
            self.drag_label.place(x=x, y=y)

    def macro_drag_end(self, event):
        if self.macro_dragging:
            if self.drag_label:
                self.drag_label.destroy()
                self.drag_label = None

            end_index = self.macro_listbox.nearest(event.y)
            start_index = self.macro_drag_data["start_index"]

            if start_index is not None and end_index != start_index:
                profile_data = self.config["profiles"][self.selected_profile]

                macros = []
                if "macros" in profile_data:
                    macros = profile_data["macros"]
                else:
                    for filepath, data in profile_data.items():
                        if isinstance(data, dict) and "macros" in data:
                            macros = data["macros"]
                            break

                if macros:
                    item = macros.pop(start_index)
                    macros.insert(end_index, item)

                    self.save_config()
                    self.refresh_macros()
                    self.macro_listbox.selection_set(end_index)
                    self.macro_listbox.see(end_index)

        self.macro_dragging = False
        self.macro_drag_start_pos = None
        self.macro_drag_data["start_index"] = None

    def setup_drag_and_drop(self):
        # For profile listbox
        self.profile_listbox.bind("<ButtonPress-1>", self.profile_drag_start)
        self.profile_listbox.bind("<B1-Motion>", self.profile_drag_motion)
        self.profile_listbox.bind("<ButtonRelease-1>", self.profile_drag_end)

        # For macro listbox
        self.macro_listbox.bind("<ButtonPress-1>", self.macro_drag_start)
        self.macro_listbox.bind("<B1-Motion>", self.macro_drag_motion)
        self.macro_listbox.bind("<ButtonRelease-1>", self.macro_drag_end)

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        bg_color = "#f0f0f0"
        frame_bg = "#ffffff"
        fg_color = "#222222"
        accent = "#007acc"
        label_font = ("Segoe UI", 11)
        label_bold = ("Segoe UI", 11, "bold")
        entry_font = ("Segoe UI", 11)
        btn_font = ("Segoe UI", 11, "bold")

        style.configure("TFrame", background=frame_bg)
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background=bg_color, foreground=accent)
        style.configure("Section.TLabel", font=label_bold, background=frame_bg, foreground=fg_color)
        style.configure("TLabel", font=label_font, background=frame_bg, foreground=fg_color)
        style.configure("TButton",
                        font=btn_font,
                        background=accent,
                        foreground="white",
                        padding=8,
                        relief="flat")
        style.map("TButton",
                  background=[("active", accent), ("pressed", "#005a9e")])
        style.configure("TEntry", foreground=fg_color, fieldbackground="#f9f9f9", padding=6, font=entry_font)
        style.configure("TCombobox", foreground=fg_color, fieldbackground="#f9f9f9", padding=6, font=entry_font)
        style.map("TCombobox", fieldbackground=[("readonly", "#f9f9f9")])

        self.root.columnconfigure(0, weight=1, uniform="a")
        self.root.columnconfigure(1, weight=0)
        self.root.columnconfigure(2, weight=2, uniform="a")
        self.root.rowconfigure(0, weight=1)

        profile_frame = ttk.Frame(self.root, style="TFrame", padding=15)
        profile_frame.grid(row=0, column=0, sticky="nsew", padx=(20,10), pady=20)
        profile_frame.columnconfigure(0, weight=1)
        profile_frame.rowconfigure(2, weight=1)

        ttk.Label(profile_frame, text="Profiles", style="Header.TLabel").grid(row=0, column=0, sticky="w")

        profile_list_frame = ttk.Frame(profile_frame, style="TFrame")
        profile_list_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        profile_list_frame.columnconfigure(0, weight=1)
        profile_list_frame.rowconfigure(0, weight=1)

        self.profile_listbox = tk.Listbox(
            profile_list_frame,
            bg="#ffffff", fg=fg_color,
            font=label_font,
            selectbackground=accent,
            selectforeground="#fff",
            relief="flat",
            activestyle="none",
            highlightthickness=1,
            highlightcolor=accent,
            highlightbackground="#ccc",
            borderwidth=0)
        self.profile_listbox.grid(row=0, column=0, sticky="nsew")
        self.profile_listbox.bind("<<ListboxSelect>>", self.on_profile_select)

        profile_scroll = ttk.Scrollbar(profile_list_frame, orient="vertical", command=self.profile_listbox.yview)
        profile_scroll.grid(row=0, column=1, sticky="ns")
        self.profile_listbox.config(yscrollcommand=profile_scroll.set)

        self.profile_meta_label = ttk.Label(profile_frame, text="", style="TLabel", justify="left")
        self.profile_meta_label.grid(row=3, column=0, sticky="w", pady=(5,0))

        profile_btn_frame = ttk.Frame(profile_frame, style="TFrame")
        profile_btn_frame.grid(row=4, column=0, sticky="ew", pady=(10,0))
        profile_btn_frame.columnconfigure((0,1), weight=1, uniform="btns")

        self.btn_add_profile = ttk.Button(profile_btn_frame, text="Add Profile", command=self.add_profile)
        self.btn_add_profile.grid(row=0, column=0, sticky="ew", padx=(0,5))

        self.btn_remove_profile = ttk.Button(profile_btn_frame, text="Remove Profile", command=self.remove_profile)
        self.btn_remove_profile.grid(row=0, column=1, sticky="ew", padx=(5,0))

        separator = ttk.Separator(self.root, orient="vertical")
        separator.grid(row=0, column=1, sticky="ns", pady=20)

        macro_frame = ttk.Frame(self.root, style="TFrame", padding=15)
        macro_frame.grid(row=0, column=2, sticky="nsew", padx=(10,20), pady=20)
        macro_frame.columnconfigure(0, weight=1)
        macro_frame.columnconfigure(2, weight=2)
        macro_frame.rowconfigure(1, weight=1)

        ttk.Label(macro_frame, text="Macros", style="Header.TLabel").grid(row=0, column=0, sticky="w")

        macro_list_frame = ttk.Frame(macro_frame, style="TFrame")
        macro_list_frame.grid(row=1, column=0, rowspan=8, sticky="nsew", pady=10)
        macro_list_frame.columnconfigure(0, weight=1)
        macro_list_frame.rowconfigure(0, weight=1)

        self.macro_listbox = tk.Listbox(
            macro_list_frame,
            bg="#ffffff", fg=fg_color,
            font=label_font,
            selectbackground=accent,
            selectforeground="#fff",
            relief="flat",
            activestyle="none",
            highlightthickness=1,
            highlightcolor=accent,
            highlightbackground="#ccc",
            borderwidth=0)
        self.macro_listbox.grid(row=0, column=0, sticky="nsew")
        self.macro_listbox.bind("<<ListboxSelect>>", self.on_macro_select)

        macro_scroll = ttk.Scrollbar(macro_list_frame, orient="vertical", command=self.macro_listbox.yview)
        macro_scroll.grid(row=0, column=1, sticky="ns")
        self.macro_listbox.config(yscrollcommand=macro_scroll.set)

        macro_btn_frame = ttk.Frame(macro_frame, style="TFrame")
        macro_btn_frame.grid(row=9, column=0, sticky="ew", pady=(10,0))
        macro_btn_frame.columnconfigure((0,1), weight=1, uniform="btns")

        self.btn_add_macro = ttk.Button(macro_btn_frame, text="Add Macro", command=self.add_macro)
        self.btn_add_macro.grid(row=0, column=0, sticky="ew", padx=(0,5))

        self.btn_remove_macro = ttk.Button(macro_btn_frame, text="Remove Macro", command=self.remove_macro)
        self.btn_remove_macro.grid(row=0, column=1, sticky="ew", padx=(5,0))

        detail_frame = ttk.Frame(macro_frame, style="TFrame", padding=15)
        detail_frame.grid(row=1, column=2, rowspan=9, sticky="nsew", padx=(20,0))
        detail_frame.columnconfigure(1, weight=1)

        labels = ["Name", "Key", "Modifier", "Type", "Key/Button"]
        self.fields = {}
        self.field_labels = {}

        for i, label in enumerate(labels):
            label_widget = ttk.Label(detail_frame, text=label + ":", style="Section.TLabel")
            label_widget.grid(row=i, column=0, sticky="e", pady=8, padx=(0, 15))
            self.field_labels[label.lower()] = label_widget
            
            if label == "Type":
                combo = ttk.Combobox(
                    detail_frame,
                    values=["keyboard_press", "click_loop", "function"],
                    state="readonly",
                    width=25,
                    font=label_font
                )
                combo.grid(row=i, column=1, sticky="ew", pady=8)
                combo.bind("<<ComboboxSelected>>", lambda e: self.update_type_fields())
                self.fields["type"] = combo
            else:
                if label == "Key/Button":
                    self.key_button_entry = ttk.Entry(detail_frame, width=27, font=label_font)
                    self.key_button_entry.grid(row=i, column=1, sticky="ew", pady=8)

                    self.click_loop_dropdown = ttk.Combobox(
                        detail_frame,
                        values=["left click", "right click"],
                        state="readonly",
                        width=25,
                        font=label_font
                    )
                    self.click_loop_dropdown.grid(row=i, column=1, sticky="ew", pady=8)
                    self.click_loop_dropdown.grid_remove()

                    self.fields["key/button"] = self.key_button_entry
                else:
                    entry = ttk.Entry(detail_frame, width=30, font=label_font)
                    entry.grid(row=i, column=1, sticky="ew", pady=8)
                    self.fields[label.lower()] = entry

        self.filepath_label = ttk.Label(detail_frame, text="File Path:", style="Section.TLabel")
        self.filepath_entry = ttk.Entry(detail_frame, width=30, font=label_font)

        self.Interval_row = len(labels)
        self.Interval_label = ttk.Label(detail_frame, text="Interval:", style="Section.TLabel")
        self.Interval_label.grid(row=self.Interval_row, column=0, sticky="e", pady=8, padx=(0, 15))
        self.Interval_entry = ttk.Entry(detail_frame, width=30, font=label_font)
        self.Interval_entry.grid(row=self.Interval_row, column=1, sticky="ew", pady=8)

        self.func_label = ttk.Label(detail_frame, text="Function Name:", style="Section.TLabel")
        self.func_entry = ttk.Entry(detail_frame, width=30, font=label_font)

        self.func_dropdown = ttk.Combobox(
            detail_frame,
            values=self.get_function_files(),
            state="readonly",
            width=27,
            font=label_font
        )

        self.run_once_var = tk.BooleanVar()
        self.toggle_var = tk.BooleanVar()

        self.run_once_checkbox = ttk.Checkbutton(
            detail_frame,
            text="Run Once",
            variable=self.run_once_var,
            style="TCheckbutton"
        )
        self.run_once_checkbox.grid(row=self.Interval_row + 1, column=0, pady=(15, 20), sticky="w")

        self.toggle_checkbox = ttk.Checkbutton(
            detail_frame,
            text="Toggle",
            variable=self.toggle_var,
            style="TCheckbutton"
        )
        self.toggle_checkbox.grid(row=self.Interval_row + 1, column=1, pady=(15, 20), sticky="w")

        self.save_button = ttk.Button(detail_frame, text="Save Macro", command=self.save_macro)

        self.save_profile_button = ttk.Button(detail_frame, text="Save Profile", command=self.save_profile_filepath)
        
        self.function_button = tk.Button(
            self.root,
            text="⚙️",
            command=self.open_function_editor,
            font=("Segoe UI", 12),
            bd=0,
            highlightthickness=0,
            bg=self.root["bg"],
            activebackground=self.root["bg"],
            relief="flat"
        )
        self.function_button.place(x=5, y=5)

        # Store main UI widgets for state preservation
        self.main_ui_widgets = [
            profile_frame, separator, macro_frame, self.function_button
        ]
        self.current_view = "main"

    def update_type_fields(self):
        t = self.fields["type"].get()

        if t == "click_loop":
            self.run_once_checkbox.config(text="Toggle")
        else:
            self.run_once_checkbox.config(text="Run Once")

        if t == "click_loop":
            self.toggle_checkbox.grid_remove()
        else:
            self.toggle_checkbox.grid()

        if t == "function":
            self.fields["key/button"].grid_remove()
            self.Interval_label.grid_remove()
            self.Interval_entry.grid_remove()
            self.func_label.grid(row=4, column=0, sticky="e", pady=8, padx=(0, 15))
            
            # Update dropdown values in case new functions were added
            self.func_dropdown['values'] = self.get_function_files()
            self.func_dropdown.grid(row=4, column=1, sticky="ew", pady=8)
            self.func_entry.grid_remove()
        else:
            self.func_label.grid_remove()
            self.func_entry.grid_remove()
            self.func_dropdown.grid_remove()

            if t == "click_loop":
                self.key_button_entry.grid_remove()
                self.click_loop_dropdown.grid(row=4, column=1, sticky="ew", pady=8)
                self.fields["key/button"] = self.click_loop_dropdown
            else:
                self.click_loop_dropdown.grid_remove()
                self.key_button_entry.grid(row=4, column=1, sticky="ew", pady=8)
                self.fields["key/button"] = self.key_button_entry

            self.Interval_label.grid(row=self.Interval_row, column=0, sticky="e", pady=8, padx=(0, 15))
            self.Interval_entry.grid(row=self.Interval_row, column=1, sticky="ew", pady=8)

    def refresh_profiles(self):
        self.profile_listbox.delete(0, tk.END)
        for p in self.config["profiles"]:
            self.profile_listbox.insert(tk.END, p)

        if self.selected_profile not in self.config["profiles"]:
            self.selected_profile = None
            self.profile_meta_label.config(text="")
        if not self.selected_profile and self.config["profiles"]:
            self.selected_profile = list(self.config["profiles"].keys())[0]
        if self.selected_profile:
            idx = list(self.config["profiles"].keys()).index(self.selected_profile)
            self.profile_listbox.selection_set(idx)
            self.profile_listbox.see(idx)
            self.update_profile_meta()

    def update_profile_meta(self):
        if not self.selected_profile:
            self.profile_meta_label.config(text="")
            return

    def refresh_macros(self):
        idx = self.selected_macro_index
        self.macro_listbox.delete(0, tk.END)
        if not self.selected_profile:
            return
        
        profile_data = self.config["profiles"][self.selected_profile]
        
        macros = []
        if "macros" in profile_data:
            macros = profile_data["macros"]
        else:
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    macros = data["macros"]
                    break
        
        for m in macros:
            self.macro_listbox.insert(tk.END, m["name"])
        
        if idx is not None and idx < len(macros):
            self.macro_listbox.selection_set(idx)
            self.macro_listbox.see(idx)
            self.on_macro_select(None)
        else:
            self.clear_fields()

    def clear_fields(self):
        for field in self.fields.values():
            try:
                field.delete(0, tk.END)
            except Exception:
                pass
        self.func_entry.delete(0, tk.END)
        self.func_dropdown.set("")
        self.filepath_entry.delete(0, tk.END)
        self.run_once_var.set(False)
        self.toggle_var.set(False)

    def on_profile_select(self, _):
        sel = self.profile_listbox.curselection()
        if not sel:
            return
        self.selected_profile = self.profile_listbox.get(sel[0])
        self.selected_macro_index = None
        self.update_filepath_visibility()
        self.update_profile_meta()
        self.refresh_macros()
        self.show_profile_mode()

    def on_macro_select(self, _):
        sel = self.macro_listbox.curselection()
        if not sel:
            return
        self.selected_macro_index = sel[0]
        
        profile_data = self.config["profiles"][self.selected_profile]
        
        macros = []
        if "macros" in profile_data:
            macros = profile_data["macros"]
        else:
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    macros = data["macros"]
                    break
        
        macro = macros[sel[0]]
        self.populate_fields(macro)
        self.show_macro_mode()

    def populate_fields(self, macro):
        self.fields["name"].delete(0, tk.END)
        self.fields["name"].insert(0, macro.get("name", ""))

        self.fields["key"].delete(0, tk.END)
        self.fields["key"].insert(0, macro.get("key", ""))

        self.fields["modifier"].delete(0, tk.END)
        self.fields["modifier"].insert(0, macro.get("modifier") or "")

        self.fields["type"].set(macro.get("type", "keyboard_press"))
        self.update_type_fields()

        value = macro.get("key_to_press") or macro.get("button") or ""
        if self.fields["type"].get() == "click_loop":
            self.click_loop_dropdown.set(value)
        else:
            self.key_button_entry.delete(0, tk.END)
            self.key_button_entry.insert(0, value)

        self.Interval_entry.delete(0, tk.END)
        self.Interval_entry.insert(0, str(macro.get("Interval") or ""))

        # Handle function name - set dropdown value if it's a function type
        function_name = macro.get("function_name") or ""
        if self.fields["type"].get() == "function":
            self.func_dropdown.set(function_name)
        else:
            self.func_entry.delete(0, tk.END)
            self.func_entry.insert(0, function_name)

        self.filepath_entry.delete(0, tk.END)
        profile_data = self.config["profiles"][self.selected_profile]
        if not "macros" in profile_data:
            for filepath in profile_data.keys():
                if isinstance(profile_data[filepath], dict) and "macros" in profile_data[filepath]:
                    self.filepath_entry.insert(0, filepath)
                    break

        self.run_once_var.set(macro.get("run_once", False))
        self.toggle_var.set(macro.get("toggle", False))

    def add_profile(self):
        name = simpledialog.askstring("New Profile", "Enter profile name:")
        if not name:
            return
        if name in self.config["profiles"]:
            messagebox.showerror("Error", "Profile already exists.")
            return
        
        filepath = simpledialog.askstring("File Path", "Enter executable file path (optional):")
        if filepath:
            self.config["profiles"][name] = {filepath: {"macros": []}}
        else:
            self.config["profiles"][name] = {"macros": []}
        
        self.save_config()
        self.refresh_profiles()

    def remove_profile(self):
        if not self.selected_profile:
            messagebox.showwarning("Warning", "No profile selected to delete.")
            return
        confirm = messagebox.askyesno("Confirm", f"Delete profile '{self.selected_profile}'?")
        if not confirm:
            return
        del self.config["profiles"][self.selected_profile]
        self.selected_profile = None
        self.save_config()
        self.refresh_profiles()
        self.refresh_macros()
        self.update_profile_meta()

    def add_macro(self):
        if not self.selected_profile:
            return
        
        new = {
            "name": "new_macro",
            "key": "f6",
            "type": "keyboard_press",
            "key_to_press": "a",
            "Interval": 0.001,
            "run_once": False
        }
        
        profile_data = self.config["profiles"][self.selected_profile]
        
        if "macros" in profile_data:
            profile_data["macros"].append(new)
        else:
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    data["macros"].append(new)
                    break
        
        self.save_config()
        self.refresh_macros()

    def remove_macro(self):
        sel = self.macro_listbox.curselection()
        if not self.selected_profile or not sel:
            messagebox.showwarning("Warning", "No macro selected to delete.")
            return
        confirm = messagebox.askyesno("Confirm", "Delete selected macro?")
        if not confirm:
            return
        
        profile_data = self.config["profiles"][self.selected_profile]
        
        if "macros" in profile_data:
            del profile_data["macros"][sel[0]]
        else:
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    del data["macros"][sel[0]]
                    break
        
        self.save_config()
        self.refresh_macros()

    def save_macro(self):
        if self.selected_profile is None or self.selected_macro_index is None:
            return

        profile_data = self.config["profiles"][self.selected_profile]

        macro = None
        if "macros" in profile_data:
            macro = profile_data["macros"][self.selected_macro_index]
        else:
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    macro = data["macros"][self.selected_macro_index]
                    break

        if not macro:
            return

        # Update common fields
        macro["name"] = self.fields["name"].get()
        macro["type"] = self.fields["type"].get()

        if self.selected_profile == "OnBoot":
            keys_to_remove = list(macro.keys())
            for key in keys_to_remove:
                if key not in ("name", "type", "function_name"):
                    macro.pop(key, None)
            macro["function_name"] = self.func_dropdown.get()
        else:

            macro["key"] = self.fields["key"].get()
            macro["modifier"] = self.fields["modifier"].get() or None

            for f in ("key_to_press", "button", "function_name", "interval"):
                macro.pop(f, None)

            macro["run_once"] = self.run_once_var.get()
            macro["toggle"] = self.toggle_var.get()

            macro_type = macro["type"]
            key_or_button = self.fields["key/button"].get()

            if macro_type == "function":
                macro["function_name"] = self.func_dropdown.get()
            elif macro_type == "click_loop":
                macro["key_to_press"] = key_or_button
            else:
                macro["key_to_press"] = key_or_button

            if macro_type != "function":
                val = self.Interval_entry.get()
                if val:
                    try:
                        d = float(val)
                        macro["Interval"] = d
                    except ValueError:
                        messagebox.showerror("Invalid Input", "Interval must be a number.")

        self.save_config()
        self.refresh_macros()

    def show_profile_mode(self):
        for key in ["key", "modifier", "type"]:
            self.field_labels[key].grid_remove()
            self.fields[key].grid_remove()
        
        self.field_labels["key/button"].grid_remove()
        self.key_button_entry.grid_remove()
        self.click_loop_dropdown.grid_remove()
        
        self.Interval_label.grid_remove()
        self.Interval_entry.grid_remove()
        
        self.func_label.grid_remove()
        self.func_entry.grid_remove()
        self.func_dropdown.grid_remove()
        
        self.run_once_checkbox.grid_remove()
        self.toggle_checkbox.grid_remove()
        self.save_button.grid_remove()
        
        self.field_labels["name"].grid(row=0, column=0, sticky="e", pady=8, padx=(0, 15))
        self.fields["name"].grid(row=0, column=1, sticky="ew", pady=8)

        self.save_profile_button.grid(row=2, column=1, sticky="e")
        
        self.fields["name"].delete(0, tk.END)
        self.fields["name"].insert(0, self.selected_profile)
        
        self.filepath_entry.delete(0, tk.END)
        profile_data = self.config["profiles"][self.selected_profile]
        if not "macros" in profile_data:
            for filepath in profile_data.keys():
                if isinstance(profile_data[filepath], dict) and "macros" in profile_data[filepath]:
                    self.filepath_entry.insert(0, filepath)
                    break

    def show_macro_mode(self):
        self.filepath_label.grid_remove()
        self.filepath_entry.grid_remove()
        self.save_profile_button.grid_remove()

        profile_name = self.selected_profile

        self.field_labels["name"].grid(row=0, column=0, sticky="e", pady=8, padx=(0, 15))
        self.fields["name"].grid(row=0, column=1, sticky="ew", pady=8)

        if profile_name == "OnBoot":
            self.field_labels["type"].grid_remove()
            self.fields["type"].set("function")
            self.fields["type"].configure(state="disabled")
            self.fields["type"].grid_remove()

            self.field_labels["key"].grid_remove()
            self.fields["key"].grid_remove()
            self.field_labels["modifier"].grid_remove()
            self.fields["modifier"].grid_remove()

            self.field_labels["key/button"].grid_remove()
            self.key_button_entry.grid_remove()
            self.click_loop_dropdown.grid_remove()

            self.Interval_label.grid_remove()
            self.Interval_entry.grid_remove()

            self.run_once_checkbox.grid_remove()
            self.toggle_checkbox.grid_remove()

            self.func_label.grid(row=1, column=0, sticky="e", pady=8, padx=(0, 15))
            self.func_dropdown['values'] = self.get_function_files()
            self.func_dropdown.grid(row=1, column=1, sticky="ew", pady=8)
            self.func_entry.grid_remove()

            self.save_button.grid(row=2, column=1, sticky="e")
        else:
            self.fields["type"].configure(state="readonly")

            self.field_labels["key"].grid(row=1, column=0, sticky="e", pady=8, padx=(0, 15))
            self.fields["key"].grid(row=1, column=1, sticky="ew", pady=8)

            self.field_labels["modifier"].grid(row=2, column=0, sticky="e", pady=8, padx=(0, 15))
            self.fields["modifier"].grid(row=2, column=1, sticky="ew", pady=8)

            self.field_labels["type"].grid(row=3, column=0, sticky="e", pady=8, padx=(0, 15))
            self.fields["type"].grid(row=3, column=1, sticky="ew", pady=8)

            self.field_labels["key/button"].grid(row=4, column=0, sticky="e", pady=8, padx=(0, 15))
            if self.fields["type"].get() == "click_loop":
                self.click_loop_dropdown.grid(row=4, column=1, sticky="ew", pady=8)
            elif self.fields["type"].get() == "function":
                self.func_dropdown['values'] = self.get_function_files()
                self.func_dropdown.grid(row=4, column=1, sticky="ew", pady=8)
                self.key_button_entry.grid_remove()
                self.click_loop_dropdown.grid_remove()
                self.field_labels["key/button"].config(text="Function Name:")
            else:
                self.key_button_entry.grid(row=4, column=1, sticky="ew", pady=8)
                self.field_labels["key/button"].config(text="Key/Button:")

            if self.fields["type"].get() != "function":
                self.Interval_label.grid(row=5, column=0, sticky="e", pady=8, padx=(0, 15))
                self.Interval_entry.grid(row=5, column=1, sticky="ew", pady=8)

            self.run_once_checkbox.grid(row=6, column=0, pady=(15, 20), sticky="w")

            if self.fields["type"].get() != "click_loop":
                self.toggle_checkbox.grid(row=6, column=1, pady=(15, 20), sticky="w")
            else:
                self.toggle_checkbox.grid_remove()

            self.save_button.grid(row=7, column=1, sticky="e")

    def save_profile_filepath(self):
        if not self.selected_profile:
            return
        
        new_name = self.fields["name"].get().strip()
        new_filepath = self.filepath_entry.get().strip()
        
        if new_name != self.selected_profile:
            if new_name in self.config["profiles"]:
                messagebox.showerror("Error", "Profile name already exists.")
                return
            
            self.config["profiles"][new_name] = self.config["profiles"].pop(self.selected_profile)
            self.selected_profile = new_name
        
        profile_data = self.config["profiles"][self.selected_profile]
        
        if "macros" in profile_data:
            if new_filepath:
                macros = profile_data.pop("macros")
                profile_data[new_filepath] = {"macros": macros}
        else:
            old_filepath = None
            macros = []
            for filepath, data in profile_data.items():
                if isinstance(data, dict) and "macros" in data:
                    old_filepath = filepath
                    macros = data["macros"]
                    break
            
            if old_filepath and new_filepath != old_filepath:
                if new_filepath:
                    profile_data[new_filepath] = {"macros": macros}
                    del profile_data[old_filepath]
                else:
                    profile_data["macros"] = macros
                    del profile_data[old_filepath]
        
        self.save_config()
        self.refresh_profiles()
        self.update_profile_meta()
        messagebox.showinfo("Success", "Profile updated successfully!")

    # Function page

    def open_function_editor(self):
        # Hide main UI widgets instead of destroying them
        for widget in self.main_ui_widgets:
            widget.grid_remove()
            widget.place_forget()

        self.current_view = "function_editor"

        # Reset column/row configuration for function editor
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)

        editor_frame = ttk.Frame(self.root, padding=15)
        editor_frame.grid(row=0, column=1, sticky="nsew")
        editor_frame.columnconfigure(0, weight=1, minsize=200)
        editor_frame.columnconfigure(1, weight=3)
        editor_frame.rowconfigure(1, weight=1)

        ttk.Label(editor_frame, text="Function Files", style="Header.TLabel").grid(row=0, column=0, sticky="w", columnspan=2, pady=(0, 10))

        self.function_listbox = tk.Listbox(editor_frame, height=20)
        self.function_listbox.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.function_listbox.bind("<<ListboxSelect>>", self.load_selected_function)

        text_frame = ttk.Frame(editor_frame)
        text_frame.grid(row=1, column=1, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)

        self.function_text = tk.Text(text_frame, wrap="none", font=("Consolas", 11))
        self.function_text.grid(row=0, column=0, sticky="nsew")

        x_scroll = ttk.Scrollbar(text_frame, orient="horizontal", command=self.function_text.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        y_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.function_text.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.function_text.config(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

        button_frame = ttk.Frame(editor_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure((0, 1, 2, 3), weight=1)

        ttk.Button(button_frame, text="⬅ Back", command=self.back_to_main_ui).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(button_frame, text="💾 Save", command=self.save_function_file).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(button_frame, text="➕ New Function", command=self.make_new_function).grid(row=0, column=2, sticky="ew", padx=(5, 0))
        ttk.Button(button_frame, text="🗑 Remove Function", command=self.delete_function_file).grid(row=0, column=3, sticky="ew", padx=(5, 0))

        # Store function editor widgets
        self.function_editor_widgets = [editor_frame]

        self.refresh_function_list()

    def update_filepath_visibility(self):
        if self.selected_profile in ["OnBoot", "Desktop"]:
            self.filepath_label.grid_remove()
            self.filepath_entry.grid_remove()
        else:
            self.filepath_label.grid(row=1, column=0, sticky="e", pady=8, padx=(0, 15))
            self.filepath_entry.grid(row=1, column=1, sticky="ew", pady=8)

    def refresh_function_list(self):
        self.function_listbox.delete(0, tk.END)
        
        for file in os.listdir(user_functions_dir):
            if file.endswith(".py"):
                self.function_listbox.insert(tk.END, file)

    def load_selected_function(self, _):
        sel = self.function_listbox.curselection()
        if not sel:
            return
        filename = self.function_listbox.get(sel[0])
        
        with open(os.path.join(user_functions_dir, filename), "r") as f:
            content = f.read()
        
        self.function_text.delete("1.0", tk.END)
        self.function_text.insert(tk.END, content)
        self.current_function_file = filename

    def save_function_file(self):
        if not hasattr(self, "current_function_file"):
            messagebox.showerror("Error", "No file selected.")
            return
        content = self.function_text.get("1.0", tk.END)

        # Save the content to the selected file
        with open(os.path.join(user_functions_dir, self.current_function_file), "w") as f:
            f.write(content)
        
        messagebox.showinfo("Saved", f"{self.current_function_file} saved!")

    def delete_function_file(self):
        sel = self.function_listbox.curselection()
        if not sel:
            messagebox.showerror("Error", "No function selected.")
            return

        filename = self.function_listbox.get(sel[0])
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{filename}'?")
        if not confirm:
            return
        
        filepath = os.path.join(user_functions_dir, filename)
        try:
            os.remove(filepath)
            self.refresh_function_list()
            self.function_text.delete("1.0", tk.END)
            if hasattr(self, "current_function_file"):
                del self.current_function_file
            messagebox.showinfo("Deleted", f"'{filename}' has been removed.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete file:\n{e}")

    def make_new_function(self):
        name = simpledialog.askstring("Function Name", "Enter function name:")
        if not name:
            return
        filename = f"{name}.py"
        
        path = os.path.join(user_functions_dir, filename)
        if os.path.exists(path):
            messagebox.showerror("Error", "That file already exists.")
            return
        with open(path, "w") as f:
            f.write(f"print(\"{name}\")\n")
        
        self.refresh_function_list()
        self.function_listbox.select_set(tk.END)
        self.function_listbox.event_generate("<<ListboxSelect>>")

    def back_to_main_ui(self):
        # Hide function editor widgets
        for widget in self.function_editor_widgets:
            widget.grid_remove()
            widget.place_forget()

        self.current_view = "main"

        self.root.columnconfigure(0, weight=1, uniform="a")
        self.root.columnconfigure(1, weight=0)
        self.root.columnconfigure(2, weight=2, uniform="a")
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

        for widget in self.main_ui_widgets:
            if hasattr(widget, 'grid_info') and widget.grid_info():
                # Widget was previously gridded, restore it
                pass  # It should already be visible
            elif widget == self.main_ui_widgets[0]:  # profile_frame
                widget.grid(row=0, column=0, sticky="nsew", padx=(20,10), pady=20)
            elif widget == self.main_ui_widgets[1]:  # separator
                widget.grid(row=0, column=1, sticky="ns", pady=20)
            elif widget == self.main_ui_widgets[2]:  # macro_frame
                widget.grid(row=0, column=2, sticky="nsew", padx=(10,20), pady=20)
            elif widget == self.main_ui_widgets[3]:  # function_button
                widget.place(x=5, y=5)

        self.function_editor_widgets = []

        if self.selected_profile:
            profile_names = list(self.config["profiles"].keys())
            if self.selected_profile in profile_names:
                idx = profile_names.index(self.selected_profile)
                self.profile_listbox.selection_set(idx)
                self.profile_listbox.see(idx)
            
            self.refresh_macros()
            
            if self.selected_macro_index is not None:
                self.show_macro_mode()
            else:
                self.show_profile_mode()

def run():
    root = tk.Tk()
    app = MacroEditor(root)
    root.mainloop()