# Typing Break Reminder

A Windows tray app that enforces typing/mouse breaks — built for tendinitis
and golfer's elbow recovery, inspired by [Lookaway](https://lookaway.app/)
(macOS).

It watches how long you've been continuously using the keyboard **or** mouse
and, on the schedule your provider recommended (default: every 25 minutes),
takes over the screen for a real break — with a countdown and an OT-style
stretch to do while you wait.

## How a cycle feels

1. **Working** — the tray icon *is* the timer: it shows the minutes left
   until your next break, teal while you're fine, amber in the last 5
   minutes, and red in the final minute (counting seconds). Blue means
   you're on a break; gray pause bars mean the timer is paused.
   Short thinking pauses don't stop the clock, but if you walk away for a
   few minutes on your own, the app credits it as a break and resets.
2. **60s before** — a banner slides in at the top of the screen:
   *"Break in 0:58 — wrap up your thought"* (with a **Start break now**
   button if you're ready early).
3. **30s before** — the screen begins to dim gradually (click-through, so
   you can still finish the sentence).
4. **Break** — every monitor is covered: your primary screen gets the full
   break view (countdown ring + rotating wrist/elbow stretches) and any
   other monitor gets a clean "On break" cover with the countdown. When it
   ends, the screens return and a fresh cycle starts.

### Enforcement

- The overlay can't be closed with Alt+F4 and re-asserts itself every
  second. If you actively fight it (repeatedly working around it), it
  **locks Windows for real** (`LockWorkStation`).
- **Emergency skips:** 2 per day (configurable). Using one requires holding
  the **Esc key** (or the on-screen button) for a full 5 seconds — enough
  friction that you won't do it reflexively. Releasing early cancels.
- Honest caveat: killing the process from Task Manager will always work.
  The app is a commitment device, not a jailer.

### Adherence score

The tray menu shows a running line — *"Today: 5 taken · 1 skipped ·
score 83"* — and clicking it opens the full breakdown. The score starts at
100 each day: completed breaks and rest you take on your own count for
you; skipped breaks count against you; bypass lockouts count double
against you. The window also lists your last week so you can watch the
habit build. Stats live locally in
`%APPDATA%\TypingBreakReminder\state.json` and never leave your machine.

### Privacy

Activity detection uses the Windows `GetLastInputInfo` API, which reports
only *the time since* your last keystroke or mouse move — never what you
typed. No keylogging, no admin rights, nothing leaves your machine.

## Getting the app

**Option A — download the built .exe:** every push to `main` builds
`TypingBreakReminder.exe` via GitHub Actions (see the *Actions* tab →
latest "Build Typing Break Reminder" run → *Artifacts*).

**Option B — build it yourself:** on your Windows laptop, install Python
from python.org, then double-click `build.bat` in this folder. The app
lands at `dist\TypingBreakReminder.exe`.

**Option C — run from source:**

```
pip install -r requirements.txt
python -m breaktimer
```

Add `--demo` for a quick test drive (1-minute work interval, 20-second
break).

## Tray menu

Right-click the teal icon: **Take a break now**, **Pause** (30 min / 1 hour /
until resumed — for presentations and meetings), **Resume**, **Settings…**,
**Quit**. Hovering shows time until the next break.

## Settings

Open **Settings…** from the tray. Everything is stored in
`%APPDATA%\TypingBreakReminder\config.json`.

| Setting | Default | Meaning |
| --- | --- | --- |
| Work interval | 25 min | Continuous use before a break is forced |
| Break length | 5 min | How long the break screen stays up |
| Heads-up banner | 60 s | Warning banner lead time |
| Screen dim starts | 30 s | Gradual dim lead time |
| Idle counts as break | 3 min | Walking away this long resets the clock |
| Emergency skips/day | 2 | Skips available per calendar day |
| Hold-to-skip | 5 s | How long the skip button must be held |
| Lock on bypass | on | Lock Windows if the overlay is fought |
| Start at login | off | Adds the app to your Windows startup |

## A note on the stretches

The break screen rotates through common OT stretches for wrist tendinitis
and golfer's elbow (wrist flexor/extensor stretches, tendon glides, prayer
stretch, and friends). They're reminders, not medical advice — follow your
own provider's program, and stop anything that hurts.
