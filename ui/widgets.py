from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


def format_bytes(value: int | None) -> str:
    size = float(value or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


class MetricCard(QFrame):
    def __init__(self, label: str, value: str = "0"):
        super().__init__()
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("Metric")
        title = QLabel(label)
        title.setObjectName("Muted")

        layout.addWidget(self.value_label)
        layout.addWidget(title)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


def page_header(title: str, subtitle: str) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 10)
    layout.setSpacing(4)

    title_label = QLabel(title)
    title_label.setObjectName("Title")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("Muted")
    subtitle_label.setWordWrap(True)

    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    return widget


def row_widget(*children: QWidget) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)
    for child in children:
        layout.addWidget(child)
    return widget
