from __future__ import annotations

import logging

from services.database_service import DatabaseService

log = logging.getLogger(__name__)


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
        except Exception as exc:
            # Notifications should never break the upload pipeline.
            log.debug("Desktop notification failed: %s", exc)
            return
