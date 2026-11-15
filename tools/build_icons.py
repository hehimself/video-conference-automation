"""Regenerate native app icons from the shared vector artwork (Qt + Pillow)."""

from pathlib import Path
from PIL import Image
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def main():
    assets = Path(__file__).resolve().parents[1] / "keypad_studio/assets"
    renderer = QSvgRenderer(str(assets / "app-icon.svg"))
    if not renderer.isValid():
        raise SystemExit("The app icon SVG is invalid")
    image = QImage(1024, 1024, QImage.Format_RGBA8888)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, 1024, 1024))
    painter.end()
    if not image.save(str(assets / "app-icon.png")):
        raise SystemExit("Could not write the app icon PNG")
    with Image.open(assets / "app-icon.png") as source:
        source.save(assets / "app-icon.icns", format="ICNS")
        source.save(
            assets / "app-icon.ico",
            format="ICO",
            sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)],
        )
    print("Generated PNG, macOS ICNS, and Windows ICO icons from app-icon.svg")


if __name__ == "__main__":
    main()
