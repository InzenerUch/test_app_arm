from PyQt6.QtWidgets import QTabWidget
from document_generator_tab import DocumentGeneratorTab
from outgoing_requests_list_tab import OutgoingRequestsListTab
from ui_helpers import is_reader
class OutgoingRequestsTab(QTabWidget):
    def __init__(self, krd_id, db_connection, audit_logger=None, user_info=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.user_info = user_info or {}
        self.list_tab = OutgoingRequestsListTab(self.krd_id, self.db, self.audit_logger, self)
        self.addTab(self.list_tab, "📋 Список запросов")
        if not is_reader(self.user_info):
            self.generator_tab = DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger)
            self.insertTab(0, self.generator_tab, "📄 Генерация запросов")
            if hasattr(self.generator_tab, 'request_saved'):
                self.generator_tab.request_saved.connect(self.list_tab.load_requests)
            print(f"📄 [PERMISSION] Вкладка генерации документов создана.")
        else:
            self.generator_tab = None
            print(f"👁️ [READ-ONLY] Вкладка генерации документов скрыта для роли 'reader'.")