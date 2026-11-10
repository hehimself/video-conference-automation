"""Build a complete install bundle from pinned official upstream releases."""

import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CP_VERSION = "10.3.1"
HID_VERSION = "6.1.4"
CP_URL = (
    "https://downloads.circuitpython.org/bin/raspberry_pi_pico/en_US/adafruit-circuitpython-raspberry_pi_pico-en_US-%s.uf2"
    % CP_VERSION
)
HID_URL = (
    "https://github.com/adafruit/Adafruit_CircuitPython_HID/archive/refs/tags/%s.zip" % HID_VERSION
)


def build(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("boot.py", "code.py", "hardware.py"):
        shutil.copyfile(ROOT / "firmware" / name, destination / name)
    shutil.copytree(
        ROOT / "keypad_core",
        destination / "lib" / "keypad_core",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    uf2 = destination / ("circuitpython-%s-pico.uf2" % CP_VERSION)
    if not uf2.exists():
        with urllib.request.urlopen(CP_URL, timeout=60) as response:
            uf2.write_bytes(response.read())
    cache = ROOT / "build" / ("adafruit-hid-%s.zip" % HID_VERSION)
    cache.parent.mkdir(exist_ok=True)
    if not cache.exists():
        with urllib.request.urlopen(HID_URL, timeout=60) as response:
            cache.write_bytes(response.read())
    with zipfile.ZipFile(cache) as archive:
        for entry in archive.infolist():
            parts = Path(entry.filename).parts
            if (
                len(parts) >= 3
                and parts[1] == "adafruit_hid"
                and not entry.is_dir()
                and entry.filename.endswith(".py")
            ):
                target = destination / "lib" / Path(*parts[1:])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(entry))
            if len(parts) == 2 and parts[1] == "LICENSE":
                (destination / "HID-LICENSE.txt").write_bytes(archive.read(entry))
    files = {
        str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in destination.rglob("*")
        if p.is_file() and p.name != "manifest.json"
    }
    manifest = {
        "circuitpython": CP_VERSION,
        "hid": HID_VERSION,
        "sources": {"circuitpython": CP_URL, "hid": HID_URL},
        "files": files,
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Firmware bundle:", destination)
    print("Verified files:", len(files))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "build" / "firmware-bundle"))
    args = parser.parse_args()
    build(args.output)
