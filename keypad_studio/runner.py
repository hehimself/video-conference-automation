"""Asynchronous host actions. Commands come from local configuration, never USB."""

import json
import os
import sys
import zipfile
import uuid
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QProcess, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from keypad_core.schema import independent, MEDIA
from keypad_core.runtime import steps


def extract_latest(source, destination):
    source, destination = Path(source).expanduser(), Path(destination).expanduser()
    files = list(source.glob("*.zip"))
    if not files:
        raise ValueError("No ZIP files found in the selected downloads folder")
    latest = max(files, key=lambda p: p.stat().st_mtime)
    root = destination.resolve()
    with zipfile.ZipFile(latest) as archive:
        for entry in archive.infolist():
            target = (root / entry.filename).resolve()
            if (
                not target.is_relative_to(root)
                or (entry.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise ValueError("ZIP contains an unsafe path or symbolic link")
        archive.extractall(root)
    return root


class Runner(QObject):
    feedback = Signal(int, str)
    log = Signal(str)
    state = Signal(int, str)
    progress = Signal(int, float)
    effect = Signal(int, dict)

    def __init__(self, library, device, parent=None):
        super().__init__(parent)
        self.library = library
        self.device = device
        self.runs = {}
        self.os_name = "macos" if sys.platform == "darwin" else "windows"
        self.device.event.connect(self.device_event)

    def device_event(self, event):
        if event.get("type") != "execution_done":
            return
        key = event["key"]
        run = self.runs.get(key)
        if not run or run.get("execution_id") != event.get("execution_id"):
            return
        run.pop("execution_id", None)
        if event.get("ok"):
            self.next(key, run)
        else:
            self.finish(key, run, event.get("error", "Device action failed"))

    def start(self, key, action, profile_id="test"):
        if key in self.runs:
            self.log.emit("Key %d is already running" % (key + 1))
            return
        run = {
            "steps": list(steps(action)),
            "process": None,
            "pending": "",
            "key": key,
            "profile": profile_id,
            "token": object(),
        }
        self.runs[key] = run
        run["show_feedback"] = not independent(action) or any(
            step.get("type") not in ("none", "effect", "toggle", "delay") for step in run["steps"]
        )
        if run["show_feedback"]:
            self.feedback.emit(key, "running")
        self.next(key, run)

    def finish(self, key, run, error=None):
        if self.runs.get(key) is not run:
            return
        self.runs.pop(key, None)
        if run.get("process"):
            run["process"].deleteLater()
        if run.get("player"):
            run["player"].stop()
            run["player"].deleteLater()
            run["audio"].deleteLater()
        if error or run["show_feedback"]:
            self.feedback.emit(key, "error" if error else "success")
        if error:
            self.log.emit("Key %d: %s" % (key + 1, error))

    def cancel(self, key):
        if self.device.info:
            self.device.submit("cancel", {"key": key})
        run = self.runs.get(key)
        if run:
            process = run.get("process")
            if process:
                process.kill()
            self.finish(key, run, "Cancelled")

    def next(self, key, run):
        if self.runs.get(key) is not run:
            return
        if not run["steps"]:
            self.finish(key, run)
            return
        action = run["steps"].pop(0)
        kind = action.get("type", "none")
        config = dict(action)
        config.update(self.library.binding(action.get("binding_id", ""), self.os_name))
        resume = lambda: self.next(key, run)
        try:
            if kind == "delay":
                QTimer.singleShot(action.get("ms", 0), resume)
                return
            if independent(action):
                if self.device.info and kind != "none":
                    ident = uuid.uuid4().hex
                    run["execution_id"] = ident
                    self.device.submit(
                        "execute", {"key": key, "action": action, "execution_id": ident}
                    )
                    QTimer.singleShot(
                        90000,
                        lambda: (
                            self.finish(key, run, "Device action timed out")
                            if self.runs.get(key) is run and run.get("execution_id") == ident
                            else None
                        ),
                    )
                    return
                if kind == "toggle":
                    self.state.emit(key, "toggle")
                elif kind == "effect":
                    self.effect.emit(key, action)
                elif kind != "none":
                    if not self.device.info:
                        import pyautogui

                        if sys.platform == "darwin":
                            from keypad_studio.platforms import mac_accessibility_trusted

                            if not mac_accessibility_trusted():
                                raise ValueError(
                                    "Allow Keypad Studio in System Settings → Privacy & Security → Accessibility to test computer actions"
                                )
                        if kind == "hotkey":
                            pyautogui.hotkey(
                                *[
                                    (
                                        "command"
                                        if n in ("cmd", "win", "gui") and self.os_name == "macos"
                                        else "win" if n in ("cmd", "gui") else n
                                    )
                                    for n in action["keys"]
                                ]
                            )
                        elif kind == "text":
                            self.paste(action.get("text", ""))
                        elif kind == "media":
                            pyautogui.press(
                                {
                                    "volume_up": "volumeup",
                                    "volume_down": "volumedown",
                                    "mute": "volumemute",
                                    "play_pause": "playpause",
                                    "next_track": "nexttrack",
                                    "previous_track": "prevtrack",
                                }[action["code"]]
                            )
                QTimer.singleShot(60, resume)
                return
            if kind == "run_script":
                path = config.get("path", "")
                if not path or not Path(path).expanduser().is_file():
                    raise ValueError("Choose a script file in Computer Settings for this action")
                from keypad_studio.platforms import script_command

                program, args = script_command(config, self.os_name)
                self.process(key, run, program, args, config)
                return
            if kind == "open_app":
                app = config.get("app", "")
                if not app:
                    raise ValueError("Choose an application")
                program, args = (
                    ("/usr/bin/open", ["-a", app])
                    if self.os_name == "macos"
                    else (app, config.get("arguments", []))
                )
                self.process(key, run, program, args, config)
                return
            if kind == "focus_app":
                app = config.get("app", "")
                if self.os_name == "macos":
                    self.process(
                        key,
                        run,
                        "/usr/bin/osascript",
                        [
                            "-e",
                            "on run argv\ntell application (item 1 of argv) to activate\nend run",
                            app,
                        ],
                        config,
                    )
                    return
                import re
                from pywinauto import Desktop

                windows = Desktop(backend="uia").windows(
                    title_re=".*" + re.escape(app) + ".*", visible_only=True
                )
                if not windows:
                    raise ValueError("Application window not found: " + app)
                windows[0].set_focus()
                QTimer.singleShot(250, resume)
                return
            if kind == "open_url":
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl

                url = QUrl(config.get("url", ""))
                if url.scheme() not in ("http", "https", "mailto"):
                    raise ValueError("Use an http, https, or mailto URL")
                if not QDesktopServices.openUrl(url):
                    raise ValueError("Could not open URL")
            elif kind == "play_sound":
                path = config.get("path", "")
                if not Path(path).is_file():
                    raise ValueError("Choose a sound file in Computer Settings")
                from PySide6.QtCore import QUrl

                player = QMediaPlayer(self)
                audio = QAudioOutput(self)
                player.setAudioOutput(audio)
                run["player"], run["audio"] = player, audio
                player.setSource(QUrl.fromLocalFile(path))
                player.play()
                player.errorOccurred.connect(
                    lambda *args: self.finish(key, run, player.errorString())
                )
                player.mediaStatusChanged.connect(
                    lambda status: resume() if status == QMediaPlayer.EndOfMedia else None
                )
                return
            elif kind == "app_volume":
                if self.os_name != "windows":
                    raise ValueError("Individual application volume is available on Windows only")
                from pycaw.pycaw import AudioUtilities

                found = False
                for session in AudioUtilities.GetAllSessions():
                    if (
                        session.Process
                        and config.get("app", "").lower() in session.Process.name().lower()
                    ):
                        volume = session.SimpleAudioVolume
                        volume.SetMasterVolume(
                            max(0, min(1, volume.GetMasterVolume() + config.get("delta", 0.05))),
                            None,
                        )
                        found = True
                if not found:
                    raise ValueError("No active audio session found for this application")
            elif kind == "extract_zip":
                if not config.get("source") or not config.get("destination"):
                    raise ValueError("Choose downloads and extraction folders in Computer Settings")
                # Extraction happens in a helper process so large archives never freeze the editor.
                args = (
                    ["--zip-helper"]
                    if getattr(sys, "frozen", False)
                    else ["-m", "keypad_studio.zip_helper"]
                ) + [config["source"], config["destination"]]
                self.process(key, run, sys.executable, args, config)
                return
            else:
                raise ValueError("Unsupported action: " + kind)
            QTimer.singleShot(0, resume)
        except Exception as exc:
            self.finish(key, run, str(exc))

    def paste(self, text):
        from PySide6.QtWidgets import QApplication
        import pyautogui

        clipboard = QApplication.clipboard()
        previous = clipboard.text()
        clipboard.setText(text)
        pyautogui.hotkey("command" if self.os_name == "macos" else "ctrl", "v")
        QTimer.singleShot(
            500, lambda: clipboard.setText(previous) if clipboard.text() == text else None
        )

    def process(self, key, run, program, args, config):
        process = QProcess(self)
        run["process"] = process
        run["pending"] = ""
        if config.get("working_directory"):
            process.setWorkingDirectory(config["working_directory"])
        from PySide6.QtCore import QProcessEnvironment

        env = QProcessEnvironment.systemEnvironment()
        env.insert("KEYPAD_KEY_ID", str(key))
        env.insert("KEYPAD_PROFILE_ID", run["profile"])
        env.insert("KEYPAD_OS", self.os_name)
        process.setProcessEnvironment(env)
        process.readyReadStandardOutput.connect(
            lambda: self.output(
                key, run, bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
            )
        )
        process.readyReadStandardError.connect(
            lambda: self.log.emit(
                bytes(process.readAllStandardError()).decode("utf-8", "replace")[:4096]
            )
        )
        process.errorOccurred.connect(lambda error: self.finish(key, run, process.errorString()))

        def done(code, status):
            if self.runs.get(key) is not run:
                return
            self.output(key, run, "\n")
            if code or status == QProcess.CrashExit:
                self.finish(key, run, "Process exited with code %d" % code)
            else:
                run["process"] = None
                process.deleteLater()
                self.next(key, run)

        process.finished.connect(done)
        process.start(program, args)
        timeout = QTimer(process)
        timeout.setSingleShot(True)
        timeout.timeout.connect(
            lambda: (
                (process.kill(), self.finish(key, run, "Action timed out"))
                if self.runs.get(key) is run and run.get("process") is process
                else None
            )
        )
        timeout.start(max(1, min(3600, int(config.get("timeout", 60)))) * 1000)

    def output(self, key, run, text):
        run["pending"] += text
        if len(run["pending"]) > 8192:
            self.log.emit(run["pending"][:4096])
            run["pending"] = ""
        while "\n" in run["pending"]:
            line, run["pending"] = run["pending"].split("\n", 1)
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("type") == "state" and event.get("state") in ("on", "off"):
                    self.state.emit(key, event["state"])
                    continue
                if event.get("type") == "progress" and 0 <= float(event["value"]) <= 1:
                    self.progress.emit(key, float(event["value"]))
                    continue
            except (ValueError, TypeError, KeyError, AttributeError):
                pass
            self.log.emit(line)
