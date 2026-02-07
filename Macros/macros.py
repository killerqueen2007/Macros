import os
import sys
import time
import json
import threading
import keyboard
import pyautogui as pag
import subprocess

pag.FAILSAFE = False
pag.PAUSE = False

script_dir = os.path.dirname(os.path.abspath(__file__))
user_functions_dir = os.path.join(script_dir, "user_functions")
os.makedirs(user_functions_dir, exist_ok=True)

# === Load Configuration Function ===
def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

# === Macro Executor Helpers ===
def run_keyboard_press(key):
    pag.press(key)

def run_click_loop(active_flag, interval, button="left"):
    
    while active_flag["active"]:
        if button == "left":
            pag.leftClick()
        elif button == "right":
            pag.rightClick()
        else:
            pag.leftClick()
        time.sleep(interval)
    active_flag["active"] = False

def run_function_by_name(name):
    script_path = os.path.join(user_functions_dir, f"{name}.py")
    if not os.path.isfile(script_path):
        print(f"[Error] Script file not found: {script_path}")
        return

    def run_script():
        try:
            subprocess.run([sys.executable, script_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[Error] Script '{name}.py' exited with error: {e}")

    threading.Thread(target=run_script, daemon=True).start()
    
# === Dynamic Macro Profile Runner ===
class DynamicMacroRunner:
    def __init__(self, profile_name, exe_name=None, config_path="config.json"):
        self.profile_name = profile_name
        self.exe_name = exe_name
        self.config_path = config_path

        self.last_mtime = os.path.getmtime(self.config_path)
        full = load_config(self.config_path)
        self.global_settings = full.get("global", {})

        profile = None

        if self.exe_name:
            profile = full["profiles"].get(self.profile_name, {})
            if isinstance(profile, dict):
                profile = profile.get(self.exe_name)
        else:
            profile = full["profiles"].get(self.profile_name)

        if not isinstance(profile, dict) or "macros" not in profile:
            if self.profile_name != "OnBoot":
                print(f"[Warning] Profile '{self.profile_name}' is invalid or missing macros. Falling back to 'Desktop'.")
            profile = full["profiles"].get("Desktop", {})

        self._apply_profile(profile)

        self.threads = {}
        self.loop_flags = {}
        self.triggered_once = {}

    def _apply_profile(self, profile):
        self.config = profile
        self.macros = profile.get("macros", [])
        self.loop_delay = self.global_settings.get("loop_delay", 0.01)

    def reload_config_if_updated(self):
        try:
            mtime = os.path.getmtime(self.config_path)
            if mtime != self.last_mtime:
                print("[Info] Detected config.json change; reloading profile...")
                self.last_mtime = mtime
                full = load_config(self.config_path)
                self.global_settings = full.get("global", {})

                if self.exe_name:
                    profile = full["profiles"].get(self.profile_name, {})
                    profile = profile.get(self.exe_name, {})
                else:
                    profile = full["profiles"].get(self.profile_name, {})

                if profile:
                    self._apply_profile(profile)
                    self.threads.clear()
                    self.loop_flags.clear()
                    self.triggered_once.clear()
                else:
                    print(f"[Warning] Profile '{self.profile_name}' not found or missing exe '{self.exe_name}' in updated config.")
        except Exception as e:
            print(f"[Error] reload_config_if_updated failed: {e}")

    def run_macro_if_needed(self):
        self.reload_config_if_updated()

        for macro in self.macros:
            key = macro["key"]
            mod = macro.get("modifier")
            name = macro["name"]
            run_once = macro.get("run_once", False)
            macro_type = macro["type"]
            toggle = macro.get("toggle", False)

            # Handle multiple modifiers by checking if all are pressed
            if mod:
                mods = mod.split("&")
                mods_pressed = all(keyboard.is_pressed(m.strip()) for m in mods)
            else:
                mods_pressed = True

            is_pressed = keyboard.is_pressed(key) and mods_pressed

            if run_once:
                if is_pressed and not self.triggered_once.get(name, False):
                    self.triggered_once[name] = True
                    if macro_type == "click_loop":
                        if name in self.loop_flags and self.loop_flags[name]["active"]:
                            self.loop_flags[name]["active"] = False
                        else:
                            self.loop_flags[name] = {"active": True}
                            threading.Thread(target=self.run_macro, args=(macro,), daemon=True).start()
                    else:
                        threading.Thread(target=self.run_macro, args=(macro,), daemon=True).start()
                elif not is_pressed:
                    self.triggered_once[name] = False
                continue

            if toggle and macro_type != "click_loop":
                if is_pressed and not self.triggered_once.get(name, False):
                    self.triggered_once[name] = True
                    if name in self.loop_flags and self.loop_flags[name].get("active"):
                        self.loop_flags[name]["active"] = False
                    else:
                        self.loop_flags[name] = {"active": True}
                        threading.Thread(target=self.run_macro_toggleable, args=(macro,), daemon=True).start()
                elif not is_pressed:
                    self.triggered_once[name] = False
                continue

            if is_pressed:
                if macro_type == "click_loop":
                    if name not in self.loop_flags or not self.loop_flags[name].get("active", False):
                        self.loop_flags[name] = {"active": True}
                        threading.Thread(target=self.run_macro, args=(macro,), daemon=True).start()
                elif name not in self.threads or not self.threads[name].is_alive():
                    self.threads[name] = threading.Thread(target=self.run_macro, args=(macro,), daemon=True)
                    self.threads[name].start()
            else:
                if macro_type == "click_loop" and name in self.loop_flags:
                    self.loop_flags[name]["active"] = False


    def run_macro(self, macro):
        t = macro["type"]
        interval = macro.get("Interval", 0.05)  # Always get interval from config.json

        if t == "keyboard_press":
            # If this is a single press, still respect interval if looped elsewhere
            run_keyboard_press(macro["key_to_press"])
            time.sleep(interval)

        elif t == "function":
            run_function_by_name(macro["function_name"])

        elif t == "click_loop":
            name = macro["name"]
            self.loop_flags[name] = {"active": True}
            button = macro.get("key_to_press", "left click").lower()
            if "left" in button:
                btn = "left"
            elif "right" in button:
                btn = "right"
            else:
                btn = "left"    

            run_click_loop(self.loop_flags[name], interval, btn)

        else:
            print(f"[Error] Unknown macro type: {t}")



    def run_macro_toggleable(self, macro):
        name = macro["name"]
        while self.loop_flags.get(name, {}).get("active", False):
            self.run_macro(macro)
            time.sleep(macro.get("interval", 0.1))
