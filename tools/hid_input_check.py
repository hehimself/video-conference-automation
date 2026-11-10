"""Opt-in Mac hardware text check; emits HID only into this process's focused field."""

import argparse, json, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit
from tools.hardware_smoke import Client

parser = argparse.ArgumentParser()
parser.add_argument("--port", required=True)
args = parser.parse_args()
app = QApplication([])
window = QWidget()
window.setWindowTitle("Keypad hardware input check")
window.resize(650, 160)
layout = QVBoxLayout(window)
layout.addWidget(QLabel("Checking USB keyboard output in this dedicated field…"))
field = QLineEdit()
layout.addWidget(field)
expected = "aAzZyY 123 !? @\\[]{}|~ äöüÄÖÜß ' #"
client = Client(args.port)
hello = client.rpc("hello")
profile, meta = client.read()
if profile["target_os"] != "macos" or profile["keyboard_layout"]["macos"] != "de_macos":
    raise SystemExit("Save a German Mac target before this check")
client.rpc("diagnostic", {"enabled": True})
window.show()
window.raise_()
window.activateWindow()
field.setFocus()
from AppKit import NSApplication, NSWorkspace

NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
report = {}


def start():
    if (
        NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier() != os.getpid()
        or not field.hasFocus()
    ):
        report["error"] = "Input check window did not receive focus; no HID sent"
        finish()
        return
    client.rpc(
        "execute",
        {"key": 0, "execution_id": "text-check", "action": {"type": "text", "text": expected}},
    )
    QTimer.singleShot(1800, finish)


def finish():
    report.update(expected=expected, received=field.text(), matches=field.text() == expected)
    Path("build/hid-input-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False))
    client.close()
    app.quit()


QTimer.singleShot(1500, start)
app.exec()
if not report.get("matches"):
    raise SystemExit(1)
