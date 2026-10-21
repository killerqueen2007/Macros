"""Tray icon image: Macro.ico if present, otherwise a generated colour wheel."""
import math
import os

from PIL import Image, ImageColor, ImageDraw

from config import BASE_DIR

ICON_PATH = os.path.join(BASE_DIR, "Macro.ico")
SIZE = 64


def load_icon():
    if os.path.exists(ICON_PATH):
        try:
            return Image.open(ICON_PATH).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"[Warning] Could not load Macro.ico: {e}")
    else:
        print("[Info] Macro.ico not found")