import os
import sys
import json
import time
import math
import threading
import subprocess
import platform
import keyboard
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw, ImageColor

from macros import DynamicMacroRunner
from window_utils import get_foreground_process
import macro_editor

# Detect OS
OS_TYPE = platform.system()

# Windows-specific imports
if OS_TYPE == "Windows":
    try:
        import ctypes
        WINDOWS_LIBS_AVAILABLE = True
        # Windows constants
        WM_CLOSE = 0x0010
        SW_HIDE = 0
        SW_SHOW = 5
    except ImportError:
        print("[Warning] ctypes not available on Windows")
        WINDOWS_LIBS_AVAILABLE = False

class TrayApp:
    def __init__(self):
        self.exit_event = threading.Event()
        self.last_window_info = ""
        self.tray_icon = None
        self.macro_thread = None
        self.cached_icon = None
        self.create_macros()
        self.macro_editor_thread = None
        
        # Windows-specific console window handling
        if OS_TYPE == "Windows" and WINDOWS_LIBS_AVAILABLE:
            self.console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            ctypes.windll.kernel32.SetConsoleTitleW("Macro")
            self.console_visible = True
            ctypes.windll.user32.ShowWindow(self.console_hwnd, SW_HIDE)
            self.console_visible = False
        else:
            self.console_hwnd = None
            self.console_visible = False

    def create_macros(self):
        self.macros = {}
        config_path = "config.json"
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)

            for profile_name, profile_data in config_data["profiles"].items():
                if profile_name == "Desktop":
                    continue  # Desktop is fallback, no exe keys here

                for exe_name in profile_data:
                    runner = DynamicMacroRunner(profile_name, exe_name=exe_name, config_path=config_path)
                    self.macros[exe_name] = runner

            if "Desktop" in config_data["profiles"]:
                self.desktop_macro = DynamicMacroRunner("Desktop", config_path=config_path)
            else:
                self.desktop_macro = DynamicMacroRunner("Desktop", config_path=config_path)

        except Exception as e:
            print(f"[Error] create_macros dynamic load: {e}")
            self.macros = {}
            self.desktop_macro = DynamicMacroRunner("Desktop", config_path=config_path)

    def draw_icon(self):
        if self.cached_icon:
            return self.cached_icon

        try:
            size = 64
            img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            center = (size // 2, size // 2)
            radius = size // 2 - 4
            for i in range(360):
                angle = i
                color = tuple(int(c) for c in ImageColor.getrgb(f"hsl({angle}, 100%, 50%)"))
                x = center[0] + radius * math.cos(math.radians(angle))
                y = center[1] + radius * math.sin(math.radians(angle))
                draw.line([center, (x, y)], fill=color, width=3)
            draw.ellipse(
                (center[0] - radius + 6, center[1] - radius + 6, center[0] + radius - 6, center[1] + radius - 6),
                fill=(255, 255, 255, 255)
            )
            self.cached_icon = img
            return img
        except Exception as e:
            print(f"[Error] draw_icon: {e}")
            self.cached_icon = Image.new('RGBA', (64, 64), (255, 0, 0, 255))
            return self.cached_icon

    def loop(self):
        while not self.exit_event.is_set():
            try:
                window_title, proc_name = get_foreground_process()
                if window_title == "Unknown" or proc_name == "Unknown":
                    time.sleep(0.01)
                    continue

                info = f"Focused Window: {window_title} | Process: {proc_name}"
                if info != self.last_window_info:
                    self.last_window_info = info
                    print(info)

                macro_class = self.macros.get(proc_name, self.desktop_macro)
                macro_class.run_macro_if_needed()

                # Mouse info hotkey - platform specific
                if keyboard.is_pressed("ctrl+alt+m"):
                    try:
                        if OS_TYPE == "Windows":
                            # Windows: Use pyautogui mouseInfo
                            subprocess.Popen(
                                ["pythonw", "-c", "import pyautogui; pyautogui.mouseInfo()"],
                                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                            )
                        else:
                            # Linux: Use xdotool
                            result = subprocess.run(
                                ['xdotool', 'getmouselocation', '--shell'],
                                capture_output=True,
                                text=True,
                                timeout=1
                            )
                            if result.returncode == 0:
                                print(f"[Mouse Info]\n{result.stdout}")
                                # Try to show notification
                                try:
                                    subprocess.Popen(
                                        ['notify-send', 'Mouse Info', result.stdout],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL
                                    )
                                except FileNotFoundError:
                                    pass  # notify-send not available
                    except Exception as e:
                        print(f"[Error] launching mouseInfo: {e}")
                    time.sleep(0.5)

                time.sleep(0.001)
            except Exception as e:
                print(f"[Error] loop cycle: {e}")
                time.sleep(0.01)

    def open_macro_editor(self):
        # If thread exists and is alive, don't open another
        if self.macro_editor_thread and self.macro_editor_thread.is_alive():
            print("Macro editor is already open.")
            return

        def run_editor():
            macro_editor.run()

        self.macro_editor_thread = threading.Thread(target=run_editor, daemon=True)
        self.macro_editor_thread.start()

    def toggle_console_window(self, icon, item=None):
        if OS_TYPE == "Windows" and self.console_hwnd and WINDOWS_LIBS_AVAILABLE:
            # Windows implementation
            if self.console_visible:
                ctypes.windll.user32.ShowWindow(self.console_hwnd, SW_HIDE)
                self.console_visible = False
            else:
                ctypes.windll.user32.ShowWindow(self.console_hwnd, SW_SHOW)
                self.console_visible = True
        else:
            # Linux implementation - just print info
            print("[Info] Console toggle: Not applicable on this platform")
            print("[Info] Console is running in the current terminal")

    def on_open_location(self, icon, item):
        try:
            folder = os.path.dirname(os.path.abspath(sys.argv[0]))
            
            if OS_TYPE == "Windows":
                os.startfile(folder)
            elif OS_TYPE == "Linux":
                subprocess.Popen(['xdg-open', folder])
            elif OS_TYPE == "Darwin":  # macOS
                subprocess.Popen(['open', folder])
            else:
                print(f"[Info] Application folder: {folder}")
                
        except Exception as e:
            print(f"[Error] open_location: {e}")

    def restart_script(self, icon, item):
        try:
            print("Restarting the script...")
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            print(f"[Error] restart_script: {e}")

    def on_quit(self, icon, item):
        self.exit_event.set()
        try:
            icon.stop()
        except Exception as e:
            print(f"[Error] tray icon stop: {e}")
        
        # Windows-specific cleanup
        if OS_TYPE == "Windows" and self.console_hwnd and WINDOWS_LIBS_AVAILABLE:
            ctypes.windll.user32.PostMessageW(self.console_hwnd, WM_CLOSE, 0, 0)
        
        sys.exit(0)

    def start_loop(self):
        try:
            self.macro_thread = threading.Thread(target=self.loop, daemon=True)
            self.macro_thread.start()
        except Exception as e:
            print(f"[Error] start_loop: {e}")

    def start(self):
        self.start_loop()
        try:
            # Try to load the icon from Macro.ico file, fallback to generated icon
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Macro.ico")
            
            if os.path.exists(icon_path):
                try:
                    icon_image = Image.open(icon_path)
                    try:
                        icon_image = icon_image.resize((64, 64), Image.LANCZOS)  # type: ignore
                    except Exception:
                        pass
                except Exception as e:
                    print(f"[Warning] Could not load Macro.ico: {e}, using generated icon")
                    icon_image = self.draw_icon()
            else:
                print("[Info] Macro.ico not found, using generated icon")
                icon_image = self.draw_icon()

            self.tray_icon = Icon(
                "Macro Tray",
                icon=icon_image,
                title="Macro Tray Controller",
                menu=Menu(
                    MenuItem("Macro Editor", self.open_macro_editor, default=True),
                    MenuItem("Toggle Console", self.toggle_console_window),
                    MenuItem("Show Location", self.on_open_location),
                    MenuItem("Restart", self.restart_script),
                    MenuItem("Quit", self.on_quit)
                )
            )

            print(f"[Info] Starting system tray icon on {OS_TYPE}...")
            self.tray_icon.run()
        except Exception as e:
            print(f"[Error] tray_icon run: {e}")
        finally:
            self.exit_event.set()
