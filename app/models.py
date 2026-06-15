from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import DEFAULT_EXCLUSIONS


TASK_STATUSES = {
    "disabled",
    "idle",
    "waiting_network",
    "scheduled",
    "running",
    "success",
    "warning",
    "error",
    "paused",
}

TASK_MODES = ("manual", "interval", "changes", "both")


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def parse_exclusions(value: str | None) -> list[str]:
    if not value:
        return list(DEFAULT_EXCLUSIONS)
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return list(DEFAULT_EXCLUSIONS)
    if not isinstance(data, list):
        return list(DEFAULT_EXCLUSIONS)
    return [str(item).strip() for item in data if str(item).strip()]


def exclusions_to_json(patterns: list[str] | str | None) -> str:
    if patterns is None:
        return json.dumps(DEFAULT_EXCLUSIONS, ensure_ascii=False)
    if isinstance(patterns, str):
        patterns = [line.strip() for line in patterns.splitlines() if line.strip()]
    return json.dumps(patterns, ensure_ascii=False)


@dataclass(slots=True)
class Task:
    id: int | None
    name: str
    source_path: str
    destination_path: str
    required_network: str | None
    mode: str
    interval_minutes: int | None
    watch_changes: int
    enabled: int
    mirror_delete: int
    dry_run: int
    exclude_patterns: str | None
    last_run_at: str | None = None
    last_success_at: str | None = None
    last_error: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_row(cls, row: Any) -> "Task":
        return cls(
            id=row["id"],
            name=row["name"],
            source_path=row["source_path"],
            destination_path=row["destination_path"],
            required_network=row["required_network"],
            mode=row["mode"],
            interval_minutes=row["interval_minutes"],
            watch_changes=row["watch_changes"],
            enabled=row["enabled"],
            mirror_delete=row["mirror_delete"],
            dry_run=row["dry_run"],
            exclude_patterns=row["exclude_patterns"],
            last_run_at=row["last_run_at"],
            last_success_at=row["last_success_at"],
            last_error=row["last_error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def exclusions(self) -> list[str]:
        return parse_exclusions(self.exclude_patterns)

    def as_db_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "required_network": self.required_network or None,
            "mode": self.mode,
            "interval_minutes": self.interval_minutes,
            "watch_changes": int(self.watch_changes),
            "enabled": int(self.enabled),
            "mirror_delete": int(self.mirror_delete),
            "dry_run": int(self.dry_run),
            "exclude_patterns": self.exclude_patterns,
            "last_run_at": self.last_run_at,
            "last_success_at": self.last_success_at,
            "last_error": self.last_error,
        }


@dataclass(slots=True)
class SyncResult:
    task_id: int
    started_at: str
    finished_at: str
    status: str
    robocopy_exit_code: int | None
    log_path: str
    error_message: str | None
    dry_run: bool
    files_copied: int | None = None
    bytes_copied: int | None = None
