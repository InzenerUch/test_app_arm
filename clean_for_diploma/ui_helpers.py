from typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTextEdit, QPlainTextEdit,
    QComboBox, QAbstractSpinBox, QCheckBox, QRadioButton,
    QTableView, QTableWidget, QListView, QListWidget, QTreeWidget, QAbstractItemView
)
from PyQt6.QtCore import Qt
def is_reader(user_info: Dict) -> bool:
    return user_info.get('role', '').lower() == 'reader'
def apply_readonly_mode(parent_widget: QWidget, is_read_only: bool) -> None:
    if not is_read_only:
        return
    for btn in parent_widget.findChildren(QPushButton):
        btn.setEnabled(False)
    for le in parent_widget.findChildren(QLineEdit):
        le.setReadOnly(True)
    for te in parent_widget.findChildren(QTextEdit):
        te.setReadOnly(True)
    for pte in parent_widget.findChildren(QPlainTextEdit):
        pte.setReadOnly(True)
    for cb in parent_widget.findChildren(QComboBox):
        cb.setEnabled(False)
    for sb in parent_widget.findChildren(QAbstractSpinBox):
        sb.setEnabled(False)
    for cb in parent_widget.findChildren(QCheckBox):
        cb.setEnabled(False)
    for rb in parent_widget.findChildren(QRadioButton):
        rb.setEnabled(False)
    for tv in parent_widget.findChildren(QTableView):
        tv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    for tw in parent_widget.findChildren(QTableWidget):
        tw.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    for lv in parent_widget.findChildren(QListView):
        lv.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    for lw in parent_widget.findChildren(QListWidget):
        lw.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    for trw in parent_widget.findChildren(QTreeWidget):
        trw.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    for widget in parent_widget.findChildren(QWidget):
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)