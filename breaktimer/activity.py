"""System-wide input activity detection for Windows.

Uses GetLastInputInfo, which reports the tick count of the last keyboard or
mouse event anywhere in the system. This tells us *that* input happened,
never *what* was typed — no keylogging, no admin rights, no hooks.

On non-Windows platforms (development only) idle time is reported as 0 so
the timer simply counts up.
"""

import sys

if sys.platform == "win32":
    import ctypes

    class _LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    def idle_seconds() -> float:
        """Seconds since the last keyboard or mouse input, system-wide."""
        info = _LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
        # GetTickCount wraps every ~49.7 days; a rare negative reading just
        # means "recent input".
        return max(millis, 0) / 1000.0

    def lock_workstation() -> None:
        ctypes.windll.user32.LockWorkStation()

else:

    def idle_seconds() -> float:
        return 0.0

    def lock_workstation() -> None:
        print("[dev] LockWorkStation() would run here (Windows only)")
