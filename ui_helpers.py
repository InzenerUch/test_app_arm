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

# ui_helpers.py
"""
Вспомогательные утилиты для управления доступом, состоянием интерфейса и базовые классы окон.
Используется для реализации прав роли 'Читатель' и настройки поведения диалоговых окон.
"""
from typing import Dict
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTextEdit, QPlainTextEdit,
    QComboBox, QAbstractSpinBox, QCheckBox, QRadioButton,
    QTableView, QTableWidget, QListView, QListWidget, QTreeWidget, QAbstractItemView,
    QDialog  # ✅ Добавлено для класса BaseDialog
)
from PyQt6.QtCore import Qt


# ==============================================================================
# 1. БАЗОВЫЙ КЛАСС ДЛЯ ДИАЛОГОВЫХ ОКОН
# ==============================================================================
class BaseDialog(QDialog):
    """
    Базовый класс для всех диалоговых окон приложения.
    Гарантирует наличие кнопок «Свернуть» и «Развернуть» (актуально для Linux/Ubuntu).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ ИСПРАВЛЕНО: Правильные названия флагов для PyQt6
        self.setWindowFlags(
            Qt.WindowType.Window |                      # Базовое окно
            Qt.WindowType.WindowCloseButtonHint |       # Кнопка закрытия
            Qt.WindowType.WindowMinimizeButtonHint |    # ✅ Кнопка свернуть (исправлено)
            Qt.WindowType.WindowMaximizeButtonHint |    # ✅ Кнопка развернуть (исправлено)
            Qt.WindowType.WindowSystemMenuHint          # Системное меню
        )
        
        # Используем WindowModal. Он позволяет разворачивать окно, в отличие от ApplicationModal.
        self.setWindowModality(Qt.WindowModality.WindowModal)
        
        # Автоматическое удаление из памяти при закрытии
        # self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

# ==============================================================================
# 2. УТИЛИТЫ ДЛЯ УПРАВЛЕНИЯ ДОСТУПОМ (РОЛЬ ЧИТАТЕЛЯ)
# ==============================================================================
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