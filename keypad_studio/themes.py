"""Neutral shadcn/Tailwind v3 surfaces; UI colors never alter device RGB values.

References: https://v3.shadcn.com/colors and
https://www.uxdesigninstitute.com/blog/dark-mode-design-practical-guide/
"""

ACCENT = "#3a86ff"

PALETTES = {
    "dark": {
        "background": "#171717",
        "surface": "#202020",
        "raised": "#262626",
        "text": "#e5e5e5",
        "heading": "#fafafa",
        "muted": "#a3a3a3",
        "border": "#525252",
        "divider": "#333333",
        "hover": "#303030",
        "selected": "#172c4c",
        "selected_text": "#dbeafe",
        "focus": ACCENT,
        "primary": "#2563eb",
        "primary_text": "#ffffff",
        "disabled": "#737373",
        "pico": "#292929",
        "pico_text": "#a3a3a3",
        "status": "#93c5fd",
        "key": "#303030",
        "key_hover": "#383838",
        "key_edge": "#484848",
        "shadow": "#121212",
        "warning": "#fcd34d",
    },
    "light": {
        "background": "#f5f5f5",
        "surface": "#fafafa",
        "raised": "#ffffff",
        "text": "#262626",
        "heading": "#171717",
        "muted": "#525252",
        "border": "#b4b4b4",
        "divider": "#e5e5e5",
        "hover": "#eeeeee",
        "selected": "#e8f0ff",
        "selected_text": "#1e3a8a",
        "focus": ACCENT,
        "primary": "#2563eb",
        "primary_text": "#ffffff",
        "disabled": "#a3a3a3",
        "pico": "#e9e9e9",
        "pico_text": "#525252",
        "status": "#1d4ed8",
        "key": "#ffffff",
        "key_hover": "#f5f5f5",
        "key_edge": "#d4d4d4",
        "shadow": "#d4d4d4",
        "warning": "#92400e",
    },
}


def stylesheet(mode):
    return """
    QWidget {{ color:{text}; font-size:13px; }}
    QMainWindow,QDialog {{ background:{background}; }}
    QLabel {{ background:transparent; }}
    QLabel#muted,QLabel#caption {{ color:{muted}; font-size:12px; }}
    QLabel#section {{ color:{heading}; font-size:13px; font-weight:600; }}
    QLabel#title {{ color:{heading}; font-size:26px; font-weight:600; }}
    QLabel#appTitle {{ color:{heading}; font-size:18px; font-weight:600; }}
    QLabel#keyTitle {{ color:{heading}; font-size:20px; font-weight:600; }}
    QLabel#brand {{ background:{selected}; border-radius:10px; }}
    QWidget#header {{ background:{surface}; border-bottom:1px solid {divider}; }}
    QWidget#sidebar,QWidget#inspector {{ background:{surface}; }}
    QWidget#sidebar {{ border-right:1px solid {divider}; }}
    QWidget#inspector {{ border-left:1px solid {divider}; }}
    QWidget#board {{ background:{pico}; border:1px solid {key_edge}; border-radius:24px; }}
    QLabel#pico {{ color:{pico_text}; font-size:11px; background:{surface}; border:1px solid {key_edge}; border-radius:8px; }}
    QLabel#connection {{ background:{raised}; border:1px solid {divider}; border-radius:14px; padding:5px 10px; color:{muted}; font-size:12px; }}
    QLabel#connection[connected="true"] {{ color:{status}; background:{selected}; border-color:{selected}; }}
    QLabel#saved {{ color:{muted}; font-size:12px; }}
    QLabel#saved[dirty="true"] {{ color:{warning}; }}
    QLabel#capability {{ background:{selected}; color:{selected_text}; border-radius:6px; padding:8px 10px; font-size:12px; }}
    QLabel#notice {{ color:{muted}; font-size:12px; padding:8px 0; }}
    QPushButton {{ background:{raised}; border:1px solid {border}; border-radius:7px; padding:8px 12px; font-weight:500; min-height:16px; }}
    QPushButton:hover {{ background:{hover}; border-color:{muted}; }}
    QPushButton:pressed {{ background:{divider}; }}
    QPushButton:focus {{ border:2px solid {focus}; padding:7px 11px; }}
    QPushButton:disabled {{ color:{disabled}; border-color:{divider}; background:{surface}; }}
    QPushButton#primary {{ background:{primary}; border-color:{primary}; color:{primary_text}; font-weight:600; }}
    QPushButton#primary:hover {{ border-color:{focus}; }}
    QPushButton[variant="ghost"] {{ background:transparent; border-color:transparent; }}
    QPushButton[variant="ghost"]:hover {{ background:{hover}; }}
    QPushButton[variant="ghost"]:focus {{ border-color:{focus}; }}
    QPushButton[variant="subtle"] {{ background:{hover}; border-color:{divider}; }}
    QPushButton::menu-indicator {{ subcontrol-position:right center; right:9px; }}
    QPushButton[hideMenuIndicator="true"]::menu-indicator {{ image:none; width:0; }}
    QListWidget {{ background:transparent; border:0; outline:0; padding:0; }}
    QListWidget::item {{ padding:10px; border-radius:7px; margin-bottom:4px; }}
    QListWidget::item:hover {{ background:{hover}; }}
    QListWidget::item:selected {{ background:{selected}; color:{selected_text}; }}
    QListWidget:focus {{ border:1px solid {focus}; border-radius:7px; }}
    QLineEdit,QPlainTextEdit,QSpinBox,QDoubleSpinBox,QComboBox {{ background:{raised}; border:1px solid {border}; border-radius:6px; padding:8px; selection-background-color:{selected}; selection-color:{selected_text}; min-height:16px; }}
    QLineEdit:focus,QPlainTextEdit:focus,QSpinBox:focus,QDoubleSpinBox:focus,QComboBox:focus {{ border:2px solid {focus}; padding:7px; }}
    QLineEdit:disabled,QSpinBox:disabled,QDoubleSpinBox:disabled,QComboBox:disabled {{ color:{disabled}; background:{surface}; border-color:{divider}; }}
    QComboBox {{ padding-right:28px; }}
    QComboBox:focus {{ padding-right:27px; }}
    QComboBox::drop-down {{ border:0; width:25px; }}
    QComboBox::down-arrow {{ image:none; }}
    QComboBox QAbstractItemView {{ background:{raised}; color:{text}; selection-background-color:{selected}; selection-color:{selected_text}; border:1px solid {border}; padding:4px; outline:0; }}
    QTabWidget::pane {{ border:0; background:transparent; }}
    QTabBar {{ background:transparent; }}
    QTabBar::tab {{ padding:11px 16px; color:{muted}; background:transparent; border-bottom:2px solid {divider}; }}
    QTabBar::tab:selected {{ color:{heading}; border-bottom-color:{focus}; font-weight:600; }}
    QTabBar::tab:hover {{ color:{heading}; background:{hover}; }}
    QTabBar::tab:focus {{ border:1px solid {focus}; }}
    QScrollArea {{ border:0; background:transparent; }}
    QScrollArea > QWidget > QWidget {{ background:transparent; }}
    QScrollBar:vertical {{ width:8px; background:transparent; margin:3px 0; }}
    QScrollBar::handle:vertical {{ background:{border}; border-radius:4px; min-height:30px; }}
    QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0; }}
    QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {{ background:transparent; }}
    QStatusBar {{ color:{muted}; background:{surface}; border-top:1px solid {divider}; font-size:12px; padding:3px 12px; }}
    QStatusBar::item {{ border:0; }}
    QSplitter::handle {{ background:transparent; }}
    QSplitter::handle:hover {{ background:{divider}; }}
    QToolTip {{ background:{raised}; color:{text}; border:1px solid {border}; padding:5px; }}
    QCheckBox {{ spacing:8px; background:transparent; }}
    QCheckBox::indicator {{ width:16px; height:16px; border:1px solid {border}; border-radius:4px; background:{raised}; }}
    QCheckBox::indicator:checked {{ background:{focus}; border:3px solid {selected}; }}
    QCheckBox:focus {{ outline:1px solid {focus}; }}
    QMenu {{ background:{raised}; border:1px solid {divider}; padding:5px; border-radius:7px; }}
    QMenu::item {{ padding:8px 22px 8px 12px; border-radius:4px; }}
    QMenu::item:selected {{ background:{selected}; color:{selected_text}; }}
    QMenu::separator {{ height:1px; background:{divider}; margin:5px; }}
    QGroupBox {{ border:1px solid {divider}; border-radius:8px; margin-top:12px; padding-top:12px; }}
    QGroupBox::title {{ subcontrol-origin:margin; left:10px; padding:0 4px; color:{muted}; }}
    """.format(
        **PALETTES[mode]
    )


def apply_palette(application, mode):
    from PySide6.QtGui import QPalette, QColor

    c = PALETTES[mode]
    application.setProperty("keypadTheme", mode)
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
