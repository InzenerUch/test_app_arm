"""
Модуль для главного окна приложения
Содержит класс MainWindow для отображения данных КРД и информации о пользователе
С функцией выгрузки данных в Excel, поиском в реальном времени и сортировкой по столбцам
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
        
        if not hasattr(self, 'theme_manager'):
            from theme_manager import ThemeManager
            self.theme_manager = ThemeManager(db_connection, user_info.get('id'))
        
        # Установка основных параметров окна
        self.setWindowTitle("АРМ Сотрудника дознания - Главное окно")
        self.setGeometry(100, 100, 1200, 800)
        
        # Переменная для хранения поискового запроса
        self.search_query = ""
        
        # === ДЛЯ СОРТИРОВКИ ===
        self.sort_column = 0  # Индекс столбца для сортировки
        self.sort_order = Qt.SortOrder.DescendingOrder  # Порядок сортировки
        self.sort_column_names = {
            0: "k.id",  # ID
            1: "k.id",  # Номер КРД (сортируем по ID)
            2: "s.surname",  # Фамилия
            3: "s.name",  # Имя
            4: "s.patronymic",  # Отчество
            5: "st.name",  # Статус
            6: "k.last_service_place_id"  # ID последнего места службы
        }
        # ===================
        
        # Таймер для задержки поиска (debounce)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        self.user_id = user_info.get('id')
     
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Загрузка данных
        self.load_krd_data()
        
        # Логирование входа в систему
        self.audit_logger.log_user_login()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        user_info_group = self.create_user_info_section()
        main_layout.addWidget(user_info_group)
        
        separator = self.create_separator()
        main_layout.addWidget(separator)
        
        krd_data_group = self.create_krd_data_section()
        main_layout.addWidget(krd_data_group)
    
    def create_menu_bar(self):
        """Создание строки меню"""
        menu_bar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menu_bar.addMenu("Файл")
        
        # === Действие "Сгенерировать отчеты по ВСЕМ КРД" ===
        generate_all_reports_action = QAction("📥 Сгенерировать отчеты по ВСЕМ КРД...", self)
        generate_all_reports_action.setShortcut("Ctrl+E")
        generate_all_reports_action.triggered.connect(self.on_generate_all_reports)
        file_menu.addAction(generate_all_reports_action)
        
        file_menu.addSeparator()
        
        # Действие "Выход"
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # === Меню "Справочники" (ДОСТУПНО ВСЕМ ПОЛЬЗОВАТЕЛЯМ) ===
        ref_menu = menu_bar.addMenu("📚 Справочники")
        
        settings_menu = self.menuBar().addMenu("⚙️ Настройки")
        theme_action = QAction("🎨 Тема оформления", self)
        theme_action.triggered.connect(self.open_theme_settings)
        settings_menu.addAction(theme_action)
        
        # Все справочники
        all_refs_action = QAction("📋 Все справочники", self)
        all_refs_action.setShortcut("Ctrl+R")
        all_refs_action.triggered.connect(self.open_reference_editor)
        ref_menu.addAction(all_refs_action)
        
        ref_menu.addSeparator()
        
        # Быстрый доступ к часто используемым справочникам
        categories_action = QAction("Категории военнослужащих", self)
        categories_action.triggered.connect(lambda: self.open_reference_editor("categories"))
        ref_menu.addAction(categories_action)
        
        ranks_action = QAction("Воинские звания", self)
        ranks_action.triggered.connect(lambda: self.open_reference_editor("ranks"))
        ref_menu.addAction(ranks_action)
        
        statuses_action = QAction("Статусы КРД", self)
        statuses_action.triggered.connect(lambda: self.open_reference_editor("statuses"))
        ref_menu.addAction(statuses_action)
        
        ref_menu.addSeparator()
        
        military_units_action = QAction("Военные управления", self)
        military_units_action.triggered.connect(lambda: self.open_reference_editor("military_units"))
        ref_menu.addAction(military_units_action)
        
        garrisons_action = QAction("Гарнизоны", self)
        garrisons_action.triggered.connect(lambda: self.open_reference_editor("garrisons"))
        ref_menu.addAction(garrisons_action)
        
        positions_action = QAction("Воинские должности", self)
        positions_action.triggered.connect(lambda: self.open_reference_editor("positions"))
        ref_menu.addAction(positions_action)
        
        ref_menu.addSeparator()
        
        request_types_action = QAction("Типы запросов", self)
        request_types_action.triggered.connect(lambda: self.open_reference_editor("request_types"))
        ref_menu.addAction(request_types_action)
        
        initiator_types_action = QAction("Типы инициаторов", self)
        initiator_types_action.triggered.connect(lambda: self.open_reference_editor("initiator_types"))
        ref_menu.addAction(initiator_types_action)
        
        # Меню "Отчеты" (только для администраторов)
        if self.user_info.get('role') == 'admin':
            reports_menu = menu_bar.addMenu("📊 Отчеты")
            
            # Управление шаблонами отчетов
            templates_action = QAction("⚙️ Управление шаблонами отчетов", self)
            templates_action.triggered.connect(self.on_manage_templates)
            reports_menu.addAction(templates_action)
            
            reports_menu.addSeparator()
            
            audit_action = QAction("Аудит действий пользователей", self)
            audit_action.triggered.connect(self.open_user_audit_window)
            reports_menu.addAction(audit_action)
        
        # Меню "Справка"
        help_menu = menu_bar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = self.addToolBar("Основная панель")

        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.load_krd_data)
        toolbar.addAction(refresh_action)

        add_krd_action = QAction("➕ Добавить КРД", self)
        add_krd_action.triggered.connect(self.open_krd_add_window)
        toolbar.addAction(add_krd_action)
        
        delete_krd_action = QAction("🗑️ Удалить КРД", self)
        delete_krd_action.triggered.connect(self.delete_selected_krd)
        delete_krd_action.setEnabled(False)
        toolbar.addAction(delete_krd_action)
        self.delete_krd_action = delete_krd_action
        
        # === РАЗДЕЛИТЕЛЬ ===
        toolbar.addSeparator()
        
        # === КНОПКИ ОТЧЕТОВ И СПРАВОЧНИКОВ (в одной группе) ===
        
        # Кнопка массового экспорта по всем КРД
        generate_all_action = QAction("📥 Отчеты по всем КРД", self)
        generate_all_action.setToolTip("Сгенерировать отчеты по всем КРД в базе данных с выбором шаблона")
        generate_all_action.triggered.connect(self.on_generate_all_reports)
        toolbar.addAction(generate_all_action)
        
        # === Кнопка справочников (ДОСТУПНО ВСЕМ ПОЛЬЗОВАТЕЛЯМ) ===
        ref_action = QAction("📚 Справочники", self)
        ref_action.setToolTip("Редактирование справочников системы")
        ref_action.triggered.connect(self.open_reference_editor)
        toolbar.addAction(ref_action)
        
        # === Административные функции (только для администраторов) ===
        if self.user_info.get('role') == 'admin':
            toolbar.addSeparator()
            
            deleted_records_action = QAction("📁 Удаленные записи", self)
            deleted_records_action.triggered.connect(self.open_deleted_records_window)
            toolbar.addAction(deleted_records_action)
            
            user_mgmt_action = QAction("👥 Управление пользователями", self)
            user_mgmt_action.triggered.connect(self.open_user_management)
            toolbar.addAction(user_mgmt_action)
            
            audit_action = QAction("📋 Аудит пользователей", self)
            audit_action.triggered.connect(self.open_user_audit_window)
            toolbar.addAction(audit_action)
            

    
    def create_status_bar(self):
        """Создание строки состояния"""
        status_bar = self.statusBar()
        status_bar.showMessage(f"Пользователь: {self.user_info['username']} | Роль: {self.user_info['role']}")
    
    def create_user_info_section(self):
        """Создание секции с информацией о пользователе"""
        group_box = QGroupBox("Информация о пользователе")
        layout = QGridLayout()
        
        username_label = QLabel(f"<b>Имя пользователя:</b> {self.user_info.get('username', 'N/A')}")
        full_name_label = QLabel(f"<b>ФИО:</b> {self.user_info.get('full_name', 'N/A')}")
        role_label = QLabel(f"<b>Роль:</b> {self.user_info.get('role', 'N/A')}")
        
        font = QFont()
        font.setBold(True)
        full_name_label.setFont(font)
        
        layout.addWidget(username_label, 0, 0)
        layout.addWidget(full_name_label, 0, 1)
        layout.addWidget(role_label, 1, 0, 1, 2)
        
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
        
        # === СТРОКА ПОИСКА ===
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Поиск:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите фамилию, имя, отчество или номер КРД...")
        self.search_input.setMinimumHeight(35)
       
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input)
        
        # Кнопка очистки поиска
        clear_search_btn = QPushButton("Очистить поиск")
        clear_search_btn.setProperty("role", "danger")
        clear_search_btn.setStyleSheet("")
        clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_search_btn)
        
        # Счётчик найденных записей
        self.found_count_label = QLabel("Найдено: 0 записей")
      
        search_layout.addWidget(self.found_count_label)
        
        layout.addLayout(search_layout)
        # ==========================
        
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
        WHERE k.is_deleted = FALSE
        ORDER BY k.id DESC"""
        
        self.load_krd_data()
        
        self.krd_table_view = QTableView()
        self.krd_table_view.setModel(self.table_model_krd)
        self.krd_table_view.setAlternatingRowColors(True)
        self.krd_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.krd_table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        
        # === ВКЛЮЧАЕМ СОРТИРОВКУ ПО ЗАГОЛОВКАМ ===
        header = self.krd_table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)  # Показывать индикатор сортировки
        header.setSortIndicator(self.sort_column, self.sort_order)  # Установить начальную сортировку
        header.setSectionsClickable(True)  # Разрешить клики по заголовкам
        header.sortIndicatorChanged.connect(self.on_sort_indicator_changed)  # Подключить сигнал
        # ===========================================
        
        self.krd_table_view.doubleClicked.connect(self.on_krd_double_clicked)
        
        selection_model = self.krd_table_view.selectionModel()
        selection_model.selectionChanged.connect(self.on_selection_changed)
        
        self.krd_table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.krd_table_view.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.krd_table_view)
        
        group_box.setLayout(layout)
        return group_box
    
    def open_theme_settings(self):
        from theme_settings_dialog import ThemeSettingsDialog
        dlg = ThemeSettingsDialog(self.theme_manager, self)
        if dlg.exec():
            # При необходимости обновить UI главного окна
            self.update()
    # === МЕТОД ДЛЯ ОБРАБОТКИ КЛИКА ПО ЗАГОЛОВКУ ===
    def on_sort_indicator_changed(self, logical_index, order):
        """
        Обработка изменения сортировки при клике на заголовок столбца
        
        Args:
            logical_index: Индекс столбца
            order: Порядок сортировки (Ascending/Descending)
        """
        self.sort_column = logical_index
        self.sort_order = order
        
        # Обновляем данные с новой сортировкой
        self.load_krd_data()
    # ===============================================
    
    def on_search_text_changed(self, text):
        """Обработка изменения текста в строке поиска"""
        self.search_query = text.strip()
        
        # Запускаем таймер для задержки поиска (debounce 300ms)
        self.search_timer.stop()
        self.search_timer.start(300)
    
    def _perform_search(self):
        """Выполнение поиска с задержкой"""
        self.load_krd_data()
    
    def clear_search(self):
        """Очистка строки поиска"""
        self.search_input.clear()
        self.search_query = ""
        self.load_krd_data()
        self.search_input.setFocus()
    
    def load_krd_data(self):
        """Загрузка данных КРД в таблицу с учётом поиска и сортировки"""
        query = QSqlQuery(self.db)
        
        # Определяем поле для сортировки
        sort_field = self.sort_column_names.get(self.sort_column, "k.id")
        sort_order = "ASC" if self.sort_order == Qt.SortOrder.AscendingOrder else "DESC"
        
        if self.search_query:
            # Поиск по фамилии, имени, отчеству или номеру КРД
            search_query = f"""
                SELECT
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
                WHERE k.is_deleted = FALSE
                AND (
                    LOWER(s.surname) LIKE LOWER(:search) OR
                    LOWER(s.name) LIKE LOWER(:search) OR
                    LOWER(s.patronymic) LIKE LOWER(:search) OR
                    LOWER(CONCAT('КРД-', k.id)) LIKE LOWER(:search) OR
                    LOWER(s.surname || ' ' || s.name || ' ' || s.patronymic) LIKE LOWER(:search)
                )
                ORDER BY {sort_field} {sort_order}
            """
            query.prepare(search_query)
            query.bindValue(":search", f"%{self.search_query}%")
        else:
            # Без поиска - все записи с сортировкой
            base_query = """SELECT
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
            WHERE k.is_deleted = FALSE
            ORDER BY {sort_field} {sort_order}"""
            
            query.prepare(base_query.format(sort_field=sort_field, sort_order=sort_order))
        
        if query.exec():
            self.table_model_krd.setQuery(query)
            
            # Обновляем счётчик найденных записей
            count = self.table_model_krd.rowCount()
            if self.search_query:
                self.found_count_label.setText(f"🔍 Найдено: {count} записей по запросу \"{self.search_query}\"")
           
            else:
                self.found_count_label.setText(f"📊 Всего записей: {count}")
             
        else:
            print(f"⚠️ Ошибка загрузки данных: {query.lastError().text()}")
            self.found_count_label.setText("⚠️ Ошибка загрузки данных")
    
    def on_selection_changed(self, selected, deselected):
        """Обработка изменения выделения в таблице"""
        has_selection = self.krd_table_view.selectionModel().hasSelection()
        self.delete_krd_action.setEnabled(has_selection)
    
    def show_context_menu(self, position: QPoint):
        """Показ контекстного меню при правом клике на таблице"""
        index = self.krd_table_view.indexAt(position)
        
        if not index.isValid():
            return
        
        menu = QMenu(self)
        
        open_action = QAction("Открыть", self)
        open_action.triggered.connect(lambda: self.on_krd_double_clicked(index))
        menu.addAction(open_action)
        
        delete_action = QAction("Удалить КРД", self)
        delete_action.triggered.connect(self.delete_selected_krd)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        export_action = QAction("📥 Сгенерировать отчеты по ВСЕМ КРД", self)
        export_action.triggered.connect(self.on_generate_all_reports)
        menu.addAction(export_action)
        
        menu.exec(self.krd_table_view.mapToGlobal(position))
    
    # ========================
    # === НОВЫЕ МЕТОДЫ ДЛЯ СПРАВОЧНИКОВ (ДОСТУПНО ВСЕМ) ===
    # ========================
    
    def open_reference_editor(self, initial_table=None):
        """
        Открытие редактора справочников
        ✅ ДОСТУПНО ВСЕМ ПОЛЬЗОВАТЕЛЯМ (не только администраторам)
        
        Args:
            initial_table: Имя таблицы для открытия (опционально)
        """
        try:
            from reference_editor_dialog import ReferenceEditorDialog
            
            dialog = ReferenceEditorDialog(self.db, self, initial_table)
            dialog.exec()
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии редактора справочников:\n{str(e)}")
    
    # ========================
    # === МЕТОДЫ ДЛЯ ГЕНЕРАЦИИ ОТЧЕТОВ ===
    # ========================
    
    def on_generate_all_reports(self):
        """
        Генерация отчетов по всем КРД в базе данных
        """
        try:
            dialog = ReportConfigDialog(self.db, self)
            dialog.report_configured.connect(lambda config: self._on_report_configured(config))
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                pass
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при подготовке отчета:\n{str(e)}")
    
    def _on_report_configured(self, config):
        """
        Обработка полученной конфигурации отчета
        
        Args:
            config: Словарь конфигурации отчета
        """
        krd_ids = config.get("krd_ids", [])
        
        # Диалог выбора файла для сохранения
        default_filename = f"КРД_ВСЕ_отчет_{QDate.currentDate().toString('yyyy-MM-dd')}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчеты по всем КРД",
            default_filename,
            "Excel файлы (*.xlsx);;Все файлы (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Показываем индикатор прогресса
            progress_msg = QProgressDialog("Генерация отчета...\nПожалуйста, подождите.", "Отмена", 0, 0, self)
            progress_msg.setWindowTitle("Генерация отчета")
            progress_msg.setWindowModality(Qt.WindowModality.WindowModal)
            progress_msg.show()
            QApplication.processEvents()
            
            # Создаем экспортер
            exporter = KrdExcelExporter(self.db, report_config=config)
            
            # Экспорт всех КРД на один лист
            exporter.export_multiple_krd_to_excel(file_path, krd_ids)
            
            progress_msg.close()
            
            message = (
                f"✅ Отчеты успешно сгенерированы и сохранены:\n\n"
                f"📊 Всего КРД: {len(krd_ids)}\n"
                f"📁 Файл: {file_path}\n\n"
                f"Все данные экспортированы на ОДИН лист в виде таблицы."
            )
            
            QMessageBox.information(self, "Успешно", message)
            
            # Логирование
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='REPORT_EXPORT',
                    table_name='krd',
                    record_id=None,
                    krd_id=None,
                    description=f'Экспортирован отчет для {len(krd_ids)} КРД в {file_path}'
                )
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"❌ Ошибка при генерации отчета:\n\n{str(e)}")
    
    def on_manage_templates(self):
        """Открытие управления шаблонами"""
        try:
            dialog = ReportConfigDialog(self.db, self)
            # Убрано обращение к dialog.tabs, так как в ReportConfigDialog нет вкладок
            dialog.exec()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии шаблонов:\n{str(e)}")
    
    # ========================
    # === СУЩЕСТВУЮЩИЕ МЕТОДЫ ===
    # ========================
    
    def delete_selected_krd(self):
        """Мягкое удаление выбранной записи КРД (помечает как удалённую, не удаляет из БД)"""
        selection_model = self.krd_table_view.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Внимание", "Выберите КРД для удаления")
            return
        
        selected_indexes = selection_model.selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Внимание", "Выберите КРД для удаления")
            return
        
        index = selected_indexes[0]
        
        krd_id = self.table_model_krd.data(self.table_model_krd.index(index.row(), 0))
        krd_number = self.table_model_krd.data(self.table_model_krd.index(index.row(), 1))
        surname = self.table_model_krd.data(self.table_model_krd.index(index.row(), 2))
        name = self.table_model_krd.data(self.table_model_krd.index(index.row(), 3))
        patronymic = self.table_model_krd.data(self.table_model_krd.index(index.row(), 4))
        
        full_name = f"{surname} {name} {patronymic}".strip()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить КРД?\n\n"
            f"Номер КРД: {krd_number}\n"
            f"Военнослужащий: {full_name}\n\n"
            f"⚠️ Внимание: Запись будет скрыта из списка, но сохранена в базе данных.\n"
            f"Восстановить можно через меню '📁 Удаленные записи' (только для администраторов).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # ✅ СОХРАНЯЕМ СТАРЫЕ ДАННЫЕ ДЛЯ АУДИТА
                query_data = QSqlQuery(self.db)
                query_data.prepare("SELECT s.* FROM krd.social_data s WHERE s.krd_id = ?")
                query_data.addBindValue(krd_id)
                query_data.exec()
                
                old_data = {}
                if query_data.next():
                    for i in range(query_data.record().count()):
                        field_name = query_data.record().fieldName(i)
                        old_data[field_name] = query_data.value(i)
                
                if not self.db.transaction():
                    raise Exception(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
                
                # ✅ ИСПРАВЛЕНО: МЯГКОЕ УДАЛЕНИЕ (UPDATE вместо DELETE)
                query = QSqlQuery(self.db)
                query.prepare("""
                    UPDATE krd.krd 
                    SET is_deleted = TRUE, 
                        deleted_at = CURRENT_TIMESTAMP,
                        deleted_by = :user_id
                    WHERE id = :id
                """)
                query.bindValue(":user_id", self.user_info.get('id'))
                query.bindValue(":id", krd_id)
                
                if not query.exec():
                    raise Exception(f"Ошибка при удалении КРД: {query.lastError().text()}")
                
                if query.numRowsAffected() == 0:
                    raise Exception("Запись не найдена или уже удалена")
                
                if not self.db.commit():
                    raise Exception(f"Ошибка при коммите транзакции: {self.db.lastError().text()}")
                
                # ✅ ЛОГИРОВАНИЕ МЯГКОГО УДАЛЕНИЯ
                self.audit_logger.log_krd_delete(krd_id, old_data)
                
                QMessageBox.information(
                    self, 
                    "Успех", 
                    f"✅ КРД №{krd_number} успешно скрыт!\n\n"
                    f"Запись сохранена в базе данных.\n"
                    f"Восстановить можно через меню администратора '📁 Удаленные записи'."
                )
                self.load_krd_data()
                
            except Exception as e:
                self.db.rollback()
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении КРД:\n{str(e)}")
    
    def open_krd_add_window(self):
        """Открытие окна добавления КРД"""
        krd_add_window = AddKrdWindow(self.db)
        if krd_add_window.exec() == QDialog.DialogCode.Accepted:
            self.load_krd_data()
    
    def open_user_management(self):
        """Открытие окна управления пользователями"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        from admin_user_management_tab import AdminUserManagementTab
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление пользователями")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        user_mgmt_tab = AdminUserManagementTab(self.db)
        layout.addWidget(user_mgmt_tab)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def on_krd_double_clicked(self, index):
        """Обработка двойного клика по строке в таблице КРД"""
        krd_id = self.table_model_krd.data(self.table_model_krd.index(index.row(), 0))

        if krd_id:
            self.audit_logger.log_krd_view(int(krd_id))
            
            from krd_details_window import KrdDetailsWindow
            details_window = KrdDetailsWindow(int(krd_id), self.db, self.audit_logger)

            if details_window.exec() == QDialog.DialogCode.Accepted:
                self.load_krd_data()
    
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
        """Обработчик закрытия окна"""
        self.audit_logger.log_user_logout()
        super().closeEvent(event)
    
    def open_user_audit_window(self):
        """Открытие окна аудита действий пользователей"""
        from user_audit_window import UserAuditWindow
        
        audit_window = UserAuditWindow(self.db, self.user_info.get('id'))
        audit_window.exec()
    
    def open_deleted_records_window(self):
        """Открытие окна удаленных записей"""
        from deleted_records_window import DeletedRecordsWindow
        
        deleted_window = DeletedRecordsWindow(self.db)
        deleted_window.exec()


def main():
    """Тестовая функция для демонстрации главного окна"""
    app = QApplication(sys.argv)
    
    db = QSqlDatabase.addDatabase("QPSQL")
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")
    
    if not db.open():
        QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных:\n{db.lastError().text()}")
        sys.exit(1)
    
    user_info = {
        'id': 1,
        'username': 'test_user',
        'full_name': 'Иванов Иван Иванович',
        'role': 'Сотрудник'
    }
    
    main_window = MainWindow(user_info, db)
    main_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()