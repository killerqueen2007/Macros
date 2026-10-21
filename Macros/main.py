from config import USER_FUNCTIONS_DIR, load_config
from tray_app import TrayApp
from user_functions import run_function_by_name


def run_onboot_functions():
    macros = load_config().get("profiles", {}).get("OnBoot", {}).get("macros", [])
    for macro in macros:
        if macro.get("type") == "function" and "function_name" in macro:
            print(f"Running OnBoot function: {macro['function_name']}")
            run_function_by_name(macro["function_name"])


if __name__ == "__main__":
    print(f"User functions directory: {USER_FUNCTIONS_DIR}")
    run_onboot_functions()
    TrayApp().start()
