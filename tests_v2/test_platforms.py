from keypad_studio.platforms import script_command
from pathlib import Path


def test_script_interpreters_and_argument_order():
    assert script_command(
        {"path": "test.py", "arguments": ["hello world"], "interpreter_arguments": ["-u"]}, "macos"
    ) == ("python3", ["-u", "test.py", "hello world"])
    assert script_command({"path": "C:/test.ps1", "arguments": ["one"]}, "windows") == (
        "powershell.exe",
        ["-NoProfile", "-File", str(Path("C:/test.ps1")), "one"],
    )
    assert script_command({"path": "/bin/echo", "arguments": ["hello"]}, "macos") == (
        str(Path("/bin/echo")),
        ["hello"],
    )
