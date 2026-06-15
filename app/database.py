from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.config import DB_PATH, DEFAULT_SETTINGS, ensure_directories
from app.models import Task, now_iso


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        ensure_directories()
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  source_path TEXT NOT NULL,
                  destination_path TEXT NOT NULL,
                  required_network TEXT,
                  mode TEXT NOT NULL,
                  interval_minutes INTEGER,
                  watch_changes INTEGER NOT NULL DEFAULT 0,
                  enabled INTEGER NOT NULL DEFAULT 1,
                  mirror_delete INTEGER NOT NULL DEFAULT 0,
                  dry_run INTEGER NOT NULL DEFAULT 0,
                  exclude_patterns TEXT,
                  last_run_at TEXT,
                  last_success_at TEXT,
                  last_error TEXT,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS runs (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_id INTEGER NOT NULL,
                  started_at TEXT NOT NULL,
                  finished_at TEXT,
                  status TEXT NOT NULL,
                  bytes_copied INTEGER,
                  files_copied INTEGER,
                  robocopy_exit_code INTEGER,
                  log_path TEXT,
                  error_message TEXT,
                  FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS settings (
                  key TEXT PRIMARY KEY,
                  value TEXT
                );
                """
            )
            schema_version = conn.execute("PRAGMA user_version").fetchone()[0]
            if schema_version < 1:
                debounce = conn.execute(
                    "SELECT value FROM settings WHERE key = ?",
                    ("default_debounce_seconds",),
                ).fetchone()
                if debounce is not None and debounce["value"] == "45":
                    conn.execute(
                        "UPDATE settings SET value = ? WHERE key = ?",
                        ("5", "default_debounce_seconds"),
                    )
                conn.execute("PRAGMA user_version = 1")
                schema_version = 1
            if schema_version < 2:
                columns = {
                    row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
                }
                if "server_ip" in columns:
                    conn.execute("ALTER TABLE tasks DROP COLUMN server_ip")
                conn.execute("PRAGMA user_version = 2")
                schema_version = 2
            if schema_version < 3:
                debounce = conn.execute(
                    "SELECT value FROM settings WHERE key = ?",
                    ("default_debounce_seconds",),
                ).fetchone()
                if debounce is not None and debounce["value"] == "5":
                    conn.execute(
                        "UPDATE settings SET value = ? WHERE key = ?",
                        ("60", "default_debounce_seconds"),
                    )
                conn.execute("PRAGMA user_version = 3")
            for key, value in DEFAULT_SETTINGS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO settings(key, value) VALUES(?, ?)",
                    (key, value),
                )

    def get_tasks(self) -> list[Task]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY name COLLATE NOCASE").fetchall()
        return [Task.from_row(row) for row in rows]

    def get_task(self, task_id: int) -> Task | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return Task.from_row(row) if row else None

    def create_task(self, task: Task) -> int:
        with self.connection() as conn:
            return self._insert_task(conn, task)

    def _insert_task(self, conn: sqlite3.Connection, task: Task) -> int:
        values = task.as_db_dict()
        created_at = now_iso()
        cursor = conn.execute(
            """
            INSERT INTO tasks (
                name, source_path, destination_path, required_network,
                mode, interval_minutes, watch_changes, enabled, mirror_delete,
                dry_run, exclude_patterns, last_run_at, last_success_at, last_error,
                created_at, updated_at
            ) VALUES (
                :name, :source_path, :destination_path, :required_network,
                :mode, :interval_minutes, :watch_changes, :enabled, :mirror_delete,
                :dry_run, :exclude_patterns, :last_run_at, :last_success_at, :last_error,
                :created_at, :updated_at
            )
            """,
            values | {"created_at": created_at, "updated_at": created_at},
        )
        return int(cursor.lastrowid)

    def update_task(self, task: Task) -> None:
        if task.id is None:
            raise ValueError("Cannot update a task without id")
        values = task.as_db_dict() | {"id": task.id, "updated_at": now_iso()}
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET name = :name,
                    source_path = :source_path,
                    destination_path = :destination_path,
                    required_network = :required_network,
                    mode = :mode,
                    interval_minutes = :interval_minutes,
                    watch_changes = :watch_changes,
                    enabled = :enabled,
                    mirror_delete = :mirror_delete,
                    dry_run = :dry_run,
                    exclude_patterns = :exclude_patterns,
                    last_run_at = :last_run_at,
                    last_success_at = :last_success_at,
                    last_error = :last_error,
                    updated_at = :updated_at
                WHERE id = :id
                """,
                values,
            )

    def delete_task(self, task_id: int) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def insert_run(self, result: Any) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    task_id, started_at, finished_at, status, bytes_copied,
                    files_copied, robocopy_exit_code, log_path, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.task_id,
                    result.started_at,
                    result.finished_at,
                    result.status,
                    result.bytes_copied,
                    result.files_copied,
                    result.robocopy_exit_code,
                    result.log_path,
                    result.error_message,
                ),
            )

    def update_task_after_run(self, result: Any) -> None:
        last_success_at = result.finished_at if result.status == "success" else None
        with self.connection() as conn:
            if last_success_at:
                conn.execute(
                    """
                    UPDATE tasks
                    SET last_run_at = ?, last_success_at = ?, last_error = NULL, updated_at = ?
                    WHERE id = ?
                    """,
                    (result.finished_at, last_success_at, now_iso(), result.task_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE tasks
                    SET last_run_at = ?, last_error = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (result.finished_at, result.error_message, now_iso(), result.task_id),
                )

    def get_recent_runs(self, limit: int = 100, task_id: int | None = None) -> list[sqlite3.Row]:
        sql = """
            SELECT runs.*, tasks.name AS task_name
            FROM runs
            JOIN tasks ON tasks.id = runs.task_id
        """
        params: tuple[Any, ...] = ()
        if task_id is not None:
            sql += " WHERE task_id = ?"
            params = (task_id,)
        sql += " ORDER BY started_at DESC LIMIT ?"
        params += (limit,)
        with self.connection() as conn:
            return conn.execute(sql, params).fetchall()

    def get_settings(self) -> dict[str, str]:
        with self.connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
        settings = dict(DEFAULT_SETTINGS)
        settings.update({row["key"]: row["value"] for row in rows})
        return settings

    def set_setting(self, key: str, value: str) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO settings(key, value)
                VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def set_settings(self, values: dict[str, str]) -> None:
        with self.connection() as conn:
            for key, value in values.items():
                conn.execute(
                    """
                    INSERT INTO settings(key, value)
                    VALUES(?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )

    def import_configuration(self, settings: dict[str, str], tasks: list[Task]) -> None:
        with self.connection() as conn:
            for key, value in settings.items():
                conn.execute(
                    """
                    INSERT INTO settings(key, value)
                    VALUES(?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )
            for task in tasks:
                self._insert_task(conn, task)

    def task_names(self) -> set[str]:
        with self.connection() as conn:
            rows = conn.execute("SELECT name FROM tasks").fetchall()
        return {row["name"] for row in rows}
