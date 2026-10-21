"""Real system-clipboard copy/paste for macros and profiles.

Copies are JSON tagged with TAG, so you can paste them into a text editor / another PC.
Anything else on the clipboard is ignored, and pasted data is sanitised before use.
"""
import json
import tkinter as tk

from .macro_fields import KNOWN_KEYS, TYPES

TAG = "macro_editor"


def copy(root, kind, data):
    """kind: "macro" (data = macro dict) or "profile" (data = {"name": ..., "profile": ...})."""
    root.clipboard_clear()
    root.clipboard_append(json.dumps({TAG: kind, "data": data}, indent=2))
    root.update()   # make the text stick on the system clipboard


def read_macro(root):
    """A macro dict from the clipboard, or None if it isn't one. Bare macro JSON copied from config.json also works."""
    return _clean_macro(_load(root, "macro"))


def read_profile(root):
    """(name, profile) from the clipboard, or None if it isn't a copied profile."""
    data = _load(root, "profile")
    if not isinstance(data, dict) or not isinstance(data.get("name"), str):
        return None
    profile = _clean_profile(data.get("profile"))
    return (data["name"], profile) if profile is not None else None


# --- internals --------------------------------------------------------------
def _load(root, kind):
    try:
        obj = json.loads(root.clipboard_get())
    except (tk.TclError, ValueError, RecursionError):
        return None   # empty, not text, or not JSON
    if not isinstance(obj, dict):
        return None
    if obj.get(TAG) == kind:
        return obj.get("data")
    return obj if kind == "macro" and TAG not in obj else None


def _clean_macro(m):
    if not isinstance(m, dict) or m.get("type") not in TYPES or not isinstance(m.get("name"), str):
        return None
    fn = m.get("function_name", "")
    if not isinstance(fn, str) or any(c in fn for c in "/\\:"):   # no paths: it runs scripts by name
        return None
    return {k: v for k, v in m.items() if k in KNOWN_KEYS}


def _clean_list(items):
    if not isinstance(items, list):
        return None
    cleaned = [_clean_macro(m) for m in items]
    return None if None in cleaned else cleaned


def _clean_profile(p):
    if not isinstance(p, dict) or not p:
        return None
    if "macros" in p:
        macros = _clean_list(p["macros"])
        return None if macros is None else {"macros": macros}
    out = {}
    for exe, v in p.items():
        macros = _clean_list(v.get("macros")) if isinstance(v, dict) else None
        if macros is None:
            return None
        out[str(exe)] = {"macros": macros}
    return out
