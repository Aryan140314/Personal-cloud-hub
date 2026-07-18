from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.database_service import DatabaseService
from services.monitor_service import MonitorService
from services.upload_service import UploadResult, UploadService
from ui.widgets import page_header

log = logging.getLogger(__name__)

_MAX_UPLOAD_WORKERS = 4


class UploadSignals(QObject):
    completed = pyqtSignal(object)


class DropZone(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setProperty("dragActive", False)
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(7)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Drop files or folders here")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("Title")

        subtitle = QLabel("They will upload into the app's separate Google Drive folder.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_drag_active(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_drag_active(False)
        paths = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path:
                paths.append(local_path)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()

    def _set_drag_active(self, active: bool) -> None:
        self.setProperty("dragActive", active)
        self.style().unpolish(self)
        self.style().polish(self)


class UploadPage(QWidget):
    def __init__(self, db: DatabaseService, upload_service: UploadService):
        super().__init__()
        self.db = db
        self.upload_service = upload_service
        self.signals = UploadSignals()
        self.signals.completed.connect(self._handle_upload_result)
        self.monitor = MonitorService(upload_service, result_callback=self.signals.completed.emit)
        self._pool = ThreadPoolExecutor(max_workers=_MAX_UPLOAD_WORKERS)
        self._queued = 0
        self._completed = 0
        self._failed = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(15)
        layout.addWidget(page_header("Upload Center", "Upload files manually, monitor folders, and recover pending uploads with confidence."))

        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.upload_dropped_paths)
        layout.addWidget(self.drop_zone)

        controls = QHBoxLayout()
        self.upload_button = QPushButton("Select Files")
        self.upload_button.clicked.connect(self.select_files)
        self.monitor_button = QPushButton("Start Monitor")
        self.monitor_button.setProperty("secondary", True)
        self.monitor_button.clicked.connect(self.toggle_monitor)
        self.retry_button = QPushButton("Retry Pending")
        self.retry_button.setProperty("secondary", True)
        self.retry_button.clicked.connect(self.retry_pending)
        controls.addWidget(self.upload_button)
        controls.addWidget(self.monitor_button)
        controls.addWidget(self.retry_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.progress_label = QLabel("")
        self.progress_label.setObjectName("Muted")
        self.progress_label.setWordWrap(True)
        layout.addWidget(self.progress_label)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.destination_label = QLabel("")
        self.destination_label.setObjectName("Muted")
        self.destination_label.setWordWrap(True)
        layout.addWidget(self.destination_label)

        watched_title = QLabel("Watched Folders")
        watched_title.setObjectName("SectionTitle")
        layout.addWidget(watched_title)
        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(120)
        layout.addWidget(self.folder_list)

        logs_title = QLabel("Upload Logs")
        logs_title.setObjectName("SectionTitle")
        layout.addWidget(logs_title)
        self.log_table = QTableWidget(0, 4)
        self.log_table.setHorizontalHeaderLabels(["Time", "File", "Status", "Message"])
        self.log_table.setAlternatingRowColors(True)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.log_table, stretch=1)

        self.refresh()

    # ── Upload actions ────────────────────────────────────────────────

    def select_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Select files to upload")
        self.upload_paths(files)

    def upload_dropped_paths(self, paths: list[str]) -> None:
        files = self._expand_files(paths)
        if not files:
            self.status_label.setText("No files found in dropped item.")
            return
        # Confirmation for large batches.
        if len(files) > 10:
            reply = QMessageBox.question(
                self,
                "Confirm Upload",
                f"You are about to upload {len(files)} files. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.status_label.setText("Upload cancelled.")
                return
        self.status_label.setText(f"Queued {len(files)} file(s) from drag and drop.")
        self.upload_paths(files)

    def upload_paths(self, paths: list[str]) -> None:
        files = self._expand_files(paths)
        self._queued += len(files)
        self._update_progress()
        for file_path in files:
            self._pool.submit(self._upload_async, file_path)

    def _upload_async(self, file_path: str) -> None:
        result = self.upload_service.upload_file(file_path)
        self.signals.completed.emit(result)

    # ── Monitor ───────────────────────────────────────────────────────

    def toggle_monitor(self) -> None:
        if self.monitor.is_running:
            self.stop_monitor()
        else:
            self.start_monitor()

    def start_monitor(self) -> None:
        try:
            folders = self.db.get_setting("watch_folders", [])
            self.monitor.start(folders)
            self.status_label.setText("Folder monitor is running.")
            self.monitor_button.setText("Stop Monitor")
        except Exception as exc:
            self.status_label.setText(str(exc))

    def stop_monitor(self) -> None:
        self.monitor.stop()
        self.status_label.setText("Folder monitor stopped.")
        self.monitor_button.setText("Start Monitor")

    # ── Retry ─────────────────────────────────────────────────────────

    def retry_pending(self) -> None:
        reply = QMessageBox.question(
            self,
            "Retry Pending Uploads",
            "Retry all files waiting for Google Drive setup?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._pool.submit(self._retry_async)

    def _retry_async(self) -> None:
        results = self.upload_service.retry_pending()
        if not results:
            self.signals.completed.emit(UploadResult(None, "Pending uploads", "info", "No pending setup files found."))
            return
        for result in results:
            self.signals.completed.emit(result)

    # ── Result handling ───────────────────────────────────────────────

    def _handle_upload_result(self, result: UploadResult) -> None:
        self._completed += 1
        if result.status == "failed":
            self._failed += 1
        self._update_progress()
        self.status_label.setText(f"{result.filename}: {result.message}")
        self.refresh()

    def _update_progress(self) -> None:
        if self._queued > 0:
            self.progress_label.setText(
                f"Progress: {self._completed}/{self._queued} completed  |  {self._failed} failed"
            )
        else:
            self.progress_label.setText("")

    def reset_counters(self) -> None:
        """Reset the upload progress counters."""
        self._queued = 0
        self._completed = 0
        self._failed = 0
        self._update_progress()

    # ── Refresh ───────────────────────────────────────────────────────

    def refresh(self) -> None:
        self.destination_label.setText(
            f"Google Drive destination: {self.upload_service.drive_service.destination_text()}"
        )

        self.folder_list.clear()
        for folder in self.db.get_setting("watch_folders", []):
            self.folder_list.addItem(folder)

        logs = self.db.get_recent_logs(limit=80)
        self.log_table.setRowCount(len(logs))
        for row_index, row in enumerate(logs):
            values = [row["upload_time"], row["filename"], row["status"], row["message"]]
            for col_index, value in enumerate(values):
                self.log_table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
        self.log_table.resizeColumnsToContents()

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _expand_files(paths: list[str]) -> list[str]:
        files: list[str] = []
        for value in paths:
            path = Path(value)
            if path.is_file():
                files.append(str(path))
            elif path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        files.append(str(child))
        return files
