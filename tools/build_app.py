"""Run on each target operating system; PyInstaller does not cross-compile."""

import subprocess
import sys
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
    "--windowed",
    "--onedir",
    "--name",
    "Keypad Studio",
    "--paths",
    str(root),
    "--add-data",
    str(root / "build/firmware-bundle") + ":firmware-bundle",
    "--hidden-import",
    "keypad_studio.zip_helper",
    "--hidden-import",
    "pyautogui",
]
if sys.platform == "darwin":
    command.extend(["--osx-bundle-identifier", "com.keypadstudio.desktop"])
else:
    command.extend(["--hidden-import", "pywinauto", "--hidden-import", "pycaw.pycaw"])
command.append(str(root / "tools/desktop_entry.py"))
subprocess.run(command, cwd=root, check=True)
