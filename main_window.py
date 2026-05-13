"""
Модуль для главного окна приложения
Содержит класс MainWindow для отображения данных КРД и информации о пользователе
С функцией выгрузки данных в Excel, поиском в реальном времени и сортировкой по столбцам
✅ ИСПРАВЛЕНО: Убран столбец "Номер КРД", ID переименован в "№ КРД"
✅ ИСПРАВЛЕНО: Убран столбец "ID последнего места службы"
✅ ДОБАВЛЕНО: Столбец "Занято пользователем" (определяется через pg_locks)
"""

import sys
import traceback
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QGroupBox,
    QGridLayout, QMenuBar, QStatusBar, QToolBar, QTableView, QPushButton, QDialog,
    QMessageBox, QMenu, QFileDialog, QAbstractItemView, QProgressDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QPoint, QDate, QTimer
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlTableModel
from PyQt6.QtGui import QAction, QFont, QContextMenuEvent, QIcon

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
    """
    Главное окно приложения
    Отображает данные КРД и информацию о вошедшем пользователе
    """
    
    def __init__(self, user_info, db_connection):
        super().__init__()
        self.user_info = user_info
        self.db = db_connection
        
        self.audit_logger = AuditLogger(self.db, self.user_info)
        
        if not hasattr(self, 'theme_manager'):
            from theme_manager import ThemeManager
            self.theme_manager = ThemeManager(db_connection, user_info.get('id'))
        
        self.setWindowTitle("АРМ Сотрудника дознания - Главное окно")
        self.setGeometry(100, 100, 1200, 800)
        
        self.search_query = ""
        
        # === ДЛЯ СОРТИРОВКИ ===
        # Индексы обновлены под новую структуру таблицы
        self.sort_column = 0
        self.sort_order = Qt.SortOrder.DescendingOrder
        self.sort_column_names = {
            0: "k.id",          # № КРД
            1: "s.surname",     # Фамилия
            2: "s.name",        # Имя
            3: "s.patronymic",  # Отчество
            4: "st.name",       # Статус
            5: "lk.usename"     # Занято пользователем (сортировка по логину)
        }
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        self.user_id = user_info.get('id')
        self.current_krd_window = None

        self.init_ui()
        self.load_krd_data()
        self.audit_logger.log_user_login()
    
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
        
        file_menu = menu_bar.addMenu("Файл")
        generate_all_reports_action = QAction("📥 Сгенерировать отчеты по ВСЕМ КРД...", self)
        generate_all_reports_action.setShortcut("Ctrl+E")
        generate_all_reports_action.triggered.connect(self.on_generate_all_reports)
        file_menu.addAction(generate_all_reports_action)
        
        file_menu.addSeparator()
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        ref_menu = menu_bar.addMenu("📚 Справочники")
        all_refs_action = QAction("📋 Все справочники", self)
        all_refs_action.setShortcut("Ctrl+R")
        all_refs_action.triggered.connect(self.open_reference_editor)
        ref_menu.addAction(all_refs_action)
        ref_menu.addSeparator()
        
        for name, table in [("Категории", "categories"), ("Звания", "ranks"), ("Статусы", "statuses"), 
                            ("Военные управления", "military_units"), ("Гарнизоны", "garrisons"), 
                            ("Должности", "positions"), ("Типы запросов", "request_types"), ("Типы инициаторов", "initiator_types")]:
            act = QAction(name, self)
            act.triggered.connect(lambda checked, t=table: self.open_reference_editor(t))
            ref_menu.addAction(act)
        
        if self.user_info.get('role') == 'admin':
            reports_menu = menu_bar.addMenu("📊 Отчеты")
            reports_menu.addAction("⚙️ Управление шаблонами отчетов", self.on_manage_templates)
            reports_menu.addSeparator()
            reports_menu.addAction("Аудит действий пользователей", self.open_user_audit_window)
        
        settings_menu = self.menuBar().addMenu("⚙️ Настройки")
        settings_menu.addAction("🎨 Тема оформления", self.open_theme_settings)
        
        help_menu = menu_bar.addMenu("Справка")
        help_menu.addAction("О программе", self.show_about_dialog)
    
    def create_toolbar(self):
        toolbar = self.addToolBar("Основная панель")
        toolbar.addAction("🔄 Обновить", self.load_krd_data)
        toolbar.addAction("➕ Добавить КРД", self.open_krd_add_window)
        
        self.delete_krd_action = QAction("🗑️ Удалить КРД", self)
        self.delete_krd_action.triggered.connect(self.delete_selected_krd)
        self.delete_krd_action.setEnabled(False)
        toolbar.addAction(self.delete_krd_action)
        
        toolbar.addSeparator()
        toolbar.addAction("📥 Отчеты по всем КРД", self.on_generate_all_reports)
        toolbar.addAction("📚 Справочники", self.open_reference_editor)
        
        if self.user_info.get('role') == 'admin':
            toolbar.addSeparator()
            toolbar.addAction("📁 Удаленные записи", self.open_deleted_records_window)
            toolbar.addAction("👥 Управление пользователями", self.open_user_management)
            toolbar.addAction("📋 Аудит пользователей", self.open_user_audit_window)
    
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
        self.load_krd_data()
        
        self.krd_table_view = QTableView()
        self.krd_table_view.setModel(self.table_model_krd)
        self.krd_table_view.setAlternatingRowColors(True)
        self.krd_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.krd_table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        
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
        self.search_timer.start(300)
    
    def _perform_search(self):
        self.load_krd_data()
    
    def clear_search(self):
        self.search_input.clear()
        self.search_query = ""
        self.load_krd_data()
        self.search_input.setFocus()
    
    def _get_base_query(self):
        """Формирует базовый SQL-запрос с учетом новой структуры колонок"""
        return """
            SELECT
                k.id AS "№ КРД",
                COALESCE(s.surname, '') AS "Фамилия",
                COALESCE(s.name, '') AS "Имя",
                COALESCE(s.patronymic, '') AS "Отчество",
                COALESCE(st.name, 'Неизвестен') AS "Статус",
                COALESCE(lk.usename, '') AS "Занято пользователем"
            FROM krd.krd k
            LEFT JOIN krd.social_data s ON k.id = s.krd_id
            LEFT JOIN krd.statuses st ON k.status_id = st.id
            LEFT JOIN pg_locks pl ON pl.locktype = 'advisory' 
                AND pl.classid = 0 
                AND pl.objid = k.id 
                AND pl.objsubid = 1 
                AND pl.granted = true
            LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid AND lk.usename != current_user
            WHERE k.is_deleted = FALSE
            ORDER BY {sort_field} {sort_order}
        """

    def load_krd_data(self):
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
                    LOWER(s.surname || ' ' || s.name || ' ' || s.patronymic) LIKE LOWER(:search)
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
            print(f"⚠️ Ошибка загрузки данных: {query.lastError().text()}")
            self.found_count_label.setText("⚠️ Ошибка загрузки данных")
    
    def on_selection_changed(self, selected, deselected):
        self.delete_krd_action.setEnabled(self.krd_table_view.selectionModel().hasSelection())
    
    def show_context_menu(self, position: QPoint):
        index = self.krd_table_view.indexAt(position)
        if not index.isValid(): return
        
        menu = QMenu(self)
        menu.addAction("Открыть", lambda: self.on_krd_double_clicked(index))
        menu.addAction("Удалить КРД", self.delete_selected_krd)
        menu.addSeparator()
        menu.addAction("📥 Сгенерировать отчеты по ВСЕМ КРД", self.on_generate_all_reports)
        menu.exec(self.krd_table_view.mapToGlobal(position))
    
    def open_reference_editor(self, initial_table=None):
        try:
            from reference_editor_dialog import ReferenceEditorDialog
            ReferenceEditorDialog(self.db, self, initial_table).exec()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии редактора справочников:\n{str(e)}")
    
    def on_generate_all_reports(self):
        try:
            dialog = ReportConfigDialog(self.db, self)
            dialog.report_configured.connect(lambda config: self._on_report_configured(config))
            dialog.exec()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при подготовке отчета:\n{str(e)}")
    
    def _on_report_configured(self, config):
        krd_ids = config.get("krd_ids", [])
        default_filename = f"КРД_ВСЕ_отчет_{QDate.currentDate().toString('yyyy-MM-dd')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчеты по всем КРД", default_filename, "Excel файлы (*.xlsx);;Все файлы (*)")
        if not file_path: return
        
        try:
            progress_msg = QProgressDialog("Генерация отчета...\nПожалуйста, подождите.", "Отмена", 0, 0, self)
            progress_msg.setWindowTitle("Генерация отчета")
            progress_msg.setWindowModality(Qt.WindowModality.WindowModal)
            progress_msg.show()
            QApplication.processEvents()
            
            exporter = KrdExcelExporter(self.db, report_config=config)
            exporter.export_multiple_krd_to_excel(file_path, krd_ids)
            progress_msg.close()
            
            QMessageBox.information(self, "Успешно", f"✅ Отчеты сохранены:\n📊 КРД: {len(krd_ids)}\n📁 {file_path}")
            self.audit_logger.log_action('REPORT_EXPORT', 'krd', description=f'Экспорт {len(krd_ids)} КРД')
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"❌ Ошибка генерации:\n{str(e)}")
    
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
        QMessageBox.about(self, "О программе", f"АРМ Сотрудника дознания\nПользователь: {self.user_info.get('username')}\nРоль: {self.user_info.get('role')}")
    
    def closeEvent(self, event):
        self.audit_logger.log_user_logout()
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

def main():
    app = QApplication(sys.argv)
    db = QSqlDatabase.addDatabase("QPSQL")
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")
    if not db.open():
        QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к БД:\n{db.lastError().text()}")
        sys.exit(1)
    
    user_info = {'id': 1, 'username': 'admin', 'full_name': 'Администратор', 'role': 'admin'}
    main_window = MainWindow(user_info, db)
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()