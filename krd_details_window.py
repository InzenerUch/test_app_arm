"""
Модуль для окна просмотра и редактирования данных КРД
✅ РЕАЛИЗОВАНО: PostgreSQL Advisory Locks (Уровень 3)
✅ АВТОСБРОС: Блокировка снимается мгновенно при разрыве соединения/крахе
✅ БЕЗОПАСНО: Используются именованные параметры (:krd_id) для обхода бага QPSQL
✅ ДОБАВЛЕНО: Управление статусом КРД с возможностью редактирования справочника
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QMessageBox, 
    QComboBox, QPushButton, QLabel, QWidget
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
        
        # ✅ 1. Пытаемся установить Advisory Lock ПЕРЕД созданием интерфейса
        lock_success, lock_message = self.try_acquire_lock()
        
        if not lock_success:
            QMessageBox.warning(self, "Доступ запрещен", lock_message)
            self.reject() # Закрываем окно, не создавая интерфейс
            return

        self.setWindowTitle(f"Карточка розыска №{krd_id} — [Редактирование]")
        self.setModal(True) 
        self.resize(1100, 750)

        # Если блокировка успешна — инициализируем интерфейс
        self.init_ui()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === ВЕРХНЯЯ ПАНЕЛЬ (HEADER) ===
        header_widget = QWidget()
        header_widget.setProperty("role", "header") # Для стилизации
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Заголовок с номером КРД
        title_label = QLabel(f"📋 <b>Карточка розыска №{self.krd_id}</b>")
        title_label.setStyleSheet("font-size: 16px; margin-right: 20px;")
        header_layout.addWidget(title_label)
        
        header_layout.addWidget(QLabel("📌 Статус:"))
        
        # === ВЫБОР СТАТУСА ===
        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(200)
        self.status_combo.currentIndexChanged.connect(self.on_status_changed)
        header_layout.addWidget(self.status_combo)
        
        # Кнопка настройки справочника статусов (Шестеренка)
        self.btn_edit_statuses = QPushButton("⚙️")
        self.btn_edit_statuses.setToolTip("Настроить справочник статусов")
        self.btn_edit_statuses.setProperty("role","edit")
        self.btn_edit_statuses.setFixedSize(30, 30)
        self.btn_edit_statuses.clicked.connect(self.open_status_editor)
        header_layout.addWidget(self.btn_edit_statuses)
        
        header_layout.addStretch()
        
        # Загрузка статусов в комбобокс
        self.load_statuses()
        
        main_layout.addWidget(header_widget)

        # === ВКЛАДКИ ===
        self.tabs = QTabWidget()
        
        # 🔧 СОХРАНЯЕМ ССЫЛКИ НА ВКЛАДКИ В АТРИБУТАХ КЛАССА
        self.social_data_tab = SocialDataTab(self.krd_id, self.db, self.audit_logger)
        self.addresses_tab = AddressesTab(self.krd_id, self.db, self.audit_logger)
        self.incoming_orders_tab = IncomingOrdersTab(self.krd_id, self.db, self.audit_logger)
        self.service_places_tab = ServicePlacesTab(self.krd_id, self.db, self.audit_logger)
        self.soch_episodes_tab = SochEpisodesTab(self.krd_id, self.db, self.audit_logger)
        self.outgoing_requests_tab = OutgoingRequestsTab(self.krd_id, self.db, self.audit_logger)
        self.doc_generator_tab = DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger)
        
        # Добавляем вкладки
        self.tabs.addTab(self.social_data_tab, "👤 Социально-демографические данные")
        self.tabs.addTab(self.addresses_tab, "🏠 Адреса проживания")
        self.tabs.addTab(self.incoming_orders_tab, "📬 Входящие поручения")
        self.tabs.addTab(self.service_places_tab, "🎖️ Места службы")
        self.tabs.addTab(self.soch_episodes_tab, "⚠️ Сведения о СОЧ")
        self.tabs.addTab(self.outgoing_requests_tab, "📤 Запросы и поручения")
        self.tabs.addTab(self.doc_generator_tab, "📄 Генерация документов")
        
        # 🔥 ПОДКЛЮЧАЕМ СИГНАЛЫ АВТООБНОВЛЕНИЯ СПИСКОВ ВЫБОРА
        self.addresses_tab.data_changed.connect(self.doc_generator_tab.load_related_records)
        self.service_places_tab.data_changed.connect(self.doc_generator_tab.load_related_records)
        self.soch_episodes_tab.data_changed.connect(self.doc_generator_tab.load_related_records)
        self.incoming_orders_tab.data_changed.connect(self.doc_generator_tab.load_related_records)
        
        self.tabs.currentChanged.connect(self._on_tab_switched)
        main_layout.addWidget(self.tabs)

    # =========================================================================
    # === ЛОГИКА СТАТУСОВ ===
    # =========================================================================

    def load_statuses(self):
        """Загрузка статусов в комбобокс и выбор текущего"""
        self.status_combo.blockSignals(True) # Блокируем сигналы во время загрузки
        self.status_combo.clear()
        
        q = QSqlQuery(self.db)
        # Загружаем все статусы
        q.exec("SELECT id, name FROM krd.statuses ORDER BY id")
        
        current_status_id = self.get_current_status_id()
        found_current = False
        
        while q.next():
            sid = q.value(0)
            sname = q.value(1)
            self.status_combo.addItem(sname, sid)
            
            # Если это текущий статус записи - запоминаем индекс
            if sid == current_status_id:
                found_current = True
                # Устанавливаем индекс после цикла, чтобы не сбивать выбор
        
        # Устанавливаем выбор
        if found_current:
            idx = self.status_combo.findData(current_status_id)
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
        
        self.status_combo.blockSignals(False) # Разблокируем сигналы

    def get_current_status_id(self):
        """Получает текущий статус из БД для этой КРД"""
        if not self.krd_id: return 1
        q = QSqlQuery(self.db)
        q.prepare("SELECT status_id FROM krd.krd WHERE id = :id")
        q.bindValue(":id", self.krd_id)
        
        if q.exec() and q.next():
            return q.value(0)
        return 1 # По умолчанию

    def on_status_changed(self, index):
        """Обработчик изменения статуса в ComboBox"""
        new_status_id = self.status_combo.currentData()
        if new_status_id is not None:
            self.save_status_to_db(new_status_id)

    def save_status_to_db(self, new_status_id):
        """Сохраняет новый статус в базу данных"""
        try:
            q = QSqlQuery(self.db)
            q.prepare("UPDATE krd.krd SET status_id = :sid WHERE id = :id")
            q.bindValue(":sid", new_status_id)
            q.bindValue(":id", self.krd_id)
            
            if q.exec():
                print(f"✅ Статус КРД-{self.krd_id} изменен на ID={new_status_id}")
                # Здесь можно добавить логирование в audit_logger
            else:
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить статус:\n{q.lastError().text()}")
                # Если ошибка, возвращаем статус обратно (опционально)
                self.load_statuses()
        except Exception as e:
            print(f"❌ Ошибка сохранения статуса: {e}")

    def open_status_editor(self):
        """Открывает редактор справочника статусов с автообновлением"""
        try:
            from reference_editor_dialog import ReferenceEditorDialog
            
            # Открываем редактор для таблицы 'statuses'
            dlg = ReferenceEditorDialog(self.db, self, initial_table='statuses')
            
            # ✅ МАГИЯ АВТООБНОВЛЕНИЯ:
            # Подключаем сигнал data_changed (издается при добавлении/удалении/редактировании)
            # к нашему методу load_statuses
            dlg.data_changed.connect(self.load_statuses)
            
            dlg.exec()
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть редактор:\n{str(e)}")

    # =========================================================================
    # === ЛОГИКА БЛОКИРОВОК И ЗАКРЫТИЯ ===
    # =========================================================================

    def try_acquire_lock(self):
        """
        Захватывает Advisory Lock через встроенные функции PostgreSQL.
        Возвращает (True, "") если успешно, или (False, "Причина отказа").
        """
        try:
            query = QSqlQuery(self.db)
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
        """Снимает Advisory Lock."""
        try:
            print(f"🔓 [Lock] Попытка снять блокировку для КРД-{self.krd_id}...")
            query = QSqlQuery(self.db)
            query.prepare("SELECT pg_advisory_unlock(:krd_id)")
            query.bindValue(":krd_id", int(self.krd_id))
            
            if query.exec():
                print(f"✅ [Lock] Блокировка на КРД-{self.krd_id} успешно снята.")
            else:
                print(f"⚠️ [Lock] Ошибка SQL при снятии блокировки: {query.lastError().text()}")
        except Exception as e:
            print(f"⚠️ [Lock] Исключение при снятии блокировки: {e}")

    def closeEvent(self, event: QCloseEvent):
        """Обработка закрытия окна."""
        # 1. Сохранение и снятие блокировки
        if hasattr(self, 'tabs') and self.tabs is not None:
            current_widget = self.tabs.currentWidget()
            if current_widget:
                self._save_widget_silent(current_widget)
        
        self.release_lock()

        # 2. ИСПУСКАЕМ СИГНАЛ
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
        """Тихое сохранение данных виджета"""
        if hasattr(widget, 'save_data'):
            try:
                widget.save_data()
            except ValueError as e:
                pass 
            except Exception as e:
                print(f"⚠️ Ошибка автосохранения вкладки {widget.__class__.__name__}: {e}")