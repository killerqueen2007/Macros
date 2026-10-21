"""Foreground window / process lookup."""
import psutil
import win32gui
import win32process

_cached_pid = None
_cached_name = "Unknown"

def get_foreground_process():
    """Return (window_title, process_name); 'Unknown' for anything unavailable."""
    global _cached_pid, _cached_name
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd) or "Unknown"
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # This runs every loop tick, so only ask psutil when the pid changes.
        if pid != _cached_pid:
            try:
                _cached_name = psutil.Process(pid).name()
                _cached_pid = pid
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                _cached_pid = None
                _cached_name = "Unknown"

        return title, _cached_name
    except Exception as e:
        if "pid must be a positive integer (got -188359904)" in str(e):
            return None
        
        print(f"[Error] get_foreground_process failed: {e}")
        return "Unknown", "Unknown"
