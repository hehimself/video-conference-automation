"""Allocation-light procedural lighting shared with the desktop preview."""

import math


def hsv(h):
    h = (h % 1) * 6
    sector = int(h)
    f = h - sector
    return ((1, f, 0), (1 - f, 1, 0), (0, 1, f), (0, 1 - f, 1), (f, 0, 1), (1, 0, 1 - f))[sector]


def pixel(style, index, elapsed, center=None):
    name = style.get("name", "solid")
    color = style.get("color", [30, 80, 160])
    speed = style.get("speed", 1)
    t = max(0, elapsed) * speed
    x, y = index % 4, index // 4
    direction = style.get("direction", "right")
    position = y if direction in ("up", "down") else x
    if direction in ("left", "up"):
        position = 3 - position
    amount = 1
    if name == "rainbow":
        return tuple(int(c * 255) for c in hsv(t * 0.15 + position / 8))
    if name in ("pulse", "breathing"):
        amount = 0.12 + 0.88 * (0.5 - 0.5 * math.cos(t * math.pi * 2))
    elif name == "wave":
        amount = 0.12 + 0.88 * (0.5 + 0.5 * math.sin(t * 3 - position * 1.2))
    elif name == "wipe":
        amount = 1 if position <= ((t * 4) % 5) else 0.04
    elif name == "heartbeat":
        phase = t % 1
        amount = max(0.05, 1 - abs(phase - 0.12) * 12, 0.65 - abs(phase - 0.36) * 12)
    elif name == "ripple":
        cx, cy = center or (1.5, 1.5)
        distance = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        amount = max(0.02, 1 - abs(distance - ((t * 3) % 5)) * 1.8)
    elif name == "blink":
        amount = 1 if t % 1 < 0.5 else 0.04
    elif name == "fade":
        amount = max(0, 1 - elapsed / style.get("duration", 1))
    elif name == "press_flash":
        amount = max(0.05, 1 - elapsed / style.get("duration", 0.3))
    return tuple(max(0, min(255, int(c * amount))) for c in color)


def frame(
    profile,
    elapsed,
    pressed=None,
    states=None,
    overlays=None,
    board_effect=None,
    key_effects=None,
    progress=None,
):
    pressed, states, overlays = pressed or {}, states or {}, overlays or {}
    result = []
    for key in profile["keys"]:
        i = key["id"]
        styles = key.get("lighting", {})
        style = styles.get("idle", profile["lighting"])
        age = elapsed
        center = None
        if board_effect:
            style, start, center = board_effect
            age = elapsed - start
        if i in states:
            style = styles.get(states[i], style)
        if i in pressed:
            style = styles.get("pressed", {"name": "solid", "color": [160, 160, 180]})
            age = elapsed - pressed[i]
        if key_effects and i in key_effects:
            style, start = key_effects[i]
            age = elapsed - start
        if i in overlays:
            state, start = overlays[i]
            style = styles.get(
                state,
                {
                    "name": "pulse" if state == "running" else "solid",
                    "color": {
                        "running": [50, 100, 255],
                        "success": [10, 220, 90],
                        "error": [255, 20, 30],
                    }.get(state, [30, 80, 160]),
                },
            )
            age = elapsed - start
        brightness = profile.get("brightness", 0.5)
        if progress and i in progress:
            brightness *= 0.2 + 0.8 * progress[i]
        result.append(tuple(int(c * brightness) for c in pixel(style, i, age, center)))
    return result
