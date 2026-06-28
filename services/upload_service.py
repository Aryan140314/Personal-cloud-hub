from __future__ import annotations

import hashlib
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from services.database_service import DatabaseService
from services.drive_service import DriveService, DriveUnavailableError
from services.file_classifier import categorize_file
from services.notification_service import NotificationService

log = logging.getLogger(__name__)


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
            log.warning("Upload skipped – file does not exist: %s", file_path)
            return UploadResult(None, file_path.name, "failed", "File does not exist.")

        file_hash = self._sha256(file_path)
        duplicate = self.db.find_uploaded_duplicate(file_hash)
        category = categorize_file(file_path)
        stat = file_path.stat()

        if duplicate:
            policy = self.db.get_setting("duplicate_policy", "skip")
            return self._handle_duplicate(file_path, stat, file_hash, category, duplicate, policy)

        return self._do_upload(file_path, stat, file_hash, category)

    # ── Duplicate handling ────────────────────────────────────────────

    def _handle_duplicate(self, file_path, stat, file_hash, category, duplicate, policy):
        """Handle a duplicate file according to the configured policy."""
        if policy == "rename":
            # Upload with a timestamped filename.
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            renamed = file_path.parent / f"{file_path.stem}_{stamp}{file_path.suffix}"
            shutil.copy2(file_path, renamed)
            log.info("Duplicate policy=rename: uploading as %s", renamed.name)
            result = self._do_upload(renamed, renamed.stat(), file_hash, category)
            try:
                renamed.unlink()
            except OSError:
                pass
            return result

        if policy == "overwrite":
            # Delete the old Drive file and upload fresh.
            old_drive_id = duplicate["google_drive_id"]
            if old_drive_id:
                try:
                    self.drive_service.delete_file(old_drive_id)
                    log.info("Duplicate policy=overwrite: removed old Drive file %s", old_drive_id)
                except Exception as exc:
                    log.warning("Could not delete old Drive file %s: %s", old_drive_id, exc)
            return self._do_upload(file_path, stat, file_hash, category)

        # Default: skip
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
        log.info("Duplicate skipped: %s (hash matches #%d)", file_path.name, duplicate["id"])
        return UploadResult(file_id, file_path.name, "duplicate", message)

    # ── Core upload logic ─────────────────────────────────────────────

    def _do_upload(self, file_path: Path, stat, file_hash: str, category: str) -> UploadResult:
        """Create a pending record, copy to local backup, and upload to Drive."""
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
            log.warning("Drive unavailable for %s: %s", file_path.name, message)
            return UploadResult(file_id, file_path.name, "pending_setup", message)
        except Exception as exc:
            message = f"Upload failed: {exc}"
            self.db.update_file_status(file_id, status="failed", message=message)
            self.db.add_upload_log(file_path.name, "failed", message)
            self.notification_service.notify("Upload Failed", f"{file_path.name}: {message}")
            log.error("Upload failed for %s: %s", file_path.name, exc)
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
        log.info("Uploaded: %s → Drive ID %s", file_path.name, result.file_id)
        return UploadResult(file_id, file_path.name, "uploaded", "Uploaded successfully.")

    # ── Retry pending uploads ─────────────────────────────────────────

    def retry_pending(self) -> list[UploadResult]:
        """Retry all files that have ``pending_setup`` status.

        Uses an exact-status query rather than a LIKE search, and updates the
        existing database record instead of creating a new one.
        """
        rows = self.db.get_files_by_status("pending_setup", limit=500)
        results: list[UploadResult] = []
        for row in rows:
            file_path = Path(row["filepath"])
            if not file_path.exists() or not file_path.is_file():
                self.db.update_file_status(
                    row["id"], status="failed", message="File no longer exists."
                )
                results.append(
                    UploadResult(row["id"], row["filename"], "failed", "File no longer exists.")
                )
                continue

            # Attempt the Drive upload for the existing record.
            try:
                drive_result = self.drive_service.upload_file(file_path, row["category"])
            except DriveUnavailableError as exc:
                results.append(
                    UploadResult(row["id"], row["filename"], "pending_setup", str(exc))
                )
                continue
            except Exception as exc:
                message = f"Retry failed: {exc}"
                self.db.update_file_status(row["id"], status="failed", message=message)
                self.db.add_upload_log(row["filename"], "failed", message)
                results.append(UploadResult(row["id"], row["filename"], "failed", message))
                log.error("Retry failed for %s: %s", row["filename"], exc)
                continue

            upload_date = datetime.now().isoformat(timespec="seconds")
            self.db.update_file_status(
                row["id"],
                status="uploaded",
                message="Uploaded successfully (retried).",
                google_drive_id=drive_result.file_id,
                google_drive_link=drive_result.link,
                upload_date=upload_date,
            )
            self.db.add_upload_log(row["filename"], "uploaded", "Uploaded successfully (retried).")
            self.notification_service.notify("Upload Successful", row["filename"])
            log.info("Retry succeeded: %s", row["filename"])
            results.append(
                UploadResult(row["id"], row["filename"], "uploaded", "Uploaded successfully (retried).")
            )
        return results

    # ── Delete from cloud ─────────────────────────────────────────────

    def delete_from_drive(self, file_id: int) -> UploadResult:
        """Move a file to Google Drive trash and update the database record."""
        rows = self.db.get_files_by_status("uploaded")
        target = None
        for row in rows:
            if row["id"] == file_id:
                target = row
                break

        if target is None:
            return UploadResult(file_id, "", "failed", "File record not found or not uploaded.")

        drive_id = target["google_drive_id"]
        if not drive_id:
            return UploadResult(file_id, target["filename"], "failed", "No Google Drive ID stored.")

        try:
            self.drive_service.delete_file(drive_id)
        except Exception as exc:
            message = f"Drive delete failed: {exc}"
            log.error(message)
            return UploadResult(file_id, target["filename"], "failed", message)

        self.db.update_file_status(
            file_id,
            status="deleted",
            message="Moved to Google Drive trash.",
            google_drive_id=None,
            google_drive_link=None,
        )
        self.db.add_upload_log(target["filename"], "deleted", "Moved to Google Drive trash.")
        log.info("Deleted from Drive: %s (record %d)", target["filename"], file_id)
        return UploadResult(file_id, target["filename"], "deleted", "Moved to Google Drive trash.")

    # ── Utilities ─────────────────────────────────────────────────────

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
            log.debug("Local backup created: %s", target_dir / file_path.name)
        except Exception as exc:
            self.db.add_upload_log(file_path.name, "backup_warning", f"Local backup copy failed: {exc}")
            log.warning("Local backup failed for %s: %s", file_path.name, exc)
