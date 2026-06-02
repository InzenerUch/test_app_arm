import re
from PyQt6.QtWidgets import (
    QCompleter, QListWidget, QListWidgetItem, QFrame,
    QVBoxLayout, QGraphicsDropShadowEffect, QApplication, QTextEdit
)
from PyQt6.QtGui import QColor, QFont, QTextOption
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QEvent, QTimer, QSize, QStringListModel
from PyQt6.QtSql import QSqlQuery
class AutoCompletePopup(QFrame):
    item_selected = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid
                border-radius: 4px;
            }
            QListWidget {
                background-color: white;
                border: none;
                outline: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 10px;
                border-radius: 2px;
                border-bottom: 1px solid
            }
            QListWidget::item:last-child {
                border-bottom: none;
            }
            QListWidget::item:selected {
                background-color:
                color: white;
            }
            QListWidget::item:hover {
                background-color:
            }
Обработка клика по элементу"""
        self.item_selected.emit(item.text())
        self.hide()
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
                current = self.list_widget.currentItem()
                if current:
                    self._on_item_clicked(current)
                return True
            elif event.key() == Qt.Key.Key_Escape:
                self.hide()
                return True
            elif event.key() == Qt.Key.Key_Up:
                current_row = self.list_widget.currentRow()
                if current_row > 0:
                    self.list_widget.setCurrentRow(current_row - 1)
                return True
            elif event.key() == Qt.Key.Key_Down:
                current_row = self.list_widget.currentRow()
                if current_row < self.list_widget.count() - 1:
                    self.list_widget.setCurrentRow(current_row + 1)
                return True
        return super().eventFilter(obj, event)
    def set_items(self, items, current_text=""):
        self.list_widget.clear()
        for item in items:
            list_item = QListWidgetItem(item)
            list_item.setToolTip(item)
            self.list_widget.addItem(list_item)
        if current_text:
            for i in range(self.list_widget.count()):
                list_item = self.list_widget.item(i)
                if list_item.text().lower().startswith(current_text.lower()):
                    self.list_widget.setCurrentItem(list_item)
                    break
        self.adjustSize()
        max_height = 300
        if self.height() > max_height:
            self.setMaximumHeight(max_height)
    def show_at(self, point):
        screen = QApplication.primaryScreen().geometry()
        if point.y() + self.height() > screen.bottom():
            point.setY(point.y() - self.height())
        if point.x() + self.width() > screen.right():
            point.setX(screen.right() - self.width() - 10)
        self.move(point)
        self.show()
        self.list_widget.setFocus()
class AutoCompleteTextEdit(QTextEdit):
    def __init__(self, parent=None, max_lines=3):
        super().__init__(parent)
        self.max_lines = max_lines
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self._autocomplete_values = []
        self._autocomplete_popup = None
        self._autocomplete_max_items = 15
        self._autocomplete_case_sensitive = False
        self._autocomplete_show_on_focus = True
        self._db_connection = None
        self._table_name = ""
        self._column_name = ""
        self._popup_timer = QTimer()
        self._popup_timer.setSingleShot(True)
        self._popup_timer.timeout.connect(self._show_popup_delayed)
        QTimer.singleShot(0, self.resizeToContents)
    def setup_autocomplete(self, db_connection, table_name, column_name,
                          max_items=15, case_sensitive=False, show_on_focus=True):
        self._db_connection = db_connection
        self._table_name = table_name
        self._column_name = column_name
        self._autocomplete_max_items = max_items
        self._autocomplete_case_sensitive = case_sensitive
        self._autocomplete_show_on_focus = show_on_focus
        self._load_autocomplete_values()
        self._create_popup()
        self.textChanged.connect(self._on_text_changed)
        if show_on_focus:
            original_focus = self.focusInEvent
            def new_focus(event):
                original_focus(event)
                if len(self.toPlainText()) <= 1:
                    self._show_popup("")
            self.focusInEvent = new_focus
    def _create_popup(self):
        self._autocomplete_popup = AutoCompletePopup(self)
        self._autocomplete_popup.item_selected.connect(self._on_item_selected)
    def _load_autocomplete_values(self):
        if not self._db_connection or not self._table_name or not self._column_name:
            return
        if not re.match(r'^\w+$', self._table_name) or not re.match(r'^\w+$', self._column_name):
            return
        query = QSqlQuery(self._db_connection)
        query.prepare(f"""
            SELECT DISTINCT {self._column_name}
            FROM krd.{self._table_name}
            WHERE {self._column_name} IS NOT NULL
              AND TRIM({self._column_name}) != ''
            ORDER BY {self._column_name}
Обработка изменения текста"""
        cursor = self.textCursor()
        cursor.select(cursor.SelectionType.WordUnderCursor)
        current_word = cursor.selectedText()
        if len(current_word) >= 1:
            self._popup_timer.start(150)
        else:
            self._popup_timer.stop()
            if self._autocomplete_popup:
                self._autocomplete_popup.hide()
    def _show_popup_delayed(self):
        cursor = self.textCursor()
        cursor.select(cursor.SelectionType.WordUnderCursor)
        current_word = cursor.selectedText()
        self._show_popup(current_word)
    def _show_popup(self, current_word):
        if not self._autocomplete_popup or not self._autocomplete_values:
            return
        if self._autocomplete_case_sensitive:
            filtered = [v for v in self._autocomplete_values if current_word in v]
        else:
            filtered = [v for v in self._autocomplete_values if current_word.lower() in v.lower()]
        filtered = filtered[:self._autocomplete_max_items]
        if filtered:
            self._autocomplete_popup.set_items(filtered, current_word)
            cursor_rect = self.cursorRect()
            global_point = self.viewport().mapToGlobal(cursor_rect.bottomLeft())
            self._autocomplete_popup.show_at(global_point)
        else:
            self._autocomplete_popup.hide()
    def _on_item_selected(self, text):
        cursor = self.textCursor()
        cursor.select(cursor.SelectionType.WordUnderCursor)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        if self._autocomplete_popup:
            self._autocomplete_popup.hide()
    def sizeHint(self):
        base_size = super().sizeHint()
        line_height = self.fontMetrics().lineSpacing()
        line_count = self.document().lineCount()
        line_count = min(line_count, self.max_lines)
        frame_height = self.frameWidth() * 2
        content_height = line_height * line_count
        return QSize(base_size.width(), content_height + frame_height)
    def resizeToContents(self):
        hint = self.sizeHint()
        self.setFixedHeight(hint.height())
    def setPlainText(self, text):
        super().setPlainText(text)
        QTimer.singleShot(0, self.resizeToContents)
    def refresh_values(self):
        self._load_autocomplete_values()
class AutocompleteHelper:
    def __init__(self, db_connection):
        self.db = db_connection
        self._cache = {}
        self._field_refs = []
    def setup_autocomplete(self, widget, table_name, column_name, max_items=15,
                          case_sensitive=False, show_on_focus=True):
        from PyQt6.QtWidgets import QLineEdit
        cache_key = f"{table_name}_{column_name}"
        if cache_key in self._cache:
            values = self._cache[cache_key]
        else:
            values = self._load_unique_values(table_name, column_name)
            self._cache[cache_key] = values
        self._field_refs.append({
            'widget': widget,
            'table': table_name,
            'column': column_name,
            'max_items': max_items,
            'case_sensitive': case_sensitive,
            'show_on_focus': show_on_focus,
            'values': values
        })
        if isinstance(widget, QLineEdit):
            self._setup_line_edit(widget, values, max_items, case_sensitive, show_on_focus)
        elif isinstance(widget, AutoCompleteTextEdit):
            widget.setup_autocomplete(
                self.db, table_name, column_name,
                max_items=max_items,
                case_sensitive=case_sensitive,
                show_on_focus=show_on_focus
            )
        print(f"✅ Настроено: {table_name}.{column_name} ({len(values)} значений)")
        return widget
    def _setup_line_edit(self, line_edit, values, max_items, case_sensitive, show_on_focus):
        if not values:
            return
        model = QStringListModel(values, line_edit)
        completer = QCompleter(model, line_edit)
        completer.setCaseSensitivity(
            Qt.CaseSensitivity.CaseSensitive if case_sensitive
            else Qt.CaseSensitivity.CaseInsensitive
        )
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setMaxVisibleItems(max_items)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        line_edit.setCompleter(completer)
        if show_on_focus:
            if not hasattr(line_edit, '_autocomplete_helper'):
                line_edit._autocomplete_helper = self
                line_edit._autocomplete_completer = completer
                original_focus = line_edit.focusInEvent
                original_mouse = line_edit.mousePressEvent
                def new_focus(event):
                    original_focus(event)
                    if len(line_edit.text()) <= 1:
                        completer.setCompletionPrefix("")
                        completer.complete()
                def new_mouse(event):
                    original_mouse(event)
                    if len(line_edit.text()) <= 1:
                        completer.setCompletionPrefix("")
                        completer.complete()
                line_edit.focusInEvent = new_focus
                line_edit.mousePressEvent = new_mouse
    def _load_unique_values(self, table_name, column_name):
        if not re.match(r'^\w+$', table_name) or not re.match(r'^\w+$', column_name):
            return []
        query = QSqlQuery(self.db)
        query.prepare(f"""
            SELECT DISTINCT {column_name}
            FROM krd.{table_name}
            WHERE {column_name} IS NOT NULL
              AND TRIM({column_name}) != ''
            ORDER BY {column_name}
Очистка кэша"""
        self._cache.clear()
    def refresh_all_fields(self):
        print("🔄 Обновление данных автодополнения...")
        updated_count = 0
        for field_ref in self._field_refs:
            widget = field_ref['widget']
            table_name = field_ref['table']
            column_name = field_ref['column']
            cache_key = f"{table_name}_{column_name}"
            from PyQt6.QtWidgets import QLineEdit
            values = self._load_unique_values(table_name, column_name)
            self._cache[cache_key] = values
            field_ref['values'] = values
            if isinstance(widget, QLineEdit):
                completer = widget.completer()
                if completer:
                    model = completer.model()
                    if isinstance(model, QStringListModel):
                        model.setStringList(values)
                        updated_count += 1
            elif isinstance(widget, AutoCompleteTextEdit):
                widget._autocomplete_values = values
                updated_count += 1
        print(f"✅ Обновлено {updated_count} полей автодополнения")