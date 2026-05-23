# ui_helpers.py
"""
Вспомогательные утилиты для управления доступом и состоянием интерфейса.
Используется для реализации прав роли 'Читатель' (только просмотр).
"""
from typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTextEdit, QPlainTextEdit,
    QComboBox, QAbstractSpinBox, QCheckBox, QRadioButton,
    QTableView, QTableWidget, QListView, QListWidget, QTreeWidget, QAbstractItemView
)
from PyQt6.QtCore import Qt


def is_reader(user_info: Dict) -> bool:
    """
    Быстрая проверка роли пользователя.
    Args:
        user_info: Словарь с данными текущего пользователя (из authorization.py)
    Returns:
        True, если роль == 'reader'
    """
    return user_info.get('role', '').lower() == 'reader'


def apply_readonly_mode(parent_widget: QWidget, is_read_only: bool) -> None:
    """
    Автоматически переводит все дочерние интерактивные виджеты в режим 'Только просмотр'.
    
    🔹 Поля ввода становятся доступны для выделения и копирования (Ctrl+C), но не для правки.
    🔹 Кнопки, списки и чекбоксы полностью блокируются.
    🔹 Контекстные меню отключаются.

    Args:
        parent_widget: Родительский виджет (окно, вкладка, QGroupBox и т.д.)
        is_read_only: Флаг режима (True - включить режим читателя)
    """
    if not is_read_only:
        return

    # 1. Кнопки (полная блокировка)
    for btn in parent_widget.findChildren(QPushButton):
        btn.setEnabled(False)

    # 2. Текстовые поля (только чтение, сохраняем возможность копирования)
    for le in parent_widget.findChildren(QLineEdit):
        le.setReadOnly(True)
    for te in parent_widget.findChildren(QTextEdit):
        te.setReadOnly(True)
    for pte in parent_widget.findChildren(QPlainTextEdit):
        pte.setReadOnly(True)

    # 3. Выпадающие списки и поля дат/чисел (блокировка)
    for cb in parent_widget.findChildren(QComboBox):
        cb.setEnabled(False)
    # QAbstractSpinBox охватывает QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit
    for sb in parent_widget.findChildren(QAbstractSpinBox):
        sb.setEnabled(False)

    # 4. Чекбоксы и радиокнопки
    for cb in parent_widget.findChildren(QCheckBox):
        cb.setEnabled(False)
    for rb in parent_widget.findChildren(QRadioButton):
        rb.setEnabled(False)

    # 5. Таблицы и списки (отключение редактирования ячеек)
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

    # 6. Отключаем контекстные меню (ПКМ) для всех дочерних виджетов
    for widget in parent_widget.findChildren(QWidget):
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)