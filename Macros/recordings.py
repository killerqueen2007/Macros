"""Recorded macros saved by the recorder (user_recd_mac/*.json).
The file format lives here, shared by the recorder window and the macro runner."""
import json
import os

from config import RECORDINGS_DIR

STEP_TYPES = ("down", "up", "wait")


def list_recording_names():
    """Names (without .json) of every saved recording."""
    return sorted(f[:-5] for f in os.listdir(RECORDINGS_DIR) if f.endswith(".json"))


def filename_for(name):
    """`name` made safe to use as a file name ('' if nothing usable is left)."""
    return "".join(c for c in name if c not in '<>:"/\\|?*').strip(" .")


def _path(stem):
    return os.path.join(RECORDINGS_DIR, f"{stem}.json")


def exists(stem):
    return os.path.isfile(_path(stem))


def read(stem):
    """(display name, steps) of a saved recording. Raises ValueError if it is missing or not a valid recording.
    Steps are [{"key", "type": down|up|wait, "delay"}]; delay = seconds since the previous step."""
    if not stem or any(c in stem for c in "/\\:"):
        raise ValueError("bad recording name")
    try:
        with open(_path(stem), encoding="utf-8") as f:
            data = json.load(f)
        name = ""
        if isinstance(data, dict):                # {"name": ..., "events": [...]}
            payload = data.get("data", data)      # also accepts the old macro_rec wrapper
            name = str(payload.get("name", ""))
            data = payload["events"] if "events" in payload else payload["key_to_press"]
        steps = [{"key": str(d.get("key_to_press", d.get("key", ""))), "type": d["type"],
                  "delay": float(d["delay"])} for d in data]
    except (OSError, KeyError, TypeError, AttributeError) as e:
        raise ValueError(str(e)) from e
    if any(s["type"] not in STEP_TYPES or s["delay"] < 0 or (s["type"] != "wait" and not s["key"]) for s in steps):
        raise ValueError("invalid step")
    return name, steps


def load_events(stem):
    """Just the steps, or None if the recording is missing/invalid (used by the macro runner)."""
    try:
        return read(stem)[1]
    except ValueError:
        return None


def save(name, events):
    """Write events ({key, type, delay} dicts) to user_recd_mac/<name>.json and return the file stem."""
    stem = filename_for(name)
    if not stem:
        raise ValueError("That name can't be used as a file name.")
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    steps = [{"key_to_press": e["key"], "type": e["type"], "delay": e["delay"]} for e in events]
    with open(_path(stem), "w", encoding="utf-8") as f:
        json.dump({"name": name, "events": steps}, f, indent=2)
    return stem
