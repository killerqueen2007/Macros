"""System tray app: watches the foreground window and drives the matching macro profile."""
import os
import subprocess
import sys
import threading
import time

import keyboard
from pystray import Icon, Menu, MenuItem

import macro_editor
from config import BASE_DIR, CONFIG_PATH, load_config
from console import ConsoleWindow
from icon import load_icon
from macros import DynamicMacroRunner
from hotkeys import open_mouse_info
from suppress import suppressor
from window_utils import get_foreground_process

# Profiles that are not keyed by name.
NON_EXE_PROFILES = ("OnBoot", "Desktop")
MOUSE_INFO_HOTKEY = "ctrl+shift+alt+m"


class TrayApp:
    
    
    def __init__(self):
        self.exit_event = threading.Event()
        self.force_recheck = False
        self.last_window_info = ""
        self.active_runner = None
        self.macro_editor_thread = None

        self.console = ConsoleWindow()
        self.runners = {}
        self.desktop_runner = None
        self._load_runners()

        keyboard.add_hotkey(MOUSE_INFO_HOTKEY, open_mouse_info, suppress=False)

    # --- setup ------------------------------------------------------------
    def _load_runners(self):
        try:
            config = load_config()
            for profile_name, profile in config.get("profiles", {}).items():
                if profile_name in NON_EXE_PROFILES:
                    continue
                for exe_name in profile:
                    self.runners[exe_name] = DynamicMacroRunner(profile_name, exe_name=exe_name, config_path=CONFIG_PATH)

            force_bind = config.get("global", {}).get("force_recheck_key")
            if force_bind:
                try:
                    keyboard.add_hotkey(force_bind, self.trigger_force_recheck)
                    print(f"[Info] Force recheck bound to: {force_bind}")
                except Exception as e:
                    print(f"[Warning] Could not bind force recheck key '{force_bind}': {e}")
        except Exception as e:
            print(f"[Error] loading macro profiles: {e}")
            self.runners = {}

        self.desktop_runner = DynamicMacroRunner("Desktop", config_path=CONFIG_PATH)

    def trigger_force_recheck(self):
        # Only sets a flag; the main loop does the actual work (keeps all macro state on one thread).
        self.force_recheck = True
        print("[Info] Force foreground recheck triggered.")

    def stop_all_macros(self):
        """Stop every running click loop / toggled macro in every profile."""
        for runner in (*self.runners.values(), self.desktop_runner):
            runner.stop_all()
        print("[Info] All active macros stopped.")

    # --- main loop --------------------------------------------------------
    def loop(self):
        while not self.exit_event.is_set():
            try:
                if self.force_recheck:
                    self.force_recheck = False
                    self.last_window_info = ""
                    self.stop_all_macros()
                    print("[Info] Rechecking foreground window...")

                window_title, proc_name = get_foreground_process()
                if window_title == "Unknown" or proc_name == "Unknown":
                    time.sleep(0.01)
                    continue

                info = f"Focused Window: {window_title} | Process: {proc_name}"
                if info != self.last_window_info:
                    self.last_window_info = info
                    print(info)

                runner = self.runners.get(proc_name, self.desktop_runner)

                # Focus moved to a different profile: stop anything the old one left running.
                if runner is not self.active_runner:
                    if self.active_runner:
                        self.active_runner.stop_all()
                    self.active_runner = runner
                    suppressor.active = runner

                runner.run_macro_if_needed()
                time.sleep(runner.loop_delay)

            except Exception as e:
                print(f"[Error] loop cycle: {e}")
                time.sleep(0.01)

    # --- tray menu actions ------------------------------------------------
    def open_macro_editor(self, icon=None, item=None):
        if self.macro_editor_thread and self.macro_editor_thread.is_alive():
            print("Macro editor is already open.")
            return
        self.macro_editor_thread = threading.Thread(target=macro_editor.run, daemon=True)
        self.macro_editor_thread.start()

    def toggle_console_window(self, icon, item=None):
        self.console.toggle()

    def on_open_location(self, icon, item):
        try:
            os.startfile(BASE_DIR)
        except Exception as e:
            print(f"[Error] open_location: {e}")

    def restart_script(self, icon, item):
        try:
            print("Restarting the script...")
            subprocess.Popen([sys.executable, *sys.argv])
            self.exit_event.set()
            icon.stop()
            os._exit(0)
        except Exception as e:
            print(f"[Error] restart_script: {e}")

    def on_quit(self, icon, item):
        self.exit_event.set()
        try:
            icon.stop()
        except Exception as e:
            print(f"[Error] tray icon stop: {e}")
        self.console.close()
        sys.exit(0)

    # --- entry point ------------------------------------------------------
    def start(self):
        threading.Thread(target=self.loop, daemon=True).start()
        try:
            tray_icon = Icon(
                "Macro Tray",
                icon=load_icon(),
                title="Macro Tray Controller",
                menu=Menu(
                    MenuItem("Macro Editor", self.open_macro_editor, default=True),
                    MenuItem("Toggle Console", self.toggle_console_window),
                    MenuItem("Show Location", self.on_open_location),
                    MenuItem("Restart", self.restart_script),
                    MenuItem("Quit", self.on_quit),
                ),
            )
            print("[Info] Starting system tray icon...")
            tray_icon.run()
        except Exception as e:
            print(f"[Error] tray_icon run: {e}")
        finally:
            self.exit_event.set()
