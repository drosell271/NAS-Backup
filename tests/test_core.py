from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import DEFAULT_SETTINGS
from app.database import Database
from app.models import Task
from app.services.autostart import build_autostart_command
from app.services.config_exporter import export_config, import_config
from app.services.network_checker import is_required_network_active
from app.services.update_checker import is_newer_version
from app.validation import validate_task_data


def make_task(**overrides) -> Task:
    values = {
        "id": None,
        "name": "Documentos",
        "source_path": r"C:\datos",
        "destination_path": r"\\nas\backups\documentos",
        "required_network": None,
        "mode": "manual",
        "interval_minutes": None,
        "watch_changes": 0,
        "enabled": 1,
        "mirror_delete": 0,
        "dry_run": 0,
        "exclude_patterns": "[]",
    }
    values.update(overrides)
    return Task(**values)


class ValidationTests(unittest.TestCase):
    def test_rejects_destination_inside_source(self) -> None:
        task = make_task(destination_path=r"C:\datos\backup")
        self.assertIsNotNone(validate_task_data(task, require_existing_source=False))

    def test_rejects_source_inside_destination(self) -> None:
        task = make_task(
            source_path=r"C:\datos\origen",
            destination_path=r"C:\datos",
        )
        self.assertIsNotNone(validate_task_data(task, require_existing_source=False))

    def test_rejects_drive_root_for_mirror(self) -> None:
        task = make_task(destination_path="C:\\", mirror_delete=1)
        self.assertIsNotNone(validate_task_data(task, require_existing_source=False))

    def test_rejects_normalized_root_for_mirror(self) -> None:
        task = make_task(destination_path=r"C:\temporal\..", mirror_delete=1)
        self.assertIsNotNone(validate_task_data(task, require_existing_source=False))

    def test_rejects_normalized_unc_share_root_for_mirror(self) -> None:
        task = make_task(destination_path=r"\\nas\backups\carpeta\..", mirror_delete=1)
        self.assertIsNotNone(validate_task_data(task, require_existing_source=False))

    def test_allows_separate_paths(self) -> None:
        task = make_task(source_path=r"C:\origen", destination_path=r"D:\destino")
        self.assertIsNone(validate_task_data(task, require_existing_source=False))


class ImportTests(unittest.TestCase):
    def test_export_uses_version_two_without_server_ip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "app.db")
            database.initialize()
            database.create_task(make_task())
            path = Path(directory) / "config.json"

            export_config(database, path)

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["version"], 2)
            self.assertNotIn("server_ip", payload["tasks"][0])

    def test_failed_import_leaves_no_partial_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "app.db")
            database.initialize()
            valid = {
                "name": "Valida",
                "source_path": r"C:\origen",
                "destination_path": r"D:\destino",
                "mode": "manual",
            }
            invalid = {**valid, "name": ""}
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "settings": {"max_parallel_tasks": "9"},
                        "tasks": [valid, invalid],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                import_config(database, path)

            self.assertEqual(database.get_tasks(), [])
            self.assertEqual(database.get_settings()["max_parallel_tasks"], "2")

    def test_import_rejects_root_mirror(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "app.db")
            database.initialize()
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "tasks": [
                            {
                                "name": "Peligrosa",
                                "source_path": r"C:\origen",
                                "destination_path": "C:\\",
                                "mode": "manual",
                                "mirror_delete": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                import_config(database, path)

            self.assertEqual(database.get_tasks(), [])


class MigrationTests(unittest.TestCase):
    def test_removes_legacy_server_ip_column(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.db"
            connection = sqlite3.connect(path)
            connection.executescript(
                """
                CREATE TABLE tasks (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  source_path TEXT NOT NULL,
                  destination_path TEXT NOT NULL,
                  server_ip TEXT NOT NULL,
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
                CREATE TABLE runs (
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
                CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT);
                PRAGMA user_version = 1;
                """
            )
            connection.execute(
                """
                INSERT INTO tasks (
                    name, source_path, destination_path, server_ip, mode,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("Antigua", r"C:\origen", r"D:\destino", "192.168.1.2", "manual", "x", "x"),
            )
            connection.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?)",
                ("default_debounce_seconds", "5"),
            )
            connection.commit()
            connection.close()

            database = Database(path)
            database.initialize()

            with database.connection() as migrated:
                columns = {
                    row["name"] for row in migrated.execute("PRAGMA table_info(tasks)").fetchall()
                }
            self.assertNotIn("server_ip", columns)
            self.assertEqual(database.get_tasks()[0].name, "Antigua")
            self.assertEqual(database.get_settings()["default_debounce_seconds"], "60")


class SettingsAndVersionTests(unittest.TestCase):
    def test_default_change_delay_is_sixty_seconds(self) -> None:
        self.assertEqual(DEFAULT_SETTINGS["default_debounce_seconds"], "60")

    def test_autostart_minimized_is_optional(self) -> None:
        main_path = Path(r"C:\NAS Backup\main.py")
        normal = build_autostart_command(main_path, minimized=False)
        minimized = build_autostart_command(main_path, minimized=True)
        self.assertNotIn("--minimized", normal)
        self.assertIn("--minimized", minimized)

    def test_version_comparison(self) -> None:
        self.assertTrue(is_newer_version("v1.1.0", "1.0.2"))
        self.assertFalse(is_newer_version("v1.0.2", "1.0.2"))
        self.assertFalse(is_newer_version("v1.0.1", "1.0.2"))


class NetworkTests(unittest.TestCase):
    @patch("app.services.network_checker.get_active_network_profiles")
    @patch("app.services.network_checker.get_current_wifi_ssid")
    def test_required_network_must_be_active(self, current_ssid, active_profiles) -> None:
        current_ssid.return_value = "Otra red"
        active_profiles.return_value = ["Ethernet"]
        self.assertFalse(is_required_network_active("Red guardada"))

    @patch("app.services.network_checker.get_active_network_profiles")
    @patch("app.services.network_checker.get_current_wifi_ssid")
    def test_accepts_current_wifi(self, current_ssid, active_profiles) -> None:
        current_ssid.return_value = "Oficina"
        active_profiles.return_value = []
        self.assertTrue(is_required_network_active("oficina"))


if __name__ == "__main__":
    unittest.main()
