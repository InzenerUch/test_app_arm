"""
Модуль для окна просмотра и редактирования данных КРД
✅ УБРАНЫ КНОПКИ СОХРАНЕНИЯ/ЗАКРЫТИЯ
✅ АВТОСОХРАНЕНИЕ ПРИ ПЕРЕКЛЮЧЕНИИ ВКЛАДОК И ЗАКРЫТИИ ОКНА
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QMessageBox
)
from PyQt6.QtGui import QCloseEvent
import traceback

# Импорт всех вкладок
from social_data_tab import SocialDataTab
from addresses_tab import AddressesTab
from incoming_orders_tab import IncomingOrdersTab
from service_places_tab import ServicePlacesTab
from soch_episodes_tab import SochEpisodesTab
from outgoing_requests_tab import OutgoingRequestsTab
from document_generator_tab import DocumentGeneratorTab


class KrdDetailsWindow(QDialog):
    """Окно просмотра и редактирования данных КРД"""
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.previous_tab_index = -1  # Для отслеживания предыдущей вкладки
        
        self.setWindowTitle(f"Карточка розыска №{krd_id}")
        self.setModal(True)
        self.resize(1000, 700)
        self.init_ui()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        # Добавляем вкладки (убраны кнопки внизу)
        self.tabs.addTab(SocialDataTab(self.krd_id, self.db, self.audit_logger), "👤 Социально-демографические данные")
        self.tabs.addTab(AddressesTab(self.krd_id, self.db, self.audit_logger), "🏠 Адреса проживания")
        self.tabs.addTab(IncomingOrdersTab(self.krd_id, self.db, self.audit_logger), "📬 Входящие поручения")
        self.tabs.addTab(ServicePlacesTab(self.krd_id, self.db, self.audit_logger), "🎖️ Места службы")
        self.tabs.addTab(SochEpisodesTab(self.krd_id, self.db, self.audit_logger), "⚠️ Сведения о СОЧ")
        self.tabs.addTab(OutgoingRequestsTab(self.krd_id, self.db, self.audit_logger), "📤 Запросы и поручения")
        self.tabs.addTab(DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger), "📄 Генератор документов")
        
        # Отслеживаем переключение вкладок
        self.tabs.currentChanged.connect(self._on_tab_switched)
        
        main_layout.addWidget(self.tabs)
    
    def _on_tab_switched(self, new_index):
        """Автосохранение предыдущей вкладки при переключении"""
        if self.previous_tab_index != -1 and self.previous_tab_index != new_index:
            prev_widget = self.tabs.widget(self.previous_tab_index)
            self._save_widget_silent(prev_widget)
        self.previous_tab_index = new_index
    
    def closeEvent(self, event: QCloseEvent):
        """Сохранение текущей вкладки перед закрытием окна"""
        current_widget = self.tabs.currentWidget()
        self._save_widget_silent(current_widget)
        event.accept()
    
    def _save_widget_silent(self, widget):
        """Тихое сохранение данных виджета (без вывода сообщений об успехе)"""
        if hasattr(widget, 'save_data'):
            try:
                widget.save_data()
                # Логирование можно добавить сюда при необходимости
            except ValueError as e:
                # Ошибки валидации не блокируют переключение вкладок
                pass
            except Exception as e:
                traceback.print_exc()