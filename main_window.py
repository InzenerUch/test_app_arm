"""
Модуль для главного окна приложения
Содержит класс MainWindow для отображения данных КРД и информации о пользователе.
С функцией выгрузки данных в Excel, поиском в реальном времени и сортировкой по столбцам.

✅ ИСПРАВЛЕНО: Убран столбец "Номер КРД", ID переименован в "№ КРД"
✅ ИСПРАВЛЕНО: Убран столбец "ID последнего места службы"
✅ ДОБАВЛЕНО: Столбец "Занято пользователем" (определяется через pg_locks)
✅ ДОБАВЛЕНО: Автообновление статуса занятости (QTimer)
✅ ДОБАВЛЕНО: Подпись "🟢 Не занято" для свободных записей
✅ ДОБАВЛЕНО: Подробная диагностика проверки блокировок в консоль
✅ ДОБАВЛЕНО: Отдельное меню "Отчеты" с пунктом "Отчеты по всем КРД"
✅ ДОБАВЛЕНО: Меню "Администрирование" (Пользователи, Удаленные, Аудит)
✅ УДАЛЕНО: Кнопки администрирования с Toolbar
✅ ИСПРАВЛЕНО: Баг с неотображаемым QFileDialog при экспорте (QTimer.singleShot)
"""

import sys
import traceback
from ui_helpers import is_reader, apply_readonly_mode

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QHeaderView, QLabel, QGroupBox, QGridLayout, QMenuBar, 
    QStatusBar, QToolBar, QTableView, QPushButton, QDialog,
    QMessageBox, QMenu, QFileDialog, QAbstractItemView, QProgressDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QPoint, QDate, QTimer
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery
from PyQt6.QtGui import QAction, QFont

# === ИМПОРТЫ ДЛЯ ЭКСПОРТА В EXCEL ===
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell

# === ИМПОРТЫ ПРИЛОЖЕНИЯ ===
from add_krd_window import AddKrdWindow
from audit_logger import AuditLogger
from export_helper import KrdExcelExporter
from report_config_dialog import ReportConfigDialog
from theme_manager import ThemeManager


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self, user_info, db_connection):
        super().__init__()
        self.user_info = user_info
        self.db = db_connection
        
        self.audit_logger = AuditLogger(self.db, self.user_info)
        
        if not hasattr(self, 'theme_manager'):
            self.theme_manager = ThemeManager(db_connection, user_info.get('id'))
        
        self.setWindowTitle("АРМ Сотрудника дознания - Главное окно")
        self.setGeometry(100, 100, 1200, 800)
        
        self.search_query = ""
        
        # === ДЛЯ СОРТИРОВКИ ===
        self.sort_column = 0
        self.sort_order = Qt.SortOrder.DescendingOrder
        self.sort_column_names = {
            0: "k.id",          # № КРД
            1: "s.surname",     # Фамилия
            2: "s.name",        # Имя
            3: "s.patronymic",  # Отчество
            4: "s.birth_date",  # Дата рождения
            5: "st.name",       # Статус
            6: "lk.usename"     # Занято пользователем (NULLS LAST обрабатывается PG по умолчанию)
        }
        
        # Таймер для поиска с задержкой (debounce)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self.user_id = user_info.get('id')
        self.current_krd_window = None

        # Таймер для обновления статуса занятости (раз в 3 секунды, чтобы не перегружать БД)
        self.lock_timer = QTimer()
        self.lock_timer.timeout.connect(self.update_lock_status)
        
        self.init_ui()
        self.load_krd_data()
        self.audit_logger.log_user_login()
        
        # Очистка зависших блокировок при старте
        self.cleanup_stale_locks_on_startup()
        
        # Запускаем мониторинг блокировок (3000 мс = 3 секунды, оптимальный баланс)
        self.lock_timer.start(3000)
    
    def init_ui(self):
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.create_user_info_section())
        main_layout.addWidget(self.create_separator())
        main_layout.addWidget(self.create_krd_data_section())
    
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        is_reader_role = self.user_info.get('role', '').lower() == 'reader'
        is_admin = self.user_info.get('role') == 'admin'

        # === МЕНЮ "ФАЙЛ" ===
        file_menu = menu_bar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # === МЕНЮ "ОТЧЕТЫ" ===
        reports_menu = menu_bar.addMenu("📊 Отчеты")
        if is_reader_role:
            reports_menu.setEnabled(False)
            reports_menu.setToolTip("🔒 Выгрузка отчетов доступна только операторам и администраторам")
        else:
            generate_all_reports_action = QAction("📥 Отчеты по всем КРД...", self)
            generate_all_reports_action.setShortcut("Ctrl+E")
            generate_all_reports_action.setToolTip("Сгенерировать отчеты по всем КРД в базе данных с выбором шаблона")
            generate_all_reports_action.triggered.connect(self.on_generate_all_reports)
            reports_menu.addAction(generate_all_reports_action)
            
        # === МЕНЮ "СПРАВОЧНИКИ" ===
        ref_menu = menu_bar.addMenu("📚 Справочники")
        if is_reader_role:
            ref_menu.setEnabled(False)
            ref_menu.setToolTip("🔒 Редактирование справочников доступно только операторам и!")
        else:
            all_refs_action = QAction("📋 Все справочники", self)
            all_refs_action.setShortcut("Ctrl+R")
            all_refs_action.triggered.connect(lambda: self.open_reference_editor(None))
            ref_menu.addAction(all_refs_action)
            ref_menu.addSeparator()
            
            for name, table in [("Категории", "categories"), ("Звания", "ranks"), ("Статусы", "statuses"), 
                                ("Военные управления", "military_units"), ("Гарнизоны", "garrisons"), 
                                ("Должности", "positions"), ("Типы запросов", "request_types"), ("Типы инициаторов", "initiator_types")]:
                act = QAction(name, self)
                act.triggered.connect(lambda checked, t=table: self.open_reference_editor(t))
                ref_menu.addAction(act)

        # === МЕНЮ "АДМИНИСТРИРОВАНИЕ" ===
        admin_menu = menu_bar.addMenu("🛡️ Администрирование")
        if is_admin:
            admin_menu.addAction("👥 Управление пользователями", self.open_user_management)
            admin_menu.addAction("📁 Удаленные записи", self.open_deleted_records_window)
            admin_menu.addAction("📋 Аудит действий пользователей", self.open_user_audit_window)
            admin_menu.addAction("⚙️ Управление шаблонами отчетов", self.on_manage_templates)
        else:
            admin_menu.setVisible(False) 
        
        # === МЕНЮ "НАСТРОЙКИ" ===
        settings_menu = menu_bar.addMenu("⚙️ Настройки")
        settings_menu.addAction("🎨 Тема оформления", self.open_theme_settings)
        
        # === МЕНЮ "СПРАВКА" ===
        help_menu = menu_bar.addMenu("Справка")
        help_menu.addAction("О программе", self.show_about_dialog)

    def create_toolbar(self):
        toolbar = self.addToolBar("Основная панель")
        toolbar.addAction("🔄 Обновить", self.load_krd_data)
        
        is_r = is_reader(self.user_info)

        # 1. Кнопка добавления
        add_action = toolbar.addAction("➕ Добавить КРД", self.open_krd_add_window)
        if is_r: add_action.setVisible(False)

        # 2. Кнопка удаления
        self.delete_krd_action = QAction("🗑️ Удалить КРД", self)
        self.delete_krd_action.triggered.connect(self.delete_selected_krd)
        self.delete_krd_action.setEnabled(False)
        if is_r: self.delete_krd_action.setVisible(False)
        toolbar.addAction(self.delete_krd_action)
        
        # 3. Кнопка очистки блокировок (только для админов)
        if self.user_info.get('role') == 'admin':
            toolbar.addSeparator()
            cleanup_btn = QAction("🔓 Очистить блокировки", self)
            cleanup_btn.setToolTip("Снять все зависшие advisory locks")
            cleanup_btn.triggered.connect(self.show_cleanup_dialog)
            toolbar.addAction(cleanup_btn)

    def show_cleanup_dialog(self):
        """Диалог очистки зависших блокировок"""
        try:
            query = QSqlQuery(self.db)
            query.prepare("""
                SELECT pl.objid as krd_id, lk.usename, lk.state, lk.application_name
                FROM pg_locks pl
                LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid
                WHERE pl.locktype = 'advisory' AND pl.granted = true
            """)
            
            if query.exec():
                locks = []
                while query.next():
                    locks.append({
                        'krd_id': query.value(0),
                        'username': query.value(1) or 'unknown',
                        'state': query.value(2) or 'unknown',
                        'app_name': query.value(3) or 'unknown'
                    })
                
                if not locks:
                    QMessageBox.information(self, "Блокировки", "✅ Зависших блокировок не найдено. Все записи свободны!")
                    return
                
                msg = f"Найдено активных блокировок: {len(locks)}\n\n"
                for lock in locks:
                    msg += f"🔒 КРД-{lock['krd_id']} | User: {lock['username']} | App: {lock['app_name']}\n"
                msg += "\n⚠️ Снять все блокировки?"
                
                reply = QMessageBox.question(
                    self, "Очистка блокировок", msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    cleanup = QSqlQuery(self.db)
                    if cleanup.exec("SELECT pg_advisory_unlock_all()"):
                        QMessageBox.information(self, "Успех", f"✅ Снято {len(locks)} блокировок!")
                        self.load_krd_data()
                    else:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось снять блокировки:\n{cleanup.lastError().text()}")
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка проверки блокировок:\n{query.lastError().text()}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
    
    def create_status_bar(self):
        self.statusBar().showMessage(f"Пользователь: {self.user_info['username']} | Роль: {self.user_info['role']}")
    
    def create_user_info_section(self):
        group_box = QGroupBox("Информация о пользователе")
        layout = QGridLayout()
        layout.addWidget(QLabel(f"<b>Имя пользователя:</b> {self.user_info.get('username', 'N/A')}"), 0, 0)
        font = QFont()
        font.setBold(True)
        fn_label = QLabel(f"<b>ФИО:</b> {self.user_info.get('full_name', 'N/A')}")
        fn_label.setFont(font)
        layout.addWidget(fn_label, 0, 1)
        layout.addWidget(QLabel(f"<b>Роль:</b> {self.user_info.get('role', 'N/A')}"), 1, 0, 1, 2)
        group_box.setLayout(layout)
        return group_box
    
    def create_separator(self):
        separator = QWidget()
        separator.setFixedHeight(10)
        return separator
    
    def create_krd_data_section(self):
        group_box = QGroupBox("Данные КРД")
        layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите фамилию, имя, отчество или номер КРД...")
        self.search_input.setMinimumHeight(35)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input)
        
        clear_search_btn = QPushButton("Очистить поиск")
        clear_search_btn.setProperty("role", "danger")
        clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_search_btn)
        
        self.found_count_label = QLabel("Найдено: 0 записей")
        search_layout.addWidget(self.found_count_label)
        
        layout.addLayout(search_layout)
        
        self.table_model_krd = QSqlQueryModel()
        self.krd_table_view = QTableView()
        self.krd_table_view.setModel(self.table_model_krd)
        self.krd_table_view.setAlternatingRowColors(True)
        self.krd_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.krd_table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        header = self.krd_table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)
        header.setSortIndicator(self.sort_column, self.sort_order)
        header.setSectionsClickable(True)
        header.sortIndicatorChanged.connect(self.on_sort_indicator_changed)
        
        self.krd_table_view.doubleClicked.connect(self.on_krd_double_clicked)
        self.krd_table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.krd_table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.krd_table_view.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.krd_table_view)
        group_box.setLayout(layout)
        return group_box
    
    def open_theme_settings(self):
        from theme_settings_dialog import ThemeSettingsDialog
        dlg = ThemeSettingsDialog(self.theme_manager, self)
        if dlg.exec():
            self.update()

    def on_sort_indicator_changed(self, logical_index, order):
        self.sort_column = logical_index
        self.sort_order = order
        self.load_krd_data()
    
    def on_search_text_changed(self, text):
        self.search_query = text.strip()
        self.search_timer.stop()
        self.search_timer.start(300) # Debounce 300ms
    
    def _perform_search(self):
        self.load_krd_data()
    
    def clear_search(self):
        self.search_input.clear()
        self.search_query = ""
        self.load_krd_data()
        self.search_input.setFocus()
    
    def _get_base_query(self):
        """Формирует базовый SQL-запрос с учетом структуры колонок и блокировок"""
        return """
        SELECT
            k.id AS "№ КРД",
            COALESCE(s.surname, '') AS "Фамилия",
            COALESCE(s.name, '') AS "Имя",
            COALESCE(s.patronymic, '') AS "Отчество",
            s.birth_date AS "Дата рождения", 
            COALESCE(st.name, 'Неизвестен') AS "Статус",
            CASE
                WHEN lk.application_name IS NOT NULL THEN lk.application_name
                ELSE '🟢 Не занято'
            END AS "Занято пользователем"
        FROM krd.krd k
        LEFT JOIN krd.social_data s ON k.id = s.krd_id
        LEFT JOIN krd.statuses st ON k.status_id = st.id
        LEFT JOIN pg_locks pl ON pl.locktype = 'advisory'
            AND pl.classid = 0
            AND pl.objid = k.id
            AND pl.objsubid = 1
            AND pl.granted = true
        LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid
        WHERE k.is_deleted = FALSE
        ORDER BY {sort_field} {sort_order}
        """

    def load_krd_data(self):
        """Загрузка данных КРД в таблицу"""
        query = QSqlQuery(self.db)
        sort_field = self.sort_column_names.get(self.sort_column, "k.id")
        sort_order = "ASC" if self.sort_order == Qt.SortOrder.AscendingOrder else "DESC"
        
        base_sql = self._get_base_query().format(sort_field=sort_field, sort_order=sort_order)
        
        if self.search_query:
            search_sql = base_sql.replace(
                "WHERE k.is_deleted = FALSE",
                """WHERE k.is_deleted = FALSE
                AND (
                LOWER(s.surname) LIKE LOWER(:search) OR
                LOWER(s.name) LIKE LOWER(:search) OR
                LOWER(s.patronymic) LIKE LOWER(:search) OR
                LOWER(k.id::text) LIKE LOWER(:search) OR
                LOWER(s.surname || ' ' || s.name || ' ' || s.patronymic) LIKE LOWER(:search) OR
                TO_CHAR(s.birth_date, 'DD.MM.YYYY') LIKE LOWER(:search)
                )"""
            )
            query.prepare(search_sql)
            query.bindValue(":search", f"%{self.search_query}%")
        else:
            query.prepare(base_sql)
        
        if query.exec():
            self.table_model_krd.setQuery(query)
            count = self.table_model_krd.rowCount()
            if self.search_query:
                self.found_count_label.setText(f"🔍 Найдено: {count} записей по запросу \"{self.search_query}\"")
            else:
                self.found_count_label.setText(f"📊 Всего записей: {count}")
        else:
            self.found_count_label.setText("⚠️ Ошибка загрузки данных")

    def update_lock_status(self):
        """Обновляет таблицу для отображения актуального статуса блокировок"""
        # Примечание: Полный перезапрос может быть тяжелым для больших БД. 
        # 3 секунды (настройка в __init__) являются компромиссом между актуальностью и нагрузкой.
        self.load_krd_data()
    
    def on_selection_changed(self, selected, deselected):
        self.delete_krd_action.setEnabled(self.krd_table_view.selectionModel().hasSelection())
    
    def show_context_menu(self, position: QPoint):
        index = self.krd_table_view.indexAt(position)
        if not index.isValid(): return
        
        model = self.table_model_krd
        krd_id = model.data(model.index(index.row(), 0))
        
        menu = QMenu(self)
        menu.addAction("Открыть", lambda: self.on_krd_double_clicked(index))
        menu.addSeparator()
        
        status_menu = menu.addMenu("🔄 Сменить статус")
        self._fill_status_menu(status_menu, krd_id)
        
        menu.addSeparator()
        menu.addAction("Удалить КРД", self.delete_selected_krd)
        menu.exec(self.krd_table_view.mapToGlobal(position))

    def _fill_status_menu(self, menu, krd_id):
        """Заполняет меню доступными статусами из БД"""
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.statuses ORDER BY id")
        
        while query.next():
            status_id = query.value(0)
            status_name = query.value(1)
            action = QAction(status_name, self)
            action.triggered.connect(lambda checked=False, sid=status_id, name=status_name: self.update_krd_status(krd_id, sid, name))
            menu.addAction(action)

    def update_krd_status(self, krd_id, new_status_id, new_status_name):
        """Метод обновления статуса в БД"""
        if not krd_id: return
        
        reply = QMessageBox.question(self, "Смена статуса", 
            f"Установить статус «{new_status_name}» для КРД №{krd_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
        if reply == QMessageBox.StandardButton.Yes:
            try:
                q = QSqlQuery(self.db)
                q.prepare("UPDATE krd.krd SET status_id = :sid WHERE id = :id")
                q.bindValue(":sid", new_status_id)
                q.bindValue(":id", krd_id)
                
                if q.exec():
                    QMessageBox.information(self, "Успех", f"Статус изменен на «{new_status_name}»")
                    self.load_krd_data() 
                    self.audit_logger.log_action('STATUS_CHANGE', 'krd', record_id=krd_id, description=f'Статус изменен на {new_status_name}')
                else:
                    QMessageBox.critical(self, "Ошибка", q.lastError().text())
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
    
    def open_reference_editor(self, initial_table=None):
        try:
            from reference_editor_dialog import ReferenceEditorDialog
            ReferenceEditorDialog(self.db, self, initial_table).exec()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии редактора справочников:\n{str(e)}")
    
    def on_generate_all_reports(self):
        """Открывает диалог конфигурации. Диалог сам выполнит экспорт и закроется."""
        print("🔵 [DEBUG] on_generate_all_reports: Открываю диалог конфигурации...")
        try:
            # ✅ Передаем audit_logger, чтобы диалог мог сам записать действие в журнал
            dialog = ReportConfigDialog(self.db, self, audit_logger=self.audit_logger)
            
            # Просто запускаем диалог. Он сам разберется с QFileDialog, экспортом и закрытием.
            dialog.exec()
            
        except Exception as e:
            print(f"❌ [DEBUG] Ошибка в on_generate_all_reports: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при подготовке отчета:\n{str(e)}")
    
    def on_manage_templates(self):
        try:
            ReportConfigDialog(self.db, self).exec()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка шаблонов:\n{str(e)}")
    
    def delete_selected_krd(self):
        selection_model = self.krd_table_view.selectionModel()
        if not selection_model.hasSelection():
            return QMessageBox.warning(self, "Внимание", "Выберите КРД для удаления")
        
        index = selection_model.selectedRows()[0]
        model = self.table_model_krd
        
        krd_id = model.data(model.index(index.row(), 0))
        surname = model.data(model.index(index.row(), 1))
        name = model.data(model.index(index.row(), 2))
        patronymic = model.data(model.index(index.row(), 3))
        full_name = f"{surname} {name} {patronymic}".strip()
        
        reply = QMessageBox.question(self, "Подтверждение удаления",
            f"Удалить КРД №{krd_id}?\nВоеннослужащий: {full_name}\n\n⚠️ Запись будет скрыта, но сохранена в БД.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if not self.db.transaction(): raise Exception("Не удалось начать транзакцию")
                query = QSqlQuery(self.db)
                query.prepare("UPDATE krd.krd SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP, deleted_by = :uid WHERE id = :id")
                query.bindValue(":uid", self.user_info.get('id'))
                query.bindValue(":id", krd_id)
                if not query.exec(): raise Exception(query.lastError().text())
                if query.numRowsAffected() == 0: raise Exception("Запись не найдена")
                if not self.db.commit(): raise Exception("Ошибка коммита")
                
                self.audit_logger.log_krd_delete(krd_id, {})
                QMessageBox.information(self, "Успех", f"✅ КРД №{krd_id} скрыт!")
                self.load_krd_data()
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления:\n{str(e)}")
    
    def open_krd_add_window(self):
        if AddKrdWindow(self.db).exec() == QDialog.DialogCode.Accepted:
            self.load_krd_data()
    
    def open_user_management(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        from admin_user_management_tab import AdminUserManagementTab
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление пользователями")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(AdminUserManagementTab(self.db))
        layout.addWidget(QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, accepted=dialog.accept))
        dialog.exec()
    
    def on_krd_double_clicked(self, index):
        krd_id = self.table_model_krd.data(self.table_model_krd.index(index.row(), 0))
        if not krd_id: return

        if self.current_krd_window is not None:
            self.current_krd_window.raise_()
            self.current_krd_window.activateWindow()
            return

        from krd_details_window import KrdDetailsWindow
        self.current_krd_window = KrdDetailsWindow(int(krd_id), self.db, self.user_info, self.audit_logger)
        self.current_krd_window.krd_window_closed.connect(self._on_krd_window_closed)
        self.current_krd_window.show()
        self.audit_logger.log_krd_view(int(krd_id))
    
    def show_about_dialog(self):
        QMessageBox.about(self, "О программе", 
            "АРМ сотрудника отдела дознания военной комендатуры\n\n"
            "Версия 1.0 | Магистерская диссертация\n\n"
            "Автор-разработчик: Карамашев Александр Владимирович\n"
            "Заказчик / предметный эксперт: Кувандыков Ильдар Султанович\n\n"
            "Проект разработан на основании требований и прототипов интерфейса,\n"
            "предоставленных заказчиком, с последующей архитектурной проработкой\n"
            "и программной реализацией автором работы."
        )
    
    def closeEvent(self, event):
        self.audit_logger.log_user_logout()
        self.lock_timer.stop()
        super().closeEvent(event)
    
    def open_user_audit_window(self):
        from user_audit_window import UserAuditWindow
        UserAuditWindow(self.db, self.user_info.get('id')).exec()
    
    def open_deleted_records_window(self):
        from deleted_records_window import DeletedRecordsWindow
        DeletedRecordsWindow(self.db).exec()
        
    def _on_krd_window_closed(self):
        print("🔄 [Main] Получен сигнал закрытия КРД. Восстанавливаю фокус...")
        self.current_krd_window = None
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self.load_krd_data()
        
    def cleanup_stale_locks_on_startup(self):
        """Автоматическая очистка зависших блокировок при запуске"""
        try:
            print(f"\n{'='*70}")
            print(f"🧹 [CLEANUP] Проверка зависших блокировок при запуске")
            print(f"{'='*70}")
            
            query = QSqlQuery(self.db)
            query.prepare("""
                SELECT pl.objid as krd_id, lk.usename, lk.state, lk.application_name,
                       lk.query_start, age(now(), lk.query_start) as duration
                FROM pg_locks pl
                LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid
                WHERE pl.locktype = 'advisory' AND pl.granted = true
                AND (lk.state IS NULL OR lk.state != 'active' OR lk.state = 'idle' OR age(now(), lk.query_start) > interval '5 minutes')
            """)
            
            if query.exec():
                stale_locks = []
                while query.next():
                    stale_locks.append({
                        'krd_id': query.value(0),
                        'username': query.value(1) or 'unknown',
                        'state': query.value(2) or 'unknown',
                        'app_name': query.value(3) or 'unknown',
                        'duration': query.value(5) or 'unknown'
                    })
                
                if stale_locks:
                    print(f"⚠️ [CLEANUP] Найдено {len(stale_locks)} потенциально зависших блокировок:")
                    for lock in stale_locks:
                        print(f"   - КРД-{lock['krd_id']} | User: {lock['username']} | State: {lock['state']} | Duration: {lock['duration']}")
                    
                    print(f"🔓 [CLEANUP] Снимаю все блокировки текущей сессии...")
                    cleanup = QSqlQuery(self.db)
                    if cleanup.exec("SELECT pg_advisory_unlock_all()"):
                        print(f"✅ [CLEANUP] Успешно снято {len(stale_locks)} блокировок")
                    else:
                        print(f"❌ [CLEANUP] Ошибка очистки: {cleanup.lastError().text()}")
                else:
                    print(f"✅ [CLEANUP] Зависших блокировок не найдено")
            else:
                print(f"⚠️ [CLEANUP] Ошибка проверки блокировок: {query.lastError().text()}")
                
            print(f"{'='*70}\n")
        except Exception as e:
            print(f"❌ [CLEANUP] Ошибка в cleanup_stale_locks_on_startup: {e}")
            traceback.print_exc()
            print(f"{'='*70}\n")