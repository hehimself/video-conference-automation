"""Firmware installation, private backups and BOOTSEL recovery helpers."""

import argparse
import datetime
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from keypad_core.schema import new_profile
from keypad_core.storage import ProfileStore

CP_VERSION = "10.3.1"


def resources():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "firmware-bundle"
    return Path(__file__).resolve().parents[1] / "build" / "firmware-bundle"


def backup(mount, directory):
    mount = Path(mount)
    if not (mount / "boot_out.txt").is_file():
        raise ValueError("CIRCUITPY is not mounted at the selected folder")
    directory = Path(directory) / datetime.datetime.now().strftime("pico-%Y%m%d-%H%M%S")
    directory.mkdir(parents=True, mode=0o700)
    directory.chmod(0o700)
    manifest = {}
    for source in mount.rglob("*"):
        if any(part.startswith(".") for part in source.relative_to(mount).parts):
            continue
        if source.is_file():
            target = directory / source.relative_to(mount)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o600)
            manifest[str(source.relative_to(mount))] = hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (directory / "manifest.json").chmod(0o600)
    return directory


def verify_bundle(bundle):
    manifest = json.loads((bundle / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        path = bundle / name
        if (
            not path.resolve().is_relative_to(bundle.resolve())
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError("Firmware bundle verification failed: " + name)
    return manifest


def install(mount, bundle=None):
    mount = Path(mount)
    bundle = Path(bundle or resources())
    verify_bundle(bundle)
    boot = (mount / "boot_out.txt").read_text()
    if "raspberry_pi_pico" not in boot or "rp2040" not in boot:
        raise ValueError("This install bundle is for the original RP2040 Raspberry Pi Pico")
    shutil.copytree(bundle / "lib", mount / "lib", dirs_exist_ok=True)
    shutil.copyfile(bundle / "hardware.py", mount / "hardware.py")
    if not (mount / "profile.a").exists() and not (mount / "profile.b").exists():
        profile = new_profile("Empty · configure in app", "empty")
        profile["target_os"] = "macos" if sys.platform == "darwin" else "windows"
        ProfileStore(str(mount)).save(json.dumps(profile, separators=(",", ":")).encode())
    for name in ("boot.py", "code.py"):
        shutil.copyfile(bundle / name, mount / name)
    for name in ("hardware.py", "boot.py", "code.py"):
        if (mount / name).read_bytes() != (bundle / name).read_bytes():
            raise ValueError("Firmware copy did not verify")


def console_command(port, command):
    import serial

    with serial.Serial(port, 115200, timeout=0.2, write_timeout=2) as connection:
        connection.write(b"\x03\x03")
        time.sleep(0.8)
        stopped = connection.read(8192)
        if b">>>" not in stopped:
            connection.write(b"\x03")
            time.sleep(0.5)
            stopped += connection.read(8192)
        if b">>>" not in stopped:
            raise RuntimeError("Could not reach the Pico console prompt")
        connection.reset_input_buffer()
        for statement in command.split("; "):
            connection.write(statement.encode("ascii") + b"\r")
            connection.flush()
            time.sleep(0.4)
            try:
                result = connection.read(8192)
            except serial.SerialException:
                if statement.endswith("reset()"):
                    return
                raise
            if b"Traceback" in result:
                raise RuntimeError("The Pico rejected the maintenance command")


def main():
    parser = argparse.ArgumentParser(
        description="Install Keypad Studio firmware. Back up first; use BOOTSEL to upgrade CircuitPython."
    )
    parser.add_argument("--mount", required=True, help="CIRCUITPY mount path")
    parser.add_argument("--console", required=True, help="CircuitPython CONSOLE serial port")
    parser.add_argument(
        "--backup-dir", required=True, help="Private backup folder outside the repository"
    )
    parser.add_argument("--bundle", type=Path, default=resources())
    parser.add_argument("--enter-bootloader", action="store_true")
    args = parser.parse_args()
    verify_bundle(args.bundle)
    saved = backup(args.mount, args.backup_dir)
    print("Private backup:", saved)
    if args.enter_bootloader:
        console_command(
            args.console,
            "import microcontroller; microcontroller.on_next_reset(microcontroller.RunMode.BOOTLOADER); microcontroller.reset()",
        )
        print(
            "Copy",
            args.bundle / ("circuitpython-%s-pico.uf2" % CP_VERSION),
            "to RPI-RP2, then rerun without --enter-bootloader.",
        )
    else:
        boot = (Path(args.mount) / "boot_out.txt").read_text()
        if "CircuitPython " + CP_VERSION not in boot:
            raise ValueError(
                "Upgrade to CircuitPython %s first (see docs/firmware.md)" % CP_VERSION
            )
        console_command(args.console, "import supervisor; supervisor.runtime.autoreload = False")
        install(args.mount, args.bundle)
        console_command(args.console, "import microcontroller; microcontroller.reset()")
        print("Installed. CIRCUITPY is hidden during normal use; open Keypad Studio to connect.")


if __name__ == "__main__":
    main()
