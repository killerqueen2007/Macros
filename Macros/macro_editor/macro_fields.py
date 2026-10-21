"""The macro form, as data.

To add a field or checkbox to the editor: add ONE Field(...) line to FIELDS.
  id         unique widget id
  label      text, or a function(ctx) -> text (ctx.mode / .onboot / .type / .exe_allowed)
  kind       "entry" (default), "combo" or "check"
  values     combo choices: a list, or a function returning one
  show       function(ctx) -> bool, when the row is visible
  cfg        config.json key if it differs from id
  conv       text -> value (raise ValueError for bad input)
  omit_blank leave the key out of config.json when the box is empty
Hidden fields are removed from the macro on save, so switching Type cleans up after itself.
"""
from dataclasses import dataclass
from typing import Any, Callable

from user_functions import list_function_names

TYPES = ("keyboard_press", "click_loop", "function")
CLICKS = ("left click", "right click")

strip = str.strip


@dataclass(frozen=True)
class Field:
    id: str
    label: Any
    kind: str = "entry"
    values: Any = ()
    show: Callable = lambda c: True
    cfg: str = None
    conv: Callable = None
    omit_blank: bool = False

    @property
    def key(self):
        return self.cfg or self.id


def _macro(c):
    return c.mode == "macro" and not c.onboot


FIELDS = (
    Field("name", "Name", show=lambda c: c.mode in ("profile", "macro"), conv=strip),
    Field("exe", "Executable", show=lambda c: c.mode == "profile" and c.exe_allowed, conv=strip),
    Field("key", "Key", show=_macro, conv=strip),
    Field("modifier", "Modifier", show=_macro, conv=lambda s: s.strip() or None),
    Field("type", "Type", "combo", TYPES, show=_macro),
    Field("key_to_press", "Key/Button", show=lambda c: _macro(c) and c.type == "keyboard_press", conv=strip),
    Field("button", "Button", "combo", CLICKS, show=lambda c: _macro(c) and c.type == "click_loop", cfg="key_to_press"),
    Field("function_name", "Function Name", "combo", list_function_names,
          show=lambda c: c.mode == "macro" and (c.onboot or c.type == "function")),
    Field("Interval", "Interval", show=_macro, conv=float, omit_blank=True),
    Field("run_once", lambda c: "Toggle" if c.type == "click_loop" else "Run Once", "check", show=_macro),
    Field("toggle", "Toggle", "check", show=lambda c: _macro(c) and c.type != "click_loop"),
    Field("suppress", "Suppress", "check", show=_macro),
)

# every config key the form owns (+ old spellings), used to clean up on save
KNOWN_KEYS = {f.key for f in FIELDS} | {"interval", "button"}
