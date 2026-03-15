from PyQt6.QtWidgets import QTabWidget
from document_generator_tab import DocumentGeneratorTab
from outgoing_requests_list_tab import OutgoingRequestsListTab

class OutgoingRequestsTab(QTabWidget):
    """Главный контейнер вкладки запросов."""
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        
        # Создаём внутренние вкладки
        self.generator_tab = DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger)
        self.list_tab = OutgoingRequestsListTab(self.krd_id, self.db, self.audit_logger, self)
        
        self.addTab(self.generator_tab, "Генерация запросов")
        self.addTab(self.list_tab, "Список запросов")
        
        # Автоматическое обновление списка при успешной генерации
        self.generator_tab.request_saved.connect(self.list_tab.load_requests)