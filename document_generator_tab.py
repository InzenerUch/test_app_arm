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
    QTableView, QMenu, QSpacerItem, QSizePolicy, QToolTip, QSplitter, QDialog
)
from PyQt6.QtCore import Qt, QByteArray, QPoint, QDate, QRect
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont, QContextMenuEvent, QAction, QCursor
from datetime import datetime
from audit_logger import AuditLogger
from composite_field_widget import CompositeFieldWidget
from field_mapping_manager import FieldMappingManager
from database_handler import DatabaseHandler
from mapping_editor_dialog import MappingEditorDialog


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
    "category_id": "ID категории военнослужащего",
    "rank_id": "ID воинского звания",
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
    "photo_civilian": "Фото в гражданской одежде",
    "photo_military_headgear": "Фото в форме с головным убором",
    "photo_military_no_headgear": "Фото в форме без головного убора",
    "photo_distinctive_marks": "Фото отличительных примет",
    
    # ========================
    # АДРЕСА ПРОЖИВАНИЯ (addresses) - ВСЕ 11 ПОЛЕЙ
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
    "military_unit_id": "🎖️ ID военного управления",
    "garrison_id": "🎖️ ID гарнизона",
    "position_id": "🎖️ ID воинской должности",
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

# === ТАБЛИЦЫ С ВЫБОРОМ ЗАПИСЕЙ ===
TABLES_WITH_SELECTION = {
    "addresses": "🏠 Адрес проживания",
    "service_places": "🎖️ Место службы",
    "soch_episodes": "⚠️ Эпизод СОЧ"
}


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
        self.current_table_name = "social_data"
        
        # Выбранные записи из связанных таблиц
        self.selected_address_id = None
        self.selected_service_place_id = None
        self.selected_soch_episode_id = None
        
        # Отслеживание используемых таблиц
        self.used_tables_in_mappings = set()
        
        print(f"\n{'='*60}")
        print(f"🔧 DocumentGeneratorTab инициализирован для КРД-{krd_id}")
        print(f"{'='*60}\n")
        
        # === 1. Сначала создаём UI ===
        self.init_ui()
        
        # === 2. ТЕПЕРЬ инициализируем модули ===
        self.composite_widget = CompositeFieldWidget(self)
        self.mapping_manager = FieldMappingManager(self)
        self.db_handler = DatabaseHandler(self.db)
        
        # === 3. Загружаем данные ===
        self.load_document_templates()
        self.load_related_records()
        self.load_db_columns()
    
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
        
        # === Выбор шаблона с кнопкой редактирования ===
        template_group = QGroupBox("📄 Выбор шаблона документа")
        template_layout = QGridLayout(template_group)
        template_layout.setSpacing(10)
        
        template_layout.addWidget(QLabel("Шаблон документа:"), 0, 0)
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(300)
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_layout.addWidget(self.template_combo, 0, 1)
        
        # Кнопка редактирования сопоставлений
        edit_btn = QPushButton("✏️ Редактировать сопоставления")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        edit_btn.clicked.connect(self.open_mapping_editor)
        template_layout.addWidget(edit_btn, 0, 2)
        
        info_label = QLabel("💡 Нажмите «Редактировать сопоставления» чтобы настроить какие поля из БД подставлять в шаблон")
        info_label.setStyleSheet("QLabel { color: #666; padding: 5px; }")
        info_label.setWordWrap(True)
        template_layout.addWidget(info_label, 1, 0, 1, 3)
        
        layout.addWidget(template_group)
        
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
        
        # === КНОПКА ГЕНЕРАЦИИ ===
        generate_btn = QPushButton("📄 Сформировать документ и сохранить в базу")
        generate_btn.setMinimumHeight(60)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                padding: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        generate_btn.clicked.connect(self.generate_and_save_document)
        layout.addWidget(generate_btn)
        
        # Добавляем распорку чтобы прижать кнопку генерации вниз
        layout.addStretch()
        
        return widget
    
    def open_mapping_editor(self):
        """Открытие окна редактирования сопоставлений"""
        if not self.current_template_id:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите шаблон документа")
            return
        
        dialog = MappingEditorDialog(
            parent=self,
            krd_id=self.krd_id,
            db_connection=self.db,
            template_id=self.current_template_id,
            audit_logger=self.audit_logger
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Перезагружаем сопоставления после сохранения
            self._update_used_tables_tracking()
            QMessageBox.information(self, "Успех", "✅ Сопоставления обновлены!\nТеперь можно сформировать документ.")
    
    # ========================
    # МЕТОДЫ ДЛЯ РАБОТЫ С РУССКИМИ НАЗВАНИЯМИ
    # ========================
    
    def get_column_description(self, column_name):
        """Получение русского описания для колонки БД"""
        return COLUMN_DESCRIPTIONS.get(column_name, column_name)
    
    def get_column_name(self, description):
        """Получение имени колонки БД из русского описания"""
        return DESCRIPTION_TO_COLUMN.get(description, description)
    
    def get_table_by_column(self, column_name):
        """Определение таблицы по имени колонки"""
        for table_name, columns in self.db_columns.items():
            if column_name in columns:
                return table_name
        return None
    
    def create_db_column_combo(self, selected_column=None):
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
        
        # === ПРОВЕРКА: Выбраны ли записи для используемых таблиц ===
        validation_errors = []
        
        if "addresses" in self.used_tables_in_mappings and not self.selected_address_id:
            validation_errors.append("🏠 Не выбран адрес проживания")
        
        if "service_places" in self.used_tables_in_mappings and not self.selected_service_place_id:
            validation_errors.append("🎖️ Не выбрано место службы")
        
        if "soch_episodes" in self.used_tables_in_mappings and not self.selected_soch_episode_id:
            validation_errors.append("⚠️ Не выбран эпизод СОЧ")
        
        if validation_errors:
            error_message = "⚠️ Для генерации документа необходимо выбрать записи:\n\n"
            error_message += "\n".join(validation_errors)
            error_message += "\n\n💡 Выберите соответствующие значения в ComboBox вверху вкладки."
            
            QMessageBox.warning(self, "Требуется выбор записей", error_message)
            return
        
        print(f"📋 Template ID: {template_id}")
        
        # Сохранение сопоставлений (теперь просто проверяем что они есть в БД)
        if not self.save_mappings_now():
            print("❌ Ошибка: Не удалось загрузить сопоставления")
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
                
                # Определяем таблицу для этой колонки
                col_table = self.get_table_by_column(column_name)
                
                # Выбираем ID записи в зависимости от таблицы
                selected_id = None
                if col_table == "addresses":
                    selected_id = self.selected_address_id
                elif col_table == "service_places":
                    selected_id = self.selected_service_place_id
                elif col_table == "soch_episodes":
                    selected_id = self.selected_soch_episode_id
                
                # Получаем значение из выбранной записи или последней
                if selected_id and col_table in TABLES_WITH_SELECTION:
                    value = self._get_value_from_specific_record(col_table, column_name, selected_id)
                else:
                    value = self._get_value_from_database(col_table, column_name, krd_id)
                
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
    
    # ========================
    # ✅ ИСПРАВЛЕННЫЙ МЕТОД (Решение 3)
    # ========================
    
    def save_mappings_now(self):
        """
        Сохранение сопоставлений (Решение 3: без mapping_table)
        Сопоставления уже сохранены в БД через MappingEditorDialog
        """
        if not self.current_template_id:
            print("⚠️ Шаблон не выбран")
            return False
        
        # Сопоставления уже сохранены в БД через MappingEditorDialog
        # Просто обновляем отслеживание используемых таблиц
        self._update_used_tables_tracking()
        
        print(f"✅ Сопоставления загружены из БД для шаблона {self.current_template_id}")
        return True
    
    def _update_used_tables_tracking(self):
        """Обновление отслеживания используемых таблиц в сопоставлениях"""
        self.used_tables_in_mappings = set()
        
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT table_name, is_composite, db_columns
            FROM krd.field_mappings
            WHERE template_id = ?
        """)
        query.addBindValue(self.current_template_id)
        
        if query.exec():
            while query.next():
                table_name = query.value(0)
                
                if table_name in TABLES_WITH_SELECTION:
                    self.used_tables_in_mappings.add(table_name)
        
        print(f"📊 Используемые таблицы: {self.used_tables_in_mappings}")
    
    def on_template_changed(self):
        tid = self.template_combo.currentData()
        template_name = self.template_combo.currentText()
        
        if tid:
            self.current_template_id = tid
            if self.audit_logger:
                self.audit_logger.log_template_view(tid, template_name)
            self._update_used_tables_tracking()
        else:
            self.current_template_id = None
    
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