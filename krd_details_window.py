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
from ui_helpers import is_reader, apply_readonly_mode

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
        header_widget.setProperty("role", "header")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel(f"📋 <b>Карточка розыска №{self.krd_id}</b>")
        title_label.setStyleSheet("font-size: 16px; margin-right: 20px;")
        header_layout.addWidget(title_label)
        header_layout.addWidget(QLabel("📌 Статус:"))
        
        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(200)
        self.status_combo.currentIndexChanged.connect(self.on_status_changed)
        header_layout.addWidget(self.status_combo)
        
        self.btn_edit_statuses = QPushButton("⚙️")
        self.btn_edit_statuses.setToolTip("Настроить справочник статусов")
        self.btn_edit_statuses.setProperty("role","edit")
        self.btn_edit_statuses.setFixedSize(30, 30)
        self.btn_edit_statuses.clicked.connect(self.open_status_editor)
        header_layout.addWidget(self.btn_edit_statuses)
        header_layout.addStretch()
        
        self.load_statuses()
        main_layout.addWidget(header_widget)

        # === ВКЛАДКИ ===
        self.tabs = QTabWidget()
        
        # 🔧 СОХРАНЯЕМ ССЫЛКИ НА ОСНОВНЫЕ ВКЛАДКИ (доступны всем)
        self.social_data_tab = SocialDataTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.addresses_tab = AddressesTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.incoming_orders_tab = IncomingOrdersTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.service_places_tab = ServicePlacesTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.soch_episodes_tab = SochEpisodesTab(self.krd_id, self.db, self.audit_logger, self.user_info)

        # Добавляем базовые вкладки
        self.tabs.addTab(self.social_data_tab, "👤 Социально-демографические данные")
        self.tabs.addTab(self.addresses_tab, "🏠 Адреса проживания")
        self.tabs.addTab(self.incoming_orders_tab, "📬 Входящие поручения")
        self.tabs.addTab(self.service_places_tab, "🎖️ Места службы")
        self.tabs.addTab(self.soch_episodes_tab, "⚠️ Сведения о СОЧ")
        
        # ✅ СКРЫВАЕМ ВКЛАДКУ ЗАПРОСОВ ДЛЯ РОЛИ 'READER'
        if not is_reader(self.user_info):
            self.outgoing_requests_tab = OutgoingRequestsTab(self.krd_id, self.db, self.audit_logger, self.user_info)
            self.tabs.addTab(self.outgoing_requests_tab, "📤 Запросы и поручения")
            
            # ✅ ПОДКЛЮЧЕНИЕ СИГНАЛОВ (только для операторов/админов)
            if hasattr(self.outgoing_requests_tab, 'generator_tab') and self.outgoing_requests_tab.generator_tab is not None:
                self.addresses_tab.data_changed.connect(self.outgoing_requests_tab.generator_tab.load_related_records)
                self.service_places_tab.data_changed.connect(self.outgoing_requests_tab.generator_tab.load_related_records)
                self.soch_episodes_tab.data_changed.connect(self.outgoing_requests_tab.generator_tab.load_related_records)
                self.incoming_orders_tab.data_changed.connect(self.outgoing_requests_tab.generator_tab.load_related_records)
        else:
            # Для читателя вкладка не создаётся, чтобы исключить лишнюю нагрузку и доступ к генератору
            self.outgoing_requests_tab = None
            print("👁️ [READ-ONLY] Вкладка '📤 Запросы и поручения' скрыта для роли 'reader'.")
            
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

    # В файл: krd_details_window.py
# Заменить метод: try_acquire_lock

    def try_acquire_lock(self):
        """
        Захватывает Advisory Lock через встроенные функции PostgreSQL.
        Возвращает (True, "") если успешно, или (False, "Причина отказа").
        📖 Пользователи с ролью 'reader' пропускают блокировку (только просмотр).
        """
        # 📖 Проверяем роль: если читатель — блокировка не нужна
        from ui_helpers import is_reader
        if is_reader(self.user_info):
            print(f"📖 [LOCK] Роль 'reader'. Advisory Lock пропускается (режим просмотра).")
            self.setWindowTitle(f"Карточка №{self.krd_id} — [Просмотр]")
            return True, ""

        try:
            print(f"\n{'='*70}")
            print(f"🔒 [LOCK] Попытка захвата блокировки для КРД-{self.krd_id}")
            print(f"{'='*70}")
            
            # 🔍 Диагностика: Проверяем текущее состояние блокировок
            check_query = QSqlQuery(self.db)
            check_query.prepare("""
                SELECT 
                    pl.locktype,
                    pl.granted,
                    lk.usename,
                    lk.application_name,
                    lk.state
                FROM pg_locks pl
                LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid
                WHERE pl.locktype = 'advisory'
                AND pl.objid = :krd_id
            """)
            check_query.bindValue(":krd_id", int(self.krd_id))
            
            print(f"🔍 [LOCK] Проверка существующих блокировок...")
            if check_query.exec():
                existing_locks = 0
                while check_query.next():
                    existing_locks += 1
                    print(f"   ⚠️ Найдена блокировка:")
                    print(f"      - Тип: {check_query.value(0)}")
                    print(f"      - Granted: {check_query.value(1)}")
                    print(f"      - User: {check_query.value(2)}")
                    print(f"      - App: {check_query.value(3)}")
                    print(f"      - State: {check_query.value(4)}")
                
                if existing_locks == 0:
                    print(f"   ✅ Существующих блокировок не найдено")
            else:
                print(f"   ⚠️ Ошибка проверки: {check_query.lastError().text()}")
            
            # Пытаемся захватить блокировку
            query = QSqlQuery(self.db)
            query.prepare("SELECT pg_try_advisory_lock(:krd_id)")
            query.bindValue(":krd_id", int(self.krd_id))
            
            print(f"🔐 [LOCK] Выполняем pg_try_advisory_lock({self.krd_id})...")
            
            if not query.exec():
                error_msg = f"Ошибка БД: {query.lastError().text()}"
                print(f"❌ [LOCK] {error_msg}")
                return False, error_msg
                
            if query.next():
                is_locked = query.value(0)
                if is_locked:
                    print(f"✅ [LOCK] Блокировка УСПЕШНО захвачена!")
                    print(f"{'='*70}\n")
                    return True, ""
                else:
                    print(f"❌ [LOCK] Не удалось захватить блокировку - запись занята")
                    print(f"{'='*70}\n")
                    return False, (
                        f"Запись №{self.krd_id} сейчас открыта в другой сессии или окне.\n"
                        f"Закройте её в другом приложении или дождитесь освобождения."
                    )
            
            print(f"❌ [LOCK] Не получен результат от pg_try_advisory_lock")
            print(f"{'='*70}\n")
            return False, "Не удалось проверить статус блокировки"
            
        except Exception as e:
            print(f"❌ [LOCK] Исключение при захвате блокировки: {str(e)}")
            print(f"{'='*70}\n")
            return False, f"Исключение при блокировке: {str(e)}"

    def release_lock(self):
            """Снимает Advisory Lock с полной диагностикой."""
            try:
                print(f"\n{'='*70}")
                print(f"🔓 [LOCK] Попытка снять блокировку для КРД-{self.krd_id}")
                print(f"{'='*70}")
                
                # 🔍 Шаг 1: Проверяем, есть ли у нас блокировка
                print(f"🔍 [LOCK] Шаг 1: Проверка наличия блокировки...")
                check_query = QSqlQuery(self.db)
                check_query.prepare("""
                    SELECT 
                        pl.objid,
                        lk.usename,
                        lk.application_name
                    FROM pg_locks pl
                    LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid
                    WHERE pl.locktype = 'advisory'
                    AND pl.objid = :krd_id
                    AND pl.granted = true
                """)
                check_query.bindValue(":krd_id", int(self.krd_id))
                
                has_lock = False
                if check_query.exec():
                    while check_query.next():
                        has_lock = True
                        print(f"   ✅ Найдена активная блокировка:")
                        print(f"      - KRD ID: {check_query.value(0)}")
                        print(f"      - User: {check_query.value(1)}")
                        print(f"      - App: {check_query.value(2)}")
                else:
                    print(f"   ⚠️ Ошибка проверки: {check_query.lastError().text()}")
                
                if not has_lock:
                    print(f"ℹ️ [LOCK] Активная блокировка не найдена (уже снята?)")
                    print(f"{'='*70}\n")
                    return
                
                # 🔍 Шаг 2: Проверяем текущее соединение
                print(f"🔍 [LOCK] Шаг 2: Проверка соединения...")
                if not self.db.isOpen():
                    print(f"   ⚠️ Соединение с БД закрыто!")
                else:
                    print(f"   ✅ Соединение активно")
                
                # 🔍 Шаг 3: Пытаемся снять блокировку
                print(f"🔍 [LOCK] Шаг 3: Выполняем pg_advisory_unlock({self.krd_id})...")
                query = QSqlQuery(self.db)
                query.prepare("SELECT pg_advisory_unlock(:krd_id)")
                query.bindValue(":krd_id", int(self.krd_id))
                
                if query.exec():
                    if query.next():
                        unlocked = query.value(0)
                        if unlocked:
                            print(f"✅ [LOCK] Блокировка УСПЕШНО снята!")
                        else:
                            print(f"⚠️ [LOCK] pg_advisory_unlock вернул False (блокировка не принадлежала этой сессии)")
                    else:
                        print(f"⚠️ [LOCK] Не получен результат от pg_advisory_unlock")
                else:
                    print(f"❌ [LOCK] Ошибка SQL: {query.lastError().text()}")
                    print(f"   Driver Error: {query.lastError().driverText()}")
                    print(f"   Database Error: {query.lastError().databaseText()}")
                
                # 🔍 Шаг 4: Финальная проверка
                print(f"🔍 [LOCK] Шаг 4: Финальная проверка блокировок...")
                final_check = QSqlQuery(self.db)
                final_check.prepare("""
                    SELECT COUNT(*)
                    FROM pg_locks
                    WHERE locktype = 'advisory'
                    AND objid = :krd_id
                    AND granted = true
                """)
                final_check.bindValue(":krd_id", int(self.krd_id))
                
                if final_check.exec() and final_check.next():
                    remaining = final_check.value(0)
                    if remaining == 0:
                        print(f"   ✅ Блокировок не осталось")
                    else:
                        print(f"   ⚠️ Осталось блокировок: {remaining}")
                else:
                    print(f"   ⚠️ Ошибка финальной проверки")
                
                print(f"{'='*70}\n")
                
            except Exception as e:
                print(f"❌ [LOCK] Исключение при снятии блокировки: {e}")
                import traceback
                traceback.print_exc()
                print(f"{'='*70}\n")

    def closeEvent(self, event: QCloseEvent):
            """
            Обработка закрытия окна.
            Испускает сигнал перед закрытием, чтобы MainWindow мог перехватить управление.
            """
            print(f"\n{'='*70}")
            print(f"🚪 [WINDOW] Закрытие окна КРД-{self.krd_id}")
            print(f"{'='*70}")
            
            # 1. Сохранение и снятие блокировки
            if hasattr(self, 'tabs') and self.tabs is not None:
                current_widget = self.tabs.currentWidget()
                if current_widget:
                    print(f"💾 [WINDOW] Автосохранение текущей вкладки...")
                    self._save_widget_silent(current_widget)
            
            # 2. Снимаем блокировку
            print(f"🔓 [WINDOW] Вызов release_lock()...")
            self.release_lock()
            
            # 3. ИСПУСКАЕМ СИГНАЛ
            print(f"📡 [WINDOW] Испускаю сигнал krd_window_closed...")
            self.krd_window_closed.emit()
            
            # 4. Принимаем событие закрытия
            print(f"✅ [WINDOW] Окно закрыто")
            print(f"{'='*70}\n")
            
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