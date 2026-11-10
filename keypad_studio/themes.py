"""Neutral shadcn/Tailwind v3 surfaces; UI colors never alter device RGB values.

References: https://v3.shadcn.com/colors and
https://www.uxdesigninstitute.com/blog/dark-mode-design-practical-guide/
"""

PALETTES = {
    "dark": {
        "background": "#171717",
        "surface": "#262626",
        "raised": "#262626",
        "text": "#e5e5e5",
        "heading": "#f5f5f5",
        "muted": "#a3a3a3",
        "border": "#737373",
        "divider": "#404040",
        "hover": "#525252",
        "selected": "#134e4a",
        "selected_text": "#ccfbf1",
        "focus": "#5eead4",
        "primary": "#d4d4d4",
        "primary_text": "#171717",
        "disabled": "#737373",
        "pico": "#262626",
        "pico_text": "#d4d4d4",
        "status": "#99f6e4",
    },
    "light": {
        "background": "#fafafa",
        "surface": "#f5f5f5",
        "raised": "#ffffff",
        "text": "#262626",
        "heading": "#171717",
        "muted": "#525252",
        "border": "#737373",
        "divider": "#d4d4d4",
        "hover": "#e5e5e5",
        "selected": "#ccfbf1",
        "selected_text": "#134e4a",
        "focus": "#0f766e",
        "primary": "#262626",
        "primary_text": "#f5f5f5",
        "disabled": "#737373",
        "pico": "#e5e5e5",
        "pico_text": "#404040",
        "status": "#0f766e",
    },
}


def stylesheet(mode):
    c = PALETTES[mode]
    return """
    QWidget {{ background:{background}; color:{text}; font-family:'Helvetica Neue','Segoe UI'; font-size:13px; }}
    QLabel {{ background:transparent; }}
    QLabel#muted {{ color:{muted}; font-size:12px; }}
    QLabel#title {{ color:{heading}; font-size:25px; font-weight:600; }}
    QLabel#pico {{ background:{pico}; border:1px solid {border}; border-radius:12px; color:{pico_text}; font-size:12px; }}
    QLabel#connection {{ color:{status}; }}
    QWidget#board {{ background:{surface}; border:1px solid {divider}; border-radius:22px; }}
    QPushButton {{ background:{surface}; border:1px solid {border}; border-radius:7px; padding:8px 11px; }}
    QPushButton:hover {{ background:{hover}; }}
    QPushButton:focus {{ border:2px solid {focus}; padding:7px 10px; }}
    QPushButton:disabled {{ color:{disabled}; border-color:{divider}; }}
    QPushButton#primary {{ background:{primary}; border-color:{primary}; color:{primary_text}; font-weight:600; }}
    QListWidget {{ background:{surface}; border:0; border-radius:8px; padding:5px; }}
    QListWidget::item {{ padding:12px 7px; border-radius:6px; }}
    QListWidget::item:selected {{ background:{selected}; color:{selected_text}; }}
    QLineEdit,QPlainTextEdit,QSpinBox,QDoubleSpinBox,QComboBox {{ background:{raised}; border:1px solid {border}; border-radius:5px; padding:6px; selection-background-color:{selected}; selection-color:{selected_text}; }}
    QLineEdit:focus,QPlainTextEdit:focus,QSpinBox:focus,QDoubleSpinBox:focus,QComboBox:focus {{ border:2px solid {focus}; padding:5px; }}
    QComboBox QAbstractItemView {{ background:{raised}; color:{text}; selection-background-color:{selected}; selection-color:{selected_text}; }}
    QTabWidget::pane {{ border:0; }}
    QTabBar::tab {{ padding:10px; color:{muted}; background:{surface}; }}
    QTabBar::tab:selected {{ color:{text}; border-bottom:2px solid {focus}; }}
    QScrollArea {{ border:0; background:transparent; }}
    QStatusBar {{ color:{muted}; background:{surface}; }}
    QSplitter::handle {{ background:{divider}; }}
    QToolTip {{ background:{raised}; color:{text}; border:1px solid {border}; }}
    QCheckBox::indicator {{ width:16px; height:16px; border:1px solid {border}; border-radius:3px; background:{raised}; }}
    QCheckBox::indicator:checked {{ background:{focus}; border:3px solid {selected}; }}
    QCheckBox:focus {{ outline:1px solid {focus}; }}
    QMenu {{ background:{surface}; border:1px solid {border}; padding:6px; }}
    QMenu::item {{ padding:7px 16px; }}
    QMenu::item:selected {{ background:{selected}; color:{selected_text}; }}
    """.format(
        **c
    )


def apply_palette(application, mode):
    from PySide6.QtGui import QPalette, QColor

    c = PALETTES[mode]
    palette = QPalette()
    roles = {
        "Window": "background",
        "WindowText": "text",
        "Base": "raised",
        "AlternateBase": "surface",
        "ToolTipBase": "raised",
        "ToolTipText": "text",
        "Text": "text",
        "Button": "surface",
        "ButtonText": "text",
        "BrightText": "heading",
        "Highlight": "selected",
        "HighlightedText": "selected_text",
        "PlaceholderText": "muted",
    }
    for role, name in roles.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(c[name]))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        palette.setColor(QPalette.Disabled, role, QColor(c["disabled"]))
    application.setPalette(palette)
    application.setStyleSheet(stylesheet(mode))
