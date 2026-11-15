"""Lucide outline icons, rendered locally in the current interface palette.

Lucide icons (ISC): https://lucide.dev/license. Paths supplied by Iconpack.
"""

from functools import lru_cache
from PySide6.QtCore import QByteArray, Qt, QSize
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QPushButton

PATHS = {
    "grid": '<path d="M12 3v18M3 12h18"/><rect x="3" y="3" width="18" height="18" rx="2"/>',
    "settings": '<path d="M20 7h-9M14 17H5"/><circle cx="17" cy="17" r="3"/><circle cx="7" cy="7" r="3"/>',
    "plus": '<path d="M5 12h14M12 5v14"/>',
    "copy": '<rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "save": '<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zM17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7M7 3v4a1 1 0 0 0 1 1h7"/>',
    "usb": '<circle cx="10" cy="7" r="1"/><circle cx="4" cy="20" r="1"/><path d="M4.7 19.3 19 5m2-2-3 1 2 2ZM9.26 7.68 5 12l2 5m3-3 5 2 3.5-3.5m-.5-1.5 1-1 1 1-1 1Z"/>',
    "download": '<path d="M12 17V3m-6 8 6 6 6-6M19 21H5"/>',
    "undo": '<path d="m9 14-5-5 5-5M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    "paste": '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>',
    "more": '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
    "stop": '<rect width="18" height="18" x="3" y="3" rx="2"/>',
    "chevron": '<path d="m6 9 6 6 6-6"/>',
}


@lru_cache(maxsize=128)
def icon(name, color, disabled=None):
    result = QIcon()
    for mode, stroke in ((QIcon.Normal, color), (QIcon.Disabled, disabled or color)):
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
            'viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (stroke, PATHS[name])
        )
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        QSvgRenderer(QByteArray(svg.encode())).render(painter)
        painter.end()
        pixmap.setDevicePixelRatio(2)
        result.addPixmap(pixmap, mode)
    return result


def refresh_icons(root, colors):
    for control in root.findChildren(QPushButton):
        name = control.property("iconName")
        if name:
            foreground = (
                colors["primary_text"] if control.objectName() == "primary" else colors["text"]
            )
            control.setIcon(icon(name, foreground, colors["disabled"]))
            control.setIconSize(QSize(16, 16))
