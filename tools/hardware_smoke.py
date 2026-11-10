"""Opt-in real-Pico checks. Saves a harmless test profile, then restores the original."""

import argparse
import base64
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serial
from keypad_core.storage import digest
from keypad_studio.profiles import encode
from keypad_studio.presets import current_pico
from keypad_studio.install import console_command


class Client:
    def __init__(self, port):
        self.connection = serial.Serial(
            port,
            115200,
            timeout=0.1,
            write_timeout=2,
            exclusive=True if sys.platform != "win32" else None,
        )
        self.ident = 0
        self.events = []

    def close(self):
        self.connection.close()

    def rpc(self, cmd, args=None):
        self.ident += 1
        self.connection.write(
            json.dumps({"v": 1, "id": self.ident, "cmd": cmd, "args": args or {}}).encode() + b"\n"
        )
        end = time.monotonic() + 5
        while time.monotonic() < end:
            line = self.connection.readline()
            if not line:
                continue
            event = json.loads(line)
            if event.get("id") == self.ident:
                if not event.get("ok"):
                    raise ValueError(event.get("error"))
                return event["result"]
            self.events.append(event)
        raise TimeoutError(cmd)

    def read(self):
        meta = self.rpc("read_begin")
        raw = b"".join(
            base64.b64decode(self.rpc("read_chunk", {"offset": i})["data"])
            for i in range(0, meta["size"], 384)
        )
        assert digest(raw) == meta["sha256"]
        return json.loads(raw), meta

    def write(self, profile, revision, preview=False):
        raw = encode(profile)
        self.rpc(
            "write_begin",
            {"size": len(raw), "sha256": digest(raw), "revision": revision, "preview": preview},
        )
        for i in range(0, len(raw), 384):
            self.rpc(
                "write_chunk", {"offset": i, "data": base64.b64encode(raw[i : i + 384]).decode()}
            )
        return self.rpc("write_commit")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--console", required=True)
    parser.add_argument("--report", default="build/hardware-report.json")
    args = parser.parse_args()
    client = Client(args.port)
    original = None
    report = {}
    try:
        report["hello"] = client.rpc("hello")
        client.rpc("diagnostic", {"enabled": True})
        original, meta = client.read()
        test = current_pico()
        test["id"] = "hardware-validation"
        test["name"] = "Hardware validation"
        test["target_os"] = "macos" if sys.platform == "darwin" else "windows"

        def disable(action):
            if action.get("type") == "sequence":
                for child in action.get("steps", []):
                    disable(child)
            else:
                action["type"] = "none"

        for key in test["keys"]:
            for bindings in key["bindings"].values():
                for action in bindings.values():
                    disable(action)
            for action in key.get("alternate", {}).values():
                disable(action)
        saved = client.write(test, meta["revision"])
        actual, meta = client.read()
        assert actual == test
        report["saved_bytes"] = len(encode(test))
        report["readback"] = True
        preview = json.loads(json.dumps(test))
        preview["name"] = "Temporary preview"
        preview["lighting"]["name"] = "rainbow"
        client.write(preview, meta["revision"], preview=True)
        assert client.read()[0] == test
        client.rpc("preview_stop")
        report["preview_preserves_saved_profile"] = True
        try:
            client.write(test, 0)
        except ValueError:
            report["stale_revision_rejected"] = True
        else:
            raise AssertionError("Stale revision was accepted")
        client.close()
        console_command(args.console, "import microcontroller; microcontroller.reset()")
        time.sleep(1)
        end = time.monotonic() + 10
        while True:
            try:
                client = Client(args.port)
                hello = client.rpc("hello")
                break
            except Exception:
                try:
                    client.close()
                except Exception:
                    pass
                if time.monotonic() > end:
                    raise
                time.sleep(0.3)
        assert hello["session"] != report["hello"]["session"] and client.read()[0] == test
        report["restart_persistence"] = True
        try:
            client.rpc("stats", {"reset": True})
            time.sleep(3)
            report["idle_performance"] = client.rpc("stats")
        except ValueError:
            pass
    finally:
        if original is not None:
            try:
                _, meta = client.read()
                client.write(original, meta["revision"])
                assert client.read()[0] == original
                report["original_profile_restored"] = True
            finally:
                client.close()
    path = Path(args.report)
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
