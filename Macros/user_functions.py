"""Runs scripts from the user_functions folder in the background."""
import os
import subprocess
import sys
import threading

from config import USER_FUNCTIONS_DIR


def run_function_by_name(name):
    script_path = os.path.join(USER_FUNCTIONS_DIR, f"{name}.py")
    if not os.path.isfile(script_path):
        print(f"[Error] Script file not found: {script_path}")
        return

    def run_script():
        try:
            subprocess.run([sys.executable, script_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[Error] Script '{name}.py' exited with error: {e}")

    threading.Thread(target=run_script, daemon=True).start()


def list_function_names():
    """Names (without .py) of every script in the user_functions folder."""
    return sorted(f[:-3] for f in os.listdir(USER_FUNCTIONS_DIR) if f.endswith(".py"))
