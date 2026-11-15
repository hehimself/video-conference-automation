"""Exercise the real Qt event loop in a disposable process; never connect hardware."""

import json
import sys
from pathlib import Path
from PySide6.QtCore import QEvent, QTimer, QProcess
from PySide6.QtGui import QKeySequence
from PySide6.QtNetwork import QLocalServer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox, QSystemTrayIcon
from keypad_studio.lifecycle import StudioApplication, Lifecycle
from keypad_studio.device import DeviceWorker
from keypad_studio.profiles import Library
from keypad_studio.runner import Runner
from keypad_studio.window import Window


def main():
    mode, root = sys.argv[1], Path(sys.argv[2])
    app = StudioApplication([])
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    library = Library(root)
    device = DeviceWorker()
    device.candidates = lambda: []
    runner = Runner(library, device)
    window = Window(library, device, runner)
    tray = QSystemTrayIcon(app)
    server = QLocalServer(app)
    server.listen("keypad-lifecycle-probe-" + str(app.applicationPid()))
    lifecycle = Lifecycle(app, window, device, runner, tray, server)
    script = root / "wait.py"
    script.write_text("import time\ntime.sleep(60)\n")
    library.set_binding("wait", runner.os_name, {"executable": sys.executable, "path": str(script)})
    runner.start(0, {"type": "run_script", "binding_id": "wait"})
    device.start()
    window.show()
    window.activateWindow()

    def exercise():
        assert not runner.is_stopped() and device.isRunning()
        if mode == "background":
            lifecycle.keep_running()
            assert not window.isVisible() and not device.stopping and runner.runs
            assert not window.board.timer.isActive()
            lifecycle.show_editor()
            assert window.isVisible() and window.board.timer.isActive()
            lifecycle.quit_action.trigger()
        elif mode == "unsaved":
            window.label.setText("Preserved on quit")
            # Quit must capture edits even before the editor debounce fires.
            QMessageBox.question = lambda *args: QMessageBox.Cancel
            app.sendEvent(app, QEvent(QEvent.Quit))
            assert not lifecycle.quitting and not device.stopping and window.isVisible()
            assert window.dirty and runner.runs
            QMessageBox.question = lambda *args: QMessageBox.Save
            app.sendEvent(app, QEvent(QEvent.Quit))
        elif mode == "discard":
            window.label.setText("Discarded on quit")
            QMessageBox.question = lambda *args: QMessageBox.Discard
            window.close()
        elif mode == "shortcut":
            assert not lifecycle.quit_action.shortcut().isEmpty()
            QTest.keySequence(window, lifecycle.quit_action.shortcut())
        elif mode == "native":
            app.sendEvent(app, QEvent(QEvent.Quit))
        elif mode == "dock":
            # Optional manual Cocoa check: asks macOS to quit this process normally.
            from AppKit import NSRunningApplication

            NSRunningApplication.currentApplication().terminate()
        elif mode == "hidden-native":
            lifecycle.keep_running()
            app.sendEvent(app, QEvent(QEvent.Quit))
        else:
            window.close()

    QTimer.singleShot(150, exercise)
    QTimer.singleShot(6000, lambda: app.exit(9))
    result = app.exec()
    stopped = runner.is_stopped() and not device.isRunning()
    server_closed = not server.isListening()
    if not stopped:
        runner.shutdown()
        device.stop()
        for process in runner.findChildren(QProcess):
            if process.state() != QProcess.NotRunning:
                process.waitForFinished(1000)
    print(
        json.dumps(
            {"stopped": stopped, "server_closed": server_closed, "exit_ready": app.exit_ready}
        )
    )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
