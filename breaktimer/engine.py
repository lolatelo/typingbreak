"""The timer state machine.

Ticks once per second. Tracks continuous computer use (typing OR mouse),
credits breaks you take on your own, and drives the break/warning callbacks
that the UI layer renders.
"""

import time
from enum import Enum, auto

# A second counts toward "continuous use" if input happened within this many
# seconds — short thinking pauses don't stop the clock.
ACTIVE_IDLE_CUTOFF = 15.0


class Phase(Enum):
    WORKING = auto()
    BREAK = auto()
    PAUSED = auto()


class Listener:
    """Override the callbacks you care about."""

    def on_work_tick(self, remaining: float) -> None: ...
    def on_break_start(self, duration: float) -> None: ...
    def on_break_tick(self, remaining: float) -> None: ...
    def on_break_end(self, completed: bool) -> None: ...
    def on_clock_reset(self, reason: str) -> None: ...


class Engine:
    def __init__(self, cfg, idle_fn, listener: Listener, skip_store):
        self.cfg = cfg
        self.idle_fn = idle_fn
        self.listener = listener
        self.skips = skip_store
        self.phase = Phase.WORKING
        self.work_elapsed = 0.0
        self.break_remaining = 0.0
        self.pause_until = None  # monotonic deadline, or None = until resumed

    # ---- queries -------------------------------------------------------

    def work_remaining(self) -> float:
        return max(self.cfg.work_seconds - self.work_elapsed, 0)

    def skips_left(self) -> int:
        return max(self.cfg.skips_per_day - self.skips.used_today(), 0)

    # ---- tick ----------------------------------------------------------

    def tick(self) -> None:
        if self.phase is Phase.PAUSED:
            if self.pause_until is not None and time.monotonic() >= self.pause_until:
                self.resume()
            return

        if self.phase is Phase.WORKING:
            idle = self.idle_fn()
            if idle >= self.cfg.natural_break_seconds:
                if self.work_elapsed > 0:
                    self.work_elapsed = 0.0
                    self.listener.on_clock_reset("you rested on your own")
            elif idle < ACTIVE_IDLE_CUTOFF:
                self.work_elapsed += 1.0
            self.listener.on_work_tick(self.work_remaining())
            if self.work_remaining() <= 0:
                self.start_break()
            return

        if self.phase is Phase.BREAK:
            self.break_remaining -= 1.0
            if self.break_remaining <= 0:
                self._finish_break(completed=True)
            else:
                self.listener.on_break_tick(self.break_remaining)

    # ---- transitions ---------------------------------------------------

    def start_break(self) -> None:
        if self.phase is Phase.BREAK:
            return
        self.phase = Phase.BREAK
        self.break_remaining = self.cfg.break_seconds
        self.listener.on_break_start(self.break_remaining)

    def _finish_break(self, completed: bool) -> None:
        self.phase = Phase.WORKING
        self.work_elapsed = 0.0
        self.break_remaining = 0.0
        self.listener.on_break_end(completed)

    def skip_break(self) -> bool:
        """Use an emergency skip, if any remain today."""
        if self.phase is not Phase.BREAK or self.skips_left() <= 0:
            return False
        self.skips.use_one()
        self._finish_break(completed=False)
        return True

    def pause(self, minutes=None) -> None:
        """Suspend the timer (e.g. for a presentation)."""
        if self.phase is Phase.BREAK:
            return
        self.phase = Phase.PAUSED
        self.pause_until = None if minutes is None else time.monotonic() + minutes * 60
        self.listener.on_clock_reset("paused")

    def resume(self) -> None:
        if self.phase is not Phase.PAUSED:
            return
        self.phase = Phase.WORKING
        self.pause_until = None
        self.work_elapsed = 0.0
        self.listener.on_clock_reset("resumed")
