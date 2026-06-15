from __future__ import annotations

import argparse
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication

from app.config import APP_NAME, asset_path, ensure_directories
from app.services.single_instance import SingleInstance
from app.theme import apply_dark_theme
from app.views.main_window import MainWindow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--minimized", action="store_true", help="Arrancar en la bandeja del sistema")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_directories()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    single_instance = SingleInstance()
    if not single_instance.acquire():
        return 0
    app.setFont(QFont("Segoe UI", 10))
    icon_file = asset_path("icon.ico")
    if icon_file:
        app.setWindowIcon(QIcon(str(icon_file)))
    app.setQuitOnLastWindowClosed(False)
    apply_dark_theme(app)
    window = MainWindow(minimized=args.minimized)
    single_instance.activation_requested.connect(window.show_normal)
    app.single_instance = single_instance
    app.main_window = window
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
