"""
Вспомогательный модуль для настройки автодополнения в текстовых полях
С поддержкой показа всех вариантов при фокусе на поле
"""
import re
from PyQt6.QtWidgets import QCompleter
from PyQt6.QtCore import Qt,QStringListModel
from PyQt6.QtSql import QSqlQuery


class AutocompleteHelper:
    """Класс для настройки автодополнения в QLineEdit"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        # Кэш для хранения значений (повышает производительность)
        self._cache = {}
    
    def setup_autocomplete(self, line_edit, table_name, column_name, max_items=15, 
                          case_sensitive=False, show_on_focus=True):
        """
        Настройка автодополнения для QLineEdit
        Args:
            line_edit: QLineEdit для настройки
            table_name: имя таблицы в схеме krd
            column_name: имя столбца
            max_items: максимальное количество отображаемых подсказок
            case_sensitive: чувствительность к регистру
            show_on_focus: показывать все варианты при фокусе на поле (по умолчанию True)
        """
        # Генерируем ключ кэша
        cache_key = f"{table_name}_{column_name}"
        
        # Проверяем кэш
        if cache_key in self._cache:
            values = self._cache[cache_key]
        else:
            # Загружаем уникальные значения из базы
            values = self._load_unique_values(table_name, column_name)
            # Сохраняем в кэш
            self._cache[cache_key] = values
        
        if not values:
            return None
        
        # Создаем модель и комплектер
        model = QStringListModel(values, line_edit)
        completer = QCompleter(model, line_edit)
        
        # Настройка поиска
        completer.setCaseSensitivity(
            Qt.CaseSensitivity.CaseSensitive if case_sensitive 
            else Qt.CaseSensitivity.CaseInsensitive
        )
        completer.setFilterMode(Qt.MatchFlag.MatchContains)  # Поиск по любой части строки
        completer.setMaxVisibleItems(max_items)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        
        # Устанавливаем комплектер в поле
        line_edit.setCompleter(completer)
        
        # === КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Показ подсказок при фокусе ===
        if show_on_focus:
            # Сохраняем оригинальные методы
            line_edit._original_focus_in_event = line_edit.focusInEvent
            line_edit._original_mouse_press_event = line_edit.mousePressEvent
            
            # Переопределяем методы
            line_edit.focusInEvent = lambda event: self._on_focus_in(
                line_edit, completer, event
            )
            line_edit.mousePressEvent = lambda event: self._on_mouse_press(
                line_edit, completer, event
            )
        
        # Подключаем сигнал для фильтрации при вводе
        line_edit.textChanged.connect(
            lambda text: self._on_text_changed(line_edit, completer, text)
        )
        
        return completer
    
    def _on_focus_in(self, line_edit, completer, event):
        """
        Показывать все варианты при получении фокуса
        Вызывается когда поле получает фокус (клик или Tab)
        """
        # Вызываем оригинальный focusInEvent
        if line_edit._original_focus_in_event:
            line_edit._original_focus_in_event(event)
        
        # Показываем все варианты если поле пустое или 1 символ
        if len(line_edit.text()) <= 1:
            completer.setCompletionPrefix("")
            completer.complete()
    
    def _on_mouse_press(self, line_edit, completer, event):
        """
        Показывать все варианты при клике на поле
        """
        # Вызываем оригинальный mousePressEvent
        if line_edit._original_mouse_press_event:
            line_edit._original_mouse_press_event(event)
        
        # Показываем все варианты если поле пустое или 1 символ
        if len(line_edit.text()) <= 1:
            completer.setCompletionPrefix("")
            completer.complete()
    
    def _on_text_changed(self, line_edit, completer, text):
        """
        Фильтрация подсказок при вводе текста
        """
        if len(text) <= 1:
            completer.setCompletionPrefix("")
            completer.complete()
        else:
            completer.setCompletionPrefix(text)
            completer.complete()
    
    def _load_unique_values(self, table_name, column_name):
        """
        Загрузка уникальных значений из базы данных
        Args:
            table_name: имя таблицы
            column_name: имя столбца
        Returns:
            list: отсортированный список уникальных значений
        """
        # Защита от SQL-инъекций
        if not re.match(r'^\w+$', table_name) or not re.match(r'^\w+$', column_name):
            print(f"⚠️ Неверное имя таблицы или столбца: {table_name}, {column_name}")
            return []
        
        query = QSqlQuery(self.db)
        query.prepare(f"""
            SELECT DISTINCT {column_name} 
            FROM krd.{table_name} 
            WHERE {column_name} IS NOT NULL 
              AND TRIM({column_name}) != ''
            ORDER BY {column_name}
        """)
        
        if not query.exec():
            print(f"❌ Ошибка загрузки автодополнения для {table_name}.{column_name}: {query.lastError().text()}")
            return []
        
        values = []
        while query.next():
            val = query.value(0)
            if val and str(val).strip():
                values.append(str(val))
        
        print(f"✅ Загружено {len(values)} уникальных значений для {table_name}.{column_name}")
        return values
    
    def clear_cache(self):
        """Очистка кэша (вызывать после сохранения новых данных)"""
        self._cache.clear()
        print("🧹 Кэш автодополнения очищен")
    
    def refresh_field(self, line_edit, table_name, column_name):
        """Обновление автодополнения для конкретного поля"""
        cache_key = f"{table_name}_{column_name}"
        if cache_key in self._cache:
            del self._cache[cache_key]
        self.setup_autocomplete(line_edit, table_name, column_name)