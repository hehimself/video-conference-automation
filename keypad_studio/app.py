import argparse
import os
import sys
from pathlib import Path
from PySide6.QtCore import QStandardPaths, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from keypad_studio.profiles import Library
from keypad_studio.device import DeviceWorker
from keypad_studio.runner import Runner
from keypad_studio.window import Window


def icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("#14251f"))
    p = QPainter(pixmap)
    p.setPen(QColor("#8bf1c7"))
    p.setBrush(QColor("#8bf1c7"))
    for y in range(4):
        for x in range(4):
            p.drawRoundedRect(6 + x * 14, 6 + y * 14, 9, 9, 2, 2)
    p.end()
    return QIcon(pixmap)


def main():
    parser = argparse.ArgumentParser(description="Keypad Studio")
    parser.add_argument("--screenshot", help=argparse.SUPPRESS)
    parser.add_argument(
        "--no-device", action="store_true", help="Open the editor without connecting to hardware"
    )
    parser.add_argument(
        "--learn",
        action="store_true",
        help="Start with physical actions suppressed for key mapping",
    )
    parser.add_argument("--zip-helper", nargs=2, help=argparse.SUPPRESS)
    parser.add_argument(
        "--theme", choices=["dark", "light", "system"], help="Choose an appearance for this session"
    )
    args = parser.parse_args()
    if args.zip_helper:
        from keypad_studio.runner import extract_latest

        extract_latest(*args.zip_helper)
        return
    app = QApplication(sys.argv)
    app.setApplicationName("Keypad Studio")
    app.setOrganizationName("Keypad Studio")
    app.setQuitOnLastWindowClosed(False)
    root = Path(
        os.environ.get("KEYPAD_HOME")
        or QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    )
    socket = QLocalSocket()
    server_name = (
        "keypad-studio-preview-" + str(os.getpid()) if args.screenshot else "keypad-studio-local-v1"
    )
    socket.connectToServer(server_name)
    if socket.waitForConnected(150):
        socket.write(b"show")
        socket.flush()
        socket.waitForBytesWritten(150)
        return
    QLocalServer.removeServer(server_name)
    server = QLocalServer()
    server.listen(server_name)
    library = Library(root)
    if args.theme:
        library.settings["appearance"] = args.theme
    device = DeviceWorker()
    runner = Runner(library, device)
    window = Window(library, device, runner)
    if args.learn:
        window.diagnostic.setChecked(True)
    app_icon = icon()
    app.setWindowIcon(app_icon)

    def show():
        window.showNormal()
        window.raise_()
        window.activateWindow()

    def client():
        connection = server.nextPendingConnection()
        connection.close()
        show()

    server.newConnection.connect(client)
    tray = QSystemTrayIcon(app_icon, app)
    tray.setToolTip("Keypad Studio")
    menu = QMenu()
    menu.addAction("Open editor", show)
    profile_menu = menu.addMenu("Profiles")
    for profile in library.all():
        action = profile_menu.addAction(profile["name"])
        action.triggered.connect(
            lambda checked=False, p=profile: (show(), window.refresh_library(p["id"]))
        )
    menu.addSeparator()

    def quit_app():
        window.capture()
        if not window.allow_discard():
            return
        for key in list(runner.runs):
            runner.cancel(key)
        if device.info:
            device.submit("preview_stop")
        device.stop()
        tray.hide()
        app.quit()

    menu.addAction("Quit", quit_app)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: show() if reason == QSystemTrayIcon.Trigger else None)
    tray.show()
    show()
    if not args.no_device:
        device.start()
    app.aboutToQuit.connect(lambda: device.stop() if device.isRunning() else None)
    if args.screenshot:

        def capture():
            window.grab().save(args.screenshot)
            quit_app()

        QTimer.singleShot(1000, capture)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
