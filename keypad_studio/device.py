"""One serial owner, bounded RPC, reconnect without replaying queued actions."""

import base64
import json
import queue
import time
import sys
from copy import deepcopy
from PySide6.QtCore import QThread, Signal, QObject
from keypad_core.storage import digest
from keypad_core.schema import validate
from keypad_studio.profiles import encode


class DeviceWorker(QThread):
    connected = Signal(dict)
    disconnected = Signal(str)
    event = Signal(dict)
    completed = Signal(str, object)
    failed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.commands = queue.Queue()
        self.stopping = False
        self.diagnostic = False
        self.port = None
        self.serial = None
        self.buffer = bytearray()
        self.counter = 0
        self.info = None
        self.last_heartbeat = 0

    @staticmethod
    def ports():
        from serial.tools import list_ports

        return list(list_ports.comports())

    def candidates(self):
        if self.port:
            return [self.port]
        ports = self.ports()
        matched = [
            p.device
            for p in ports
            if any(s in (p.interface or "").lower() for s in ("data", "cdc2", "keypad"))
        ]
        if matched:
            return matched
        # A stock console-only Pico must not receive configuration traffic.
        groups = {}
        for p in ports:
            if p.vid in (0x239A, 0x2E8A):
                groups.setdefault(p.serial_number, []).append(p.device)
        return [sorted(group)[-1] for group in groups.values() if len(group) >= 2]

    def submit(self, name, args=None):
        if not self.info:
            self.failed.emit(name, "Connect a Pico with Keypad Studio firmware first")
            return
        self.commands.put((name, deepcopy(args or {})))

    def line(self, deadline):
        while time.monotonic() < deadline and not self.stopping:
            if b"\n" in self.buffer:
                line, _, self.buffer = self.buffer.partition(b"\n")
                try:
                    return json.loads(line)
                except (ValueError, UnicodeError):
                    continue
            data = self.serial.read(512)
            self.buffer.extend(data)
            if len(self.buffer) > 65536:
                raise ValueError("Device response exceeded buffer limit")
        return None

    def rpc(self, cmd, args=None):
        self.counter += 1
        ident = self.counter
        raw = (
            json.dumps(
                {"v": 1, "id": ident, "cmd": cmd, "args": args or {}}, separators=(",", ":")
            ).encode()
            + b"\n"
        )
        self.serial.write(raw)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            message = self.line(deadline)
            if message is None:
                break
            if message.get("id") == ident:
                if not message.get("ok"):
                    raise ValueError(message.get("error", "Device rejected command"))
                return message.get("result", {})
            if "type" in message:
                self.event.emit(message)
        raise TimeoutError("The Pico did not reply")

    def read_profile(self):
        meta = self.rpc("read_begin")
        raw = bytearray()
        for offset in range(0, meta["size"], 384):
            raw.extend(base64.b64decode(self.rpc("read_chunk", {"offset": offset})["data"]))
        if len(raw) != meta["size"] or digest(raw) != meta["sha256"]:
            raise ValueError("Downloaded profile checksum mismatch")
        profile = validate(json.loads(raw))
        self.info.update(meta)
        return {"profile": profile, "meta": meta}

    def write_profile(self, args, preview=False):
        raw = encode(args["profile"])
        self.rpc(
            "write_begin",
            {
                "size": len(raw),
                "sha256": digest(raw),
                "revision": args["revision"],
                "preview": preview,
            },
        )
        for offset in range(0, len(raw), 384):
            self.rpc(
                "write_chunk",
                {"offset": offset, "data": base64.b64encode(raw[offset : offset + 384]).decode()},
            )
        result = self.rpc("write_commit")
        if not preview:
            verified = self.read_profile()
            if verified["profile"] != args["profile"]:
                raise ValueError("Read-back differs from saved profile")
            result = verified
        return result

    def run(self):
        import serial

        next_attempt = 0
        while not self.stopping:
            try:
                if self.serial is None:
                    if time.monotonic() < next_attempt:
                        self.msleep(100)
                        continue
                    next_attempt = time.monotonic() + 2
                    for port in self.candidates():
                        try:
                            self.serial = serial.Serial(
                                port,
                                115200,
                                timeout=0.05,
                                write_timeout=1,
                                exclusive=True if sys.platform != "win32" else None,
                            )
                            self.buffer = bytearray()
                            info = self.rpc("hello")
                            if info.get("protocol") != 1:
                                raise ValueError("Unsupported device protocol")
                            self.info = info
                            # Drain all pre-connection telemetry before activating the companion.
                            self.serial.reset_input_buffer()
                            self.buffer = bytearray()
                            self.connected.emit(dict(info))
                            self.completed.emit("read", self.read_profile())
                            self.last_heartbeat = 0
                            break
                        except Exception:
                            if self.serial:
                                self.serial.close()
                            self.serial = None
                            self.info = None
                    if self.serial is None:
                        self.msleep(100)
                        continue
                if time.monotonic() - self.last_heartbeat > 1:
                    self.rpc("heartbeat", {"diagnostic": self.diagnostic})
                    self.last_heartbeat = time.monotonic()
                try:
                    name, args = self.commands.get_nowait()
                except queue.Empty:
                    name = None
                if name:
                    try:
                        if name == "read":
                            result = self.read_profile()
                        elif name in ("save", "preview"):
                            result = self.write_profile(args, name == "preview")
                        else:
                            result = self.rpc(name, args)
                        self.completed.emit(name, result)
                    except ValueError as exc:
                        if name == "execute":
                            self.event.emit(
                                {
                                    "type": "execution_done",
                                    "key": args["key"],
                                    "execution_id": args["execution_id"],
                                    "ok": False,
                                    "error": str(exc),
                                }
                            )
                        else:
                            self.failed.emit(name, str(exc))
                else:
                    message = self.line(time.monotonic() + 0.08)
                    if message and "type" in message:
                        self.event.emit(message)
            except Exception as exc:
                self.info = None
                if self.serial:
                    self.serial.close()
                self.serial = None
                while not self.commands.empty():
                    try:
                        self.commands.get_nowait()
                    except queue.Empty:
                        break
                self.disconnected.emit(str(exc))
        if self.serial:
            self.serial.close()

    def stop(self):
        self.stopping = True
        self.wait(4000)
