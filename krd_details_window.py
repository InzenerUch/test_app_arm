"""
Модуль для окна просмотра и редактирования данных КРД
✅ РЕАЛИЗОВАНО: PostgreSQL Advisory Locks (Уровень 3)
✅ АВТОСБРОС: Блокировка снимается мгновенно при разрыве соединения/крахе
✅ БЕЗОПАСНО: Используются именованные параметры (:krd_id) для обхода бага QPSQL
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QMessageBox
)
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtCore import pyqtSignal
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
    """Окно просмотра и редактирования данных КРД с Advisory Locks"""
    krd_window_closed = pyqtSignal()

    def __init__(self, krd_id, db_connection, user_info, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.user_info = user_info
        self.audit_logger = audit_logger
        
        self.current_user_id = user_info.get('id')
        self.current_username = user_info.get('username', 'Неизвестный')
        self.previous_tab_index = -1
        
        self.setWindowTitle(f"Карточка розыска №{krd_id}")
        self.setModal(True) # Не модальное, чтобы можно было переключаться между окнами (если разрешено)
        self.resize(1100, 750)

        # ✅ 1. Пытаемся установить Advisory Lock ПЕРЕД созданием интерфейса
        lock_success, lock_message = self.try_acquire_lock()
        
        if not lock_success:
            QMessageBox.warning(self, "Доступ запрещен", lock_message)
            self.reject() # Закрываем окно, не создавая интерфейс
            return

        # Если блокировка успешна — инициализируем интерфейс
        self.init_ui()
        self.setWindowTitle(f"Карточка розыска №{krd_id} — [Редактирование]")

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        self.tabs.addTab(SocialDataTab(self.krd_id, self.db, self.audit_logger), "👤 Социально-демографические данные")
        self.tabs.addTab(AddressesTab(self.krd_id, self.db, self.audit_logger), "🏠 Адреса проживания")
        self.tabs.addTab(IncomingOrdersTab(self.krd_id, self.db, self.audit_logger), "📬 Входящие поручения")
        self.tabs.addTab(ServicePlacesTab(self.krd_id, self.db, self.audit_logger), "🎖️ Места службы")
        self.tabs.addTab(SochEpisodesTab(self.krd_id, self.db, self.audit_logger), "⚠️ Сведения о СОЧ")
        self.tabs.addTab(OutgoingRequestsTab(self.krd_id, self.db, self.audit_logger), "📤 Запросы и поручения")
        self.tabs.addTab(DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger), "📄 Генерация документов")
        
        self.tabs.currentChanged.connect(self._on_tab_switched)
        main_layout.addWidget(self.tabs)

    def try_acquire_lock(self):
        """
        Захватывает Advisory Lock через встроенные функции PostgreSQL.
        Возвращает (True, "") если успешно, или (False, "Причина отказа").
        """
        try:
            query = QSqlQuery(self.db)
            # pg_try_advisory_lock возвращает TRUE, если блокировка захвачена, и FALSE, если уже занята
            query.prepare("SELECT pg_try_advisory_lock(:krd_id)")
            query.bindValue(":krd_id", int(self.krd_id))
            
            if not query.exec():
                return False, f"Ошибка БД: {query.lastError().text()}"
                
            if query.next():
                is_locked = query.value(0)
                if is_locked:
                    return True, ""
                else:
                    return False, (
                        f"Запись №{self.krd_id} сейчас открыта в другой сессии или окне.\n"
                        f"Закройте её в другом приложении или дождитесь освобождения."
                    )
            return False, "Не удалось проверить статус блокировки."
        except Exception as e:
            return False, f"Исключение при блокировке: {str(e)}"

    def release_lock(self):
        """Снимает Advisory Lock. Безопасно: если блокировки нет, PostgreSQL просто проигнорирует."""
        try:
            print(f"🔓 [Lock] Попытка снять блокировку для КРД-{self.krd_id}...")
            query = QSqlQuery(self.db)
            # Используем prepare для стабильности
            query.prepare("SELECT pg_advisory_unlock(:krd_id)")
            query.bindValue(":krd_id", int(self.krd_id))
            
            if query.exec():
                print(f"✅ [Lock] Блокировка на КРД-{self.krd_id} успешно снята.")
            else:
                print(f"⚠️ [Lock] Ошибка SQL при снятии блокировки: {query.lastError().text()}")
        except Exception as e:
            print(f"⚠️ [Lock] Исключение при снятии блокировки: {e}")

    def closeEvent(self, event: QCloseEvent):
        """
        Обработка закрытия окна.
        Испускает сигнал перед закрытием, чтобы MainWindow мог перехватить управление.
        """
        # 1. Сохранение и снятие блокировки
        if hasattr(self, 'tabs') and self.tabs is not None:
            current_widget = self.tabs.currentWidget()
            if current_widget:
                self._save_widget_silent(current_widget)
        
        self.release_lock()
        print(f"🔓 [Lock] Блокировка на КРД-{self.krd_id} снята.")

        # 2. ИСПУСКАЕМ СИГНАЛ
        print("📡 [Signal] Испускаю krd_window_closed...")
        self.krd_window_closed.emit()
        
        # 3. Принимаем событие закрытия
        event.accept()

    def _on_tab_switched(self, new_index):
        """Автосохранение предыдущей вкладки при переключении"""
        if self.previous_tab_index != -1 and self.previous_tab_index != new_index:
            prev_widget = self.tabs.widget(self.previous_tab_index)
            if prev_widget:
                self._save_widget_silent(prev_widget)
            self.previous_tab_index = new_index

    def _save_widget_silent(self, widget):
        """Тихое сохранение данных виджета (без вывода сообщений об успехе)"""
        if hasattr(widget, 'save_data'):
            try:
                widget.save_data()
            except ValueError as e:
                pass # Ошибки валидации не блокируют закрытие
            except Exception as e:
                print(f"⚠️ Ошибка автосохранения вкладки {widget.__class__.__name__}: {e}")
                traceback.print_exc()