"""Build download packages and smoke-test the actual extracted/mounted payloads."""

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import runpy
import struct
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("macOS-arm64", "macOS-x86_64", "Windows-x64")


def project_version():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), "Use a three-part release version"
    assert version == runpy.run_path(str(ROOT / "keypad_studio/__init__.py"))["__version__"]
    tag = os.environ.get("RELEASE_TAG", "")
    if tag and tag != "v" + version:
        raise ValueError("The release tag must match the project version: v" + version)
    return version


def asset_name(target):
    return "Keypad-Studio-%s-%s.%s" % (
        project_version(),
        target,
        "zip" if target == "Windows-x64" else "dmg",
    )


def verify_payload(app, target):
    if target.startswith("macOS"):
        resources = app / "Contents/Resources"
        binary = app / "Contents/MacOS/Keypad Studio"
        info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
        assert info["CFBundleShortVersionString"] == project_version()
        assert info["CFBundleVersion"] == project_version()
        assert (resources / info["CFBundleIconFile"]).read_bytes() == (
            ROOT / "keypad_studio/assets/app-icon.icns"
        ).read_bytes()
        arch = subprocess.check_output(["lipo", "-archs", str(binary)], text=True).strip()
        assert arch == target.removeprefix("macOS-"), arch
    else:
        resources = app / "_internal"
        binary = app / "Keypad Studio.exe"
        raw = binary.read_bytes()
        header = struct.unpack_from("<I", raw, 0x3C)[0]
        assert raw[:2] == b"MZ" and raw[header : header + 4] == b"PE\0\0"
        assert struct.unpack_from("<H", raw, header + 4)[0] == 0x8664
    manifest = json.loads((resources / "firmware-bundle/manifest.json").read_text())
    for name, expected in manifest["files"].items():
        file = resources / "firmware-bundle" / name
        assert hashlib.sha256(file.read_bytes()).hexdigest() == expected, name
    assert (resources / "keypad_studio/assets/app-icon.png").read_bytes() == (
        ROOT / "keypad_studio/assets/app-icon.png"
    ).read_bytes()
    assert (resources / "licenses/LUCIDE-LICENSE.txt").is_file()
    with tempfile.TemporaryDirectory(prefix="keypad-smoke-") as temporary:
        temporary = Path(temporary)
        environment = dict(os.environ)
        environment.update(KEYPAD_HOME=str(temporary / "settings"), QT_QPA_PLATFORM="offscreen")
        environment["PATH"] = (
            str(Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32")
            if sys.platform == "win32"
            else "/usr/bin:/bin"
        )
        screenshot = temporary / "editor.png"
        result = subprocess.run(
            [str(binary), "--no-device", "--theme", "dark", "--screenshot", str(screenshot)],
            cwd=temporary,
            env=environment,
            capture_output=True,
            text=True,
            timeout=45,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert screenshot.is_file() and screenshot.stat().st_size > 10000
        downloads = temporary / "downloads"
        downloads.mkdir()
        with zipfile.ZipFile(downloads / "example.zip", "w") as archive:
            archive.writestr("test.txt", "Packaged helper works")
        extracted = temporary / "extracted"
        result = subprocess.run(
            [str(binary), "--zip-helper", str(downloads), str(extracted)],
            cwd=temporary,
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert (extracted / "test.txt").read_text() == "Packaged helper works"
    print(
        "Verified payload, native architecture, firmware, icon, GUI exit, and ZIP helper:", target
    )


def package(target):
    expected = {"macOS-arm64": "arm64", "macOS-x86_64": "x86_64", "Windows-x64": "AMD64"}
    assert platform.machine() == expected[target], (platform.machine(), target)
    output = ROOT / "release-assets"
    output.mkdir(exist_ok=True)
    asset = output / asset_name(target)
    with tempfile.TemporaryDirectory(prefix="keypad-package-") as temporary:
        temporary = Path(temporary)
        if target.startswith("macOS"):
            source = ROOT / "dist/Keypad Studio.app"
            staging = temporary / "staging"
            staging.mkdir()
            subprocess.run(["ditto", str(source), str(staging / source.name)], check=True)
            (staging / "Applications").symlink_to("/Applications")
            subprocess.run(
                [
                    "hdiutil",
                    "create",
                    "-ov",
                    "-volname",
                    "Keypad Studio",
                    "-srcfolder",
                    str(staging),
                    "-fs",
                    "HFS+",
                    "-format",
                    "UDZO",
                    str(asset),
                ],
                check=True,
            )
            mount = temporary / "mounted"
            mount.mkdir()
            subprocess.run(
                [
                    "hdiutil",
                    "attach",
                    "-readonly",
                    "-nobrowse",
                    "-mountpoint",
                    str(mount),
                    str(asset),
                ],
                check=True,
            )
            try:
                verify_payload(mount / "Keypad Studio.app", target)
            finally:
                subprocess.run(["hdiutil", "detach", str(mount)], check=True)
        else:
            source = ROOT / "dist/Keypad Studio"
            with zipfile.ZipFile(asset, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for file in sorted(source.rglob("*")):
                    if file.is_file():
                        archive.write(file, file.relative_to(source.parent).as_posix())
            with zipfile.ZipFile(asset) as archive:
                assert archive.testzip() is None
                archive.extractall(temporary)
            verify_payload(temporary / "Keypad Studio", target)
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    asset.with_suffix(asset.suffix + ".sha256").write_text(digest + "  " + asset.name + "\n")
    print("Release asset:", asset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=TARGETS)
    parser.add_argument("--check-version", action="store_true")
    arguments = parser.parse_args()
    if arguments.check_version:
        print("Version:", project_version())
    elif arguments.target:
        package(arguments.target)
    else:
        parser.error("Choose --target or --check-version")
