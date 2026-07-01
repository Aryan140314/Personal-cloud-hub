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
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(18)
        layout.addWidget(page_header("Dashboard", "Live overview of your personal cloud archive."))

        grid = QGridLayout()
        grid.setSpacing(14)
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
        recent_layout.setContentsMargins(18, 16, 18, 18)
        recent_layout.setSpacing(12)
        recent_title = QLabel("Recent Activity")
        recent_title.setObjectName("SectionTitle")
        recent_layout.addWidget(recent_title)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["File", "Category", "Size", "Status", "Updated"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
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
        self.resize(1240, 790)

        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(236)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 22, 16, 18)
        sidebar_layout.setSpacing(8)

        brand = QLabel("Personal Cloud Hub")
        brand.setObjectName("Brand")
        sidebar_layout.addWidget(brand)
        status = QLabel("Automatic file backup")
        status.setObjectName("Muted")
        sidebar_layout.addWidget(status)
        sidebar_layout.addSpacing(16)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage(db, drive_service)
        self.upload_page = UploadPage(db, upload_service)
        self.search_page = SearchPage(db, upload_service)
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
        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.stack, stretch=1)
        main_layout.addWidget(body, stretch=1)

        # ── Status bar ────────────────────────────────────────────────
        self.status_bar = QFrame()
        self.status_bar.setObjectName("StatusBar")
        self.status_bar.setFixedHeight(40)
        status_bar_layout = QHBoxLayout(self.status_bar)
        status_bar_layout.setContentsMargins(18, 0, 18, 0)
        status_bar_layout.setSpacing(24)

        self.sb_files_label = QLabel("")
        self.sb_files_label.setObjectName("Muted")
        self.sb_monitor_label = QLabel("")
        self.sb_monitor_label.setObjectName("Muted")
        self.sb_drive_label = QLabel("")
        self.sb_drive_label.setObjectName("Muted")

        status_bar_layout.addWidget(self.sb_files_label)
        status_bar_layout.addWidget(self.sb_monitor_label)
        status_bar_layout.addStretch(1)
        status_bar_layout.addWidget(self.sb_drive_label)
        main_layout.addWidget(self.status_bar)

        self.nav_buttons[0].setChecked(True)
        self.apply_current_settings()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(5000)

        if self.db.get_setting("auto_start_monitor", False):
            self.upload_page.start_monitor()

        self._refresh_status_bar()

    def set_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        self._refresh_visible_page()

    def _on_tick(self) -> None:
        """Timer callback — refresh only what is visible."""
        self._refresh_visible_page()
        self._refresh_status_bar()

    def _refresh_visible_page(self) -> None:
        """Only refresh the currently visible page to save CPU/DB queries."""
        current = self.stack.currentIndex()
        page = self.pages[current][1]
        if hasattr(page, "refresh"):
            page.refresh()

    def _refresh_status_bar(self) -> None:
        stats = self.db.get_dashboard_stats()
        total = stats["total_files"]
        uploaded = stats["uploaded_files"]
        failed = stats["failed_uploads"]
        pending = stats["pending_uploads"]

        self.sb_files_label.setText(
            f"Files: {total}  |  Uploaded: {uploaded}  |  Pending: {pending}  |  Failed: {failed}"
        )

        monitor_status = "Running" if self.upload_page.monitor.is_running else "Stopped"
        self.sb_monitor_label.setText(f"Monitor: {monitor_status}")
        self.sb_drive_label.setText(self.drive_service.status_text())

    def apply_current_settings(self) -> None:
        self.drive_service.set_root_folder_name(self.db.get_setting("google_drive_root", "Personal Cloud Hub"))
        theme = self.db.get_setting("theme", "dark")
        self.setStyleSheet(stylesheet(theme))
        self.analytics_page.set_theme(theme)

    def closeEvent(self, event):

        self.timer.stop()

        self.upload_page.stop_monitor()

        self.upload_page.shutdown_pool()

        super().closeEvent(event)
