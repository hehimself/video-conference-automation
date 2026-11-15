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
    QListWidgetItem,
    QSizePolicy,
    QMenu,
    QGroupBox,
    QSplitter,
    QTabWidget,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QScrollArea,
    QPlainTextEdit,
    QMessageBox,
    QFileDialog,
    QInputDialog,
)
from keypad_studio.controls import ComboBox as QComboBox, ElidedLabel
from keypad_core.schema import new_profile, validate, independent, effect
from keypad_core.runtime import steps
from keypad_studio.profiles import encode
from keypad_studio.widgets import (
    Board,
    ActionEditor,
    EffectEditor,
    BindingDialog,
    ProfileDelegate,
    button,
)


class Window(QMainWindow):
    def __init__(self, library, device, runner):
        super().__init__()
        self.library = library
        self.device = device
        self.runner = runner
        self.quit_handler = None
        self.closing = False
        self.setWindowTitle("Keypad Studio")
        self.resize(1400, 940)
        self.setMinimumSize(1100, 760)
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
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        header = QWidget()
        header.setObjectName("header")
        header.setAttribute(Qt.WA_StyledBackground, True)
        top = QHBoxLayout(header)
        top.setContentsMargins(24, 16, 24, 16)
        top.setSpacing(12)
        self.brand = QLabel()
        self.brand.setObjectName("brand")
        self.brand.setFixedSize(40, 40)
        self.brand.setAlignment(Qt.AlignCenter)
        top.addWidget(self.brand)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        title = QLabel("Keypad Studio")
        title.setObjectName("appTitle")
        brand_text.addWidget(title)
        subtitle = QLabel("Your keys. Your workflow.")
        subtitle.setObjectName("caption")
        brand_text.addWidget(subtitle)
        top.addLayout(brand_text)
        top.addStretch()
        self.connection = QLabel("Pico not connected")
        self.connection.setObjectName("connection")
        top.addWidget(self.connection)
        self.connect_button = button("Connection…", self.choose_port, top, variant="ghost")
        button("Set up Pico…", self.setup_device, top, variant="ghost")
        self.appearance = QComboBox()
        self.appearance.setAccessibleName("Appearance")
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
        self.save_device_button = button("Save to Pico", self.save_device, top, icon_name="usb")
        self.save_device_button.setObjectName("primary")
        self.save_device_button.setToolTip("Save the active profile to the connected Pico")
        outer.addWidget(header)
        self.split = split = QSplitter()
        split.setHandleWidth(1)
        split.setChildrenCollapsible(False)
        outer.addWidget(split, 1)

        left = QWidget()
        left.setObjectName("sidebar")
        left.setAttribute(Qt.WA_StyledBackground, True)
        left.setMinimumWidth(190)
        left.setMaximumWidth(280)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 24, 16, 20)
        left_layout.setSpacing(12)
        row = QHBoxLayout()
        heading = QLabel("Profiles")
        heading.setObjectName("section")
        row.addWidget(heading)
        row.addStretch()
        button("New", self.new_profile, row, icon_name="plus", variant="ghost")
        left_layout.addLayout(row)
        self.profiles = QListWidget()
        self.profiles.setAccessibleName("Profile library")
        self.profiles.setItemDelegate(ProfileDelegate(self.profiles))
        left_layout.addWidget(self.profiles, 1)
        self.profiles.currentRowChanged.connect(self.select_profile)
        options = button(
            "Profile options", lambda: None, left_layout, icon_name="more", variant="ghost"
        )
        profile_menu = QMenu(options)
        profile_menu.addAction("Duplicate profile", self.duplicate)
        profile_menu.addAction("Rename profile…", self.rename)
        options.setMenu(profile_menu)
        row = QHBoxLayout()
        button("Import", self.import_profile, row, variant="ghost")
        button("Export", self.export_profile, row, variant="ghost")
        left_layout.addLayout(row)
        note = QLabel("Your profile library is saved on this computer.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        left_layout.addWidget(note)
        left_layout.addSpacing(12)
        button(
            "Computer settings",
            self.computer_settings,
            left_layout,
            icon_name="settings",
            variant="subtle",
        )
        split.addWidget(left)

        center = QWidget()
        middle = QVBoxLayout(center)
        middle.setContentsMargins(26, 24, 26, 20)
        middle.setSpacing(12)
        profile_row = QHBoxLayout()
        profile_text = QVBoxLayout()
        profile_text.setSpacing(4)
        self.profile_title = ElidedLabel()
        self.profile_title.setObjectName("title")
        self.profile_title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        profile_text.addWidget(self.profile_title)
        self.saved_label = QLabel("Saved locally")
        self.saved_label.setObjectName("saved")
        profile_text.addWidget(self.saved_label)
        profile_row.addLayout(profile_text, 1)
        button("Save locally", self.save_local, profile_row, icon_name="save")
        middle.addLayout(profile_row)
        target_row = QHBoxLayout()
        target_row.setSpacing(12)
        self.target = QComboBox()
        self.target.addItem("Windows", "windows")
        self.target.addItem("macOS", "macos")
        self.layout_choice = QComboBox()
        for label, value in (
            ("German · Windows", "de_windows"),
            ("German · Mac", "de_macos"),
            ("US English", "us"),
        ):
            self.layout_choice.addItem(label, value)
        for label, control in (("Target OS", self.target), ("Keyboard layout", self.layout_choice)):
            column = QVBoxLayout()
            column.setSpacing(6)
            caption = QLabel(label)
            caption.setObjectName("caption")
            caption.setBuddy(control)
            column.addWidget(caption)
            column.addWidget(control)
            target_row.addLayout(column, 1)
        middle.addLayout(target_row)
        self.board = Board()
        middle.addWidget(self.board, 1, Qt.AlignCenter)
        self.board.selected.connect(self.select_key)
        self.board.swapped.connect(self.swap)
        hint = QLabel("Click to edit · drag to swap assignments")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignCenter)
        middle.addWidget(hint)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        button("Read from Pico", self.read_device, toolbar, icon_name="download", variant="ghost")
        toolbar.addStretch()
        self.preview_button = button(
            "Preview on Pico", self.preview, toolbar, icon_name="play", variant="subtle"
        )
        button(
            "Stop",
            lambda: self.device.submit("preview_stop"),
            toolbar,
            icon_name="stop",
            variant="ghost",
        ).setToolTip("Stop the lighting preview")
        middle.addLayout(toolbar)
        self.diagnostic = QCheckBox("Learn mode · suppress physical key actions")
        self.diagnostic.setToolTip("Identify physical keys without executing their actions")
        self.diagnostic.toggled.connect(self.set_diagnostic)
        middle.addWidget(self.diagnostic)
        split.addWidget(center)

        inspector = QWidget()
        inspector.setObjectName("inspector")
        inspector.setAttribute(Qt.WA_StyledBackground, True)
        inspector.setMinimumWidth(320)
        inspector.setMaximumWidth(440)
        inspector_layout = QVBoxLayout(inspector)
        inspector_layout.setContentsMargins(20, 24, 20, 12)
        inspector_layout.setSpacing(16)
        key_header = QHBoxLayout()
        key_titles = QVBoxLayout()
        key_titles.setSpacing(4)
        self.key_heading = QLabel("Key 1")
        self.key_heading.setObjectName("keyTitle")
        self.key_context = QLabel()
        self.key_context.setObjectName("caption")
        key_titles.addWidget(self.key_heading)
        key_titles.addWidget(self.key_context)
        key_header.addLayout(key_titles, 1)
        more = button("", lambda: None, key_header, icon_name="more", variant="ghost")
        more.setAccessibleName("Key options")
        more.setProperty("hideMenuIndicator", True)
        more.setToolTip("Key options")
        more.setFixedWidth(38)
        key_menu = QMenu(more)
        key_menu.addAction("Copy key", self.copy_key)
        key_menu.addAction("Paste key", self.paste_key)
        key_menu.addAction("Undo", self.undo)
        key_menu.addSeparator()
        key_menu.addAction("Use a legacy script-launch macro…", self.use_legacy)
        more.setMenu(key_menu)
        inspector_layout.addLayout(key_header)
        self.tabs = tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.tabBar().setExpanding(True)
        tabs.tabBar().setDrawBase(False)
        inspector_layout.addWidget(tabs, 1)
        split.addWidget(inspector)
        key_content = QWidget()
        key_layout = QVBoxLayout(key_content)
        key_layout.setContentsMargins(0, 20, 4, 8)
        key_layout.setSpacing(16)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        form.setVerticalSpacing(8)
        key_layout.addLayout(form)
        self.label = QLineEdit()
        self.label.setMaxLength(80)
        form.addRow("Key label", self.label)
        self.trigger = QComboBox()
        for caption, value in (
            ("On press", "press"),
            ("On hold", "hold"),
            ("On release", "release"),
        ):
            self.trigger.addItem(caption, value)
        form.addRow("Trigger", self.trigger)
        self.action_editor = ActionEditor()
        key_layout.addWidget(self.action_editor)
        timing_box = QGroupBox("Timing and repeat")
        timing = QFormLayout(timing_box)
        timing.setContentsMargins(12, 16, 12, 12)
        timing.setVerticalSpacing(10)
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
        key_layout.addWidget(timing_box)
        controls = QHBoxLayout()
        controls.setSpacing(6)
        button("Copy", self.copy_key, controls, icon_name="copy", variant="ghost")
        button("Paste", self.paste_key, controls, icon_name="paste", variant="ghost")
        button("Undo", self.undo, controls, icon_name="undo", variant="ghost")
        key_layout.addLayout(controls)
        test_row = QHBoxLayout()
        button(
            "Test action", self.test_action, test_row, icon_name="play", variant="subtle"
        ).setToolTip(
            "Run the selected action now. Editing and lighting previews do not run actions."
        )
        button("Cancel", lambda: self.runner.cancel(self.selected), test_row, variant="ghost")
        key_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(key_content)
        tabs.addTab(scroll, "Action")
        lights = QWidget()
        light_layout = QVBoxLayout(lights)
        light_layout.setContentsMargins(0, 20, 4, 8)
        light_layout.setSpacing(12)
        heading = QLabel("Key state")
        heading.setObjectName("section")
        light_layout.addWidget(heading)
        self.state_choice = QComboBox()
        for state in ("idle", "pressed", "on", "off", "running", "success", "error"):
            self.state_choice.addItem(state.capitalize(), state)
        self.state_choice.setAccessibleName("Key lighting state")
        light_layout.addWidget(self.state_choice)
        self.override = QCheckBox("Customize this state")
        light_layout.addWidget(self.override)
        self.key_effect = EffectEditor()
        light_layout.addWidget(self.key_effect)
        button("Preview local toggle", self.local_toggle, light_layout, variant="ghost")
        note = QLabel(
            "Toggle colors are locally tracked. They do not verify an app’s actual mute state."
        )
        note.setWordWrap(True)
        note.setObjectName("notice")
        light_layout.addWidget(note)
        light_layout.addSpacing(12)
        heading = QLabel("Whole keypad")
        heading.setObjectName("section")
        light_layout.addWidget(heading)
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
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(lights)
        tabs.addTab(scroll, "Lighting")
        logs = QWidget()
        log_layout = QVBoxLayout(logs)
        log_layout.setContentsMargins(0, 20, 0, 0)
        log_layout.setSpacing(12)
        caption = QLabel("Device events and script output")
        caption.setObjectName("caption")
        log_layout.addWidget(caption)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setAccessibleName("Device events and script output")
        self.log.setPlaceholderText(
            "Activity appears here when a device connects or an action runs."
        )
        self.log.setMaximumBlockCount(500)
        log_layout.addWidget(self.log)
        tabs.addTab(logs, "Activity")
        inspector_layout.addLayout(test_row)
        split.setSizes([220, 760, 380])
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setStretchFactor(2, 0)
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
        self.trigger.currentIndexChanged.connect(self.switch_trigger)
        self.state_choice.currentIndexChanged.connect(self.switch_state)
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
        from keypad_studio.themes import apply_palette, PALETTES
        from keypad_studio.icons import icon, refresh_icons

        mode = self.appearance.currentData()
        if mode == "system":
            mode = (
                "dark"
                if QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
                else "light"
            )
        apply_palette(QApplication.instance(), mode)
        self.board.set_theme(mode)
        refresh_icons(self, PALETTES[mode])
        self.brand.setPixmap(icon("grid", PALETTES[mode]["focus"]).pixmap(24, 24))
        self.profiles.viewport().update()

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
            item = QListWidgetItem(p["name"])
            item.setToolTip(p["name"])
            item.setData(
                Qt.UserRole, ("macOS" if p["target_os"] == "macos" else "Windows") + " · 16 keys"
            )
            self.profiles.addItem(item)
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
        self.key_heading.setText("Key %d" % (self.selected + 1))
        self.key_context.setText("%s binding" % ("macOS" if self.edit_os == "macos" else "Windows"))
        self.label.setText(key["label"])
        self.hold.setValue(key.get("hold_ms", 500))
        self.repeat.setValue(key.get("repeat_ms", 0))
        self.active_trigger = self.trigger.currentData()
        self.active_state = self.state_choice.currentData()
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
        self.saved_label.setText("●  Unsaved changes" if self.dirty else "Saved locally")
        self.saved_label.setProperty("dirty", self.dirty)
        self.saved_label.style().unpolish(self.saved_label)
        self.saved_label.style().polish(self.saved_label)
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
            self.active_trigger = self.trigger.currentData()
            self.render()

    def switch_state(self, value):
        if not self.loading:
            self.capture()
            self.active_state = self.state_choice.currentData()
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

    def set_connection(self, text, connected):
        self.connection.setText(text)
        self.connection.setProperty("connected", connected)
        self.connection.style().unpolish(self.connection)
        self.connection.style().polish(self.connection)

    def on_connected(self, info):
        self.session = info["session"]
        self.event_floor = info.get("event_floor", 0)
        self.seen_events.clear()
        self.set_connection("Pico connected", True)
        self.connection.setToolTip("Firmware " + info["firmware"])
        self.device_revision = info["revision"]
        self.verified_revision = None
        self.device_profile = None

    def on_disconnected(self, message):
        self.set_connection("Pico not connected", False)
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
            self.set_connection("Pico connected", True)
            self.connection.setToolTip("Active profile: " + self.device_profile["name"])
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
        if self.closing:
            return
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
        allowed = self.quit_handler() if self.quit_handler else self.allow_discard()
        if allowed:
            event.accept()
        else:
            event.ignore()
