from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import QUrl

from services.database_service import DatabaseService
from ui.widgets import format_bytes, page_header, row_widget


class SearchPage(QWidget):
    def __init__(self, db: DatabaseService):
        super().__init__()
        self.db = db
        self.rows = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(page_header("Search", "Find files by name, type, category, status, or path."))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files")
        self.search_input.textChanged.connect(self.run_search)
        self.open_button = QPushButton("Open Local File")
        self.open_button.clicked.connect(self.open_selected)
        self.drive_button = QPushButton("Open Drive Link")
        self.drive_button.clicked.connect(self.open_drive_link)
        layout.addWidget(row_widget(self.search_input, self.open_button, self.drive_button))

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
