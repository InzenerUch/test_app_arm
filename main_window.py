"""
Модуль для главного окна приложения
Содержит класс MainWindow для отображения данных КРД и информации о пользователе
С функцией выгрузки данных в Excel
"""

import sys
import traceback
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QGroupBox,
    QGridLayout, QMenuBar, QStatusBar, QToolBar, QTableView, QPushButton, QDialog,
    QMessageBox, QMenu, QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, QPoint, QDate
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery, QSqlTableModel
from PyQt6.QtGui import QAction, QFont, QContextMenuEvent

# === ИМПОРТЫ ДЛЯ ЭКСПОРТА В EXCEL ===
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell

# === ИМПОРТЫ ПРИЛОЖЕНИЯ ===
from add_krd_window import AddKrdWindow
from audit_logger import AuditLogger
from export_helper import KrdExcelExporter


class MainWindow(QMainWindow):
    """
    Главное окно приложения
    Отображает данные КРД и информацию о вошедшем пользователе
    """
    
    def __init__(self, user_info, db_connection):
        """
        Инициализация главного окна
        
        Args:
            user_info (dict): информация о пользователе, полученная из окна авторизации
            db_connection: соединение с базой данных
        """
        super().__init__()
        self.user_info = user_info
        self.db = db_connection
        
        # Инициализация логгера аудита
        self.audit_logger = AuditLogger(self.db, self.user_info)
        
        # Установка основных параметров окна
        self.setWindowTitle("АРМ Сотрудника дознания - Главное окно")
        self.setGeometry(100, 100, 1200, 800)  # x, y, ширина, высота
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Загрузка данных
        self.load_krd_data()
        
        # Логирование входа в систему
        self.audit_logger.log_user_login()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        # Создание меню
        self.create_menu_bar()
        
        # Создание тулбара
        self.create_toolbar()
        
        # Создание статусбара
        self.create_status_bar()
        
        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной макет
        main_layout = QVBoxLayout(central_widget)
        
        # Группа с информацией о пользователе
        user_info_group = self.create_user_info_section()
        main_layout.addWidget(user_info_group)
        
        # Разделитель
        separator = self.create_separator()
        main_layout.addWidget(separator)
        
        # Группа с данными КРД
        krd_data_group = self.create_krd_data_section()
        main_layout.addWidget(krd_data_group)
    
    def create_menu_bar(self):
        """Создание строки меню"""
        menu_bar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menu_bar.addMenu("Файл")
        
        # Действие "Выгрузить все КРД в Excel"
        export_action = QAction("📊 Выгрузить все КРД в Excel", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_all_krd_to_excel)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Действие "Выход"
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Отчеты" (только для администраторов)
        if self.user_info.get('role') == 'admin':
            reports_menu = menu_bar.addMenu("Отчеты")
            
            # Действие "Аудит пользователей"
            audit_action = QAction("Аудит действий пользователей", self)
            audit_action.triggered.connect(self.open_user_audit_window)
            reports_menu.addAction(audit_action)
        
        # Меню "Справка"
        help_menu = menu_bar.addMenu("Справка")
        
        # Действие "О программе"
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = self.addToolBar("Основная панель")

        # Добавляем действия на тулбар
        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.load_krd_data)
        toolbar.addAction(refresh_action)

        # Добавляем действие "Добавить КРД"
        add_krd_action = QAction("➕ Добавить КРД", self)
        add_krd_action.triggered.connect(self.open_krd_add_window)
        toolbar.addAction(add_krd_action)
        
        # Добавляем действие "Удалить КРД"
        delete_krd_action = QAction("🗑️ Удалить КРД", self)
        delete_krd_action.triggered.connect(self.delete_selected_krd)
        delete_krd_action.setEnabled(False)  # По умолчанию отключено
        toolbar.addAction(delete_krd_action)
        self.delete_krd_action = delete_krd_action
        
        # Действие "Выгрузить в Excel"
        toolbar.addSeparator()
        export_action = QAction("📊 Выгрузить в Excel", self)
        export_action.triggered.connect(self.export_all_krd_to_excel)
        toolbar.addAction(export_action)
        
        # Добавляем разделитель
        toolbar.addSeparator()
        
        # Добавляем действие "Удаленные записи" (только для администраторов)
        if self.user_info.get('role') == 'admin':
            deleted_records_action = QAction("📁 Удаленные записи", self)
            deleted_records_action.triggered.connect(self.open_deleted_records_window)
            toolbar.addAction(deleted_records_action)
        
        # Добавляем действие "Аудит пользователей" (только для администраторов)
        if self.user_info.get('role') == 'admin':
            audit_action = QAction("📋 Аудит пользователей", self)
            audit_action.triggered.connect(self.open_user_audit_window)
            toolbar.addAction(audit_action)
        
        # Добавляем действие "Управление пользователями" (только для администраторов)
        if self.user_info.get('role') == 'admin':
            user_mgmt_action = QAction("👥 Управление пользователями", self)
            user_mgmt_action.triggered.connect(self.open_user_management)
            toolbar.addAction(user_mgmt_action)
    
    def open_deleted_records_window(self):
        """Открытие окна удаленных записей"""
        from deleted_records_window import DeletedRecordsWindow
        
        deleted_window = DeletedRecordsWindow(self.db)
        deleted_window.exec()
    
    def create_status_bar(self):
        """Создание строки состояния"""
        status_bar = self.statusBar()
        status_bar.showMessage(f"Пользователь: {self.user_info['username']} | Роль: {self.user_info['role']}")
    
    def create_user_info_section(self):
        """Создание секции с информацией о пользователе"""
        group_box = QGroupBox("Информация о пользователе")
        layout = QGridLayout()
        
        # Метки для отображения информации о пользователе
        username_label = QLabel(f"<b>Имя пользователя:</b> {self.user_info.get('username', 'N/A')}")
        full_name_label = QLabel(f"<b>ФИО:</b> {self.user_info.get('full_name', 'N/A')}")
        role_label = QLabel(f"<b>Роль:</b> {self.user_info.get('role', 'N/A')}")
        
        # Устанавливаем жирный шрифт для значений
        font = QFont()
        font.setBold(True)
        full_name_label.setFont(font)
        
        # Добавляем метки в макет
        layout.addWidget(username_label, 0, 0)
        layout.addWidget(full_name_label, 0, 1)
        layout.addWidget(role_label, 1, 0, 1, 2)  # Занимает 2 колонки
        
        group_box.setLayout(layout)
        return group_box
    
    def create_separator(self):
        """Создание разделителя между секциями"""
        separator = QWidget()
        separator.setFixedHeight(10)
        return separator
    
    def create_krd_data_section(self):
        """Создание секции с данными КРД"""
        group_box = QGroupBox("Данные КРД")
        layout = QVBoxLayout()
        
        # Создаем модель данных для таблицы krd 
        self.table_model_krd = QSqlQueryModel()
        self.query_table_krd = """SELECT
            k.id AS "ID",
            CONCAT('КРД-', k.id) AS "Номер КРД",
            COALESCE(s.surname, '') AS "Фамилия",
            COALESCE(s.name, '') AS "Имя",
            COALESCE(s.patronymic, '') AS "Отчество",
            COALESCE(st.name, 'Неизвестен') AS "Статус",
            k.last_service_place_id AS "ID последнего места службы"
        FROM krd.krd k
        LEFT JOIN krd.social_data s ON k.id = s.krd_id
        LEFT JOIN krd.statuses st ON k.status_id = st.id
        ORDER BY k.id DESC
        LIMIT 100"""
        self.table_model_krd.setQuery(self.query_table_krd, self.db)
        
        # Создаем таблицу для отображения данных КРД
        self.krd_table_view = QTableView()
        self.krd_table_view.setModel(self.table_model_krd)
        self.krd_table_view.setAlternatingRowColors(True)
        self.krd_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.krd_table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        header = self.krd_table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.krd_table_view.doubleClicked.connect(self.on_krd_double_clicked)
        
        # Подключаем сигнал изменения выделения
        selection_model = self.krd_table_view.selectionModel()
        selection_model.selectionChanged.connect(self.on_selection_changed)
        
        # Включаем контекстное меню
        self.krd_table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.krd_table_view.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.krd_table_view)
        
        group_box.setLayout(layout)
        
        return group_box
    
    def on_selection_changed(self, selected, deselected):
        """Обработка изменения выделения в таблице"""
        # Включаем/выключаем кнопку удаления в зависимости от выделения
        has_selection = self.krd_table_view.selectionModel().hasSelection()
        self.delete_krd_action.setEnabled(has_selection)
    
    def show_context_menu(self, position: QPoint):
        """Показ контекстного меню при правом клике на таблице"""
        # Получаем индекс строки, на которой был клик
        index = self.krd_table_view.indexAt(position)
        
        if not index.isValid():
            return
        
        # Создаем контекстное меню
        menu = QMenu(self)
        
        # Действие "Открыть"
        open_action = QAction("Открыть", self)
        open_action.triggered.connect(lambda: self.on_krd_double_clicked(index))
        menu.addAction(open_action)
        
        # Действие "Удалить"
        delete_action = QAction("Удалить КРД", self)
        delete_action.triggered.connect(self.delete_selected_krd)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Действие "Выгрузить в Excel"
        export_action = QAction("📊 Выгрузить в Excel", self)
        export_action.triggered.connect(self.export_all_krd_to_excel)
        menu.addAction(export_action)
        
        # Показываем меню в позиции курсора
        menu.exec(self.krd_table_view.mapToGlobal(position))
    
    def export_all_krd_to_excel(self):
        """Экспорт ВСЕХ данных КРД в Excel файл"""
        try:
            # Диалог выбора пути сохранения
            default_filename = f"КРД_выгрузка_{QDate.currentDate().toString('yyyy-MM-dd')}.xlsx"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить выгрузку в Excel",
                default_filename,
                "Excel файлы (*.xlsx);;Все файлы (*)"
            )
            
            if not file_path:
                return  # Пользователь отменил
            
            # Показываем индикатор загрузки
            QMessageBox.information(
                self,
                "Выгрузка данных",
                "⏳ Пожалуйста, подождите...\nИдёт выгрузка данных в Excel."
            )
            
            # Получаем список всех KRD ID
            query = QSqlQuery(self.db)
            query.prepare("SELECT id FROM krd.krd ORDER BY id")
            query.exec()
            
            krd_ids = []
            while query.next():
                krd_ids.append(query.value(0))
            
            if not krd_ids:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "⚠️ В базе данных нет записей КРД для выгрузки."
                )
                return
            
            # Создаём Excel файл с несколькими листами
            wb = Workbook()
            wb.remove(wb.active)  # Удаляем стандартный лист
            
            # Создаём лист с общим списком КРД
            ws_summary = wb.create_sheet("Список КРД")
            self._fill_summary_sheet(ws_summary, krd_ids)
            
            # Создаём листы для каждой КРД
            for krd_id in krd_ids:
                exporter = KrdExcelExporter(self.db, krd_id)
                ws = wb.create_sheet(f"КРД-{krd_id}")
                exporter.export_to_single_sheet(ws)
            
            # Сохраняем файл
            wb.save(file_path)
            
            # Логирование
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='EXPORT_ALL_KRD_EXCEL',
                    table_name='krd',
                    krd_id=None,
                    description=f'Выгрузка всех КРД ({len(krd_ids)} записей) в Excel: {file_path}'
                )
            
            QMessageBox.information(
                self,
                "Успех",
                f"✅ Данные успешно выгружены в Excel\n\n"
                f"📊 Всего КРД: {len(krd_ids)}\n"
                f"📁 Файл: {file_path}\n\n"
                f"Файл содержит:\n"
                f"• Лист 'Список КРД' - общий реестр\n"
                f"• Листы 'КРД-X' - подробные данные по каждой КРД"
            )
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Ошибка",
                f"❌ Ошибка при выгрузке в Excel:\n{str(e)}"
            )
    
    def _fill_summary_sheet(self, ws, krd_ids):
        """Заполнение листа с общим списком КРД"""
        # Стили
        header_font = Font(bold=True, size=11, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Заголовок
        ws.merge_cells('A1:H1')
        cell = ws['A1']
        cell.value = "ОБЩИЙ РЕЕСТР КАРТОЧЕК РОЗЫСКА (КРД)"
        cell.font = Font(bold=True, size=14)
        cell.alignment = header_alignment
        
        # Заголовки колонок
        headers = [
            "№ КРД", "Фамилия", "Имя", "Отчество",
            "Дата рождения", "Статус", "Табельный номер", "Личный номер"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=2, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        # Данные - используем IN вместо ANY для совместимости
        placeholders = ','.join(['%s'] * len(krd_ids))
        query = QSqlQuery(self.db)
        query.prepare(f"""
            SELECT 
                k.id,
                s.surname,
                s.name,
                s.patronymic,
                s.birth_date,
                st.name as status_name,
                s.tab_number,
                s.personal_number
            FROM krd.krd k
            LEFT JOIN krd.social_data s ON k.id = s.krd_id
            LEFT JOIN krd.statuses st ON k.status_id = st.id
            WHERE k.id IN ({placeholders})
            ORDER BY k.id
        """)
        
        for krd_id in krd_ids:
            query.addBindValue(krd_id)
        
        query.exec()
        
        row = 3
        while query.next():
            ws.cell(row=row, column=1, value=query.value('id'))
            ws.cell(row=row, column=2, value=query.value('surname') or '')
            ws.cell(row=row, column=3, value=query.value('name') or '')
            ws.cell(row=row, column=4, value=query.value('patronymic') or '')
            ws.cell(row=row, column=5, value=query.value('birth_date').toString("dd.MM.yyyy") if query.value('birth_date') else '')
            ws.cell(row=row, column=6, value=query.value('status_name') or '')
            ws.cell(row=row, column=7, value=query.value('tab_number') or '')
            ws.cell(row=row, column=8, value=query.value('personal_number') or '')
            
            # Применяем границы
            for col in range(1, 9):
                ws.cell(row=row, column=col).border = thin_border
            
            row += 1
        
        # Настройка ширины колонок (исправлено для MergedCell)
        for col_num in range(1, 9):
            max_length = 0
            column_letter = get_column_letter(col_num)
            
            # Проходим только по строкам с данными (начиная с 2, заголовки тоже учитываем)
            for row_num in range(2, row + 1):
                cell = ws.cell(row=row_num, column=col_num)
                # Пропускаем merged cells
                if not isinstance(cell, MergedCell):
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def delete_selected_krd(self):
        """Удаление выбранной записи КРД с подтверждением"""
        # Получаем выделенную строку
        selection_model = self.krd_table_view.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Внимание", "Выберите КРД для удаления")
            return
        
        # Получаем индекс выбранной строки
        selected_indexes = selection_model.selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Внимание", "Выберите КРД для удаления")
            return
        
        index = selected_indexes[0]
        
        # Получаем данные о выбранной записи
        krd_id = self.table_model_krd.data(self.table_model_krd.index(index.row(), 0))
        krd_number = self.table_model_krd.data(self.table_model_krd.index(index.row(), 1))
        surname = self.table_model_krd.data(self.table_model_krd.index(index.row(), 2))
        name = self.table_model_krd.data(self.table_model_krd.index(index.row(), 3))
        patronymic = self.table_model_krd.data(self.table_model_krd.index(index.row(), 4))
        
        full_name = f"{surname} {name} {patronymic}".strip()
        
        # Показываем диалог подтверждения
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить КРД?\n\n"
            f"Номер КРД: {krd_number}\n"
            f"Военнослужащий: {full_name}\n\n"
            f"⚠️ Внимание: Все связанные данные (адреса, места службы, "
            f"поручения, запросы, эпизоды СОЧ) будут удалены безвозвратно!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        # Если пользователь подтвердил удаление
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Получаем данные для логирования
                query_data = QSqlQuery(self.db)
                query_data.prepare("""
                    SELECT s.* 
                    FROM krd.social_data s 
                    WHERE s.krd_id = ?
                """)
                query_data.addBindValue(krd_id)
                query_data.exec()
                
                old_data = {}
                if query_data.next():
                    for i in range(query_data.record().count()):
                        field_name = query_data.record().fieldName(i)
                        old_data[field_name] = query_data.value(i)
                
                # Начинаем транзакцию
                if not self.db.transaction():
                    raise Exception(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
                
                # Удаляем запись из таблицы КРД
                query = QSqlQuery(self.db)
                query.prepare("DELETE FROM krd.krd WHERE id = ?")
                query.addBindValue(krd_id)
                
                if not query.exec():
                    raise Exception(f"Ошибка при удалении КРД: {query.lastError().text()}")
                
                # Фиксируем транзакцию
                if not self.db.commit():
                    raise Exception(f"Ошибка при коммите транзакции: {self.db.lastError().text()}")
                
                # Логирование удаления
                self.audit_logger.log_krd_delete(krd_id, old_data)
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"КРД №{krd_number} успешно удален!\n"
                    f"Все связанные данные также удалены."
                )
                
                # Обновляем данные в таблице
                self.load_krd_data()
                
            except Exception as e:
                # Откатываем транзакцию при ошибке
                self.db.rollback()
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Ошибка при удалении КРД:\n{str(e)}"
                )
    
    def open_krd_add_window(self):
        """Открытие окна добавления КРД"""
        krd_add_window = AddKrdWindow(self.db)

        if krd_add_window.exec() == QDialog.DialogCode.Accepted:
            self.load_krd_data()
    
    def open_user_management(self):
        """Открытие окна управления пользователями (только для администраторов)"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        from admin_user_management_tab import AdminUserManagementTab
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление пользователями")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Добавляем вкладку управления пользователями
        user_mgmt_tab = AdminUserManagementTab(self.db)
        layout.addWidget(user_mgmt_tab)
        
        # Кнопки OK и Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def on_krd_double_clicked(self, index):
        """Обработка двойного клика по строке в таблице КРД"""
        # Получаем ID КРД из первой колонки
        krd_id = self.table_model_krd.data(self.table_model_krd.index(index.row(), 0))

        if krd_id:
            # Логирование просмотра КРД
            self.audit_logger.log_krd_view(int(krd_id))
            
            # Открываем окно деталей КРД
            from krd_details_window import KrdDetailsWindow
            details_window = KrdDetailsWindow(int(krd_id), self.db, self.audit_logger)

            if details_window.exec() == QDialog.DialogCode.Accepted:
                # Обновляем данные в таблице после сохранения
                self.load_krd_data()

    def load_krd_data(self):
        """Загрузка данных КРД в таблицу"""
        self.table_model_krd.setQuery(self.query_table_krd, self.db)
    
    def show_about_dialog(self):
        """Показ диалога "О программе" """
        QMessageBox.about(
            self,
            "О программе",
            "АРМ Сотрудника дознания\n\n"
            "Главное окно приложения\n"
            f"Пользователь: {self.user_info.get('username', 'N/A')}\n"
            f"Роль: {self.user_info.get('role', 'N/A')}"
        )
    
    def closeEvent(self, event):
        """
        Обработчик закрытия окна
        Логирует выход пользователя из системы
        """
        # Логирование выхода из системы
        self.audit_logger.log_user_logout()
        
        # Вызываем родительский метод
        super().closeEvent(event)
    
    def open_user_audit_window(self):
        """Открытие окна аудита действий пользователей"""
        from user_audit_window import UserAuditWindow
        
        audit_window = UserAuditWindow(self.db, self.user_info.get('id'))
        audit_window.exec()


def main():
    """Тестовая функция для демонстрации главного окна"""
    app = QApplication(sys.argv)
    
    # Подключение к базе данных (для тестирования)
    db = QSqlDatabase.addDatabase("QPSQL")
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")
    
    if not db.open():
        QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных:\n{db.lastError().text()}")
        sys.exit(1)
    
    # Тестовые данные пользователя (обычно передаются из окна авторизации)
    user_info = {
        'id': 1,
        'username': 'test_user',
        'full_name': 'Иванов Иван Иванович',
        'role': 'Сотрудник'
    }
    
    # Создание и показ главного окна
    main_window = MainWindow(user_info, db)
    main_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()