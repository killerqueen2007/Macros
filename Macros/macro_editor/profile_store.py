"""config.json access. Hides the two profile shapes:
   {"macros": [...]}   or   {"game.exe": {"macros": [...]}}"""
import json
import os

from config import CONFIG_PATH


class Store:
    def __init__(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {"global": {"loop_delay": 0.001}}
        self.config.setdefault("profiles", {})

    @property
    def profiles(self):
        return self.config["profiles"]

    def names(self):
        return list(self.profiles)

    def save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    # --- one profile ------------------------------------------------------
    def exe(self, name):
        """The exe key of a profile, or None for plain {"macros": [...]} profiles."""
        p = self.profiles[name]
        if "macros" in p:
            return None
        return next((k for k, v in p.items() if isinstance(v, dict) and "macros" in v), None)

    def macros(self, name):
        exe = self.exe(name)
        return (self.profiles[name][exe] if exe else self.profiles[name]).setdefault("macros", [])

    def set_exe(self, name, exe):
        old = self.exe(name)
        if (old or "") == exe:
            return
        p = self.profiles[name]
        macros = p.pop(old)["macros"] if old else p.pop("macros", [])
        if exe:
            p[exe] = {"macros": macros}
        else:
            p["macros"] = macros
        self.save()

    # --- all profiles -----------------------------------------------------
    def put(self, name, data):
        self.profiles[name] = data
        self.save()

    def remove(self, name):
        del self.profiles[name]
        self.save()

    def rename(self, old, new):
        self.config["profiles"] = {(new if k == old else k): v for k, v in self.profiles.items()}
        self.save()

    def move(self, start, end):
        keys = self.names()
        keys.insert(end, keys.pop(start))
        self.config["profiles"] = {k: self.profiles[k] for k in keys}
        self.save()
