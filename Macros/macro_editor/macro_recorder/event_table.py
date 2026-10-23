"""The event table: a Treeview with cell editing, drag-to-reorder and add/delete steps."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import keyboard

from .theme import ACCENT, FONT, GREEN

COLUMNS = ("#", "Key", "Action", "Delay (s)", "Time (s)", "Held (s)")
WIDTHS = (60, 160, 110, 110, 110, 110)
EDITABLE = {"#2": "key", "#3": "type", "#4": "delay"}   # tree column id -> event field


class EventTable(ttk.Frame):
    """busy() -> True while recording/playing (edits are refused); on_change() runs after every edit."""

    def __init__(self, master, busy, on_change, reserved_keys=()):
        super().__init__(master)
        self.busy, self.on_change, self.reserved = busy, on_change, set(reserved_keys)
        self.events = []        # dicts: key, type, delay, time, held
        self.editor = None      # (widget, iid, field) while a cell is being edited
        self._drag = None       # state of a row drag in progress
        self._ghost = None      # label that follows the cursor while dragging
        self._marker = None     # line showing where the dragged rows will land
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, columns=COLUMNS, show="headings", selectmode="extended")
        for c, w in zip(COLUMNS, WIDTHS):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w" if c == "Key" else "center")
        self.tree.tag_configure("down", foreground=GREEN)
        self.tree.tag_configure("up", foreground="#555555")
        self.tree.tag_configure("wait", foreground="#b45f06")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self, command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.config(yscrollcommand=scroll.set)

        self.tree.bind("<Double-1>", self._edit_cell)
        self.tree.bind("<Button-1>", self._press)
        self.tree.bind("<B1-Motion>", self._motion)
        self.tree.bind("<ButtonRelease-1>", self._release)
        self.tree.bind("<MouseWheel>", lambda e: self.cancel_edit(), add="+")
        self.tree.bind("<Delete>", lambda e: self.delete_selected())

    # --- content ------------------------------------------------------------
    def load(self, events):
        """Replace everything with `events` ({key, type, delay} dicts)."""
        self.cancel_edit()
        self.events = [{**e, "time": 0, "held": None} for e in events]
        self.recompute()
        self.refresh()

    def clear(self):
        self.cancel_edit()
        self.events.clear()
        self.refresh()

    def recompute(self):
        """Time = running total of the delays; Held = gap between a key's Down and its next Up."""
        t, downs = 0.0, {}
        for ev in self.events:
            t += ev["delay"]
            ev["time"] = round(t, 4)
            if ev["type"] == "wait":
                ev["held"] = None
            elif ev["type"] == "down":
                downs.setdefault(ev["key"], t)
                ev["held"] = None
            else:
                start = downs.pop(ev["key"], None)
                ev["held"] = round(t - start, 4) if start is not None else None

    def refresh(self, select=()):
        self.tree.delete(*self.tree.get_children())
        for ev in self.events:
            self.append_row(ev)
        keep = [str(i) for i in select if 0 <= i < len(self.events)]
        if keep:
            self.tree.selection_set(keep)
            self.tree.see(keep[0])
        self.on_change()

    def append_row(self, ev):
        arrow = {"down": "▼ Down", "up": "▲ Up", "wait": "⏱ Wait"}[ev["type"]]
        key = ev["key"] or "—"
        held = "" if ev.get("held") is None else f"{ev['held']:.3f}"
        index = len(self.tree.get_children())
        self.tree.insert("", "end", iid=str(index), tags=(ev["type"],),
                         values=(index + 1, key, arrow, f"{ev['delay']:.3f}", f"{ev['time']:.3f}", held))
        self.tree.see(str(index))

    def highlight(self, i):
        """Show which row is playing."""
        iid = str(i)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.see(iid)

    def unhighlight(self):
        self.tree.selection_remove(*self.tree.selection())

    def _selected(self):
        return sorted(int(i) for i in self.tree.selection())

    # --- add / delete -------------------------------------------------------
    def add_key(self):
        """Insert a Down + Up pair after the selected row (or at the end)."""
        if self.busy():
            return
        self.cancel_edit()
        sel = self._selected()
        at = sel[-1] + 1 if sel else len(self.events)
        self.events[at:at] = [{"key": "a", "type": "down", "delay": 0.05, "time": 0, "held": None},
                              {"key": "a", "type": "up", "delay": 0.05, "time": 0, "held": None}]
        self.recompute()
        self.refresh(select=[at, at + 1])

    def add_delay(self):
        """Insert a pure wait step after the selected row (or at the end)."""
        if self.busy():
            return
        self.cancel_edit()
        seconds = simpledialog.askfloat("Add Delay", "Delay in seconds:", initialvalue=1.0,
                                        minvalue=0.0, parent=self.winfo_toplevel())
        if seconds is None:
            return
        sel = self._selected()
        at = sel[-1] + 1 if sel else len(self.events)
        self.events.insert(at, {"key": "", "type": "wait", "delay": round(seconds, 4), "time": 0, "held": None})
        self.recompute()
        self.refresh(select=[at])

    def delete_selected(self):
        if self.busy():
            return
        self.cancel_edit()
        sel = self._selected()[::-1]
        if not sel:
            return messagebox.showwarning("Warning", "No rows selected to delete.")
        for i in sel:
            del self.events[i]
        self.recompute()
        self.refresh(select=[min(sel[-1], len(self.events) - 1)])

    # --- cell editing -------------------------------------------------------
    def _edit_cell(self, event):
        self.cancel_edit()
        if self.busy() or self.tree.identify_region(event.x, event.y) != "cell":
            return
        iid = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        field = EDITABLE.get(col)
        if not iid or not field:
            return
        x, y, w, h = self.tree.bbox(iid, col)
        ev = self.events[int(iid)]
        if field == "key" and ev["type"] == "wait":
            return   # wait rows have no key

        if field == "type":
            widget = ttk.Combobox(self.tree, values=("Down", "Up", "Wait"), state="readonly", font=FONT)
            widget.set(ev["type"].capitalize())
            widget.bind("<<ComboboxSelected>>", lambda e: self._commit_edit())
        else:
            widget = ttk.Entry(self.tree, font=FONT)
            widget.insert(0, str(ev[field]))
            widget.select_range(0, "end")
            widget.bind("<Return>", lambda e: self._commit_edit())
            widget.bind("<FocusOut>", lambda e: self._commit_edit())
        widget.bind("<Escape>", lambda e: self.cancel_edit())
        widget.place(x=x, y=y, width=w, height=h)
        widget.focus_set()
        self.editor = (widget, iid, field)

    def cancel_edit(self):
        if self.editor:
            widget = self.editor[0]
            self.editor = None
            widget.destroy()

    def _commit_edit(self):
        if not self.editor:
            return
        widget, iid, field = self.editor
        value = widget.get().strip()
        self.editor = None
        widget.destroy()

        idx = int(iid)
        ev = self.events[idx]
        if field == "key":
            name = value.lower()
            if name in self.reserved:
                return messagebox.showerror("Error", f"{name.upper()} is reserved for the recorder.")
            try:
                keyboard.key_to_scan_codes(name)
            except (ValueError, KeyError):
                return messagebox.showerror(
                    "Error", f"'{value}' isn't a valid key name.\nExamples: a, space, enter, left shift, up")
            ev["key"] = name
        elif field == "type":
            ev["type"] = value.lower()
            if ev["type"] == "wait":
                ev["key"] = ""
            elif not ev["key"]:
                ev["key"] = "a"
        else:
            try:
                delay = float(value)
                if delay < 0:
                    raise ValueError
            except ValueError:
                return messagebox.showerror("Error", "Delay must be a number of seconds, 0 or more.")
            ev["delay"] = round(delay, 4)
        self.recompute()
        self.refresh(select=[idx])

    # --- drag to reorder ----------------------------------------------------
    def _press(self, e):
        self.cancel_edit()
        self._drag = None
        if self.busy() or self.tree.identify_region(e.x, e.y) != "cell":
            return
        iid = self.tree.identify_row(e.y)
        if not iid:
            return
        self._drag = {"iid": iid, "x": e.x, "y": e.y, "active": False, "defer": False,
                      "rows": [], "drop": None}
        # pressing an already-selected row keeps the selection so the whole group can be dragged
        if iid in self.tree.selection() and not e.state & 0x5:    # no Shift/Ctrl held
            self.tree.focus_set()
            self._drag["defer"] = True
            return "break"

    def _motion(self, e):
        d = self._drag
        if not d:
            return
        if not d["active"]:
            if abs(e.x - d["x"]) <= 5 and abs(e.y - d["y"]) <= 5:
                return "break"
            self._start_drag(d)
        top = self.winfo_toplevel()
        self._ghost.place(x=e.x_root - top.winfo_rootx() + 14, y=e.y_root - top.winfo_rooty() + 14)
        self._ghost.lift()
        if e.y < 40:                                    # autoscroll near the edges
            self.tree.yview_scroll(-1, "units")
        elif e.y > self.tree.winfo_height() - 20:
            self.tree.yview_scroll(1, "units")
        d["drop"] = self._drop_index(e.y)
        self._place_marker(d["drop"])
        return "break"

    def _start_drag(self, d):
        idx = int(d["iid"])
        rows = self._selected()
        if idx not in rows:
            rows = [idx]
            self.tree.selection_set(d["iid"])
        d["rows"], d["active"] = rows, True
        ev = self.events[idx]
        text = f"⏱ Wait {ev['delay']:.2f}s" if ev["type"] == "wait" else \
            f"{'▼' if ev['type'] == 'down' else '▲'} {ev['key']}"
        if len(rows) > 1:
            text += f"  (+{len(rows) - 1} more)"
        self._ghost = tk.Label(self.winfo_toplevel(), text=text, bg=ACCENT, fg="white", font=FONT,
                               relief="raised", padx=8, pady=2)
        self._marker = tk.Frame(self.tree, bg=ACCENT)

    def _drop_index(self, y):
        """Index in self.events where the dragged rows would be inserted for a cursor at y."""
        n = len(self.events)
        if y < 0 or self.tree.identify_region(10, y) == "heading":
            return round(self.tree.yview()[0] * n)      # above the list: top visible row
        row = self.tree.identify_row(y)
        if not row:
            return n                                     # below the last row
        _, by, _, bh = self.tree.bbox(row)
        return int(row) + (1 if y > by + bh / 2 else 0)

    def _place_marker(self, drop):
        n = len(self.events)
        if drop < n:
            box = self.tree.bbox(str(drop))
            y = box[1] if box else None
        else:
            box = self.tree.bbox(str(n - 1)) if n else None
            y = box[1] + box[3] if box else None
        if y is None:
            self._marker.place_forget()
            return
        self._marker.place(x=0, y=y - 1, relwidth=1, height=2)
        self._marker.lift()

    def _release(self, e):
        d, self._drag = self._drag, None
        if not d:
            return
        for name in ("_ghost", "_marker"):
            widget = getattr(self, name)
            if widget:
                widget.destroy()
                setattr(self, name, None)
        if not d["active"]:
            if d["defer"]:     # plain click on a selected row: select just that one
                self.tree.selection_set(d["iid"])
                self.tree.focus(d["iid"])
            return
        if d["drop"] is None:
            return
        rows, drop = set(d["rows"]), d["drop"]
        moved = [ev for i, ev in enumerate(self.events) if i in rows]
        rest = [ev for i, ev in enumerate(self.events) if i not in rows]
        at = drop - sum(1 for i in rows if i < drop)
        rest[at:at] = moved
        self.events = rest
        self.recompute()
        self.refresh(select=range(at, at + len(moved)))
