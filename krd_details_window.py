"""
Модуль для окна просмотра и редактирования данных КРД
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QTextEdit, QDateEdit, QPushButton, QMessageBox, 
    QGroupBox, QComboBox, QScrollArea, QWidget, QTabWidget,
    QSpinBox, QLabel, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlTableModel, QSqlRecord, QSqlQuery
from PyQt6.QtGui import QFont

from audit_logger import AuditLogger


class KrdDetailsWindow(QDialog):
    """
    Окно просмотра и редактирования данных КРД
    """
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        """
        Инициализация окна просмотра КРД
        
        Args:
            krd_id (int): ID КРД для редактирования
            db_connection: соединение с базой данных
            audit_logger (AuditLogger, optional): логгер аудита
        """
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        
        self.setWindowTitle(f"Карточка розыска №{krd_id}")
        self.setModal(True)
        self.resize(1000, 700)
        
        # Создаем модели для данных
        self.social_data_model = QSqlTableModel(db=self.db)
        self.social_data_model.setTable("krd.social_data")
        self.social_data_model.setFilter(f"krd_id = {krd_id}")
        self.social_data_model.select()
        
        # Проверяем, есть ли данные
        if self.social_data_model.rowCount() == 0:
            self.create_new_record()
        
        # Получаем запись
        self.record = self.social_data_model.record(0)
        
        # Сохраняем старые значения для логирования изменений
        self.old_data = self._get_current_data()
        
        self.init_ui()
        self.load_data()
    
    def create_new_record(self):
        """Создание новой записи, если она не существует"""
        row = self.social_data_model.rowCount()
        self.social_data_model.insertRow(row)
        record = self.social_data_model.record(row)
        record.setValue("krd_id", self.krd_id)
        self.social_data_model.setRecord(row, record)
    
    def _get_current_data(self):
        """Получение текущих данных для логирования"""
        data = {}
        
        if self.record:
            for i in range(self.record.count()):
                field_name = self.record.fieldName(i)
                data[field_name] = self.record.value(i)
        
        return data
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_layout = QVBoxLayout()
        
        # Создаем вкладки
        tabs = QTabWidget()
        
        # Вкладка 1: Социально-демографические данные
        tabs.addTab(self.create_social_data_tab(), "Социально-демографические данные")
        
        # Вкладка 2: Адреса проживания
        tabs.addTab(self.create_addresses_tab(), "Адреса проживания")
        
        # Вкладка 3: Входящие поручения на розыск
        tabs.addTab(self.create_incoming_orders_tab(), "Входящие поручения")
        
        # Вкладка 4: Места службы
        tabs.addTab(self.create_service_places_tab(), "Места службы")
        
        # Вкладка 5: Сведения о СОЧ
        tabs.addTab(self.create_soch_tab(), "Сведения о СОЧ")
        
        # Вкладка 6: Запросы и поручения
        tabs.addTab(self.create_requests_tab(), "Запросы и поручения")
        
        main_layout.addWidget(tabs)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Сохранить")
        save_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def create_social_data_tab(self):
        """Создание вкладки социально-демографических данных"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        # === Группа 1: Основные данные ===
        group1 = QGroupBox("Основные данные (поля со знаком * обязательны)")
        group1_layout = QGridLayout()
        
        # Фамилия, Имя, Отчество
        group1_layout.addWidget(QLabel("Фамилия *:"), 0, 0)
        self.surname_input = QLineEdit()
        group1_layout.addWidget(self.surname_input, 0, 1)
        
        group1_layout.addWidget(QLabel("Имя *:"), 0, 2)
        self.name_input = QLineEdit()
        group1_layout.addWidget(self.name_input, 0, 3)
        
        group1_layout.addWidget(QLabel("Отчество *:"), 0, 4)
        self.patronymic_input = QLineEdit()
        group1_layout.addWidget(self.patronymic_input, 0, 5)
        
        # Табельный номер, Личный номер
        group1_layout.addWidget(QLabel("Табельный номер:"), 1, 0)
        self.tab_number_input = QLineEdit()
        group1_layout.addWidget(self.tab_number_input, 1, 1)
        
        group1_layout.addWidget(QLabel("Личный номер:"), 1, 2)
        self.personal_number_input = QLineEdit()
        group1_layout.addWidget(self.personal_number_input, 1, 3)
        
        # Категория и звание
        group1_layout.addWidget(QLabel("Категория военнослужащего:"), 2, 0)
        self.category_combo = QComboBox()
        self.load_categories()
        group1_layout.addWidget(self.category_combo, 2, 1)
        
        group1_layout.addWidget(QLabel("Воинское звание:"), 2, 2)
        self.rank_combo = QComboBox()
        self.load_ranks()
        group1_layout.addWidget(self.rank_combo, 2, 3)
        
        group1.setLayout(group1_layout)
        layout.addWidget(group1)
        
        # === Группа 2: Место рождения ===
        group2 = QGroupBox("Место рождения")
        group2_layout = QGridLayout()
        
        group2_layout.addWidget(QLabel("Населенный пункт:"), 0, 0)
        self.birth_place_town_input = QLineEdit()
        group2_layout.addWidget(self.birth_place_town_input, 0, 1)
        
        group2_layout.addWidget(QLabel("Административный район:"), 0, 2)
        self.birth_place_district_input = QLineEdit()
        group2_layout.addWidget(self.birth_place_district_input, 0, 3)
        
        group2_layout.addWidget(QLabel("Субъект (регион):"), 1, 0)
        self.birth_place_region_input = QLineEdit()
        group2_layout.addWidget(self.birth_place_region_input, 1, 1)
        
        group2_layout.addWidget(QLabel("Страна:"), 1, 2)
        self.birth_place_country_input = QLineEdit()
        group2_layout.addWidget(self.birth_place_country_input, 1, 3)
        
        group2_layout.addWidget(QLabel("Дата рождения:"), 2, 0)
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate.currentDate())
        group2_layout.addWidget(self.birth_date_input, 2, 1)
        
        group2.setLayout(group2_layout)
        layout.addWidget(group2)
        
        # === Группа 3: Призыв ===
        group3 = QGroupBox("Призыв")
        group3_layout = QGridLayout()
        
        group3_layout.addWidget(QLabel("Каким комиссариатом призван:"), 0, 0)
        self.drafted_by_commissariat_input = QLineEdit()
        group3_layout.addWidget(self.drafted_by_commissariat_input, 0, 1)
        
        group3_layout.addWidget(QLabel("Дата призыва:"), 0, 2)
        self.draft_date_input = QDateEdit()
        self.draft_date_input.setCalendarPopup(True)
        self.draft_date_input.setDate(QDate.currentDate())
        group3_layout.addWidget(self.draft_date_input, 0, 3)
        
        group3_layout.addWidget(QLabel("Каким ПОВСК отобран:"), 1, 0)
        self.povsk_input = QLineEdit()
        group3_layout.addWidget(self.povsk_input, 1, 1)
        
        group3_layout.addWidget(QLabel("Дата отбора:"), 1, 2)
        self.selection_date_input = QDateEdit()
        self.selection_date_input.setCalendarPopup(True)
        self.selection_date_input.setDate(QDate.currentDate())
        group3_layout.addWidget(self.selection_date_input, 1, 3)
        
        group3.setLayout(group3_layout)
        layout.addWidget(group3)
        
        # === Группа 4: Образование и судимость ===
        group4 = QGroupBox("Образование и судимость")
        group4_layout = QGridLayout()
        
        group4_layout.addWidget(QLabel("Образование:"), 0, 0)
        self.education_input = QLineEdit()
        group4_layout.addWidget(self.education_input, 0, 1)
        
        group4_layout.addWidget(QLabel("Сведения о судимости:"), 1, 0)
        self.criminal_record_input = QTextEdit()
        self.criminal_record_input.setMaximumHeight(80)
        group4_layout.addWidget(self.criminal_record_input, 1, 1)
        
        group4_layout.addWidget(QLabel("Аккаунт в соцсетях:"), 2, 0)
        self.social_media_account_input = QLineEdit()
        group4_layout.addWidget(self.social_media_account_input, 2, 1)
        
        group4_layout.addWidget(QLabel("Номер банковской карты:"), 2, 2)
        self.bank_card_number_input = QLineEdit()
        group4_layout.addWidget(self.bank_card_number_input, 2, 3)
        
        group4.setLayout(group4_layout)
        layout.addWidget(group4)
        
        # === Группа 5: Паспортные данные ===
        group5 = QGroupBox("Паспортные данные")
        group5_layout = QGridLayout()
        
        group5_layout.addWidget(QLabel("Серия паспорта:"), 0, 0)
        self.passport_series_input = QLineEdit()
        group5_layout.addWidget(self.passport_series_input, 0, 1)
        
        group5_layout.addWidget(QLabel("Номер паспорта:"), 0, 2)
        self.passport_number_input = QLineEdit()
        group5_layout.addWidget(self.passport_number_input, 0, 3)
        
        group5_layout.addWidget(QLabel("Дата выдачи:"), 1, 0)
        self.passport_issue_date_input = QDateEdit()
        self.passport_issue_date_input.setCalendarPopup(True)
        self.passport_issue_date_input.setDate(QDate.currentDate())
        group5_layout.addWidget(self.passport_issue_date_input, 1, 1)
        
        group5_layout.addWidget(QLabel("Кем выдан:"), 1, 2)
        self.passport_issued_by_input = QLineEdit()
        group5_layout.addWidget(self.passport_issued_by_input, 1, 3)
        
        group5.setLayout(group5_layout)
        layout.addWidget(group5)
        
        # === Группа 6: Военный билет ===
        group6 = QGroupBox("Военный билет (удостоверение личности)")
        group6_layout = QGridLayout()
        
        group6_layout.addWidget(QLabel("Серия:"), 0, 0)
        self.military_id_series_input = QLineEdit()
        group6_layout.addWidget(self.military_id_series_input, 0, 1)
        
        group6_layout.addWidget(QLabel("Номер:"), 0, 2)
        self.military_id_number_input = QLineEdit()
        group6_layout.addWidget(self.military_id_number_input, 0, 3)
        
        group6_layout.addWidget(QLabel("Дата выдачи:"), 1, 0)
        self.military_id_issue_date_input = QDateEdit()
        self.military_id_issue_date_input.setCalendarPopup(True)
        self.military_id_issue_date_input.setDate(QDate.currentDate())
        group6_layout.addWidget(self.military_id_issue_date_input, 1, 1)
        
        group6_layout.addWidget(QLabel("Кем выдан:"), 1, 2)
        self.military_id_issued_by_input = QLineEdit()
        group6_layout.addWidget(self.military_id_issued_by_input, 1, 3)
        
        group6.setLayout(group6_layout)
        layout.addWidget(group6)
        
        # === Группа 7: Внешность ===
        group7 = QGroupBox("Особенности внешности")
        group7_layout = QGridLayout()
        
        group7_layout.addWidget(QLabel("Особенности внешности:"), 0, 0)
        self.appearance_features_input = QTextEdit()
        self.appearance_features_input.setMaximumHeight(80)
        group7_layout.addWidget(self.appearance_features_input, 0, 1)
        
        group7_layout.addWidget(QLabel("Личные приметы:"), 1, 0)
        self.personal_marks_input = QTextEdit()
        self.personal_marks_input.setMaximumHeight(80)
        group7_layout.addWidget(self.personal_marks_input, 1, 1)
        
        group7_layout.addWidget(QLabel("Сведения о федеральном розыске:"), 2, 0)
        self.federal_search_info_input = QTextEdit()
        self.federal_search_info_input.setMaximumHeight(80)
        group7_layout.addWidget(self.federal_search_info_input, 2, 1)
        
        group7_layout.addWidget(QLabel("Контакты военнослужащего:"), 3, 0)
        self.military_contacts_input = QLineEdit()
        group7_layout.addWidget(self.military_contacts_input, 3, 1)
        
        group7_layout.addWidget(QLabel("Сведения о близких родственниках:"), 4, 0)
        self.relatives_info_input = QTextEdit()
        self.relatives_info_input.setMaximumHeight(80)
        group7_layout.addWidget(self.relatives_info_input, 4, 1)
        
        group7.setLayout(group7_layout)
        layout.addWidget(group7)
        
        layout.addStretch()
        return scroll
    
    def create_addresses_tab(self):
        """Создание вкладки адресов проживания"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Адреса проживания")
        group_layout = QGridLayout()
        
        # Адрес №1
        group_layout.addWidget(QLabel("Субъект РФ:"), 0, 0)
        self.address_region_input = QLineEdit()
        group_layout.addWidget(self.address_region_input, 0, 1)
        
        group_layout.addWidget(QLabel("Административный район:"), 0, 2)
        self.address_district_input = QLineEdit()
        group_layout.addWidget(self.address_district_input, 0, 3)
        
        group_layout.addWidget(QLabel("Населенный пункт:"), 1, 0)
        self.address_town_input = QLineEdit()
        group_layout.addWidget(self.address_town_input, 1, 1)
        
        group_layout.addWidget(QLabel("Улица:"), 1, 2)
        self.address_street_input = QLineEdit()
        group_layout.addWidget(self.address_street_input, 1, 3)
        
        group_layout.addWidget(QLabel("Дом:"), 2, 0)
        self.address_house_input = QLineEdit()
        group_layout.addWidget(self.address_house_input, 2, 1)
        
        group_layout.addWidget(QLabel("Корпус:"), 2, 2)
        self.address_building_input = QLineEdit()
        group_layout.addWidget(self.address_building_input, 2, 3)
        
        group_layout.addWidget(QLabel("Литер:"), 3, 0)
        self.address_letter_input = QLineEdit()
        group_layout.addWidget(self.address_letter_input, 3, 1)
        
        group_layout.addWidget(QLabel("Квартира:"), 3, 2)
        self.address_apartment_input = QLineEdit()
        group_layout.addWidget(self.address_apartment_input, 3, 3)
        
        group_layout.addWidget(QLabel("Комната:"), 4, 0)
        self.address_room_input = QLineEdit()
        group_layout.addWidget(self.address_room_input, 4, 1)
        
        group_layout.addWidget(QLabel("Дата адресной проверки:"), 5, 0)
        self.check_date_input = QDateEdit()
        self.check_date_input.setCalendarPopup(True)
        self.check_date_input.setDate(QDate.currentDate())
        group_layout.addWidget(self.check_date_input, 5, 1)
        
        group_layout.addWidget(QLabel("Результат проверки:"), 6, 0)
        self.check_result_input = QTextEdit()
        self.check_result_input.setMaximumHeight(60)
        group_layout.addWidget(self.check_result_input, 6, 1, 1, 3)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        layout.addStretch()
        return scroll
    
    def create_incoming_orders_tab(self):
        """Создание вкладки входящих поручений"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Входящие поручения на розыск")
        group_layout = QGridLayout()
        
        group_layout.addWidget(QLabel("Инициатор розыска *:"), 0, 0)
        self.initiator_type_combo = QComboBox()
        self.load_initiator_types()
        group_layout.addWidget(self.initiator_type_combo, 0, 1)
        
        group_layout.addWidget(QLabel("Полное наименование инициатора *:"), 1, 0)
        self.initiator_full_name_input = QLineEdit()
        group_layout.addWidget(self.initiator_full_name_input, 1, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Военное управление инициатора *:"), 2, 0)
        self.initiator_military_unit_combo = QComboBox()
        self.load_military_units()
        group_layout.addWidget(self.initiator_military_unit_combo, 2, 1)
        
        group_layout.addWidget(QLabel("Исходящая дата поручения *:"), 3, 0)
        self.order_date_input = QDateEdit()
        self.order_date_input.setCalendarPopup(True)
        self.order_date_input.setDate(QDate.currentDate())
        group_layout.addWidget(self.order_date_input, 3, 1)
        
        group_layout.addWidget(QLabel("Исходящий номер поручения *:"), 3, 2)
        self.order_number_input = QLineEdit()
        group_layout.addWidget(self.order_number_input, 3, 3)
        
        group_layout.addWidget(QLabel("Дата поступления в ВК *:"), 4, 0)
        self.receipt_date_input = QDateEdit()
        self.receipt_date_input.setCalendarPopup(True)
        self.receipt_date_input.setDate(QDate.currentDate())
        group_layout.addWidget(self.receipt_date_input, 4, 1)
        
        group_layout.addWidget(QLabel("Входящий номер в ВК *:"), 4, 2)
        self.receipt_number_input = QLineEdit()
        group_layout.addWidget(self.receipt_number_input, 4, 3)
        
        # Почтовый адрес инициатора
        group_layout.addWidget(QLabel("Почтовый адрес инициатора:"), 5, 0)
        group_layout.addWidget(QLabel("Индекс:"), 6, 0)
        self.initiator_postal_index_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_index_input, 6, 1)
        
        group_layout.addWidget(QLabel("Субъект РФ:"), 6, 2)
        self.initiator_postal_region_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_region_input, 6, 3)
        
        group_layout.addWidget(QLabel("Административный район:"), 7, 0)
        self.initiator_postal_district_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_district_input, 7, 1)
        
        group_layout.addWidget(QLabel("Населенный пункт:"), 7, 2)
        self.initiator_postal_town_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_town_input, 7, 3)
        
        group_layout.addWidget(QLabel("Улица:"), 8, 0)
        self.initiator_postal_street_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_street_input, 8, 1)
        
        group_layout.addWidget(QLabel("Дом:"), 8, 2)
        self.initiator_postal_house_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_house_input, 8, 3)
        
        group_layout.addWidget(QLabel("Корпус:"), 9, 0)
        self.initiator_postal_building_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_building_input, 9, 1)
        
        group_layout.addWidget(QLabel("Литер:"), 9, 2)
        self.initiator_postal_letter_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_letter_input, 9, 3)
        
        group_layout.addWidget(QLabel("Квартира:"), 10, 0)
        self.initiator_postal_apartment_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_apartment_input, 10, 1)
        
        group_layout.addWidget(QLabel("Комната:"), 10, 2)
        self.initiator_postal_room_input = QLineEdit()
        group_layout.addWidget(self.initiator_postal_room_input, 10, 3)
        
        group_layout.addWidget(QLabel("Контакты источника:"), 11, 0)
        self.initiator_contacts_input = QLineEdit()
        group_layout.addWidget(self.initiator_contacts_input, 11, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Дата нашего ответа:"), 12, 0)
        self.our_response_date_input = QDateEdit()
        self.our_response_date_input.setCalendarPopup(True)
        self.our_response_date_input.setDate(QDate.currentDate())
        group_layout.addWidget(self.our_response_date_input, 12, 1)
        
        group_layout.addWidget(QLabel("Исходящий номер нашего ответа:"), 12, 2)
        self.our_response_number_input = QLineEdit()
        group_layout.addWidget(self.our_response_number_input, 12, 3)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        layout.addStretch()
        return scroll
    
    def create_service_places_tab(self):
        """Создание вкладки мест службы"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Места службы")
        group_layout = QGridLayout()
        
        group_layout.addWidget(QLabel("Наименование места службы:"), 0, 0)
        self.place_name_input = QLineEdit()
        group_layout.addWidget(self.place_name_input, 0, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Военное управление:"), 1, 0)
        self.service_military_unit_combo = QComboBox()
        self.load_military_units()
        group_layout.addWidget(self.service_military_unit_combo, 1, 1)
        
        group_layout.addWidget(QLabel("Гарнизон:"), 1, 2)
        self.garrison_combo = QComboBox()
        self.load_garrisons()
        group_layout.addWidget(self.garrison_combo, 1, 3)
        
        group_layout.addWidget(QLabel("Воинская должность:"), 2, 0)
        self.position_combo = QComboBox()
        self.load_positions()
        group_layout.addWidget(self.position_combo, 2, 1)
        
        group_layout.addWidget(QLabel("Командиры (звание, ФИО, контакты):"), 3, 0)
        self.commanders_input = QTextEdit()
        self.commanders_input.setMaximumHeight(80)
        group_layout.addWidget(self.commanders_input, 3, 1, 1, 3)
        
        # Почтовый адрес места службы
        group_layout.addWidget(QLabel("Почтовый адрес места службы:"), 4, 0)
        group_layout.addWidget(QLabel("Индекс:"), 5, 0)
        self.service_postal_index_input = QLineEdit()
        group_layout.addWidget(self.service_postal_index_input, 5, 1)
        
        group_layout.addWidget(QLabel("Субъект РФ:"), 5, 2)
        self.service_postal_region_input = QLineEdit()
        group_layout.addWidget(self.service_postal_region_input, 5, 3)
        
        group_layout.addWidget(QLabel("Административный район:"), 6, 0)
        self.service_postal_district_input = QLineEdit()
        group_layout.addWidget(self.service_postal_district_input, 6, 1)
        
        group_layout.addWidget(QLabel("Населенный пункт:"), 6, 2)
        self.service_postal_town_input = QLineEdit()
        group_layout.addWidget(self.service_postal_town_input, 6, 3)
        
        group_layout.addWidget(QLabel("Улица:"), 7, 0)
        self.service_postal_street_input = QLineEdit()
        group_layout.addWidget(self.service_postal_street_input, 7, 1)
        
        group_layout.addWidget(QLabel("Дом:"), 7, 2)
        self.service_postal_house_input = QLineEdit()
        group_layout.addWidget(self.service_postal_house_input, 7, 3)
        
        group_layout.addWidget(QLabel("Корпус:"), 8, 0)
        self.service_postal_building_input = QLineEdit()
        group_layout.addWidget(self.service_postal_building_input, 8, 1)
        
        group_layout.addWidget(QLabel("Литер:"), 8, 2)
        self.service_postal_letter_input = QLineEdit()
        group_layout.addWidget(self.service_postal_letter_input, 8, 3)
        
        group_layout.addWidget(QLabel("Квартира:"), 9, 0)
        self.service_postal_apartment_input = QLineEdit()
        group_layout.addWidget(self.service_postal_apartment_input, 9, 1)
        
        group_layout.addWidget(QLabel("Комната:"), 9, 2)
        self.service_postal_room_input = QLineEdit()
        group_layout.addWidget(self.service_postal_room_input, 9, 3)
        
        group_layout.addWidget(QLabel("Контакты места службы:"), 10, 0)
        self.place_contacts_input = QLineEdit()
        group_layout.addWidget(self.place_contacts_input, 10, 1, 1, 3)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        layout.addStretch()
        return scroll
    
    def create_soch_tab(self):
        """Создание вкладки сведений о СОЧ"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Сведения о самовольном оставлении части (СОЧ)")
        group_layout = QGridLayout()
        
        group_layout.addWidget(QLabel("Дата СОЧ:"), 0, 0)
        self.soch_date_input = QDateEdit()
        self.soch_date_input.setCalendarPopup(True)
        self.soch_date_input.setDate(QDate.currentDate())
        group_layout.addWidget(self.soch_date_input, 0, 1)
        
        group_layout.addWidget(QLabel("Место СОЧ:"), 0, 2)
        self.soch_location_input = QLineEdit()
        group_layout.addWidget(self.soch_location_input, 0, 3)
        
        group_layout.addWidget(QLabel("Дата и номер приказа о СОЧ:"), 1, 0)
        self.order_date_number_input = QLineEdit()
        group_layout.addWidget(self.order_date_number_input, 1, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Очевидцы СОЧ:"), 2, 0)
        self.witnesses_input = QTextEdit()
        self.witnesses_input.setMaximumHeight(60)
        group_layout.addWidget(self.witnesses_input, 2, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Вероятные причины СОЧ:"), 3, 0)
        self.reasons_input = QTextEdit()
        self.reasons_input.setMaximumHeight(60)
        group_layout.addWidget(self.reasons_input, 3, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Сведения о наличии оружия:"), 4, 0)
        self.weapon_info_input = QTextEdit()
        self.weapon_info_input.setMaximumHeight(60)
        group_layout.addWidget(self.weapon_info_input, 4, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Во что был одет:"), 5, 0)
        self.clothing_input = QTextEdit()
        self.clothing_input.setMaximumHeight(60)
        group_layout.addWidget(self.clothing_input, 5, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Варианты движения:"), 6, 0)
        self.movement_options_input = QTextEdit()
        self.movement_options_input.setMaximumHeight(60)
        group_layout.addWidget(self.movement_options_input, 6, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Другая значимая информация:"), 7, 0)
        self.other_info_input = QTextEdit()
        self.other_info_input.setMaximumHeight(60)
        group_layout.addWidget(self.other_info_input, 7, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Контакт дежурного по ВК:"), 8, 0)
        self.duty_officer_commissariat_input = QLineEdit()
        group_layout.addWidget(self.duty_officer_commissariat_input, 8, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Контакт дежурного по ОМВД:"), 9, 0)
        self.duty_officer_omvd_input = QLineEdit()
        group_layout.addWidget(self.duty_officer_omvd_input, 9, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Сведения о проверке:"), 10, 0)
        self.investigation_info_input = QTextEdit()
        self.investigation_info_input.setMaximumHeight(60)
        group_layout.addWidget(self.investigation_info_input, 10, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Сведения о прокуратуре:"), 11, 0)
        self.prosecution_info_input = QTextEdit()
        self.prosecution_info_input.setMaximumHeight(60)
        group_layout.addWidget(self.prosecution_info_input, 11, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Сведения об уголовном деле:"), 12, 0)
        self.criminal_case_info_input = QTextEdit()
        self.criminal_case_info_input.setMaximumHeight(60)
        group_layout.addWidget(self.criminal_case_info_input, 12, 1, 1, 3)
        
        # Данные о розыске
        group_layout.addWidget(QLabel("Дата розыска:"), 13, 0)
        self.search_date_input = QDateEdit()
        self.search_date_input.setCalendarPopup(True)
        self.search_date_input.setDate(QDate.currentDate())
        group_layout.addWidget(self.search_date_input, 13, 1)
        
        group_layout.addWidget(QLabel("Кем разыскан:"), 13, 2)
        self.found_by_input = QLineEdit()
        group_layout.addWidget(self.found_by_input, 13, 3)
        
        group_layout.addWidget(QLabel("Обстоятельства розыска:"), 14, 0)
        self.search_circumstances_input = QTextEdit()
        self.search_circumstances_input.setMaximumHeight(60)
        group_layout.addWidget(self.search_circumstances_input, 14, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Адресат уведомления:"), 15, 0)
        self.notification_recipient_input = QLineEdit()
        group_layout.addWidget(self.notification_recipient_input, 15, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Дата уведомления:"), 16, 0)
        self.notification_date_input = QDateEdit()
        self.notification_date_input.setCalendarPopup(True)
        self.notification_date_input.setDate(QDate.currentDate())
        group_layout.addWidget(self.notification_date_input, 16, 1)
        
        group_layout.addWidget(QLabel("Номер уведомления:"), 16, 2)
        self.notification_number_input = QLineEdit()
        group_layout.addWidget(self.notification_number_input, 16, 3)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        layout.addStretch()
        return scroll
    
    def create_requests_tab(self):
        """Создание вкладки запросов и поручений"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("Запросы и поручения в регистрирующие органы")
        group_layout = QGridLayout()
        
        group_layout.addWidget(QLabel("Тип запроса:"), 0, 0)
        self.request_type_combo = QComboBox()
        self.load_request_types()
        group_layout.addWidget(self.request_type_combo, 0, 1)
        
        group_layout.addWidget(QLabel("Наименование адресата:"), 1, 0)
        self.recipient_name_input = QLineEdit()
        group_layout.addWidget(self.recipient_name_input, 1, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Военное управление адресата:"), 2, 0)
        self.request_military_unit_combo = QComboBox()
        self.load_military_units()
        group_layout.addWidget(self.request_military_unit_combo, 2, 1)
        
        group_layout.addWidget(QLabel("Исходящая дата:"), 3, 0)
        self.issue_date_input = QDateEdit()
        self.issue_date_input.setCalendarPopup(True)
        self.issue_date_input.setDate(QDate.currentDate())
        group_layout.addWidget(self.issue_date_input, 3, 1)
        
        group_layout.addWidget(QLabel("Исходящий номер:"), 3, 2)
        self.issue_number_input = QLineEdit()
        group_layout.addWidget(self.issue_number_input, 3, 3)
        
        # Почтовый адрес адресата
        group_layout.addWidget(QLabel("Почтовый адрес:"), 4, 0)
        group_layout.addWidget(QLabel("Индекс:"), 5, 0)
        self.request_postal_index_input = QLineEdit()
        group_layout.addWidget(self.request_postal_index_input, 5, 1)
        
        group_layout.addWidget(QLabel("Субъект РФ:"), 5, 2)
        self.request_postal_region_input = QLineEdit()
        group_layout.addWidget(self.request_postal_region_input, 5, 3)
        
        group_layout.addWidget(QLabel("Административный район:"), 6, 0)
        self.request_postal_district_input = QLineEdit()
        group_layout.addWidget(self.request_postal_district_input, 6, 1)
        
        group_layout.addWidget(QLabel("Населенный пункт:"), 6, 2)
        self.request_postal_town_input = QLineEdit()
        group_layout.addWidget(self.request_postal_town_input, 6, 3)
        
        group_layout.addWidget(QLabel("Улица:"), 7, 0)
        self.request_postal_street_input = QLineEdit()
        group_layout.addWidget(self.request_postal_street_input, 7, 1)
        
        group_layout.addWidget(QLabel("Дом:"), 7, 2)
        self.request_postal_house_input = QLineEdit()
        group_layout.addWidget(self.request_postal_house_input, 7, 3)
        
        group_layout.addWidget(QLabel("Корпус:"), 8, 0)
        self.request_postal_building_input = QLineEdit()
        group_layout.addWidget(self.request_postal_building_input, 8, 1)
        
        group_layout.addWidget(QLabel("Литер:"), 8, 2)
        self.request_postal_letter_input = QLineEdit()
        group_layout.addWidget(self.request_postal_letter_input, 8, 3)
        
        group_layout.addWidget(QLabel("Квартира:"), 9, 0)
        self.request_postal_apartment_input = QLineEdit()
        group_layout.addWidget(self.request_postal_apartment_input, 9, 1)
        
        group_layout.addWidget(QLabel("Комната:"), 9, 2)
        self.request_postal_room_input = QLineEdit()
        group_layout.addWidget(self.request_postal_room_input, 9, 3)
        
        group_layout.addWidget(QLabel("Контакты:"), 10, 0)
        self.recipient_contacts_input = QLineEdit()
        group_layout.addWidget(self.recipient_contacts_input, 10, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Текст запроса:"), 11, 0)
        self.request_text_input = QTextEdit()
        self.request_text_input.setMaximumHeight(100)
        group_layout.addWidget(self.request_text_input, 11, 1, 1, 3)
        
        group_layout.addWidget(QLabel("Должностное лицо (подписавшее):"), 12, 0)
        self.signed_by_position_input = QLineEdit()
        group_layout.addWidget(self.signed_by_position_input, 12, 1, 1, 3)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        layout.addStretch()
        return scroll
    
    def load_categories(self):
        """Загрузка категорий из базы данных"""
        self.category_combo.clear()
        self.category_combo.addItem("", None)
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.categories ORDER BY name")
        
        while query.next():
            category_id = query.value(0)
            category_name = query.value(1)
            self.category_combo.addItem(category_name, category_id)
    
    def load_ranks(self):
        """Загрузка воинских званий из базы данных"""
        self.rank_combo.clear()
        self.rank_combo.addItem("", None)
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.ranks ORDER BY name")
        
        while query.next():
            rank_id = query.value(0)
            rank_name = query.value(1)
            self.rank_combo.addItem(rank_name, rank_id)
    
    def load_initiator_types(self):
        """Загрузка типов инициаторов"""
        self.initiator_type_combo.clear()
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.initiator_types ORDER BY name")
        
        while query.next():
            type_id = query.value(0)
            type_name = query.value(1)
            self.initiator_type_combo.addItem(type_name, type_id)
    
    def load_request_types(self):
        """Загрузка типов запросов"""
        self.request_type_combo.clear()
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.request_types ORDER BY name")
        
        while query.next():
            type_id = query.value(0)
            type_name = query.value(1)
            self.request_type_combo.addItem(type_name, type_id)
    
    def load_military_units(self):
        """Загрузка военных управлений"""
        # Для всех комбобоксов военных управлений
        for combo in [self.initiator_military_unit_combo, 
                      self.service_military_unit_combo,
                      self.request_military_unit_combo]:
            combo.clear()
            combo.addItem("", None)
            
            query = QSqlQuery(self.db)
            query.exec("SELECT id, name FROM krd.military_units ORDER BY name")
            
            while query.next():
                unit_id = query.value(0)
                unit_name = query.value(1)
                combo.addItem(unit_name, unit_id)
    
    def load_garrisons(self):
        """Загрузка гарнизонов"""
        self.garrison_combo.clear()
        self.garrison_combo.addItem("", None)
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.garrisons ORDER BY name")
        
        while query.next():
            garrison_id = query.value(0)
            garrison_name = query.value(1)
            self.garrison_combo.addItem(garrison_name, garrison_id)
    
    def load_positions(self):
        """Загрузка воинских должностей"""
        self.position_combo.clear()
        self.position_combo.addItem("", None)
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.positions ORDER BY name")
        
        while query.next():
            position_id = query.value(0)
            position_name = query.value(1)
            self.position_combo.addItem(position_name, position_id)
    
    def load_data(self):
        """Загрузка данных из базы в интерфейс"""
        if not self.record:
            return
        
        # Основные данные
        self.surname_input.setText(self.record.value("surname") or "")
        self.name_input.setText(self.record.value("name") or "")
        self.patronymic_input.setText(self.record.value("patronymic") or "")
        self.tab_number_input.setText(self.record.value("tab_number") or "")
        self.personal_number_input.setText(self.record.value("personal_number") or "")
        
        # Категория и звание
        category_id = self.record.value("category_id")
        if category_id:
            index = self.category_combo.findData(category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        
        rank_id = self.record.value("rank_id")
        if rank_id:
            index = self.rank_combo.findData(rank_id)
            if index >= 0:
                self.rank_combo.setCurrentIndex(index)
        
        # Место рождения
        self.birth_place_town_input.setText(self.record.value("birth_place_town") or "")
        self.birth_place_district_input.setText(self.record.value("birth_place_district") or "")
        self.birth_place_region_input.setText(self.record.value("birth_place_region") or "")
        self.birth_place_country_input.setText(self.record.value("birth_place_country") or "")
        
        birth_date = self.record.value("birth_date")
        if birth_date:
            self.birth_date_input.setDate(birth_date)
        
        # Призыв
        self.drafted_by_commissariat_input.setText(self.record.value("drafted_by_commissariat") or "")
        draft_date = self.record.value("draft_date")
        if draft_date:
            self.draft_date_input.setDate(draft_date)
        
        self.povsk_input.setText(self.record.value("povsk") or "")
        selection_date = self.record.value("selection_date")
        if selection_date:
            self.selection_date_input.setDate(selection_date)
        
        # Образование и судимость
        self.education_input.setText(self.record.value("education") or "")
        self.criminal_record_input.setPlainText(self.record.value("criminal_record") or "")
        self.social_media_account_input.setText(self.record.value("social_media_account") or "")
        self.bank_card_number_input.setText(self.record.value("bank_card_number") or "")
        
        # Паспортные данные
        self.passport_series_input.setText(self.record.value("passport_series") or "")
        self.passport_number_input.setText(self.record.value("passport_number") or "")
        passport_issue_date = self.record.value("passport_issue_date")
        if passport_issue_date:
            self.passport_issue_date_input.setDate(passport_issue_date)
        self.passport_issued_by_input.setText(self.record.value("passport_issued_by") or "")
        
        # Военный билет
        self.military_id_series_input.setText(self.record.value("military_id_series") or "")
        self.military_id_number_input.setText(self.record.value("military_id_number") or "")
        military_id_issue_date = self.record.value("military_id_issue_date")
        if military_id_issue_date:
            self.military_id_issue_date_input.setDate(military_id_issue_date)
        self.military_id_issued_by_input.setText(self.record.value("military_id_issued_by") or "")
        
        # Внешность
        self.appearance_features_input.setPlainText(self.record.value("appearance_features") or "")
        self.personal_marks_input.setPlainText(self.record.value("personal_marks") or "")
        self.federal_search_info_input.setPlainText(self.record.value("federal_search_info") or "")
        self.military_contacts_input.setText(self.record.value("military_contacts") or "")
        self.relatives_info_input.setPlainText(self.record.value("relatives_info") or "")
    
    def save_changes(self):
        """Сохранение изменений в базе данных"""
        try:
            # Валидация обязательных полей
            if not self.surname_input.text().strip():
                QMessageBox.warning(self, "Ошибка", "Поле 'Фамилия' обязательно для заполнения")
                return
            
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "Ошибка", "Поле 'Имя' обязательно для заполнения")
                return
            
            if not self.patronymic_input.text().strip():
                QMessageBox.warning(self, "Ошибка", "Поле 'Отчество' обязательно для заполнения")
                return
            
            # Обновляем запись
            self.record.setValue("surname", self.surname_input.text().strip())
            self.record.setValue("name", self.name_input.text().strip())
            self.record.setValue("patronymic", self.patronymic_input.text().strip())
            self.record.setValue("birth_date", self.birth_date_input.date())
            self.record.setValue("birth_place_town", self.birth_place_town_input.text().strip())
            self.record.setValue("birth_place_district", self.birth_place_district_input.text().strip())
            self.record.setValue("birth_place_region", self.birth_place_region_input.text().strip())
            self.record.setValue("birth_place_country", self.birth_place_country_input.text().strip())
            self.record.setValue("tab_number", self.tab_number_input.text().strip())
            self.record.setValue("personal_number", self.personal_number_input.text().strip())
            
            # Категория и звание
            category_id = self.category_combo.currentData()
            rank_id = self.rank_combo.currentData()
            self.record.setValue("category_id", category_id if category_id is not None else None)
            self.record.setValue("rank_id", rank_id if rank_id is not None else None)
            
            # Призыв
            self.record.setValue("drafted_by_commissariat", self.drafted_by_commissariat_input.text().strip())
            self.record.setValue("draft_date", self.draft_date_input.date())
            self.record.setValue("povsk", self.povsk_input.text().strip())
            self.record.setValue("selection_date", self.selection_date_input.date())
            
            # Образование и судимость
            self.record.setValue("education", self.education_input.text().strip())
            self.record.setValue("criminal_record", self.criminal_record_input.toPlainText())
            self.record.setValue("social_media_account", self.social_media_account_input.text().strip())
            self.record.setValue("bank_card_number", self.bank_card_number_input.text().strip())
            
            # Паспортные данные
            self.record.setValue("passport_series", self.passport_series_input.text().strip())
            self.record.setValue("passport_number", self.passport_number_input.text().strip())
            self.record.setValue("passport_issue_date", self.passport_issue_date_input.date())
            self.record.setValue("passport_issued_by", self.passport_issued_by_input.text().strip())
            
            # Военный билет
            self.record.setValue("military_id_series", self.military_id_series_input.text().strip())
            self.record.setValue("military_id_number", self.military_id_number_input.text().strip())
            self.record.setValue("military_id_issue_date", self.military_id_issue_date_input.date())
            self.record.setValue("military_id_issued_by", self.military_id_issued_by_input.text().strip())
            
            # Внешность
            self.record.setValue("appearance_features", self.appearance_features_input.toPlainText())
            self.record.setValue("personal_marks", self.personal_marks_input.toPlainText())
            self.record.setValue("federal_search_info", self.federal_search_info_input.toPlainText())
            self.record.setValue("military_contacts", self.military_contacts_input.text().strip())
            self.record.setValue("relatives_info", self.relatives_info_input.toPlainText())
            
            # Обновляем запись в модели
            if not self.social_data_model.setRecord(0, self.record):
                raise Exception(f"Ошибка при обновлении записи: {self.social_data_model.lastError().text()}")
            
            # Подтверждаем изменения
            if not self.social_data_model.submitAll():
                raise Exception(f"Ошибка при сохранении изменений: {self.social_data_model.lastError().text()}")
            
            # Логирование обновления
            if self.audit_logger:
                new_data = self._get_current_data()
                self.audit_logger.log_krd_update(self.krd_id, self.old_data, new_data)
                self.old_data = new_data
            
            QMessageBox.information(self, "Успех", "Данные успешно сохранены")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении данных:\n{str(e)}")
    
    def reject(self):
        """Отмена изменений"""
        self.social_data_model.revertAll()
        super().reject()