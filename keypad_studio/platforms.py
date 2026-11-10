"""Small native helpers, isolated from the editor and firmware."""

import ctypes
from pathlib import Path


def mac_accessibility_trusted():
    services = ctypes.CDLL(
        "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
    )
    check = services.AXIsProcessTrusted
    check.argtypes = []
    check.restype = ctypes.c_bool
    return bool(check())


def script_command(config, os_name):
    path = str(Path(config["path"]).expanduser())
    program = config.get("executable")
    prefix = config.get("interpreter_arguments", [])
    arguments = config.get("arguments", [])
    if not program:
        suffix = Path(path).suffix.lower()
        if suffix == ".py":
            program = "python3" if os_name == "macos" else "python"
        elif suffix == ".ps1":
            program = "pwsh" if os_name == "macos" else "powershell.exe"
        elif suffix in (".sh", ".zsh", ".bash") and os_name == "macos":
            program = "/bin/zsh"
        else:
            return path, arguments
    if (
        Path(program).name.lower() in ("pwsh", "pwsh.exe", "powershell", "powershell.exe")
        and not prefix
    ):
        prefix = ["-NoProfile", "-File"]
    return program, prefix + [path] + arguments
