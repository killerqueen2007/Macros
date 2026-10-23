"""Macro recorder window: glue between the file list, event table, key capture and player."""
import json
import queue
import tkinter as tk
from tkinter import messagebox, ttk

import keyboard

import recordings

from .capture import KeyCapture
from .event_table import EventTable
from .file_list import FileList
from .player import Player
from .theme import BG, FG, RED, GREEN, apply_style

START_KEY, STOP_KEY, PLAY_KEY = "f8", "f9", "f10"
CONTROL_KEYS = {START_KEY, STOP_KEY, PLAY_KEY}


class RecorderApp:
    def __init__(self, root):
        self.root = root
        root.title("Macro Recorder")
        root.geometry("1180x660")
        root.minsize(1180, 660)
        root.configure(bg=BG)
        apply_style(root)

        self.ui_q = queue.Queue()        # listener / playback threads -> UI thread
        self.name_var = tk.StringVar()   # macro name shown in the UI / saved to file
        self.current_file = None         # saved file open in the editor (name without .json); None = new recording
        self._saved = None               # snapshot as last opened/saved, to spot unsaved changes
        self.capture = KeyCapture(CONTROL_KEYS, lambda ev: self.ui_q.put(("event", ev)))
        self.player = Player(lambda *msg: self.ui_q.put(msg))

        self._build()
        self._saved = self._snapshot()

        keyboard.hook(self.capture)
        for key, cmd in ((START_KEY, "record"), (STOP_KEY, "stop"), (PLAY_KEY, "play")):
            keyboard.add_hotkey(key, lambda c=cmd: self.ui_q.put(("cmd", c)))

        root.protocol("WM_DELETE_WINDOW", self.close)
        self._poll()

    # --- UI ---------------------------------------------------------------
    def _build(self):
        outer = ttk.Frame(self.root, style="Root.TFrame", padding=20)
        outer.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        card = ttk.Frame(outer, padding=15)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(1, weight=1)
        card.rowconfigure(0, weight=1)

        self.files = FileList(card, self._on_file_pick)
        self.files.grid(row=0, column=0, sticky="ns")
        self.files.refresh()

        body = ttk.Frame(card)
        body.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)

        ttk.Label(body, text="Macro Recorder", style="Header.TLabel").grid(row=0, column=0, sticky="w")

        info = ttk.Frame(body)
        info.grid(row=1, column=0, sticky="ew", pady=(6, 10))
        info.columnconfigure(1, weight=1)
        self.status = ttk.Label(info, text="Idle", style="Status.TLabel")
        self.status.grid(row=0, column=0, sticky="w")
        self.summary = ttk.Label(info, text="0 events")
        self.summary.grid(row=0, column=1, sticky="e")

        name_row = ttk.Frame(info)
        name_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        name_row.columnconfigure(1, weight=1)
        ttk.Label(name_row, text="Name:").grid(row=0, column=0, padx=(0, 8))
        ttk.Entry(name_row, textvariable=self.name_var).grid(row=0, column=1, sticky="ew")

        self.table = EventTable(body, self.busy, self._update_summary, reserved_keys=CONTROL_KEYS)
        self.table.grid(row=2, column=0, sticky="nsew")

        ttk.Label(body, text="Double-click a Key, Action or Delay cell to edit it. "
                             "Wait rows are pure delays. Drag rows to reorder them.",
                  style="Hint.TLabel").grid(row=3, column=0, sticky="w", pady=(6, 0))

        # add a button = one tuple
        self._button_row(body, 4, (
            (f"⏺ Record ({START_KEY.upper()})", self.start_record, "Rec.TButton"),
            (f"⏹ Stop ({STOP_KEY.upper()})", self.stop, "TButton"),
            (f"▶ Play ({PLAY_KEY.upper()})", self.play, "TButton"),
        ))
        self._button_row(body, 5, (
            ("➕ Add Key", self.table.add_key, "TButton"),
            ("⏱ Add Delay", self.table.add_delay, "TButton"),
            ("➖ Delete", self.table.delete_selected, "TButton"),
            ("🗑 Clear", self.clear, "TButton"),
            ("💾 Save", self.save, "TButton"),
        ))

    @staticmethod
    def _button_row(parent, row, buttons):
        bar = ttk.Frame(parent)
        bar.grid(row=row, column=0, sticky="ew", pady=(10, 0))
        for i, (label, cmd, style) in enumerate(buttons):
            bar.columnconfigure(i, weight=1, uniform="b")
            ttk.Button(bar, text=label, command=cmd, style=style).grid(row=0, column=i, sticky="ew", padx=3)

    # --- state ------------------------------------------------------------
    def busy(self):
        return self.capture.recording or self.player.playing

    def _snapshot(self):
        events = [(e["key"], e["type"], e["delay"]) for e in self.table.events]
        return json.dumps([self.name_var.get().strip(), events])

    def _update_summary(self):
        events = self.table.events
        total = events[-1]["time"] if events else 0
        self.summary.config(text=f"{len(events)} events  |  {total:.3f}s total")

    def _set_status(self, text, color):
        self.status.config(text=text, foreground=color)

    # --- saved recordings ---------------------------------------------------
    def _on_file_pick(self, stem):
        if stem == self.current_file:
            return
        if self.busy():
            return self.files.refresh(self.current_file)    # can't switch files while recording / playing
        if self.table.events and self._snapshot() != self._saved and not messagebox.askyesno(
                "Unsaved changes", "The current recording has unsaved changes.\n\nDiscard them and open this file?"):
            return self.files.refresh(self.current_file)    # put the highlight back on the file that's still open
        try:
            name, events = recordings.read(stem)
        except ValueError:
            messagebox.showerror("Error", "That file isn't a valid recording.")
            return self.files.refresh(self.current_file)
        self.name_var.set(name or stem)
        self.table.load(events)
        self.current_file = stem
        self._saved = self._snapshot()

    def save(self):
        events = self.table.events
        if not events:
            return messagebox.showwarning("Warning", "Nothing to save.")
        name = self.name_var.get().strip() or "Untitled"
        stem = recordings.filename_for(name)
        if not stem:
            return messagebox.showerror("Error", "That name can't be used as a file name.")
        if recordings.exists(stem) and stem != self.current_file and not messagebox.askyesno(
                "Overwrite?", f"'{stem}.json' already exists in user_recd_mac.\n\nOverwrite it?"):
            return
        try:
            recordings.save(name, events)
        except OSError as err:
            return messagebox.showerror("Error", f"Couldn't save the file:\n{err}")
        self.current_file = stem
        self._saved = self._snapshot()
        self.files.refresh(stem)
        messagebox.showinfo("Saved", f"Saved to user_recd_mac/{stem}.json")

    # --- actions (UI thread) -----------------------------------------------
    def start_record(self):
        if self.busy():
            return
        self.clear()
        self.capture.start(self.table.events)
        self._set_status("● Recording...", RED)

    def stop(self):
        if self.capture.recording:
            self.capture.stop()
            self._set_status("Idle", FG)
            self._update_summary()
        elif self.player.playing:
            self.player.stop()

    def play(self):
        if self.busy() or not self.table.events:
            return
        self.table.cancel_edit()
        self.player.start(self.table.events)
        self._set_status("▶ Playing...", GREEN)

    def clear(self):
        if self.busy():
            return
        self.table.clear()
        self.current_file = None
        self.files.clear_selection()

    # --- UI updates ---------------------------------------------------------
    def _poll(self):
        try:
            while True:
                kind, *rest = self.ui_q.get_nowait()
                if kind == "event":
                    self.table.append_row(rest[0])
                    self._update_summary()
                elif kind == "cmd":
                    {"record": self.start_record, "stop": self.stop, "play": self.play}[rest[0]]()
                elif kind == "playing":
                    self.table.highlight(rest[0])
                elif kind == "play_done":
                    self.table.unhighlight()
                    self._set_status(f"Idle ({rest[0]} keys skipped)" if rest[0] else "Idle", FG)
        except queue.Empty:
            pass
        if self.capture.recording:
            self.summary.config(text=f"{len(self.table.events)} events  |  {self.capture.elapsed:.1f}s elapsed")
        self.root.after(30, self._poll)

    def close(self):
        self.player.stop()
        keyboard.unhook_all()
        self.root.destroy()


def run():
    root = tk.Tk()
    RecorderApp(root)
    root.mainloop()
