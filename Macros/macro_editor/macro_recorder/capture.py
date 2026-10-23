"""Turns global keyboard events into recorded steps. Runs on the keyboard listener thread."""
import time


class KeyCapture:
    def __init__(self, ignore, on_event):
        self.ignore = ignore        # key names that are never recorded (the recorder's own hotkeys)
        self.on_event = on_event    # called with every new step (from the listener thread!)
        self.recording = False
        self.events = None
        self.down = {}              # key -> perf_counter when pressed
        self.t0 = None              # perf_counter of the first recorded event
        self.last_t = 0.0
        self.started = 0.0

    def start(self, events):
        """Begin recording into the list `events`."""
        self.events = events
        self.down.clear()
        self.t0, self.last_t = None, 0.0
        self.started = time.perf_counter()
        self.recording = True

    def stop(self):
        self.recording = False

    @property
    def elapsed(self):
        return time.perf_counter() - self.started

    def __call__(self, e):
        if not self.recording or e.name in self.ignore:
            return
        now = time.perf_counter()
        held = None
        if e.event_type == "down":
            if e.name in self.down:      # ignore auto-repeat while a key is held
                return
            self.down[e.name] = now
        else:
            start = self.down.pop(e.name, None)
            held = round(now - start, 4) if start is not None else None
        if self.t0 is None:
            self.t0 = now
        t = now - self.t0
        ev = {"key": e.name, "type": e.event_type, "delay": round(t - self.last_t, 4),
              "time": round(t, 4), "held": held}
        self.last_t = t
        self.events.append(ev)
        self.on_event(ev)
