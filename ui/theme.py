from __future__ import annotations


DARK_THEME = """
QMainWindow, QWidget {
    background: #15171b;
    color: #edf0f2;
    font-family: Segoe UI, Arial;
    font-size: 13px;
}
QFrame#Sidebar {
    background: #101216;
    border-right: 1px solid #252a31;
}
QLabel#Title {
    font-size: 20px;
    font-weight: 700;
}
QLabel#Muted {
    color: #9ca6b2;
}
QLabel#Metric {
    font-size: 24px;
    font-weight: 700;
}
QFrame#Card {
    background: #1d2128;
    border: 1px solid #2d3440;
    border-radius: 8px;
}
QFrame#DropZone {
    background: #101216;
    border: 2px dashed #4b5968;
    border-radius: 8px;
}
QFrame#DropZone[dragActive="true"] {
    background: #1f2c35;
    border-color: #d6a039;
}
QPushButton {
    background: #2b6f7f;
    color: #ffffff;
    border: 0;
    border-radius: 6px;
    padding: 9px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background: #35879a;
}
QPushButton:checked {
    background: #d6a039;
    color: #141414;
}
QPushButton#NavButton {
    text-align: left;
    background: transparent;
    color: #c6ccd3;
}
QPushButton#NavButton:hover {
    background: #1d2128;
}
QPushButton#NavButton:checked {
    background: #27313b;
    color: #ffffff;
}
QLineEdit, QComboBox, QListWidget, QTableWidget {
    background: #101216;
    color: #edf0f2;
    border: 1px solid #303844;
    border-radius: 6px;
    padding: 7px;
}
QHeaderView::section {
    background: #20252d;
    color: #edf0f2;
    border: 0;
    padding: 7px;
}
QTableWidget {
    gridline-color: #303844;
}
QCheckBox {
    spacing: 8px;
}
"""


LIGHT_THEME = """
QMainWindow, QWidget {
    background: #f6f7f9;
    color: #1e242b;
    font-family: Segoe UI, Arial;
    font-size: 13px;
}
QFrame#Sidebar {
    background: #ffffff;
    border-right: 1px solid #d8dde5;
}
QLabel#Title {
    font-size: 20px;
    font-weight: 700;
}
QLabel#Muted {
    color: #65717f;
}
QLabel#Metric {
    font-size: 24px;
    font-weight: 700;
}
QFrame#Card {
    background: #ffffff;
    border: 1px solid #d8dde5;
    border-radius: 8px;
}
QFrame#DropZone {
    background: #ffffff;
    border: 2px dashed #9aa7b5;
    border-radius: 8px;
}
QFrame#DropZone[dragActive="true"] {
    background: #edf6f8;
    border-color: #d59b2c;
}
QPushButton {
    background: #276f7d;
    color: #ffffff;
    border: 0;
    border-radius: 6px;
    padding: 9px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background: #348698;
}
QPushButton:checked {
    background: #d59b2c;
    color: #141414;
}
QPushButton#NavButton {
    text-align: left;
    background: transparent;
    color: #34404c;
}
QPushButton#NavButton:hover {
    background: #edf1f4;
}
QPushButton#NavButton:checked {
    background: #dfe8ee;
    color: #1e242b;
}
QLineEdit, QComboBox, QListWidget, QTableWidget {
    background: #ffffff;
    color: #1e242b;
    border: 1px solid #cbd3dc;
    border-radius: 6px;
    padding: 7px;
}
QHeaderView::section {
    background: #e7ecf1;
    color: #1e242b;
    border: 0;
    padding: 7px;
}
QTableWidget {
    gridline-color: #d8dde5;
}
QCheckBox {
    spacing: 8px;
}
"""


def stylesheet(theme: str) -> str:
    return LIGHT_THEME if theme == "light" else DARK_THEME
