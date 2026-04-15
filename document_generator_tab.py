"""
Модуль для генерации документов из Word-шаблонов
С поддержкой составных полей, выбора записей и автоматического сохранения в БД
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
    QTableView, QMenu, QSpacerItem, QSizePolicy, QToolTip, QSplitter
)
from PyQt6.QtCore import Qt, QByteArray, QPoint, QDate, QRect
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont, QContextMenuEvent, QAction, QCursor
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


# === СПРАВОЧНИК: DB колонка → Русское описание ===
COLUMN_DESCRIPTIONS = {
    # ========================
    # СОЦИАЛЬНО-ДЕМОГРАФИЧЕСКИЕ ДАННЫЕ (social_data)
    # ========================
    "surname": "Фамилия военнослужащего",
    "name": "Имя военнослужащего",
    "patronymic": "Отчество военнослужащего",
    "birth_date": "Дата рождения",
    "birth_place_town": "Населенный пункт места рождения (город, село)",
    "birth_place_district": "Район места рождения",
    "birth_place_region": "Субъект РФ места рождения (область, край, республика)",
    "birth_place_country": "Страна места рождения",
    "tab_number": "Табельный номер",
    "personal_number": "Личный номер",
    "category_name": "Категория военнослужащего (офицер, солдат и т.д.)",
    "rank_name": "Воинское звание",
    "drafted_by_commissariat": "Наименование военкомата призыва",
    "draft_date": "Дата призыва на военную службу",
    "povsk": "Наименование ПОВСК (пункт отбора на военную службу по контракту)",
    "selection_date": "Дата отбора на военную службу",
    "education": "Образование военнослужащего",
    "criminal_record": "Сведения о судимости",
    "social_media_account": "Аккаунты в социальных сетях",
    "bank_card_number": "Номер банковской карты",
    "passport_series": "Серия паспорта",
    "passport_number": "Номер паспорта",
    "passport_issue_date": "Дата выдачи паспорта",
    "passport_issued_by": "Кем выдан паспорт (наименование органа)",
    "military_id_series": "Серия военного билета",
    "military_id_number": "Номер военного билета",
    "military_id_issue_date": "Дата выдачи военного билета",
    "military_id_issued_by": "Кем выдан военный билет",
    "appearance_features": "Особенности внешности (рост, телосложение и т.д.)",
    "personal_marks": "Личные приметы (татуировки, шрамы, родимые пятна)",
    "federal_search_info": "Сведения о федеральном розыске",
    "military_contacts": "Контакты военнослужащего (телефон, email)",
    "relatives_info": "Сведения о близких родственниках (ФИО, контакты, адреса)",
    
    # ========================
    # АДРЕСА ПРОЖИВАНИЯ (addresses)
    # ========================
    "region": "📍 Субъект РФ (область, край, республика, автономный округ)",
    "district": "📍 Административный район (район области/края)",
    "town": "📍 Населенный пункт (город, посёлок, село, деревня)",
    "street": "📍 Улица (наименование улицы, проспекта, переулка)",
    "house": "📍 Номер дома (основной номер здания)",
    "building": "📍 Номер корпуса (корпус, строение, владение)",
    "letter": "📍 Литера (буквенное обозначение здания: А, Б, В и т.д.)",
    "apartment": "📍 Номер квартиры (номер жилого помещения)",
    "room": "📍 Номер комнаты (номер комнаты в коммунальной квартире/общежитии)",
    "check_date": "📅 Дата проведения адресной проверки (когда проверяли адрес)",
    "check_result": "✅ Результат адресной проверки (найден, не найден, выбыл, иное)",
    
    # ========================
    # МЕСТА СЛУЖБЫ (service_places)
    # ========================
    "place_name": "🎖️ Наименование места службы (воинская часть, подразделение)",
    "military_unit_name": "🎖️ Воинское управление (ЦВО, ЮВО, ЗВО, ВДВ и т.д.)",
    "garrison_name": "🎖️ Гарнизон (наименование военного гарнизона)",
    "position_name": "🎖️ Воинская должность (наименование должности)",
    "commanders": "🎖️ Командиры (начальники) с контактами (ФИО, телефоны)",
    "postal_index": "📮 Почтовый индекс (цифровой код почтового отделения)",
    "postal_region": "📮 Субъект РФ почтового адреса (для корреспонденции)",
    "postal_district": "📮 Район почтового адреса",
    "postal_town": "📮 Населенный пункт почтового адреса (город для почты)",
    "postal_street": "📮 Улица почтового адреса",
    "postal_house": "📮 Дом почтового адреса",
    "postal_building": "📮 Корпус почтового адреса",
    "postal_letter": "📮 Литера почтового адреса",
    "postal_apartment": "📮 Квартира почтового адреса",
    "postal_room": "📮 Комната почтового адреса",
    "place_contacts": "📞 Контакты места службы (телефоны, email)",
    
    # ========================
    # ЭПИЗОДЫ СОЧ (soch_episodes)
    # ========================
    "soch_date": "⚠️ Дата самовольного оставления части (когда ушёл)",
    "soch_location": "⚠️ Место СОЧ (откуда ушёл: часть, КПП, увольнение и т.д.)",
    "order_date_number": "⚠️ Дата и номер приказа о СОЧ (приказ об объявлении в розыск)",
    "witnesses": "⚠️ Очевидцы СОЧ (ФИО, контакты свидетелей)",
    "reasons": "⚠️ Вероятные причины СОЧ (мотивы, обстоятельства)",
    "weapon_info": "⚠️ Сведения о наличии оружия (что было при себе)",
    "clothing": "⚠️ Описание одежды (во что был одет при уходе)",
    "movement_options": "⚠️ Возможные направления движения (куда мог направиться)",
    "other_info": "⚠️ Другая значимая информация (дополнительные сведения)",
    "duty_officer_commissariat": "📞 Дежурный по военкомату (ФИО, телефон)",
    "duty_officer_omvd": "📞 Дежурный по ОМВД (ФИО, телефон)",
    "investigation_info": "📋 Сведения о проверке (кто проводит, статус)",
    "prosecution_info": "📋 Сведения о прокуратуре (контакты, номер дела)",
    "criminal_case_info": "📋 Сведения об уголовном деле (номер, статья УК)",
    "search_date": "🔍 Дата розыска (когда начаты розыскные мероприятия)",
    "found_by": "✅ Кем разыскан (кто обнаружил: полиция, часть, граждане)",
    "search_circumstances": "🔍 Обстоятельства розыска (где и как найден)",
    "notification_recipient": "📬 Адресат уведомления (кому отправлено уведомление)",
    "notification_date": "📅 Дата уведомления (когда отправлено)",
    "notification_number": "📬 Номер уведомления (исходящий номер документа)"
}

# === ОБРАТНЫЙ СПРАВОЧНИК: Русское описание → DB колонка ===
DESCRIPTION_TO_COLUMN = {v: k for k, v in COLUMN_DESCRIPTIONS.items()}


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
        self.current_template_id = None
        
        # Выбранные записи из связанных таблиц
        self.selected_address_id = None
        self.selected_service_place_id = None
        self.selected_soch_episode_id = None
        
        # Инициализация модулей
        self.composite_widget = CompositeFieldWidget(self)
        self.mapping_manager = FieldMappingManager(self)
        self.db_handler = DatabaseHandler(self.db)
        
        print(f"\n{'='*60}")
        print(f"🔧 DocumentGeneratorTab инициализирован для КРД-{krd_id}")
        print(f"{'='*60}\n")
        
        self.init_ui()
        self.load_document_templates()
        self.load_related_records()
    
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
        
        # === Выбор записей из связанных таблиц ===
        records_group = QGroupBox("📋 Выбор записей для подстановки")
        records_layout = QGridLayout(records_group)
        records_layout.setSpacing(10)
        
        # Адреса проживания
        records_layout.addWidget(QLabel("🏠 Адрес проживания:"), 0, 0)
        self.address_combo = QComboBox()
        self.address_combo.addItem("— Не выбрано —", None)
        self.address_combo.currentIndexChanged.connect(self.on_address_selected)
        records_layout.addWidget(self.address_combo, 0, 1)
        
        # Места службы
        records_layout.addWidget(QLabel("🎖️ Место службы:"), 0, 2)
        self.service_place_combo = QComboBox()
        self.service_place_combo.addItem("— Не выбрано —", None)
        self.service_place_combo.currentIndexChanged.connect(self.on_service_place_selected)
        records_layout.addWidget(self.service_place_combo, 0, 3)
        
        # Эпизоды СОЧ
        records_layout.addWidget(QLabel("⚠️ Эпизод СОЧ:"), 1, 0)
        self.soch_episode_combo = QComboBox()
        self.soch_episode_combo.addItem("— Не выбрано —", None)
        self.soch_episode_combo.currentIndexChanged.connect(self.on_soch_episode_selected)
        records_layout.addWidget(self.soch_episode_combo, 1, 1)
        
        # Кнопка обновления
        refresh_records_btn = QPushButton("🔄 Обновить списки")
        refresh_records_btn.clicked.connect(self.load_related_records)
        records_layout.addWidget(refresh_records_btn, 1, 2, 1, 2)
        
        layout.addWidget(records_group)
        
        # Выбор шаблона
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("📄 Шаблон документа:"))
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(300)
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_layout.addWidget(self.template_combo)
        
        save_mapping_btn = QPushButton("💾 Сохранить сопоставления")
        save_mapping_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        save_mapping_btn.clicked.connect(self.save_mappings_now)
        template_layout.addWidget(save_mapping_btn)
        
        layout.addLayout(template_layout)
        
        # === Поля для метаданных запроса ===
        metadata_group = QGroupBox("📝 Информация о запросе (сохраняется в базу данных)")
        metadata_layout = QGridLayout(metadata_group)
        
        metadata_layout.addWidget(QLabel("Тип запроса *:"), 0, 0)
        self.request_type_combo = QComboBox()
        self.load_request_types()
        metadata_layout.addWidget(self.request_type_combo, 0, 1)
        
        metadata_layout.addWidget(QLabel("Адресат *:"), 0, 2)
        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Наименование организации")
        metadata_layout.addWidget(self.recipient_input, 0, 3)
        
        layout.addWidget(metadata_group)
        
        # === Таблица сопоставления полей ===
        mapping_group = QGroupBox("🔗 Сопоставление полей шаблона с данными из БД")
        mapping_layout = QVBoxLayout()
        
        info_label = QLabel("💡 Выберите переменную из шаблона и укажите, какое поле из базы данных должно быть подставлено")
        info_label.setStyleSheet("QLabel { color: #666; padding: 5px; background-color: #f0f0f0; border-radius: 3px; }")
        info_label.setWordWrap(True)
        mapping_layout.addWidget(info_label)
        
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
        self.mapping_table.setColumnWidth(2, 80)
        
        mapping_layout.addWidget(self.mapping_table)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("➕ Добавить сопоставление", clicked=self.add_field_mapping))
        btn_layout.addWidget(QPushButton("🔗 Добавить составное поле", clicked=self.add_composite_field_mapping))
        btn_layout.addWidget(QPushButton("🗑️ Удалить сопоставление", clicked=self.remove_field_mapping))
        mapping_layout.addLayout(btn_layout)
        
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # === ЕДИНАЯ КНОПКА ===
        generate_btn = QPushButton("📄 Сформировать документ и сохранить в базу")
        generate_btn.setMinimumHeight(50)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        generate_btn.clicked.connect(self.generate_and_save_document)
        layout.addWidget(generate_btn)
        
        return widget
    
    # ========================
    # МЕТОДЫ ДЛЯ РАБОТЫ С РУССКИМИ НАЗВАНИЯМИ
    # ========================
    
    def _get_column_description(self, column_name):
        """Получение русского описания для колонки БД"""
        return COLUMN_DESCRIPTIONS.get(column_name, column_name)
    
    def _get_column_name(self, description):
        """Получение имени колонки БД из русского описания"""
        return DESCRIPTION_TO_COLUMN.get(description, description)
    
    def _create_db_column_combo(self, selected_column=None):
        """Создание ComboBox с русскими описаниями полей БД"""
        combo = QComboBox()
        combo.setEditable(False)
        
        # Собираем все доступные колонки
        all_columns = []
        for table_name, columns in self.db_columns.items():
            for col in columns:
                if col in COLUMN_DESCRIPTIONS:
                    all_columns.append((col, COLUMN_DESCRIPTIONS[col]))
        
        # Сортируем по описанию
        all_columns.sort(key=lambda x: x[1])
        
        # Добавляем в ComboBox: отображаем описание, храним имя колонки
        for col_name, col_description in all_columns:
            combo.addItem(col_description, col_name)
        
        # Выбираем нужную колонку
        if selected_column:
            index = combo.findData(selected_column)
            if index >= 0:
                combo.setCurrentIndex(index)
        
        return combo
    
    def load_related_records(self):
        """Загрузка записей из связанных таблиц для выбора"""
        print(f"\n{'='*60}")
        print(f"🔄 Загрузка связанных записей для КРД-{self.krd_id}")
        print(f"{'='*60}")
        
        # Адреса
        self.address_combo.clear()
        self.address_combo.addItem("— Не выбрано —", None)
        
        addr_query = QSqlQuery(self.db)
        addr_query.prepare("""
            SELECT id, 
                   COALESCE(region, '') || ', ' || 
                   COALESCE(district, '') || ', ' || 
                   COALESCE(town, '') || ', ' || 
                   COALESCE(street, '') || ', ' || 
                   COALESCE(house, '') as address_string
            FROM krd.addresses
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        addr_query.addBindValue(self.krd_id)
        
        if addr_query.exec():
            count = 0
            while addr_query.next():
                addr_id = addr_query.value(0)
                addr_string = addr_query.value(1)
                if addr_string.strip(', '):
                    self.address_combo.addItem(f"🏠 {addr_string}", addr_id)
                    count += 1
            print(f"✅ Загружено {count} адресов")
        
        # Места службы
        self.service_place_combo.clear()
        self.service_place_combo.addItem("— Не выбрано —", None)
        
        sp_query = QSqlQuery(self.db)
        sp_query.prepare("""
            SELECT id, 
                   COALESCE(place_name, 'Без названия') || 
                   ' (' || COALESCE(postal_town, 'Город не указан') || ')'
            FROM krd.service_places
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        sp_query.addBindValue(self.krd_id)
        
        if sp_query.exec():
            count = 0
            while sp_query.next():
                sp_id = sp_query.value(0)
                sp_string = sp_query.value(1)
                self.service_place_combo.addItem(f"🎖️ {sp_string}", sp_id)
                count += 1
            print(f"✅ Загружено {count} мест службы")
        
        # Эпизоды СОЧ
        self.soch_episode_combo.clear()
        self.soch_episode_combo.addItem("— Не выбрано —", None)
        
        soch_query = QSqlQuery(self.db)
        soch_query.prepare("""
            SELECT id, 
                   COALESCE(soch_date, 'Дата не указана') || ' - ' || 
                   COALESCE(soch_location, 'Место не указано')
            FROM krd.soch_episodes
            WHERE krd_id = ?
            ORDER BY soch_date DESC
        """)
        soch_query.addBindValue(self.krd_id)
        
        if soch_query.exec():
            count = 0
            while soch_query.next():
                soch_id = soch_query.value(0)
                soch_string = soch_query.value(1)
                self.soch_episode_combo.addItem(f"⚠️ {soch_string}", soch_id)
                count += 1
            print(f"✅ Загружено {count} эпизодов СОЧ")
        
        print(f"{'='*60}\n")
    
    def on_address_selected(self, index):
        self.selected_address_id = self.address_combo.currentData()
        print(f"🏠 Выбран адрес ID: {self.selected_address_id}")
    
    def on_service_place_selected(self, index):
        self.selected_service_place_id = self.service_place_combo.currentData()
        print(f"🎖️ Выбрано место службы ID: {self.selected_service_place_id}")
    
    def on_soch_episode_selected(self, index):
        self.selected_soch_episode_id = self.soch_episode_combo.currentData()
        print(f"⚠️ Выбран эпизод СОЧ ID: {self.selected_soch_episode_id}")
    
    def generate_and_save_document(self):
        """Генерация документа с автоматическим сохранением в базу данных"""
        print(f"\n{'='*60}")
        print(f"📄 ГЕНЕРАЦИЯ И СОХРАНЕНИЕ ДОКУМЕНТА")
        print(f"{'='*60}")
        
        # Проверка шаблона
        template_id = self.template_combo.currentData()
        if not template_id:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон документа")
            return
        
        # Проверка метаданных
        request_type_id = self.request_type_combo.currentData()
        if not request_type_id:
            QMessageBox.warning(self, "Ошибка", "Выберите тип запроса")
            return
        
        recipient_name = self.recipient_input.text().strip()
        if not recipient_name:
            QMessageBox.warning(self, "Ошибка", "Введите адресата")
            return
        
        print(f"📋 Template ID: {template_id}")
        
        # Сохранение сопоставлений
        if not self.save_mappings_now():
            print("❌ Ошибка: Не удалось сохранить сопоставления")
            return
        
        try:
            # === 1. Загрузка шаблона ===
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
            
            # === 2. Генерация документа ===
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
            
            # === 3. Сохранение в базу данных ===
            print(f"\n💾 Сохранение в базу данных...")
            
            issue_number = self.generate_request_number()
            issue_date = QDate.currentDate()
            
            with open(self.generated_doc_path, 'rb') as f:
                document_bytes = f.read()
            
            save_query = QSqlQuery(self.db)
            save_query.prepare("""
                INSERT INTO krd.outgoing_requests (
                    krd_id, request_type_id, recipient_name, military_unit_id,
                    issue_date, issue_number, document_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """)
            
            save_query.addBindValue(self.krd_id)
            save_query.addBindValue(request_type_id)
            save_query.addBindValue(recipient_name)
            save_query.addBindValue(None)
            save_query.addBindValue(issue_date)
            save_query.addBindValue(issue_number)
            save_query.addBindValue(QByteArray(document_bytes))
            
            if not save_query.exec():
                raise Exception(f"Ошибка сохранения: {save_query.lastError().text()}")
            
            request_id = save_query.lastInsertId()
            
            check_query = QSqlQuery(self.db)
            check_query.prepare("SELECT LENGTH(document_data) FROM krd.outgoing_requests WHERE id = ?")
            check_query.addBindValue(request_id)
            check_query.exec()
            
            if check_query.next():
                saved_size = check_query.value(0)
                print(f"✅ Документ сохранен в базу. Размер: {saved_size} байт")
                
                if saved_size == 0:
                    raise Exception("Документ сохранен как пустой!")
            
            try:
                os.unlink(self.generated_doc_path)
                self.generated_doc_path = None
            except:
                pass
            
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='REQUEST_CREATE',
                    table_name='outgoing_requests',
                    record_id=request_id,
                    krd_id=self.krd_id,
                    description=f'Создан запрос №{issue_number} для КРД-{self.krd_id}'
                )
            
            parent = self.parent()
            if parent and hasattr(parent, 'load_requests'):
                parent.load_requests()
            
            QMessageBox.information(
                self, 
                "Успех", 
                f"✅ Документ успешно сгенерирован и сохранён в базу!\n\n"
                f"📄 Шаблон: {template_name}\n"
                f"🔢 Запрос №: {issue_number}\n"
                f"📋 Тип: {self.request_type_combo.currentText()}\n"
                f"📬 Адресат: {recipient_name}\n"
                f"📊 Переменных заменено: {replacements}\n"
                f"💾 Размер файла: {file_size} байт"
            )
            
            self.recipient_input.clear()
            
        except Exception as e:
            print(f"❌ Ошибка генерации/сохранения: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка:\n{str(e)}")
        
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
        """Получение данных для подстановки из базы данных"""
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
            
            if is_composite and db_columns_json:
                value = self._get_composite_value(table_name, db_columns_json, self.krd_id)
            else:
                selected_id = None
                if table_name == "addresses":
                    selected_id = self.selected_address_id
                elif table_name == "service_places":
                    selected_id = self.selected_service_place_id
                elif table_name == "soch_episodes":
                    selected_id = self.selected_soch_episode_id
                
                if selected_id:
                    value = self._get_value_from_specific_record(table_name, db_column, selected_id)
                    print(f"   📌 {field_name} = {value} (из выбранной записи ID={selected_id})")
                else:
                    value = self._get_value_from_database(table_name, db_column, self.krd_id)
                    print(f"   📌 {field_name} = {value} (из последней записи)")
            
            if field_name in context:
                print(f"   ⚠️ ПРЕДУПРЕЖДЕНИЕ: {field_name} уже существует в контексте!")
            
            if value is not None:
                context[field_name] = value
                count += 1
        
        print(f"✅ Получено {count} значений")
        print(f"📊 Уникальных переменных в контексте: {len(context)}")
        
        return context
    
    def _get_value_from_specific_record(self, table_name, column_name, record_id):
        """Получение значения из конкретной записи по ID"""
        if not re.match(r'^\w+$', table_name) or not re.match(r'^\w+$', column_name):
            return ""
        
        query = QSqlQuery(self.db)
        query.prepare(f"SELECT {column_name} FROM krd.{table_name} WHERE id = ?")
        query.addBindValue(record_id)
        
        if query.exec() and query.next():
            value = query.value(0)
            if hasattr(value, 'getDate'):
                year, month, day = value.getDate()
                return f"{day:02d}.{month:02d}.{year}"
            elif value is not None:
                return str(value)
        
        return ""
    
    def _get_value_from_database(self, table_name, column_name, krd_id):
        """Получение значения из базы данных (последняя запись)"""
        join_col = "krd_id" if table_name != "krd" else "id"
        
        if not re.match(r'^\w+$', table_name) or not re.match(r'^\w+$', column_name):
            return ""
        
        query = QSqlQuery(self.db)
        query.prepare(f"SELECT {column_name} FROM krd.{table_name} WHERE {join_col} = ? ORDER BY id DESC LIMIT 1")
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
    
    def generate_request_number(self):
        """Генерация номера запроса"""
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
    
    def add_field_mapping(self):
        """Добавление простого сопоставления"""
        print(f"\n{'='*60}")
        print(f"📝 ДОБАВЛЕНИЕ ПРОСТОГО СОПОСТАВЛЕНИЯ")
        print(f"{'='*60}")
        
        try:
            if self.template_combo.count() == 0:
                print("❌ Ошибка: Шаблоны не загружены")
                QMessageBox.warning(self, "Ошибка", "Сначала добавьте шаблон")
                return
            
            tid = self.template_combo.currentData()
            
            if not tid:
                print("❌ Ошибка: Шаблон не выбран")
                QMessageBox.warning(self, "Ошибка", "Выберите шаблон")
                return
            
            if not self.template_variables:
                self.load_template_variables(tid)
            
            if not self.db_columns:
                self.load_db_columns()
            
            if not self.template_variables:
                QMessageBox.warning(self, "Ошибка", "Не загружены переменные шаблона")
                return
            
            if not self.db_columns:
                QMessageBox.warning(self, "Ошибка", "Не загружены поля БД")
                return
            
            row = self.mapping_table.rowCount()
            self.mapping_table.insertRow(row)
            
            var_combo = QComboBox()
            var_combo.addItems(self.template_variables)
            self.mapping_table.setCellWidget(row, 0, var_combo)
            
            # === НОВОЕ: ComboBox с русскими описаниями ===
            col_combo = self._create_db_column_combo()
            self.mapping_table.setCellWidget(row, 1, col_combo)
            
            type_label = QLabel("Простое")
            type_label.setStyleSheet("color: #666; font-size: 10px;")
            self.mapping_table.setCellWidget(row, 2, type_label)
            
            self.mapping_table.resizeRowToContents(row)
            self.mapping_table.selectRow(row)
            
            print(f"✅ Сопоставление добавлено в строку #{row}")
            print(f"   Переменная: {var_combo.currentText()}")
            print(f"   Поле БД: {col_combo.currentData()} ({col_combo.currentText()})")
            
            self.save_mappings_now()
            
            if self.audit_logger:
                field_name = var_combo.currentText()
                db_column = col_combo.currentData()
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
        """Добавление составного поля"""
        if not self.current_template_id:
            QMessageBox.warning(self, "Ошибка", "Выберите шаблон")
            return
        
        row = self.mapping_table.rowCount()
        self.composite_widget.add_composite_field_mapping(row)
        self.save_mappings_now()
    
    def remove_field_mapping(self):
        """Удаление сопоставления"""
        selected_rows = self.mapping_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Внимание", "Выберите сопоставление для удаления")
            return
        
        row = selected_rows[0].row()
        
        var_widget = self.mapping_table.cellWidget(row, 0)
        col_widget = self.mapping_table.cellWidget(row, 1)
        
        if not var_widget or not col_widget:
            return
        
        var_name = var_widget.currentText()
        is_composite = hasattr(col_widget, 'layout')
        col_name = "Составное поле" if is_composite else col_widget.currentData()
        
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Удалить сопоставление?\nПеременная: {var_name}\nПоле: {col_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.current_template_id:
                    field_name_clean = var_name.strip('{} ')
                    self.mapping_manager.delete_field_mapping(
                        self.current_template_id, 
                        field_name_clean, 
                        col_name
                    )
                
                self.mapping_table.removeRow(row)
                
                if self.audit_logger:
                    self.audit_logger.log_mapping_delete(
                        field_name=field_name_clean,
                        db_column=col_name
                    )
                
                QMessageBox.information(self, "Успех", "Сопоставление удалено")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка удаления:\n{str(e)}")
    
    def on_template_changed(self):
        tid = self.template_combo.currentData()
        template_name = self.template_combo.currentText()
        
        if tid:
            self.current_template_id = tid
            if self.audit_logger:
                self.audit_logger.log_template_view(tid, template_name)
            self.load_field_mappings(tid)
        else:
            self.current_template_id = None
    
    def save_mappings_now(self):
        if not self.current_template_id:
            return False
        
        result = self.mapping_manager.save_field_mappings(self.current_template_id)
        
        if result:
            QMessageBox.information(self, "Успех", "Сопоставления сохранены!")
        
        return result
    
    def load_field_mappings(self, template_id):
        print(f"\n{'='*60}")
        print(f"📥 ЗАГРУЗКА СОПОСТАВЛЕНИЙ")
        print(f"{'='*60}")
        
        try:
            self.mapping_table.setRowCount(0)
            
            self.load_template_variables(template_id)
            self.load_db_columns()
            
            self.mapping_manager.load_field_mappings(template_id)
            
            row_count = self.mapping_table.rowCount()
            print(f"✅ Загружено сопоставлений: {row_count}")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            traceback.print_exc()
    
    def add_simple_mapping_row(self, row, field_name, db_column, table_name):
        """Добавление простого сопоставления с русским описанием"""
        self.mapping_table.insertRow(row)
        
        var_combo = QComboBox()
        var_combo.addItems(self.template_variables)
        var_combo.setCurrentText(field_name)
        self.mapping_table.setCellWidget(row, 0, var_combo)
        
        # === НОВОЕ: ComboBox с русским описанием ===
        col_combo = self._create_db_column_combo(db_column)
        self.mapping_table.setCellWidget(row, 1, col_combo)
        
        type_label = QLabel("Простое")
        type_label.setStyleSheet("color: #666; font-size: 10px;")
        self.mapping_table.setCellWidget(row, 2, type_label)
        
        self.mapping_table.resizeRowToContents(row)
    
    def add_composite_mapping_row(self, row, field_name, db_columns_json, table_name):
        """Добавление составного сопоставления"""
        self.composite_widget.create_composite_field_row(
            row, field_name, db_columns_json, table_name, self.mapping_table
        )
    
    def load_request_types(self):
        self.request_type_combo.clear()
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.request_types ORDER BY name")
        while query.next():
            self.request_type_combo.addItem(query.value(1), query.value(0))
    
    def get_table_by_column(self, col):
        for tbl, cols in self.db_columns.items():
            if col in cols:
                return tbl
        return None
    
    def load_template_variables(self, template_id):
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
            print(f"✅ Найдено {len(self.template_variables)} переменных")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.template_variables = ["{{surname}}", "{{name}}", "{{patronymic}}"]
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
            # === ВСЕ СТОЛБЦЫ ИЗ addresses ===
            "addresses": [
                "region",       # Субъект РФ
                "district",     # Район
                "town",         # Населенный пункт
                "street",       # Улица
                "house",        # Дом
                "building",     # Корпус
                "letter",       # Литера
                "apartment",    # Квартира
                "room",         # Комната
                "check_date",   # Дата проверки
                "check_result"  # Результат проверки
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
        print(f"✅ Загружено {len(self.db_columns)} таблиц")
        print(f"   📍 addresses: {len(self.db_columns['addresses'])} столбцов")
    
    # ========================
    # МЕТОДЫ УПРАВЛЕНИЯ ШАБЛОНАМИ
    # ========================
    
    def create_templates_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title_label = QLabel("Управление шаблонами документов")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
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
        
        templates_group = QGroupBox("Список шаблонов")
        templates_layout = QVBoxLayout()
        
        self.templates_model = QSqlQueryModel()
        self.templates_table = QTableView()
        self.templates_table.setModel(self.templates_model)
        self.templates_table.setAlternatingRowColors(True)
        self.templates_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        header = self.templates_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        templates_layout.addWidget(self.templates_table)
        
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
                INSERT INTO krd.document_templates 
                (name, description, template_data, is_deleted)
                VALUES (:name, :description, :template_data, FALSE)
            """)
            query.bindValue(":name", name)
            query.bindValue(":description", desc)
            query.bindValue(":template_data", QByteArray(data))
            
            if not query.exec():
                raise Exception(query.lastError().text())
            
            QMessageBox.information(self, "Успех", "Шаблон успешно добавлен")
            self.template_name_input.clear()
            self.template_desc_input.clear()
            self.selected_file_label.setText("Файл не выбран")
            if hasattr(self, 'selected_file_path'):
                delattr(self, 'selected_file_path')
            self.load_document_templates()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка:\n{str(e)}")
    
    def load_document_templates(self):
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT id, name, description, created_at 
            FROM krd.document_templates 
            WHERE is_deleted = FALSE
            ORDER BY name
        """)
        query.exec()
        self.templates_model.setQuery(query)
        
        self.template_combo.clear()
        query2 = QSqlQuery(self.db)
        query2.prepare("SELECT id, name FROM krd.document_templates WHERE is_deleted = FALSE ORDER BY name")
        query2.exec()
        while query2.next():
            self.template_combo.addItem(query2.value(1), query2.value(0))
    
    def show_context_menu(self, position: QPoint):
        index = self.templates_table.indexAt(position)
        if not index.isValid():
            return
        
        menu = QMenu(self)
        delete_action = QAction("Удалить шаблон", self)
        delete_action.triggered.connect(self.delete_selected_template)
        menu.addAction(delete_action)
        menu.exec(self.templates_table.mapToGlobal(position))
    
    def delete_selected_template(self):
        selection_model = self.templates_table.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Внимание", "Выберите шаблон")
            return
        
        index = selection_model.selectedRows()[0]
        template_id = self.templates_model.data(self.templates_model.index(index.row(), 0))
        template_name = self.templates_model.data(self.templates_model.index(index.row(), 1))
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить шаблон '{template_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            query = QSqlQuery(self.db)
            query.prepare("UPDATE krd.document_templates SET is_deleted = TRUE WHERE id = ?")
            query.addBindValue(template_id)
            query.exec()
            self.load_document_templates()
    
    def get_table_by_column(self, col):
        for tbl, cols in self.db_columns.items():
            if col in cols:
                return tbl
        return None