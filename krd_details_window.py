"""
Модуль для окна просмотра и редактирования данных КРД
С подтверждением сохранения при закрытии
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QTabWidget
)
from PyQt6.QtGui import QFont, QCloseEvent
from PyQt6.QtCore import Qt
import traceback

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
        
        # Флаг наличия несохранённых изменений
        self.has_unsaved_changes = False
        
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
        tabs.addTab(DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger), "Генератор документов")
        
        # Сохраняем ссылку на вкладки для доступа из save_all_changes
        self.tabs = tabs
        
        # Отслеживаем изменения в вкладках
        tabs.currentChanged.connect(self.on_tab_changed)
        
        main_layout.addWidget(tabs)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("💾 Сохранить все изменения")
        save_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px; padding: 10px 20px;")
        save_button.clicked.connect(self.save_all_changes)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("❌ Закрыть")
        cancel_button.setStyleSheet("padding: 10px 20px;")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def on_tab_changed(self, index):
        """Обработчик переключения вкладок"""
        # Можно отслеживать изменения при переключении вкладок
        pass
    
    def mark_as_changed(self):
        """Отметить наличие несохранённых изменений"""
        self.has_unsaved_changes = True
        # Обновляем заголовок окна
        self.setWindowTitle(f"Карточка розыска №{self.krd_id} *")
    
    def mark_as_saved(self):
        """Отметить что изменения сохранены"""
        self.has_unsaved_changes = False
        # Обновляем заголовок окна
        self.setWindowTitle(f"Карточка розыска №{self.krd_id}")
    
    def closeEvent(self, event: QCloseEvent):
        """
        Перехват события закрытия окна
        ❗ СПРАШИВАЕТ о сохранении при наличии изменений
        """
        # Проверяем есть ли несохранённые изменения
        if self.has_unsaved_changes:
            # Создаём диалог подтверждения
            reply = QMessageBox.question(
                self,
                "Подтверждение закрытия",
                "⚠️ Обнаружены несохранённые изменения!\n\n"
                "Вы хотите сохранить изменения перед закрытием?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                # Пользователь выбрал "Сохранить"
                if self.save_all_changes(silent=True):
                    # Сохранение успешно - закрываем окно
                    event.accept()
                else:
                    # Ошибка сохранения - не закрываем окно
                    event.ignore()
                    
            elif reply == QMessageBox.StandardButton.Discard:
                # Пользователь выбрал "Не сохранять" - закрываем без сохранения
                event.accept()
                
            elif reply == QMessageBox.StandardButton.Cancel:
                # Пользователь выбрал "Отмена" - не закрываем окно
                event.ignore()
        else:
            # Нет несохранённых изменений - закрываем без вопросов
            event.accept()
    
    def save_all_changes(self, silent=False):
        """
        Сохранение изменений во всех вкладках
        Args:
            silent: Если True, не показывать сообщения об успехе
        Returns:
            bool: True если сохранение успешно, False если ошибка
        """
        try:
            # Получаем текущую активную вкладку
            current_widget = self.tabs.currentWidget()
            
            if hasattr(current_widget, 'save_data'):
                # Получаем старые и новые данные из вкладки (если поддерживается)
                old_data = {}
                new_data = {}
                
                if hasattr(current_widget, 'get_old_data'):
                    old_data = current_widget.get_old_data()
                if hasattr(current_widget, 'get_new_data'):
                    new_data = current_widget.get_new_data()
                
                # Вызываем сохранение данных в текущей вкладке
                current_widget.save_data()
                
                # Логирование с реальными данными
                if self.audit_logger:
                    self.audit_logger.log_krd_update(
                        self.krd_id, 
                        old_data, 
                        new_data
                    )
                
                # Помечаем как сохранённое
                self.mark_as_saved()
                
                # Показываем сообщение только если не silent режим
                if not silent:
                    QMessageBox.information(
                        self, 
                        "Успех", 
                        "✅ Данные успешно сохранены\n\n"
                        "Вы можете продолжить редактирование или закрыть окно."
                    )
                
                # Обновляем данные в текущей вкладке после сохранения
                if hasattr(current_widget, 'load_data'):
                    current_widget.load_data()
                
                return True
                
            else:
                if not silent:
                    QMessageBox.warning(self, "Ошибка", "⚠️ Текущая вкладка не поддерживает сохранение")
                return False
                
        except ValueError as e:
            # Ошибка валидации - показываем предупреждение
            if not silent:
                QMessageBox.warning(self, "Ошибка валидации", f"⚠️ {str(e)}")
            return False
            
        except Exception as e:
            traceback.print_exc()
            if not silent:
                QMessageBox.critical(self, "Ошибка", f"❌ Ошибка при сохранении данных:\n{str(e)}")
            return False
    
    def reject(self):
        """
        Переопределение метода reject для подтверждения закрытия
        """
        # Используем closeEvent для единообразия
        self.close()