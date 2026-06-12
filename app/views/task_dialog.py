from __future__ import annotations

import os

from PyQt5 import uic
from PyQt5.QtCore import QObject, QRunnable, QSize, QThreadPool, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox, QPushButton

from app.config import DEFAULT_EXCLUSIONS, UI_DIR
from app.icons import create_icon
from app.models import TASK_MODES, Task, exclusions_to_json, parse_exclusions
from app.services.network_checker import can_run_task, get_available_networks
from app.validation import validate_task_data


MODE_LABELS = {
    "manual": "Solo manual",
    "interval": "Cada X minutos",
    "changes": "Cuando haya cambios",
    "both": "Ambas",
}

INTERVAL_OPTIONS = (
    ("5 minutos", 5),
    ("10 minutos", 10),
    ("15 minutos", 15),
    ("30 minutos", 30),
    ("1 hora", 60),
    ("2 horas", 120),
    ("4 horas", 240),
    ("8 horas", 480),
    ("1 dia", 1440),
)


class NetworkScanSignals(QObject):
    finished = pyqtSignal(list)


class NetworkScanWorker(QRunnable):
    def __init__(self) -> None:
        super().__init__()
        self.signals = NetworkScanSignals()

    @pyqtSlot()
    def run(self) -> None:
        self.signals.finished.emit(get_available_networks())


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Task | None = None) -> None:
        super().__init__(parent)
        uic.loadUi(str(UI_DIR / "task_dialog.ui"), self)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.task = task
        self.network_scan_worker: NetworkScanWorker | None = None
        self._setup()
        if task:
            self._load_task(task)
        else:
            self.exclusionsEdit.setPlainText("\n".join(DEFAULT_EXCLUSIONS))

    def _setup(self) -> None:
        self.modeCombo.clear()
        for mode in TASK_MODES:
            self.modeCombo.addItem(MODE_LABELS[mode], mode)
        self.intervalCombo.clear()
        for label, minutes in INTERVAL_OPTIONS:
            self.intervalCombo.addItem(label, minutes)
        self.networkCombo.addItem("Cualquier red", "")
        self._load_networks_async()
        self.browseSourceButton.clicked.connect(self._browse_source)
        self.browseDestinationButton.clicked.connect(self._browse_destination)
        self.refreshNetworksButton.clicked.connect(self._load_networks_async)
        self.testConnectionButton.clicked.connect(self._test_connection)
        self.saveButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self._setup_button_icons()

    def _setup_button_icons(self) -> None:
        icon_map = {
            self.browseSourceButton: "folder",
            self.browseDestinationButton: "folder",
            self.refreshNetworksButton: "refresh",
            self.testConnectionButton: "test",
            self.saveButton: "save",
            self.cancelButton: "cancel",
        }
        for button, icon_name in icon_map.items():
            button.setIcon(create_icon(icon_name))
            button.setIconSize(QSize(20, 20))
            button.setMinimumHeight(40)
        for button in self.findChildren(QPushButton):
            button.setCursor(Qt.PointingHandCursor)

    def _load_networks_async(self) -> None:
        current = self.networkCombo.currentText().strip() if hasattr(self, "networkCombo") else ""
        self.networkCombo.blockSignals(True)
        self.networkCombo.clear()
        self.networkCombo.addItem("Escaneando redes...", "")
        if current and current != "Escaneando redes...":
            self.networkCombo.addItem(current, current)
            self.networkCombo.setCurrentIndex(1)
        self.networkCombo.blockSignals(False)
        self.refreshNetworksButton.setEnabled(False)
        self.network_scan_worker = NetworkScanWorker()
        self.network_scan_worker.signals.finished.connect(lambda networks: self._on_networks_loaded(networks, self.networkCombo.currentText().strip()))
        QThreadPool.globalInstance().start(self.network_scan_worker)

    def _on_networks_loaded(self, networks: list[str], selected: str) -> None:
        self.networkCombo.blockSignals(True)
        self.networkCombo.clear()
        self.networkCombo.addItem("Cualquier red", "")
        for network in networks:
            self.networkCombo.addItem(network, network)
        if selected and selected not in {"Escaneando redes...", "Cualquier red"}:
            index = self.networkCombo.findText(selected)
            if index < 0:
                self.networkCombo.addItem(selected, selected)
                index = self.networkCombo.findText(selected)
            self.networkCombo.setCurrentIndex(index)
        else:
            self.networkCombo.setCurrentIndex(0)
        self.networkCombo.blockSignals(False)
        self.refreshNetworksButton.setEnabled(True)
        self.network_scan_worker = None

    def _load_task(self, task: Task) -> None:
        self.nameEdit.setText(task.name)
        self.sourceEdit.setText(task.source_path)
        self.destinationEdit.setText(task.destination_path)
        self.serverIpEdit.setText(task.server_ip)
        self._set_network(task.required_network or "")
        index = self.modeCombo.findData(task.mode)
        self.modeCombo.setCurrentIndex(max(0, index))
        self._set_interval(task.interval_minutes)
        self.enabledCheck.setChecked(bool(task.enabled))
        self.mirrorDeleteCheck.setChecked(bool(task.mirror_delete))
        self.dryRunCheck.setChecked(bool(task.dry_run))
        self.exclusionsEdit.setPlainText("\n".join(parse_exclusions(task.exclude_patterns)))

    def _set_network(self, network: str) -> None:
        index = self.networkCombo.findData(network)
        if index < 0:
            index = self.networkCombo.findText(network)
        if index < 0 and network:
            self.networkCombo.addItem(network, network)
            index = self.networkCombo.findText(network)
        self.networkCombo.setCurrentIndex(max(0, index))

    def _set_interval(self, minutes: int | None) -> None:
        if not minutes:
            self.intervalCombo.setCurrentIndex(0)
            return
        index = self.intervalCombo.findData(minutes)
        if index < 0:
            self.intervalCombo.addItem(f"{minutes} minutos", minutes)
            index = self.intervalCombo.findData(minutes)
        self.intervalCombo.setCurrentIndex(max(0, index))

    def _browse_source(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta origen", self.sourceEdit.text())
        if path:
            self.sourceEdit.setText(path)

    def _browse_destination(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta destino", self.destinationEdit.text())
        if path:
            self.destinationEdit.setText(path)

    def _test_connection(self) -> None:
        task = self.to_task(validate=False)
        ok, reason = can_run_task(task)
        icon = QMessageBox.Information if ok else QMessageBox.Warning
        QMessageBox(icon, "Prueba de conexion", reason, QMessageBox.Ok, self).exec_()

    def accept(self) -> None:
        task = self.to_task(validate=False)
        error = self.validate_task(task)
        if error:
            QMessageBox.warning(self, "Validacion", error)
            return
        if task.mirror_delete:
            if is_dangerous_mirror_destination(task.destination_path):
                QMessageBox.critical(
                    self,
                    "Destino no permitido",
                    "El destino es demasiado general para usar borrado espejo.",
                )
                return
            answer = QMessageBox.warning(
                self,
                "Confirmar borrado espejo",
                "Esta opcion permite que robocopy borre en destino lo que no exista en origen.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
        super().accept()

    def validate_task(self, task: Task) -> str | None:
        return validate_task_data(task, require_existing_source=True)

    def to_task(self, validate: bool = True) -> Task:
        mode = self.modeCombo.currentData() or "manual"
        interval = self.intervalCombo.currentData()
        interval = int(interval) if interval is not None else None
        exclusions = self.exclusionsEdit.toPlainText()
        network = self.networkCombo.currentData()
        if network is None:
            network = self.networkCombo.currentText()
        return Task(
            id=self.task.id if self.task else None,
            name=self.nameEdit.text().strip(),
            source_path=self.sourceEdit.text().strip(),
            destination_path=self.destinationEdit.text().strip(),
            server_ip=self.serverIpEdit.text().strip(),
            required_network=str(network).strip() or None,
            mode=mode,
            interval_minutes=interval,
            watch_changes=1 if mode in ("changes", "both") else 0,
            enabled=int(self.enabledCheck.isChecked()),
            mirror_delete=int(self.mirrorDeleteCheck.isChecked()),
            dry_run=int(self.dryRunCheck.isChecked()),
            exclude_patterns=exclusions_to_json(exclusions),
            last_run_at=self.task.last_run_at if self.task else None,
            last_success_at=self.task.last_success_at if self.task else None,
            last_error=self.task.last_error if self.task else None,
            created_at=self.task.created_at if self.task else None,
            updated_at=self.task.updated_at if self.task else None,
        )


def is_dangerous_mirror_destination(destination: str) -> bool:
    dest = destination.strip().replace("/", "\\").rstrip("\\")
    if not dest:
        return True
    drive, tail = os.path.splitdrive(dest)
    if drive and not tail.strip("\\"):
        return True
    if dest.startswith("\\\\"):
        parts = [part for part in dest.split("\\") if part]
        return len(parts) <= 2
    return False
