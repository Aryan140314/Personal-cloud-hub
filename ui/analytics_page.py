from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from services.database_service import DatabaseService
from ui.widgets import page_header


class AnalyticsPage(QWidget):
    def __init__(self, db: DatabaseService):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(page_header("Analytics", "Upload trends and file type distribution."))

        charts = QHBoxLayout()
        self.upload_chart = self._make_chart("Uploads Per Day")
        self.type_chart = self._make_chart("File Types")
        charts.addWidget(self.upload_chart)
        charts.addWidget(self.type_chart)
        layout.addLayout(charts, stretch=1)

        self.summary_table = QTableWidget(0, 2)
        self.summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.summary_table)

        self.refresh()

    def _make_chart(self, title: str) -> QWidget:
        try:
            import pyqtgraph as pg

            plot = pg.PlotWidget()
            plot.setTitle(title)
            plot.showGrid(x=True, y=True, alpha=0.25)
            return plot
        except Exception:
            return QLabel(f"{title} chart requires pyqtgraph.")

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
