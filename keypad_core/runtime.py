"""Nonblocking key scanning, lighting and device-side action scheduler."""

from keypad_core.schema import validate, independent, MEDIA
from keypad_core.keycodes import chord, character
from keypad_core.effects import frame


def steps(action):
    if action.get("type") == "sequence":
        for child in action.get("steps", []):
            for leaf in steps(child):
                yield leaf
    else:
        yield action


class Runtime:
    def __init__(self, hardware, profile, emit=None):
        self.hw = hardware
        self.emit = emit or (lambda event: None)
        self.now = 0
        self.diag_until = 0
        self.companion_until = 0
        self.preview_until = 0
        self.saved_profile = profile
        self.set_profile(profile)

    def set_profile(self, profile):
        validate(profile)
        self.hw.release_all()
        self.profile = profile
        self.jobs = {}
        self.external_jobs = {}
        self.alternating = set()
        self.raw = [False] * 16
        self.stable = [False] * 16
        self.changed = [self.now] * 16
        self.pressed = {}
        self.hold_sent = set()
        self.repeat_at = {}
        self.states = {}
        self.overlays = {}
        self.key_effects = {}
        self.progress = {}
        self.board_effect = None
        self.last_frame = -1
        self.stats_start = self.now
        self.last_scan = self.now
        self.scans = 0
        self.frames = 0
        self.max_gap = 0
        if not hasattr(self, "sequence"):
            self.sequence = 0
        # Keys held during a profile change must be released before firing.
        self.inhibited = set(i for i, v in enumerate(self.hw.read_keys()) if v)

    def diagnostic(self, seconds=15):
        previously = bool(self.diag_until)
        self.diag_until = self.now + min(30, max(0, seconds)) if seconds else 0
        if not previously or not seconds:
            for key, ident in self.external_jobs.items():
                self.emit(
                    {
                        "type": "execution_done",
                        "key": key,
                        "execution_id": ident,
                        "ok": False,
                        "error": "Diagnostic mode changed",
                    }
                )
            self.jobs.clear()
            self.external_jobs.clear()
            self.hw.release_all()
        if previously and not seconds:
            self.inhibited.update(self.pressed)

    def feedback(self, key, state, progress=None):
        if not 0 <= key < 16 or state not in ("on", "off", "running", "success", "error"):
            raise ValueError("Invalid feedback")
        if state in ("on", "off"):
            self.states[key] = state
        else:
            self.overlays[key] = (state, self.now)
        if progress is not None:
            if not 0 <= progress <= 1:
                raise ValueError("Invalid progress")
            self.progress[key] = progress
        elif state in ("success", "error"):
            self.progress.pop(key, None)

    def trigger(self, key_id, trigger):
        action = (
            self.profile["keys"][key_id]
            .get("bindings", {})
            .get(self.profile["target_os"], {})
            .get(trigger, {"type": "none"})
        )
        if action.get("type") == "none":
            return
        alternate = self.profile["keys"][key_id].get("alternate", {}).get(self.profile["target_os"])
        if alternate and trigger == "press":
            if key_id in self.alternating:
                action = alternate
                self.alternating.remove(key_id)
            else:
                self.alternating.add(key_id)
        self.sequence += 1
        event = {
            "type": "action",
            "event_id": self.sequence,
            "key": key_id,
            "trigger": trigger,
            "owner": "device" if independent(action) else "host",
            "profile_id": self.profile["id"],
        }
        if not independent(action):
            if self.companion_until > self.now:
                self.overlays[key_id] = ("running", self.now)
                self.emit(event)
            else:
                self.overlays[key_id] = ("error", self.now)
            return
        if key_id not in self.jobs:
            self.jobs[key_id] = (self.perform(key_id, action), self.now)
            self.emit(event)

    def perform(self, key, action):
        layout = self.profile["keyboard_layout"][self.profile["target_os"]]
        for step in steps(action):
            kind = step.get("type", "none")
            if kind == "delay":
                yield step.get("ms", 0) / 1000
            elif kind == "hotkey":
                codes = list(chord(step["keys"]))
                if layout != "us":
                    codes = [29 if c == 28 else 28 if c == 29 else c for c in codes]
                self.hw.tap(tuple(codes))
                yield 0.01
            elif kind == "text":
                # Validate the entire string before emitting any of it.
                text = step.get("text", "")
                for char in text:
                    character(char, layout)
                for char in text:
                    for codes in character(char, layout):
                        self.hw.tap(codes)
                        yield 0.008
            elif kind == "media":
                self.hw.media(MEDIA[step["code"]])
                yield 0.01
            elif kind == "toggle":
                self.states[key] = "off" if self.states.get(key) == "on" else "on"
                self.emit({"type": "state", "key": key, "state": self.states[key]})
            elif kind == "effect":
                style = step["effect"]
                self.emit(
                    {
                        "type": "effect",
                        "key": key,
                        "effect": style,
                        "scope": step.get("scope", "board"),
                    }
                )
                if step.get("scope", "board") == "board":
                    self.board_effect = (style, self.now, (key % 4, key // 4))
                else:
                    self.key_effects[key] = (style, self.now)

    def tick(self, now):
        self.scans += 1
        self.max_gap = max(self.max_gap, now - self.last_scan)
        self.last_scan = now
        self.now = now
        if self.preview_until and now >= self.preview_until:
            self.preview_until = 0
            self.set_profile(self.saved_profile)
        if self.diag_until and now >= self.diag_until:
            self.diag_until = 0
            self.inhibited.update(self.pressed)
        readings = self.hw.read_keys()
        for i, down in enumerate(readings):
            if down != self.raw[i]:
                self.raw[i] = down
                self.changed[i] = now
            if down != self.stable[i] and now - self.changed[i] >= 0.020:
                self.stable[i] = down
                self.emit({"type": "key", "key": i, "pressed": down})
                if down:
                    self.pressed[i] = now
                    self.repeat_at[i] = now + self.profile["keys"][i].get("hold_ms", 500) / 1000
                    if not self.diag_until and i not in self.inhibited:
                        self.trigger(i, "press")
                else:
                    self.pressed.pop(i, None)
                    self.hold_sent.discard(i)
                    if not self.diag_until and i not in self.inhibited:
                        self.trigger(i, "release")
                    self.inhibited.discard(i)
            if self.stable[i] and not self.diag_until and i not in self.inhibited:
                key = self.profile["keys"][i]
                if (
                    i not in self.hold_sent
                    and now - self.pressed[i] >= key.get("hold_ms", 500) / 1000
                ):
                    self.hold_sent.add(i)
                    self.trigger(i, "hold")
                if key.get("repeat_ms", 0) and now >= self.repeat_at[i]:
                    self.trigger(i, "press")
                    self.repeat_at[i] = now + key["repeat_ms"] / 1000
        for i in tuple(self.jobs):
            job, due = self.jobs[i]
            if now >= due:
                try:
                    delay = next(job)
                    self.jobs[i] = (job, now + (delay or 0))
                except StopIteration:
                    del self.jobs[i]
                    if i in self.external_jobs:
                        self.emit(
                            {
                                "type": "execution_done",
                                "key": i,
                                "execution_id": self.external_jobs.pop(i),
                                "ok": True,
                            }
                        )
                except Exception as exc:
                    self.hw.release_all()
                    del self.jobs[i]
                    self.overlays[i] = ("error", now)
                    self.emit({"type": "error", "key": i, "message": str(exc)})
                    if i in self.external_jobs:
                        self.emit(
                            {
                                "type": "execution_done",
                                "key": i,
                                "execution_id": self.external_jobs.pop(i),
                                "ok": False,
                                "error": str(exc),
                            }
                        )
        for i in tuple(self.overlays):
            state, start = self.overlays[i]
            if state == "running" and now >= self.companion_until:
                self.overlays[i] = ("error", now)
                self.progress.pop(i, None)
                continue
            if state != "running" and now - start >= 1.5:
                del self.overlays[i]
            elif state == "running" and now - start > 300:
                self.overlays[i] = ("error", now)
        if self.board_effect and now - self.board_effect[1] >= self.board_effect[0].get(
            "duration", 1
        ):
            self.board_effect = None
        for i in tuple(self.key_effects):
            style, start = self.key_effects[i]
            if now - start >= style.get("duration", 1):
                del self.key_effects[i]
        if now - self.last_frame >= 1 / 30:
            self.hw.write_leds(
                frame(
                    self.profile,
                    now,
                    self.pressed,
                    self.states,
                    self.overlays,
                    self.board_effect,
                    self.key_effects,
                    self.progress,
                )
            )
            self.last_frame = now
            self.frames += 1
