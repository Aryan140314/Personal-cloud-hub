from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.database_service import DatabaseService
from ui.widgets import page_header, row_widget


class SettingsPage(QWidget):
    def __init__(self, db: DatabaseService, theme_callback):
        super().__init__()
        self.db = db
        self.theme_callback = theme_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(page_header("Settings", "Choose watch folders, Drive destination, and app preferences."))

        self.folder_list = QListWidget()
        layout.addWidget(self.folder_list)

        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.clicked.connect(self.add_folder)
        self.remove_folder_button = QPushButton("Remove Selected")
        self.remove_folder_button.clicked.connect(self.remove_selected)
        layout.addWidget(row_widget(self.add_folder_button, self.remove_folder_button))

        self.root_folder_input = QLineEdit()
        self.root_folder_input.setPlaceholderText("Google Drive root folder")
        layout.addWidget(self.root_folder_input)

        self.backup_folder_input = QLineEdit()
        self.backup_folder_input.setPlaceholderText("Optional local backup folder")
        self.choose_backup_button = QPushButton("Choose Backup Folder")
        self.choose_backup_button.clicked.connect(self.choose_backup_folder)
        layout.addWidget(row_widget(self.backup_folder_input, self.choose_backup_button))

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        layout.addWidget(self.theme_combo)

        self.auto_start_check = QCheckBox("Start folder monitor automatically")
        self.notifications_check = QCheckBox("Enable desktop notifications")
        layout.addWidget(self.auto_start_check)
        layout.addWidget(self.notifications_check)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save)
        layout.addWidget(self.save_button)
        layout.addStretch(1)

        self.load()

    def load(self) -> None:
        self.folder_list.clear()
        for folder in self.db.get_setting("watch_folders", []):
            self.folder_list.addItem(folder)
        self.root_folder_input.setText(self.db.get_setting("google_drive_root", "Personal Cloud Hub"))
        self.backup_folder_input.setText(self.db.get_setting("backup_folder", ""))
        self.theme_combo.setCurrentText(self.db.get_setting("theme", "dark"))
        self.auto_start_check.setChecked(bool(self.db.get_setting("auto_start_monitor", False)))
        self.notifications_check.setChecked(bool(self.db.get_setting("notifications", True)))

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose folder to monitor")
        if folder:
            existing = [self.folder_list.item(index).text() for index in range(self.folder_list.count())]
            if folder not in existing:
                self.folder_list.addItem(folder)

    def remove_selected(self) -> None:
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))

    def choose_backup_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose backup folder")
        if folder:
            self.backup_folder_input.setText(folder)

    def save(self) -> None:
        folders = []
        for index in range(self.folder_list.count()):
            folder = self.folder_list.item(index).text()
            if Path(folder).exists():
                folders.append(folder)

        self.db.replace_watch_folders(folders)
        self.db.set_setting("google_drive_root", self.root_folder_input.text().strip() or "Personal Cloud Hub")
        self.db.set_setting("backup_folder", self.backup_folder_input.text().strip())
        self.db.set_setting("theme", self.theme_combo.currentText())
        self.db.set_setting("auto_start_monitor", self.auto_start_check.isChecked())
        self.db.set_setting("notifications", self.notifications_check.isChecked())
        self.theme_callback()
