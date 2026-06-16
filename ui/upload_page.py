from __future__ import annotations

import threading
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
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
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)
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
        self.signals.completed.connect(self.handle_upload_result)
        self.monitor = MonitorService(upload_service, result_callback=self.signals.completed.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(page_header("Upload Center", "Upload files manually or watch folders automatically."))

        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.upload_dropped_paths)
        layout.addWidget(self.drop_zone)

        controls = QHBoxLayout()
        self.upload_button = QPushButton("Select Files")
        self.upload_button.clicked.connect(self.select_files)
        self.monitor_button = QPushButton("Start Monitor")
        self.monitor_button.clicked.connect(self.toggle_monitor)
        self.retry_button = QPushButton("Retry Pending")
        self.retry_button.clicked.connect(self.retry_pending)
        controls.addWidget(self.upload_button)
        controls.addWidget(self.monitor_button)
        controls.addWidget(self.retry_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        layout.addWidget(self.status_label)

        self.destination_label = QLabel("")
        self.destination_label.setObjectName("Muted")
        layout.addWidget(self.destination_label)

        layout.addWidget(QLabel("Watched Folders"))
        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(120)
        layout.addWidget(self.folder_list)

        layout.addWidget(QLabel("Upload Logs"))
        self.log_table = QTableWidget(0, 4)
        self.log_table.setHorizontalHeaderLabels(["Time", "File", "Status", "Message"])
        self.log_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.log_table, stretch=1)

        self.refresh()

    def select_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Select files to upload")
        self.upload_paths(files)

    def upload_dropped_paths(self, paths: list[str]) -> None:
        files = self._expand_files(paths)
        if not files:
            self.status_label.setText("No files found in dropped item.")
            return
        self.status_label.setText(f"Queued {len(files)} file(s) from drag and drop.")
        self.upload_paths(files)

    def upload_paths(self, paths: list[str]) -> None:
        for file_path in self._expand_files(paths):
            threading.Thread(target=self._upload_async, args=(file_path,), daemon=True).start()

    def _upload_async(self, file_path: str) -> None:
        result = self.upload_service.upload_file(file_path)
        self.signals.completed.emit(result)

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

    def retry_pending(self) -> None:
        threading.Thread(target=self._retry_async, daemon=True).start()

    def _retry_async(self) -> None:
        results = self.upload_service.retry_pending()
        if not results:
            self.signals.completed.emit(UploadResult(None, "Pending uploads", "info", "No pending setup files found."))
            return
        for result in results:
            self.signals.completed.emit(result)

    def handle_upload_result(self, result: UploadResult) -> None:
        self.status_label.setText(f"{result.filename}: {result.message}")
        self.refresh()

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
