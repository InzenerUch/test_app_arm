"""
Модуль для просмотра аудита действий пользователей
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QComboBox, QTableView, QPushButton, QLabel, QDateEdit,
    QMessageBox, QHeaderView, QAbstractItemView, QSplitter, QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery
from PyQt6.QtGui import QFont


class UserAuditWindow(QDialog):
    """
    Окно для просмотра аудита действий пользователей
    Доступно только для администраторов
    """
    
    def __init__(self, db_connection, current_user_id=None):
        """
        Инициализация окна аудита
        
        Args:
            db_connection: соединение с базой данных
            current_user_id: ID текущего пользователя (для фильтрации по умолчанию)
        """
        super().__init__()
        self.db = db_connection
        self.current_user_id = current_user_id
        
        self.setWindowTitle("Аудит действий пользователей")
        self.resize(1200, 700)
        
        self.init_ui()
        self.load_users()
        self.load_audit_data()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_layout = QVBoxLayout()
        
        # Верхняя панель с фильтрами
        filters_group = self.create_filters_section()
        main_layout.addWidget(filters_group)
        
        # Разделитель
        separator = self.create_separator()
        main_layout.addWidget(separator)
        
        # Основная область с таблицей аудита
        audit_group = self.create_audit_section()
        main_layout.addWidget(audit_group, 1)
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        
        export_button = QPushButton("Экспортировать отчет")
        export_button.clicked.connect(self.export_report)
        buttons_layout.addWidget(export_button)
        
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_audit_data)
        buttons_layout.addWidget(refresh_button)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)
        
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
    
    def create_filters_section(self):
        """Создание секции с фильтрами"""
        group_box = QGroupBox("Фильтры")
        layout = QGridLayout()
        
        # Выбор пользователя
        layout.addWidget(QLabel("Пользователь:"), 0, 0)
        self.user_combo = QComboBox()
        self.user_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.user_combo, 0, 1)
        
        # Выбор типа действия
        layout.addWidget(QLabel("Тип действия:"), 0, 2)
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItem("Все действия", "")
        self.action_type_combo.addItem("Создание", "CREATE")
        self.action_type_combo.addItem("Обновление", "UPDATE")
        self.action_type_combo.addItem("Удаление", "DELETE")
        self.action_type_combo.addItem("Просмотр", "VIEW")
        self.action_type_combo.addItem("Вход в систему", "LOGIN")
        self.action_type_combo.addItem("Выход из системы", "LOGOUT")
        self.action_type_combo.addItem("Генерация документа", "DOCUMENT_GENERATE")
        self.action_type_combo.addItem("Сохранение документа", "DOCUMENT_SAVE")
        self.action_type_combo.addItem("Создание шаблона", "TEMPLATE_CREATE")
        self.action_type_combo.addItem("Обновление шаблона", "TEMPLATE_UPDATE")
        self.action_type_combo.addItem("Удаление шаблона", "TEMPLATE_DELETE")
        self.action_type_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.action_type_combo, 0, 3)
        
        # Дата начала
        layout.addWidget(QLabel("Дата от:"), 1, 0)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))  # По умолчанию - 30 дней
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.date_from, 1, 1)
        
        # Дата окончания
        layout.addWidget(QLabel("Дата до:"), 1, 2)
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.date_to, 1, 3)
        
        group_box.setLayout(layout)
        return group_box
    
    def create_separator(self):
        """Создание разделителя"""
        separator = QWidget()
        separator.setFixedHeight(10)
        return separator
    
    def create_audit_section(self):
        """Создание секции с таблицей аудита"""
        group_box = QGroupBox("История действий")
        layout = QVBoxLayout()
        
        # Создаем модель для таблицы аудита
        self.audit_model = QSqlQueryModel()
        
        # Создаем таблицу
        self.audit_table = QTableView()
        self.audit_table.setModel(self.audit_model)
        self.audit_table.setAlternatingRowColors(True)
        self.audit_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.audit_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Настройка заголовков
        header = self.audit_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        # Установка ширины колонок
        self.audit_table.setColumnWidth(0, 150)  # Дата и время
        self.audit_table.setColumnWidth(1, 150)  # Пользователь
        self.audit_table.setColumnWidth(2, 180)  # Тип действия
        self.audit_table.setColumnWidth(3, 150)  # Таблица
        self.audit_table.setColumnWidth(4, 80)   # ID записи
        self.audit_table.setColumnWidth(5, 80)   # ID КРД
        
        layout.addWidget(self.audit_table)
        group_box.setLayout(layout)
        
        return group_box
    
    def load_users(self):
        """Загрузка списка пользователей"""
        self.user_combo.clear()
        
        # Добавляем опцию "Все пользователи"
        self.user_combo.addItem("Все пользователи", 0)
        
        query = QSqlQuery(self.db)
        query.exec("""
            SELECT id, username, full_name 
            FROM krd.users 
            ORDER BY username
        """)
        
        while query.next():
            user_id = query.value(0)
            username = query.value(1)
            full_name = query.value(2)
            
            # Формируем отображаемое имя
            display_name = f"{username} - {full_name}"
            
            self.user_combo.addItem(display_name, user_id)
        
        # Если указан текущий пользователь, выбираем его
        if self.current_user_id:
            index = self.user_combo.findData(self.current_user_id)
            if index >= 0:
                self.user_combo.setCurrentIndex(index)
    
    def load_audit_data(self):
        """Загрузка данных аудита с применением фильтров"""
        # Получаем параметры фильтрации
        user_id = self.user_combo.currentData()
        action_type = self.action_type_combo.currentData()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        # Формируем SQL-запрос
        query_parts = [
            "SELECT ",
            "    al.created_at as \"Дата и время\",",
            "    al.username as \"Пользователь\",",
            "    al.action_type as \"Тип действия\",",
            "    al.table_name as \"Таблица\",",
            "    al.record_id as \"ID записи\",",
            "    al.krd_id as \"ID КРД\",",
            "    al.description as \"Описание\"",
            "FROM krd.audit_log al",
            "WHERE 1=1"
        ]
        
        params = []
        
        # Фильтр по пользователю
        if user_id and user_id > 0:
            query_parts.append("AND al.user_id = ?")
            params.append(user_id)
        
        # Фильтр по типу действия
        if action_type:
            query_parts.append("AND al.action_type = ?")
            params.append(action_type)
        
        # Фильтр по дате
        query_parts.append("AND al.created_at >= ?")
        params.append(date_from)
        
        query_parts.append("AND al.created_at <= ?")
        params.append(f"{date_to} 23:59:59")
        
        # Сортировка
        query_parts.append("ORDER BY al.created_at DESC")
        
        # Ограничение количества записей
        query_parts.append("LIMIT 1000")
        
        query_str = " ".join(query_parts)
        
        # Выполняем запрос
        query = QSqlQuery(self.db)
        query.prepare(query_str)
        
        for param in params:
            query.addBindValue(param)
        
        if not query.exec():
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Ошибка выполнения запроса:\n{query.lastError().text()}"
            )
            return
        
        # Устанавливаем результаты в модель
        self.audit_model.setQuery(query)
        
        # Обновляем заголовок окна
        record_count = self.audit_model.rowCount()
        self.setWindowTitle(f"Аудит действий пользователей - {record_count} записей")
    
    def on_filter_changed(self):
        """Обработчик изменения фильтров"""
        self.load_audit_data()
    
    def export_report(self):
        """Экспорт отчета в файл"""
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime
        
        # Формируем имя файла по умолчанию
        default_filename = f"Аудит_пользователей_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Диалог сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспортировать отчет",
            default_filename,
            "CSV файлы (*.csv);;Все файлы (*)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.csv'):
                self.export_to_csv(file_path)
            else:
                QMessageBox.warning(self, "Предупреждение", "Поддерживается только формат CSV")
                return
            
            QMessageBox.information(
                self,
                "Успех",
                f"Отчет успешно экспортирован:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Ошибка экспорта отчета:\n{str(e)}"
            )
    
    def export_to_csv(self, file_path):
        """Экспорт данных в CSV файл"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Записываем заголовки
            headers = []
            for col in range(self.audit_model.columnCount()):
                headers.append(self.audit_model.headerData(col, Qt.Orientation.Horizontal))
            writer.writerow(headers)
            
            # Записываем данные
            for row in range(self.audit_model.rowCount()):
                row_data = []
                for col in range(self.audit_model.columnCount()):
                    value = self.audit_model.data(self.audit_model.index(row, col))
                    row_data.append(str(value) if value is not None else "")
                writer.writerow(row_data)