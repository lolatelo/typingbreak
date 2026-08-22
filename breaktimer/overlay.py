"""On-screen UI: pre-break banner, gradual screen dim, and the break overlay.

Lookaway-inspired flow:
  1. A calm banner slides in near the top of the screen 60s before the break.
  2. From 30s out, the whole screen dims gradually (click-through, so you can
     still finish your thought).
  3. At zero, an undismissable full-screen overlay takes over with the
     countdown and a stretch. Fighting the overlay locks Windows for real.
"""

import sys
import time
import tkinter as tk
import tkinter.font as tkfont

from .activity import lock_workstation
from .stretches import stretch_for

BG = "#101418"
FG = "#e8edf2"
ACCENT = "#4fb8a8"
WARN = "#e0a458"
DANGER = "#d06060"

# Fighting the overlay this many times triggers the real Windows lock.
BYPASS_STRIKES_TO_LOCK = 3


def _virtual_screen():
    """(x, y, width, height) covering all monitors."""
    if sys.platform == "win32":
        import ctypes

        m = ctypes.windll.user32.GetSystemMetrics
        return m(76), m(77), m(78), m(79)  # SM_[XY]VIRTUALSCREEN, SM_C[XY]VIRTUALSCREEN
    return 0, 0, None, None


def _make_click_through(win: tk.Toplevel) -> None:
    """Let mouse/keyboard events pass through this window (Windows only)."""
    if sys.platform != "win32":
        return
    import ctypes

    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_NOACTIVATE = 0x08000000
    hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    )


def _fmt(seconds: float) -> str:
    seconds = max(int(seconds), 0)
    return f"{seconds // 60}:{seconds % 60:02d}"


class Banner:
    """Small always-on-top notice: 'Break in 0:58 — wrap up'."""

    def __init__(self, root: tk.Tk, on_start_now):
        self.root = root
        self.on_start_now = on_start_now
        self.win = None

    def _build(self) -> None:
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=BG)
        frame = tk.Frame(self.win, bg=BG, padx=18, pady=10)
        frame.pack()
        self.label = tk.Label(
            frame, text="", bg=BG, fg=FG, font=("Segoe UI", 13, "bold")
        )
        self.label.pack(side="left", padx=(0, 14))
        button = tk.Label(
            frame, text="Start break now", bg=ACCENT, fg=BG,
            font=("Segoe UI", 10, "bold"), padx=10, pady=3, cursor="hand2",
        )
        button.pack(side="left")
        button.bind("<Button-1>", lambda _e: self.on_start_now())
        self.win.update_idletasks()
        width = self.win.winfo_reqwidth()
        x = (self.win.winfo_screenwidth() - width) // 2
        self.win.geometry(f"+{x}+16")

    def update(self, remaining: float) -> None:
        if self.win is None:
            self._build()
        color = DANGER if remaining <= 30 else WARN
        self.label.configure(
            text=f"✋  Break in {_fmt(remaining)} — wrap up your thought", fg=color
        )
        self.win.attributes("-topmost", True)
        self.win.lift()

    def hide(self) -> None:
        if self.win is not None:
            self.win.destroy()
            self.win = None


class DimLayer:
    """Click-through black layer that fades in as the break approaches."""

    MAX_ALPHA = 0.55

    def __init__(self, root: tk.Tk):
        self.root = root
        self.win = None

    def _build(self) -> None:
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        self.win.configure(bg="black")
        x, y, w, h = _virtual_screen()
        if w is None:
            w, h = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.update_idletasks()
        _make_click_through(self.win)

    def set_progress(self, fraction: float) -> None:
        """fraction: 0.0 (no dim) → 1.0 (full dim)."""
        if self.win is None:
            self._build()
        alpha = min(max(fraction, 0.0), 1.0) * self.MAX_ALPHA
        self.win.attributes("-alpha", alpha)
        self.win.attributes("-topmost", True)
        self.win.lift()

    def hide(self) -> None:
        if self.win is not None:
            self.win.destroy()
            self.win = None


class BreakOverlay:
    """Full-screen, undismissable break screen with countdown and stretches.

    Escalation: the overlay re-asserts itself every second. Attempts to work
    around it (typing/clicking into another window it keeps losing focus to)
    accumulate strikes; enough strikes locks the workstation for real.
    """

    def __init__(self, root: tk.Tk, cfg, on_skip):
        self.root = root
        self.cfg = cfg
        self.on_skip = on_skip  # callback -> bool (True if skip granted)
        self.win = None
        self.strikes = 0
        self.stretch_index = 0
        self.shown_at = 0.0
        self._hold_started = None
        self._hold_job = None

    # ---- lifecycle -----------------------------------------------------

    def show(self, duration: float, skips_left: int) -> None:
        self.strikes = 0
        self.shown_at = time.monotonic()
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=BG)
        x, y, w, h = _virtual_screen()
        if w is None:
            w, h = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        self.win.protocol("WM_DELETE_WINDOW", self._on_bypass_attempt)
        self.win.bind("<Escape>", lambda _e: self._on_bypass_attempt())

        center = tk.Frame(self.win, bg=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            center, text="Hands off the keyboard 🙌", bg=BG, fg=FG,
            font=("Segoe UI", 26, "bold"),
        ).pack(pady=(0, 6))
        tk.Label(
            center, text="This break protects your wrists and elbow.",
            bg=BG, fg="#9aa7b0", font=("Segoe UI", 13),
        ).pack(pady=(0, 24))

        self.countdown = tk.Label(
            center, text=_fmt(duration), bg=BG, fg=ACCENT,
            font=("Segoe UI", 72, "bold"),
        )
        self.countdown.pack(pady=(0, 28))

        card = tk.Frame(center, bg="#1a2128", padx=28, pady=20)
        card.pack(pady=(0, 30))
        self.stretch_title = tk.Label(
            card, text="", bg="#1a2128", fg=FG, font=("Segoe UI", 16, "bold")
        )
        self.stretch_title.pack()
        self.stretch_body = tk.Label(
            card, text="", bg="#1a2128", fg="#b9c4cc", font=("Segoe UI", 12),
            wraplength=560, justify="center",
        )
        self.stretch_body.pack(pady=(8, 0))
        self._show_stretch()

        if skips_left > 0:
            hold = self.cfg.hold_to_skip_seconds
            self.skip_label = tk.Label(
                center,
                text=f"Emergency? Hold {hold}s to skip  ({skips_left} left today)",
                bg="#2a2f36", fg="#8a949c", font=("Segoe UI", 10),
                padx=14, pady=6, cursor="hand2",
            )
            self.skip_label.pack()
            self.skip_label.bind("<ButtonPress-1>", self._hold_start)
            self.skip_label.bind("<ButtonRelease-1>", self._hold_end)
        else:
            tk.Label(
                center, text="No emergency skips left today.",
                bg=BG, fg="#5a646c", font=("Segoe UI", 10),
            ).pack()

        self.win.update_idletasks()
        self.win.focus_force()

    def hide(self) -> None:
        self._cancel_hold_job()
        if self.win is not None:
            self.win.destroy()
            self.win = None

    @property
    def visible(self) -> bool:
        return self.win is not None

    # ---- per-second updates -------------------------------------------

    def update(self, remaining: float) -> None:
        if self.win is None:
            return
        self.countdown.configure(text=_fmt(remaining))
        # Rotate the stretch every 45 seconds.
        elapsed = int(time.monotonic() - self.shown_at)
        index = elapsed // 45
        if index != self.stretch_index:
            self.stretch_index = index
            self._show_stretch()
        self.reassert()

    def reassert(self) -> None:
        """Keep the overlay on top and focused; escalate if it's being fought."""
        if self.win is None:
            return
        self.win.attributes("-topmost", True)
        self.win.lift()
        self.win.deiconify()
        if sys.platform == "win32" and self._foreground_stolen():
            self.win.focus_force()
            self._on_bypass_attempt()

    def _foreground_stolen(self) -> bool:
        import ctypes

        # Give the user a moment after the overlay appears before judging.
        if time.monotonic() - self.shown_at < 3:
            return False
        fg = ctypes.windll.user32.GetForegroundWindow()
        hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id()) or self.win.winfo_id()
        return fg not in (hwnd, self.win.winfo_id()) and fg != 0

    def _on_bypass_attempt(self) -> None:
        self.strikes += 1
        if self.strikes >= BYPASS_STRIKES_TO_LOCK and self.cfg.lock_on_bypass:
            self.strikes = 0
            lock_workstation()

    # ---- stretch card --------------------------------------------------

    def _show_stretch(self) -> None:
        title, body = stretch_for(self.stretch_index)
        self.stretch_title.configure(text=title)
        self.stretch_body.configure(text=body)

    # ---- hold-to-skip --------------------------------------------------

    def _hold_start(self, _event) -> None:
        self._hold_started = time.monotonic()
        self._tick_hold()

    def _tick_hold(self) -> None:
        if self._hold_started is None or self.win is None:
            return
        held = time.monotonic() - self._hold_started
        needed = self.cfg.hold_to_skip_seconds
        if held >= needed:
            self._hold_started = None
            self.on_skip()
            return
        self.skip_label.configure(
            text=f"Keep holding… {needed - int(held)}s", fg=WARN
        )
        self._hold_job = self.win.after(200, self._tick_hold)

    def _hold_end(self, _event) -> None:
        self._cancel_hold_job()
        if self._hold_started is not None and self.win is not None:
            self._hold_started = None
            hold = self.cfg.hold_to_skip_seconds
            self.skip_label.configure(
                text=f"Released too early — hold the full {hold}s to skip",
                fg="#8a949c",
            )

    def _cancel_hold_job(self) -> None:
        if self._hold_job is not None and self.win is not None:
            self.win.after_cancel(self._hold_job)
        self._hold_job = None
        self._hold_started = None
