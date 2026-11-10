"""Bounded JSON-lines RPC; previews never write flash."""

import json
import binascii
import gc
from keypad_core.schema import MAX_PROFILE_BYTES, validate, validate_action, independent
from keypad_core.storage import digest

PROTOCOL_VERSION = 1
MAX_LINE = 1400


class Protocol:
    def __init__(self, runtime, store, session="boot"):
        self.runtime, self.store, self.session = runtime, store, session
        self.upload = None
        self.download = None

    def handle(self, request):
        gc.collect()
        ident = request.get("id")
        try:
            if request.get("v") != PROTOCOL_VERSION:
                raise ValueError("Unsupported protocol version")
            result = self.command(request.get("cmd"), request.get("args", {}))
            return {"id": ident, "ok": True, "result": result}
        except Exception as exc:
            self.upload = None
            return {"id": ident, "ok": False, "error": str(exc)}

    def command(self, cmd, args):
        rt = self.runtime
        if cmd == "stats":
            gc.collect()
            if args.get("reset"):
                rt.stats_start = rt.now
                rt.last_scan = rt.now
                rt.scans = 0
                rt.frames = 0
                rt.max_gap = 0
            return {
                "elapsed": rt.now - rt.stats_start,
                "scans": rt.scans,
                "frames": rt.frames,
                "max_gap_ms": rt.max_gap * 1000,
                "free_heap": gc.mem_free() if hasattr(gc, "mem_free") else None,
            }
        if cmd == "hello":
            rt.companion_until = 0
            return {
                "protocol": 1,
                "firmware": "0.1.0",
                "session": self.session,
                "profile_id": rt.saved_profile["id"],
                "revision": self.store.revision,
                "max_profile_bytes": MAX_PROFILE_BYTES,
                "keys": 16,
                "fps": 30,
                "saved": self.store.slot is not None,
                "event_floor": rt.sequence,
            }
        if cmd == "heartbeat":
            rt.companion_until = rt.now + 5
            if args.get("diagnostic"):
                rt.diagnostic(15)
            return {"diagnostic": bool(rt.diag_until)}
        if cmd == "diagnostic":
            rt.diagnostic(15 if args.get("enabled", True) else 0)
            return {}
        if cmd == "feedback":
            rt.feedback(int(args["key"]), args["state"], args.get("progress"))
            return {}
        if cmd == "execute":
            key = int(args["key"])
            action = args["action"]
            validate_action(action)
            if not 0 <= key < 16 or not independent(action):
                raise ValueError("Only device actions can be executed through this command")
            if key in rt.jobs:
                raise ValueError("Key action is still running")
            rt.jobs[key] = (rt.perform(key, action), rt.now)
            rt.external_jobs[key] = args["execution_id"]
            return {"execution_id": args["execution_id"]}
        if cmd == "cancel":
            key = int(args["key"])
            rt.jobs.pop(key, None)
            ident = rt.external_jobs.pop(key, None)
            rt.hw.release_all()
            if ident:
                rt.emit(
                    {
                        "type": "execution_done",
                        "key": key,
                        "execution_id": ident,
                        "ok": False,
                        "error": "Cancelled",
                    }
                )
            return {}
        if cmd == "read_begin":
            self.close_download()
            gc.collect()
            if self.store.slot:
                handle, meta = self.store.open_raw()
                self.download = {"handle": handle, "meta": meta}
            else:
                raw = json.dumps(rt.saved_profile, separators=(",", ":")).encode()
                meta = {"size": len(raw), "sha256": digest(raw), "header_size": 0}
                self.download = {"raw": raw, "meta": meta}
            return {
                "size": meta["size"],
                "sha256": meta["sha256"],
                "revision": self.store.revision,
            }
        if cmd == "read_chunk":
            if self.download is None:
                raise ValueError("Start a read first")
            offset = int(args["offset"])
            if not 0 <= offset < self.download["meta"]["size"]:
                raise ValueError("Invalid download offset")
            if "handle" in self.download:
                handle = self.download["handle"]
                handle.seek(self.download["meta"]["header_size"] + offset)
                chunk = handle.read(384)
            else:
                chunk = self.download["raw"][offset : offset + 384]
            if offset + len(chunk) >= self.download["meta"]["size"]:
                self.close_download()
            return {"data": binascii.b2a_base64(chunk).decode().strip()}
        if cmd == "write_begin":
            self.close_download()
            gc.collect()
            size = int(args["size"])
            if not 0 < size <= MAX_PROFILE_BYTES:
                raise ValueError("Profile is too large")
            if args.get("revision") != self.store.revision:
                raise ValueError("Device changed; read its profile before saving")
            self.upload = {
                "size": size,
                "sha256": args["sha256"],
                "raw": bytearray(size),
                "received": 0,
                "preview": bool(args.get("preview")),
            }
            return {}
        if cmd == "write_chunk":
            upload = self.upload
            if not upload or args["offset"] != upload["received"]:
                raise ValueError("Invalid upload offset")
            data = binascii.a2b_base64(args["data"])
            if len(data) > 384 or upload["received"] + len(data) > upload["size"]:
                raise ValueError("Upload exceeds declared size")
            offset = upload["received"]
            upload["raw"][offset : offset + len(data)] = data
            upload["received"] += len(data)
            return {"offset": upload["received"]}
        if cmd == "write_commit":
            upload, self.upload = self.upload, None
            if (
                not upload
                or upload["received"] != upload["size"]
                or digest(upload["raw"]) != upload["sha256"]
            ):
                raise ValueError("Incomplete or invalid upload")
            profile = validate(json.loads(upload["raw"]))
            rt.hw.release_all()
            if upload["preview"]:
                rt.diagnostic(30)
                rt.set_profile(profile)
                rt.preview_until = rt.now + 30
            else:
                self.store.save(upload["raw"], validated=True)
                rt.saved_profile = profile
                rt.preview_until = 0
                rt.set_profile(profile)
            return {"revision": self.store.revision, "sha256": upload["sha256"]}
        if cmd == "preview_stop":
            rt.preview_until = 0
            rt.set_profile(rt.saved_profile)
            return {}
        if cmd == "maintenance":
            rt.hw.release_all()
            # Only firmware can supply this callback; never execute arbitrary USB code.
            callback = getattr(rt.hw, "maintenance", None)
            if callback:
                callback()
                return {}
            raise ValueError("Maintenance mode is not available")
        raise ValueError("Unknown command")

    def close_download(self):
        if self.download and "handle" in self.download:
            self.download["handle"].close()
        self.download = None
