"""Macro editor window. tray_app.py does `import macro_editor; macro_editor.run()`."""


def run():
    from .macro_editor import run as _run   # imported on demand: the recorder sub-package shares this package
    _run()


__all__ = ["run"]
