"""
Модуль для генерации документов из Word-шаблонов
"""

import os
import sys
import tempfile
import re
import traceback
from docx import Document  # Убрали импорт docxtpl
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QGroupBox, QFileDialog, QMessageBox, QComboBox, QTabWidget, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont
from datetime import datetime

# Добавляем импорт логгера аудита
from audit_logger import AuditLogger


# ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ИСКЛЮЧЕНИЙ ДЛЯ ОТЛАДКИ
def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    QMessageBox.critical(
        None, 
        "Критическая ошибка", 
        f"Произошла непредвиденная ошибка:\n{exc_value}\n\nПроверьте консоль для деталей."
    )
sys.excepthook = excepthook


class DocumentGeneratorTab(QWidget):
    """
    Вкладка для генерации документов из Word-шаблонов
    """
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        """
        Инициализация вкладки генерации документов
        
        Args:
            krd_id (int): ID КРД
            db_connection: соединение с базой данных
            audit_logger (AuditLogger, optional): логгер аудита
        """
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger  # Сохраняем логгер аудита
        
        self.template_variables = []
        self.db_columns = {}
        self.generated_doc_path = None  # Инициализируем атрибут
        
        self.init_ui()
        self.load_document_templates()
    
    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        tabs.addTab(self.create_generate_tab(), "Генерация документов")
        tabs.addTab(self.create_templates_tab(), "Управление шаблонами")
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def create_generate_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title_label = QLabel("Генерация документов из шаблонов")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Выбор шаблона
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Шаблон документа:"))
        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_layout.addWidget(self.template_combo)
        layout.addLayout(template_layout)
        
        # Таблица сопоставления
        mapping_group = QGroupBox("Сопоставление полей")
        mapping_layout = QVBoxLayout()
        
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Переменная из шаблона", "Столбец из базы данных"])
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.mapping_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # КРИТИЧНО: блокируем редактирование
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        mapping_layout.addWidget(self.mapping_table)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("Добавить сопоставление", clicked=self.add_field_mapping))
        btn_layout.addWidget(QPushButton("Удалить сопоставление", clicked=self.remove_field_mapping))
        mapping_layout.addLayout(btn_layout)
        
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # Кнопки генерации
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QPushButton("Сформировать документ", clicked=self.generate_document))
        gen_layout.addWidget(QPushButton("Сохранить документ", clicked=self.save_document))
        layout.addLayout(gen_layout)
        
        return widget
    
    def create_templates_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title_label = QLabel("Управление шаблонами документов")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Добавление шаблона
        add_group = QGroupBox("Добавить новый шаблон")
        add_layout = QVBoxLayout()
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Название:"))
        self.template_name_input = QLineEdit()
        name_layout.addWidget(self.template_name_input)
        add_layout.addLayout(name_layout)
        
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Описание:"))
        self.template_desc_input = QLineEdit()
        desc_layout.addWidget(self.template_desc_input)
        add_layout.addLayout(desc_layout)
        
        file_layout = QHBoxLayout()
        self.selected_file_label = QLabel("Файл не выбран")
        select_btn = QPushButton("Выбрать файл шаблона")
        select_btn.clicked.connect(self.select_template_file)
        file_layout.addWidget(select_btn)
        file_layout.addWidget(self.selected_file_label, 1)
        add_layout.addLayout(file_layout)
        
        add_btn = QPushButton("Добавить шаблон")
        add_btn.clicked.connect(self.add_template)
        add_layout.addWidget(add_btn)
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Список шаблонов
        list_group = QGroupBox("Существующие шаблоны")
        list_layout = QVBoxLayout()
        self.templates_list = QTextEdit()
        self.templates_list.setMaximumHeight(150)
        self.templates_list.setReadOnly(True)
        list_layout.addWidget(self.templates_list)
        list_layout.addWidget(QPushButton("Обновить список", clicked=self.refresh_templates_list))
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def select_template_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл шаблона", "", "Word документы (*.docx);;Все файлы (*)"
        )
        if path:
            self.selected_file_path = path
            self.selected_file_label.setText(os.path.basename(path))
    
    def add_template(self):
        name = self.template_name_input.text().strip()
        desc = self.template_desc_input.text().strip()
        
        if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
            QMessageBox.warning(self, "Ошибка", "Выберите файл шаблона")
            return
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название шаблона")
            return
        
        try:
            with open(self.selected_file_path, 'rb') as f:
                data = f.read()
            
            query = QSqlQuery(self.db)
            query.prepare("""
                INSERT INTO krd.document_templates (name, description, template_data)
                VALUES (:name, :description, :template_data)
            """)
            query.bindValue(":name", name)
            query.bindValue(":description", desc)
            query.bindValue(":template_data", QByteArray(data))
            
            if not query.exec():
                raise Exception(query.lastError().text())
            
            # Получаем ID созданного шаблона
            template_id = query.lastInsertId()
            
            # Логирование создания шаблона
            if self.audit_logger:
                file_size = len(data)
                self.audit_logger.log_template_create(template_id, name, desc, file_size)
            
            QMessageBox.information(self, "Успех", "Шаблон успешно добавлен")
            self.template_name_input.clear()
            self.template_desc_input.clear()
            self.selected_file_label.setText("Файл не выбран")
            if hasattr(self, 'selected_file_path'):
                delattr(self, 'selected_file_path')
            self.load_document_templates()
            self.refresh_templates_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления шаблона:\n{str(e)}")
    
    def refresh_templates_list(self):
        query = QSqlQuery(self.db)
        query.exec("""
            SELECT id, name, description, created_at
            FROM krd.document_templates
            ORDER BY created_at DESC
        """)
        
        text = "Список шаблонов:\n"
        while query.next():
            text += (f"\nID: {query.value(0)}\nНазвание: {query.value(1)}\n"
                    f"Описание: {query.value(2)}\nДата: {query.value(3)}\n{'─'*40}\n")
        self.templates_list.setPlainText(text)
    
    def load_document_templates(self):
        self.template_combo.clear()
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.document_templates ORDER BY name")
        while query.next():
            self.template_combo.addItem(query.value(1), query.value(0))
    
    def on_template_changed(self):
        tid = self.template_combo.currentData()
        if tid:
            # Логирование просмотра шаблона
            if self.audit_logger:
                template_name = self.template_combo.currentText()
                self.audit_logger.log_template_view(tid, template_name)
            
            self.load_field_mappings(tid)
    
    def load_field_mappings(self, template_id):
        """
        Загрузка сопоставления полей для выбранного шаблона
        """
        # Очищаем таблицу
        self.mapping_table.setRowCount(0)
        
        # Загружаем переменные из шаблона и столбцы из базы данных
        self.load_template_variables(template_id)
        self.load_db_columns()

        
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
        query = QSqlQuery(self.db)
        query.prepare("SELECT template_data FROM krd.document_templates WHERE id = ?")
        query.addBindValue(template_id)
        if not query.exec() or not query.next():
            self.template_variables = []
            return
        
        # Безопасное преобразование данных
        data = query.value(0)
        if isinstance(data, QByteArray):
            template_bytes = bytes(data)
        else:
            template_bytes = bytes(data) if data else b''
        
        if not template_bytes:
            self.template_variables = []
            return
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp.write(template_bytes)
            tmp_path = tmp.name
        
        try:
            doc = Document(tmp_path)
            vars_set = set()
            # Поиск в параграфах
            for para in doc.paragraphs:
                vars_set.update(re.findall(r'\{\{[^{}]+\}\}', para.text))
            # Поиск в таблицах
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            vars_set.update(re.findall(r'\{\{[^{}]+\}\}', para.text))
            self.template_variables = sorted(vars_set)
        except Exception as e:
            print(f"Ошибка извлечения переменных: {e}", file=sys.stderr)
            self.template_variables = [
                "{{surname}}", "{{name}}", "{{patronymic}}", "{{birth_date}}",
                "{{birth_place_town}}", "{{registration_address}}", "{{passport_series}}",
                "{{passport_number}}", "{{passport_issue_date}}", "{{passport_issued_by}}",
                "{{recipient_fio}}", "{{recipient_address}}", "{{recipient_phone}}",
                "{{response_address}}", "{{contact_phone}}", "{{signatory_name}}"
            ]
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def load_db_columns(self):
        self.db_columns = {
            "social_data": [
                "surname", "name", "patronymic", "birth_date", "birth_place_town",
                "birth_place_district", "birth_place_region", "birth_place_country",
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
            "users": ["username", "full_name", "email", "role_id", "is_active", "created_at", "last_login"],
            "statuses": ["name"],
            "ranks": ["name"],
            "categories": ["name"],
            "military_units": ["name"],
            "garrisons": ["name"],
            "positions": ["name"]
        }
    
    def add_field_mapping(self):
        """БЕЗОПАСНОЕ ДОБАВЛЕНИЕ СОПОСТАВЛЕНИЯ"""
        try:
            if self.template_combo.count() == 0:
                QMessageBox.warning(self, "Ошибка", "Сначала добавьте шаблон")
                return
            
            tid = self.template_combo.currentData()
            if not tid:
                QMessageBox.warning(self, "Ошибка", "Выберите шаблон")
                return
            
            # Гарантируем загрузку данных
            if not self.template_variables:
                self.load_template_variables(tid)
            if not self.db_columns:
                self.load_db_columns()
            
            if not self.template_variables:
                QMessageBox.warning(self, "Ошибка", "Не загружены переменные шаблона")
                return
            if not self.db_columns:
                QMessageBox.warning(self, "Ошибка", "Не загружены столбцы БД")
                return
            
            row = self.mapping_table.rowCount()
            self.mapping_table.insertRow(row)
            
            # Создаём комбобоксы
            var_combo = QComboBox()
            var_combo.addItems(self.template_variables)
            self.mapping_table.setCellWidget(row, 0, var_combo)
            
            col_combo = QComboBox()
            all_cols = sorted({c for cols in self.db_columns.values() for c in cols})
            col_combo.addItems(all_cols)
            self.mapping_table.setCellWidget(row, 1, col_combo)
            
            self.mapping_table.selectRow(row)
            
            # Логирование добавления сопоставления
            if self.audit_logger:
                field_name = var_combo.currentText()
                db_column = col_combo.currentText()
                table_name = self.get_table_by_column(db_column)
                self.audit_logger.log_mapping_create(
                    template_id=tid,
                    field_name=field_name,
                    db_column=db_column,
                    table_name=table_name
                )
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления сопоставления:\n{str(e)}")
    
    def remove_field_mapping(self):
        """
        Удаление выбранного сопоставления из таблицы
        """
        # Получаем индекс выбранной строки
        selected_rows = self.mapping_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите сопоставление для удаления")
            return
        
        # Получаем первую выбранную строку
        row = selected_rows[0].row()
        
        # Получаем имя переменной для информативного сообщения
        var_widget = self.mapping_table.cellWidget(row, 0)
        col_widget = self.mapping_table.cellWidget(row, 1)
        
        if var_widget and col_widget:
            var_name = var_widget.currentText()
            col_name = col_widget.currentText()
            
            # Запрашиваем подтверждение удаления
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Вы действительно хотите удалить сопоставление?\n"
                f"Переменная: {var_name}\n"
                f"Столбец: {col_name}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
            
            # Логирование удаления сопоставления
            if self.audit_logger:
                self.audit_logger.log_mapping_delete(
                    field_name=var_name.strip('{} '),
                    db_column=col_name
                )
        
        # Удаляем выбранную строку
        self.mapping_table.removeRow(row)
        
        QMessageBox.information(
            self,
            "Успех",
            f"Сопоставление удалено"
        )
    
    def get_table_by_column(self, col):
        for tbl, cols in self.db_columns.items():
            if col in cols:
                return tbl
        return None

    # ========================================
    # УПРОЩЁННЫЕ МЕТОДЫ ГЕНЕРАЦИИ ДОКУМЕНТА
    # ========================================
    
    def generate_document(self):
        """
        Генерация документа из шаблона с подстановкой данных
        Простой способ: прямая замена текста во всех элементах документа
        """
        template_id = self.template_combo.currentData()
        if not template_id:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон документа")
            return
        
        # Сохраняем текущие сопоставления перед генерацией
        if not self.save_field_mappings(template_id):
            return
        
        try:
            # === ШАГ 1: Получаем шаблон из базы данных ===
            query = QSqlQuery(self.db)
            query.prepare("SELECT template_data, name FROM krd.document_templates WHERE id = ?")
            query.addBindValue(template_id)
            
            if not query.exec() or not query.next():
                raise Exception("Шаблон не найден в базе данных")
            
            template_name = query.value(1)
            template_data = bytes(query.value(0)) if isinstance(query.value(0), QByteArray) else bytes(query.value(0))
            
            if not template_data:
                raise Exception("Шаблон пуст")
            
            print(f"\n📄 Генерация документа: {template_name}")
            
            # === ШАГ 2: Сохраняем шаблон во временный файл ===
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                tmp.write(template_data)
                template_path = tmp.name
            
            # === ШАГ 3: Загружаем документ ===
            doc = Document(template_path)
            
            # === ШАГ 4: Получаем данные для подстановки ===
            context = self.get_context_data(template_id)
            
            print(f"Контекст ({len(context)} переменных):")
            for key, value in context.items():
                print(f"  {key}: {value}")
            
            # === ШАГ 5: Прямая замена переменных во всём документе ===
            replacements = 0
            
            # Замена в параграфах
            for paragraph in doc.paragraphs:
                replacements += self._replace_text_in_element(paragraph, context)
            
            # Замена в таблицах
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            replacements += self._replace_text_in_element(paragraph, context)
            
            # Замена в заголовках и колонтитулах
            for section in doc.sections:
                for paragraph in section.header.paragraphs:
                    replacements += self._replace_text_in_element(paragraph, context)
                for paragraph in section.footer.paragraphs:
                    replacements += self._replace_text_in_element(paragraph, context)
            
            print(f"✅ Заменено переменных: {replacements}")
            
            # === ШАГ 6: Сохраняем документ ===
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as out_file:
                doc.save(out_file.name)
                self.generated_doc_path = out_file.name
            
            file_size = os.path.getsize(self.generated_doc_path)
            print(f"💾 Размер файла: {file_size} байт")
            
            # Очищаем временный файл шаблона
            os.unlink(template_path)
            
            # Логирование генерации документа
            if self.audit_logger:
                self.audit_logger.log_document_generate(self.krd_id, template_name)
            
            QMessageBox.information(
                self,
                "Успех",
                f"Документ успешно сгенерирован!\n\n"
                f"Переменных заменено: {replacements}\n"
                f"Размер файла: {file_size} байт"
            )
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка генерации:\n{str(e)}")

    def _replace_text_in_element(self, element, context):
        """
        Прямая замена переменных в элементе документа с сохранением ВСЕХ стилей
        Работает с параграфами, ячейками таблиц и т.д.
        
        Возвращает: количество замен
        """
        replacements = 0
        
        # Если элемент - параграф
        if hasattr(element, 'text') and hasattr(element, 'runs'):
            original_text = element.text
            
            if not original_text:
                return 0
            
            # Заменяем все переменные из контекста
            new_text = original_text
            for var_name, value in context.items():
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in new_text:
                    count = new_text.count(placeholder)
                    replacements += count
                    new_text = new_text.replace(placeholder, str(value))
            
            # Если текст изменился, обновляем параграф
            if new_text != original_text:
                # Если есть раны, обновляем каждый ран
                if element.runs:
                    # Сохраняем стили ПЕРВОГО рана
                    first_run = element.runs[0]
                    
                    # Сохраняем текущие стили перед заменой
                    saved_bold = first_run.bold
                    saved_italic = first_run.italic
                    saved_underline = first_run.underline
                    
                    # Сохраняем стили шрифта
                    saved_font_name = None
                    saved_font_size = None
                    saved_font_color = None
                    
                    if first_run.font:
                        saved_font_name = first_run.font.name
                        saved_font_size = first_run.font.size
                        if first_run.font.color and first_run.font.color.rgb:
                            saved_font_color = first_run.font.color.rgb
                    
                    # Устанавливаем новый текст
                    first_run.text = new_text
                    
                    # Восстанавливаем стили
                    first_run.bold = saved_bold
                    first_run.italic = saved_italic
                    first_run.underline = saved_underline
                    
                    if first_run.font:
                        if saved_font_name:
                            first_run.font.name = saved_font_name
                        if saved_font_size:
                            first_run.font.size = saved_font_size
                        if saved_font_color:
                            first_run.font.color.rgb = saved_font_color
                    
                    # Удаляем остальные раны
                    for i in range(len(element.runs) - 1, 0, -1):
                        run = element.runs[i]
                        if hasattr(run, '_element') and run._element in element._element:
                            try:
                                element._element.remove(run._element)
                            except:
                                pass
                else:
                    # Если нет ранов, создаём новый с базовыми стилями
                    element.clear()
                    new_run = element.add_run(new_text)
                    # Устанавливаем базовые стили
                    new_run.font.name = 'Times New Roman'
                    # Не устанавливаем размер - используем размер по умолчанию из стиля параграфа
        
        return replacements

    def get_context_data(self, template_id):
        """
        Получение данных для подстановки из базы данных
        """
        context = {}
        
        # Загружаем сопоставления из базы
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT field_name, db_column, table_name
            FROM krd.field_mappings
            WHERE template_id = ?
        """)
        query.addBindValue(template_id)
        query.exec()
        
        while query.next():
            field_name = query.value(0).strip('{} ')
            db_column = query.value(1)
            table_name = query.value(2)
            
            # Получаем значение из базы
            value = self._get_value_from_database(table_name, db_column, self.krd_id)
            if value is not None:
                context[field_name] = value
        
        return context

    def _get_value_from_database(self, table_name, column_name, krd_id):
        """
        Получение значения из базы данных с правильным преобразованием типов
        """
        join_col = "krd_id" if table_name != "krd" else "id"
        
        # Защита от инъекций
        if not re.match(r'^\w+$', table_name) or not re.match(r'^\w+$', column_name):
            return ""
        
        query = QSqlQuery(self.db)
        query.prepare(f"SELECT {column_name} FROM krd.{table_name} WHERE {join_col} = ?")
        query.addBindValue(krd_id)
        
        if query.exec() and query.next():
            value = query.value(0)
            
            # Обработка QDate
            if hasattr(value, 'getDate'):
                year, month, day = value.getDate()
                return f"{day:02d}.{month:02d}.{year}"
            # Обработка других типов
            elif value is not None:
                return str(value)
        
        return ""

    def save_document(self):
        """
        Сохранение сгенерированного документа
        """
        if not self.generated_doc_path or not os.path.exists(self.generated_doc_path):
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте документ")
            return
        
        default_name = f"Документ_{self.krd_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить документ",
            default_name,
            "Word документы (*.docx);;Все файлы (*)"
        )
        
        if path:
            try:
                import shutil
                shutil.copy2(self.generated_doc_path, path)
                
                # Логирование сохранения документа
                if self.audit_logger:
                    filename = os.path.basename(path)
                    self.audit_logger.log_document_save(self.krd_id, filename)
                
                # Очищаем временный файл
                try:
                    os.unlink(self.generated_doc_path)
                    self.generated_doc_path = None
                except:
                    pass
                
                QMessageBox.information(self, "Успех", f"Документ сохранён:\n{path}")
                
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{str(e)}")
    
    def save_field_mappings(self, template_id):
        """
        Сохранение сопоставлений полей в базу данных с транзакцией
        """
        try:
            # Начинаем транзакцию
            if not self.db.transaction():
                raise Exception(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
            
            # Удаляем старые сопоставления
            del_query = QSqlQuery(self.db)
            del_query.prepare("DELETE FROM krd.field_mappings WHERE template_id = ?")
            del_query.addBindValue(template_id)
            if not del_query.exec():
                raise Exception(f"Ошибка удаления старых сопоставлений: {del_query.lastError().text()}")
            
            # Сохраняем новые сопоставления
            saved_count = 0
            for row in range(self.mapping_table.rowCount()):
                var_w = self.mapping_table.cellWidget(row, 0)
                col_w = self.mapping_table.cellWidget(row, 1)
                
                if not var_w or not col_w:
                    continue
                
                field_name = var_w.currentText().strip()
                db_column = col_w.currentText().strip()
                table_name = self.get_table_by_column(db_column)
                
                if not field_name or not db_column or not table_name:
                    continue
                
                ins_query = QSqlQuery(self.db)
                ins_query.prepare("""
                    INSERT INTO krd.field_mappings (template_id, field_name, db_column, table_name)
                    VALUES (?, ?, ?, ?)
                """)
                ins_query.addBindValue(template_id)
                ins_query.addBindValue(field_name)
                ins_query.addBindValue(db_column)
                ins_query.addBindValue(table_name)
                
                if not ins_query.exec():
                    raise Exception(f"Ошибка сохранения '{field_name}': {ins_query.lastError().text()}")
                
                saved_count += 1
            
            # Фиксируем изменения
            if not self.db.commit():
                raise Exception(f"Ошибка коммита: {self.db.lastError().text()}")
            
            print(f"✅ Сохранено {saved_count} сопоставлений для шаблона {template_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка сохранения", 
                            f"Не удалось сохранить сопоставления:\n{str(e)}\n\nПроверьте консоль для деталей.")
            return False