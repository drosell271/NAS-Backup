from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "NAS Backup"
RUN_REGISTRY_NAME = "NASBackupApp"


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = base_dir()


def runtime_dir() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return BASE_DIR


def data_dir() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / APP_NAME
        return Path.home() / f".{RUN_REGISTRY_NAME}"
    return BASE_DIR / "data"


RUNTIME_DIR = runtime_dir()
DATA_DIR = data_dir()
LOG_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "app.db"
UI_DIR = RUNTIME_DIR / "app" / "ui"
ASSETS_DIR = RUNTIME_DIR / "app" / "assets"


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return str(BASE_DIR / relative_path)


def asset_path(filename: str) -> Path | None:
    candidates = [
        ASSETS_DIR / filename,
        BASE_DIR / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


DEFAULT_SETTINGS = {
    "start_with_windows": "0",
    "start_minimized": "0",
    "max_parallel_tasks": "2",
    "notify_on_success": "1",
    "notify_on_error": "1",
    "default_debounce_seconds": "5",
    "log_retention_days": "30",
}


DEFAULT_EXCLUSIONS = [
    "*.tmp",
    "*.bak",
    "~$*",
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
]
