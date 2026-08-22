# Typing Break Reminder

A Windows tray app that enforces typing/mouse breaks — built for tendinitis
and golfer's elbow recovery, inspired by [Lookaway](https://lookaway.app/)
(macOS).

It watches how long you've been continuously using the keyboard **or** mouse
and, on the schedule your provider recommended (default: every 25 minutes),
takes over the screen for a real break — with a countdown and an OT-style
stretch to do while you wait.

## How a cycle feels

1. **Working** — a tray icon quietly shows time until your next break.
   Short thinking pauses don't stop the clock, but if you walk away for a
   few minutes on your own, the app credits it as a break and resets.
2. **60s before** — a banner slides in at the top of the screen:
   *"Break in 0:58 — wrap up your thought"* (with a **Start break now**
   button if you're ready early).
3. **30s before** — the screen begins to dim gradually (click-through, so
   you can still finish the sentence).
4. **Break** — a full-screen, undismissable overlay shows the countdown and
   rotates through wrist/elbow stretches. When it ends, the screen returns
   and a fresh cycle starts.

### Enforcement

- The overlay can't be closed with Esc or Alt+F4 and re-asserts itself every
  second. If you actively fight it (repeatedly working around it), it
  **locks Windows for real** (`LockWorkStation`).
- **Emergency skips:** 2 per day (configurable). Using one requires holding
  the skip button for a full 5 seconds — enough friction that you won't do
  it reflexively.
- Honest caveat: killing the process from Task Manager will always work.
  The app is a commitment device, not a jailer.

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
