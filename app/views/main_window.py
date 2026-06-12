from __future__ import annotations

import os
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.config import UI_DIR, asset_path
from app.database import Database
from app.icons import create_icon
from app.services.config_exporter import export_config, import_config
from app.services.logger import cleanup_old_logs
from app.services.notifications import notify
from app.services.scheduler import ChangeWatcher, IntervalScheduler
from app.services.task_manager import TaskManager
from app.services.tray import TrayService
from app.views.settings_dialog import SettingsDialog
from app.views.task_dialog import TaskDialog


STATUS_LABELS = {
    "disabled": "Desactivada",
    "idle": "Lista",
    "waiting_network": "Esperando red",
    "scheduled": "Programada",
    "running": "En ejecucion",
    "success": "Correcta",
    "warning": "Advertencia",
    "error": "Error",
    "paused": "Pausada",
}

STATUS_COLORS = {
    "disabled": "#64748b",
    "idle": "#94a3b8",
    "waiting_network": "#38bdf8",
    "scheduled": "#a78bfa",
    "running": "#0ea5e9",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "paused": "#f97316",
}


class MainWindow(QMainWindow):
    def __init__(self, minimized: bool = False) -> None:
        super().__init__()
        uic.loadUi(str(UI_DIR / "main_window.ui"), self)
        self.database = Database()
        self.database.initialize()
        self._cleanup_logs()
        self.task_manager = TaskManager(self.database)
        self.scheduler = IntervalScheduler(self.database, self.task_manager)
        self.change_watcher = ChangeWatcher(self.database, self.task_manager)
        self.tray = TrayService(self, self.task_manager)
        self.exiting = False
        self._setup_ui()
        self._connect()
        self.refresh_tasks()
        self.scheduler.start()
        self.change_watcher.restart()
        self.tray.show()
        if not minimized:
            self._show_initial_window()

    def _setup_ui(self) -> None:
        self._setup_branding()
        self.statusbar.addPermanentWidget(self.statusLabel)
        header = self.taskTable.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.taskTable.setColumnWidth(0, 190)
        self.taskTable.setColumnWidth(3, 175)
        self.taskTable.setColumnWidth(4, 135)
        self.taskTable.setColumnWidth(5, 180)
        self.taskTable.setColumnWidth(6, 220)
        self.taskTable.verticalHeader().setVisible(False)
        self.taskTable.verticalHeader().setDefaultSectionSize(42)
        self.taskTable.setShowGrid(False)
        self.taskTable.setWordWrap(False)
        self.logText.setMaximumBlockCount(500)
        self._setup_button_icons()

    def _show_initial_window(self) -> None:
        screen = self.screen() or QApplication.primaryScreen()
        if screen is None:
            self.resize(1600, 960)
            self.show()
            return

        available = screen.availableGeometry()
        if available.width() <= 1600 or available.height() <= 950:
            self.showMaximized()
            return

        width = min(1680, int(available.width() * 0.92))
        height = min(980, int(available.height() * 0.90))
        self.resize(width, height)
        self.move(
            available.x() + (available.width() - width) // 2,
            available.y() + (available.height() - height) // 2,
        )
        self.show()

    def _setup_branding(self) -> None:
        icon_file = asset_path("icon.ico")
        if icon_file:
            self.setWindowIcon(QIcon(str(icon_file)))
        logo_file = asset_path("logo.png")
        if logo_file:
            pixmap = QPixmap(str(logo_file))
            if not pixmap.isNull():
                self.logoLabel.setPixmap(
                    pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.logoLabel.setVisible(True)
                return
        self.logoLabel.setVisible(False)

    def _setup_button_icons(self) -> None:
        button_specs = {
            self.addButton: ("add", "Crear una nueva tarea", 160, QColor("#03121d")),
            self.editButton: ("edit", "Editar la tarea seleccionada", 115, QColor("#f1f5f9")),
            self.deleteButton: ("delete", "Eliminar la tarea seleccionada", 125, QColor("#fecaca")),
            self.runButton: ("run", "Ejecutar la tarea seleccionada ahora", 155, QColor("#03121d")),
            self.dryRunButton: ("test", "Simular la copia sin modificar archivos", 170, QColor("#f1f5f9")),
            self.cancelRunButton: ("cancel", "Cancelar la ejecucion en curso", 135, QColor("#fed7aa")),
            self.pauseButton: ("pause", "Pausar o reanudar la tarea seleccionada", 180, QColor("#f1f5f9")),
            self.logButton: ("log", "Abrir el ultimo log de la tarea", 130, QColor("#f1f5f9")),
            self.historyButton: ("history", "Ver historial de ejecuciones", 130, QColor("#f1f5f9")),
            self.exitButton: ("exit", "Cerrar completamente la aplicacion", 100, QColor("#fecaca")),
        }
        for button, (icon_name, tooltip, width, color) in button_specs.items():
            button.setIcon(create_icon(icon_name, color))
            button.setIconSize(QSize(22, 22))
            button.setToolTip(tooltip)
            button.setMinimumWidth(width)
            button.setMinimumHeight(44)
            button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        for button in self.findChildren(QPushButton):
            button.setCursor(Qt.PointingHandCursor)

    def _connect(self) -> None:
        self.addButton.clicked.connect(self.add_task)
        self.editButton.clicked.connect(self.edit_task)
        self.deleteButton.clicked.connect(self.delete_task)
        self.runButton.clicked.connect(self.run_selected)
        self.pauseButton.clicked.connect(self.pause_or_resume_selected)
        self.dryRunButton.clicked.connect(self.dry_run_selected)
        self.cancelRunButton.clicked.connect(self.cancel_selected)
        self.logButton.clicked.connect(self.open_last_log)
        self.historyButton.clicked.connect(self.show_history)
        self.exitButton.clicked.connect(self.exit_application)
        self.actionSettings.triggered.connect(self.open_settings)
        self.actionExportConfig.triggered.connect(self.export_configuration)
        self.actionImportConfig.triggered.connect(self.import_configuration)
        self.actionExit.triggered.connect(self.exit_application)
        self.taskTable.itemDoubleClicked.connect(lambda _item: self.edit_task())
        self.task_manager.tasks_changed.connect(self.refresh_tasks)
        self.task_manager.status_changed.connect(self._on_status_changed)
        self.task_manager.log_message.connect(self.append_log)
        self.task_manager.run_finished.connect(self._on_run_finished)

    def _cleanup_logs(self) -> None:
        settings = self.database.get_settings()
        try:
            retention_days = int(settings.get("log_retention_days", "30"))
        except ValueError:
            retention_days = 30
        cleanup_old_logs(retention_days)

    def selected_task_id(self) -> int | None:
        row = self.taskTable.currentRow()
        if row < 0:
            return None
        item = self.taskTable.item(row, 0)
        if item is None:
            return None
        value = item.data(Qt.UserRole)
        return int(value) if value is not None else None

    def add_task(self) -> None:
        dialog = TaskDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.task_manager.create_task(dialog.to_task())
            self.change_watcher.restart()

    def edit_task(self) -> None:
        task_id = self.selected_task_id()
        if task_id is None:
            QMessageBox.information(self, "Editar", "Selecciona una tarea.")
            return
        task = self.database.get_task(task_id)
        if task is None:
            return
        dialog = TaskDialog(self, task)
        if dialog.exec_() == QDialog.Accepted:
            self.task_manager.update_task(dialog.to_task())
            self.change_watcher.restart()

    def delete_task(self) -> None:
        task_id = self.selected_task_id()
        if task_id is None:
            QMessageBox.information(self, "Eliminar", "Selecciona una tarea.")
            return
        answer = QMessageBox.question(self, "Eliminar", "Eliminar la tarea seleccionada?")
        if answer == QMessageBox.Yes:
            self.task_manager.delete_task(task_id)
            self.change_watcher.restart()

    def run_selected(self) -> None:
        task_id = self.selected_task_id()
        if task_id is not None:
            self.task_manager.run_task(task_id, automatic=False)

    def dry_run_selected(self) -> None:
        task_id = self.selected_task_id()
        if task_id is not None:
            self.task_manager.run_task(task_id, dry_run_override=True, automatic=False)

    def cancel_selected(self) -> None:
        task_id = self.selected_task_id()
        if task_id is not None:
            self.task_manager.cancel_task(task_id)

    def pause_or_resume_selected(self) -> None:
        task_id = self.selected_task_id()
        if task_id is None:
            return
        if task_id in self.task_manager.paused:
            self.task_manager.resume_task(task_id)
        else:
            self.task_manager.pause_task(task_id)

    def open_last_log(self) -> None:
        task_id = self.selected_task_id()
        if task_id is None:
            QMessageBox.information(self, "Log", "Selecciona una tarea.")
            return
        rows = self.database.get_recent_runs(limit=1, task_id=task_id)
        if not rows or not rows[0]["log_path"]:
            QMessageBox.information(self, "Log", "La tarea no tiene logs todavia.")
            return
        path = Path(rows[0]["log_path"])
        if not path.exists():
            QMessageBox.warning(self, "Log", "El archivo de log ya no existe.")
            return
        os.startfile(path)

    def show_history(self) -> None:
        rows = self.database.get_recent_runs(limit=100)
        dialog = QDialog(self)
        dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        dialog.setWindowTitle("Historial")
        dialog.resize(900, 420)
        layout = QVBoxLayout(dialog)
        table = QTableWidget(dialog)
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Tarea", "Estado", "Inicio", "Fin", "Codigo", "Log"])
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["task_name"],
                row["status"],
                row["started_at"],
                row["finished_at"] or "",
                "" if row["robocopy_exit_code"] is None else str(row["robocopy_exit_code"]),
                row["log_path"] or "",
            ]
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(str(value)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(table)
        dialog.exec_()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.database, self)
        if dialog.exec_() == QDialog.Accepted:
            self.task_manager.reload_settings()
            self.change_watcher.restart()
            self._cleanup_logs()

    def export_configuration(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Exportar configuracion", "", "JSON (*.json)")
        if not path:
            return
        export_config(self.database, path)
        QMessageBox.information(self, "Exportar", "Configuracion exportada.")

    def import_configuration(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Importar configuracion", "", "JSON (*.json)")
        if not path:
            return
        try:
            created = import_config(self.database, path)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Importar", str(exc))
            return
        self.task_manager.refresh_states()
        self.refresh_tasks()
        self.change_watcher.restart()
        QMessageBox.information(self, "Importar", f"Tareas importadas: {created}")

    def refresh_tasks(self) -> None:
        self.task_manager.refresh_states()
        tasks = self.database.get_tasks()
        self.taskTable.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            state = self.task_manager.get_state(task)
            values = [
                task.name,
                task.source_path,
                task.destination_path,
                task.required_network or "",
                STATUS_LABELS.get(state, state),
                task.last_run_at or "",
                task.last_error or task.last_success_at or "",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.UserRole, task.id)
                if column == 4:
                    color = STATUS_COLORS.get(state, "#94a3b8")
                    item.setForeground(QBrush(QColor(color)))
                    item.setTextAlignment(Qt.AlignCenter)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.taskTable.setItem(row, column, item)
        self.statusLabel.setText(f"{len(tasks)} tarea(s)")

    def append_log(self, message: str) -> None:
        if not message:
            return
        self.logText.appendPlainText(message)

    def _on_status_changed(self, _task_id: int, _status: str, message: str) -> None:
        self.statusLabel.setText(message)
        self.append_log(message)

    def _on_run_finished(self, result) -> None:
        settings = self.database.get_settings()
        if result.status == "success":
            notify(self.tray.icon, "NAS Backup", "Copia finalizada correctamente.", settings.get("notify_on_success", "1") == "1")
        elif result.status == "error":
            notify(self.tray.icon, "NAS Backup", result.error_message or "La copia ha fallado.", settings.get("notify_on_error", "1") == "1")

    def show_normal(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        if self.exiting:
            self.change_watcher.stop()
            self.scheduler.stop()
            event.accept()
            return
        event.ignore()
        self.hide()
        self.tray.icon.showMessage("NAS Backup", "La aplicacion sigue funcionando en segundo plano.")

    def exit_application(self) -> None:
        self.exiting = True
        self.tray.icon.hide()
        self.change_watcher.stop()
        self.scheduler.stop()
        self.task_manager.shutdown()
        self.close()
        QApplication.quit()
