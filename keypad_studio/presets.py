"""Reviewed starter layouts. No credentials or personal script paths belong here."""

from copy import deepcopy
from keypad_core.schema import new_profile, effect


def hotkey(*keys):
    return {"type": "hotkey", "keys": list(keys)}


def sequence(*actions):
    return {"type": "sequence", "steps": list(actions)}


def toggle(action):
    return sequence(action, {"type": "toggle"})


def host(kind, ident, **settings):
    out = {"type": kind, "binding_id": ident}
    out.update(settings)
    return out


def legacy_launch(command):
    return sequence(
        hotkey("win", "r"),
        {"type": "delay", "ms": 150},
        {"type": "text", "text": "PowerShell\n"},
        {"type": "delay", "ms": 1000},
        {"type": "text", "text": command + "\n"},
    )


def set_key(profile, index, label, win=None, mac=None, color=None, repeat=False, state=False):
    key = profile["keys"][index - 1]
    key["label"] = label
    key["bindings"] = {
        "windows": {"press": win or {"type": "none"}},
        "macos": {"press": mac or {"type": "none"}},
    }
    key["repeat_ms"] = 100 if repeat else 0
    if color:
        key["lighting"]["idle"] = effect("solid", color)
    if state:
        key["lighting"].update(
            {"on": effect("solid", [255, 30, 20]), "off": effect("solid", [0, 180, 70])}
        )


def current_pico():
    p = new_profile("Current Pico", "current-pico")
    animation = {"type": "effect", "scope": "board", "effect": effect("rainbow", duration=2)}
    set_key(
        p,
        1,
        "Startup script",
        sequence(host("run_script", "startup"), animation),
        sequence(host("run_script", "startup"), animation),
    )
    set_key(p, 2, "Lock computer", hotkey("win", "l"), hotkey("ctrl", "cmd", "q"), [40, 10, 0])
    set_key(
        p,
        3,
        "ChatGPT",
        host("open_url", "chatgpt", url="https://chatgpt.com"),
        host("open_url", "chatgpt", url="https://chatgpt.com"),
        [20, 0, 20],
    )
    for i, code, label in (
        (4, "volume_up", "Volume +"),
        (8, "volume_down", "Volume −"),
        (6, "play_pause", "Play / Pause"),
        (12, "mute", "Output mute"),
    ):
        action = {"type": "media", "code": code}
        if i == 12:
            action = toggle(action)
        set_key(
            p,
            i,
            label,
            deepcopy(action),
            deepcopy(action),
            [20, 20, 0] if i in (4, 8) else [0, 0, 50] if i == 6 else [20, 0, 0],
            repeat=i in (4, 8),
            state=i == 12,
        )
    set_key(p, 5, "Unassigned")
    set_key(
        p,
        7,
        "Sound-test script",
        host("run_script", "sound-test"),
        host("run_script", "sound-test"),
        [0, 30, 0],
    )
    set_key(
        p,
        9,
        "Teams · hand",
        toggle(hotkey("ctrl", "shift", "k")),
        toggle(hotkey("cmd", "shift", "k")),
        [0, 0, 100],
        state=True,
    )
    set_key(
        p,
        10,
        "Type text · set up",
        sequence(
            {"type": "effect", "effect": effect("heartbeat", [255, 0, 0], duration=2)},
            {"type": "text", "text": ""},
        ),
        sequence(
            {"type": "effect", "effect": effect("heartbeat", [255, 0, 0], duration=2)},
            {"type": "text", "text": ""},
        ),
    )
    set_key(
        p,
        11,
        "Red wipe",
        {"type": "effect", "effect": effect("ripple", [255, 0, 0], duration=1.5)},
        {"type": "effect", "effect": effect("ripple", [255, 0, 0], duration=1.5)},
    )
    set_key(
        p,
        13,
        "Teams · microphone",
        toggle(hotkey("ctrl", "shift", "m")),
        toggle(hotkey("cmd", "shift", "m")),
        [0, 200, 0],
        state=True,
    )
    set_key(p, 14, "Minimize / Restore", {"type": "sequence", "steps": [hotkey("win", "m")]}, None)
    # Alternate shortcuts implement minimize / restore without guessing window state.
    p["keys"][13]["alternate"] = {"windows": hotkey("win", "shift", "m")}
    set_key(
        p,
        15,
        "Teams · sharing",
        hotkey("ctrl", "shift", "e"),
        hotkey("cmd", "shift", "e"),
        [0, 40, 80],
    )
    set_key(
        p,
        16,
        "Teams · hang up",
        sequence(
            hotkey("ctrl", "shift", "h"),
            {"type": "effect", "effect": effect("fade", [255, 0, 0], duration=2)},
        ),
        sequence(
            hotkey("cmd", "shift", "h"),
            {"type": "effect", "effect": effect("fade", [255, 0, 0], duration=2)},
        ),
    )
    p["legacy_actions"] = {
        "startup": legacy_launch(".\\startup_script.ps1"),
        "sound-test": legacy_launch(".\\sound_test.ps1"),
    }
    return p


def classic_conference():
    p = new_profile("Classic Conference", "classic-conference")
    focus = lambda name: host("focus_app", name.lower(), app=name)
    call = lambda name, keys: sequence(focus(name), hotkey(*keys), {"type": "toggle"})
    set_key(
        p,
        1,
        "Startup sound",
        sequence(host("play_sound", "startup-sound"), focus("Teams"), focus("Discord")),
        sequence(host("play_sound", "startup-sound"), focus("Teams"), focus("Discord")),
    )
    for i, code in ((2, "volume_up"), (6, "volume_down")):
        a = {"type": "media", "code": code}
        set_key(
            p, i, "Volume +" if i == 2 else "Volume −", a, deepcopy(a), [10, 10, 0], repeat=True
        )
    for i, app, delta in (
        (3, "Discord", 0.05),
        (7, "Discord", -0.05),
        (4, "Teams", 0.05),
        (8, "Teams", -0.05),
    ):
        set_key(
            p,
            i,
            app + " volume " + ("+" if delta > 0 else "−"),
            host("app_volume", app.lower() + "-volume", app=app, delta=delta),
            None,
            [10, 0, 64] if app == "Discord" else [1, 0, 64],
        )
    set_key(p, 5, "Unassigned")
    set_key(
        p,
        9,
        "Teams · hand",
        call("Teams", ["ctrl", "shift", "k"]),
        call("Teams", ["cmd", "shift", "k"]),
        [40, 20, 0],
        state=True,
    )
    set_key(
        p,
        10,
        "Extract latest ZIP",
        host("extract_zip", "downloads"),
        host("extract_zip", "downloads"),
    )
    set_key(p, 11, "Unassigned")
    set_key(p, 12, "Unassigned")
    set_key(
        p,
        13,
        "Teams · microphone",
        call("Teams", ["ctrl", "shift", "m"]),
        call("Teams", ["cmd", "shift", "m"]),
        state=True,
    )
    set_key(
        p,
        14,
        "Discord · microphone",
        call("Discord", ["ctrl", "shift", "m"]),
        call("Discord", ["cmd", "shift", "m"]),
        state=True,
    )
    set_key(
        p,
        15,
        "Discord · deafen",
        call("Discord", ["ctrl", "shift", "d"]),
        call("Discord", ["cmd", "shift", "d"]),
        state=True,
    )
    set_key(
        p,
        16,
        "Switch microphones",
        sequence(
            focus("Teams"),
            hotkey("ctrl", "shift", "m"),
            focus("Discord"),
            hotkey("ctrl", "shift", "m"),
        ),
        sequence(
            focus("Teams"),
            hotkey("cmd", "shift", "m"),
            focus("Discord"),
            hotkey("cmd", "shift", "m"),
        ),
    )
    return p


def starters():
    return [current_pico(), classic_conference()]
