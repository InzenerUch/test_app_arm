"""
Модуль для генерации документов из Word-шаблонов
"""

import os
import tempfile
from docxtpl import DocxTemplate
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QGroupBox, QFileDialog, QMessageBox, QComboBox, QTabWidget, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont, QStandardItemModel
import json
from datetime import datetime


class ComboBoxDelegate(QStyledItemDelegate):
    """
    Делегат для отображения QComboBox в ячейках таблицы
    """
    
    def __init__(self, options, parent=None):
        super().__init__(parent)
        self.options = options
    
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(self.options)
        return combo
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class DocumentGeneratorTab(QWidget):
    """
    Вкладка для генерации документов из Word-шаблонов
    """
    
    def __init__(self, krd_id, db_connection):
        """
        Инициализация вкладки генерации документов
        
        Args:
            krd_id (int): ID КРД
            db_connection: соединение с базой данных
        """
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        
        # Загружаем переменные из шаблона и столбцы из базы данных
        self.template_variables = []
        self.db_columns = {}
        
        self.init_ui()
        self.load_document_templates()
    
    def init_ui(self):
        """
        Инициализация пользовательского интерфейса
        """
        layout = QVBoxLayout()
        
        # Создаем вкладки
        tabs = QTabWidget()
        
        # Вкладка для генерации документов
        generate_widget = self.create_generate_tab()
        tabs.addTab(generate_widget, "Генерация документов")
        
        # Вкладка для управления шаблонами
        templates_widget = self.create_templates_tab()
        tabs.addTab(templates_widget, "Управление шаблонами")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def create_generate_tab(self):
        """
        Создание вкладки генерации документов
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Заголовок
        title_label = QLabel("Генерация документов из шаблонов")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Выбор шаблона
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Шаблон документа:"))
        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)
        
        # Таблица сопоставления полей
        mapping_group = QGroupBox("Сопоставление полей")
        mapping_layout = QVBoxLayout()
        
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Переменная из шаблона", "Столбец из базы данных"])
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        mapping_layout.addWidget(self.mapping_table)
        
        # Кнопки управления сопоставлением
        mapping_buttons_layout = QHBoxLayout()
        
        add_mapping_button = QPushButton("Добавить сопоставление")
        add_mapping_button.clicked.connect(self.add_field_mapping)
        mapping_buttons_layout.addWidget(add_mapping_button)
        
        remove_mapping_button = QPushButton("Удалить сопоставление")
        remove_mapping_button.clicked.connect(self.remove_field_mapping)
        mapping_buttons_layout.addWidget(remove_mapping_button)
        
        mapping_layout.addLayout(mapping_buttons_layout)
        
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        generate_button = QPushButton("Сформировать документ")
        generate_button.clicked.connect(self.generate_document)
        button_layout.addWidget(generate_button)
        
        save_button = QPushButton("Сохранить документ")
        save_button.clicked.connect(self.save_document)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_templates_tab(self):
        """
        Создание вкладки управления шаблонами
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Заголовок
        title_label = QLabel("Управление шаблонами документов")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Форма добавления шаблона
        add_template_group = QGroupBox("Добавить новый шаблон")
        add_template_layout = QVBoxLayout()
        
        # Поля ввода
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название:"))
        self.template_name_input = QLineEdit()
        name_layout.addWidget(self.template_name_input)
        add_template_layout.addLayout(name_layout)
        
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Описание:"))
        self.template_desc_input = QLineEdit()
        desc_layout.addWidget(self.template_desc_input)
        add_template_layout.addLayout(desc_layout)
        
        # Кнопка выбора файла
        file_layout = QHBoxLayout()
        self.selected_file_label = QLabel("Файл не выбран")
        select_file_button = QPushButton("Выбрать файл шаблона")
        select_file_button.clicked.connect(self.select_template_file)
        file_layout.addWidget(select_file_button)
        file_layout.addWidget(self.selected_file_label)
        add_template_layout.addLayout(file_layout)
        
        # Кнопка добавления
        add_button = QPushButton("Добавить шаблон")
        add_button.clicked.connect(self.add_template)
        add_template_layout.addWidget(add_button)
        
        add_template_group.setLayout(add_template_layout)
        layout.addWidget(add_template_group)
        
        # Список существующих шаблонов
        templates_list_group = QGroupBox("Существующие шаблоны")
        templates_list_layout = QVBoxLayout()
        
        self.templates_list = QTextEdit()
        self.templates_list.setMaximumHeight(150)
        self.templates_list.setReadOnly(True)
        templates_list_layout.addWidget(self.templates_list)
        
        refresh_button = QPushButton("Обновить список")
        refresh_button.clicked.connect(self.refresh_templates_list)
        templates_list_layout.addWidget(refresh_button)
        
        templates_list_group.setLayout(templates_list_layout)
        layout.addWidget(templates_list_group)
        
        return widget
    
    def select_template_file(self):
        """
        Выбор файла шаблона
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл шаблона",
            "",
            "Word документы (*.docx);;Все файлы (*)"
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.selected_file_label.setText(os.path.basename(file_path))
    
    def add_template(self):
        """
        Добавление нового шаблона в базу данных
        """
        name = self.template_name_input.text().strip()
        description = self.template_desc_input.text().strip()
        
        if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
            QMessageBox.warning(self, "Ошибка", "Выберите файл шаблона")
            return
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название шаблона")
            return
        
        try:
            # Читаем файл шаблона
            with open(self.selected_file_path, 'rb') as file:
                template_data = file.read()
            
            # Добавляем шаблон в базу данных
            query = QSqlQuery(self.db)
            query.prepare("""
                INSERT INTO krd.document_templates (name, description, template_data)
                VALUES (:name, :description, :template_data)
            """)
            query.bindValue(":name", name)
            query.bindValue(":description", description)
            query.bindValue(":template_data", QByteArray(template_data))
            
            if not query.exec():
                raise Exception(f"Ошибка при добавлении шаблона: {query.lastError().text()}")
            
            QMessageBox.information(self, "Успех", "Шаблон успешно добавлен")
            
            # Очищаем поля
            self.template_name_input.clear()
            self.template_desc_input.clear()
            self.selected_file_label.setText("Файл не выбран")
            if hasattr(self, 'selected_file_path'):
                delattr(self, 'selected_file_path')
            
            # Обновляем список шаблонов
            self.load_document_templates()
            self.refresh_templates_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении шаблона:\n{str(e)}")
    
    def refresh_templates_list(self):
        """
        Обновление списка шаблонов
        """
        query = QSqlQuery(self.db)
        query.exec("""
            SELECT id, name, description, created_at
            FROM krd.document_templates
            ORDER BY created_at DESC
        """)
        
        templates_text = "Список шаблонов:\n"
        while query.next():
            template_id = query.value(0)
            name = query.value(1)
            description = query.value(2)
            created_at = query.value(3)
            templates_text += f"\nID: {template_id}\nНазвание: {name}\nОписание: {description}\nДата создания: {created_at}\n{'-'*40}\n"
        
        self.templates_list.setPlainText(templates_text)
    
    def load_document_templates(self):
        """
        Загрузка доступных шаблонов документов из базы данных
        """
        self.template_combo.clear()
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.document_templates ORDER BY name")
        
        while query.next():
            template_id = query.value(0)
            template_name = query.value(1)
            self.template_combo.addItem(template_name, template_id)
    
    def on_template_changed(self):
        """
        Обработка изменения выбранного шаблона
        """
        template_id = self.template_combo.currentData()
        if template_id:
            self.load_field_mappings(template_id)
    
    def load_field_mappings(self, template_id):
        """
        Загрузка сопоставления полей для выбранного шаблона
        """
        # Очищаем таблицу
        self.mapping_table.setRowCount(0)
        
        # Загружаем переменные из шаблона и столбцы из базы данных
        self.load_template_variables(template_id)
        self.load_db_columns()
        
        # Устанавливаем делегаты для выпадающих списков
        self.setup_combobox_delegates()
        
        # Загружаем существующие сопоставления из базы данных
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT field_name, db_column, table_name
            FROM krd.field_mappings
            WHERE template_id = ?
            ORDER BY field_name
        """)
        query.addBindValue(template_id)
        query.exec()
        
        row = 0
        while query.next():
            field_name = query.value(0)
            db_column = query.value(1)
            
            # Добавляем строку в таблицу
            self.mapping_table.insertRow(row)
            
            # Создаем комбобоксы для ячеек
            var_combo = QComboBox()
            var_combo.addItems(self.template_variables)
            var_combo.setCurrentText(field_name)
            self.mapping_table.setCellWidget(row, 0, var_combo)
            
            col_combo = QComboBox()
            # Заполняем столбцы из соответствующей таблицы
            table_name = query.value(2)
            if table_name in self.db_columns:
                col_combo.addItems(self.db_columns[table_name])
            col_combo.setCurrentText(db_column)
            self.mapping_table.setCellWidget(row, 1, col_combo)
            
            row += 1
    
    def load_template_variables(self, template_id):
        """
        Загрузка переменных из шаблона (пока используем стандартный набор)
        """
        # В реальном приложении нужно извлекать переменные из шаблона
        # Для примера используем стандартный набор переменных
        self.template_variables = [
            "{{surname}}",
            "{{name}}",
            "{{patronymic}}",
            "{{birth_date}}",
            "{{birth_place_town}}",
            "{{registration_address}}",
            "{{passport_series}}",
            "{{passport_number}}",
            "{{passport_issue_date}}",
            "{{passport_issued_by}}",
            "{{recipient_fio}}",
            "{{recipient_address}}",
            "{{recipient_phone}}",
            "{{response_address}}",
            "{{contact_phone}}",
            "{{signatory_name}}"
        ]
    
    def load_db_columns(self):
        """
        Загрузка столбцов из таблиц базы данных
        """
        # Определяем столбцы для каждой таблицы
        self.db_columns = {
            "social_data": [
                "surname", "name", "patronymic", "birth_date", 
                "birth_place_town", "birth_place_district", "birth_place_region", "birth_place_country",
                "tab_number", "personal_number", "category_id", "rank_id",
                "drafted_by_commissariat", "draft_date", "povsk", "selection_date",
                "education", "criminal_record", "social_media_account", "bank_card_number",
                "passport_series", "passport_number", "passport_issue_date", "passport_issued_by",
                "military_id_series", "military_id_number", "military_id_issue_date", "military_id_issued_by",
                "appearance_features", "personal_marks", "federal_search_info", "military_contacts", "relatives_info"
            ],
            "addresses": [
                "region", "district", "town", "street", "house", "building", "letter", "apartment", "room",
                "check_date", "check_result"
            ],
            "service_places": [
                "place_name", "military_unit_id", "garrison_id", "position_id", "commanders",
                "postal_index", "postal_region", "postal_district", "postal_town", "postal_street",
                "postal_house", "postal_building", "postal_letter", "postal_apartment", "postal_room",
                "place_contacts"
            ],
            "users": [
                "username", "full_name", "email", "role_id", "is_active", "created_at", "last_login"
            ],
            "statuses": [
                "name"
            ],
            "ranks": [
                "name"
            ],
            "categories": [
                "name"
            ],
            "military_units": [
                "name"
            ],
            "garrisons": [
                "name"
            ],
            "positions": [
                "name"
            ]
        }
    
    def setup_combobox_delegates(self):
        """
        Настройка делегатов для выпадающих списков
        """
        # Устанавливаем делегаты для столбцов
        var_delegate = ComboBoxDelegate(self.template_variables)
        self.mapping_table.setItemDelegateForColumn(0, var_delegate)
        
        # Для второго столбца нужно создать делегат с динамическими значениями
        # Пока используем общий список всех столбцов
        all_columns = []
        for table_cols in self.db_columns.values():
            all_columns.extend(table_cols)
        col_delegate = ComboBoxDelegate(list(set(all_columns)))  # Убираем дубликаты
        self.mapping_table.setItemDelegateForColumn(1, col_delegate)
    
    def add_field_mapping(self):
        """
        Добавление нового сопоставления поля
        """
        template_id = self.template_combo.currentData()
        if not template_id:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон документа")
            return
        
        # Загружаем переменные и столбцы, если еще не загружены
        if not self.template_variables:
            self.load_template_variables(template_id)
        if not self.db_columns:
            self.load_db_columns()
        
        # Добавляем новую строку в таблицу
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)
        
        # Создаем комбобоксы для ячеек
        var_combo = QComboBox()
        var_combo.addItems(self.template_variables)
        self.mapping_table.setCellWidget(row, 0, var_combo)
        
        col_combo = QComboBox()
        # Заполняем все доступные столбцы
        all_columns = []
        for table_cols in self.db_columns.values():
            all_columns.extend(table_cols)
        col_combo.addItems(list(set(all_columns)))  # Убираем дубликаты
        self.mapping_table.setCellWidget(row, 1, col_combo)
    
    def remove_field_mapping(self):
        """
        Удаление выбранного сопоставления поля
        """
        current_row = self.mapping_table.currentRow()
        if current_row >= 0:
            self.mapping_table.removeRow(current_row)
    
    def get_context_data(self, template_id):
        """
        Получение данных для подстановки в шаблон из таблицы сопоставлений
        """
        context = {}
        
        # Проходим по всем строкам таблицы сопоставлений
        for row in range(self.mapping_table.rowCount()):
            var_combo = self.mapping_table.cellWidget(row, 0)
            col_combo = self.mapping_table.cellWidget(row, 1)
            
            if var_combo and col_combo:
                variable_name = var_combo.currentText()
                column_name = col_combo.currentText()
                
                # Убираем символы {{ }} из начала и конца переменной
                variable_name = variable_name.strip('{} ')
                
                # Определяем таблицу по столбцу
                table_name = self.get_table_by_column(column_name)
                
                if table_name:
                    # Получаем значение из базы данных
                    value = self.get_db_value(table_name, column_name, self.krd_id)
                    context[variable_name] = value
        
        return context
    
    def get_table_by_column(self, column_name):
        """
        Определение таблицы по имени столбца
        """
        for table_name, columns in self.db_columns.items():
            if column_name in columns:
                return table_name
        return None
    
    def get_db_value(self, table_name, column_name, krd_id):
        """
        Получение значения из базы данных по таблице, колонке и ID КРД
        """
        # Определяем, какую колонку использовать для связи с krd
        join_column = "krd_id" if table_name != "krd" else "id"
        
        query = QSqlQuery(self.db)
        query.prepare(f"SELECT {column_name} FROM krd.{table_name} WHERE {join_column} = ?")
        query.addBindValue(krd_id)
        query.exec()
        
        if query.next():
            return query.value(0) or ""
        else:
            return ""
    
    def generate_document(self):
        """
        Генерация документа из выбранного шаблона с подстановкой данных
        """
        template_id = self.template_combo.currentData()
        if not template_id:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон документа")
            return
        
        try:
            # Получаем шаблон из базы данных
            query = QSqlQuery(self.db)
            query.prepare("SELECT template_data FROM krd.document_templates WHERE id = ?")
            query.addBindValue(template_id)
            query.exec()
            
            if not query.next():
                raise Exception("Шаблон не найден")
            
            # Получаем бинарные данные
            template_data_variant = query.value(0)
            
            # Преобразуем QVariant в bytes
            if hasattr(template_data_variant, 'data'):
                # Если это QByteArray
                template_data = template_data_variant.data()
            else:
                # Если это уже bytes
                template_data = bytes(template_data_variant)
            
            # Сохраняем шаблон во временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(template_data)
                template_path = tmp_file.name
            
            # Загружаем шаблон
            doc = DocxTemplate(template_path)
            
            # Получаем данные для подстановки из таблицы сопоставлений
            context = self.get_context_data(template_id)
            
            # Производим подстановку данных
            doc.render(context)
            
            # Сохраняем сгенерированный документ во временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as output_file:
                doc.save(output_file.name)
                self.generated_doc_path = output_file.name
            
            # Удаляем временный файл шаблона
            os.unlink(template_path)
            
            QMessageBox.information(self, "Успех", "Документ успешно сгенерирован")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации документа:\n{str(e)}")
    
    def save_document(self):
        """
        Сохранение сгенерированного документа
        """
        if not hasattr(self, 'generated_doc_path') or not os.path.exists(self.generated_doc_path):
            QMessageBox.warning(self, "Ошибка", "Сначала сформируйте документ")
            return
        
        # Открываем диалог сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить документ",
            f"Документ_{self.krd_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            "Word документы (*.docx);;Все файлы (*)"
        )
        
        if file_path:
            try:
                # Копируем сгенерированный документ в выбранное место
                import shutil
                shutil.copy2(self.generated_doc_path, file_path)
                
                QMessageBox.information(self, "Успех", f"Документ сохранен в файл:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении файла:\n{str(e)}")