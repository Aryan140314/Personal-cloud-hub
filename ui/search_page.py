from __future__ import annotations

import csv
import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.database_service import DatabaseService
from services.upload_service import UploadService
from ui.widgets import format_bytes, page_header, row_widget

log = logging.getLogger(__name__)


class SearchPage(QWidget):
    def __init__(self, db: DatabaseService, upload_service: UploadService):
        super().__init__()
        self.db = db
        self.upload_service = upload_service
        self.rows = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(page_header("Search", "Find files by name, type, category, status, or path."))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files")
        self.search_input.textChanged.connect(self.run_search)
        layout.addWidget(self.search_input)

        # Action buttons row.
        self.open_button = QPushButton("Open Local File")
        self.open_button.clicked.connect(self.open_selected)
        self.drive_button = QPushButton("Open Drive Link")
        self.drive_button.clicked.connect(self.open_drive_link)
        self.delete_button = QPushButton("Delete from Drive")
        self.delete_button.clicked.connect(self.delete_from_drive)
        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_csv)
        layout.addWidget(row_widget(self.open_button, self.drive_button, self.delete_button, self.export_button))

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Type", "Size", "Status", "Path", "Drive"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, stretch=1)
        self.run_search("")

    def run_search(self, text: str) -> None:
        self.rows = self.db.search_files(text, limit=200) if text.strip() else self.db.get_recent_files(limit=200)
        self.table.setRowCount(len(self.rows))
        for row_index, row in enumerate(self.rows):
            values = [
                row["filename"],
                row["category"] or "",
                row["filetype"] or "",
                format_bytes(row["filesize"]),
                row["status"],
                row["filepath"],
                "available" if row["google_drive_link"] else "",
            ]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, row_index)
                self.table.setItem(row_index, col_index, item)
        self.table.resizeColumnsToContents()

    def selected_row(self):
        current = self.table.currentRow()
        if current < 0 or current >= len(self.rows):
            return None
        return self.rows[current]

    def open_selected(self) -> None:
        row = self.selected_row()
        if row:
            QDesktopServices.openUrl(QUrl.fromLocalFile(row["filepath"]))

    def open_drive_link(self) -> None:
        row = self.selected_row()
        if row and row["google_drive_link"]:
            QDesktopServices.openUrl(QUrl(row["google_drive_link"]))

    def delete_from_drive(self) -> None:
        row = self.selected_row()
        if row is None:
            QMessageBox.information(self, "No Selection", "Select a file to delete from Google Drive.")
            return
        if not row["google_drive_id"]:
            QMessageBox.information(self, "Not on Drive", "This file has no Google Drive record.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Move \"{row['filename']}\" to Google Drive trash?\n\nThis can be undone from Google Drive's trash.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self.upload_service.delete_from_drive(row["id"])
        if result.status == "deleted":
            QMessageBox.information(self, "Deleted", f"{result.filename} moved to Drive trash.")
        else:
            QMessageBox.warning(self, "Delete Failed", result.message)
        self.run_search(self.search_input.text())

    def export_csv(self) -> None:
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Files to CSV",
            "personal_cloud_hub_export.csv",
            "CSV Files (*.csv)",
        )
        if not save_path:
            return

        all_rows = self.db.get_all_files_for_export()
        columns = [
            "id", "filename", "filepath", "filesize", "filetype", "category",
            "file_hash", "upload_date", "google_drive_id", "google_drive_link",
            "status", "message", "created_at", "updated_at",
        ]

        try:
            with open(save_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                for row in all_rows:
                    writer.writerow([row[col] for col in columns])
            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {len(all_rows)} records to:\n{save_path}",
            )
            log.info("CSV export: %d records written to %s", len(all_rows), save_path)
        except Exception as exc:
            QMessageBox.warning(self, "Export Failed", f"Could not write CSV:\n{exc}")
            log.error("CSV export failed: %s", exc)
