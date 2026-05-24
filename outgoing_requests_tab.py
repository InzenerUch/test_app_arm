# outgoing_requests_tab.py
"""
Главный контейнер вкладки запросов.
✅ АДАПТИРОВАНО: Скрытие вкладки генерации для роли 'reader'
✅ ИСПРАВЛЕНО: Добавлен параметр user_info для проверки прав
"""
from PyQt6.QtWidgets import QTabWidget
from document_generator_tab import DocumentGeneratorTab
from outgoing_requests_list_tab import OutgoingRequestsListTab
from ui_helpers import is_reader  # 🔒 Импорт функции проверки роли

class OutgoingRequestsTab(QTabWidget):
    """Главный контейнер вкладки запросов."""
    
    def __init__(self, krd_id, db_connection, audit_logger=None, user_info=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.user_info = user_info or {}  # ✅ Сохраняем данные пользователя
        
        # 1. Список запросов (история) — доступен всем (в режиме чтения кнопки удаляются внутри list_tab)
        # Передаем self как parent, чтобы list_tab мог при необходимости получить доступ к user_info
        self.list_tab = OutgoingRequestsListTab(self.krd_id, self.db, self.audit_logger, self)
        self.addTab(self.list_tab, "📋 Список запросов")
        
        # 🔒 2. Генерация документов — только для НЕ читателей
        if not is_reader(self.user_info):
            # Создаем вкладку генерации
            self.generator_tab = DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger)
            
            # Вставляем вкладку генерации ПЕРЕД списком (индекс 0), чтобы она была первой
            self.insertTab(0, self.generator_tab, "📄 Генерация запросов")
            
            # Автоматическое обновление списка при успешной генерации
            if hasattr(self.generator_tab, 'request_saved'):
                self.generator_tab.request_saved.connect(self.list_tab.load_requests)
                
            print(f"📄 [PERMISSION] Вкладка генерации документов создана.")
        else:
            # 🔒 Для читателя вкладка генерации НЕ создается и не добавляется в интерфейс
            self.generator_tab = None
            print(f"👁️ [READ-ONLY] Вкладка генерации документов скрыта для роли 'reader'.")