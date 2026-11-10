import base64
import json
from copy import deepcopy
import pytest
from keypad_core.schema import (
    new_profile,
    validate,
    effect,
    independent,
    validate_action,
    MAX_PROFILE_BYTES,
)
from keypad_core.keycodes import character
from keypad_core.effects import frame
from keypad_core.storage import ProfileStore, digest
from keypad_core.runtime import Runtime
from keypad_core.protocol import Protocol
from keypad_studio.presets import starters
from keypad_studio.profiles import encode, Library


class Hardware:
    def __init__(self):
        self.keys = [False] * 16
        self.taps = []
        self.media_codes = []
        self.frames = []
        self.releases = 0

    def read_keys(self):
        return self.keys[:]

    def tap(self, codes):
        self.taps.append(codes)

    def media(self, code):
        self.media_codes.append(code)

    def release_all(self):
        self.releases += 1

    def write_leds(self, colors):
        self.frames.append(colors)


def rig(profile=None):
    hardware = Hardware()
    events = []
    runtime = Runtime(hardware, profile or new_profile(), events.append)
    return hardware, runtime, events


def action(profile, key, action, trigger="press"):
    profile["keys"][key]["bindings"]["windows"][trigger] = action


def ticks(runtime, start, end):
    now = start
    while now < end:
        runtime.tick(now)
        now += 0.005


def test_starters_round_trip_and_no_saved_text_literal():
    for profile in starters():
        assert validate(json.loads(encode(profile))) == profile
        assert len(encode(profile)) < MAX_PROFILE_BYTES
    assert starters()[0]["keys"][9]["bindings"]["windows"]["press"]["steps"][-1]["text"] == ""
    assert starters()[1]["keys"][9]["bindings"]["windows"]["press"]["type"] == "extract_zip"


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(schema_version=99),
        lambda p: p.update(target_os="guess"),
        lambda p: p.update(brightness=5),
        lambda p: p["keys"].pop(),
        lambda p: p["keys"][0].update(repeat_ms=1),
        lambda p: action(p, 0, {"type": "hotkey", "keys": ["arbitrary"]}),
        lambda p: action(p, 0, {"type": "sequence", "steps": [{"type": "none"}] * 33}),
        lambda p: p["lighting"].update(color=[-1, 0, 0]),
    ],
)
def test_invalid_profiles_rejected(change):
    p = new_profile()
    change(p)
    with pytest.raises((ValueError, TypeError)):
        validate(p)


def test_debounce_edges_hold_repeat_and_other_keys():
    p = new_profile()
    action(p, 0, {"type": "media", "code": "volume_up"})
    p["keys"][0]["repeat_ms"] = 100
    action(p, 1, {"type": "hotkey", "keys": ["ctrl", "m"]})
    h, r, events = rig(p)
    h.keys[0] = True
    ticks(r, 0, 0.01)
    h.keys[0] = False
    ticks(r, 0.01, 0.04)
    assert not h.media_codes
    h.keys[0] = True
    ticks(r, 0.04, 0.3)
    h.keys[1] = True
    ticks(r, 0.3, 0.8)
    assert len(h.media_codes) >= 3 and (224, 16) in h.taps
    assert len([e for e in events if e["type"] == "key" and e["key"] == 0 and e["pressed"]]) == 1


def test_long_macro_and_animation_do_not_block_scan():
    p = new_profile()
    action(
        p,
        0,
        {
            "type": "sequence",
            "steps": [
                {"type": "effect", "effect": effect("rainbow", duration=3)},
                {"type": "delay", "ms": 1500},
                {"type": "hotkey", "keys": ["a"]},
            ],
        },
    )
    action(p, 1, {"type": "media", "code": "play_pause"})
    h, r, events = rig(p)
    h.keys[0] = True
    ticks(r, 0, 0.1)
    h.keys[1] = True
    ticks(r, 0.1, 0.3)
    assert h.media_codes == [205] and not h.taps and len(h.frames) > 5
    ticks(r, 0.3, 2)
    assert h.taps == [(4,)]


def test_diagnostic_suppresses_press_hold_release_until_released():
    p = new_profile()
    for trigger in ("press", "hold", "release"):
        action(p, 0, {"type": "hotkey", "keys": ["a"]}, trigger)
    h, r, _ = rig(p)
    r.diagnostic(1)
    h.keys[0] = True
    ticks(r, 0, 1.5)
    h.keys[0] = False
    ticks(r, 1.5, 1.7)
    assert h.taps == []
    h.keys[0] = True
    ticks(r, 1.7, 1.8)
    assert h.taps == [(4,)]


def test_diagnostic_refresh_does_not_cancel_explicit_test_job():
    h, r, _ = rig()
    r.diagnostic(15)
    r.jobs[0] = (
        r.perform(
            0,
            {
                "type": "sequence",
                "steps": [{"type": "delay", "ms": 1500}, {"type": "hotkey", "keys": ["a"]}],
            },
        ),
        0,
    )
    ticks(r, 0, 1)
    r.diagnostic(15)
    ticks(r, 1, 2)
    assert h.taps == [(4,)]


def test_host_action_has_one_owner_and_requires_live_lease():
    p = new_profile()
    action(
        p,
        0,
        {
            "type": "sequence",
            "steps": [
                {"type": "focus_app", "binding_id": "teams"},
                {"type": "hotkey", "keys": ["ctrl", "m"]},
            ],
        },
    )
    h, r, events = rig(p)
    r.trigger(0, "press")
    assert not events and not h.taps
    r.companion_until = 5
    r.trigger(0, "press")
    ticks(r, 0, 0.1)
    assert events[-1]["owner"] == "host" and not h.taps


def test_profile_change_releases_keys_and_inhibits_current_press():
    p = new_profile()
    action(p, 0, {"type": "hotkey", "keys": ["a"]})
    h, r, _ = rig(p)
    h.keys[0] = True
    r.set_profile(p)
    ticks(r, 0, 1)
    assert not h.taps
    h.keys[0] = False
    ticks(r, 1, 1.1)
    h.keys[0] = True
    ticks(r, 1.1, 1.2)
    assert h.taps == [(4,)]


def test_german_layouts_are_explicit_and_prevalidate_whole_text():
    assert character("@", "de_windows") == [(230, 20)]
    assert character("@", "de_macos") == [(226, 15)]
    assert character("\\", "de_macos") == [(226, 225, 36)]
    assert character("y", "de_windows") == [(29,)]
    assert character("'", "de_windows") == [(225, 49)]
    for char in "PowerShell .\\'Ordner' äöüÄÖÜß @[]{}|~\n":
        for layout in ("de_windows", "de_macos"):
            assert character(char, layout)
    h, r, events = rig()
    r.jobs[0] = (r.perform(0, {"type": "text", "text": "abc😀"}), 0)
    ticks(r, 0, 0.1)
    assert not h.taps and r.overlays[0][0] == "error"


def test_all_effects_bounded_and_status_restored():
    from keypad_core.schema import EFFECTS

    p = new_profile()
    p["keys"][0]["lighting"]["on"] = effect("solid", [255, 0, 0])
    for name in EFFECTS:
        p["lighting"] = effect(name)
        for time in (0, 0.1, 1, 10):
            colors = frame(p, time, states={0: "on"})
            assert len(colors) == 16 and colors[0] == (127, 0, 0)
            assert all(0 <= c <= 255 for rgb in colors for c in rgb)


def test_torn_save_recovers_previous_valid_slot(tmp_path):
    store = ProfileStore(str(tmp_path))
    p = new_profile()
    store.save(encode(p))
    p["name"] = "Second"
    store.save(encode(p))
    (tmp_path / "profile.b").write_bytes(b'{"revision":2}\ntruncated')
    restored = ProfileStore(str(tmp_path))
    assert restored.load()["name"] == "Untitled" and restored.revision == 1
    (tmp_path / "profile.a").write_bytes(b"bad")
    assert ProfileStore(str(tmp_path)).load() is None


def transfer(protocol, profile, revision=0, preview=False):
    raw = encode(profile)

    def rpc(cmd, args={}):
        out = protocol.handle({"v": 1, "id": 1, "cmd": cmd, "args": args})
        assert out["ok"], out
        return out["result"]

    rpc(
        "write_begin",
        {"size": len(raw), "sha256": digest(raw), "revision": revision, "preview": preview},
    )
    for offset in range(0, len(raw), 384):
        rpc(
            "write_chunk",
            {"offset": offset, "data": base64.b64encode(raw[offset : offset + 384]).decode()},
        )
    return rpc("write_commit")


def test_protocol_save_readback_preview_and_revision_conflict(tmp_path):
    h, r, _ = rig()
    store = ProfileStore(str(tmp_path))
    protocol = Protocol(r, store)
    p = starters()[0]
    transfer(protocol, p)
    assert store.load() == p and store.revision == 1
    other = starters()[1]
    transfer(protocol, other, 1, preview=True)
    assert r.profile == other and r.saved_profile == p and store.revision == 1
    ticks(r, 30, 31)
    assert r.profile == p
    out = protocol.handle(
        {
            "v": 1,
            "id": 3,
            "cmd": "write_begin",
            "args": {"size": 10, "sha256": "wrong", "revision": 0},
        }
    )
    assert not out["ok"]
    read = protocol.command("read_begin", {})
    assert read["revision"] == 1
    raw = b"".join(
        base64.b64decode(protocol.command("read_chunk", {"offset": offset})["data"])
        for offset in range(0, read["size"], 384)
    )
    assert json.loads(raw) == p and digest(raw) == read["sha256"]


def test_invalid_upload_and_protocol_do_not_change_saved_profile(tmp_path):
    h, r, _ = rig()
    store = ProfileStore(str(tmp_path))
    protocol = Protocol(r, store)
    transfer(protocol, starters()[0])
    before = store.raw()
    assert not protocol.handle({"v": 99, "cmd": "hello"})["ok"]
    protocol.command("write_begin", {"size": 3, "sha256": "wrong", "revision": 1})
    protocol.command("write_chunk", {"offset": 0, "data": base64.b64encode(b"bad").decode()})
    assert not protocol.handle({"v": 1, "cmd": "write_commit"})["ok"] and store.raw() == before


def test_connection_hello_resets_companion_and_advertises_event_floor(tmp_path):
    h, r, _ = rig()
    r.sequence = 50
    r.companion_until = 100
    hello = Protocol(r, ProfileStore(str(tmp_path))).command("hello", {})
    assert hello["event_floor"] == 50 and r.companion_until == 0


def test_external_execution_reports_completion(tmp_path):
    h, r, events = rig()
    protocol = Protocol(r, ProfileStore(str(tmp_path)))
    protocol.command(
        "execute", {"key": 0, "execution_id": "one", "action": {"type": "hotkey", "keys": ["a"]}}
    )
    ticks(r, 0, 0.1)
    assert h.taps == [(4,)] and events[-1]["execution_id"] == "one" and events[-1]["ok"]


def test_library_ids_cannot_escape_directory(tmp_path):
    library = Library(tmp_path)
    p = new_profile("Path test", "../../outside")
    library.save(p)
    assert len(library.all()) == 3 and not (tmp_path.parent / "outside.json").exists()
    library.set_binding("my-script", "macos", {"path": "/private/example.py"})
    assert b"/private/example.py" not in encode(p)


def test_key_effect_overrides_press_then_restores_state():
    p = new_profile()
    p["keys"][0]["lighting"]["on"] = effect("solid", [0, 255, 0])
    temporary = {0: (effect("solid", [255, 0, 0]), 0)}
    assert frame(p, 0.1, pressed={0: 0}, states={0: "on"}, key_effects=temporary)[0] == (127, 0, 0)
    assert frame(p, 2, states={0: "on"})[0] == (0, 127, 0)


def test_download_is_streamed_and_upload_is_preallocated(tmp_path):
    h, r, _ = rig()
    store = ProfileStore(str(tmp_path))
    protocol = Protocol(r, store)
    transfer(protocol, starters()[0])
    meta = protocol.command("read_begin", {})
    assert "handle" in protocol.download and "raw" not in protocol.download
    protocol.command("write_begin", {"size": 1000, "sha256": "pending", "revision": 1})
    assert (
        protocol.download is None
        and len(protocol.upload["raw"]) == 1000
        and protocol.upload["received"] == 0
    )
