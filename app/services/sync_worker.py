from __future__ import annotations

import fnmatch
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot

from app.models import SyncResult, Task, now_iso
from app.services.logger import new_task_log_path
from app.services.process_utils import hidden_process_kwargs


class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    output = pyqtSignal(int, str)


def robocopy_status(exit_code: int) -> str:
    if exit_code in (0, 1):
        return "success"
    if 2 <= exit_code <= 7:
        return "warning"
    return "error"


def split_exclusions(patterns: list[str]) -> tuple[list[str], list[str]]:
    files: list[str] = []
    dirs: list[str] = []
    for pattern in patterns:
        clean = pattern.strip()
        if not clean:
            continue
        if any(ch in clean for ch in "*?"):
            files.append(clean)
        else:
            dirs.append(clean)
    return dirs, files


def build_robocopy_command(task: Task, dry_run_override: bool = False) -> list[str]:
    command = ["robocopy", task.source_path, task.destination_path]
    command.append("/MIR" if int(task.mirror_delete) else "/E")
    command.extend(["/Z", "/R:2", "/W:5", "/MT:8", "/FFT", "/XJ"])
    if int(task.dry_run) or dry_run_override:
        command.append("/L")
    excluded_dirs, excluded_files = split_exclusions(task.exclusions())
    if excluded_dirs:
        command.append("/XD")
        command.extend(excluded_dirs)
    if excluded_files:
        command.append("/XF")
        command.extend(excluded_files)
    return command


def should_ignore_path(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    for pattern in patterns:
        clean = pattern.strip()
        if not clean:
            continue
        if fnmatch.fnmatch(Path(normalized).name, clean):
            return True
        if clean in parts:
            return True
    return False


class SyncWorker(QRunnable):
    def __init__(self, task: Task, dry_run_override: bool = False) -> None:
        super().__init__()
        if task.id is None:
            raise ValueError("Task id is required")
        self.task = task
        self.dry_run_override = dry_run_override
        self.signals = WorkerSignals()
        self.process: subprocess.Popen | None = None
        self.cancel_requested = False

    def cancel(self) -> None:
        self.cancel_requested = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    self.process.kill()
                except OSError:
                    pass
            except OSError:
                pass

    @pyqtSlot()
    def run(self) -> None:
        started_dt = datetime.now()
        started_at = started_dt.replace(microsecond=0).isoformat()
        log_path = new_task_log_path(int(self.task.id), started_dt)
        command = build_robocopy_command(self.task, self.dry_run_override)
        status = "error"
        exit_code: int | None = None
        error_message: str | None = None

        with open(log_path, "w", encoding="utf-8", errors="replace") as log:
            self._write_header(log, started_at, command)
            try:
                self.process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    **hidden_process_kwargs(),
                )
                assert self.process.stdout is not None
                for line in self.process.stdout:
                    log.write(line)
                    log.flush()
                    self.signals.output.emit(int(self.task.id), line.rstrip())
                exit_code = self.process.wait()
                if self.cancel_requested:
                    status = "error"
                    error_message = "Ejecucion cancelada por el usuario"
                else:
                    status = robocopy_status(exit_code)
                    if status == "warning":
                        error_message = f"Robocopy termino con advertencias (codigo {exit_code})"
                    elif status == "error":
                        error_message = f"Robocopy fallo (codigo {exit_code})"
            except FileNotFoundError:
                error_message = "No se encontro robocopy en el sistema"
                log.write(f"\nERROR: {error_message}\n")
            except OSError as exc:
                error_message = str(exc)
                log.write(f"\nERROR: {error_message}\n")
            finally:
                self.process = None

            finished_at = now_iso()
            log.write("\n")
            log.write(f"Codigo de salida: {exit_code}\n")
            log.write(f"Estado: {status}\n")
            log.write(f"Fecha de fin: {finished_at}\n")

        result = SyncResult(
            task_id=int(self.task.id),
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            robocopy_exit_code=exit_code,
            log_path=str(log_path),
            error_message=error_message,
            dry_run=bool(int(self.task.dry_run) or self.dry_run_override),
        )
        self.signals.finished.emit(result)

    def _write_header(self, log, started_at: str, command: list[str]) -> None:
        mode = "SI" if int(self.task.dry_run) or self.dry_run_override else "NO"
        log.write(f"Fecha de inicio: {started_at}\n")
        log.write(f"Tarea: {self.task.name} (ID {self.task.id})\n")
        log.write(f"Origen: {self.task.source_path}\n")
        log.write(f"Destino: {self.task.destination_path}\n")
        log.write(f"Modo prueba: {mode}\n")
        log.write(f"Comando: {subprocess.list2cmdline(command)}\n")
        log.write("\n--- Salida robocopy ---\n")
