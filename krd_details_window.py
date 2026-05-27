"""
Модуль для окна просмотра и редактирования данных КРД
✅ ИСПРАВЛЕНО: Проблема фокуса в Ubuntu/Linux (Z-order fighting)
✅ ДОБАВЛЕНО: WindowStaysOnTopHint для окна предпросмотра
✅ БЕЗОПАСНО: Используются именованные параметры (:krd_id)
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QMessageBox,
    QComboBox, QPushButton, QLabel, QWidget, QHeaderView, QAbstractItemView
)
from PyQt6.QtGui import QCloseEvent, QStandardItemModel, QStandardItem
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
import traceback
import json
from ui_helpers import is_reader, apply_readonly_mode
# Импорт всех вкладок и менеджеров
from social_data_tab import SocialDataTab
from addresses_tab import AddressesTab
from incoming_orders_tab import IncomingOrdersTab
from service_places_tab import ServicePlacesTab
from soch_episodes_tab import SochEpisodesTab
from outgoing_requests_tab import OutgoingRequestsTab
from krd_version_manager import KrdVersionManager
from krd_version_history_dialog import KrdVersionHistoryDialog
from krd_version_preview_window import KrdVersionPreviewWindow

class KrdDetailsWindow(QDialog):
    """Окно просмотра и редактирования данных КРД с Advisory Locks и версионированием"""
    krd_window_closed = pyqtSignal()

    def __init__(self, krd_id, db_connection, user_info, audit_logger=None, preview_version_id=None):
        # ✅ ВАЖНО: super() вызывается БЕЗ родителя (None), чтобы окно стало независимым
        super().__init__(None)
        
        self.krd_id = krd_id
        self.db = db_connection
        self.user_info = user_info
        self.audit_logger = audit_logger
        self.current_user_id = user_info.get('id')
        self.current_username = user_info.get('username', 'Неизвестный')
        self.previous_tab_index = -1
        self.version_mgr = KrdVersionManager(db_connection)
        self._tabs_list = []
        
        # Параметры режима предпросмотра версии
        self.preview_version_id = preview_version_id
        self.preview_mode = preview_version_id is not None
        self.preview_banner = None
        self._preview_window = None  # Ссылка для удержания окна от GC

        # === ЛОГИКА НАСТРОЙКИ ОКНА ===
        if self.preview_mode:
            self.setWindowTitle(f"Карточка розыска №{krd_id} — [Просмотр версии #{preview_version_id}]")
            
            # ✅ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ДЛЯ UBUNTU:
            # 1. Убираем флаг Dialog
            # 2. Делаем окно полноценным Window
            # 3. Добавляем WindowStaysOnTopHint, чтобы оно не перекрывалось модальным окном редактора
            self.setWindowFlags(
                Qt.WindowType.Window |
                Qt.WindowType.WindowStaysOnTopHint | 
                Qt.WindowType.WindowCloseButtonHint |
                Qt.WindowType.WindowMinimizeButtonHint |
                Qt.WindowType.WindowMaximizeButtonHint
            )
            
            self.setWindowModality(Qt.WindowModality.NonModal)
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        else:
            # Обычный режим: Модальное окно с блокировкой
            lock_success, lock_message = self.try_acquire_lock()
            if not lock_success:
                QMessageBox.warning(self, "Доступ запрещен", lock_message)
                self.reject()
                return
            self.setWindowTitle(f"Карточка розыска №{krd_id} — [Редактирование]")
            self.setModal(True)
            
        self.resize(1100, 750)
        self.init_ui()
        
        # Загрузка снапшота строго после отрисовки
        if self.preview_mode:
            QTimer.singleShot(20, self._load_version_snapshot)

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
        # Кнопка версий
        self.btn_versions = QPushButton("📜 Версии")
        self.btn_versions.setProperty("role", "info")
        self.btn_versions.clicked.connect(self.open_versions_dialog)
        header_layout.addWidget(self.btn_versions)
        header_layout.addStretch()
        self.load_statuses()
        main_layout.addWidget(header_widget)
        # === БАННЕР ПРЕДПРОСМОТРА ===
        self.preview_banner = QLabel("👁️ РЕЖИМ ПРЕДПРОСМОТРА: данные только для чтения.")
        self.preview_banner.setStyleSheet("background-color: #fff3cd; color: #856404; padding: 10px; font-weight: bold; border-radius: 0px; text-align: center;")
        self.preview_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_banner.hide()
        main_layout.addWidget(self.preview_banner)
        # === ВКЛАДКИ ===
        self.tabs = QTabWidget()
        self.social_data_tab = SocialDataTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.addresses_tab = AddressesTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.incoming_orders_tab = IncomingOrdersTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.service_places_tab = ServicePlacesTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.soch_episodes_tab = SochEpisodesTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self._tabs_list = [
            self.social_data_tab, self.addresses_tab, self.incoming_orders_tab,
            self.service_places_tab, self.soch_episodes_tab
        ]
        self.tabs.addTab(self.social_data_tab, "👤 Социально-демографические данные")
        self.tabs.addTab(self.addresses_tab, "🏠 Адреса проживания")
        self.tabs.addTab(self.incoming_orders_tab, "📬 Входящие поручения")
        self.tabs.addTab(self.service_places_tab, "🎖️ Места службы")
        self.tabs.addTab(self.soch_episodes_tab, "⚠️ Сведения о СОЧ")
        if not is_reader(self.user_info):
            self.outgoing_requests_tab = OutgoingRequestsTab(self.krd_id, self.db, self.audit_logger, self.user_info)
            self.tabs.addTab(self.outgoing_requests_tab, "📤 Запросы и поручения")
            self._tabs_list.append(self.outgoing_requests_tab)
            if hasattr(self.outgoing_requests_tab, 'generator_tab') and self.outgoing_requests_tab.generator_tab is not None:
                self.addresses_tab.data_changed.connect(self.outgoing_requests_tab.generator_tab.load_related_records)
                self.service_places_tab.data_changed.connect(self.outgoing_requests_tab.generator_tab.load_related_records)
                self.soch_episodes_tab.data_changed.connect(self.outgoing_requests_tab.generator_tab.load_related_records)
                self.incoming_orders_tab.data_changed.connect(self.outgoing_requests_tab.generator_tab.load_related_records)
        else:
            self.outgoing_requests_tab = None
        self.tabs.currentChanged.connect(self._on_tab_switched)
        main_layout.addWidget(self.tabs)

    # =========================================================================
    # === ЛОГИКА СТАТУСОВ ===
    # =========================================================================
    def load_statuses(self):
        self.status_combo.blockSignals(True)
        self.status_combo.clear()
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.statuses ORDER BY id")
        current_status_id = self.get_current_status_id()
        found_current = False
        while q.next():
            sid, sname = q.value(0), q.value(1)
            self.status_combo.addItem(sname, sid)
            if sid == current_status_id: found_current = True
        if found_current:
            idx = self.status_combo.findData(current_status_id)
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
        self.status_combo.blockSignals(False)

    def get_current_status_id(self):
        if not self.krd_id: return 1
        q = QSqlQuery(self.db)
        q.prepare("SELECT status_id FROM krd.krd WHERE id = :id")
        q.bindValue(":id", self.krd_id)
        if q.exec() and q.next(): return q.value(0)
        return 1

    def on_status_changed(self, index):
        if self.preview_mode: return
        new_status_id = self.status_combo.currentData()
        if new_status_id is not None:
            self.save_status_to_db(new_status_id)

    def save_status_to_db(self, new_status_id):
        try:
            q = QSqlQuery(self.db)
            q.prepare("UPDATE krd.krd SET status_id = :sid WHERE id = :id")
            q.bindValue(":sid", new_status_id)
            q.bindValue(":id", self.krd_id)
            if not q.exec():
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить статус:\n{q.lastError().text()}")
                self.load_statuses()
        except Exception as e:
            print(f"❌ Ошибка сохранения статуса: {e}")

    def open_status_editor(self):
        try:
            from reference_editor_dialog import ReferenceEditorDialog
            dlg = ReferenceEditorDialog(self.db, self, initial_table='statuses')
            dlg.data_changed.connect(self.load_statuses)
            dlg.exec()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть редактор:\n{str(e)}")

    # =========================================================================
    # === ЛОГИКА БЛОКИРОВОК И ЗАКРЫТИЯ ===
    # =========================================================================
    def try_acquire_lock(self):
        if is_reader(self.user_info):
            self.setWindowTitle(f"Карточка №{self.krd_id} — [Просмотр]")
            return True, ""
        try:
            check_query = QSqlQuery(self.db)
            check_query.prepare("""SELECT pl.locktype, pl.granted, lk.usename FROM pg_locks pl LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid WHERE pl.locktype = 'advisory' AND pl.objid = :krd_id""")
            check_query.bindValue(":krd_id", int(self.krd_id))
            query = QSqlQuery(self.db)
            query.prepare("SELECT pg_try_advisory_lock(:krd_id)")
            query.bindValue(":krd_id", int(self.krd_id))
            if query.exec() and query.next() and query.value(0):
                return True, ""
            return False, f"Запись №{self.krd_id} сейчас открыта в другой сессии."
        except Exception as e:
            return False, f"Исключение при блокировке: {str(e)}"

    def release_lock(self):
        try:
            query = QSqlQuery(self.db)
            query.prepare("SELECT pg_advisory_unlock(:krd_id)")
            query.bindValue(":krd_id", int(self.krd_id))
            query.exec()
        except Exception as e:
            print(f"❌ Ошибка снятия блокировки: {e}")

    def closeEvent(self, event: QCloseEvent):
        if hasattr(self, 'tabs') and self.tabs is not None:
            current_widget = self.tabs.currentWidget()
            if current_widget and not self.preview_mode:
                self._save_widget_silent(current_widget)
        if not self.preview_mode:
            self.release_lock()
        self.krd_window_closed.emit()
        event.accept()

    def _on_tab_switched(self, new_index):
        if self.previous_tab_index != -1 and self.previous_tab_index != new_index:
            prev_widget = self.tabs.widget(self.previous_tab_index)
            if prev_widget and not self.preview_mode:
                self._save_widget_silent(prev_widget)
            self.previous_tab_index = new_index

    def _on_field_changed(self):
        if self.preview_mode: return
        for tab in self._tabs_list:
            if hasattr(tab, '_auto_save_timer') and tab._auto_save_timer:
                tab._auto_save_timer.start(400)

    def _save_widget_silent(self, widget):
        if self.preview_mode: return
        if hasattr(widget, 'save_data'):
            try:
                widget.save_data()
                if self.version_mgr.capture_snapshot(self.krd_id, self.current_user_id, "Автосохранение"):
                    print(f"✅ Снапшот версии сохранен для КРД-{self.krd_id}")
            except ValueError: pass
            except Exception as e:
                print(f"⚠️ Ошибка автосохранения: {e}")

    # =========================================================================
    # === ЛОГИКА ВЕРСИЙ И ПРЕДПРОСМОТРА ===
    # =====================================    
    def open_versions_dialog(self):
        """Открывает диалог истории версий"""
        dlg = KrdVersionHistoryDialog(self.db, self.krd_id, self)
        # Явное подключение сигнала. Убедитесь, что имя метода совпадает!
        dlg.preview_requested.connect(self._open_preview_window)
        dlg.restore_requested.connect(self.restore_version_from_db)
        dlg.exec()
    def _open_preview_window(self, version_id: int):
        print(f"🟡 [DEBUG] _open_preview_window вызван с version_id={version_id}")
        if not version_id: 
            print("❌ version_id is None")
            return
        
        try:
            self._preview_window = KrdVersionPreviewWindow(
                db_connection=self.db,
                krd_id=self.krd_id,
                version_id=version_id,
                user_info=self.user_info,
                audit_logger=self.audit_logger,
                parent=self  # ✅ Явно передаем родительское окно
            )
            self._preview_window.show()
            
            # ✅ Прямая активация без таймеров (работает стабильнее)
            self._preview_window.raise_()
            self._preview_window.activateWindow()
            self._preview_window.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
            
            print("✅ Окно предпросмотра успешно показано и сфокусировано")
        except ImportError as e:
            QMessageBox.critical(self, "Ошибка", f"Не найден файл окна предпросмотра!\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно:\n{e}")
            traceback.print_exc()
    def _load_version_snapshot(self):
        """Загружает снапшот версии и переводит окно в режим предпросмотра"""
        if not self.preview_version_id: return
        q = QSqlQuery(self.db)
        q.prepare("SELECT snapshot_data FROM krd.krd_versions WHERE id = :id")
        q.bindValue(":id", self.preview_version_id)
        if q.exec() and q.next():
            snapshot = json.loads(q.value(0))
            self.preview_banner.show()
            self.preview_banner.setText(f"👁️ РЕЖИМ ПРЕДПРОСМОТРА: Версия #{self.preview_version_id}. Данные доступны только для чтения. Вы можете открыть несколько окон параллельно.")
            for tab in self._tabs_list:
                if hasattr(tab, '_auto_save_timer') and tab._auto_save_timer:
                    tab._auto_save_timer.stop()
            apply_readonly_mode(self, True)
            for btn in self.findChildren(QPushButton):
                if "Закрыть" in btn.text() or "❌" in btn.text():
                    btn.setEnabled(True)
            self._apply_snapshot_to_all_tabs(snapshot)

    def restore_version_from_db(self, version_id: int):
        if self.version_mgr and self.version_mgr.rollback_to(version_id, self.krd_id):
            QMessageBox.information(self, "Успех", f"✅ КРД восстановлена до версии #{version_id}")
            self.load_statuses()
            if hasattr(self, 'social_data_tab') and self.social_data_tab:
                self.social_data_tab.load_data()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось восстановить версию. Проверьте логи.")

    def _apply_snapshot_to_all_tabs(self, snapshot: dict):
        if 'social_data' in snapshot and self.social_data_tab:
            sd = snapshot['social_data']
            tab = self.social_data_tab
            for attr_name, val in sd.items():
                widget_name = f"{attr_name}_input"
                if hasattr(tab, widget_name):
                    widget = getattr(tab, widget_name)
                    if hasattr(widget, 'setText'):
                        widget.setText(str(val) if val is not None else "")
                    elif hasattr(widget, 'setPlainText'):
                        widget.setPlainText(str(val) if val is not None else "")
        tab_mapping = {
            'addresses': (self.addresses_tab, 'addresses_table'),
            'service_places': (self.service_places_tab, 'places_table'),
            'soch_episodes': (self.soch_episodes_tab, 'episodes_table'),
            'incoming_orders': (self.incoming_orders_tab, 'orders_table')
        }
        for key, (tab, table_attr) in tab_mapping.items():
            if key in snapshot and tab is not None:
                table_view = getattr(tab, table_attr, None)
                if table_view:
                    self._setup_readonly_table(table_view, snapshot[key])

    def _setup_readonly_table(self, table_view, data_list):
        if not data_list: return
        model = QStandardItemModel()
        headers = list(data_list[0].keys())
        model.setHorizontalHeaderLabels(headers)
        for row_data in data_list:
            items = [QStandardItem(str(row_data.get(h, ""))) for h in headers]
            model.appendRow(items)
        table_view.setModel(model)
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_view.resizeColumnsToContents()