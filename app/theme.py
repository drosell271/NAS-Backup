from __future__ import annotations

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication


BACKGROUND = "#0f141b"
SURFACE = "#151b24"
SURFACE_2 = "#1b2430"
BORDER = "#2a3442"
TEXT = "#e5e9f0"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
ACCENT_STRONG = "#0ea5e9"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ef4444"


def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.WindowText, QColor(TEXT))
    palette.setColor(QPalette.Base, QColor(SURFACE))
    palette.setColor(QPalette.AlternateBase, QColor(SURFACE_2))
    palette.setColor(QPalette.ToolTipBase, QColor(SURFACE_2))
    palette.setColor(QPalette.ToolTipText, QColor(TEXT))
    palette.setColor(QPalette.Text, QColor(TEXT))
    palette.setColor(QPalette.Button, QColor(SURFACE_2))
    palette.setColor(QPalette.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.Highlight, QColor(ACCENT_STRONG))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)


STYLESHEET = f"""
QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 10.5pt;
}}

QMainWindow::separator {{
    background: {BORDER};
    width: 1px;
    height: 1px;
}}

QMenuBar {{
    background-color: {BACKGROUND};
    border-bottom: 1px solid {BORDER};
    padding: 4px 8px;
}}

QMenuBar::item {{
    background: transparent;
    border-radius: 6px;
    padding: 6px 10px;
}}

QMenuBar::item:selected {{
    background-color: {SURFACE_2};
}}

QMenu {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    padding: 6px;
}}

QMenu::item {{
    border-radius: 6px;
    padding: 7px 26px 7px 12px;
}}

QMenu::item:selected {{
    background-color: {SURFACE_2};
}}

QPushButton {{
    background-color: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 7px;
    color: {TEXT};
    font-weight: 600;
    padding: 8px 14px;
}}

QPushButton:hover {{
    background-color: #223044;
    border-color: #3b4b5f;
}}

QPushButton:pressed {{
    background-color: #0b1118;
}}

QPushButton:disabled {{
    color: #64748b;
    background-color: #111827;
    border-color: #1f2937;
}}

QPushButton#addButton,
QPushButton#runButton,
QPushButton#saveButton {{
    background-color: {ACCENT_STRONG};
    border-color: {ACCENT};
    color: #03121d;
}}

QPushButton#addButton:hover,
QPushButton#runButton:hover,
QPushButton#saveButton:hover {{
    background-color: {ACCENT};
}}

QPushButton#deleteButton {{
    color: #fecaca;
}}

QPushButton#cancelRunButton {{
    color: #fed7aa;
}}

QPushButton#exitButton {{
    color: #fecaca;
    border-color: #7f1d1d;
}}

QPushButton#exitButton:hover {{
    background-color: #3b1216;
    border-color: {ERROR};
}}

QLineEdit,
QComboBox,
QSpinBox,
QPlainTextEdit {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 7px;
    color: {TEXT};
    padding: 8px 10px;
    selection-background-color: {ACCENT_STRONG};
}}

QPlainTextEdit {{
    font-family: "Cascadia Mono", "Consolas";
    font-size: 9.5pt;
}}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QPlainTextEdit:focus {{
    border-color: {ACCENT};
}}

QComboBox::drop-down {{
    border: 0;
    width: 28px;
}}

QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT_STRONG};
    outline: 0;
}}

QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background-color: {SURFACE};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_STRONG};
    border-color: {ACCENT};
}}

QTableWidget {{
    background-color: {SURFACE};
    alternate-background-color: #111923;
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: #202a38;
    selection-background-color: #12344a;
    selection-color: {TEXT};
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid #1d2633;
}}

QHeaderView::section {{
    background-color: #101722;
    border: 0;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    color: {MUTED};
    font-weight: 700;
    padding: 10px 8px;
}}

QStatusBar {{
    background-color: #0b1118;
    border-top: 1px solid {BORDER};
}}

QStatusBar QLabel {{
    color: {MUTED};
    padding: 2px 8px;
}}

QScrollBar:vertical {{
    background: {SURFACE};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #334155;
    min-height: 28px;
    border-radius: 6px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QDialog {{
    background-color: {BACKGROUND};
}}

QLabel {{
    color: {TEXT};
}}

QLabel#appTitleLabel {{
    color: #f8fafc;
    font-size: 18pt;
    font-weight: 700;
}}

QLabel#appSubtitleLabel {{
    color: {MUTED};
    font-size: 10pt;
}}

QLabel#logoLabel {{
    background-color: transparent;
}}
"""
