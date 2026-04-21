"""
Диалог для редактирования сопоставлений полей шаблона с данными из БД
"""

import os
import tempfile
import json
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QHeaderView, QAbstractItemView, QMessageBox,
    QComboBox, QDialogButtonBox, QGroupBox, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont
from docx import Document
from composite_field_widget import CompositeFieldWidget
from field_mapping_manager import FieldMappingManager


# === СПРАВОЧНИК: DB колонка → Русское описание ===
COLUMN_DESCRIPTIONS = {
    # social_data
    "surname": "Фамилия военнослужащего",
    "name": "Имя военнослужащего",
    "patronymic": "Отчество военнослужащего",
    "birth_date": "Дата рождения",
    "birth_place_town": "Населенный пункт места рождения",
    "birth_place_district": "Район места рождения",
    "birth_place_region": "Субъект РФ места рождения",
    "birth_place_country": "Страна места рождения",
    "tab_number": "Табельный номер",
    "personal_number": "Личный номер",
    "category_id": "ID категории военнослужащего",
    "rank_id": "ID воинского звания",
    "drafted_by_commissariat": "Наименование военкомата призыва",
    "draft_date": "Дата призыва на военную службу",
    "povsk": "Наименование ПОВСК",
    "selection_date": "Дата отбора на военную службу",
    "education": "Образование военнослужащего",
    "criminal_record": "Сведения о судимости",
    "social_media_account": "Аккаунты в социальных сетях",
    "bank_card_number": "Номер банковской карты",
    "passport_series": "Серия паспорта",
    "passport_number": "Номер паспорта",
    "passport_issue_date": "Дата выдачи паспорта",
    "passport_issued_by": "Кем выдан паспорт",
    "military_id_series": "Серия военного билета",
    "military_id_number": "Номер военного билета",
    "military_id_issue_date": "Дата выдачи военного билета",
    "military_id_issued_by": "Кем выдан военный билет",
    "appearance_features": "Особенности внешности",
    "personal_marks": "Личные приметы (татуировки, шрамы)",
    "federal_search_info": "Сведения о федеральном розыске",
    "military_contacts": "Контакты военнослужащего",
    "relatives_info": "Сведения о близких родственниках",
    
    # addresses
    "region": "📍 Субъект РФ (область, край, республика)",
    "district": "📍 Административный район",
    "town": "📍 Населенный пункт (город, село)",
    "street": "📍 Улица",
    "house": "📍 Номер дома",
    "building": "📍 Номер корпуса",
    "letter": "📍 Литера здания",
    "apartment": "📍 Номер квартиры",
    "room": "📍 Номер комнаты",
    "check_date": "📅 Дата адресной проверки",
    "check_result": "✅ Результат проверки",
    
    # service_places
    "place_name": "🎖️ Наименование места службы",
    "military_unit_id": "🎖️ ID военного управления",
    "garrison_id": "🎖️ ID гарнизона",
    "position_id": "🎖️ ID воинской должности",
    "commanders": "🎖️ Командиры (ФИО, контакты)",
    "postal_index": "📮 Почтовый индекс",
    "postal_region": "📮 Субъект РФ почтового адреса",
    "postal_district": "📮 Район почтового адреса",
    "postal_town": "📮 Город почтового адреса",
    "postal_street": "📮 Улица почтового адреса",
    "postal_house": "📮 Дом почтового адреса",
    "postal_building": "📮 Корпус почтового адреса",
    "postal_letter": "📮 Литера почтового адреса",
    "postal_apartment": "📮 Квартира почтового адреса",
    "postal_room": "📮 Комната почтового адреса",
    "place_contacts": "📞 Контакты места службы",
    
    # soch_episodes
    "soch_date": "⚠️ Дата СОЧ",
    "soch_location": "⚠️ Место СОЧ",
    "order_date_number": "⚠️ Дата и номер приказа о СОЧ",
    "witnesses": "⚠️ Очевидцы СОЧ",
    "reasons": "⚠️ Вероятные причины СОЧ",
    "weapon_info": "⚠️ Сведения о наличии оружия",
    "clothing": "⚠️ Описание одежды",
    "movement_options": "⚠️ Возможные направления движения",
    "other_info": "⚠️ Другая значимая информация",
    "duty_officer_commissariat": "📞 Дежурный по военкомату",
    "duty_officer_omvd": "📞 Дежурный по ОМВД",
    "investigation_info": "📋 Сведения о проверке",
    "prosecution_info": "📋 Сведения о прокуратуре",
    "criminal_case_info": "📋 Сведения об уголовном деле",
    "search_date": "🔍 Дата розыска",
    "found_by": "✅ Кем разыскан",
    "search_circumstances": "🔍 Обстоятельства розыска",
    "notification_recipient": "📬 Адресат уведомления",
    "notification_date": "📅 Дата уведомления",
    "notification_number": "📬 Номер уведомления"
}


class MappingEditorDialog(QDialog):
    """Отдельное окно для редактирования сопоставлений"""
    
    def __init__(self, parent=None, krd_id=None, db_connection=None, template_id=None, audit_logger=None):
        super().__init__(parent)
        self.krd_id = krd_id
        self.db = db_connection
        self.template_id = template_id
        self.audit_logger = audit_logger
        self.template_variables = []
        self.db_columns = {}
        self.current_template_id = template_id
        
        # Инициализация модулей
        self.composite_widget = CompositeFieldWidget(self)
        self.mapping_manager = FieldMappingManager(self)
        
        self.setWindowTitle("✏️ Редактирование сопоставлений полей")
        self.setMinimumSize(1100, 750)
        self.setModal(False)  # Не модальное окно
        
        self.init_ui()
        if template_id:
            self.load_field_mappings(template_id)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel("🔗 Сопоставление полей шаблона с данными из БД")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        info_label = QLabel("💡 Выберите переменную из шаблона и укажите, какое поле из базы данных должно быть подставлено")
        info_label.setStyleSheet("QLabel { color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 5px; }")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Таблица сопоставлений
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels([
            "Переменная из шаблона",
            "Поле из базы данных",
            "Тип"
        ])
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.mapping_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.mapping_table.setColumnWidth(2, 100)
        
        layout.addWidget(self.mapping_table)
        
        # Кнопки управления
        btn_group = QGroupBox("Управление сопоставлениями")
        btn_layout = QHBoxLayout(btn_group)
        
        add_simple_btn = QPushButton("➕ Добавить простое сопоставление")
        add_simple_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        add_simple_btn.clicked.connect(self.add_field_mapping)
        btn_layout.addWidget(add_simple_btn)
        
        add_composite_btn = QPushButton("🔗 Добавить составное поле")
        add_composite_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        add_composite_btn.clicked.connect(self.add_composite_field_mapping)
        btn_layout.addWidget(add_composite_btn)
        
        delete_btn = QPushButton("🗑️ Удалить выбранное")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(self.remove_field_mapping)
        btn_layout.addWidget(delete_btn)
        
        layout.addWidget(btn_group)
        
        # Кнопки сохранения и закрытия
        button_box = QDialogButtonBox()
        save_btn = QPushButton("💾 Сохранить сопоставления")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 12px 30px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_and_close)
        
        cancel_btn = QPushButton("❌ Закрыть без сохранения")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                font-weight: bold;
                padding: 12px 30px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addButton(save_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        # Загрузка данных
        self.load_template_variables(self.template_id)
        self.load_db_columns()
    
    def add_field_mapping(self):
        """Добавление простого сопоставления"""
        if not self.current_template_id:
            QMessageBox.warning(self, "Ошибка", "Шаблон не выбран")
            return
        
        if not self.template_variables:
            QMessageBox.warning(self, "Ошибка", "Переменные шаблона не загружены")
            return
        
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)
        
        var_combo = QComboBox()
        var_combo.addItems(self.template_variables)
        self.mapping_table.setCellWidget(row, 0, var_combo)
        
        col_combo = self._create_db_column_combo()
        self.mapping_table.setCellWidget(row, 1, col_combo)
        
        type_label = QLabel("Простое")
        type_label.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        self.mapping_table.setCellWidget(row, 2, type_label)
        
        self.mapping_table.resizeRowToContents(row)
        self.mapping_table.selectRow(row)
    
    def add_composite_field_mapping(self):
        """Добавление составного поля"""
        if not self.current_template_id:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон")
            return
        
        if not self.template_variables:
            QMessageBox.warning(self, "Ошибка", "Переменные шаблона не загружены")
            return
        
        row = self.mapping_table.rowCount()
        self.composite_widget.add_composite_field_mapping(row)
    
    def remove_field_mapping(self):
        """Удаление сопоставления"""
        selected_rows = self.mapping_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите сопоставление для удаления")
            return
        
        row = selected_rows[0].row()
        self.mapping_table.removeRow(row)
    
    # === НОВЫЕ МЕТОДЫ ДЛЯ ЗАГРУЗКИ СОПОСТАВЛЕНИЙ ===
    
    def add_simple_mapping_row(self, row, field_name, db_column, table_name):
        """Добавление простого сопоставления при загрузке из БД"""
        self.mapping_table.insertRow(row)
        
        var_combo = QComboBox()
        var_combo.addItems(self.template_variables)
        var_combo.setCurrentText(field_name)
        self.mapping_table.setCellWidget(row, 0, var_combo)
        
        col_combo = self._create_db_column_combo(db_column)
        self.mapping_table.setCellWidget(row, 1, col_combo)
        
        type_label = QLabel("Простое")
        type_label.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        self.mapping_table.setCellWidget(row, 2, type_label)
        
        self.mapping_table.resizeRowToContents(row)
    
    def add_composite_mapping_row(self, row, field_name, db_columns_json, table_name):
        """Добавление составного сопоставления при загрузке из БД"""
        self.composite_widget.create_composite_field_row(
            row, field_name, db_columns_json, table_name, self.mapping_table
        )
    
    def load_field_mappings(self, template_id):
        """Загрузка сопоставлений"""
        self.mapping_table.setRowCount(0)
        self.mapping_manager.load_field_mappings(template_id)
    
    # ==============================================
    
    def _create_db_column_combo(self, selected_column=None):
        """Создание ComboBox с русскими описаниями полей БД"""
        combo = QComboBox()
        combo.setEditable(False)
        combo.setMaxVisibleItems(50)
        combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        combo.view().setMinimumHeight(400)
        combo.setMinimumWidth(350)
        combo.setMaximumWidth(600)
        
        all_columns = []
        for table_name, columns in self.db_columns.items():
            for col in columns:
                if col in COLUMN_DESCRIPTIONS:
                    all_columns.append((col, COLUMN_DESCRIPTIONS[col]))
        
        all_columns.sort(key=lambda x: x[1])
        
        for col_name, col_description in all_columns:
            combo.addItem(col_description, col_name)
        
        if selected_column:
            index = combo.findData(selected_column)
            if index >= 0:
                combo.setCurrentIndex(index)
        
        return combo
    
    def load_template_variables(self, template_id):
        """Загрузка переменных из шаблона"""
        if not template_id:
            return
        
        query = QSqlQuery(self.db)
        query.prepare("SELECT template_data FROM krd.document_templates WHERE id = ?")
        query.addBindValue(template_id)
        
        if not query.exec() or not query.next():
            self.template_variables = []
            return
        
        data = query.value(0)
        template_bytes = bytes(data) if isinstance(data, QByteArray) else bytes(data) if data else b''
        
        if not template_bytes:
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
            
        except Exception as e:
            print(f"❌ Ошибка загрузки переменных: {e}")
            self.template_variables = ["{{surname}}", "{{name}}", "{{patronymic}}"]
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def load_db_columns(self):
        """Загрузка структуры столбцов базы данных"""
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
                "region", "district", "town", "street", "house",
                "building", "letter", "apartment", "room", "check_date", "check_result"
            ],
            "service_places": [
                "place_name", "military_unit_id", "garrison_id", "position_id", "commanders",
                "postal_index", "postal_region", "postal_district", "postal_town", "postal_street",
                "postal_house", "postal_building", "postal_letter", "postal_apartment", "postal_room",
                "place_contacts"
            ],
            "soch_episodes": [
                "soch_date", "soch_location", "order_date_number", "witnesses",
                "reasons", "weapon_info", "clothing", "movement_options", "other_info",
                "duty_officer_commissariat", "duty_officer_omvd", "investigation_info",
                "prosecution_info", "criminal_case_info", "search_date", "found_by",
                "search_circumstances", "notification_recipient", "notification_date",
                "notification_number"
            ]
        }
    
    def save_and_close(self):
        """Сохранение и закрытие"""
        if not self.current_template_id:
            QMessageBox.critical(self, "Ошибка", "Шаблон не выбран")
            return
        
        if self.mapping_manager.save_field_mappings(self.current_template_id):
            QMessageBox.information(self, "Успех", "✅ Сопоставления успешно сохранены!")
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "❌ Не удалось сохранить сопоставления")