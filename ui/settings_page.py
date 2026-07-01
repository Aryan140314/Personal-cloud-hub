from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QLabel,
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
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(15)
        layout.addWidget(page_header("Settings", "Choose watch folders, Drive destination, and app preferences."))

        # ── Watch folders ─────────────────────────────────────────────
        watch_title = QLabel("Watch Folders")
        watch_title.setObjectName("SectionTitle")
        layout.addWidget(watch_title)
        self.folder_list = QListWidget()
        layout.addWidget(self.folder_list)

        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.setProperty("secondary", True)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.remove_folder_button = QPushButton("Remove Selected")
        self.remove_folder_button.setProperty("danger", True)
        self.remove_folder_button.clicked.connect(self.remove_selected)
        layout.addWidget(row_widget(self.add_folder_button, self.remove_folder_button))

        # ── Drive root ────────────────────────────────────────────────
        drive_title = QLabel("Google Drive Root Folder")
        drive_title.setObjectName("SectionTitle")
        layout.addWidget(drive_title)
        self.root_folder_input = QLineEdit()
        self.root_folder_input.setPlaceholderText("Google Drive root folder")
        layout.addWidget(self.root_folder_input)

        # ── Local backup ──────────────────────────────────────────────
        backup_title = QLabel("Local Backup Folder (optional)")
        backup_title.setObjectName("SectionTitle")
        layout.addWidget(backup_title)
        self.backup_folder_input = QLineEdit()
        self.backup_folder_input.setPlaceholderText("Optional local backup folder")
        self.choose_backup_button = QPushButton("Choose Backup Folder")
        self.choose_backup_button.setProperty("secondary", True)
        self.choose_backup_button.clicked.connect(self.choose_backup_folder)
        layout.addWidget(row_widget(self.backup_folder_input, self.choose_backup_button))

        # ── Duplicate policy ──────────────────────────────────────────
        duplicate_title = QLabel("Duplicate File Policy")
        duplicate_title.setObjectName("SectionTitle")
        layout.addWidget(duplicate_title)
        self.duplicate_combo = QComboBox()
        self.duplicate_combo.addItems(["skip", "rename", "overwrite"])
        layout.addWidget(self.duplicate_combo)

        # ── Theme ─────────────────────────────────────────────────────
        theme_title = QLabel("Theme")
        theme_title.setObjectName("SectionTitle")
        layout.addWidget(theme_title)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        layout.addWidget(self.theme_combo)

        # ── Toggles ───────────────────────────────────────────────────
        self.auto_start_check = QCheckBox("Start folder monitor automatically")
        self.notifications_check = QCheckBox("Enable desktop notifications")
        layout.addWidget(self.auto_start_check)
        layout.addWidget(self.notifications_check)

        # ── Save button & feedback ────────────────────────────────────
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save)
        layout.addWidget(self.save_button)

        self.save_status_label = QLabel("")
        self.save_status_label.setObjectName("Muted")
        self.save_status_label.setWordWrap(True)
        layout.addWidget(self.save_status_label)

        layout.addStretch(1)

        self.load()

    def load(self) -> None:
        self.folder_list.clear()
        for folder in self.db.get_setting("watch_folders", []):
            self.folder_list.addItem(folder)
        self.root_folder_input.setText(self.db.get_setting("google_drive_root", "Personal Cloud Hub"))
        self.backup_folder_input.setText(self.db.get_setting("backup_folder", ""))
        self.duplicate_combo.setCurrentText(self.db.get_setting("duplicate_policy", "skip"))
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
        dropped = []
        for index in range(self.folder_list.count()):
            folder = self.folder_list.item(index).text()
            if Path(folder).exists():
                folders.append(folder)
            else:
                dropped.append(folder)

        self.db.replace_watch_folders(folders)
        self.db.set_setting("google_drive_root", self.root_folder_input.text().strip() or "Personal Cloud Hub")
        self.db.set_setting("backup_folder", self.backup_folder_input.text().strip())
        self.db.set_setting("duplicate_policy", self.duplicate_combo.currentText())
        self.db.set_setting("theme", self.theme_combo.currentText())
        self.db.set_setting("auto_start_monitor", self.auto_start_check.isChecked())
        self.db.set_setting("notifications", self.notifications_check.isChecked())
        self.theme_callback()

        # User feedback.
        if dropped:
            names = ", ".join(dropped)
            self.save_status_label.setText(f"Settings saved. Removed {len(dropped)} missing folder(s): {names}")
        else:
            self.save_status_label.setText("Settings saved successfully.")

        # Refresh the folder list to reflect dropped items.
        self.folder_list.clear()
        for folder in folders:
            self.folder_list.addItem(folder)
