import json
import time
import uuid
from copy import deepcopy
from PySide6.QtCore import Qt, Signal, QMimeData, QTimer, QPointF, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QDrag, QTextLayout, QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QColorDialog,
    QListWidget,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QCheckBox,
    QFileDialog,
    QSizePolicy,
    QStyledItemDelegate,
    QStyle,
    QApplication,
)
from keypad_core.schema import EFFECTS, MEDIA, effect, independent, validate_action
from keypad_core.effects import frame
from keypad_studio.themes import PALETTES
from keypad_studio.controls import ComboBox as QComboBox


def button(text, callback, layout, icon_name=None, variant=None):
    control = QPushButton(text)
    if icon_name:
        control.setProperty("iconName", icon_name)
    if variant:
        control.setProperty("variant", variant)
    control.clicked.connect(callback)
    layout.addWidget(control)
    return control


class ProfileDelegate(QStyledItemDelegate):
    """Two-line library rows that keep long profile names inside the sidebar."""

    def sizeHint(self, option, index):
        return QSize(180, 66)

    def paint(self, painter, option, index):
        c = PALETTES[QApplication.instance().property("keypadTheme") or "dark"]
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect.adjusted(0, 2, -1, -2)
        selected = bool(option.state & QStyle.State_Selected)
        if selected or option.state & QStyle.State_MouseOver:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(c["selected"] if selected else c["hover"]))
            painter.drawRoundedRect(rect, 8, 8)
        if option.state & QStyle.State_HasFocus and option.widget.hasFocus():
            painter.setPen(QPen(QColor(c["focus"]), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 7, 7)
        if selected:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(c["focus"]))
            painter.drawRoundedRect(QRectF(rect.left(), rect.top() + 17, 3, 28), 1.5, 1.5)
        font = QFont(option.font)
        font.setPixelSize(13)
        font.setWeight(QFont.DemiBold if selected else QFont.Medium)
        painter.setFont(font)
        painter.setPen(QColor(c["selected_text"] if selected else c["text"]))
        title = painter.fontMetrics().elidedText(index.data(), Qt.ElideRight, rect.width() - 24)
        painter.drawText(rect.adjusted(12, 10, -12, -30), Qt.AlignVCenter, title)
        font.setPixelSize(11)
        font.setWeight(QFont.Normal)
        painter.setFont(font)
        painter.setPen(QColor(c["selected_text"] if selected else c["muted"]))
        painter.drawText(rect.adjusted(12, 31, -12, -8), Qt.AlignVCenter, index.data(Qt.UserRole))
        painter.restore()


class EffectEditor(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = [30, 80, 160]
        self.loading = False
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        form.setVerticalSpacing(10)
        self.preset = QComboBox()
        self.preset.addItems(EFFECTS)
        self.color_button = QPushButton("Choose color")
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.05, 20)
        self.speed.setSingleStep(0.1)
        self.speed.setValue(1)
        self.duration = QDoubleSpinBox()
        self.duration.setRange(0.05, 60)
        self.duration.setSuffix(" s")
        self.duration.setValue(1)
        self.direction = QComboBox()
        self.direction.addItems(["right", "left", "down", "up"])
        for name, control in (
            ("Preset", self.preset),
            ("Color", self.color_button),
            ("Speed", self.speed),
            ("Duration", self.duration),
            ("Direction", self.direction),
        ):
            form.addRow(name, control)
        self.color_button.clicked.connect(self.choose_color)
        self.preset.currentTextChanged.connect(self.changed)
        self.speed.valueChanged.connect(self.changed)
        self.duration.valueChanged.connect(self.changed)
        self.direction.currentTextChanged.connect(self.changed)

    def choose_color(self):
        c = QColorDialog.getColor(QColor(*self.color), self)
        if c.isValid():
            self.color = [c.red(), c.green(), c.blue()]
            self.paint_color()
            self.changed.emit()

    def paint_color(self):
        swatch = QPixmap(16, 16)
        swatch.fill(QColor(*self.color))
        self.color_button.setIcon(QIcon(swatch))
        self.color_button.setText("#%02X%02X%02X" % tuple(self.color))

    def load(self, value):
        self.preset.setCurrentText(value.get("name", "solid"))
        self.color = list(value.get("color", [30, 80, 160]))
        self.speed.setValue(value.get("speed", 1))
        self.duration.setValue(value.get("duration", 1))
        self.direction.setCurrentText(value.get("direction", "right"))
        self.paint_color()

    def value(self):
        return effect(
            self.preset.currentText(),
            self.color,
            speed=self.speed.value(),
            duration=self.duration.value(),
            direction=self.direction.currentText(),
        )


ACTION_LABELS = {
    "none": "Unassigned",
    "hotkey": "Keyboard shortcut",
    "media": "Media control",
    "text": "Type text",
    "delay": "Wait",
    "sequence": "Action sequence",
    "toggle": "Toggle local state",
    "effect": "Lighting effect",
    "run_script": "Run script",
    "open_app": "Open application",
    "focus_app": "Focus application",
    "open_url": "Open URL",
    "play_sound": "Play sound",
    "app_volume": "Application volume (Windows)",
    "extract_zip": "Extract latest ZIP",
}


class ActionEditor(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading = False
        self.action = {"type": "none"}
        self.fields = {}
        self.sequence = []
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(12)
        caption = QLabel("Action")
        self.layout_.addWidget(caption)
        self.kind = QComboBox()
        self.kind.setAccessibleName("Action type")
        for key, label in ACTION_LABELS.items():
            self.kind.addItem(label, key)
        self.layout_.addWidget(self.kind)
        self.details = QWidget()
        self.form = QFormLayout(self.details)
        self.form.setContentsMargins(0, 8, 0, 0)
        self.form.setVerticalSpacing(8)
        self.layout_.addWidget(self.details)
        self.form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.capability = QLabel()
        self.capability.setWordWrap(True)
        self.capability.setObjectName("capability")
        self.layout_.addWidget(self.capability)
        self.kind.currentIndexChanged.connect(self.type_changed)
        self.load({"type": "none"})

    def clear(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.fields = {}

    def type_changed(self):
        if self.loading:
            return
        kind = self.kind.currentData()
        defaults = {
            "hotkey": {"keys": ["ctrl", "shift", "m"]},
            "media": {"code": "play_pause"},
            "text": {"text": ""},
            "sequence": {"steps": []},
            "effect": {"effect": effect(), "scope": "board"},
            "delay": {"ms": 250},
        }
        value = {"type": kind}
        if kind in (
            "run_script",
            "open_app",
            "focus_app",
            "open_url",
            "play_sound",
            "app_volume",
            "extract_zip",
        ):
            value["binding_id"] = kind.replace("_", "-") + "-" + uuid.uuid4().hex[:8]
        value.update(defaults.get(kind, {}))
        self.load(value)
        self.changed.emit()

    def field(self, name, label, value="", multiline=False):
        control = QPlainTextEdit(str(value)) if multiline else QLineEdit(str(value))
        if multiline:
            control.setMaximumHeight(110)
            control.textChanged.connect(self.changed)
        else:
            control.textChanged.connect(self.changed)
        self.fields[name] = control
        self.form.addRow(label, control)
        return control

    def load(self, action):
        self.loading = True
        self.action = deepcopy(action)
        self.clear()
        kind = action.get("type", "none")
        self.kind.setCurrentIndex(max(0, self.kind.findData(kind)))
        if kind == "hotkey":
            self.field("keys", "Keys · separated by +", " + ".join(action.get("keys", [])))
        elif kind == "text":
            self.field("text", "Text", action.get("text", ""), True)
        elif kind == "media":
            combo = QComboBox()
            combo.addItems(MEDIA)
            combo.setCurrentText(action.get("code", "play_pause"))
            combo.currentTextChanged.connect(self.changed)
            self.fields["code"] = combo
            self.form.addRow("Control", combo)
        elif kind == "delay":
            spin = QSpinBox()
            spin.setRange(0, 60000)
            spin.setSuffix(" ms")
            spin.setValue(action.get("ms", 250))
            spin.valueChanged.connect(self.changed)
            self.fields["ms"] = spin
            self.form.addRow("Wait", spin)
        elif kind == "effect":
            editor = EffectEditor()
            editor.load(action.get("effect", effect()))
            editor.changed.connect(self.changed)
            self.fields["effect"] = editor
            self.form.addRow(editor)
            scope = QComboBox()
            scope.addItems(["board", "key"])
            scope.setCurrentText(action.get("scope", "board"))
            scope.currentTextChanged.connect(self.changed)
            self.fields["scope"] = scope
            self.form.addRow("Apply to", scope)
        elif kind == "sequence":
            self.sequence = deepcopy(action.get("steps", []))
            self.step_list = QListWidget()
            self.step_list.setMaximumHeight(170)
            self.form.addRow(self.step_list)
            row = QHBoxLayout()
            row.setSpacing(6)
            for label, callback in (
                ("+", self.add_step),
                ("Edit", self.edit_step),
                ("−", self.remove_step),
                ("↑", lambda: self.move_step(-1)),
                ("↓", lambda: self.move_step(1)),
            ):
                button(label, callback, row)
            self.form.addRow(row)
            self.refresh_steps()
        elif kind not in ("none", "toggle"):
            self.field("binding_id", "Computer binding", action.get("binding_id", kind + "-action"))
            if kind in ("open_app", "focus_app", "app_volume"):
                self.field("app", "Application", action.get("app", ""))
            if kind == "open_url":
                self.field("url", "URL", action.get("url", "https://"))
            if kind == "app_volume":
                spin = QDoubleSpinBox()
                spin.setRange(-1, 1)
                spin.setSingleStep(0.05)
                spin.setValue(action.get("delta", 0.05))
                spin.valueChanged.connect(self.changed)
                self.fields["delta"] = spin
                self.form.addRow("Volume change", spin)
            note = QLabel(
                "Use Computer Settings to choose script/sound files and machine-specific paths."
            )
            note.setWordWrap(True)
            note.setObjectName("muted")
            self.form.addRow(note)
        self.refresh_capability(action)
        self.loading = False

    def refresh_capability(self, action=None):
        action = self.value() if action is None else action
        self.capability.setText(
            "Works independently" if independent(action) else "Requires background companion"
        )

    def value(self):
        kind = self.kind.currentData()
        out = {"type": kind}
        for name, control in self.fields.items():
            if isinstance(control, QLineEdit):
                value = control.text().strip() if name != "text" else control.text()
            elif isinstance(control, QPlainTextEdit):
                value = control.toPlainText()
            elif isinstance(control, QComboBox):
                value = control.currentText()
            else:
                value = control.value()
            out[name] = (
                [n.strip().lower() for n in value.split("+") if n.strip()]
                if name == "keys"
                else value
            )
        if kind == "sequence":
            out["steps"] = deepcopy(self.sequence)
        return out

    def refresh_steps(self):
        selected = self.step_list.currentRow()
        self.step_list.clear()
        self.step_list.setFixedHeight(min(180, max(74, len(self.sequence) * 40 + 8)))
        for index, step in enumerate(self.sequence):
            label = ACTION_LABELS.get(step.get("type"), "Action")
            detail = (
                " + ".join(step["keys"])
                if step.get("type") == "hotkey"
                else step.get("binding_id", step.get("code", ""))
            )
            self.step_list.addItem("%d  %s  %s" % (index + 1, label, detail))
        if self.sequence:
            self.step_list.setCurrentRow(max(0, min(selected, len(self.sequence) - 1)))
        self.capability.setText(
            "Works independently" if independent(self.value()) else "Requires background companion"
        )

    def action_dialog(self, value):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit sequence step")
        dialog.resize(410, 400)
        layout = QVBoxLayout(dialog)
        editor = ActionEditor()
        editor.load(value)
        layout.addWidget(editor)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        def accept():
            try:
                validate_action(editor.value())
                dialog.accept()
            except ValueError as exc:
                QMessageBox.warning(dialog, "Check action", str(exc))

        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        return editor.value() if dialog.exec() == QDialog.Accepted else None

    def add_step(self):
        value = self.action_dialog({"type": "hotkey", "keys": ["enter"]})
        if value is not None:
            self.sequence.append(value)
            self.refresh_steps()
            self.changed.emit()

    def edit_step(self):
        i = self.step_list.currentRow()
        if i < 0:
            return
        value = self.action_dialog(self.sequence[i])
        if value is not None:
            self.sequence[i] = value
            self.refresh_steps()
            self.changed.emit()

    def remove_step(self):
        i = self.step_list.currentRow()
        if i >= 0:
            self.sequence.pop(i)
            self.refresh_steps()
            self.changed.emit()

    def move_step(self, delta):
        i = self.step_list.currentRow()
        j = i + delta
        if 0 <= i < len(self.sequence) and 0 <= j < len(self.sequence):
            self.sequence[i], self.sequence[j] = self.sequence[j], self.sequence[i]
            self.refresh_steps()
            self.step_list.setCurrentRow(j)
            self.changed.emit()


class KeyButton(QPushButton):
    swapped = Signal(int, int)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.label = ""
        self.color = (10, 10, 10)
        self.selected = False
        self.pressed = False
        self.theme = PALETTES["dark"]
        self.setMinimumSize(64, 64)
        self.setAcceptDrops(True)
        self.setCheckable(True)
        self.origin = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(3, 3, -3, -5)
        color = QColor(*self.color)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(self.theme["shadow"]))
        p.drawRoundedRect(rect.translated(0, 3), 12, 12)
        if self.pressed or self.isDown():
            rect.translate(0, 2)
        fill = (
            self.theme["selected"]
            if self.pressed
            else self.theme["key_hover"] if self.underMouse() else self.theme["key"]
        )
        p.setBrush(QColor(fill))
        p.setPen(
            QPen(
                QColor(self.theme["focus"] if self.selected else self.theme["key_edge"]),
                2 if self.selected else 1,
            )
        )
        p.drawRoundedRect(rect, 12, 12)
        if self.hasFocus():
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(self.theme["focus"]), 1, Qt.DotLine))
            p.drawRoundedRect(rect.adjusted(4, 4, -4, -4), 9, 9)
        font = QFont(self.font())
        font.setPixelSize(10)
        font.setWeight(QFont.Normal)
        p.setFont(font)
        p.setPen(QColor(self.theme["muted"]))
        p.drawText(rect.adjusted(10, 7, -9, -7), Qt.AlignTop | Qt.AlignLeft, str(self.index + 1))
        font.setPixelSize(11 if self.height() < 80 else 13)
        font.setWeight(QFont.Medium)
        p.setFont(font)
        p.setPen(QColor(self.theme["text"]))
        content = rect.adjusted(
            8, 19 if self.height() < 80 else 25, -8, -13 if self.height() < 80 else -16
        )
        text_layout = QTextLayout(self.label, font)
        text_layout.beginLayout()
        lines = []
        while True:
            line = text_layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(content.width())
            lines.append((line.textStart(), line.textLength()))
        text_layout.endLayout()
        line_height = p.fontMetrics().height()
        limit = max(1, min(3, int(content.height() / line_height)))
        visible = lines[:limit]
        y = content.center().y() - len(visible) * line_height / 2
        for n, (start, length) in enumerate(visible):
            text = self.label[start : start + length].strip()
            if n == limit - 1 and len(lines) > limit:
                text = p.fontMetrics().elidedText(
                    self.label[start:], Qt.ElideRight, int(content.width())
                )
            p.drawText(
                QRectF(content.left(), y, content.width(), line_height), Qt.AlignCenter, text
            )
            y += line_height
        p.setPen(Qt.NoPen)
        p.setBrush(color.lighter(180) if max(self.color) > 4 else QColor(self.theme["key_edge"]))
        p.drawRoundedRect(
            QRectF(rect.left() + 16, rect.bottom() - 11, rect.width() - 32, 3), 1.5, 1.5
        )

    def mousePressEvent(self, event):
        self.origin = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self.origin is not None
            and (event.position().toPoint() - self.origin).manhattanLength() > 12
        ):
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData("application/x-keypad-key", str(self.index).encode())
            drag.setMimeData(mime)
            drag.exec(Qt.MoveAction)
            self.origin = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-keypad-key"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        try:
            self.swapped.emit(
                int(bytes(event.mimeData().data("application/x-keypad-key"))), self.index
            )
            event.acceptProposedAction()
        except ValueError:
            pass


class Board(QWidget):
    selected = Signal(int)
    swapped = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = None
        self.started = time.monotonic()
        self.pressed = {}
        self.states = {}
        self.overlays = {}
        self.board_effect = None
        self.key_effects = {}
        self.progress = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        header = QLabel("↑  USB connector\nRaspberry Pi Pico")
        header.setAlignment(Qt.AlignCenter)
        header.setObjectName("pico")
        header.setFixedSize(220, 46)
        layout.addWidget(header, 0, Qt.AlignCenter)
        self.grid = QGridLayout()
        self.grid.setSpacing(7)
        layout.addLayout(self.grid, 1)
        self.buttons = []
        for i in range(16):
            key = KeyButton(i)
            key.clicked.connect(lambda checked=False, index=i: self.selected.emit(index))
            key.swapped.connect(self.swapped)
            self.grid.addWidget(key, i // 4, i % 4)
            self.buttons.append(key)
        self.setObjectName("board")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumSize(360, 360)
        self.setMaximumSize(540, 602)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(33)

    def sizeHint(self):
        return QSize(500, 558)

    def showEvent(self, event):
        super().showEvent(event)
        self.timer.start(33)

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def set_theme(self, mode):
        for key in self.buttons:
            key.theme = PALETTES[mode]
            key.update()

    def load(self, profile, selected=0):
        self.profile = profile
        for key in self.buttons:
            self.grid.removeWidget(key)
        for key in self.buttons:
            key.label = profile["keys"][key.index]["label"]
            key.setAccessibleName("Key %d: %s" % (key.index + 1, key.label))
            key.setToolTip("Key %d · %s\nClick to edit. Drag to swap." % (key.index + 1, key.label))
            key.selected = key.index == selected
            key.setChecked(key.selected)
            x, y = key.index % 4, key.index // 4
            for _ in range(profile.get("orientation", 0) // 90):
                x, y = 3 - y, x
            self.grid.addWidget(key, y, x)
        self.animate()

    def animate(self):
        if not self.profile:
            return
        now = time.monotonic() - self.started
        if self.board_effect and now - self.board_effect[1] >= self.board_effect[0].get(
            "duration", 1
        ):
            self.board_effect = None
        for i, (style, start) in list(self.key_effects.items()):
            if now - start >= style.get("duration", 1):
                del self.key_effects[i]
        for i, (_, start) in list(self.overlays.items()):
            if self.overlays[i][0] != "running" and now - start > 1.5:
                del self.overlays[i]
        colors = frame(
            self.profile,
            now,
            self.pressed,
            self.states,
            self.overlays,
            self.board_effect,
            self.key_effects,
            self.progress,
        )
        for key, color in zip(self.buttons, colors):
            key.color = color
            key.pressed = key.index in self.pressed
            key.update()


class BindingDialog(QDialog):
    def __init__(self, library, profile, os_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Computer Settings · " + os_name)
        self.resize(560, 700)
        self.library = library
        self.draft = deepcopy(library.settings)
        self.os_name = os_name
        self.entries = {}
        self.current = None
        for key in profile["keys"]:
            for action in key.get("bindings", {}).get(os_name, {}).values():
                self.collect(action)
        layout = QVBoxLayout(self)
        note = QLabel(
            "These paths stay on this computer. The Pico stores the binding name, so scripts can be configured separately on each machine."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.select = QComboBox()
        for ident, action in self.entries.items():
            self.select.addItem(
                ident + " · " + ACTION_LABELS.get(action["type"], action["type"]), ident
            )
        layout.addWidget(self.select)
        form = QFormLayout()
        layout.addLayout(form)
        self.controls = {}
        for name, label in (
            ("executable", "Executable / interpreter"),
            ("path", "Script or sound file"),
            ("arguments", "Arguments · JSON array"),
            ("interpreter_arguments", "Interpreter flags · JSON array"),
            ("working_directory", "Working folder"),
            ("app", "Application name/path"),
            ("url", "URL"),
            ("source", "Downloads folder"),
            ("destination", "Extract to folder"),
            ("timeout", "Timeout · seconds"),
        ):
            field = QLineEdit()
            self.controls[name] = field
            row = QHBoxLayout()
            row.addWidget(field)
            if name in ("executable", "path", "working_directory", "source", "destination"):
                button("…", lambda checked=False, n=name: self.browse(n), row)
            form.addRow(label, row)
        layout.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        self.select.currentIndexChanged.connect(self.switch)
        self.switch()

    def collect(self, action):
        ident = action.get("binding_id")
        if ident:
            self.entries[ident] = action
        for child in action.get("steps", []):
            self.collect(child)

    def browse(self, name):
        path = (
            QFileDialog.getExistingDirectory(self, "Choose folder")
            if name in ("source", "destination", "working_directory")
            else QFileDialog.getOpenFileName(self, "Choose file")[0]
        )
        if path:
            self.controls[name].setText(path)

    def capture(self):
        if not self.current:
            return
        value = {k: v.text().strip() for k, v in self.controls.items() if v.text().strip()}
        value["arguments"] = json.loads(value.get("arguments", "[]"))
        value["interpreter_arguments"] = json.loads(value.get("interpreter_arguments", "[]"))
        if not isinstance(value["arguments"], list) or any(
            not isinstance(a, str) for a in value["arguments"]
        ):
            raise ValueError("Arguments must be a JSON array of strings")
        if not isinstance(value["interpreter_arguments"], list) or any(
            not isinstance(a, str) for a in value["interpreter_arguments"]
        ):
            raise ValueError("Interpreter flags must be a JSON array of strings")
        value["timeout"] = int(value.get("timeout", "60"))
        if not 1 <= value["timeout"] <= 3600:
            raise ValueError("Timeout must be 1–3600 seconds")
        self.draft.setdefault("bindings", {}).setdefault(self.current, {})[self.os_name] = value

    def switch(self):
        try:
            self.capture()
        except ValueError as exc:
            QMessageBox.warning(self, "Check settings", str(exc))
            return
        self.current = self.select.currentData()
        value = self.draft.get("bindings", {}).get(self.current, {}).get(self.os_name, {})
        defaults = self.entries.get(self.current, {})
        for name, control in self.controls.items():
            data = value.get(name, defaults.get(name, ""))
            if name in ("arguments", "interpreter_arguments"):
                data = json.dumps(data or [])
            if name == "timeout":
                data = data or 60
            control.setText(str(data))

    def save_and_accept(self):
        try:
            self.capture()
            self.library.settings = self.draft
            self.library.save_settings()
            self.accept()
        except ValueError as exc:
            QMessageBox.warning(self, "Check settings", str(exc))
