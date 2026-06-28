from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

log = logging.getLogger(__name__)


DEFAULT_SETTINGS = {
    "watch_folders": [],
    "theme": "dark",
    "notifications": True,
    "auto_start_monitor": False,
    "google_drive_root": "Personal Cloud Hub",
    "backup_folder": "",
    "duplicate_policy": "skip",
}


class DatabaseService:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @contextmanager
    def connect(self):
        """Thread-safe database connection context manager."""
        if not self._lock.acquire(timeout=30):
            raise RuntimeError("Database lock timeout — another operation may be stuck.")
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
            self._lock.release()

    def initialize(self) -> None:
        log.info("Initializing database at %s", self.db_path)
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    filesize INTEGER NOT NULL DEFAULT 0,
                    filetype TEXT,
                    category TEXT,
                    file_hash TEXT,
                    upload_date TEXT,
                    google_drive_id TEXT,
                    google_drive_link TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS upload_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    upload_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename);
                CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash);
                CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
                CREATE INDEX IF NOT EXISTS idx_files_upload_date ON files(upload_date);
                """
            )

        for key, value in DEFAULT_SETTINGS.items():
            if self.get_setting(key) is None:
                self.set_setting(key, value)

    def add_file_record(
        self,
        *,
        filename: str,
        filepath: str,
        filesize: int,
        filetype: str,
        category: str,
        file_hash: str,
        status: str,
        message: str = "",
        google_drive_id: str | None = None,
        google_drive_link: str | None = None,
        upload_date: str | None = None,
    ) -> int:
        log.debug("Adding file record: %s [%s]", filename, status)
        now = datetime.now().isoformat(timespec="seconds")
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO files (
                    filename, filepath, filesize, filetype, category, file_hash,
                    upload_date, google_drive_id, google_drive_link, status,
                    message, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    filepath,
                    filesize,
                    filetype,
                    category,
                    file_hash,
                    upload_date,
                    google_drive_id,
                    google_drive_link,
                    status,
                    message,
                    now,
                    now,
                ),
            )
            return int(cursor.lastrowid)

    def update_file_status(
        self,
        file_id: int,
        *,
        status: str,
        message: str = "",
        google_drive_id: str | None = None,
        google_drive_link: str | None = None,
        upload_date: str | None = None,
    ) -> None:
        log.debug("Updating file %d status to %s", file_id, status)
        now = datetime.now().isoformat(timespec="seconds")
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE files
                SET status = ?,
                    message = ?,
                    google_drive_id = COALESCE(?, google_drive_id),
                    google_drive_link = COALESCE(?, google_drive_link),
                    upload_date = COALESCE(?, upload_date),
                    updated_at = ?
                WHERE id = ?
                """,
                (status, message, google_drive_id, google_drive_link, upload_date, now, file_id),
            )

    def find_uploaded_duplicate(self, file_hash: str) -> sqlite3.Row | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM files
                WHERE file_hash = ?
                  AND status = 'uploaded'
                ORDER BY id DESC
                LIMIT 1
                """,
                (file_hash,),
            ).fetchone()
            return row

    def add_upload_log(self, filename: str, status: str, message: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO upload_logs (filename, upload_time, status, message)
                VALUES (?, ?, ?, ?)
                """,
                (filename, datetime.now().isoformat(timespec="seconds"), status, message),
            )

    def search_files(self, query: str, limit: int = 200) -> list[sqlite3.Row]:
        needle = f"%{query.strip()}%"
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM files
                WHERE filename LIKE ?
                   OR filepath LIKE ?
                   OR category LIKE ?
                   OR filetype LIKE ?
                   OR status LIKE ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (needle, needle, needle, needle, needle, limit),
            ).fetchall()
            return list(rows)

    def get_recent_files(self, limit: int = 12) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT *
                    FROM files
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            )

    def get_recent_logs(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT *
                    FROM upload_logs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            )

    def get_dashboard_stats(self) -> dict[str, Any]:
        today = datetime.now().date().isoformat()
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            uploaded = conn.execute("SELECT COUNT(*) FROM files WHERE status = 'uploaded'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM files WHERE status = 'failed'").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM files WHERE status IN ('pending', 'pending_setup')").fetchone()[0]
            uploads_today = conn.execute(
                "SELECT COUNT(*) FROM files WHERE status = 'uploaded' AND substr(upload_date, 1, 10) = ?",
                (today,),
            ).fetchone()[0]
            storage_used = conn.execute(
                "SELECT COALESCE(SUM(filesize), 0) FROM files WHERE status = 'uploaded'"
            ).fetchone()[0]
            return {
                "total_files": total,
                "uploaded_files": uploaded,
                "failed_uploads": failed,
                "pending_uploads": pending,
                "uploads_today": uploads_today,
                "storage_used": storage_used,
            }

    def uploads_per_day(self, limit: int = 7) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT substr(upload_date, 1, 10) AS day, COUNT(*) AS total
                    FROM files
                    WHERE status = 'uploaded' AND upload_date IS NOT NULL
                    GROUP BY day
                    ORDER BY day DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            )

    def file_type_counts(self, limit: int = 8) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT COALESCE(NULLIF(filetype, ''), 'unknown') AS filetype,
                           COUNT(*) AS total
                    FROM files
                    GROUP BY filetype
                    ORDER BY total DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            )

    def get_setting(self, key: str, default: Any = None) -> Any:
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            if not row:
                return default
            try:
                return json.loads(row["value"])
            except json.JSONDecodeError:
                return row["value"]

    def set_setting(self, key: str, value: Any) -> None:
        serialized = json.dumps(value)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, serialized),
            )

    def replace_watch_folders(self, folders: Iterable[str]) -> None:
        clean = []
        for folder in folders:
            value = str(folder).strip()
            if value and value not in clean:
                clean.append(value)
        self.set_setting("watch_folders", clean)

    def get_files_by_status(self, status: str, limit: int = 500) -> list[sqlite3.Row]:
        """Return file records matching an exact status value."""
        with self.connect() as conn:
            return list(
                conn.execute(
                    "SELECT * FROM files WHERE status = ? ORDER BY id LIMIT ?",
                    (status, limit),
                ).fetchall()
            )

    def delete_file_record(self, file_id: int) -> None:
        """Remove a file record from the database."""
        log.info("Deleting file record %d", file_id)
        with self.connect() as conn:
            conn.execute("DELETE FROM files WHERE id = ?", (file_id,))

    def get_all_files_for_export(self) -> list[sqlite3.Row]:
        """Return all file records for CSV export."""
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT id, filename, filepath, filesize, filetype, category,
                           file_hash, upload_date, google_drive_id,
                           google_drive_link, status, message, created_at, updated_at
                    FROM files
                    ORDER BY id
                    """
                ).fetchall()
            )
