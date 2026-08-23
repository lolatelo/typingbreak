"""System tray icon and menu (pystray).

The tray runs on its own thread; menu actions are pushed onto a queue that
the tkinter main loop drains, so all UI work stays on the main thread.

The icon itself is a live countdown: the minutes remaining are drawn onto
the icon bitmap, color-coded by urgency (teal → amber at 5 min → red in the
final minute, where it counts seconds). Redrawn only when the displayed
value changes, so this costs about one tiny bitmap per minute.
"""

import math
import queue

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont

    HAVE_TRAY = True
except ImportError:  # dev environments without pystray/Pillow
    HAVE_TRAY = False

TEAL = (79, 184, 168, 255)     # working, plenty of time
AMBER = (224, 164, 88, 255)    # 5 minutes left
RED = (208, 96, 96, 255)       # final minute (shows seconds)
BLUE = (91, 141, 214, 255)     # on break
GRAY = (122, 130, 138, 255)    # paused


def _font(px: int):
    for name in ("segoeuib.ttf", "seguisb.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_icon(text, bg):
    """A filled circle with `text` centered on it; None = pause bars."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((1, 1, size - 1, size - 1), fill=bg)
    if text is None:
        bar_w, bar_h = 8, 28
        top = (size - bar_h) // 2
        draw.rounded_rectangle((20, top, 20 + bar_w, top + bar_h), 3, fill="white")
        draw.rounded_rectangle((36, top, 36 + bar_w, top + bar_h), 3, fill="white")
        return img
    font = _font(44 if len(text) <= 2 else 32)
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1]),
              text, font=font, fill="white")
    return img


def _countdown_face(state: str, remaining):
    """(text, color) for the icon given engine state + seconds remaining."""
    if state == "paused":
        return None, GRAY
    if state == "break":
        return str(max(math.ceil(remaining / 60), 1)), BLUE
    # working
    if remaining < 60:
        return str(max(int(remaining), 0)), RED
    minutes = math.ceil(remaining / 60)
    if minutes > 99:
        return "99", TEAL
    return str(minutes), AMBER if minutes <= 5 else TEAL


class Tray:
    """Commands land in .commands as strings the app understands."""

    def __init__(self):
        self.commands: "queue.Queue[str]" = queue.Queue()
        self.icon = None
        self._status = "Starting…"
        self._stats_line = "Today: no breaks yet"
        self._face = None  # (text, color) currently drawn on the icon

    def start(self) -> None:
        if not HAVE_TRAY:
            print("[dev] pystray/Pillow not installed — running without a tray icon")
            return

        def push(cmd):
            return lambda: self.commands.put(cmd)

        menu = pystray.Menu(
            pystray.MenuItem(lambda _i: self._status, None, enabled=False),
            pystray.MenuItem(lambda _i: self._stats_line, push("stats")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Take a break now", push("break_now")),
            pystray.MenuItem(
                "Pause",
                pystray.Menu(
                    pystray.MenuItem("For 30 minutes", push("pause_30")),
                    pystray.MenuItem("For 1 hour", push("pause_60")),
                    pystray.MenuItem("Until I resume", push("pause_forever")),
                ),
            ),
            pystray.MenuItem("Resume", push("resume")),
            pystray.MenuItem("Settings…", push("settings")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", push("quit")),
        )
        self.icon = pystray.Icon(
            "TypingBreakReminder", _render_icon(None, TEAL),
            "Typing Break Reminder", menu,
        )
        self.icon.run_detached()

    def set_status(self, text: str) -> None:
        self._status = text
        if self.icon is not None:
            self.icon.title = text  # hover tooltip

    def set_stats_line(self, text: str) -> None:
        self._stats_line = text  # read lazily when the menu opens

    def set_countdown(self, state: str, remaining=None) -> None:
        """Redraw the icon face if the displayed value changed."""
        if self.icon is None:
            return
        face = _countdown_face(state, remaining)
        if face != self._face:
            self._face = face
            self.icon.icon = _render_icon(*face)

    def stop(self) -> None:
        if self.icon is not None:
            self.icon.stop()
