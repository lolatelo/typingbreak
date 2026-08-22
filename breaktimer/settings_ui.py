"""Settings dialog (tkinter)."""

import tkinter as tk
from tkinter import messagebox

from . import config as config_mod


class SettingsDialog:
    FIELDS = [
        ("work_minutes", "Work interval (minutes)", float),
        ("break_minutes", "Break length (minutes)", float),
        ("warning_seconds", "Heads-up banner (seconds before break)", int),
        ("dim_seconds", "Screen dim starts (seconds before break)", int),
        ("natural_break_minutes", "Idle time that counts as a break (minutes)", float),
        ("skips_per_day", "Emergency skips per day", int),
        ("hold_to_skip_seconds", "Hold-to-skip duration (seconds)", int),
    ]

    def __init__(self, root: tk.Tk, cfg, on_saved):
        self.cfg = cfg
        self.on_saved = on_saved
        self.win = tk.Toplevel(root)
        self.win.title("Typing Break Reminder — Settings")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)

        body = tk.Frame(self.win, padx=16, pady=12)
        body.pack()
        self.vars = {}
        for row, (name, label, _cast) in enumerate(self.FIELDS):
            tk.Label(body, text=label, anchor="w").grid(
                row=row, column=0, sticky="w", pady=3, padx=(0, 12)
            )
            var = tk.StringVar(value=str(getattr(cfg, name)))
            self.vars[name] = var
            tk.Entry(body, textvariable=var, width=8, justify="right").grid(
                row=row, column=1, pady=3
            )

        row = len(self.FIELDS)
        self.lock_var = tk.BooleanVar(value=cfg.lock_on_bypass)
        tk.Checkbutton(
            body, text="Lock Windows if I fight the break screen",
            variable=self.lock_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.autostart_var = tk.BooleanVar(value=config_mod.autostart_enabled())
        tk.Checkbutton(
            body, text="Start automatically when I log in",
            variable=self.autostart_var,
        ).grid(row=row + 1, column=0, columnspan=2, sticky="w")

        buttons = tk.Frame(body)
        buttons.grid(row=row + 2, column=0, columnspan=2, pady=(14, 0))
        tk.Button(buttons, text="Save", width=10, command=self._save).pack(
            side="left", padx=4
        )
        tk.Button(buttons, text="Cancel", width=10, command=self.win.destroy).pack(
            side="left", padx=4
        )

    def _save(self) -> None:
        try:
            for name, _label, cast in self.FIELDS:
                value = cast(self.vars[name].get())
                if value < 0:
                    raise ValueError(name)
                setattr(self.cfg, name, value)
        except ValueError:
            messagebox.showerror(
                "Invalid value", "Please enter positive numbers only.",
                parent=self.win,
            )
            return
        self.cfg.lock_on_bypass = self.lock_var.get()
        config_mod.save_config(self.cfg)
        try:
            config_mod.set_autostart(self.autostart_var.get())
        except OSError:
            messagebox.showwarning(
                "Autostart", "Couldn't update the login autostart entry.",
                parent=self.win,
            )
        self.win.destroy()
        self.on_saved()
