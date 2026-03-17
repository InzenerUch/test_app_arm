"""
Модуль для генерации документов из Word-шаблонов
С поддержкой составных полей и сохранения запросов в базу данных
"""
import os
import sys
import tempfile
import json
from docx.shared import Pt
import re
import traceback
from docx import Document
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QGroupBox, QFileDialog, QMessageBox, QComboBox, QTabWidget, QLineEdit,
    QTableWidget, QTableWidgetItem, QGridLayout, QHeaderView, QAbstractItemView,
    QTableView, QMenu, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QByteArray, QPoint, QDate
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont, QContextMenuEvent, QAction
from datetime import datetime
from audit_logger import AuditLogger
from composite_field_widget import CompositeFieldWidget
from field_mapping_manager import FieldMappingManager
from database_handler import DatabaseHandler


# ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ИСКЛЮЧЕНИЙ
def excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    QMessageBox.critical(
        None,
        "Критическая ошибка",
        f"Произошла непредвиденная ошибка:\n{exc_value}\nПроверьте консоль для деталей."
    )

sys.excepthook = excepthook


class DocumentGeneratorTab(QWidget):
    """Вкладка для генерации документов из шаблонов"""
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.template_variables = []
        self.db_columns = {}
        self.generated_doc_path = None
        self.selected_file_path = None
        self.current_table_name = "social_data"
        
        # ✅ ДОБАВЛЕНО: Отслеживание текущего шаблона
        self.current_template_id = None
        
        # Инициализация модулей
        self.composite_widget = CompositeFieldWidget(self)
        self.mapping_manager = FieldMappingManager(self)
        self.db_handler = DatabaseHandler(self.db)
        
        print(f"\n{'='*60}")
        print(f"🔧 DocumentGeneratorTab инициализирован для КРД-{krd_id}")
        print(f"{'='*60}\n")
        
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
        """Создание вкладки генерации документов"""
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
        
        # ✅ ДОБАВЛЕНО: Кнопка сохранения сопоставлений
        save_mapping_btn = QPushButton("💾 Сохранить сопоставления")
        save_mapping_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        save_mapping_btn.clicked.connect(self.save_mappings_now)
        template_layout.addWidget(save_mapping_btn)
        
        layout.addLayout(template_layout)
        
        # Таблица сопоставления полей
        mapping_group = QGroupBox("Сопоставление полей")
        mapping_layout = QVBoxLayout()
        
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels([
            "Переменная из шаблона",
            "Столбец(ы) из базы данных",
            "Тип"
        ])
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.mapping_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.mapping_table.setColumnWidth(2, 80)
        
        mapping_layout.addWidget(self.mapping_table)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("Добавить сопоставление", clicked=self.add_field_mapping))
        btn_layout.addWidget(QPushButton("Добавить составное поле", clicked=self.add_composite_field_mapping))
        btn_layout.addWidget(QPushButton("Удалить сопоставление", clicked=self.remove_field_mapping))
        mapping_layout.addLayout(btn_layout)
        
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # Поля для сохранения в базу данных
        save_db_group = QGroupBox("Сохранение запроса в базу данных")
        save_db_layout = QGridLayout()
        
        save_db_layout.addWidget(QLabel("Тип запроса *:"), 0, 0)
        self.request_type_combo = QComboBox()
        self.load_request_types()
        save_db_layout.addWidget(self.request_type_combo, 0, 1, 1, 2)
        
        save_db_layout.addWidget(QLabel("Адресат *:"), 1, 0)
        self.recipient_input = QLineEdit()
        save_db_layout.addWidget(self.recipient_input, 1, 1, 1, 2)
        
        save_to_db_btn = QPushButton("Сохранить запрос в базу")
        save_to_db_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 11px;")
        save_to_db_btn.clicked.connect(self.save_to_database)
        save_db_layout.addWidget(save_to_db_btn, 2, 0, 1, 3)
        
        save_db_group.setLayout(save_db_layout)
        layout.addWidget(save_db_group)
        
        # Кнопки генерации и сохранения на диск
        gen_layout = QHBoxLayout()
        gen_layout.addWidget(QPushButton("Сформировать документ", clicked=self.generate_document))
        gen_layout.addWidget(QPushButton("Сохранить на диск", clicked=self.save_to_disk))
        layout.addLayout(gen_layout)
        
        return widget
    
    # ========================
    # ✅ МЕТОДЫ УПРАВЛЕНИЯ ПОЛЯМИ (С АВТОСОХРАНЕНИЕМ)
    # ========================
    
    def add_field_mapping(self):
        """Добавление простого сопоставления (один столбец)"""
        print(f"\n{'='*60}")
        print(f"📝 ДОБАВЛЕНИЕ ПРОСТОГО СОПОСТАВЛЕНИЯ")
        print(f"{'='*60}")
        
        try:
            if self.template_combo.count() == 0:
                print("❌ Ошибка: Шаблоны не загружены")
                QMessageBox.warning(self, "Ошибка", "Сначала добавьте шаблон")
                return
            
            tid = self.template_combo.currentData()
            print(f"📋 Template ID: {tid}")
            
            if not tid:
                print("❌ Ошибка: Шаблон не выбран")
                QMessageBox.warning(self, "Ошибка", "Выберите шаблон")
                return
            
            if not self.template_variables:
                print("🔄 Загрузка переменных шаблона...")
                self.load_template_variables(tid)
            
            if not self.db_columns:
                print("🔄 Загрузка столбцов БД...")
                self.load_db_columns()
            
            print(f"📊 Переменных шаблона: {len(self.template_variables)}")
            print(f"📊 Таблиц БД: {len(self.db_columns)}")
            
            if not self.template_variables:
                print("❌ Ошибка: Не загружены переменные шаблона")
                QMessageBox.warning(self, "Ошибка", "Не загружены переменные шаблона")
                return
            
            if not self.db_columns:
                print("❌ Ошибка: Не загружены столбцы БД")
                QMessageBox.warning(self, "Ошибка", "Не загружены столбцы БД")
                return
            
            row = self.mapping_table.rowCount()
            print(f"📊 Добавление строки #{row}")
            
            self.mapping_table.insertRow(row)
            
            var_combo = QComboBox()
            var_combo.addItems(self.template_variables)
            self.mapping_table.setCellWidget(row, 0, var_combo)
            
            col_combo = QComboBox()
            all_cols = sorted({c for cols in self.db_columns.values() for c in cols})
            col_combo.addItems(all_cols)
            self.mapping_table.setCellWidget(row, 1, col_combo)
            
            type_label = QLabel("Простое")
            type_label.setStyleSheet("color: #666; font-size: 10px;")
            self.mapping_table.setCellWidget(row, 2, type_label)
            
            self.mapping_table.resizeRowToContents(row)
            self.mapping_table.selectRow(row)
            
            print(f"✅ Сопоставление добавлено в строку #{row}")
            print(f"   Переменная: {var_combo.currentText()}")
            print(f"   Столбец: {col_combo.currentText()}")
            
            # ✅ АВТОСОХРАНЕНИЕ после добавления
            print(f"🔄 Автосохранение сопоставлений...")
            self.save_mappings_now()
            
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
            
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Ошибка добавления сопоставления: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления сопоставления:\n{str(e)}")
    
    def add_composite_field_mapping(self):
        """Добавление нового составного поля через виджет"""
        print(f"\n{'='*60}")
        print(f"📝 ДОБАВЛЕНИЕ СОСТАВНОГО ПОЛЯ")
        print(f"{'='*60}")
        
        if not self.current_template_id:
            print("❌ Ошибка: Шаблон не выбран")
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон для добавления сопоставления")
            return
        
        row = self.mapping_table.rowCount()
        print(f"📊 Новая строка: #{row}")
        
        self.composite_widget.add_composite_field_mapping(row)
        
        print(f"✅ Составное поле добавлено")
        
        # ✅ АВТОСОХРАНЕНИЕ после добавления
        print(f"🔄 Автосохранение сопоставлений...")
        self.save_mappings_now()
        
        print(f"{'='*60}\n")
    
    def remove_field_mapping(self):
        """✅ Удаление сопоставления (из UI и БД)"""
        print(f"\n{'='*60}")
        print(f"🗑️ УДАЛЕНИЕ СОПОСТАВЛЕНИЯ")
        print(f"{'='*60}")
        
        selected_rows = self.mapping_table.selectionModel().selectedRows()
        if not selected_rows:
            print("❌ Ошибка: Строка не выбрана")
            QMessageBox.warning(self, "Внимание", "Выберите сопоставление для удаления")
            return
        
        row = selected_rows[0].row()
        print(f"📊 Выбрана строка #{row}")
        
        var_widget = self.mapping_table.cellWidget(row, 0)
        col_widget = self.mapping_table.cellWidget(row, 1)
        
        if not var_widget or not col_widget:
            print("❌ Ошибка: Виджеты не найдены")
            return
        
        var_name = var_widget.currentText()
        is_composite = hasattr(col_widget, 'layout')
        col_name = "Составное поле" if is_composite else col_widget.currentText()
        
        print(f"📊 Переменная: {var_name}")
        print(f"📊 Столбец: {col_name}")
        print(f"📊 Тип: {'Составное' if is_composite else 'Простое'}")
        
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы действительно хотите удалить сопоставление?\n"
            f"Переменная: {var_name}\n"
            f"Столбец: {col_name}\n"
            f"⚠️ Сопоставление будет удалено из базы данных!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # ✅ Удаление из базы данных
                if self.current_template_id:
                    print(f"🔄 Удаление из БД (template_id={self.current_template_id})...")
                    
                    # Для составных полей нужно удалить по field_name
                    field_name_clean = var_name.strip('{} ')
                    
                    self.mapping_manager.delete_field_mapping(
                        self.current_template_id, 
                        field_name_clean, 
                        col_name
                    )
                    print(f"✅ Удалено из базы данных")
                else:
                    print("⚠️ Шаблон не выбран, удаление только из UI")
                
                # Удаление из UI
                self.mapping_table.removeRow(row)
                print(f"✅ Удалено из интерфейса")
                
                if self.audit_logger:
                    self.audit_logger.log_mapping_delete(
                        field_name=field_name_clean,
                        db_column=col_name
                    )
                
                QMessageBox.information(self, "Успех", "Сопоставление удалено")
                
            except Exception as e:
                print(f"❌ Ошибка удаления: {e}")
                traceback.print_exc()
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления:\n{str(e)}")
        
        print(f"{'='*60}\n")
    
    def on_template_changed(self):
        """Обработчик изменения шаблона"""
        tid = self.template_combo.currentData()
        template_name = self.template_combo.currentText()
        
        print(f"\n{'='*60}")
        print(f"🔄 ШАБЛОН ИЗМЕНЁН")
        print(f"{'='*60}")
        print(f"📋 Template ID: {tid}")
        print(f"📋 Template Name: {template_name}")
        
        if tid:
            # ✅ СОХРАНЯЕМ текущий ID шаблона
            self.current_template_id = tid
            
            if self.audit_logger:
                self.audit_logger.log_template_view(tid, template_name)
            
            print(f"🔄 Загрузка сопоставлений...")
            self.load_field_mappings(tid)
        else:
            print("⚠️ Шаблон не выбран")
            self.current_template_id = None
        
        print(f"{'='*60}\n")

    
    def save_mappings_now(self):
        """Явное сохранение сопоставлений (кнопка + автосохранение)"""
        print(f"\n{'='*60}")
        print(f"💾 СОХРАНЕНИЕ СОПОСТАВЛЕНИЙ (ЯВНОЕ)")
        print(f"{'='*60}")
        
        if not self.current_template_id:
            print("⚠️ Шаблон не выбран, сохранение отменено")
            return False
        
        print(f"📋 Template ID: {self.current_template_id}")
        
        result = self.mapping_manager.save_field_mappings(self.current_template_id)
        
        if result:
            print(f"✅ Сохранение успешно")
            QMessageBox.information(self, "Успех", "Сопоставления сохранены в базу данных!")
        else:
            print(f"❌ Сохранение не удалось")
        
        print(f"{'='*60}\n")
        
        return result
    
    def load_field_mappings(self, template_id):
        """Загрузка сопоставлений через менеджер"""
        print(f"\n{'='*60}")
        print(f"📥 ЗАГРУЗКА СОПОСТАВЛЕНИЙ")
        print(f"{'='*60}")
        print(f"📋 Template ID: {template_id}")
        
        try:
            # ✅ Очищаем таблицу
            self.mapping_table.setRowCount(0)
            print(f"🔄 Очистка таблицы сопоставлений")
            
            # ✅ Загружаем переменные и столбцы
            print(f"🔄 Загрузка переменных шаблона...")
            self.load_template_variables(template_id)
            print(f"📊 Переменных загружено: {len(self.template_variables)}")
            
            print(f"🔄 Загрузка столбцов БД...")
            self.load_db_columns()
            print(f"📊 Таблиц БД: {len(self.db_columns)}")
            
            # ✅ Загружаем сопоставления из БД
            print(f"🔄 Вызов mapping_manager.load_field_mappings()...")
            self.mapping_manager.load_field_mappings(template_id)
            
            # ✅ ПРОВЕРКА: сколько строк в таблице
            row_count = self.mapping_table.rowCount()
            print(f"✅ Загружено сопоставлений: {row_count}")
            
            # ✅ ВЫВОД всех строк таблицы
            for row in range(row_count):
                var_w = self.mapping_table.cellWidget(row, 0)
                col_w = self.mapping_table.cellWidget(row, 1)
                type_w = self.mapping_table.cellWidget(row, 2)
                
                if var_w and col_w and type_w:
                    var_name = var_w.currentText()
                    is_composite = hasattr(col_w, 'layout')
                    col_name = "Составное" if is_composite else col_w.currentText()
                    type_name = type_w.text()
                    print(f"   [{row}] {var_name} → {col_name} ({type_name})")
                else:
                    print(f"   [{row}] ⚠️ ОШИБКА: виджеты не созданы!")
                    print(f"       var_w={var_w}, col_w={col_w}, type_w={type_w}")
            
            if row_count == 0:
                print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Таблица пуста после загрузки!")
                
        except Exception as e:
            print(f"❌ Ошибка загрузки сопоставлений: {e}")
            traceback.print_exc()
        
        print(f"{'='*60}\n")
    
    def add_simple_mapping_row(self, row, field_name, db_column, table_name):
        """Добавление простого сопоставления"""
        print(f"📝 Добавление простого сопоставления в строку #{row}")
        print(f"   Поле: {field_name}, Столбец: {db_column}, Таблица: {table_name}")
        
        try:
            # ✅ Вставляем строку
            self.mapping_table.insertRow(row)
            
            # ✅ Создаем ComboBox для переменной
            var_combo = QComboBox()
            var_combo.addItems(self.template_variables)
            var_combo.setCurrentText(field_name)
            self.mapping_table.setCellWidget(row, 0, var_combo)
            
            # ✅ Создаем ComboBox для столбца БД
            col_combo = QComboBox()
            if table_name in self.db_columns:
                col_combo.addItems(self.db_columns[table_name])
            col_combo.setCurrentText(db_column)
            self.mapping_table.setCellWidget(row, 1, col_combo)
            
            # ✅ Создаем метку типа
            type_label = QLabel("Простое")
            type_label.setStyleSheet("color: #666; font-size: 10px;")
            self.mapping_table.setCellWidget(row, 2, type_label)
            
            # ✅ Подстраиваем высоту строки
            self.mapping_table.resizeRowToContents(row)
            
            # ✅ ПРОВЕРКА: что было добавлено
            var_w = self.mapping_table.cellWidget(row, 0)
            col_w = self.mapping_table.cellWidget(row, 1)
            type_w = self.mapping_table.cellWidget(row, 2)
            
            if var_w and col_w and type_w:
                print(f"✅ Простое сопоставление добавлено")
                print(f"   var_combo: {var_w.currentText()}")
                print(f"   col_combo: {col_w.currentText()}")
                print(f"   type_label: {type_w.text()}")
            else:
                print(f"❌ ОШИБКА: виджеты не созданы!")
                
        except Exception as e:
            print(f"❌ Ошибка добавления простого сопоставления: {e}")
            traceback.print_exc()
    def add_composite_mapping_row(self, row, field_name, db_columns_json, table_name):
        """Добавление составного сопоставления через виджет"""
        print(f"📝 Добавление составного сопоставления в строку #{row}")
        print(f"   Поле: {field_name}, Таблица: {table_name}")
        print(f"   Столбцы: {db_columns_json}")
        
        try:
            # ✅ Вызываем виджет
            self.composite_widget.create_composite_field_row(
                row, field_name, db_columns_json, table_name, self.mapping_table
            )
            
            # ✅ ПРОВЕРКА: что было добавлено
            var_w = self.mapping_table.cellWidget(row, 0)
            col_w = self.mapping_table.cellWidget(row, 1)
            type_w = self.mapping_table.cellWidget(row, 2)
            
            if var_w and col_w and type_w:
                print(f"✅ Составное сопоставление добавлено")
                print(f"   var_combo: {var_w.currentText()}")
                print(f"   composite_widget: {col_w}")
                print(f"   type_label: {type_w.text()}")
            else:
                print(f"❌ ОШИБКА: виджеты не созданы!")
                print(f"   var_w={var_w}, col_w={col_w}, type_w={type_w}")
                
        except Exception as e:
            print(f"❌ Ошибка добавления составного сопоставления: {e}")
            traceback.print_exc()
    # ========================
    # ✅ МЕТОДЫ-ОБЁРТКИ ДЛЯ МЕНЕДЖЕРОВ
    # ========================
    
    def save_field_mappings(self, template_id):
        """Обёртка для вызова менеджера сопоставлений"""
        print(f"\n{'='*60}")
        print(f"💾 СОХРАНЕНИЕ СОПОСТАВЛЕНИЙ")
        print(f"{'='*60}")
        print(f"📋 Template ID: {template_id}")
        
        result = self.mapping_manager.save_field_mappings(template_id)
        
        if result:
            print(f"✅ Сохранение успешно")
        else:
            print(f"❌ Сохранение не удалось")
        
        print(f"{'='*60}\n")
        
        return result
    
    def get_composite_columns(self, composite_widget):
        """Обёртка для вызова виджета составных полей"""
        return self.composite_widget.get_composite_columns(composite_widget)
    
    # ========================
    # ✅ МЕТОДЫ ЗАГРУЗКИ ДАННЫХ
    # ========================
    
    def load_request_types(self):
        """Загрузка типов запросов из базы данных"""
        print(f"🔄 Загрузка типов запросов...")
        self.request_type_combo.clear()
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.request_types ORDER BY name")
        count = 0
        while query.next():
            type_id = query.value(0)
            type_name = query.value(1)
            self.request_type_combo.addItem(type_name, type_id)
            count += 1
        print(f"✅ Загружено {count} типов запросов")
    
    def get_table_by_column(self, col):
        """Определение таблицы по имени столбца"""
        for tbl, cols in self.db_columns.items():
            if col in cols:
                return tbl
        return None
    
    def load_template_variables(self, template_id):
        """Загрузка переменных из шаблона документа"""
        print(f"🔄 Загрузка переменных шаблона (id={template_id})...")
        
        query = QSqlQuery(self.db)
        query.prepare("SELECT template_data FROM krd.document_templates WHERE id = ?")
        query.addBindValue(template_id)
        
        if not query.exec():
            print(f"❌ Ошибка запроса: {query.lastError().text()}")
            self.template_variables = []
            return
        
        if not query.next():
            print(f"⚠️ Шаблон не найден")
            self.template_variables = []
            return
        
        data = query.value(0)
        if isinstance(data, QByteArray):
            template_bytes = bytes(data)
        else:
            template_bytes = bytes(data) if data else b''
        
        if not template_bytes:
            print(f"⚠️ Шаблон пуст")
            self.template_variables = []
            return
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp.write(template_bytes)
            tmp_path = tmp.name
        
        try:
            doc = Document(tmp_path)
            vars_set = set()
            
            for para in doc.paragraphs:
                vars_set.update(re.findall(r'\{\{[^{}]+\}\}', para.text))
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            vars_set.update(re.findall(r'\{\{[^{}]+\}\}', para.text))
            
            self.template_variables = sorted(vars_set)
            print(f"✅ Найдено {len(self.template_variables)} переменных")
            
        except Exception as e:
            print(f"❌ Ошибка извлечения переменных: {e}")
            traceback.print_exc()
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
        """Загрузка структуры столбцов базы данных"""
        print(f"🔄 Загрузка структуры столбцов БД...")
        
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
        print(f"✅ Загружено {len(self.db_columns)} таблиц")
    
    # ========================
    # ✅ МЕТОДЫ ГЕНЕРАЦИИ ДОКУМЕНТОВ
    # ========================
    
    def generate_document(self):
        """Генерация документа на основе шаблона и данных"""
        print(f"\n{'='*60}")
        print(f"📄 ГЕНЕРАЦИЯ ДОКУМЕНТА")
        print(f"{'='*60}")
        
        template_id = self.template_combo.currentData()
        if not template_id:
            print("❌ Ошибка: Шаблон не выбран")
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон документа")
            return
        
        print(f"📋 Template ID: {template_id}")
        
        # ✅ Сохраняем сопоставления перед генерацией
        if not self.save_field_mappings(template_id):
            print("❌ Ошибка: Не удалось сохранить сопоставления")
            return
        
        try:
            query = QSqlQuery(self.db)
            query.prepare("SELECT template_data, name FROM krd.document_templates WHERE id = ?")
            query.addBindValue(template_id)
            
            if not query.exec():
                raise Exception(f"Ошибка запроса: {query.lastError().text()}")
            
            if not query.next():
                raise Exception("Шаблон не найден в базе данных")
            
            template_name = query.value(1)
            template_data = bytes(query.value(0)) if isinstance(query.value(0), QByteArray) else bytes(query.value(0))
            
            if not template_data:
                raise Exception("Шаблон пуст")
            
            print(f"📄 Шаблон: {template_name}")
            print(f"📂 Размер шаблона: {len(template_data)} байт")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                tmp.write(template_data)
                template_path = tmp.name
            
            doc = Document(template_path)
            context = self.get_context_data(template_id)
            
            print(f"📊 Контекст ({len(context)} переменных):")
            for key, value in context.items():
                print(f"   {key}: {value}")
            
            replacements = 0
            
            for paragraph in doc.paragraphs:
                replacements += self._replace_text_in_element(paragraph, context)
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            replacements += self._replace_text_in_element(paragraph, context)
            
            for section in doc.sections:
                for paragraph in section.header.paragraphs:
                    replacements += self._replace_text_in_element(paragraph, context)
                for paragraph in section.footer.paragraphs:
                    replacements += self._replace_text_in_element(paragraph, context)
            
            print(f"✅ Заменено переменных: {replacements}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as out_file:
                doc.save(out_file.name)
                self.generated_doc_path = out_file.name
            
            file_size = os.path.getsize(self.generated_doc_path)
            print(f"💾 Размер сгенерированного файла: {file_size} байт")
            
            if file_size == 0:
                raise Exception("Сгенерированный документ пустой!")
            
            os.unlink(template_path)
            
            if self.audit_logger:
                self.audit_logger.log_document_generate(self.krd_id, template_name)
            
            QMessageBox.information(
                self, "Успех",
                f"Документ успешно сгенерирован!\n"
                f"Переменных заменено: {replacements}\n"
                f"Размер файла: {file_size} байт"
            )
            
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка генерации:\n{str(e)}")
        
        print(f"{'='*60}\n")
    
    def _replace_text_in_element(self, element, context):
        """Замена переменных в элементе документа"""
        replacements = 0
        
        if hasattr(element, 'text') and hasattr(element, 'runs'):
            original_text = element.text
            if not original_text:
                return 0
            
            new_text = original_text
            
            for var_name, value in context.items():
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in new_text:
                    count = new_text.count(placeholder)
                    replacements += count
                    new_text = new_text.replace(placeholder, str(value))
            
            if element.runs:
                if new_text != original_text:
                    first_run = element.runs[0]
                    saved_bold = first_run.bold
                    saved_italic = first_run.italic
                    saved_underline = first_run.underline
                    saved_font_name = None
                    saved_font_size = None
                    saved_font_color = None
                    
                    if first_run.font:
                        saved_font_name = first_run.font.name
                        saved_font_size = first_run.font.size
                        if first_run.font.color and first_run.font.color.rgb:
                            saved_font_color = first_run.font.color.rgb
                    
                    first_run.text = new_text
                    first_run.bold = saved_bold
                    first_run.italic = saved_italic
                    first_run.underline = saved_underline
                    
                    if first_run.font:
                        if saved_font_name:
                            first_run.font.name = saved_font_name
                        if saved_font_size:
                            first_run.font.size = saved_font_size
                        else:
                            first_run.font.size = Pt(14)
                        if saved_font_color:
                            first_run.font.color.rgb = saved_font_color
                    
                    for i in range(len(element.runs) - 1, 0, -1):
                        run = element.runs[i]
                        if hasattr(run, '_element') and run._element in element._element:
                            try:
                                element._element.remove(run._element)
                            except:
                                pass
                else:
                    for run in element.runs:
                        if run.font:
                            if not run.font.size or run.font.size is None:
                                run.font.size = Pt(14)
                            if not run.font.name:
                                run.font.name = 'Times New Roman'
            else:
                element.clear()
                new_run = element.add_run(new_text)
                new_run.font.name = 'Times New Roman'
                new_run.font.size = Pt(14)
        
        return replacements
    
    def get_context_data(self, template_id):
        """Получение данных для подстановки из базы данных с поддержкой составных полей"""
        print(f"🔄 Получение контекста данных...")
        
        context = {}
        
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT field_name, db_column, table_name, db_columns, is_composite
            FROM krd.field_mappings
            WHERE template_id = ?
        """)
        query.addBindValue(template_id)
        
        if not query.exec():
            print(f"❌ Ошибка запроса: {query.lastError().text()}")
            return context
        
        count = 0
        while query.next():
            field_name = query.value(0).strip('{} ')
            db_column = query.value(1)
            table_name = query.value(2)
            db_columns_json = query.value(3)
            is_composite = query.value(4) or False
            
            # ✅ Получаем значение
            if is_composite and db_columns_json:
                value = self._get_composite_value(table_name, db_columns_json, self.krd_id)
            else:
                value = self._get_value_from_database(table_name, db_column, self.krd_id)
            
            # ✅ ИСПРАВЛЕНО: Не перезаписываем существующие field_name
            if field_name in context:
                print(f"   ⚠️ ПРЕДУПРЕЖДЕНИЕ: {field_name} уже существует в контексте!")
                print(f"      Старое значение: {context[field_name]}")
                print(f"      Новое значение: {value}")
                # Можно добавить суффикс или пропустить
                # field_name = f"{field_name}_{count}"
            
            if value is not None:
                context[field_name] = value
                count += 1
                print(f"   {field_name} = {value}")
        
        print(f"✅ Получено {count} значений")
        print(f"📊 Уникальных переменных в контексте: {len(context)}")
        
        return context
    def _get_value_from_database(self, table_name, column_name, krd_id):
        """Получение значения из базы данных"""
        join_col = "krd_id" if table_name != "krd" else "id"
        
        if not re.match(r'^\w+$', table_name) or not re.match(r'^\w+$', column_name):
            return ""
        
        query = QSqlQuery(self.db)
        query.prepare(f"SELECT {column_name} FROM krd.{table_name} WHERE {join_col} = ?")
        query.addBindValue(krd_id)
        
        if query.exec() and query.next():
            value = query.value(0)
            if hasattr(value, 'getDate'):
                year, month, day = value.getDate()
                return f"{day:02d}.{month:02d}.{year}"
            elif value is not None:
                return str(value)
        
        return ""
    
    def _get_composite_value(self, table_name, db_columns_json, krd_id):
        """Получение составного значения из нескольких столбцов"""
        try:
            db_columns = json.loads(db_columns_json) if isinstance(db_columns_json, str) else db_columns_json
            
            if not db_columns:
                return None
            
            parts = []
            for col_info in db_columns:
                column_name = col_info.get('column')
                separator = col_info.get('separator', '')
                
                if not column_name:
                    continue
                
                value = self._get_value_from_database(table_name, column_name, krd_id)
                
                if value:
                    parts.append(str(value))
                    parts.append(separator)
            
            if parts:
                if parts[-1] in [', ', ' ', '; ', ': ', ' - ']:
                    parts.pop()
                return ''.join(parts)
            else:
                return None
        except Exception as e:
            print(f"❌ Ошибка получения составного значения: {e}")
            return None

    # ========================
    # МЕТОДЫ СОХРАНЕНИЯ
    # ========================

    def save_to_database(self):
        """Сохранение сгенерированного документа в базу данных"""
        if not self.generated_doc_path or not os.path.exists(self.generated_doc_path):
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте документ")
            return
        
        file_size = os.path.getsize(self.generated_doc_path)
        if file_size == 0:
            QMessageBox.warning(self, "Ошибка", "Сгенерированный документ пустой!")
            return
        
        request_type_id = self.request_type_combo.currentData()
        if not request_type_id:
            QMessageBox.warning(self, "Ошибка", "Выберите тип запроса")
            return
        
        recipient_name = self.recipient_input.text().strip()
        if not recipient_name:
            QMessageBox.warning(self, "Ошибка", "Введите адресата")
            return
        
        try:
            with open(self.generated_doc_path, 'rb') as f:
                document_bytes = f.read()
            
            if not document_bytes or len(document_bytes) == 0:
                raise Exception("Документ пустой или не был прочитан")
            
            print(f"📄 Размер документа для сохранения: {len(document_bytes)} байт")
            
            issue_number = self.generate_request_number()
            issue_date = QDate.currentDate()
            
            query = QSqlQuery(self.db)
            query.prepare("""
                INSERT INTO krd.outgoing_requests (
                    krd_id, request_type_id, recipient_name, military_unit_id,
                    issue_date, issue_number, document_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """)
            
            query.addBindValue(self.krd_id)
            query.addBindValue(request_type_id)
            query.addBindValue(recipient_name)
            query.addBindValue(None)
            query.addBindValue(issue_date)
            query.addBindValue(issue_number)
            query.addBindValue(QByteArray(document_bytes))
            
            if query.exec():
                request_id = query.lastInsertId()
                
                check_query = QSqlQuery(self.db)
                check_query.prepare("SELECT LENGTH(document_data) FROM krd.outgoing_requests WHERE id = ?")
                check_query.addBindValue(request_id)
                check_query.exec()
                
                if check_query.next():
                    saved_size = check_query.value(0)
                    print(f"✅ Документ сохранен в базу. Размер: {saved_size} байт")
                    
                    if saved_size == 0:
                        raise Exception("Документ сохранен как пустой!")
                
                QMessageBox.information(
                    self, 
                    "Успех", 
                    f"Запрос успешно сохранен в базу!\n\nID: {request_id}\nНомер: {issue_number}\nТип: {self.request_type_combo.currentText()}\nАдресат: {recipient_name}"
                )
                
                if self.audit_logger:
                    self.audit_logger.log_action(
                        action_type='REQUEST_CREATE',
                        table_name='outgoing_requests',
                        record_id=request_id,
                        krd_id=self.krd_id,
                        description=f'Создан запрос №{issue_number} для КРД-{self.krd_id} (Тип: {self.request_type_combo.currentText()}, Адресат: {recipient_name})'
                    )
                
                try:
                    os.unlink(self.generated_doc_path)
                    self.generated_doc_path = None
                except:
                    pass
                
                self.recipient_input.clear()
                
                parent = self.parent()
                if parent and hasattr(parent, 'load_requests'):
                    parent.load_requests()
                
            else:
                error_text = query.lastError().text()
                raise Exception(f"Ошибка сохранения запроса: {error_text}")
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения запроса в базу:\n{str(e)}")

    def generate_request_number(self):
        """Генерация номера запроса в формате КРД-{krd_id}/З-{номер}"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT COUNT(*) FROM krd.outgoing_requests 
            WHERE krd_id = ? AND issue_date = CURRENT_DATE
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        count = 1
        if query.next():
            count = query.value(0) + 1
        
        return f"КРД-{self.krd_id}/З-{count}"

    def save_to_disk(self):
        """Сохранение документа на диск (без сохранения в базу)"""
        if not self.generated_doc_path or not os.path.exists(self.generated_doc_path):
            QMessageBox.warning(self, "Ошибка", "Сначала сгенерируйте документ")
            return
        
        file_size = os.path.getsize(self.generated_doc_path)
        if file_size == 0:
            QMessageBox.warning(self, "Ошибка", "Сгенерированный документ пустой!")
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
                
                saved_size = os.path.getsize(path)
                print(f"✅ Документ сохранен на диск. Размер: {saved_size} байт")
                
                if saved_size == 0:
                    os.unlink(path)
                    raise Exception("Сохраненный файл пустой!")
                
                if self.audit_logger:
                    filename = os.path.basename(path)
                    self.audit_logger.log_document_save(self.krd_id, filename)
                
                try:
                    os.unlink(self.generated_doc_path)
                    self.generated_doc_path = None
                except:
                    pass
                
                QMessageBox.information(self, "Успех", f"Документ сохранён на диск:\n{path}\nРазмер: {saved_size} байт")
                
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{str(e)}")

    # ========================
    # МЕТОДЫ УПРАВЛЕНИЯ ШАБЛОНАМИ
    # ========================

    def create_templates_tab(self):
        """Создание вкладки управления шаблонами"""
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
        
        # Таблица шаблонов
        templates_group = QGroupBox("Список шаблонов")
        templates_layout = QVBoxLayout()
        
        # Создаем модель для таблицы шаблонов
        self.templates_model = QSqlQueryModel()
        
        # Создаем таблицу для отображения шаблонов
        self.templates_table = QTableView()
        self.templates_table.setModel(self.templates_model)
        self.templates_table.setAlternatingRowColors(True)
        self.templates_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.templates_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Настройка заголовков
        header = self.templates_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        # Установка ширины колонок
        self.templates_table.setColumnWidth(0, 60)   # ID
        self.templates_table.setColumnWidth(1, 200)  # Название
        self.templates_table.setColumnWidth(2, 300)  # Описание
        self.templates_table.setColumnWidth(3, 150)  # Дата создания
        
        # Включаем контекстное меню
        self.templates_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.templates_table.customContextMenuRequested.connect(self.show_context_menu)
        
        templates_layout.addWidget(self.templates_table)
        
        # Кнопки управления шаблонами
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Обновить список")
        refresh_btn.clicked.connect(self.load_document_templates)
        btn_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("Удалить шаблон")
        delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        delete_btn.clicked.connect(self.delete_selected_template)
        btn_layout.addWidget(delete_btn)
        
        templates_layout.addLayout(btn_layout)
        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)
        
        return widget

    def select_template_file(self):
        """Выбор файла шаблона"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл шаблона", "", "Word документы (*.docx);;Все файлы (*)"
        )
        if path:
            self.selected_file_path = path
            self.selected_file_label.setText(os.path.basename(path))

    def add_template(self):
        """Добавление нового шаблона в базу данных"""
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
                INSERT INTO krd.document_templates 
                (name, description, template_data, is_deleted)
                VALUES (:name, :description, :template_data, FALSE)
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
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления шаблона:\n{str(e)}")

    def load_document_templates(self):
        """Загрузка списка шаблонов из базы данных"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT id, name, description, created_at 
            FROM krd.document_templates 
            WHERE is_deleted = FALSE
            ORDER BY name
        """)
        query.exec()
        self.templates_model.setQuery(query)
        
        # Обновляем комбобокс для генерации
        self.template_combo.clear()
        query2 = QSqlQuery(self.db)
        query2.prepare("SELECT id, name FROM krd.document_templates WHERE is_deleted = FALSE ORDER BY name")
        query2.exec()
        while query2.next():
            self.template_combo.addItem(query2.value(1), query2.value(0))

    def show_context_menu(self, position: QPoint):
        """Отображение контекстного меню для таблицы шаблонов"""
        index = self.templates_table.indexAt(position)
        
        if not index.isValid():
            return
        
        menu = QMenu(self)
        
        delete_action = QAction("Удалить шаблон", self)
        delete_action.triggered.connect(self.delete_selected_template)
        menu.addAction(delete_action)
        
        menu.exec(self.templates_table.mapToGlobal(position))

    def delete_selected_template(self):
        """Удаление выбранного шаблона (мягкое удаление)"""
        # Получаем выделенную строку
        selection_model = self.templates_table.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Внимание", "Выберите шаблон для удаления")
            return
        
        selected_indexes = selection_model.selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Внимание", "Выберите шаблон для удаления")
            return
        
        index = selected_indexes[0]
        
        # Получаем данные о выбранном шаблоне
        template_id = self.templates_model.data(self.templates_model.index(index.row(), 0))
        template_name = self.templates_model.data(self.templates_model.index(index.row(), 1))
        
        # Показываем диалог подтверждения
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить шаблон?\n\n"
            f"Название: {template_name}\n\n"
            f"⚠️ Внимание: Шаблон будет скрыт из списка, но сохранён в базе данных.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        # Если пользователь подтвердил удаление
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Помечаем шаблон как удаленный
                query = QSqlQuery(self.db)
                query.prepare("""
                    UPDATE krd.document_templates 
                    SET is_deleted = TRUE, 
                        deleted_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """)
                query.addBindValue(template_id)
                
                if not query.exec():
                    raise Exception(f"Ошибка при удалении шаблона: {query.lastError().text()}")
                
                # Логирование удаления
                if self.audit_logger:
                    self.audit_logger.log_template_delete(template_id, template_name)
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Шаблон \"{template_name}\" успешно скрыт из списка!\n"
                    f"Шаблон сохранён в базе данных для истории."
                )
                
                # Обновляем список шаблонов
                self.load_document_templates()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Ошибка при удалении шаблона:\n{str(e)}"
                )

    def get_table_by_column(self, col):
        """Определение таблицы по имени столбца"""
        for tbl, cols in self.db_columns.items():
            if col in cols:
                return tbl
        return None