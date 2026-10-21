"""Show / hide / close the console window (Windows)."""
import ctypes

SW_HIDE = 0
SW_SHOW = 5
WM_CLOSE = 0x0010


class ConsoleWindow:
    def __init__(self, title="Macro", start_hidden=True):
        self.hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.kernel32.SetConsoleTitleW(title)
        self.visible = True
        if start_hidden:
            self.hide()

    def hide(self):
        if self.hwnd:
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_HIDE)
        self.visible = False

    def show(self):
        if self.hwnd:
            ctypes.windll.user32.ShowWindow(self.hwnd, SW_SHOW)
        self.visible = True

    def toggle(self):
        self.hide() if self.visible else self.show()

    def close(self):
        if self.hwnd:
            ctypes.windll.user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
