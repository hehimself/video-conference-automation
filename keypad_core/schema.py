"""Profile v1. This module must remain compatible with CircuitPython."""

VERSION = 1
MAX_PROFILE_BYTES = 16384
EFFECTS = (
    "solid",
    "rainbow",
    "breathing",
    "wave",
    "wipe",
    "heartbeat",
    "ripple",
    "pulse",
    "blink",
    "fade",
    "press_flash",
)
DEVICE_ACTIONS = ("none", "hotkey", "text", "media", "delay", "effect", "toggle", "sequence")
HOST_ACTIONS = (
    "run_script",
    "open_app",
    "focus_app",
    "open_url",
    "play_sound",
    "app_volume",
    "extract_zip",
)
MEDIA = {
    "volume_up": 0xE9,
    "volume_down": 0xEA,
    "mute": 0xE2,
    "play_pause": 0xCD,
    "next_track": 0xB5,
    "previous_track": 0xB6,
}


def effect(name="solid", color=None, **options):
    out = {
        "name": name,
        "color": color or [30, 80, 160],
        "speed": 1.0,
        "duration": 1.0,
        "direction": "right",
    }
    out.update(options)
    return out


def new_profile(name="Untitled", profile_id="untitled"):
    return {
        "schema_version": VERSION,
        "id": profile_id,
        "name": name,
        "target_os": "windows",
        "keyboard_layout": {"windows": "de_windows", "macos": "de_macos"},
        "orientation": 0,
        "brightness": 0.5,
        "lighting": effect("solid", [10, 10, 10]),
        "keys": [
            {
                "id": i,
                "label": "Key %d" % (i + 1),
                "bindings": {"windows": {}, "macos": {}},
                "lighting": {},
                "hold_ms": 500,
                "repeat_ms": 0,
            }
            for i in range(16)
        ],
    }


def independent(action):
    return action.get("type", "none") in DEVICE_ACTIONS and all(
        independent(a) for a in action.get("steps", [])
    )


def validate_effect(value):
    if not isinstance(value, dict) or value.get("name") not in EFFECTS:
        raise ValueError("Unknown lighting preset")
    color = value.get("color", [])
    if len(color) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in color):
        raise ValueError("Colors must contain three values from 0 to 255")
    if not 0.05 <= value.get("speed", 1) <= 20 or not 0.05 <= value.get("duration", 1) <= 60:
        raise ValueError("Effect speed/duration is out of range")
    if value.get("direction", "right") not in ("right", "left", "down", "up"):
        raise ValueError("Unknown direction")


def validate_action(action, depth=0):
    if depth > 4 or not isinstance(action, dict):
        raise ValueError("Action nesting exceeds four levels")
    kind = action.get("type", "none")
    if kind not in DEVICE_ACTIONS + HOST_ACTIONS:
        raise ValueError("Unknown action: %s" % kind)
    if kind == "hotkey":
        from keypad_core.keycodes import chord

        chord(action.get("keys", []))
    if kind == "media" and action.get("code") not in MEDIA:
        raise ValueError("Unknown media control")
    if kind == "text" and (
        not isinstance(action.get("text", ""), str) or len(action.get("text", "")) > 2048
    ):
        raise ValueError("Text must contain at most 2048 characters")
    if kind == "delay" and not 0 <= action.get("ms", 0) <= 60000:
        raise ValueError("Delay must be between 0 and 60000 ms")
    if kind == "sequence":
        steps = action.get("steps", [])
        if not isinstance(steps, list) or len(steps) > 32:
            raise ValueError("Sequences support at most 32 steps")
        for step in steps:
            validate_action(step, depth + 1)
    if kind == "effect":
        validate_effect(action.get("effect", {}))
    if kind in HOST_ACTIONS and not isinstance(action.get("binding_id", ""), str):
        raise ValueError("Invalid computer binding ID")


def validate(profile):
    if not isinstance(profile, dict) or profile.get("schema_version") != VERSION:
        raise ValueError("Unsupported profile version")
    for field in ("id", "name"):
        if not isinstance(profile.get(field), str) or not 1 <= len(profile[field]) <= 80:
            raise ValueError("Invalid profile %s" % field)
    if profile.get("target_os") not in ("windows", "macos"):
        raise ValueError("Choose Windows or macOS")
    if profile.get("orientation", 0) not in (0, 90, 180, 270):
        raise ValueError("Invalid orientation")
    if not 0 <= profile.get("brightness", 0.5) <= 1:
        raise ValueError("Brightness must be between 0 and 1")
    for os_name in ("windows", "macos"):
        if profile.get("keyboard_layout", {}).get(os_name) not in ("us", "de_windows", "de_macos"):
            raise ValueError("Unsupported keyboard layout")
    validate_effect(profile.get("lighting", {}))
    keys = profile.get("keys", [])
    if len(keys) != 16 or [k.get("id") for k in keys] != list(range(16)):
        raise ValueError("A profile must contain the 16 ordered keys (0–15)")
    for key in keys:
        if not isinstance(key.get("label", ""), str) or len(key.get("label", "")) > 80:
            raise ValueError("Key labels must be at most 80 characters")
        if not 100 <= key.get("hold_ms", 500) <= 10000 or not 0 <= key.get("repeat_ms", 0) <= 10000:
            raise ValueError("Invalid hold/repeat timing")
        if 0 < key.get("repeat_ms", 0) < 50:
            raise ValueError("Repeat interval must be at least 50 ms")
        for os_name, bindings in key.get("bindings", {}).items():
            if os_name not in ("windows", "macos") or not isinstance(bindings, dict):
                raise ValueError("Invalid OS bindings")
            for trigger, action in bindings.items():
                if trigger not in ("press", "hold", "release"):
                    raise ValueError("Invalid trigger")
                validate_action(action)
        for state, style in key.get("lighting", {}).items():
            if state not in ("idle", "pressed", "on", "off", "running", "success", "error"):
                raise ValueError("Unknown key state")
            validate_effect(style)
        for action in key.get("alternate", {}).values():
            validate_action(action)
    for action in profile.get("legacy_actions", {}).values():
        validate_action(action)
    return profile
