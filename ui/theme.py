from __future__ import annotations


DARK_THEME = """
QMainWindow {
    background: #07111b;
}
QWidget {
    background: #07111b;
    color: #f5f7fb;
    font-family: Segoe UI, Arial;
    font-size: 13px;
}
QFrame#Sidebar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #111b2b, stop:1 #0c1420);
    border-right: 1px solid #23364b;
}
QFrame#StatusBar {
    background: #0d1724;
    border-top: 1px solid #23364b;
}
QLabel#Brand {
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
}
QLabel#Title {
    color: #ffffff;
    font-size: 24px;
    font-weight: 800;
}
QLabel#SectionTitle {
    color: #f7fbff;
    font-size: 15px;
    font-weight: 700;
}
QLabel#Muted {
    color: #90a4b7;
}
QLabel#Metric {
    color: #ffffff;
    font-size: 28px;
    font-weight: 800;
}
QFrame#Card {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #132132, stop:1 #0f1724);
    border: 1px solid #29415d;
    border-radius: 10px;
}
QFrame#Card:hover {
    border-color: #3c6288;
}
QFrame#DropZone {
    background: #0e1723;
    border: 2px dashed #4d6b8f;
    border-radius: 12px;
}
QFrame#DropZone[dragActive="true"] {
    background: #102a33;
    border-color: #14b8a6;
}
QPushButton {
    background: #0f766e;
    color: #ffffff;
    border: 1px solid #14b8a6;
    border-radius: 8px;
    min-height: 20px;
    padding: 8px 14px;
    font-weight: 700;
}
QPushButton:hover {
    background: #15a39a;
}
QPushButton:pressed {
    background: #0b615b;
}
QPushButton:checked {
    background: #f59e0b;
    border-color: #fbbf24;
    color: #101418;
}
QPushButton[secondary="true"] {
    background: #172335;
    color: #dce7f4;
    border: 1px solid #2f4460;
}
QPushButton[secondary="true"]:hover {
    background: #21344b;
}
QPushButton[danger="true"] {
    background: #b91c45;
    border-color: #f43f5e;
}
QPushButton[danger="true"]:hover {
    background: #dc274c;
}
QPushButton#NavButton {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: #b9c7d8;
    padding: 10px 12px;
    border-radius: 8px;
}
QPushButton#NavButton:hover {
    background: #172536;
    border-color: #25384e;
}
QPushButton#NavButton:checked {
    background: #e8f7f5;
    border-color: #e8f7f5;
    color: #0f172a;
}
QLineEdit, QComboBox, QListWidget, QTableWidget {
    background: #0e1723;
    color: #f5f7fb;
    border: 1px solid #2d4360;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #0f766e;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QListWidget:focus, QTableWidget:focus {
    border-color: #14b8a6;
}
QHeaderView::section {
    background: #14233a;
    color: #dce7f4;
    border: 0;
    border-bottom: 1px solid #2d4360;
    padding: 8px;
    font-weight: 700;
}
QTableWidget {
    gridline-color: #24364a;
    alternate-background-color: #101b2b;
}
QTableWidget::item {
    padding: 6px;
}
QTableWidget::item:selected, QListWidget::item:selected {
    background: #0f766e;
    color: #ffffff;
}
QComboBox::drop-down {
    border: 0;
    width: 26px;
}
QCheckBox {
    spacing: 9px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""


LIGHT_THEME = """
QMainWindow {
    background: #f4f7fb;
}
QWidget {
    background: #f4f7fb;
    color: #182230;
    font-family: Segoe UI, Arial;
    font-size: 13px;
}
QFrame#Sidebar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #edf4f8);
    border-right: 1px solid #d7e0ea;
}
QFrame#StatusBar {
    background: #ffffff;
    border-top: 1px solid #d7e0ea;
}
QLabel#Brand {
    color: #101828;
    font-size: 20px;
    font-weight: 800;
}
QLabel#Title {
    color: #101828;
    font-size: 24px;
    font-weight: 800;
}
QLabel#SectionTitle {
    color: #101828;
    font-size: 15px;
    font-weight: 700;
}
QLabel#Muted {
    color: #66778a;
}
QLabel#Metric {
    color: #101828;
    font-size: 28px;
    font-weight: 800;
}
QFrame#Card {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 10px;
}
QFrame#Card:hover {
    border-color: #b9c8d8;
}
QFrame#DropZone {
    background: #ffffff;
    border: 2px dashed #9aabc0;
    border-radius: 12px;
}
QFrame#DropZone[dragActive="true"] {
    background: #effcf9;
    border-color: #0f766e;
}
QPushButton {
    background: #0f766e;
    color: #ffffff;
    border: 1px solid #0f766e;
    border-radius: 8px;
    min-height: 20px;
    padding: 8px 14px;
    font-weight: 700;
}
QPushButton:hover {
    background: #0d9488;
}
QPushButton:pressed {
    background: #0b615b;
}
QPushButton:checked {
    background: #f59e0b;
    border-color: #f59e0b;
    color: #101828;
}
QPushButton[secondary="true"] {
    background: #ffffff;
    color: #24364b;
    border: 1px solid #c9d6e3;
}
QPushButton[secondary="true"]:hover {
    background: #edf4f8;
}
QPushButton[danger="true"] {
    background: #be123c;
    border-color: #be123c;
}
QPushButton[danger="true"]:hover {
    background: #9f1239;
}
QPushButton#NavButton {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: #405168;
    padding: 10px 12px;
    border-radius: 8px;
}
QPushButton#NavButton:hover {
    background: #eef4f8;
    border-color: #dbe4ee;
}
QPushButton#NavButton:checked {
    background: #102331;
    border-color: #102331;
    color: #ffffff;
}
QLineEdit, QComboBox, QListWidget, QTableWidget {
    background: #ffffff;
    color: #182230;
    border: 1px solid #cbd8e5;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #0f766e;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QListWidget:focus, QTableWidget:focus {
    border-color: #0f766e;
}
QHeaderView::section {
    background: #edf3f8;
    color: #24364b;
    border: 0;
    border-bottom: 1px solid #cbd8e5;
    padding: 8px;
    font-weight: 700;
}
QTableWidget {
    gridline-color: #e4ebf2;
    alternate-background-color: #f8fbfd;
}
QTableWidget::item {
    padding: 6px;
}
QTableWidget::item:selected, QListWidget::item:selected {
    background: #0f766e;
    color: #ffffff;
}
QComboBox::drop-down {
    border: 0;
    width: 26px;
}
QCheckBox {
    spacing: 9px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""


def stylesheet(theme_name: str) -> str:
    theme_name = (theme_name or "dark").lower()
    if theme_name == "light":
        return LIGHT_THEME
    return DARK_THEME
