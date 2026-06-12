from __future__ import annotations

from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QDialog, QMessageBox, QPushButton

from app.config import BASE_DIR, UI_DIR
from app.database import Database
from app.icons import create_icon
from app.services import autostart


class SettingsDialog(QDialog):
    def __init__(self, database: Database, parent=None) -> None:
        super().__init__(parent)
        uic.loadUi(str(UI_DIR / "settings_dialog.ui"), self)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.database = database
        self.settings = database.get_settings()
        self._load_settings()
        self.saveButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self._setup_button_icons()

    def _setup_button_icons(self) -> None:
        self.saveButton.setIcon(create_icon("save"))
        self.cancelButton.setIcon(create_icon("cancel"))
        for button in self.findChildren(QPushButton):
            button.setIconSize(QSize(20, 20))
            button.setMinimumHeight(40)
            button.setCursor(Qt.PointingHandCursor)

    def _load_settings(self) -> None:
        self.startWithWindowsCheck.setChecked(self.settings.get("start_with_windows", "0") == "1")
        self.startMinimizedCheck.setChecked(self.settings.get("start_minimized", "0") == "1")
        self.maxParallelSpin.setValue(_int_setting(self.settings, "max_parallel_tasks", 2))
        self.notifySuccessCheck.setChecked(self.settings.get("notify_on_success", "1") == "1")
        self.notifyErrorCheck.setChecked(self.settings.get("notify_on_error", "1") == "1")
        self.debounceSpin.setValue(_int_setting(self.settings, "default_debounce_seconds", 5))
        self.retentionSpin.setValue(_int_setting(self.settings, "log_retention_days", 30))

    def accept(self) -> None:
        values = {
            "start_with_windows": "1" if self.startWithWindowsCheck.isChecked() else "0",
            "start_minimized": "1" if self.startMinimizedCheck.isChecked() else "0",
            "max_parallel_tasks": str(self.maxParallelSpin.value()),
            "notify_on_success": "1" if self.notifySuccessCheck.isChecked() else "0",
            "notify_on_error": "1" if self.notifyErrorCheck.isChecked() else "0",
            "default_debounce_seconds": str(self.debounceSpin.value()),
            "log_retention_days": str(self.retentionSpin.value()),
        }
        try:
            main_path = BASE_DIR / "main.py"
            if values["start_with_windows"] == "1":
                autostart.enable_autostart(autostart.build_autostart_command(Path(main_path)))
            else:
                autostart.disable_autostart()
        except OSError as exc:
            QMessageBox.warning(self, "Autoarranque", f"No se pudo actualizar el registro de Windows:\n{exc}")
            return
        self.database.set_settings(values)
        super().accept()


def _int_setting(settings: dict[str, str], key: str, default: int) -> int:
    try:
        return int(settings.get(key, str(default)))
    except ValueError:
        return default
