"""Stretch prompts shown during breaks.

These are common OT stretches for wrist tendinitis and golfer's elbow —
follow your own provider's program first; these are reminders, not medical
advice. Stop any stretch that causes pain.
"""

STRETCHES = [
    (
        "Wrist extensor stretch",
        "Arm straight out, palm down. With the other hand, gently bend the "
        "hand down and toward you until you feel a stretch on top of the "
        "forearm. Hold 20–30s, then switch sides.",
    ),
    (
        "Wrist flexor stretch",
        "Arm straight out, palm up. Gently pull the fingers down and back "
        "until you feel a stretch along the inside of the forearm. "
        "Hold 20–30s, then switch sides.",
    ),
    (
        "Golfer's elbow stretch",
        "Arm straight, elbow locked, palm facing up. Pull the hand down and "
        "back until you feel it along the inner elbow. Gentle — no pain. "
        "Hold 20–30s each side.",
    ),
    (
        "Tendon glides",
        "Start with fingers straight. Make a hook fist (bend just the top "
        "knuckles), back to straight, then a full fist, then straight again. "
        "Slow and smooth, 5–10 reps per hand.",
    ),
    (
        "Prayer stretch",
        "Palms together in front of your chest, elbows out. Slowly lower "
        "your hands toward your waist, keeping palms together, until you "
        "feel a stretch in the wrists. Hold 20–30s.",
    ),
    (
        "Shake it out + shoulder rolls",
        "Let your arms hang loose and gently shake out your hands for 10s. "
        "Then roll your shoulders backward 10 times — slow, big circles.",
    ),
    (
        "Thumb stretch",
        "Tuck your thumb into your palm and wrap your fingers over it, then "
        "gently tilt the hand down (pinky side). Mild stretch only. "
        "Hold 15s each side.",
    ),
    (
        "Look away, too",
        "Bonus for your eyes: focus on something at least 20 feet away for "
        "20 seconds. Unclench your jaw, drop your shoulders, breathe.",
    ),
]


def stretch_for(index: int):
    """Deterministic rotation through the list."""
    return STRETCHES[index % len(STRETCHES)]
