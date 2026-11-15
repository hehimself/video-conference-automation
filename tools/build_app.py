"""Run on each target operating system; PyInstaller does not cross-compile."""

import subprocess
import sys
import plistlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if not (root / "build/firmware-bundle/manifest.json").exists():
    raise SystemExit("Build the firmware bundle first: python tools/build_firmware.py")
command = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    "--distpath",
    str(root / "dist"),
    "--workpath",
    str(root / "build/pyinstaller"),
    str(root / "packaging/keypad_studio.spec"),
]
subprocess.run(command, cwd=root, check=True)
if sys.platform == "darwin":
    contents = root / "dist/Keypad Studio.app/Contents"
    info = plistlib.loads((contents / "Info.plist").read_bytes())
    bundled_icon = contents / "Resources" / info["CFBundleIconFile"]
    if bundled_icon.read_bytes() != (root / "keypad_studio/assets/app-icon.icns").read_bytes():
        raise SystemExit("The app bundle does not contain the correct Finder icon")
    print("Verified the Finder app icon and bundle metadata")
