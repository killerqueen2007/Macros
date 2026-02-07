import threading
import json
import os
import sys
import subprocess
from tray_app import TrayApp

CONFIG_PATH = "config.json"

script_dir = os.path.dirname(os.path.abspath(__file__))
user_functions_dir = os.path.join(script_dir, "user_functions")
os.makedirs(user_functions_dir, exist_ok=True)

print(f"User functions directory: {user_functions_dir}")

def load_config(path=CONFIG_PATH):
    with open(path, "r") as f:
        return json.load(f)

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

if __name__ == "__main__":
    config = load_config()

    onboot_profile = config.get("profiles", {}).get("OnBoot", {})
    macros = onboot_profile.get("macros", [])

    # Run all function type macros in OnBoot profile
    for macro in macros:
        if macro.get("type") == "function" and "function_name" in macro:
            print(f"Running OnBoot function: {macro['function_name']}")
            run_function_by_name(macro["function_name"])

    app = TrayApp()
    app.start()
