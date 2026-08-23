"""Today's adherence stats window."""

import datetime
import tkinter as tk
from tkinter import ttk

BG = "#101418"
FG = "#e8edf2"
MUTED = "#9aa7b0"
ACCENT = "#4fb8a8"
WARN = "#e0a458"
DANGER = "#d06060"


def _score_color(score: int) -> str:
    if score >= 80:
        return ACCENT
    if score >= 50:
        return WARN
    return DANGER


class StatsWindow:
    def __init__(self, root: tk.Tk, stats):
        self.win = tk.Toplevel(root)
        self.win.title("Typing Break Reminder — Today")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.configure(bg=BG)

        today = stats.today()
        score = stats.score(today)

        body = tk.Frame(self.win, bg=BG, padx=28, pady=22)
        body.pack()

        tk.Label(body, text="Adherence score", bg=BG, fg=MUTED,
                 font=("Segoe UI", 11)).pack()
        tk.Label(body, text=str(score), bg=BG, fg=_score_color(score),
                 font=("Segoe UI", 52, "bold")).pack(pady=(0, 4))
        blurb = ("Fresh slate — take your breaks!" if score == 100
                 and today["breaks_completed"] + today["natural_breaks"] == 0
                 else "Breaks taken help; skips and lockouts hurt.")
        tk.Label(body, text=blurb, bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(pady=(0, 16))

        rows = [
            ("Breaks completed", today["breaks_completed"], ACCENT),
            ("Rest you took on your own", today["natural_breaks"], ACCENT),
            ("Breaks skipped", today["breaks_skipped"], WARN),
            ("Bypass lockouts", today["lockouts"], DANGER),
        ]
        grid = tk.Frame(body, bg=BG)
        grid.pack(fill="x", pady=(0, 16))
        for r, (label, value, color) in enumerate(rows):
            tk.Label(grid, text=label, bg=BG, fg=FG, anchor="w",
                     font=("Segoe UI", 11)).grid(row=r, column=0, sticky="w",
                                                 pady=2, padx=(0, 24))
            tk.Label(grid, text=str(value), bg=BG, fg=color,
                     font=("Segoe UI", 11, "bold")).grid(row=r, column=1,
                                                         sticky="e", pady=2)
        grid.columnconfigure(0, weight=1)

        past = [(day, s) for day, s in stats.history(8)
                if day != datetime.date.today().isoformat()][:7]
        if past:
            tk.Frame(body, bg="#232a31", height=1).pack(fill="x", pady=(0, 10))
            tk.Label(body, text="Previous days", bg=BG, fg=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            for day, s in past:
                nice = datetime.date.fromisoformat(day).strftime("%a %b %d")
                line = (f"{nice}   score {stats.score(s)}  ·  "
                        f"{s['breaks_completed']} taken · "
                        f"{s['breaks_skipped']} skipped")
                tk.Label(body, text=line, bg=BG, fg="#7d8892",
                         font=("Segoe UI", 9)).pack(anchor="w")

        ttk.Button(body, text="Close", command=self.win.destroy).pack(
            pady=(14, 0)
        )
        self.win.bind("<Escape>", lambda _e: self.win.destroy())
