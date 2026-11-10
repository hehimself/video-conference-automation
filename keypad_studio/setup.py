"""A small GUI for the same backup/update steps as keypad-firmware."""

import sys
import shutil
from pathlib import Path
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QFileDialog,
)
from keypad_studio.install import (
    backup,
    console_command,
    install,
    resources,
    verify_bundle,
    CP_VERSION,
)


class Task(QThread):
    done = Signal(str)

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    def run(self):
        try:
            self.done.emit(self.operation())
        except Exception as exc:
            self.done.emit("Could not complete: " + str(exc))


class SetupDialog(QDialog):
    def __init__(self, library, device, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set up / update Pico")
        self.resize(610, 600)
        self.task = None
        self.library, self.device = library, device
        layout = QVBoxLayout(self)
        note = QLabel(
            "Use these steps for first installation or firmware updates. Backups stay private on this computer. A first installation starts with an empty profile; saved Studio profiles are retained."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        layout.addLayout(form)
        self.mount = QLineEdit("/Volumes/CIRCUITPY" if sys.platform == "darwin" else "E:/")
        form.addRow("CIRCUITPY folder", self.mount)
        self.boot_mount = QLineEdit("/Volumes/RPI-RP2" if sys.platform == "darwin" else "E:/")
        form.addRow("RPI-RP2 folder", self.boot_mount)
        self.console = QComboBox()
        self.console.setEditable(True)
        for port in device.ports():
            self.console.addItem(port.device)
        form.addRow("CONSOLE port", self.console)
        self.buttons = []
        for text, callback in (
            (
                "Existing Studio firmware: enter maintenance mode",
                lambda: device.submit("maintenance"),
            ),
            ("1 · Back up and enter bootloader", self.enter_bootloader),
            ("2 · Copy CircuitPython 10.3.1 to RPI-RP2", self.flash),
            ("3 · Install Studio files and restart", self.install_files),
        ):
            button = QPushButton(text)
            button.clicked.connect(callback)
            layout.addWidget(button)
            self.buttons.append(button)
        hint = QLabel(
            "If the bootloader does not appear, reconnect while holding BOOTSEL. For an existing Studio device, enter maintenance first. Choose the console port, not DATA. Quit other serial tools before setup."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def start(self, operation):
        if self.task and self.task.isRunning():
            return
        self.log.appendPlainText("Working…")
        for button in self.buttons:
            button.setEnabled(False)
        self.task = Task(operation)

        def finished(message):
            self.log.appendPlainText(message)
            for button in self.buttons:
                button.setEnabled(True)

        self.task.done.connect(finished)
        self.task.start()

    def enter_bootloader(self):
        mount, port = self.mount.text(), self.console.currentText()

        def operation():
            verify_bundle(resources())
            saved = backup(mount, self.library.root / "private-backups")
            console_command(
                port,
                "import microcontroller; microcontroller.on_next_reset(microcontroller.RunMode.BOOTLOADER); microcontroller.reset()",
            )
            return "Backup: %s\nWait for RPI-RP2, then use step 2." % saved

        self.start(operation)

    def flash(self):
        mount = Path(self.boot_mount.text())

        def operation():
            verify_bundle(resources())
            info = mount / "INFO_UF2.TXT"
            if not info.exists() or "RP2" not in info.read_text():
                raise ValueError("Choose the Pico's RPI-RP2 bootloader folder")
            shutil.copyfile(
                resources() / ("circuitpython-%s-pico.uf2" % CP_VERSION),
                mount / "keypad-circuitpython.uf2",
            )
            return "Firmware copied. Wait for CIRCUITPY, refresh the console port if necessary, then use step 3."

        self.start(operation)

    def install_files(self):
        mount, port = self.mount.text(), self.console.currentText()

        def operation():
            boot = (Path(mount) / "boot_out.txt").read_text()
            if "CircuitPython " + CP_VERSION not in boot:
                raise ValueError("Complete the CircuitPython upgrade first")
            saved = backup(mount, self.library.root / "private-backups")
            console_command(port, "import supervisor; supervisor.runtime.autoreload = False")
            install(mount)
            console_command(port, "import microcontroller; microcontroller.reset()")
            return (
                "Installed and restarted. Close setup and use Learn mode to verify your keys.\nBackup: "
                + str(saved)
            )

        self.start(operation)

    def done(self, result):
        if self.task and self.task.isRunning():
            self.log.appendPlainText("Wait for the current step to finish before closing.")
            return
        super().done(result)
