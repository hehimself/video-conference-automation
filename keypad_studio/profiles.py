import json
import os
import uuid
import sys
from pathlib import Path
from copy import deepcopy
from keypad_core.schema import validate, MAX_PROFILE_BYTES
from keypad_studio.presets import starters


def encode(profile):
    validate(profile)
    raw = json.dumps(profile, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_PROFILE_BYTES:
        raise ValueError("This profile exceeds the Pico's 16 KiB profile limit")
    return raw


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class Library:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.directory = self.root / "profiles"
        self.directory.mkdir(exist_ok=True)
        self.settings_path = self.root / "computer-settings.json"
        self.settings = (
            json.loads(self.settings_path.read_text())
            if self.settings_path.exists()
            else {"bindings": {}}
        )
        if not any(self.directory.glob("*.json")):
            for profile in starters():
                profile["target_os"] = "macos" if sys.platform == "darwin" else "windows"
                self.save(profile)

    def all(self):
        profiles = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                profiles.append(validate(json.loads(path.read_text(encoding="utf-8"))))
            except (ValueError, KeyError, TypeError):
                continue
        return sorted(profiles, key=lambda p: (p["id"] != "current-pico", p["name"].lower()))

    def save(self, profile):
        validate(profile)
        # Never use imported profile IDs directly as filesystem paths.
        import hashlib

        filename = hashlib.sha256(profile["id"].encode()).hexdigest()[:32] + ".json"
        atomic_json(self.directory / filename, profile)

    def duplicate(self, profile, name=None):
        copy = deepcopy(profile)
        copy["id"] = uuid.uuid4().hex
        copy["name"] = name or profile["name"] + " copy"
        self.save(copy)
        return copy

    def save_settings(self):
        atomic_json(self.settings_path, self.settings)

    def binding(self, ident, os_name):
        return self.settings.get("bindings", {}).get(ident, {}).get(os_name, {})

    def set_binding(self, ident, os_name, value):
        self.settings.setdefault("bindings", {}).setdefault(ident, {})[os_name] = value
        self.save_settings()
