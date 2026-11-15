"""One quit path for window close, native macOS Quit, menus, and the tray."""

from PySide6.QtCore import QEvent, QObject, QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication


class StudioApplication(QApplication):
    quit_handler = None
    exit_ready = False

    def event(self, event):
        if event.type() == QEvent.Quit and self.quit_handler and not self.exit_ready:
            event.ignore()
            self.quit_handler()
            return True
        return super().event(event)


class Lifecycle(QObject):
    def __init__(self, app, window, device, runner, tray, server):
        super().__init__(app)
        self.app, self.window = app, window
        self.device, self.runner = device, runner
        self.tray, self.server = tray, server
        self.quitting = False
        self.prompting = False
        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.finish_quit)
        app.quit_handler = self.request_quit
        window.quit_handler = self.request_quit

        file_menu = window.menuBar().addMenu("File")
        file_menu.addAction("Open editor", self.show_editor)
        self.background_action = file_menu.addAction("Keep companion running", self.keep_running)
        self.background_action.setToolTip(
            "Hide the editor and keep computer-side actions available"
        )
        file_menu.addSeparator()
        close = file_menu.addAction("Close", window.close)
        close.setShortcut(QKeySequence.Close)
        self.quit_action = QAction("Quit Keypad Studio", window)
        self.quit_action.setMenuRole(QAction.QuitRole)
        shortcut = QKeySequence(QKeySequence.Quit)
        # Some platform plugins provide no standard Quit binding. Qt maps Ctrl
        # to Command on macOS, so this fallback also gives the native Cmd+Q.
        self.quit_action.setShortcut(shortcut if not shortcut.isEmpty() else QKeySequence("Ctrl+Q"))
        self.quit_action.setShortcutContext(Qt.ApplicationShortcut)
        self.quit_action.triggered.connect(self.request_quit)
        window.addAction(self.quit_action)
        file_menu.addAction(self.quit_action)

    def show_editor(self):
        if not self.quitting:
            self.window.showNormal()
            self.window.raise_()
            self.window.activateWindow()

    def keep_running(self):
        if not self.quitting:
            self.window.capture()
            self.window.hide()
            self.tray.showMessage(
                "Keypad Studio",
                "Companion is running. Use the menu-bar/tray icon to reopen the editor or Quit.",
            )

    def request_quit(self):
        if self.quitting:
            return True
        if self.prompting:
            return False
        self.prompting = True
        try:
            self.window.capture()
            if self.window.dirty:
                self.show_editor()
            if not self.window.allow_discard():
                return False
        finally:
            self.prompting = False
        self.quitting = True
        self.window.closing = True
        self.window.hide()
        self.window.setEnabled(False)
        self.runner.shutdown()
        self.device.request_stop()
        # Keep the event loop alive until processes and the USB owner have exited.
        # Waiting here would freeze the UI; destroying a running QThread can abort.
        self.timer.start()
        return True

    def finish_quit(self):
        if self.device.isRunning() or not self.runner.is_stopped():
            return
        self.timer.stop()
        self.tray.hide()
        self.server.close()
        self.app.exit_ready = True
        QTimer.singleShot(0, self.app.quit)
