"""Launches pyautogui's MouseInfo window in a separate process."""
import subprocess
import sys


def open_mouse_info():
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        exe = exe[: -len("python.exe")] + "pythonw.exe"
    try:
        subprocess.Popen(
            [exe, "-c", "import pyautogui; pyautogui.mouseInfo()"],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as e:
        print(f"[Error] launching mouseInfo: {e}")
