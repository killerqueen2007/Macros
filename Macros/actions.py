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


# keyboard-library key name -> pydirectinput name (only where they differ)
KEYMAP = {
    "left shift": "shiftleft", "right shift": "shiftright",
    "left ctrl": "ctrlleft", "right ctrl": "ctrlright",
    "left alt": "altleft", "right alt": "altright",
    "left windows": "winleft", "right windows": "winright",
    "caps lock": "capslock", "page up": "pageup", "page down": "pagedown",
    "print screen": "printscreen", "num lock": "numlock", "scroll lock": "scrolllock",
}


def play_recording(events, flag, on_step=None):
    """Replay recorded steps (key down / up / wait). 'delay' = seconds since the previous step.
    Stops as soon as flag['active'] turns False, and never leaves a key stuck down.
    on_step(i) is called as each step starts. Returns how many keys had to be skipped (bad key names)."""
    due = time.perf_counter()
    held = set()
    skipped = 0
    try:
        for i, ev in enumerate(events):
            due += ev["delay"]
            if ev["type"] == "wait" and on_step:
                on_step(i)
            while flag["active"] and (wait := due - time.perf_counter()) > 0:
                time.sleep(min(wait, 0.005))
            if not flag["active"]:
                return skipped
            if ev["type"] == "wait":
                continue
            if on_step:
                on_step(i)
            key = KEYMAP.get(ev["key"], ev["key"])
            try:
                if ev["type"] == "down":
                    pag.keyDown(key)
                    held.add(key)
                else:
                    pag.keyUp(key)
                    held.discard(key)
            except Exception as e:
                skipped += 1
                print(f"[Warning] Skipped key '{ev['key']}': {e}")
    finally:
        for key in held:
            try:
                pag.keyUp(key)
            except Exception:
                pass
    return skipped
