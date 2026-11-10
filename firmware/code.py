"""Keypad Studio firmware entry point. Install with keypad-firmware."""

import storage

if storage.getmount("/").readonly:
    # Maintenance mode intentionally runs no key actions.
    print("Keypad Studio maintenance mode. Reconnect after updating files.")
else:
    import time
    import json
    import gc
    import os
    import binascii
    import microcontroller
    import usb_cdc
    from hardware import Hardware
    from keypad_core.schema import new_profile
    from keypad_core.storage import ProfileStore
    from keypad_core.runtime import Runtime
    from keypad_core.protocol import Protocol, MAX_LINE

    port = usb_cdc.data
    if port is None:
        raise RuntimeError("Data port is disabled; install boot.py and reconnect")
    port.timeout = 0
    port.write_timeout = 0
    outgoing = []

    def emit(event):
        # Unplugging or a slow host must never stop scanning or HID actions.
        if port.connected and len(outgoing) < 32:
            event["session"] = session
            outgoing.append(json.dumps(event).encode() + b"\n")

    session = binascii.hexlify(os.urandom(8)).decode()
    hardware = Hardware()
    store = ProfileStore("")
    profile = store.load() or new_profile("Empty · configure in app", "empty")
    runtime = Runtime(hardware, profile, emit)
    del profile
    protocol = Protocol(runtime, store, session)
    incoming = bytearray()
    pending = b""
    last_gc = 0
    discard = False
    connected = False
    while True:
        now = time.monotonic()
        try:
            runtime.tick(now)
            if connected and not port.connected:
                outgoing.clear()
                pending = b""
                incoming = bytearray()
                protocol.upload = None
                runtime.companion_until = 0
            connected = port.connected
            if port.in_waiting:
                data = port.read(min(port.in_waiting, 256))
                for byte in data:
                    if byte == 10:
                        if incoming and not discard:
                            try:
                                request = json.loads(incoming)
                                reply = protocol.handle(request)
                            except Exception as exc:
                                reply = {"id": None, "ok": False, "error": str(exc)}
                            # Replies take priority over telemetry.
                            outgoing.insert(0, json.dumps(reply).encode() + b"\n")
                        incoming = bytearray()
                        discard = False
                    elif len(incoming) < MAX_LINE and not discard:
                        incoming.append(byte)
                    else:
                        discard = True
            if port.connected:
                if not pending and outgoing:
                    pending = outgoing.pop(0)
                if pending:
                    written = port.write(pending) or 0
                    pending = pending[written:]
            if now - last_gc > 5:
                gc.collect()
                last_gc = now
        except Exception as exc:
            hardware.release_all()
            print("Keypad runtime:", exc)
            runtime.jobs.clear()
