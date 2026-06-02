import sys
import traceback
from ui_helpers import is_reader, apply_readonly_mode
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QGroupBox,
    QGridLayout, QMenuBar, QStatusBar, QToolBar, QTableView, QPushButton, QDialog,
    QMessageBox, QMenu, QFileDialog, QAbstractItemView, QProgressDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QPoint, QDate, QTime, QTimer
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlTableModel
from PyQt6.QtGui import QAction, QFont, QContextMenuEvent, QIcon
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell
from add_krd_window import AddKrdWindow
from audit_logger import AuditLogger
from export_helper import KrdExcelExporter
from report_config_dialog import ReportConfigDialog
from theme_manager import ThemeManager
class MainWindow(QMainWindow):
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
        self.sort_column = 0
        self.sort_order = Qt.SortOrder.DescendingOrder
        self.sort_column_names = {
            0: "k.id",
            1: "s.surname",
            2: "s.name",
            3: "s.patronymic",
            4: "s.birth_date",
            5: "st.name",
            6: "lk.usename"
        }
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        self.user_id = user_info.get('id')
        self.current_krd_window = None
        self.lock_timer = QTimer()
        self.lock_timer.timeout.connect(self.update_lock_status)
        self.init_ui()
        self.load_krd_data()
        self.audit_logger.log_user_login()
        self.cleanup_stale_locks_on_startup()
        self.lock_timer.start(1000)
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
        is_reader = self.user_info.get('role', '').lower() == 'reader'
        is_admin = self.user_info.get('role') == 'admin'
        file_menu = menu_bar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        reports_menu = menu_bar.addMenu("📊 Отчеты")
        if is_reader:
            reports_menu.setEnabled(False)
            reports_menu.setToolTip("🔒 Выгрузка отчетов доступна только операторам и администраторам")
        else:
            generate_all_reports_action = QAction("📥 Отчеты по всем КРД...", self)
            generate_all_reports_action.setShortcut("Ctrl+E")
            generate_all_reports_action.setToolTip("Сгенерировать отчеты по всем КРД в базе данных с выбором шаблона")
            generate_all_reports_action.triggered.connect(self.on_generate_all_reports)
            reports_menu.addAction(generate_all_reports_action)
        ref_menu = menu_bar.addMenu("📚 Справочники")
        if is_reader:
            ref_menu.setEnabled(False)
            ref_menu.setToolTip("🔒 Редактирование справочников доступно только операторам и администраторам")
        else:
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
        admin_menu = menu_bar.addMenu("🛡️ Администрирование")
        if is_admin:
            admin_menu.addAction("👥 Управление пользователями", self.open_user_management)
            admin_menu.addAction("📁 Удаленные записи", self.open_deleted_records_window)
            admin_menu.addAction("📋 Аудит действий пользователей", self.open_user_audit_window)
            admin_menu.addAction("⚙️ Управление шаблонами отчетов", self.on_manage_templates)
        else:
            admin_menu.setVisible(False)
        settings_menu = self.menuBar().addMenu("⚙️ Настройки")
        settings_menu.addAction("🎨 Тема оформления", self.open_theme_settings)
        help_menu = menu_bar.addMenu("Справка")
        help_menu.addAction("О программе", self.show_about_dialog)
    def create_toolbar(self):
        toolbar = self.addToolBar("Основная панель")
        toolbar.addAction("🔄 Обновить", self.load_krd_data)
        is_r = is_reader(self.user_info)
        add_action = toolbar.addAction("➕ Добавить КРД", self.open_krd_add_window)
        if is_r: add_action.setVisible(False)
        self.delete_krd_action = QAction("🗑️ Удалить КРД", self)
        self.delete_krd_action.triggered.connect(self.delete_selected_krd)
        self.delete_krd_action.setEnabled(False)
        if is_r: self.delete_krd_action.setVisible(False)
        toolbar.addAction(self.delete_krd_action)
        if self.user_info.get('role') == 'admin':
            toolbar.addSeparator()
            cleanup_btn = QAction("🔓 Очистить блокировки", self)
            cleanup_btn.setToolTip("Снять все зависшие advisory locks")
            cleanup_btn.triggered.connect(self.show_cleanup_dialog)
            toolbar.addAction(cleanup_btn)
    def show_cleanup_dialog(self):
        try:
            query = QSqlQuery(self.db)
            query.prepare("""
                SELECT
                    pl.objid as krd_id,
                    lk.usename,
                    lk.state,
                    lk.application_name
                FROM pg_locks pl
                LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid
                WHERE pl.locktype = 'advisory'
                AND pl.granted = true
Формирует базовый SQL-запрос с учетом новой структуры колонок"""
        return """
        SELECT
            k.id AS "№ КРД",
            COALESCE(s.surname, '') AS "Фамилия",
            COALESCE(s.name, '') AS "Имя",
            COALESCE(s.patronymic, '') AS "Отчество",
            -- ✅ ДОБАВЛЕНО: Дата рождения
            s.birth_date AS "Дата рождения",
            COALESCE(st.name, 'Неизвестен') AS "Статус",
            -- ✅ ИЗМЕНЕНО: Теперь показываем application_name (логин программы)
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
Загрузка данных КРД в таблицу"""
        query = QSqlQuery(self.db)
        sort_field = self.sort_column_names.get(self.sort_column, "k.id")
        sort_order = "ASC" if self.sort_order == Qt.SortOrder.AscendingOrder else "DESC"
        base_sql = self._get_base_query().format(sort_field=sort_field, sort_order=sort_order)
        if self.search_query:
            search_sql = base_sql.replace(
                "WHERE k.is_deleted = FALSE",
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
        global_locks_query = QSqlQuery(self.db)
        global_locks_query.prepare("""
            SELECT pl.objid, lk.usename, lk.pid
            FROM pg_locks pl
            LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid
            WHERE pl.locktype = 'advisory' AND pl.granted = true
Заполняет меню доступными статусами из БД"""
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.statuses ORDER BY id")
        while query.next():
            status_id = query.value(0)
            status_name = query.value(1)
            action = QAction(status_name, self)
            action.triggered.connect(lambda checked=False, sid=status_id, name=status_name: self.update_krd_status(krd_id, sid, name))
            menu.addAction(action)
    def update_krd_status(self, krd_id, new_status_id, new_status_name):
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
        try:
            print(f"\n{'='*70}")
            print(f"🧹 [CLEANUP] Проверка зависших блокировок при запуске")
            print(f"{'='*70}")
            query = QSqlQuery(self.db)
            query.prepare("""
                SELECT
                    pl.objid as krd_id,
                    lk.usename,
                    lk.state,
                    lk.application_name,
                    lk.query_start,
                    age(now(), lk.query_start) as duration
                FROM pg_locks pl
                LEFT JOIN pg_stat_activity lk ON lk.pid = pl.pid
                WHERE pl.locktype = 'advisory'
                AND pl.granted = true
                AND (
                    lk.state IS NULL
                    OR lk.state != 'active'
                    OR lk.state = 'idle'
                    OR age(now(), lk.query_start) > interval '5 minutes'
                )
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
                        print(f"   - КРД-{lock['krd_id']} | User: {lock['username']} | "
                            f"State: {lock['state']} | Duration: {lock['duration']}")
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
            import traceback
            traceback.print_exc()
            print(f"{'='*70}\n")
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