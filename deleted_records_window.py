"""
Модуль для просмотра удаленных записей (только для администраторов)
✅ ИСПРАВЛЕНО: Использованы именованные параметры для UNION запроса
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QComboBox, QTableView, QPushButton, QLabel, QDateEdit,
    QMessageBox, QHeaderView, QAbstractItemView, QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery
from PyQt6.QtGui import QFont
import traceback


class DeletedRecordsWindow(QDialog):
    """
    Окно для просмотра удаленных записей (только для администраторов)
    """
    
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        
        self.setWindowTitle("Удаленные записи")
        self.resize(1200, 700)
        
        self.init_ui()
        self.load_deleted_records()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_layout = QVBoxLayout()
        
        # Верхняя панель с фильтрами
        filters_group = self.create_filters_section()
        main_layout.addWidget(filters_group)
        
        # Разделитель
        separator = self.create_separator()
        main_layout.addWidget(separator)
        
        # Основная область с таблицей удаленных записей
        records_group = self.create_records_section()
        main_layout.addWidget(records_group, 1)
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        
        restore_button = QPushButton("Восстановить выбранную запись")
        restore_button.setStyleSheet("background-color: #4CAF50; color: white;")
        restore_button.clicked.connect(self.restore_selected_record)
        buttons_layout.addWidget(restore_button)
        
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_deleted_records)
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
        
        # Выбор типа записей
        layout.addWidget(QLabel("Тип записей:"), 0, 0)
        self.record_type_combo = QComboBox()
        self.record_type_combo.addItem("Все удаленные записи", "all")
        self.record_type_combo.addItem("Удаленные КРД", "krd")
        self.record_type_combo.addItem("Удаленные шаблоны", "templates")
        self.record_type_combo.addItem("Удаленные запросы", "requests")
        self.record_type_combo.currentIndexChanged.connect(self.on_filter_changed)
        layout.addWidget(self.record_type_combo, 0, 1)
        
        # Дата удаления от
        layout.addWidget(QLabel("Дата удаления от:"), 1, 0)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-90))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.on_filter_changed)
        layout.addWidget(self.date_from, 1, 1)
        
        # Дата удаления до
        layout.addWidget(QLabel("Дата удаления до:"), 1, 2)
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
    
    def create_records_section(self):
        """Создание секции с таблицей удаленных записей"""
        group_box = QGroupBox("Удаленные записи")
        layout = QVBoxLayout()
        
        # Создаем модель для таблицы
        self.records_model = QSqlQueryModel()
        
        # Создаем таблицу
        self.records_table = QTableView()
        self.records_table.setModel(self.records_model)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.records_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Настройка заголовков
        header = self.records_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.records_table)
        group_box.setLayout(layout)
        
        return group_box
    
    # В файле deleted_records_window.py, метод load_deleted_records:

    def load_deleted_records(self):
        """Загрузка удаленных записей с применением фильтров и обработкой ошибок"""
        record_type = self.record_type_combo.currentData()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        
        try:
            if record_type == "krd":
                # Загрузка удаленных КРД
                query = QSqlQuery(self.db)
                query.prepare("""
                    SELECT
                        k.id as "ID КРД",
                        CONCAT('КРД-', k.id) as "Номер КРД",
                        COALESCE(s.surname, '') || ' ' || COALESCE(s.name, '') || ' ' || COALESCE(s.patronymic, '') as "ФИО",
                        k.deleted_at as "Дата удаления"
                    FROM krd.krd k
                    LEFT JOIN krd.social_data s ON k.id = s.krd_id
                    WHERE k.is_deleted = TRUE
                    AND k.deleted_at >= :date_from
                    AND k.deleted_at <= :date_to
                    ORDER BY k.deleted_at DESC
                """)
                query.bindValue(":date_from", date_from)
                query.bindValue(":date_to", f"{date_to} 23:59:59")
                
                if not query.exec():
                    raise Exception(f"Ошибка выполнения запроса: {query.lastError().text()}")
                
                self.records_model.setQuery(query)
                # ... rest of the code

            elif record_type == "templates":
                # Загрузка удаленных шаблонов
                query = QSqlQuery(self.db)
                query.prepare("""
                    SELECT
                        dt.id as "ID шаблона",
                        dt.name as "Название шаблона",
                        dt.description as "Описание",
                        dt.deleted_at as "Дата удаления"
                    FROM krd.document_templates dt
                    WHERE dt.is_deleted = TRUE
                    AND dt.deleted_at >= :date_from
                    AND dt.deleted_at <= :date_to
                    ORDER BY dt.deleted_at DESC
                """)
                query.bindValue(":date_from", date_from)
                query.bindValue(":date_to", f"{date_to} 23:59:59")
                
                if not query.exec():
                    raise Exception(f"Ошибка выполнения запроса: {query.lastError().text()}")
                
                self.records_model.setQuery(query)
                # ... rest of the code

            elif record_type == "requests":
                # Загрузка удаленных исходящих запросов
                query = QSqlQuery(self.db)
                query.prepare("""
                    SELECT
                        o.id as "ID запроса",
                        o.issue_number as "Номер запроса",
                        rt.name as "Тип запроса",
                        o.recipient_name as "Адресат",
                        o.issue_date as "Дата запроса",
                        o.deleted_at as "Дата удаления"
                    FROM krd.outgoing_requests o
                    LEFT JOIN krd.request_types rt ON o.request_type_id = rt.id
                    WHERE o.is_deleted = TRUE
                    AND o.deleted_at >= :date_from
                    AND o.deleted_at <= :date_to
                    ORDER BY o.deleted_at DESC
                """)
                query.bindValue(":date_from", date_from)
                query.bindValue(":date_to", f"{date_to} 23:59:59")
                
                if not query.exec():
                    raise Exception(f"Ошибка выполнения запроса: {query.lastError().text()}")
                
                self.records_model.setQuery(query)
                # ... rest of the code

            else:
                # Загрузка всех удаленных записей
                query = QSqlQuery(self.db)
                query.prepare("""
                    SELECT
                        'КРД' as "Тип",
                        k.id::text as "ID записи",
                        CONCAT('КРД-', k.id) as "Идентификатор",
                        COALESCE(s.surname, '') || ' ' || COALESCE(s.name, '') || ' ' || COALESCE(s.patronymic, '') as "Название",
                        k.deleted_at as "Дата удаления"
                    FROM krd.krd k
                    LEFT JOIN krd.social_data s ON k.id = s.krd_id
                    WHERE k.is_deleted = TRUE
                    AND k.deleted_at >= :date_from
                    AND k.deleted_at <= :date_to
                    UNION ALL
                    SELECT
                        'Шаблон' as "Тип",
                        dt.id::text as "ID записи",
                        dt.name as "Идентификатор",
                        dt.description as "Название",
                        dt.deleted_at as "Дата удаления"
                    FROM krd.document_templates dt
                    WHERE dt.is_deleted = TRUE
                    AND dt.deleted_at >= :date_from
                    AND dt.deleted_at <= :date_to
                    UNION ALL
                    SELECT
                        'Запрос' as "Тип",
                        o.id::text as "ID записи",
                        o.issue_number as "Идентификатор",
                        rt.name || ' → ' || o.recipient_name as "Название",
                        o.deleted_at as "Дата удаления"
                    FROM krd.outgoing_requests o
                    LEFT JOIN krd.request_types rt ON o.request_type_id = rt.id
                    WHERE o.is_deleted = TRUE
                    AND o.deleted_at >= :date_from
                    AND o.deleted_at <= :date_to
                    ORDER BY "Дата удаления" DESC
                """)
                query.bindValue(":date_from", date_from)
                query.bindValue(":date_to", f"{date_to} 23:59:59")
                query.bindValue(":date_from", date_from)
                query.bindValue(":date_to", f"{date_to} 23:59:59")
                query.bindValue(":date_from", date_from)
                query.bindValue(":date_to", f"{date_to} 23:59:59")
                
                if not query.exec():
                    raise Exception(f"Ошибка выполнения запроса: {query.lastError().text()}")
                
                self.records_model.setQuery(query)
                # ... rest of the code
                
        except Exception as e:
            error_msg = f"Ошибка загрузки удаленных записей:\n{str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "Критическая ошибка", error_msg)
          
    
    def on_filter_changed(self):
        """Обработчик изменения фильтров"""
        self.load_deleted_records()
    
    def restore_selected_record(self):
        """Восстановление выбранной записи"""
        selection_model = self.records_table.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Внимание", "Выберите запись для восстановления")
            return
        
        selected_indexes = selection_model.selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Внимание", "Выберите запись для восстановления")
            return
        
        index = selected_indexes[0]
        
        # Определяем тип записи
        record_type = self.record_type_combo.currentData()
        
        if record_type == "krd":
            # Восстановление КРД
            krd_id = self.records_model.data(self.records_model.index(index.row(), 0))
            krd_number = self.records_model.data(self.records_model.index(index.row(), 1))
            
            reply = QMessageBox.question(
                self,
                "Подтверждение восстановления",
                f"Вы действительно хотите восстановить КРД?\n\n"
                f"Номер КРД: {krd_number}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    query = QSqlQuery(self.db)
                    query.prepare("""
                        UPDATE krd.krd 
                        SET is_deleted = FALSE, 
                            deleted_at = NULL,
                            deleted_by = NULL
                        WHERE id = ?
                    """)
                    query.addBindValue(krd_id)
                    
                    if not query.exec():
                        raise Exception(f"Ошибка при восстановлении КРД: {query.lastError().text()}")
                    
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"КРД №{krd_number} успешно восстановлен!"
                    )
                    
                    self.load_deleted_records()
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Ошибка при восстановлении КРД:\n{str(e)}"
                    )
        
        elif record_type == "templates":
            # Восстановление шаблона
            template_id = self.records_model.data(self.records_model.index(index.row(), 0))
            template_name = self.records_model.data(self.records_model.index(index.row(), 1))
            
            reply = QMessageBox.question(
                self,
                "Подтверждение восстановления",
                f"Вы действительно хотите восстановить шаблон?\n\n"
                f"Название: {template_name}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    query = QSqlQuery(self.db)
                    query.prepare("""
                        UPDATE krd.document_templates 
                        SET is_deleted = FALSE, 
                            deleted_at = NULL,
                            deleted_by = NULL
                        WHERE id = ?
                    """)
                    query.addBindValue(template_id)
                    
                    if not query.exec():
                        raise Exception(f"Ошибка при восстановлении шаблона: {query.lastError().text()}")
                    
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Шаблон \"{template_name}\" успешно восстановлен!"
                    )
                    
                    self.load_deleted_records()
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Ошибка при восстановлении шаблона:\n{str(e)}"
                    )
        
        elif record_type == "requests":
            # Восстановление запроса
            request_id = self.records_model.data(self.records_model.index(index.row(), 0))
            issue_number = self.records_model.data(self.records_model.index(index.row(), 1))
            
            reply = QMessageBox.question(
                self,
                "Подтверждение восстановления",
                f"Вы действительно хотите восстановить запрос?\n\n"
                f"Номер запроса: {issue_number}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    query = QSqlQuery(self.db)
                    query.prepare("""
                        UPDATE krd.outgoing_requests 
                        SET is_deleted = FALSE, 
                            deleted_at = NULL,
                            deleted_by = NULL
                        WHERE id = ?
                    """)
                    query.addBindValue(request_id)
                    
                    if not query.exec():
                        raise Exception(f"Ошибка при восстановлении запроса: {query.lastError().text()}")
                    
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Запрос №{issue_number} успешно восстановлен!"
                    )
                    
                    self.load_deleted_records()
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Ошибка при восстановлении запроса:\n{str(e)}"
                    )
        
        else:
            # Автоматическое определение типа записи
            record_type_text = self.records_model.data(self.records_model.index(index.row(), 0))
            record_id = self.records_model.data(self.records_model.index(index.row(), 1))
            record_name = self.records_model.data(self.records_model.index(index.row(), 2))
            
            reply = QMessageBox.question(
                self,
                "Подтверждение восстановления",
                f"Вы действительно хотите восстановить запись?\n\n"
                f"Тип: {record_type_text}\n"
                f"Идентификатор: {record_name}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if record_type_text == "КРД":
                        query = QSqlQuery(self.db)
                        query.prepare("""
                            UPDATE krd.krd 
                            SET is_deleted = FALSE, 
                                deleted_at = NULL,
                                deleted_by = NULL
                            WHERE id = ?
                        """)
                        query.addBindValue(record_id)
                    elif record_type_text == "Шаблон":
                        query = QSqlQuery(self.db)
                        query.prepare("""
                            UPDATE krd.document_templates 
                            SET is_deleted = FALSE, 
                                deleted_at = NULL,
                                deleted_by = NULL
                            WHERE id = ?
                        """)
                        query.addBindValue(record_id)
                    else:  # Запрос
                        query = QSqlQuery(self.db)
                        query.prepare("""
                            UPDATE krd.outgoing_requests 
                            SET is_deleted = FALSE, 
                                deleted_at = NULL,
                                deleted_by = NULL
                            WHERE id = ?
                        """)
                        query.addBindValue(record_id)
                    
                    if not query.exec():
                        raise Exception(f"Ошибка при восстановлении записи: {query.lastError().text()}")
                    
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Запись успешно восстановлена!"
                    )
                    
                    self.load_deleted_records()
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Ошибка при восстановлении записи:\n{str(e)}"
                    )