"""Two checksummed slots with bounded reads for the Pico's small heap."""

import json
import hashlib
import binascii
import os
from keypad_core.schema import validate, MAX_PROFILE_BYTES


def digest(raw):
    return binascii.hexlify(hashlib.new("sha256", raw).digest()).decode("ascii")


class ProfileStore:
    def __init__(self, root):
        self.root = root.rstrip("/")
        self.revision = 0
        self.slot = None

    def path(self, slot):
        return self.root + "/profile." + slot

    def open_raw(self, slot=None):
        path = self.path(slot or self.slot)
        handle = open(path, "rb")
        try:
            line = handle.readline()
            header = json.loads(line)
            if not isinstance(header, dict):
                raise ValueError("Invalid profile header")
            size = os.stat(path)[6] - len(line)
            if not 0 < size <= MAX_PROFILE_BYTES or header.get("size", size) != size:
                raise ValueError("Invalid profile size")
            if (
                type(header["revision"]) is not int
                or header["revision"] < 1
                or len(header["sha256"]) != 64
            ):
                raise ValueError("Invalid profile header")
            header["size"] = size
            header["header_size"] = len(line)
            return handle, header
        except Exception:
            handle.close()
            raise

    def read_slot(self, slot):
        handle, header = self.open_raw(slot)
        try:
            raw = handle.read(header["size"])
        finally:
            handle.close()
        if len(raw) != header["size"] or digest(raw) != header["sha256"]:
            raise ValueError("Profile checksum mismatch")
        return header["revision"], raw

    def load(self):
        candidates = []
        for slot in ("a", "b"):
            try:
                handle, header = self.open_raw(slot)
                handle.close()
                candidates.append((header["revision"], slot))
            except (OSError, ValueError, KeyError, TypeError):
                pass
        candidates.sort(reverse=True)
        for revision, slot in candidates:
            try:
                _, raw = self.read_slot(slot)
                profile = validate(json.loads(raw))
                self.revision, self.slot = revision, slot
                return profile
            except (OSError, ValueError, KeyError, TypeError):
                pass
        return None

    def raw(self):
        return self.read_slot(self.slot)[1] if self.slot else None

    def verify_slot(self, slot):
        handle, header = self.open_raw(slot)
        checksum = hashlib.new("sha256")
        count = 0
        try:
            while True:
                chunk = handle.read(384)
                if not chunk:
                    break
                count += len(chunk)
                checksum.update(chunk)
        finally:
            handle.close()
        if (
            count != header["size"]
            or binascii.hexlify(checksum.digest()).decode() != header["sha256"]
        ):
            raise ValueError("Saved profile did not verify")
        return header

    def save(self, raw, validated=False):
        if len(raw) > MAX_PROFILE_BYTES:
            raise ValueError("Profile exceeds device size limit")
        if not validated:
            validate(json.loads(raw))
        slot = "b" if self.slot == "a" else "a"
        revision = self.revision + 1
        header = {"revision": revision, "sha256": digest(raw), "size": len(raw)}
        with open(self.path(slot), "wb") as handle:
            handle.write(json.dumps(header).encode() + b"\n")
            handle.write(raw)
            handle.flush()
        verified = self.verify_slot(slot)
        if verified["revision"] != revision:
            raise ValueError("Saved revision did not verify")
        self.revision, self.slot = revision, slot
        return revision
