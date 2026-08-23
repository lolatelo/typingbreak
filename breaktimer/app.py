"""Wires everything together: engine, banner, dim layer, overlay, tray."""

import argparse
import queue
import sys
import tkinter as tk

from . import config as config_mod
from .activity import idle_seconds
from .engine import Engine, Listener, Phase
from .overlay import Banner, BreakOverlay, DimLayer
from .settings_ui import SettingsDialog
from .tray import Tray


def _fmt(seconds: float) -> str:
    seconds = max(int(seconds), 0)
    return f"{seconds // 60}:{seconds % 60:02d}"


class App(Listener):
    def __init__(self, cfg):
        self.cfg = cfg
        self.root = tk.Tk()
        self.root.withdraw()
        self.banner = Banner(self.root, cfg, on_start_now=self._break_now)
        self.dim = DimLayer(self.root)
        self.overlay = BreakOverlay(self.root, cfg, on_skip=self._skip_break)
        self.engine = Engine(cfg, idle_seconds, self, config_mod.SkipStore())
        self.tray = Tray()

    # ---- engine callbacks (main thread) --------------------------------

    def on_work_tick(self, remaining: float) -> None:
        self.tray.set_status(f"Break in {_fmt(remaining)}")
        self.tray.set_countdown("work", remaining)
        if remaining <= self.cfg.warning_seconds:
            self.banner.update(remaining)
        else:
            self.banner.hide()
        if 0 < remaining <= self.cfg.dim_seconds:
            self.dim.set_progress(1 - remaining / self.cfg.dim_seconds)
        else:
            self.dim.hide()

    def on_break_start(self, duration: float) -> None:
        self.banner.hide()
        self.dim.hide()
        self.tray.set_status("On break 🙌")
        self.tray.set_countdown("break", duration)
        self.overlay.show(duration, self.engine.skips_left())

    def on_break_tick(self, remaining: float) -> None:
        self.tray.set_status(f"On break — {_fmt(remaining)} left")
        self.tray.set_countdown("break", remaining)
        self.overlay.update(remaining)

    def on_break_end(self, completed: bool) -> None:
        self.overlay.hide()
        self.tray.set_status("Fresh cycle started")

    def on_clock_reset(self, reason: str) -> None:
        self.banner.hide()
        self.dim.hide()
        if reason == "paused":
            self.tray.set_status("Paused")
            self.tray.set_countdown("paused")

    # ---- actions -------------------------------------------------------

    def _break_now(self) -> None:
        self.engine.start_break()

    def _skip_break(self) -> None:
        self.engine.skip_break()

    def _open_settings(self) -> None:
        def saved():
            # Apply new limits immediately; never extend past a new max.
            self.engine.work_elapsed = min(
                self.engine.work_elapsed, self.cfg.work_seconds
            )

        SettingsDialog(self.root, self.cfg, saved)

    def _quit(self) -> None:
        self.tray.stop()
        self.root.after(100, self.root.destroy)

    # ---- main loop -----------------------------------------------------

    def _drain_tray_commands(self) -> None:
        while True:
            try:
                cmd = self.tray.commands.get_nowait()
            except queue.Empty:
                return
            if cmd == "break_now":
                self._break_now()
            elif cmd == "pause_30":
                self.engine.pause(30)
            elif cmd == "pause_60":
                self.engine.pause(60)
            elif cmd == "pause_forever":
                self.engine.pause(None)
            elif cmd == "resume":
                self.engine.resume()
            elif cmd == "settings":
                self._open_settings()
            elif cmd == "quit":
                self._quit()

    def _tick(self) -> None:
        self._drain_tray_commands()
        self.engine.tick()
        if self.engine.phase is Phase.BREAK:
            self.overlay.reassert()
        self.root.after(1000, self._tick)

    def run(self) -> None:
        self.tray.start()
        self.root.after(1000, self._tick)
        self.root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Typing break reminder")
    parser.add_argument(
        "--demo", action="store_true",
        help="short timings for a quick test: 1 min work, 20s break",
    )
    args = parser.parse_args()

    cfg = config_mod.load_config()
    if args.demo:
        cfg.work_minutes = 1.0
        cfg.break_minutes = 1 / 3  # 20 seconds
        cfg.warning_seconds = 30
        cfg.dim_seconds = 15
        cfg.natural_break_minutes = 0.5

    if sys.platform != "win32":
        print("Note: not on Windows — idle detection and screen lock are stubbed.")

    App(cfg).run()
