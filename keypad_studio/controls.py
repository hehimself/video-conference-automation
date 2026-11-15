"""Qt primitives with consistent decoration; native keyboard/accessibility behavior."""

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QSizePolicy
from keypad_studio.icons import icon
from keypad_studio.themes import PALETTES


class ElidedLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def setText(self, text):
        super().setText(text)
        self.setToolTip(text)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().windowText().color())
        text = self.fontMetrics().elidedText(
            self.text(), Qt.ElideRight, self.contentsRect().width()
        )
        painter.drawText(self.contentsRect(), Qt.AlignLeft | Qt.AlignVCenter, text)


class ComboBox(QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        colors = PALETTES[QApplication.instance().property("keypadTheme") or "dark"]
        color = colors["muted"] if self.isEnabled() else colors["disabled"]
        painter = QPainter(self)
        x = 8 if self.layoutDirection() == Qt.RightToLeft else self.width() - 24
        icon("chevron", color).paint(painter, QRect(x, (self.height() - 16) // 2, 16, 16))
