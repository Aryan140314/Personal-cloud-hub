from __future__ import annotations

import csv
import logging

from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.database_service import DatabaseService
from ui.widgets import page_header

log = logging.getLogger(__name__)


class AnalyticsPage(QWidget):
    def __init__(self, db: DatabaseService):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(15)
        layout.addWidget(page_header("Analytics", "Upload trends and file type distribution."))

        charts = QHBoxLayout()
        self.upload_chart = self._make_chart("Uploads Per Day")
        self.type_chart = self._make_chart("File Types")
        charts.addWidget(self.upload_chart)
        charts.addWidget(self.type_chart)
        layout.addLayout(charts, stretch=1)

        self.summary_table = QTableWidget(0, 2)
        self.summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.summary_table)

        self.export_button = QPushButton("Export Upload History to CSV")
        self.export_button.setProperty("secondary", True)
        self.export_button.clicked.connect(self.export_csv)
        layout.addWidget(self.export_button)

        self.refresh()

    def _make_chart(self, title: str) -> QWidget:
        try:
            import pyqtgraph as pg

            plot = pg.PlotWidget()
            plot.setProperty("chartTitle", title)
            plot.setTitle(title)
            plot.showGrid(x=True, y=True, alpha=0.25)
            plot.setBackground("#151d28")
            return plot
        except Exception:
            return QLabel(f"{title} chart requires pyqtgraph.")

    def set_theme(self, theme: str) -> None:
        colors = {
            "dark": {
                "background": "#151d28",
                "foreground": "#dbe7f3",
            },
            "light": {
                "background": "#ffffff",
                "foreground": "#24364b",
            },
        }[theme if theme == "light" else "dark"]
        for chart in (self.upload_chart, self.type_chart):
            if not hasattr(chart, "setBackground"):
                continue
            chart.setBackground(colors["background"])
            plot_item = chart.getPlotItem()
            plot_item.setTitle(chart.property("chartTitle"), color=colors["foreground"])
            plot_item.getAxis("bottom").setTextPen(colors["foreground"])
            plot_item.getAxis("left").setTextPen(colors["foreground"])
            plot_item.showGrid(x=True, y=True, alpha=0.25)

    def refresh(self) -> None:
        self._refresh_upload_chart()
        self._refresh_type_chart()
        self._refresh_summary()

    def _refresh_upload_chart(self) -> None:
        if not hasattr(self.upload_chart, "clear"):
            return
        rows = list(reversed(self.db.uploads_per_day(limit=7)))
        self.upload_chart.clear()
        totals = [row["total"] for row in rows]
        labels = [row["day"][5:] for row in rows]
        if not totals:
            totals = [0]
            labels = ["No data"]
        self.upload_chart.plot(range(len(totals)), totals, pen=None, symbol="o", symbolBrush="#d6a039")
        axis = self.upload_chart.getAxis("bottom")
        axis.setTicks([list(enumerate(labels))])

    def _refresh_type_chart(self) -> None:
        if not hasattr(self.type_chart, "clear"):
            return
        rows = self.db.file_type_counts(limit=8)
        self.type_chart.clear()
        totals = [row["total"] for row in rows]
        labels = [row["filetype"] for row in rows]
        if not totals:
            totals = [0]
            labels = ["No data"]
        try:
            import pyqtgraph as pg

            bars = pg.BarGraphItem(x=list(range(len(totals))), height=totals, width=0.55, brush="#2b6f7f")
            self.type_chart.addItem(bars)
            axis = self.type_chart.getAxis("bottom")
            axis.setTicks([list(enumerate(labels))])
        except Exception:
            return

    def _refresh_summary(self) -> None:
        stats = self.db.get_dashboard_stats()
        rows = [
            ("Total files", stats["total_files"]),
            ("Uploaded files", stats["uploaded_files"]),
            ("Pending uploads", stats["pending_uploads"]),
            ("Failed uploads", stats["failed_uploads"]),
        ]
        self.summary_table.setRowCount(len(rows))
        for index, (name, value) in enumerate(rows):
            self.summary_table.setItem(index, 0, QTableWidgetItem(name))
            self.summary_table.setItem(index, 1, QTableWidgetItem(str(value)))

    def export_csv(self) -> None:
        """Export all file records to a CSV file."""
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Upload History",
            "upload_history.csv",
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
            log.info("CSV export: %d records to %s", len(all_rows), save_path)
        except Exception as exc:
            QMessageBox.warning(self, "Export Failed", f"Could not write CSV:\n{exc}")
            log.error("CSV export failed: %s", exc)
