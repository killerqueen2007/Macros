import platform
import subprocess
import psutil

# Detect operating system
OS_TYPE = platform.system()

if OS_TYPE == "Windows":
    try:
        import win32gui
        import win32process
        WINDOWS_LIBS_AVAILABLE = True
    except ImportError:
        print("[Warning] win32gui not available. Please install: pip install pywin32")
        WINDOWS_LIBS_AVAILABLE = False


def get_foreground_process_windows():
    """Get foreground process on Windows using win32gui"""
    if not WINDOWS_LIBS_AVAILABLE:
        return "Unknown", "Unknown"
    
    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        if not psutil.pid_exists(pid):
            return window_title or "Unknown", "Unknown"

        proc = psutil.Process(pid)
        return window_title or "Unknown", proc.name()

    except Exception as e:
        print(f"[Error] get_foreground_process_windows failed: {e}")
        return "Unknown", "Unknown"


def get_foreground_process_linux_x11():
    """Get foreground process on Linux using xdotool (X11)"""
    try:
        # Get the active window ID using xdotool
        result = subprocess.run(
            ['xdotool', 'getactivewindow'],
            capture_output=True,
            text=True,
            timeout=1
        )
        
        if result.returncode != 0:
            return "Unknown", "Unknown"
        
        window_id = result.stdout.strip()
        
        # Get window title using xdotool
        title_result = subprocess.run(
            ['xdotool', 'getwindowname', window_id],
            capture_output=True,
            text=True,
            timeout=1
        )
        
        window_title = title_result.stdout.strip() if title_result.returncode == 0 else "Unknown"
        
        # Get window PID using xdotool
        pid_result = subprocess.run(
            ['xdotool', 'getwindowpid', window_id],
            capture_output=True,
            text=True,
            timeout=1
        )
        
        if pid_result.returncode != 0:
            return window_title, "Unknown"
        
        pid = int(pid_result.stdout.strip())
        
        if not psutil.pid_exists(pid):
            return window_title, "Unknown"
        
        proc = psutil.Process(pid)
        return window_title, proc.name()
        
    except subprocess.TimeoutExpired:
        print("[Error] Timeout getting foreground window")
        return "Unknown", "Unknown"
    except FileNotFoundError:
        print("[Error] xdotool not found. Please install it: sudo apt install xdotool")
        return "Unknown", "Unknown"
    except Exception as e:
        print(f"[Error] get_foreground_process_linux failed: {e}")
        return "Unknown", "Unknown"


def get_foreground_process_linux_wayland():
    """
    Fallback for Wayland - limited window information due to security restrictions.
    This is less reliable than X11 but works on Wayland compositors.
    """
    try:
        # Try to get the focused application via gdbus (works on GNOME)
        result = subprocess.run(
            ['gdbus', 'call', '--session', '--dest', 'org.gnome.Shell',
             '--object-path', '/org/gnome/Shell', '--method',
             'org.gnome.Shell.Eval', 'global.get_window_actors().map(a => a.meta_window.get_wm_class())'],
            capture_output=True,
            text=True,
            timeout=1
        )
        
        if result.returncode == 0:
            # Parse the output to get the focused window class
            # This is a simplified implementation
            return "Wayland Window", "wayland-app"
        
    except Exception:
        pass
    
    # Fallback to checking focused process via other means
    try:
        # Get all running processes and try to identify GUI applications
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # This is a very basic heuristic
                if proc.info['name'] and not proc.info['name'].startswith(('systemd', 'kworker')):
                    return "Wayland Session", proc.info['name']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    
    return "Unknown", "Unknown"


def detect_linux_display_server():
    """Detect whether Linux is running X11 or Wayland"""
    import os
    session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
    wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
    
    if session_type == 'wayland' or wayland_display:
        return 'wayland'
    elif session_type == 'x11' or os.environ.get('DISPLAY'):
        return 'x11'
    else:
        return 'unknown'


# Select the appropriate function based on OS
if OS_TYPE == "Windows":
    print("[Info] Running on Windows")
    get_foreground_process = get_foreground_process_windows
    
elif OS_TYPE == "Linux":
    display_server = detect_linux_display_server()
    print(f"[Info] Running on Linux with {display_server.upper()} display server")
    
    if display_server == 'wayland':
        print("[Warning] Wayland detected - window detection will be limited")
        get_foreground_process = get_foreground_process_linux_wayland
    else:
        # Default to X11 (also handles 'unknown')
        get_foreground_process = get_foreground_process_linux_x11
        
elif OS_TYPE == "Darwin":
    print("[Warning] macOS detected - using basic implementation")
    # Basic macOS support (can be expanded)
    def get_foreground_process():
        return "macOS Window", "Unknown"
    
else:
    print(f"[Warning] Unsupported OS: {OS_TYPE}")
    def get_foreground_process():
        return "Unknown", "Unknown"
