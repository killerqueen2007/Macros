"""Plays the table back on a worker thread (the actual key presses live in actions.play_recording)."""
import threading

import actions


class Player:
    def __init__(self, post):
        self.post = post           # post("playing", row) / post("play_done", skipped_keys), thread-safe
        self.playing = False
        self._flag = {"active": False}

    def start(self, events):
        self._flag = flag = {"active": True}
        self.playing = True
        threading.Thread(target=self._run, args=(list(events), flag), daemon=True).start()

    def stop(self):
        self._flag["active"] = False

    def _run(self, events, flag):
        skipped = 0
        try:
            skipped = actions.play_recording(events, flag, on_step=lambda i: self.post("playing", i))
        finally:
            self.playing = False
            self.post("play_done", skipped)
