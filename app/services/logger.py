from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from app.config import LOG_DIR, ensure_directories


def new_task_log_path(task_id: int, started_at: datetime | None = None) -> Path:
    ensure_directories()
    started_at = started_at or datetime.now()
    filename = f"task_{task_id}_{started_at.strftime('%Y%m%d_%H%M%S')}.log"
    return LOG_DIR / filename


def cleanup_old_logs(retention_days: int) -> None:
    if retention_days < 1:
        return
    ensure_directories()
    cutoff = datetime.now() - timedelta(days=retention_days)
    for path in LOG_DIR.glob("*.log"):
        try:
            modified = datetime.fromtimestamp(path.stat().st_mtime)
        except OSError:
            continue
        if modified < cutoff:
            try:
                path.unlink()
            except OSError:
                pass
