from __future__ import annotations

from services.database_service import DatabaseService


class NotificationService:
    def __init__(self, db: DatabaseService):
        self.db = db

    def notify(self, title: str, message: str) -> None:
        if not self.db.get_setting("notifications", True):
            return

        try:
            from plyer import notification

            notification.notify(
                title=title,
                message=message,
                app_name="Personal Cloud Hub",
                timeout=5,
            )
        except Exception:
            # Notifications should never break the upload pipeline.
            return
