"""System tray icon and menu (pystray).

The tray runs on its own thread; menu actions are pushed onto a queue that
the tkinter main loop drains, so all UI work stays on the main thread.
"""

import queue

try:
    import pystray
    from PIL import Image, ImageDraw

    HAVE_TRAY = True
except ImportError:  # dev environments without pystray/Pillow
    HAVE_TRAY = False


def _icon_image():
    """Teal circle with white 'pause' bars — drawn in code, no asset files."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, size - 2, size - 2), fill=(79, 184, 168, 255))
    bar_w, bar_h = 8, 28
    top = (size - bar_h) // 2
    draw.rounded_rectangle((20, top, 20 + bar_w, top + bar_h), 3, fill="white")
    draw.rounded_rectangle((36, top, 36 + bar_w, top + bar_h), 3, fill="white")
    return img


class Tray:
    """Commands land in .commands as strings the app understands."""

    def __init__(self):
        self.commands: "queue.Queue[str]" = queue.Queue()
        self.icon = None
        self._status = "Starting…"

    def start(self) -> None:
        if not HAVE_TRAY:
            print("[dev] pystray/Pillow not installed — running without a tray icon")
            return

        def push(cmd):
            return lambda: self.commands.put(cmd)

        menu = pystray.Menu(
            pystray.MenuItem(lambda _i: self._status, None, enabled=False),
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
        self.icon = pystray.Icon("TypingBreakReminder", _icon_image(),
                                 "Typing Break Reminder", menu)
        self.icon.run_detached()

    def set_status(self, text: str) -> None:
        self._status = text
        if self.icon is not None:
            self.icon.title = text  # hover tooltip

    def stop(self) -> None:
        if self.icon is not None:
            self.icon.stop()
