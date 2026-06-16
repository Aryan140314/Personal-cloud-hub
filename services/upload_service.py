from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from services.database_service import DatabaseService
from services.drive_service import DriveService, DriveUnavailableError
from services.file_classifier import categorize_file
from services.notification_service import NotificationService


@dataclass
class UploadResult:
    file_id: int | None
    filename: str
    status: str
    message: str


class UploadService:
    def __init__(
        self,
        db: DatabaseService,
        drive_service: DriveService,
        notification_service: NotificationService,
    ):
        self.db = db
        self.drive_service = drive_service
        self.notification_service = notification_service

    def upload_file(self, path: str | Path) -> UploadResult:
        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            return UploadResult(None, file_path.name, "failed", "File does not exist.")

        file_hash = self._sha256(file_path)
        duplicate = self.db.find_uploaded_duplicate(file_hash)
        category = categorize_file(file_path)
        stat = file_path.stat()

        if duplicate:
            file_id = self.db.add_file_record(
                filename=file_path.name,
                filepath=str(file_path),
                filesize=stat.st_size,
                filetype=file_path.suffix.lower().lstrip("."),
                category=category,
                file_hash=file_hash,
                status="duplicate",
                message=f"Duplicate of uploaded file #{duplicate['id']}.",
                google_drive_id=duplicate["google_drive_id"],
                google_drive_link=duplicate["google_drive_link"],
                upload_date=duplicate["upload_date"],
            )
            message = "Duplicate detected. Upload skipped."
            self.db.add_upload_log(file_path.name, "duplicate", message)
            return UploadResult(file_id, file_path.name, "duplicate", message)

        file_id = self.db.add_file_record(
            filename=file_path.name,
            filepath=str(file_path),
            filesize=stat.st_size,
            filetype=file_path.suffix.lower().lstrip("."),
            category=category,
            file_hash=file_hash,
            status="pending",
            message="Waiting for Google Drive upload.",
        )
        self._copy_to_local_backup(file_path, category)

        try:
            result = self.drive_service.upload_file(file_path, category)
        except DriveUnavailableError as exc:
            message = str(exc)
            self.db.update_file_status(file_id, status="pending_setup", message=message)
            self.db.add_upload_log(file_path.name, "pending_setup", message)
            return UploadResult(file_id, file_path.name, "pending_setup", message)
        except Exception as exc:
            message = f"Upload failed: {exc}"
            self.db.update_file_status(file_id, status="failed", message=message)
            self.db.add_upload_log(file_path.name, "failed", message)
            self.notification_service.notify("Upload Failed", f"{file_path.name}: {message}")
            return UploadResult(file_id, file_path.name, "failed", message)

        upload_date = datetime.now().isoformat(timespec="seconds")
        self.db.update_file_status(
            file_id,
            status="uploaded",
            message="Uploaded successfully.",
            google_drive_id=result.file_id,
            google_drive_link=result.link,
            upload_date=upload_date,
        )
        self.db.add_upload_log(file_path.name, "uploaded", "Uploaded successfully.")
        self.notification_service.notify("Upload Successful", file_path.name)
        return UploadResult(file_id, file_path.name, "uploaded", "Uploaded successfully.")

    def retry_pending(self) -> list[UploadResult]:
        rows = self.db.search_files("pending_setup", limit=500)
        results: list[UploadResult] = []
        for row in rows:
            if row["status"] == "pending_setup":
                results.append(self.upload_file(row["filepath"]))
        return results

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _copy_to_local_backup(self, file_path: Path, category: str) -> None:
        backup_root = self.db.get_setting("backup_folder", "")
        if not backup_root:
            return

        target_dir = Path(backup_root) / category
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_dir / file_path.name)
        except Exception as exc:
            self.db.add_upload_log(file_path.name, "backup_warning", f"Local backup copy failed: {exc}")
