"""Configuration and small persisted state for the break reminder.

Settings live in a JSON file under %APPDATA%\\TypingBreakReminder so they
survive rebuilds of the .exe. A separate state file tracks how many
emergency skips have been used today.
"""

import datetime
import json
import os
import sys
from dataclasses import asdict, dataclass, fields

APP_NAME = "TypingBreakReminder"


def config_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def _config_path() -> str:
    return os.path.join(config_dir(), "config.json")


def _state_path() -> str:
    return os.path.join(config_dir(), "state.json")


@dataclass
class Config:
    work_minutes: float = 25.0        # continuous computer use before a break
    break_minutes: float = 5.0        # how long the break lasts
    warning_seconds: int = 60         # heads-up banner appears this far out
    dim_seconds: int = 30             # screen starts dimming this far out
    natural_break_minutes: float = 3.0  # walking away this long resets the clock
    skips_per_day: int = 2            # emergency skips available each day
    hold_to_skip_seconds: int = 5     # hold the skip button this long to use one
    lock_on_bypass: bool = True       # lock Windows if the overlay is fought

    @property
    def work_seconds(self) -> float:
        return self.work_minutes * 60

    @property
    def break_seconds(self) -> float:
        return self.break_minutes * 60

    @property
    def natural_break_seconds(self) -> float:
        return self.natural_break_minutes * 60


def load_config() -> Config:
    cfg = Config()
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        known = {f.name for f in fields(Config)}
        for key, value in data.items():
            if key in known:
                setattr(cfg, key, value)
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg: Config) -> None:
    with open(_config_path(), "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, indent=2)


STAT_KEYS = ("skips_used", "breaks_completed", "breaks_skipped",
             "natural_breaks", "lockouts")


class DayStats:
    """Per-day adherence stats (and the skip allowance), persisted to disk.

    Also computes a Lookaway-style adherence score: completed and self-taken
    breaks count for you, skipped breaks count against you, and bypass
    lockouts count double against you. No events yet = a fresh 100.
    """

    KEEP_DAYS = 14

    def __init__(self) -> None:
        self.days = {}
        try:
            with open(_state_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            if "days" in data:
                self.days = {
                    day: {k: int(stats.get(k, 0)) for k in STAT_KEYS}
                    for day, stats in data["days"].items()
                }
            elif "date" in data:  # legacy v1.x skip-only format
                legacy = dict.fromkeys(STAT_KEYS, 0)
                legacy["skips_used"] = int(data.get("skips_used", 0))
                self.days[data["date"]] = legacy
        except (OSError, ValueError):
            pass

    def _today(self) -> dict:
        key = datetime.date.today().isoformat()
        return self.days.setdefault(key, dict.fromkeys(STAT_KEYS, 0))

    def _save(self) -> None:
        keep = sorted(self.days)[-self.KEEP_DAYS:]
        self.days = {day: self.days[day] for day in keep}
        try:
            with open(_state_path(), "w", encoding="utf-8") as f:
                json.dump({"days": self.days}, f, indent=1)
        except OSError:
            pass

    def record(self, key: str, n: int = 1) -> None:
        self._today()[key] += n
        self._save()

    # -- the skip allowance (API the engine uses) --
    def used_today(self) -> int:
        return self._today()["skips_used"]

    def use_one(self) -> None:
        self.record("skips_used")

    # -- reporting --
    def today(self) -> dict:
        return dict(self._today())

    @staticmethod
    def score(stats: dict) -> int:
        good = stats["breaks_completed"] + stats["natural_breaks"]
        bad = stats["breaks_skipped"] + 2 * stats["lockouts"]
        if good + bad == 0:
            return 100
        return round(100 * good / (good + bad))

    def history(self, n: int = 7):
        """[(iso_date, stats)] for the most recent days, newest first."""
        self._today()  # make sure today exists
        return [(day, dict(self.days[day]))
                for day in sorted(self.days)[-n:]][::-1]


def autostart_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    return f'"{pythonw}" -m breaktimer'


def set_autostart(enabled: bool) -> None:
    """Register/unregister the app to start at Windows login."""
    if sys.platform != "win32":
        return
    import winreg

    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, autostart_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def autostart_enabled() -> bool:
    if sys.platform != "win32":
        return False
    import winreg

    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_QUERY_VALUE) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False
