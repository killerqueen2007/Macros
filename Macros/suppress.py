"""Hides a macro's trigger key from the focused program ("Suppress" checkbox in the editor).
Modifiers are not hidden: for "ctrl+a" the program still sees ctrl go down, but never the "a".
"""
import keyboard


class KeySuppressor:
    def __init__(self):
        self.active = None
        self._rules = {}
        self._hooks = {}
        self._blocked = set()

    def set_rules(self, owner, rules):
        """rules: [(key, modifiers)] for the owner's macros that have suppress turned on."""
        parsed = []
        for key, mods in rules:
            try:
                codes = frozenset(keyboard.key_to_scan_codes(key, error_if_missing=False))
            except ValueError:
                codes = frozenset()
            if codes:
                parsed.append((key, codes, mods))
            else:
                print(f"[Warning] Can't suppress unknown key '{key}'.")
        self._rules[owner] = parsed
        self._sync_hooks()

    def _sync_hooks(self):
        wanted = {key for rules in self._rules.values() for key, _, _ in rules}
        for key in set(self._hooks) - wanted:
            self._hooks.pop(key)()
            self._blocked.clear()
        for key in wanted - set(self._hooks):
            try:
                self._hooks[key] = keyboard.hook_key(key, lambda e: self._on_event(e), suppress=True)
            except ValueError:
                print(f"[Warning] Can't suppress unknown key '{key}'.")

    def _matches(self, code):
        for _, codes, mods in self._rules.get(self.active, ()):
            if code in codes and all(keyboard.is_pressed(m) for m in mods):
                return True
        return False

    def _on_event(self, event):
        """Called for every event of a hooked key. Return True to let it through, False to block it."""
        code = event.scan_code
        if event.event_type == keyboard.KEY_UP:
            if code in self._blocked:
                self._blocked.discard(code)
                return False
            return True
        if code in self._blocked or self._matches(code):
            self._blocked.add(code)
            return False
        return True


suppressor = KeySuppressor()
