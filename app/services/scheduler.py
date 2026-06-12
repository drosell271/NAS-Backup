from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from app.database import Database
from app.models import parse_exclusions
from app.services.sync_worker import should_ignore_path


class IntervalScheduler(QObject):
    def __init__(self, database: Database, task_manager, interval_ms: int = 30_000) -> None:
        super().__init__()
        self.database = database
        self.task_manager = task_manager
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.check_due_tasks)

    def start(self) -> None:
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def check_due_tasks(self) -> None:
        now = datetime.now()
        for task in self.database.get_tasks():
            if task.id is None or not int(task.enabled):
                continue
            if task.mode not in ("interval", "both"):
                continue
            if not task.interval_minutes or task.interval_minutes < 1:
                continue
            if task.id in self.task_manager.paused:
                continue
            due = task.last_run_at is None
            if task.last_run_at:
                try:
                    last_run = datetime.fromisoformat(task.last_run_at)
                except ValueError:
                    due = True
                else:
                    due = now - last_run >= timedelta(minutes=task.interval_minutes)
            if due:
                self.task_manager.run_task(task.id, automatic=True)


class _WatchdogHandler:
    def __init__(self, callback, ignored_patterns: list[str]) -> None:
        from watchdog.events import FileSystemEventHandler

        class Handler(FileSystemEventHandler):
            def on_created(self, event):
                self._handle(event)

            def on_modified(self, event):
                self._handle(event)

            def on_deleted(self, event):
                self._handle(event)

            def on_moved(self, event):
                self._handle(event)

            def _handle(self, event):
                paths = [event.src_path]
                if hasattr(event, "dest_path"):
                    paths.append(event.dest_path)
                if any(should_ignore_path(path, ignored_patterns) for path in paths):
                    return
                callback()

        self.handler = Handler()


class ChangeWatcher(QObject):
    changed = pyqtSignal(int)

    def __init__(self, database: Database, task_manager) -> None:
        super().__init__()
        self.database = database
        self.task_manager = task_manager
        self.observers: dict[int, object] = {}
        self.debounce_timers: dict[int, QTimer] = {}
        self.changed.connect(self._on_changed)

    def restart(self) -> None:
        self.stop()
        settings = self.database.get_settings()
        try:
            debounce_seconds = max(1, int(settings.get("default_debounce_seconds", "5")))
        except ValueError:
            debounce_seconds = 5

        try:
            from watchdog.observers import Observer
        except ImportError:
            self.task_manager.log_message.emit("watchdog no esta instalado; deteccion de cambios desactivada.")
            return

        for task in self.database.get_tasks():
            if task.id is None or not int(task.enabled):
                continue
            if task.mode not in ("changes", "both") or not int(task.watch_changes):
                continue
            source = Path(task.source_path)
            if not source.exists():
                continue
            handler = _WatchdogHandler(
                lambda task_id=task.id: self.changed.emit(task_id),
                parse_exclusions(task.exclude_patterns),
            ).handler
            observer = Observer()
            observer.schedule(handler, str(source), recursive=True)
            observer.daemon = True
            observer.start()
            self.observers[task.id] = observer
            self.task_manager.log_message.emit(
                f"{task.name}: deteccion de cambios activa ({debounce_seconds} s)."
            )

            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(debounce_seconds * 1000)
            timer.timeout.connect(
                lambda task_id=task.id: self.task_manager.request_change_run(task_id)
            )
            self.debounce_timers[task.id] = timer

    def stop(self) -> None:
        observers = list(self.observers.values())
        for observer in observers:
            observer.stop()
        deadline = time.monotonic() + 3.0
        for observer in observers:
            remaining = max(0.0, deadline - time.monotonic())
            if remaining <= 0:
                break
            observer.join(timeout=remaining)
        self.observers.clear()
        for timer in self.debounce_timers.values():
            timer.stop()
            timer.deleteLater()
        self.debounce_timers.clear()

    def _on_changed(self, task_id: int) -> None:
        timer = self.debounce_timers.get(task_id)
        if timer:
            timer.start()
