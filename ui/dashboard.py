from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.database_service import DatabaseService
from services.drive_service import DriveService
from services.upload_service import UploadService
from ui.analytics_page import AnalyticsPage
from ui.search_page import SearchPage
from ui.settings_page import SettingsPage
from ui.theme import stylesheet
from ui.upload_page import UploadPage
from ui.widgets import MetricCard, format_bytes, page_header


class DashboardPage(QWidget):
    def __init__(self, db: DatabaseService, drive_service: DriveService):
        super().__init__()
        self.db = db
        self.drive_service = drive_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(page_header("Dashboard", "Live overview of your personal cloud archive."))

        grid = QGridLayout()
        grid.setSpacing(12)
        self.cards = {
            "total_files": MetricCard("Total Files"),
            "storage_used": MetricCard("Storage Used"),
            "uploads_today": MetricCard("Uploads Today"),
            "failed_uploads": MetricCard("Failed Uploads"),
            "pending_uploads": MetricCard("Pending"),
            "drive": MetricCard("Drive Status", self.drive_service.status_text()),
        }
        for index, card in enumerate(self.cards.values()):
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)

        recent_card = QFrame()
        recent_card.setObjectName("Card")
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(16, 14, 16, 16)
        recent_layout.addWidget(QLabel("Recent Activity"))

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Size", "Status", "Updated"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        recent_layout.addWidget(self.table)
        layout.addWidget(recent_card, stretch=1)

        self.refresh()

    def refresh(self) -> None:
        stats = self.db.get_dashboard_stats()
        self.cards["total_files"].set_value(str(stats["total_files"]))
        self.cards["storage_used"].set_value(format_bytes(stats["storage_used"]))
        self.cards["uploads_today"].set_value(str(stats["uploads_today"]))
        self.cards["failed_uploads"].set_value(str(stats["failed_uploads"]))
        self.cards["pending_uploads"].set_value(str(stats["pending_uploads"]))
        self.cards["drive"].set_value(self.drive_service.status_text())

        rows = self.db.get_recent_files(limit=12)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["filename"],
                row["category"] or "",
                format_bytes(row["filesize"]),
                row["status"],
                row["updated_at"],
            ]
            for col_index, value in enumerate(values):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseService, drive_service: DriveService, upload_service: UploadService):
        super().__init__()
        self.db = db
        self.drive_service = drive_service
        self.upload_service = upload_service
        self.setWindowTitle("Personal Cloud Hub")
        self.resize(1180, 760)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 18, 14, 18)
        sidebar_layout.setSpacing(8)

        brand = QLabel("Personal Cloud Hub")
        brand.setObjectName("Title")
        sidebar_layout.addWidget(brand)
        status = QLabel("Automatic file backup")
        status.setObjectName("Muted")
        sidebar_layout.addWidget(status)
        sidebar_layout.addSpacing(16)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage(db, drive_service)
        self.upload_page = UploadPage(db, upload_service)
        self.search_page = SearchPage(db)
        self.analytics_page = AnalyticsPage(db)
        self.settings_page = SettingsPage(db, self.apply_current_settings)

        self.pages = [
            ("Dashboard", self.dashboard_page),
            ("Upload Center", self.upload_page),
            ("Search", self.search_page),
            ("Analytics", self.analytics_page),
            ("Settings", self.settings_page),
        ]

        self.nav_buttons: list[QPushButton] = []
        for index, (label, page) in enumerate(self.pages):
            self.stack.addWidget(page)
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self.set_page(i))
            self.nav_buttons.append(button)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)
        layout.addWidget(sidebar)
        layout.addWidget(self.stack, stretch=1)

        self.nav_buttons[0].setChecked(True)
        self.apply_current_settings()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_current_pages)
        self.timer.start(5000)

        if self.db.get_setting("auto_start_monitor", False):
            self.upload_page.start_monitor()

    def set_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        self.refresh_current_pages()

    def refresh_current_pages(self) -> None:
        self.dashboard_page.refresh()
        self.upload_page.refresh()
        self.analytics_page.refresh()

    def apply_current_settings(self) -> None:
        self.drive_service.set_root_folder_name(self.db.get_setting("google_drive_root", "Personal Cloud Hub"))
        self.setStyleSheet(stylesheet(self.db.get_setting("theme", "dark")))

    def closeEvent(self, event):
        self.upload_page.stop_monitor()
        super().closeEvent(event)
