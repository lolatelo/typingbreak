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


class SkipStore:
    """Persists how many emergency skips have been used today."""

    def __init__(self) -> None:
        self._date = ""
        self._used = 0
        self._load()

    def _load(self) -> None:
        try:
            with open(_state_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            self._date = data.get("date", "")
            self._used = int(data.get("skips_used", 0))
        except (OSError, ValueError):
            pass
        self._roll_day()

    def _save(self) -> None:
        try:
            with open(_state_path(), "w", encoding="utf-8") as f:
                json.dump({"date": self._date, "skips_used": self._used}, f)
        except OSError:
            pass

    def _roll_day(self) -> None:
        today = datetime.date.today().isoformat()
        if self._date != today:
            self._date = today
            self._used = 0
            self._save()

    def used_today(self) -> int:
        self._roll_day()
        return self._used

    def use_one(self) -> None:
        self._roll_day()
        self._used += 1
        self._save()


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
