from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable

from services.upload_service import UploadResult, UploadService

log = logging.getLogger(__name__)

_SEEN_EXPIRY_SECONDS = 30


class MonitorService:
    def __init__(
        self,
        upload_service: UploadService,
        result_callback: Callable[[UploadResult], None] | None = None,
    ):
        self.upload_service = upload_service
        self.result_callback = result_callback
        self._observer = None
        self._running = False
        self._seen_recently: dict[str, float] = {}

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, folders: list[str]) -> None:
        if self._running:
            return

        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError as exc:
            raise RuntimeError("watchdog is not installed. Run pip install -r requirements.txt.") from exc

        service = self

        class Handler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    service._schedule_upload(Path(event.src_path))

            def on_moved(self, event):
                if not event.is_directory:
                    service._schedule_upload(Path(event.dest_path))

        observer = Observer()
        valid_folders = [Path(folder) for folder in folders if Path(folder).exists()]
        for folder in valid_folders:
            observer.schedule(Handler(), str(folder), recursive=True)

        if not valid_folders:
            raise RuntimeError("No valid watch folders configured.")

        observer.start()
        self._observer = observer
        self._running = True
        log.info("Folder monitor started for %d folder(s).", len(valid_folders))

    def stop(self) -> None:
        if self._observer is None:
            self._running = False
            return
        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None
        self._running = False
        self._seen_recently.clear()
        log.info("Folder monitor stopped.")

    def _schedule_upload(self, path: Path) -> None:
        key = str(path.resolve())
        now = time.monotonic()

        # Prune stale entries to prevent memory leak.
        stale = [k for k, t in self._seen_recently.items() if now - t > _SEEN_EXPIRY_SECONDS]
        for k in stale:
            del self._seen_recently[k]

        last = self._seen_recently.get(key)
        if last and now - last < 3:
            return
        self._seen_recently[key] = now
        threading.Thread(target=self._upload_when_stable, args=(path,), daemon=True).start()

    def _upload_when_stable(self, path: Path) -> None:
        if not self._wait_until_stable(path):
            return
        result = self.upload_service.upload_file(path)
        if self.result_callback:
            self.result_callback(result)

    @staticmethod
    def _wait_until_stable(path: Path, attempts: int = 10, delay: float = 0.75) -> bool:
        last_size = -1
        for _ in range(attempts):
            if not path.exists() or not path.is_file():
                time.sleep(delay)
                continue
            size = path.stat().st_size
            if size == last_size:
                return True
            last_size = size
            time.sleep(delay)
        return path.exists() and path.is_file()
