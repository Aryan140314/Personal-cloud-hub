from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from services.database_service import DatabaseService
from services.drive_service import DriveService
from services.logging_config import setup_logging
from services.notification_service import NotificationService
from services.upload_service import UploadService
from ui.dashboard import MainWindow

log = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent


def ensure_project_dirs() -> None:
    for relative in (
        "config",
        "database",
        "services",
        "ui",
        "assets/icons",
        "assets/images",
        "logs",
    ):
        (BASE_DIR / relative).mkdir(parents=True, exist_ok=True)


def main() -> int:
    ensure_project_dirs()
    setup_logging(BASE_DIR / "logs")
    log.info("Starting Personal Cloud Hub")

    db = DatabaseService(BASE_DIR / "database" / "files.db")
    db.initialize()

    notification_service = NotificationService(db)
    drive_service = DriveService(
        config_dir=BASE_DIR / "config",
        db=db,
        root_folder_name=db.get_setting("google_drive_root", "Personal Cloud Hub"),
    )
    upload_service = UploadService(
        db=db,
        drive_service=drive_service,
        notification_service=notification_service,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Personal Cloud Hub")
    app.setOrganizationName("Personal Cloud Hub")

    window = MainWindow(db=db, drive_service=drive_service, upload_service=upload_service)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
