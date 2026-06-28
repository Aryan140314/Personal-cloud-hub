from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

from services.database_service import DatabaseService


@dataclass
class DriveUploadResult:
    file_id: str
    link: str


class DriveUnavailableError(RuntimeError):
    pass


class DriveService:
    def __init__(self, config_dir: Path, db: DatabaseService, root_folder_name: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.db = db
        self.root_folder_name = root_folder_name
        self.credentials_path = self.config_dir / "credentials.json"
        self.token_path = self.config_dir / "token.json"
        self.settings_path = self.config_dir / "pydrive_settings.yaml"
        self._drive = None
        self._root_folder_id: str | None = None
        self._folder_cache: dict[str, str] = {}

    def has_credentials(self) -> bool:
        return self.credentials_path.exists()

    def status_text(self) -> str:
        if not self.has_credentials():
            return "Google Drive setup required"
        if self._drive is None:
            return "Google Drive ready to connect"
        return "Google Drive connected"

    def destination_text(self) -> str:
        return f"My Drive / {self.root_folder_name} / <Category>"

    def set_root_folder_name(self, root_folder_name: str) -> None:
        clean_name = root_folder_name.strip() or "Personal Cloud Hub"
        if clean_name == self.root_folder_name:
            return
        self.root_folder_name = clean_name
        self._root_folder_id = None
        self._folder_cache.clear()

    def _write_pydrive_settings(self) -> None:
        credentials = self.credentials_path.as_posix().replace("'", "''")
        token = self.token_path.as_posix().replace("'", "''")
        content = f"""client_config_backend: file
client_config_file: '{credentials}'
save_credentials: true
save_credentials_backend: file
save_credentials_file: '{token}'
get_refresh_token: true
oauth_scope:
  - https://www.googleapis.com/auth/drive.file
"""
        self.settings_path.write_text(content, encoding="utf-8")

    def connect(self):
        if self._drive is not None:
            return self._drive

        if not self.has_credentials():
            raise DriveUnavailableError(
                "Missing config/credentials.json. Create a desktop OAuth client in Google Cloud first."
            )

        try:
            from pydrive2.auth import GoogleAuth
            from pydrive2.drive import GoogleDrive
        except ImportError as exc:
            raise DriveUnavailableError("PyDrive2 is not installed. Run pip install -r requirements.txt.") from exc

        self._write_pydrive_settings()
        gauth = GoogleAuth(settings_file=str(self.settings_path))

        if self.token_path.exists():
            gauth.LoadCredentialsFile(str(self.token_path))

        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()

        gauth.SaveCredentialsFile(str(self.token_path))
        self._drive = GoogleDrive(gauth)
        log.info("Connected to Google Drive successfully.")
        return self._drive

    def upload_file(self, file_path: Path, category: str) -> DriveUploadResult:
        drive = self.connect()
        root_id = self._ensure_root_folder(drive)
        folder_id = self._ensure_category_folder(drive, category, root_id)

        metadata: dict[str, Any] = {
            "title": file_path.name,
            "parents": [{"id": folder_id}],
        }
        drive_file = drive.CreateFile(metadata)
        drive_file.SetContentFile(str(file_path))
        drive_file.Upload()

        return DriveUploadResult(
            file_id=drive_file.get("id", ""),
            link=drive_file.get("alternateLink", ""),
        )

    def delete_file(self, drive_file_id: str) -> None:
        """Delete a file from Google Drive by its Drive file ID."""
        drive = self.connect()
        drive_file = drive.CreateFile({"id": drive_file_id})
        drive_file.Trash()  # Move to trash rather than permanent delete for safety.
        log.info("Trashed Google Drive file %s", drive_file_id)

    def _ensure_root_folder(self, drive) -> str:
        if self._root_folder_id:
            return self._root_folder_id
        self._root_folder_id = self._find_or_create_folder(drive, self.root_folder_name)
        return self._root_folder_id

    def _ensure_category_folder(self, drive, category: str, parent_id: str) -> str:
        cache_key = f"{parent_id}:{category}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]
        folder_id = self._find_or_create_folder(drive, category, parent_id=parent_id)
        self._folder_cache[cache_key] = folder_id
        return folder_id

    def _find_or_create_folder(self, drive, name: str, parent_id: str | None = None) -> str:
        escaped_name = name.replace("'", "\\'")
        query = (
            "mimeType = 'application/vnd.google-apps.folder' "
            "and trashed = false "
            f"and title = '{escaped_name}'"
        )
        if parent_id:
            query += f" and '{parent_id}' in parents"

        folders = drive.ListFile({"q": query, "maxResults": 1}).GetList()
        if folders:
            return folders[0]["id"]

        metadata: dict[str, Any] = {
            "title": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [{"id": parent_id}]

        folder = drive.CreateFile(metadata)
        folder.Upload()
        return folder["id"]
