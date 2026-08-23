"""Settings dialog (tkinter/ttk, native Windows theming)."""

import tkinter as tk
from tkinter import messagebox, ttk

from . import config as config_mod

SECTIONS = [
    ("Timing", [
        ("work_minutes", "Work interval (minutes)", float),
        ("break_minutes", "Break length (minutes)", float),
        ("natural_break_minutes", "Idle time that counts as a break (minutes)", float),
    ]),
    ("Warnings", [
        ("warning_seconds", "Heads-up banner (seconds before break)", int),
        ("dim_seconds", "Screen dim starts (seconds before break)", int),
    ]),
    ("Emergency skips", [
        ("skips_per_day", "Skips allowed per day", int),
        ("hold_to_skip_seconds", "Hold-to-skip duration (seconds)", int),
    ]),
]


class SettingsDialog:
    def __init__(self, root: tk.Tk, cfg, on_saved):
        self.cfg = cfg
        self.on_saved = on_saved
        self.win = tk.Toplevel(root)
        self.win.title("Typing Break Reminder — Settings")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)

        try:
            ttk.Style(self.win).theme_use("vista")
        except tk.TclError:
            pass

        body = ttk.Frame(self.win, padding=(16, 12))
        body.pack(fill="both", expand=True)

        self.vars = {}
        self.casts = {}
        for title, fields in SECTIONS:
            box = ttk.LabelFrame(body, text=title, padding=(12, 8))
            box.pack(fill="x", pady=(0, 10))
            box.columnconfigure(0, weight=1)
            for row, (name, label, cast) in enumerate(fields):
                ttk.Label(box, text=label).grid(
                    row=row, column=0, sticky="w", pady=3, padx=(0, 12)
                )
                var = tk.StringVar(value=str(getattr(cfg, name)))
                self.vars[name] = var
                self.casts[name] = cast
                ttk.Entry(box, textvariable=var, width=7,
                          justify="right").grid(row=row, column=1, pady=3)

        behavior = ttk.LabelFrame(body, text="Behavior", padding=(12, 8))
        behavior.pack(fill="x", pady=(0, 10))
        self.lock_var = tk.BooleanVar(value=cfg.lock_on_bypass)
        ttk.Checkbutton(
            behavior, text="Lock Windows if I fight the break screen",
            variable=self.lock_var,
        ).pack(anchor="w", pady=2)
        self.autostart_var = tk.BooleanVar(value=config_mod.autostart_enabled())
        ttk.Checkbutton(
            behavior, text="Start automatically when I log in",
            variable=self.autostart_var,
        ).pack(anchor="w", pady=2)

        buttons = ttk.Frame(body)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Cancel", command=self.win.destroy).pack(
            side="right", padx=(6, 0)
        )
        ttk.Button(buttons, text="Save", command=self._save,
                   default="active").pack(side="right")
        self.win.bind("<Return>", lambda _e: self._save())
        self.win.bind("<Escape>", lambda _e: self.win.destroy())

    def _save(self) -> None:
        try:
            for name, var in self.vars.items():
                value = self.casts[name](var.get())
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
