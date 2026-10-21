"""Low-level input actions (pydirectinput)."""
import time

import pydirectinput as pag

pag.FAILSAFE = False
pag.PAUSE = False


def press_key(key):
    pag.press(key)


def parse_button(text):
    """'right click' -> 'right', anything else -> 'left'."""
    return "right" if "right" in (text or "").lower() else "left"


def click_loop(flag, interval, button="left"):
    """Click until flag['active'] is set to False."""
    click = pag.rightClick if button == "right" else pag.leftClick
    while flag["active"]:
        click()
        time.sleep(interval)
    flag["active"] = False
