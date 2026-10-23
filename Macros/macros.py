"""Per-profile macro runner: polls key state and fires the configured macros."""
import os
import threading
import time

import keyboard

import actions
from config import CONFIG_PATH, load_config
from recordings import load_events
from suppress import suppressor
from user_functions import run_function_by_name

RELOAD_CHECK_INTERVAL = 1.0  # seconds between config.json change checks


def parse_modifiers(modifier):
    """'ctrl & shift' -> ('ctrl', 'shift'); None -> ()."""
    if not modifier:
        return ()
    return tuple(m.strip() for m in modifier.split("&") if m.strip())


class DynamicMacroRunner:
    def __init__(self, profile_name, exe_name=None, config_path=CONFIG_PATH):
        self.profile_name = profile_name
        self.exe_name = exe_name
        self.config_path = config_path

        self.threads = {}      # name -> Thread (hold-style one-shot macros)
        self.loop_flags = {}   # name -> {"active": bool} (click loops / toggles)
        self.triggered = {}    # name -> bool (edge detection for run_once / toggle)
        self._warned = set()   # recordings we've already reported as missing

        self.macros = []       # list of (macro_dict, modifier_tuple)
        self.global_settings = {}
        self.loop_delay = 0.01

        self._last_check = time.monotonic()
        self.last_mtime = os.path.getmtime(config_path)
        self._apply_config(load_config(config_path))

    # --- config -----------------------------------------------------------
    def _resolve_profile(self, full):
        profile = full.get("profiles", {}).get(self.profile_name)
        if self.exe_name and isinstance(profile, dict):
            profile = profile.get(self.exe_name)
        if isinstance(profile, dict) and "macros" in profile:
            return profile
        return None

    def _apply_config(self, full):
        self.global_settings = full.get("global", {})
        self.loop_delay = self.global_settings.get("loop_delay", 0.01)

        profile = self._resolve_profile(full)
        if profile is None:
            print(f"[Warning] Profile '{self.profile_name}' is invalid or missing macros. Falling back to 'Desktop'.")
            profile = full.get("profiles", {}).get("Desktop", {})

        self.macros = [(m, parse_modifiers(m.get("modifier"))) for m in profile.get("macros", [])]
        suppressor.set_rules(self, [(m["key"], mods) for m, mods in self.macros if m.get("suppress") and m.get("key")])

    def reload_config_if_updated(self):
        now = time.monotonic()
        if now - self._last_check < RELOAD_CHECK_INTERVAL:
            return
        self._last_check = now

        try:
            mtime = os.path.getmtime(self.config_path)
            if mtime == self.last_mtime:
                return
            self.last_mtime = mtime
            print("[Info] Detected config.json change; reloading profile...")

            full = load_config(self.config_path)
            self.stop_all()
            self.threads.clear()
            self.triggered.clear()
            self._apply_config(full)
        except Exception as e:
            print(f"[Error] reload_config_if_updated failed: {e}")

    # --- state helpers ----------------------------------------------------
    def stop_all(self):
        """Stop every running click loop / toggle (also used when focus leaves this profile)."""
        for flag in self.loop_flags.values():
            flag["active"] = False
        self.loop_flags.clear()

    @staticmethod
    def _spawn(target, *args):
        threading.Thread(target=target, args=args, daemon=True).start()

    def _rising_edge(self, name, pressed):
        """True once per key press (resets when released)."""
        if not pressed:
            self.triggered[name] = False
            return False
        if self.triggered.get(name):
            return False
        self.triggered[name] = True
        return True

    def _toggle(self, macro, target):
        name = macro["name"]
        flag = self.loop_flags.get(name)
        if flag and flag["active"]:
            flag["active"] = False
        else:
            flag = {"active": True}
            self.loop_flags[name] = flag
            self._spawn(target, macro, flag)

    # --- main polling -----------------------------------------------------
    def run_macro_if_needed(self):
        self.reload_config_if_updated()

        for macro, mods in self.macros:
            name = macro["name"]
            is_loop = macro["type"] == "click_loop"
            pressed = keyboard.is_pressed(macro["key"]) and all(keyboard.is_pressed(m) for m in mods)

            if macro.get("run_once", False):
                if self._rising_edge(name, pressed):
                    if is_loop:
                        self._toggle(macro, self._run_click_loop)
                    else:
                        self._spawn(self.run_macro, macro)

            elif macro.get("toggle", False) and not is_loop:
                if self._rising_edge(name, pressed):
                    self._toggle(macro, self._run_toggle_loop)

            elif pressed:
                self._hold(macro, is_loop)

            elif is_loop or macro["type"] == "recording":   # key released: cut a click loop / recording short
                flag = self.loop_flags.get(name)
                if flag:
                    flag["active"] = False

    def _hold(self, macro, is_loop):
        name = macro["name"]
        if is_loop:
            flag = self.loop_flags.get(name)
            if not flag or not flag["active"]:
                flag = {"active": True}
                self.loop_flags[name] = flag
                self._spawn(self._run_click_loop, macro, flag)
        else:
            thread = self.threads.get(name)
            if thread is None or not thread.is_alive():
                thread = threading.Thread(target=self.run_macro, args=(macro,), daemon=True)
                self.threads[name] = thread
                thread.start()

    # --- macro actions ----------------------------------------------------
    def _run_click_loop(self, macro, flag):
        button = actions.parse_button(macro.get("key_to_press", "left click"))
        actions.click_loop(flag, macro.get("Interval", 0.05), button)

    def _run_toggle_loop(self, macro, flag):
        interval = macro.get("Interval", 0.1)
        while flag["active"]:
            self.run_macro(macro, flag)
            if macro["type"] != "keyboard_press":  # keyboard_press already sleeps
                time.sleep(interval)

    def run_macro(self, macro, flag=None):
        kind = macro["type"]
        if kind == "keyboard_press":
            actions.press_key(macro["key_to_press"])
            time.sleep(macro.get("Interval", 0.05))
        elif kind == "function":
            run_function_by_name(macro["function_name"])
        elif kind == "recording":
            self._play_recording(macro, flag)
        else:
            print(f"[Error] Unknown macro type: {kind}")

    def _play_recording(self, macro, flag=None):
        name = macro.get("recording_name", "")
        events = load_events(name)
        if events is None:
            if name not in self._warned:
                self._warned.add(name)
                print(f"[Error] Recording '{name}' is missing or invalid (user_recd_mac/{name}.json).")
            return
        own = flag is None
        if own:   # run-once / hold: own flag so releasing the key or stop_all() can cut it short
            flag = {"active": True}
            self.loop_flags[macro["name"]] = flag
        try:
            actions.play_recording(events, flag)
        finally:
            if own:
                flag["active"] = False
