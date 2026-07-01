from __future__ import annotations


DARK_THEME = """
QMainWindow {
    background: #0f141b;
}
QWidget {
    background: #0f141b;
    color: #eef3f8;
    font-family: Segoe UI, Arial;
    font-size: 13px;
}
QFrame#Sidebar {
    background: #111923;
    border-right: 1px solid #233143;
}
QFrame#StatusBar {
    background: #111923;
    border-top: 1px solid #233143;
}
QLabel#Brand {
    color: #ffffff;
    font-size: 19px;
    font-weight: 800;
}
QLabel#Title {
    color: #ffffff;
    font-size: 24px;
    font-weight: 800;
}
QLabel#SectionTitle {
    color: #f7fafc;
    font-size: 15px;
    font-weight: 700;
}
QLabel#Muted {
    color: #9fb0c2;
}
QLabel#Metric {
    color: #ffffff;
    font-size: 27px;
    font-weight: 800;
}
QFrame#Card {
    background: #151d28;
    border: 1px solid #26364a;
    border-radius: 8px;
}
QFrame#Card:hover {
    border-color: #36506d;
}
QFrame#DropZone {
    background: #111923;
    border: 2px dashed #48627d;
    border-radius: 8px;
}
QFrame#DropZone[dragActive="true"] {
    background: #132b34;
    border-color: #14b8a6;
}
QPushButton {
    background: #0f766e;
    color: #ffffff;
    border: 1px solid #119184;
    border-radius: 6px;
    min-height: 18px;
    padding: 8px 13px;
    font-weight: 700;
}
QPushButton:hover {
    background: #0d9488;
    border-color: #2dd4bf;
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
    background: #182333;
    color: #dbe7f3;
    border: 1px solid #344862;
}
QPushButton[secondary="true"]:hover {
    background: #203148;
    border-color: #4f6b8d;
}
QPushButton[danger="true"] {
    background: #9f1239;
    border-color: #be123c;
}
QPushButton[danger="true"]:hover {
    background: #be123c;
    border-color: #fb7185;
}
QPushButton#NavButton {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: #bdc9d6;
    padding: 10px 12px;
}
QPushButton#NavButton:hover {
    background: #182333;
    border-color: #26364a;
}
QPushButton#NavButton:checked {
    background: #e8f7f5;
    border-color: #e8f7f5;
    color: #0f172a;
}
QLineEdit, QComboBox, QListWidget, QTableWidget {
    background: #111923;
    color: #eef3f8;
    border: 1px solid #2b3c51;
    border-radius: 7px;
    padding: 8px;
    selection-background-color: #0f766e;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QListWidget:focus, QTableWidget:focus {
    border-color: #14b8a6;
}
QHeaderView::section {
    background: #182333;
    color: #dbe7f3;
    border: 0;
    border-bottom: 1px solid #2b3c51;
    padding: 8px;
    font-weight: 700;
}
QTableWidget {
    gridline-color: #233143;
    alternate-background-color: #121b26;
}
QTableWidget::item {
    padding: 5px;
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
    background: #ffffff;
    border-right: 1px solid #d7e0ea;
}
QFrame#StatusBar {
    background: #ffffff;
    border-top: 1px solid #d7e0ea;
}
QLabel#Brand {
    color: #101828;
    font-size: 19px;
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
    font-size: 27px;
    font-weight: 800;
}
QFrame#Card {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 8px;
}
QFrame#Card:hover {
    border-color: #b9c8d8;
}
QFrame#DropZone {
    background: #ffffff;
    border: 2px dashed #9aabc0;
    border-radius: 8px;
}
QFrame#DropZone[dragActive="true"] {
    background: #effcf9;
    border-color: #0f766e;
}
QPushButton {
    background: #0f766e;
    color: #ffffff;
    border: 1px solid #0f766e;
    border-radius: 6px;
    min-height: 18px;
    padding: 8px 13px;
    font-weight: 700;
}
QPushButton:hover {
    background: #0d9488;
    border-color: #0d9488;
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
    border-color: #aebfd1;
}
QPushButton[danger="true"] {
    background: #be123c;
    border-color: #be123c;
}
QPushButton[danger="true"]:hover {
    background: #9f1239;
    border-color: #9f1239;
}
QPushButton#NavButton {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    color: #405168;
    padding: 10px 12px;
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
    border-radius: 7px;
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
    padding: 5px;
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


def stylesheet(theme: str) -> str:
    return LIGHT_THEME if theme == "light" else DARK_THEME
