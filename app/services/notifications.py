from __future__ import annotations

from PyQt5.QtWidgets import QSystemTrayIcon


def notify(tray_icon: QSystemTrayIcon | None, title: str, message: str, enabled: bool = True) -> None:
    if not enabled or tray_icon is None or not tray_icon.isVisible():
        return
    tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)
