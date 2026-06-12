from __future__ import annotations

import json
from pathlib import Path

from app.database import Database
from app.models import TASK_MODES, Task, exclusions_to_json, now_iso
from app.validation import validate_task_data


EXPORT_VERSION = 1


def export_config(database: Database, path: str | Path) -> None:
    tasks = []
    for task in database.get_tasks():
        data = task.as_db_dict()
        data.pop("last_run_at", None)
        data.pop("last_success_at", None)
        data.pop("last_error", None)
        tasks.append(data)
    payload = {
        "version": EXPORT_VERSION,
        "settings": database.get_settings(),
        "tasks": tasks,
    }
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def import_config(database: Database, path: str | Path) -> int:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("version") != EXPORT_VERSION:
        raise ValueError("Version de configuracion no soportada")
    settings = payload.get("settings")
    if isinstance(settings, dict):
        database.set_settings({str(key): str(value) for key, value in settings.items()})

    existing_names = database.task_names()
    created = 0
    for item in payload.get("tasks", []):
        if not isinstance(item, dict):
            continue
        task = _task_from_import(item, existing_names)
        error = validate_task_data(task, require_existing_source=False)
        if error:
            raise ValueError(f"Tarea importada no valida ({task.name}): {error}")
        database.create_task(task)
        existing_names.add(task.name)
        created += 1
    return created


def _task_from_import(item: dict, existing_names: set[str]) -> Task:
    raw_name = str(item.get("name", "")).strip()
    name = _unique_name(raw_name, existing_names) if raw_name else ""
    source_path = str(item.get("source_path", "")).strip()
    destination_path = str(item.get("destination_path", "")).strip()
    server_ip = str(item.get("server_ip", "")).strip()
    mode = str(item.get("mode", "manual")).strip()
    if mode not in TASK_MODES:
        mode = "manual"
    interval = item.get("interval_minutes")
    try:
        interval = int(interval) if interval not in (None, "") else None
    except (TypeError, ValueError):
        interval = None
    exclude_patterns = item.get("exclude_patterns")
    if not isinstance(exclude_patterns, str):
        exclude_patterns = exclusions_to_json(exclude_patterns)
    created_at = now_iso()
    return Task(
        id=None,
        name=name,
        source_path=source_path,
        destination_path=destination_path,
        server_ip=server_ip,
        required_network=str(item.get("required_network") or "").strip() or None,
        mode=mode,
        interval_minutes=interval,
        watch_changes=_to_int_bool(item.get("watch_changes", 0)),
        enabled=_to_int_bool(item.get("enabled", 1)),
        mirror_delete=_to_int_bool(item.get("mirror_delete", 0)),
        dry_run=_to_int_bool(item.get("dry_run", 0)),
        exclude_patterns=exclude_patterns,
        created_at=created_at,
        updated_at=created_at,
    )


def _unique_name(name: str, existing_names: set[str]) -> str:
    if name not in existing_names:
        return name
    index = 2
    while f"{name} ({index})" in existing_names:
        index += 1
    return f"{name} ({index})"


def _to_int_bool(value) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return 1 if value else 0
    if isinstance(value, str):
        return 1 if value.strip().lower() in {"1", "true", "yes", "si", "on"} else 0
    return 0
