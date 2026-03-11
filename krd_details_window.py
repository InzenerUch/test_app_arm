"""
Модуль для окна просмотра и редактирования данных КРД
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QTabWidget
)
from PyQt6.QtGui import QFont

# Импорт всех вкладок
from social_data_tab import SocialDataTab
from addresses_tab import AddressesTab
from incoming_orders_tab import IncomingOrdersTab
from service_places_tab import ServicePlacesTab
from soch_episodes_tab import SochEpisodesTab
from outgoing_requests_tab import OutgoingRequestsTab
from document_generator_tab import DocumentGeneratorTab

from audit_logger import AuditLogger


class KrdDetailsWindow(QDialog):
    """
    Окно просмотра и редактирования данных КРД
    """
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        
        self.setWindowTitle(f"Карточка розыска №{krd_id}")
        self.setModal(True)
        self.resize(1000, 700)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_layout = QVBoxLayout()
        
        # Создаем вкладки
        tabs = QTabWidget()
        
        # Добавляем все вкладки
        tabs.addTab(SocialDataTab(self.krd_id, self.db, self.audit_logger), "Социально-демографические данные")
        tabs.addTab(AddressesTab(self.krd_id, self.db, self.audit_logger), "Адреса проживания")
        tabs.addTab(IncomingOrdersTab(self.krd_id, self.db, self.audit_logger), "Входящие поручения")
        tabs.addTab(ServicePlacesTab(self.krd_id, self.db, self.audit_logger), "Места службы")
        tabs.addTab(SochEpisodesTab(self.krd_id, self.db, self.audit_logger), "Сведения о СОЧ")
        tabs.addTab(OutgoingRequestsTab(self.krd_id, self.db, self.audit_logger), "Запросы и поручения")
        
        main_layout.addWidget(tabs)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Сохранить все изменения")
        save_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px;")
        save_button.clicked.connect(self.save_all_changes)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def save_all_changes(self):
        """Сохранение изменений во всех вкладках"""
        try:
            # Получаем текущую вкладку
            current_widget = self.findChild(QTabWidget).currentWidget()
            
            # Вызываем метод сохранения у текущей вкладки
            if hasattr(current_widget, 'save_data'):
                current_widget.save_data()
                
                # Логирование
                if self.audit_logger:
                    self.audit_logger.log_krd_update(
                        self.krd_id, 
                        {},  # старые данные можно получить из вкладки
                        {}   # новые данные
                    )
                
                QMessageBox.information(self, "Успех", "Данные успешно сохранены")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Текущая вкладка не поддерживает сохранение")
                
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка валидации", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении данных:\n{str(e)}")