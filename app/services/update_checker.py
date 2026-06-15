from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal, pyqtSlot

from app.config import APP_NAME, APP_VERSION, GITHUB_RELEASES_URL, GITHUB_REPOSITORY
from app.database import Database
from app.models import now_iso


CHECK_INTERVAL = timedelta(days=1)
GITHUB_LATEST_RELEASE_API = (
    f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
)


@dataclass(frozen=True, slots=True)
class UpdateResult:
    current_version: str
    latest_version: str
    release_url: str
    update_available: bool


class UpdateCheckSignals(QObject):
    finished = pyqtSignal(object, bool)
    failed = pyqtSignal(str, bool)


class UpdateCheckWorker(QRunnable):
    def __init__(self, manual: bool) -> None:
        super().__init__()
        self.manual = manual
        self.signals = UpdateCheckSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            result = fetch_latest_release()
        except (ValueError, HTTPError, URLError, OSError, TimeoutError) as exc:
            self.signals.failed.emit(str(exc), self.manual)
            return
        self.signals.finished.emit(result, self.manual)


class UpdateChecker(QObject):
    checked = pyqtSignal(object, bool)
    failed = pyqtSignal(str, bool)

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.pool = QThreadPool.globalInstance()
        self.worker: UpdateCheckWorker | None = None
        self.timer = QTimer(self)
        self.timer.setInterval(60 * 60 * 1000)
        self.timer.timeout.connect(self.check_automatic)

    def start(self) -> None:
        self.timer.start()
        QTimer.singleShot(1500, self.check_on_startup)

    def stop(self) -> None:
        self.timer.stop()

    def check_automatic(self) -> None:
        settings = self.database.get_settings()
        if settings.get("check_updates", "1") != "1":
            return
        if not _is_check_due(settings.get("last_update_check_at", "")):
            return
        self.check(manual=False)

    def check_on_startup(self) -> None:
        settings = self.database.get_settings()
        if settings.get("check_updates", "1") == "1":
            self.check(manual=False)

    def check_manual(self) -> None:
        self.check(manual=True)

    def check(self, manual: bool) -> None:
        if self.worker is not None:
            if manual:
                self.failed.emit("Ya hay una comprobacion de actualizaciones en curso.", True)
            return
        self.database.set_setting("last_update_check_at", now_iso())
        worker = UpdateCheckWorker(manual)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.failed.connect(self._on_failed)
        self.worker = worker
        self.pool.start(worker)

    def _on_finished(self, result: UpdateResult, manual: bool) -> None:
        self.worker = None
        self.checked.emit(result, manual)

    def _on_failed(self, message: str, manual: bool) -> None:
        self.worker = None
        self.failed.emit(message, manual)


def fetch_latest_release() -> UpdateResult:
    request = Request(
        GITHUB_LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{APP_NAME}/{APP_VERSION}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GitHub devolvio una respuesta no valida")
    latest_version = str(payload.get("tag_name") or "").strip()
    release_url = str(payload.get("html_url") or GITHUB_RELEASES_URL).strip()
    if not latest_version:
        raise ValueError("La ultima release de GitHub no tiene una version valida")
    return UpdateResult(
        current_version=APP_VERSION,
        latest_version=latest_version,
        release_url=release_url,
        update_available=is_newer_version(latest_version, APP_VERSION),
    )


def is_newer_version(candidate: str, current: str) -> bool:
    return _version_tuple(candidate) > _version_tuple(current)


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+)*", value)
    if not match:
        raise ValueError(f"Version no valida: {value}")
    parts = tuple(int(part) for part in match.group(0).split("."))
    return parts + (0,) * (4 - len(parts))


def _is_check_due(last_check: str) -> bool:
    if not last_check:
        return True
    try:
        checked_at = datetime.fromisoformat(last_check)
    except ValueError:
        return True
    return datetime.now() - checked_at >= CHECK_INTERVAL
