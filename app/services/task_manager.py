from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Deque

from PyQt5.QtCore import QObject, QThreadPool, QTimer, pyqtSignal

from app.database import Database
from app.models import SyncResult, Task
from app.services.network_checker import can_run_task, has_enough_destination_space
from app.services.sync_worker import SyncWorker


class TaskManager(QObject):
    tasks_changed = pyqtSignal()
    status_changed = pyqtSignal(int, str, str)
    run_finished = pyqtSignal(object)
    log_message = pyqtSignal(str)

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.pool = QThreadPool.globalInstance()
        self.running: set[int] = set()
        self.workers: dict[int, SyncWorker] = {}
        self.paused: set[int] = set()
        self.states: dict[int, str] = {}
        self.retry_after: dict[int, datetime] = {}
        self.retry_timers: dict[int, QTimer] = {}
        self.pending_change_runs: set[int] = set()
        self.queue: Deque[tuple[int, bool, bool]] = deque()
        self.reload_settings()
        self.refresh_states()

    def reload_settings(self) -> None:
        settings = self.database.get_settings()
        try:
            max_parallel = max(1, int(settings.get("max_parallel_tasks", "2")))
        except ValueError:
            max_parallel = 2
        self.max_parallel_tasks = max_parallel
        self.pool.setMaxThreadCount(max_parallel)

    def refresh_states(self) -> None:
        for task in self.database.get_tasks():
            if task.id is None:
                continue
            if task.id in self.running:
                self.states[task.id] = "running"
            elif task.id in self.paused:
                self.states[task.id] = "paused"
            elif not int(task.enabled):
                self.states[task.id] = "disabled"
            else:
                self.states.setdefault(task.id, "idle")

    def get_state(self, task: Task) -> str:
        if task.id is None:
            return "idle"
        if not int(task.enabled):
            return "disabled"
        return self.states.get(task.id, "idle")

    def create_task(self, task: Task) -> int:
        task_id = self.database.create_task(task)
        self.states[task_id] = "idle" if int(task.enabled) else "disabled"
        self.tasks_changed.emit()
        return task_id

    def update_task(self, task: Task) -> None:
        self.database.update_task(task)
        if task.id is not None:
            self.states[task.id] = "idle" if int(task.enabled) else "disabled"
        self.tasks_changed.emit()

    def delete_task(self, task_id: int) -> None:
        if task_id in self.running:
            self.log_message.emit("No se puede eliminar una tarea en ejecucion.")
            return
        self.database.delete_task(task_id)
        self.states.pop(task_id, None)
        self.retry_after.pop(task_id, None)
        retry_timer = self.retry_timers.pop(task_id, None)
        if retry_timer:
            retry_timer.stop()
            retry_timer.deleteLater()
        self.pending_change_runs.discard(task_id)
        self.paused.discard(task_id)
        self.tasks_changed.emit()

    def pause_task(self, task_id: int) -> None:
        self.paused.add(task_id)
        self._set_status(task_id, "paused", "Tarea pausada")

    def cancel_task(self, task_id: int) -> None:
        worker = self.workers.get(task_id)
        if not worker:
            self.log_message.emit("La tarea seleccionada no esta en ejecucion.")
            return
        worker.cancel()
        self._set_status(task_id, "running", "Cancelando ejecucion...")

    def resume_task(self, task_id: int) -> None:
        self.paused.discard(task_id)
        self.retry_after.pop(task_id, None)
        task = self.database.get_task(task_id)
        state = "idle" if task and int(task.enabled) else "disabled"
        self._set_status(task_id, state, "Tarea reanudada")

    def pause_all(self) -> None:
        for task in self.database.get_tasks():
            if task.id is not None:
                self.pause_task(task.id)

    def resume_all(self) -> None:
        for task in self.database.get_tasks():
            if task.id is not None:
                self.resume_task(task.id)

    def run_all_now(self) -> None:
        for task in self.database.get_tasks():
            if task.id is not None:
                self.run_task(task.id, automatic=False)

    def shutdown(self) -> None:
        self.queue.clear()
        self.pending_change_runs.clear()
        for timer in self.retry_timers.values():
            timer.stop()
            timer.deleteLater()
        self.retry_timers.clear()
        self.pool.clear()
        for worker in list(self.workers.values()):
            worker.cancel()
        self.pool.waitForDone(3000)

    def run_task(self, task_id: int, dry_run_override: bool = False, automatic: bool = False) -> bool:
        task = self.database.get_task(task_id)
        if task is None:
            return False
        if automatic and self.is_waiting_for_retry(task_id):
            return False
        if task_id in self.running:
            self.log_message.emit(f"{task.name}: ya esta en ejecucion.")
            return False
        if automatic and task_id in self.paused:
            return False
        if task_id in self.paused:
            self._set_status(task_id, "paused", "Tarea pausada")
            return False

        can_run, reason = can_run_task(task)
        if not can_run:
            state = "disabled" if reason == "Tarea desactivada" else "waiting_network"
            if state == "waiting_network" and automatic:
                self._schedule_retry(task_id)
            self._set_status(task_id, state, f"{task.name}: {reason}")
            return False
        self.retry_after.pop(task_id, None)
        if reason != "Lista para ejecutar":
            self.log_message.emit(f"{task.name}: {reason}")

        space_ok, space_message = has_enough_destination_space(task.destination_path)
        if not space_ok:
            self._set_status(task_id, "warning", f"{task.name}: {space_message}")
            return False

        if len(self.running) >= self.max_parallel_tasks:
            if (task_id, dry_run_override, automatic) not in self.queue:
                self.queue.append((task_id, dry_run_override, automatic))
            self._set_status(task_id, "scheduled", f"{task.name}: esperando hueco libre")
            return True

        self._start_worker(task, dry_run_override)
        return True

    def request_change_run(self, task_id: int) -> bool:
        if task_id in self.running:
            if task_id not in self.pending_change_runs:
                task = self.database.get_task(task_id)
                if task:
                    self.log_message.emit(
                        f"{task.name}: cambios detectados durante la copia; se ejecutara de nuevo al terminar."
                    )
            self.pending_change_runs.add(task_id)
            return True
        return self.run_task(task_id, automatic=True)

    def _start_worker(self, task: Task, dry_run_override: bool) -> None:
        assert task.id is not None
        self.running.add(task.id)
        self._set_status(task.id, "running", f"{task.name}: copia iniciada")
        worker = SyncWorker(task, dry_run_override)
        worker.signals.output.connect(lambda _task_id, line: self.log_message.emit(line))
        worker.signals.finished.connect(self._on_worker_finished)
        self.workers[task.id] = worker
        self.pool.start(worker)

    def is_waiting_for_retry(self, task_id: int) -> bool:
        retry_at = self.retry_after.get(task_id)
        return bool(retry_at and datetime.now() < retry_at)

    def _schedule_retry(self, task_id: int, seconds: int = 60) -> None:
        self.retry_after[task_id] = datetime.now() + timedelta(seconds=seconds)
        current_timer = self.retry_timers.pop(task_id, None)
        if current_timer:
            current_timer.stop()
            current_timer.deleteLater()

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(seconds * 1000)
        timer.timeout.connect(lambda task_id=task_id: self._retry_automatic_task(task_id))
        timer.start()
        self.retry_timers[task_id] = timer

    def _retry_automatic_task(self, task_id: int) -> None:
        timer = self.retry_timers.pop(task_id, None)
        if timer:
            timer.deleteLater()
        self.retry_after.pop(task_id, None)
        task = self.database.get_task(task_id)
        if task is None or task_id in self.paused or not int(task.enabled):
            return
        if task.mode in ("changes", "both"):
            self.request_change_run(task_id)
        else:
            self.run_task(task_id, automatic=True)

    def _on_worker_finished(self, result: SyncResult) -> None:
        self.running.discard(result.task_id)
        self.workers.pop(result.task_id, None)
        self.database.insert_run(result)
        self.database.update_task_after_run(result)
        message = result.error_message or "Ejecucion finalizada correctamente"
        self._set_status(result.task_id, result.status, message)
        self.run_finished.emit(result)
        self.tasks_changed.emit()
        if result.task_id in self.pending_change_runs:
            self.pending_change_runs.discard(result.task_id)
            self.request_change_run(result.task_id)
        self._drain_queue()

    def _drain_queue(self) -> None:
        while self.queue and len(self.running) < self.max_parallel_tasks:
            task_id, dry_run_override, automatic = self.queue.popleft()
            self.run_task(task_id, dry_run_override=dry_run_override, automatic=automatic)

    def _set_status(self, task_id: int, status: str, message: str) -> None:
        self.states[task_id] = status
        self.status_changed.emit(task_id, status, message)
        self.tasks_changed.emit()
