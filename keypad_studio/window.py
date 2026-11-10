import json
import sys
import time
import uuid
from copy import deepcopy
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QSplitter,
    QTabWidget,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QScrollArea,
    QPlainTextEdit,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QFrame,
)
from keypad_core.schema import new_profile, validate, independent, effect
from keypad_core.runtime import steps
from keypad_studio.profiles import encode
from keypad_studio.widgets import Board, ActionEditor, EffectEditor, BindingDialog, button


class Window(QMainWindow):
    def __init__(self, library, device, runner):
        super().__init__()
        self.library = library
        self.device = device
        self.runner = runner
        self.setWindowTitle("Keypad Studio")
        self.resize(1370, 920)
        self.setMinimumSize(1150, 760)
        self.loading = True
        self.profile = None
        self.selected = 0
        self.dirty = False
        self.undo_stack = []
        self.redo_stack = []
        self.clipboard = None
        self.device_profile = None
        self.device_revision = None
        self.seen_events = set()
        self.session = None
        self.verified_revision = None
        self.pending_profile = None
        self.commit_timer = QTimer(self)
        self.commit_timer.setSingleShot(True)
        self.commit_timer.timeout.connect(self.capture)
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 20, 24, 12)
        outer.setSpacing(16)
        top = QHBoxLayout()
        title = QLabel("Keypad Studio")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch()
        self.connection = QLabel("○  Editor ready · Pico not connected")
        self.connection.setObjectName("connection")
        top.addWidget(self.connection)
        self.connect_button = button("Connection…", self.choose_port, top)
        outer.addLayout(top)
        button("Set up Pico…", self.setup_device, top)
        self.appearance = QComboBox()
        for label, value in (
            ("Dark gray", "dark"),
            ("Light", "light"),
            ("Follow system", "system"),
        ):
            self.appearance.addItem(label, value)
        self.appearance.setToolTip("Appearance · saved on this computer")
        self.appearance.setCurrentIndex(
            max(0, self.appearance.findData(library.settings.get("appearance", "dark")))
        )
        top.addWidget(self.appearance)
        toolbar = QHBoxLayout()
        button("Save locally", self.save_local, toolbar)
        button("Read from Pico", self.read_device, toolbar)
        self.preview_button = button("Preview on Pico", self.preview, toolbar)
        button("Stop preview", lambda: self.device.submit("preview_stop"), toolbar)
        toolbar.addStretch()
        self.saved_label = QLabel("Local profile")
        self.saved_label.setObjectName("muted")
        toolbar.addWidget(self.saved_label)
        self.save_device_button = button("Save to Pico", self.save_device, toolbar)
        self.save_device_button.setObjectName("primary")
        outer.addLayout(toolbar)
        split = QSplitter()
        outer.addWidget(split, 1)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 14, 0)
        heading = QLabel("YOUR PROFILES")
        heading.setObjectName("muted")
        left_layout.addWidget(heading)
        self.profiles = QListWidget()
        left_layout.addWidget(self.profiles, 1)
        self.profiles.currentRowChanged.connect(self.select_profile)
        row = QHBoxLayout()
        button("New", self.new_profile, row)
        button("Duplicate", self.duplicate, row)
        left_layout.addLayout(row)
        button("Rename", self.rename, left_layout)
        row = QHBoxLayout()
        button("Import", self.import_profile, row)
        button("Export", self.export_profile, row)
        left_layout.addLayout(row)
        note = QLabel(
            "The library stays on this computer.\nSave to Pico replaces its active profile."
        )
        note.setWordWrap(True)
        note.setObjectName("muted")
        left_layout.addWidget(note)
        split.addWidget(left)
        center = QWidget()
        middle = QVBoxLayout(center)
        middle.setContentsMargins(15, 0, 15, 0)
        self.profile_title = QLabel()
        self.profile_title.setObjectName("title")
        middle.addWidget(self.profile_title)
        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Saved target"))
        self.target = QComboBox()
        self.target.addItem("Windows", "windows")
        self.target.addItem("macOS", "macos")
        target_row.addWidget(self.target)
        self.layout_choice = QComboBox()
        for label, value in (
            ("German · Windows", "de_windows"),
            ("German · Mac", "de_macos"),
            ("US English", "us"),
        ):
            self.layout_choice.addItem(label, value)
        target_row.addWidget(self.layout_choice)
        middle.addLayout(target_row)
        self.board = Board()
        middle.addWidget(self.board, 1, Qt.AlignCenter)
        self.board.selected.connect(self.select_key)
        self.board.swapped.connect(self.swap)
        hint = QLabel("Click a key to edit · drag to swap · labels appear in this app only")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignCenter)
        middle.addWidget(hint)
        self.diagnostic = QCheckBox("Learn / diagnostic mode · suppress physical key actions")
        self.diagnostic.toggled.connect(self.set_diagnostic)
        middle.addWidget(self.diagnostic)
        button("Computer Settings…", self.computer_settings, middle)
        split.addWidget(center)
        tabs = QTabWidget()
        split.addWidget(tabs)
        key_content = QWidget()
        key_layout = QVBoxLayout(key_content)
        key_layout.setContentsMargins(12, 16, 0, 0)
        self.key_heading = QLabel("KEY 01")
        self.key_heading.setObjectName("muted")
        key_layout.addWidget(self.key_heading)
        form = QFormLayout()
        key_layout.addLayout(form)
        self.label = QLineEdit()
        self.label.setMaxLength(80)
        form.addRow("Label", self.label)
        self.trigger = QComboBox()
        self.trigger.addItems(["press", "hold", "release"])
        form.addRow("Trigger", self.trigger)
        self.action_editor = ActionEditor()
        key_layout.addWidget(self.action_editor)
        timing = QFormLayout()
        key_layout.addLayout(timing)
        self.hold = QSpinBox()
        self.hold.setRange(100, 10000)
        self.hold.setSuffix(" ms")
        timing.addRow("Hold after", self.hold)
        self.repeat = QSpinBox()
        self.repeat.setRange(0, 10000)
        self.repeat.setSpecialValueText("Off")
        self.repeat.setSuffix(" ms")
        self.repeat.setSingleStep(50)
        timing.addRow("Repeat press", self.repeat)
        controls = QHBoxLayout()
        button("Copy", self.copy_key, controls)
        button("Paste", self.paste_key, controls)
        button("Undo", self.undo, controls)
        key_layout.addLayout(controls)
        button("Test selected action", self.test_action, key_layout)
        button("Cancel action", lambda: self.runner.cancel(self.selected), key_layout)
        button("Use a legacy script-launch macro…", self.use_legacy, key_layout)
        note = QLabel(
            "Toggle colors are locally tracked. They do not verify the application's actual mute state."
        )
        note.setWordWrap(True)
        note.setObjectName("muted")
        key_layout.addWidget(note)
        key_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(key_content)
        tabs.addTab(scroll, "Action")
        lights = QWidget()
        light_layout = QVBoxLayout(lights)
        light_layout.setContentsMargins(12, 18, 0, 0)
        light_layout.addWidget(QLabel("KEY LIGHTING"))
        self.state_choice = QComboBox()
        self.state_choice.addItems(["idle", "pressed", "on", "off", "running", "success", "error"])
        light_layout.addWidget(self.state_choice)
        self.override = QCheckBox("Customize this state")
        light_layout.addWidget(self.override)
        self.key_effect = EffectEditor()
        light_layout.addWidget(self.key_effect)
        button("Preview local toggle", self.local_toggle, light_layout)
        light_layout.addSpacing(28)
        light_layout.addWidget(QLabel("WHOLE KEYPAD · IDLE"))
        self.board_style = EffectEditor()
        light_layout.addWidget(self.board_style)
        f = QFormLayout()
        self.brightness = QDoubleSpinBox()
        self.brightness.setRange(0, 1)
        self.brightness.setSingleStep(0.05)
        f.addRow("Brightness", self.brightness)
        self.rotation = QComboBox()
        self.rotation.addItems(["0", "90", "180", "270"])
        f.addRow("View rotation", self.rotation)
        light_layout.addLayout(f)
        light_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(lights)
        tabs.addTab(scroll, "Lighting")
        logs = QWidget()
        log_layout = QVBoxLayout(logs)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        log_layout.addWidget(self.log)
        tabs.addTab(logs, "Activity")
        split.setSizes([205, 660, 375])
        for widget in (self.label, self.hold, self.repeat, self.brightness):
            (widget.textChanged if isinstance(widget, QLineEdit) else widget.valueChanged).connect(
                self.schedule_capture
            )
        self.action_editor.changed.connect(self.schedule_capture)
        self.key_effect.changed.connect(self.schedule_capture)
        self.board_style.changed.connect(self.schedule_capture)
        self.override.toggled.connect(self.schedule_capture)
        self.rotation.currentTextChanged.connect(self.schedule_capture)
        self.target.currentIndexChanged.connect(self.switch_target)
        self.layout_choice.currentIndexChanged.connect(self.schedule_capture)
        self.trigger.currentTextChanged.connect(self.switch_trigger)
        self.state_choice.currentTextChanged.connect(self.switch_state)
        self.device.connected.connect(self.on_connected)
        self.device.disconnected.connect(self.on_disconnected)
        self.device.completed.connect(self.on_completed)
        self.device.failed.connect(self.on_failed)
        self.device.event.connect(self.on_event)
        self.runner.feedback.connect(self.on_feedback)
        self.runner.log.connect(self.log.appendPlainText)
        self.runner.state.connect(self.on_state)
        self.runner.progress.connect(self.on_progress)
        self.runner.effect.connect(self.on_effect)
        self.active_trigger = "press"
        self.active_state = "idle"
        self.edit_os = "windows"
        self.loading = False
        self.refresh_library()
        self.shortcuts()
        self.statusBar().showMessage("Ready. Edits and previews do not run actions.")
        self.appearance.currentIndexChanged.connect(self.change_appearance)
        from PySide6.QtWidgets import QApplication

        QApplication.styleHints().colorSchemeChanged.connect(lambda scheme: self.apply_appearance())
        self.apply_appearance()

    def apply_appearance(self):
        from PySide6.QtWidgets import QApplication
        from keypad_studio.themes import apply_palette

        mode = self.appearance.currentData()
        if mode == "system":
            mode = (
                "dark"
                if QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
                else "light"
            )
        apply_palette(QApplication.instance(), mode)
        self.board.set_theme(mode)

    def change_appearance(self):
        self.library.settings["appearance"] = self.appearance.currentData()
        self.library.save_settings()
        self.apply_appearance()

    def shortcuts(self):
        for title, key, callback in (
            ("Save", QKeySequence.Save, self.save_local),
            ("Undo", QKeySequence.Undo, self.undo),
            ("Redo", QKeySequence.Redo, self.redo),
        ):
            action = QAction(title, self)
            action.setShortcut(key)
            action.triggered.connect(callback)
            self.addAction(action)

    def refresh_library(self, ident=None):
        index = self.update_library_list(ident)
        self.select_profile(index)

    def update_library_list(self, ident=None):
        self.library_profiles = self.library.all()
        self.profiles.blockSignals(True)
        self.profiles.clear()
        for p in self.library_profiles:
            self.profiles.addItem(p["name"])
        index = next((i for i, p in enumerate(self.library_profiles) if p["id"] == ident), 0)
        self.profiles.setCurrentRow(index)
        self.profiles.blockSignals(False)
        return index

    def allow_discard(self):
        if not self.dirty:
            return True
        result = QMessageBox.question(
            self,
            "Unsaved profile",
            "Save your changes to the local library?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        )
        if result == QMessageBox.Cancel:
            return False
        if result == QMessageBox.Save:
            return self.save_local()
        return True

    def select_profile(self, index):
        if self.loading or index < 0 or index >= len(self.library_profiles):
            return
        chosen = deepcopy(self.library_profiles[index])
        self.capture()
        if not self.allow_discard():
            self.profiles.blockSignals(True)
            self.profiles.setCurrentRow(
                next(
                    (
                        i
                        for i, p in enumerate(self.library_profiles)
                        if p["id"] == self.profile["id"]
                    ),
                    0,
                )
            )
            self.profiles.blockSignals(False)
            return
        self.profile = chosen
        self.update_library_list(chosen["id"])
        self.dirty = False
        self.undo_stack = []
        self.redo_stack = []
        self.selected = 0
        self.board.states = {}
        self.board.pressed = {}
        self.render()

    def render(self):
        if not self.profile:
            return
        self.loading = True
        self.profile_title.setText(self.profile["name"])
        self.target.setCurrentIndex(self.target.findData(self.profile["target_os"]))
        self.edit_os = self.profile["target_os"]
        self.layout_choice.setCurrentIndex(
            self.layout_choice.findData(self.profile["keyboard_layout"][self.edit_os])
        )
        self.brightness.setValue(self.profile["brightness"])
        self.rotation.setCurrentText(str(self.profile.get("orientation", 0)))
        self.board_style.load(self.profile["lighting"])
        key = self.profile["keys"][self.selected]
        self.key_heading.setText("KEY %02d · %s" % (self.selected + 1, self.edit_os.upper()))
        self.label.setText(key["label"])
        self.hold.setValue(key.get("hold_ms", 500))
        self.repeat.setValue(key.get("repeat_ms", 0))
        self.active_trigger = self.trigger.currentText()
        self.active_state = self.state_choice.currentText()
        self.action_editor.load(
            key["bindings"].get(self.edit_os, {}).get(self.active_trigger, {"type": "none"})
        )
        value = key.get("lighting", {}).get(self.active_state)
        self.override.setChecked(value is not None)
        self.key_effect.load(value or effect())
        self.key_effect.setEnabled(value is not None)
        self.board.load(self.profile, self.selected)
        self.loading = False
        self.update_dirty()

    def schedule_capture(self, *args):
        if not self.loading:
            self.commit_timer.start(350)

    def snapshot(self):
        self.undo_stack.append(deepcopy(self.profile))
        self.undo_stack = self.undo_stack[-80:]
        self.redo_stack = []

    def capture(self):
        self.commit_timer.stop()
        if self.loading or self.profile is None:
            return
        candidate = deepcopy(self.profile)
        key = candidate["keys"][self.selected]
        key.update(
            label=self.label.text(), hold_ms=self.hold.value(), repeat_ms=self.repeat.value()
        )
        key["bindings"].setdefault(self.edit_os, {})[
            self.active_trigger
        ] = self.action_editor.value()
        if self.override.isChecked():
            key["lighting"][self.active_state] = self.key_effect.value()
        else:
            key["lighting"].pop(self.active_state, None)
        candidate["keyboard_layout"][self.edit_os] = self.layout_choice.currentData()
        candidate["brightness"] = self.brightness.value()
        candidate["orientation"] = int(self.rotation.currentText())
        candidate["lighting"] = self.board_style.value()
        if candidate != self.profile:
            self.snapshot()
            self.profile = candidate
            self.dirty = True
            self.board.load(self.profile, self.selected)
            self.update_dirty()
        self.key_effect.setEnabled(self.override.isChecked())
        self.action_editor.capability.setText(
            "Works independently"
            if independent(self.action_editor.value())
            else "Requires background companion"
        )

    def update_dirty(self):
        self.saved_label.setText("Unsaved changes" if self.dirty else "Saved locally")
        self.setWindowTitle(
            self.profile["name"] + (" *" if self.dirty else "") + " · Keypad Studio"
        )

    def select_key(self, index):
        self.capture()
        self.selected = index
        self.render()

    def switch_trigger(self, value):
        if not self.loading:
            self.capture()
            self.active_trigger = value
            self.render()

    def switch_state(self, value):
        if not self.loading:
            self.capture()
            self.active_state = value
            self.render()

    def switch_target(self, *args):
        if self.loading:
            return
        self.capture()
        self.snapshot()
        self.profile["target_os"] = self.target.currentData()
        self.dirty = True
        self.render()

    def swap(self, a, b):
        self.capture()
        self.snapshot()
        keys = self.profile["keys"]
        keys[a], keys[b] = keys[b], keys[a]
        keys[a]["id"] = a
        keys[b]["id"] = b
        self.dirty = True
        self.render()

    def copy_key(self):
        self.capture()
        self.clipboard = deepcopy(self.profile["keys"][self.selected])

    def paste_key(self):
        if self.clipboard:
            self.capture()
            self.snapshot()
            key = deepcopy(self.clipboard)
            key["id"] = self.selected
            self.profile["keys"][self.selected] = key
            self.dirty = True
            self.render()

    def undo(self):
        self.capture()
        if self.undo_stack:
            self.redo_stack.append(deepcopy(self.profile))
            self.profile = self.undo_stack.pop()
            self.dirty = True
            self.render()

    def redo(self):
        self.capture()
        if self.redo_stack:
            self.undo_stack.append(deepcopy(self.profile))
            self.profile = self.redo_stack.pop()
            self.dirty = True
            self.render()

    def save_local(self):
        self.capture()
        try:
            encode(self.profile)
            self.library.save(self.profile)
            self.dirty = False
            self.update_dirty()
            self.update_library_list(self.profile["id"])
            return True
        except Exception as exc:
            QMessageBox.warning(self, "Could not save", str(exc))
            return False

    def new_profile(self):
        self.capture()
        if not self.allow_discard():
            return
        name, ok = QInputDialog.getText(self, "New profile", "Name")
        if ok and name.strip():
            p = new_profile(name.strip(), uuid.uuid4().hex)
            p["target_os"] = self.runner.os_name
            self.library.save(p)
            self.refresh_library(p["id"])

    def duplicate(self):
        self.capture()
        p = self.library.duplicate(self.profile)
        self.dirty = False
        self.refresh_library(p["id"])

    def rename(self):
        name, ok = QInputDialog.getText(self, "Rename profile", "Name", text=self.profile["name"])
        if ok and name.strip():
            self.capture()
            self.snapshot()
            self.profile["name"] = name.strip()
            self.dirty = True
            self.render()

    def import_profile(self):
        path = QFileDialog.getOpenFileName(self, "Import profile", "", "JSON profiles (*.json)")[0]
        if path:
            try:
                p = validate(json.loads(Path(path).read_text(encoding="utf-8")))
                p = self.library.duplicate(p, p["name"] + " (imported)")
                self.refresh_library(p["id"])
            except Exception as exc:
                QMessageBox.warning(self, "Could not import", str(exc))

    def export_profile(self):
        self.capture()
        path = QFileDialog.getSaveFileName(
            self, "Export profile", self.profile["name"] + ".json", "JSON profiles (*.json)"
        )[0]
        if path:
            try:
                Path(path).write_bytes(encode(self.profile))
            except Exception as exc:
                QMessageBox.warning(self, "Could not export", str(exc))

    def computer_settings(self):
        self.capture()
        BindingDialog(self.library, self.profile, self.profile["target_os"], self).exec()

    def setup_device(self):
        from keypad_studio.setup import SetupDialog

        SetupDialog(self.library, self.device, self).exec()

    def use_legacy(self):
        choices = self.profile.get("legacy_actions", {})
        if not choices:
            QMessageBox.information(
                self, "Legacy macros", "This profile has no saved legacy launch macros."
            )
            return
        if self.profile["target_os"] != "windows":
            QMessageBox.information(
                self,
                "Windows macro",
                "Choose Windows as the target to use these PowerShell keyboard macros.",
            )
            return
        name, ok = QInputDialog.getItem(
            self,
            "Legacy keyboard launcher",
            "Choose a macro, then edit its text step to set the script path",
            list(choices),
            0,
            False,
        )
        if ok:
            self.action_editor.load(deepcopy(choices[name]))
            self.capture()

    def choose_port(self):
        ports = self.device.ports()
        options = ["Automatic data-port detection"] + [
            p.device + " · " + p.description for p in ports
        ]
        choice, ok = QInputDialog.getItem(
            self,
            "Device connection",
            "Choose the DATA port, not the debug console",
            options,
            0,
            False,
        )
        if ok:
            self.device.port = None if choice == options[0] else choice.split(" · ")[0]
            self.statusBar().showMessage(
                "Connection preference updated; reconnect the cable if already connected"
            )

    def on_connected(self, info):
        self.session = info["session"]
        self.event_floor = info.get("event_floor", 0)
        self.seen_events.clear()
        self.connection.setText("●  Pico connected · firmware " + info["firmware"])
        self.device_revision = info["revision"]
        self.verified_revision = None
        self.device_profile = None

    def on_disconnected(self, message):
        self.connection.setText("○  Pico disconnected · editor available")
        self.device_revision = None
        self.verified_revision = None
        self.board.pressed = {}
        self.log.appendPlainText(message)
        for key in list(self.runner.runs):
            self.runner.cancel(key)

    def on_completed(self, name, result):
        if name in ("read", "save"):
            self.device_profile = deepcopy(result["profile"])
            self.device_revision = result["meta"]["revision"]
            self.verified_revision = self.device_revision
            self.connection.setText("●  Pico · " + self.device_profile["name"])
            self.log.appendPlainText(
                "Pico profile: %s · revision %d"
                % (self.device_profile["name"], self.device_revision)
            )
            if name == "save":
                self.statusBar().showMessage(
                    "Saved to Pico and read-back verified. Unplugging preserves this profile."
                )
        elif name == "preview":
            self.statusBar().showMessage(
                "Preview active for 30 seconds. Keyboard actions are suppressed; flash unchanged."
            )

    def on_failed(self, name, message):
        self.log.appendPlainText(name + ": " + message)
        self.statusBar().showMessage(message, 10000)

    def read_device(self):
        self.capture()
        if self.device_profile:
            if not self.allow_discard():
                return
            p = self.library.duplicate(
                self.device_profile, self.device_profile["name"] + " (from Pico)"
            )
            self.dirty = False
            self.refresh_library(p["id"])
        else:
            self.device.submit("read")
            self.statusBar().showMessage(
                "Reading device profile; click Read from Pico again to add it to the library"
            )

    def save_device(self):
        self.capture()
        try:
            encode(self.profile)
        except ValueError as exc:
            QMessageBox.warning(self, "Check profile", str(exc))
            return
        if self.verified_revision is None:
            self.device.submit("read")
            self.statusBar().showMessage("Read the device first, then click Save to Pico")
            return
        if self.profile["target_os"] != self.runner.os_name:
            if (
                QMessageBox.question(
                    self,
                    "Saved target differs",
                    "This profile will use %s shortcuts even on this computer. Save it to the Pico?"
                    % self.profile["target_os"],
                )
                != QMessageBox.Yes
            ):
                return
        if (
            QMessageBox.question(
                self,
                "Save to Pico",
                "Replace the Pico's active profile “%s” with “%s”?"
                % (self.device_profile["name"], self.profile["name"]),
            )
            != QMessageBox.Yes
        ):
            return
        self.device.submit("save", {"profile": self.profile, "revision": self.verified_revision})

    def preview(self):
        self.capture()
        if self.device_revision is not None:
            self.device.submit(
                "preview", {"profile": self.profile, "revision": self.device_revision}
            )
        else:
            self.statusBar().showMessage(
                "Local preview is live. Connect a Pico with the new firmware for device preview."
            )

    def set_diagnostic(self, enabled):
        self.device.diagnostic = enabled
        if enabled:
            (self.library.root / "diagnostic-events.jsonl").write_text("")
        if self.device.info:
            self.device.submit("diagnostic", {"enabled": enabled})

    def local_toggle(self):
        self.on_state(self.selected, "toggle")

    def on_state(self, key, state):
        if state == "toggle":
            state = "off" if self.board.states.get(key) == "on" else "on"
        self.board.states[key] = state
        if self.device.info:
            self.device.submit("feedback", {"key": key, "state": state})

    def on_feedback(self, key, state):
        self.board.overlays[key] = (state, time.monotonic() - self.board.started)
        if state in ("success", "error"):
            self.board.progress.pop(key, None)
        if self.device.info:
            self.device.submit("feedback", {"key": key, "state": state})

    def on_progress(self, key, value):
        self.board.progress[key] = value
        self.statusBar().showMessage("Key %d · %d%%" % (key + 1, value * 100))
        if self.device.info:
            self.device.submit("feedback", {"key": key, "state": "running", "progress": value})

    def on_effect(self, key, action):
        now = time.monotonic() - self.board.started
        if action.get("scope", "board") == "board":
            self.board.board_effect = (action["effect"], now, (key % 4, key // 4))
        else:
            self.board.key_effects[key] = (action["effect"], now)

    def on_event(self, event):
        kind = event.get("type")
        key = event.get("key", 0)
        if not 0 <= key < 16:
            return
        if kind == "key":
            if event["pressed"]:
                self.board.pressed[key] = time.monotonic() - self.board.started
            else:
                self.board.pressed.pop(key, None)
            if self.diagnostic.isChecked() and event["pressed"]:
                self.select_key(key)
                self.log.appendPlainText("Learn mode · key %02d" % (key + 1))
                with (self.library.root / "diagnostic-events.jsonl").open("a") as handle:
                    handle.write(
                        json.dumps({"time": time.time(), "key": key, "display": key + 1}) + "\n"
                    )
        elif kind == "state":
            self.board.states[key] = event["state"]
        elif kind == "effect":
            self.on_effect(key, event)
        elif kind == "error":
            self.log.appendPlainText(event.get("message", "Device error"))
        elif kind == "action" and event.get("owner") == "host":
            ident = (event.get("session"), event.get("event_id"))
            if (
                ident in self.seen_events
                or event.get("session") != self.session
                or event.get("event_id", 0) <= self.event_floor
            ):
                return
            self.seen_events.add(ident)
            if len(self.seen_events) > 2048:
                self.seen_events = {ident}
            p = self.device_profile
            if not p or p["id"] != event.get("profile_id"):
                return
            if p["target_os"] != self.runner.os_name:
                self.on_feedback(key, "error")
                self.log.appendPlainText(
                    "Save this profile for the current operating system before running companion actions"
                )
                return
            action = (
                p["keys"][key]["bindings"]
                .get(p["target_os"], {})
                .get(event["trigger"], {"type": "none"})
            )
            self.runner.start(key, action, p["id"])

    def test_action(self):
        self.capture()
        if self.profile["target_os"] != self.runner.os_name:
            QMessageBox.information(
                self,
                "Choose current OS",
                "Select the current operating system before testing actions.",
            )
            return
        action = self.action_editor.value()
        try:
            validate(self.profile)
        except ValueError as exc:
            QMessageBox.warning(self, "Check action", str(exc))
            return
        self.runner.start(self.selected, action, self.profile["id"])

    def closeEvent(self, event):
        self.capture()
        self.hide()
        event.ignore()
