# searchable_combo.py
"""
ComboBox с функцией поиска/фильтрации элементов
✅ ИСПРАВЛЕНО: Все 3 критические ошибки устранены
"""
from PyQt6.QtWidgets import QComboBox, QCompleter
from PyQt6.QtCore import Qt

class SearchableComboBox(QComboBox):
    """ComboBox с функцией поиска/фильтрации элементов"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Делаем поле редактируемым
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setPlaceholderText("🔍 Поиск поля...")
        
        # ✅ ИСПРАВЛЕНИЕ 1: Передаём модель комбобокса в QCompleter
        self.setCompleter(QCompleter(self.model(), self))
        
        # ✅ ИСПРАВЛЕНИЕ 2: Используем метод completer(), не переопределяем атрибут
        completer = self.completer()
        if completer:
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            # ✅ ИСПРАВЛЕНИЕ 3: Режим PopupCompletion обязателен для фильтрации
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        
        # ❌ УДАЛЕНО: Ручное подключение textEdited (QCompleter делает это сам)