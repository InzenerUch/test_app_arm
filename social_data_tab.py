"""
Вкладка социально-демографических данных с поддержкой изображений
Соответствует структуре из шаблона "Шаблон проги.xlsx"
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QDateEdit, QComboBox, QLabel, QPushButton, QFileDialog, 
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, QByteArray
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtSql import QSqlQuery
import os
import traceback

from autocomplete_helper import AutocompleteHelper


class SocialDataTab(QWidget):
    """Вкладка социально-демографических данных с поддержкой изображений"""
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.record = None
        
        # === ИНИЦИАЛИЗАЦИЯ ПОМОЩНИКА АВТОДОПОЛНЕНИЯ ===
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        
        # Хранилище путей к временным файлам изображений
        self.photo_paths = {
            'civilian': None,
            'military_headgear': None,
            'military_no_headgear': None,
            'distinctive_marks': None
        }
        # Хранилище оригинальных фото из базы
        self.original_photos = {
            'civilian': None,
            'military_headgear': None,
            'military_no_headgear': None,
            'distinctive_marks': None
        }
        
        # === ВАЖНО: Сначала init_ui(), потом load_data() ===
        self.init_ui()
        self.load_data()
        
        # === НАСТРОЙКА АВТОДОПОЛНЕНИЯ ПОСЛЕ ЗАГРУЗКИ ===
        self.setup_autocomplete_fields()
    
    def init_ui(self):
        """Инициализация интерфейса - ВСЕ виджеты создаются здесь"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # === Группа 1: Основные данные ===
        group1 = QGroupBox("Основные данные (поля со знаком * обязательны)")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group1_layout = QGridLayout()
        group1_layout.setSpacing(8)
        
        group1_layout.addWidget(QLabel("Фамилия *:"), 0, 0)
        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("Введите фамилию")
        group1_layout.addWidget(self.surname_input, 0, 1)
        
        group1_layout.addWidget(QLabel("Имя *:"), 0, 2)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите имя")
        group1_layout.addWidget(self.name_input, 0, 3)
        
        group1_layout.addWidget(QLabel("Отчество *:"), 0, 4)
        self.patronymic_input = QLineEdit()
        self.patronymic_input.setPlaceholderText("Введите отчество")
        group1_layout.addWidget(self.patronymic_input, 0, 5)
        
        group1_layout.addWidget(QLabel("Табельный номер:"), 1, 0)
        self.tab_number_input = QLineEdit()
        group1_layout.addWidget(self.tab_number_input, 1, 1)
        
        group1_layout.addWidget(QLabel("Личный номер:"), 1, 2)
        self.personal_number_input = QLineEdit()
        group1_layout.addWidget(self.personal_number_input, 1, 3)
        
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
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group2_layout = QGridLayout()
        group2_layout.setSpacing(8)
        
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
        group3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group3_layout = QGridLayout()
        group3_layout.setSpacing(8)
        
        group3_layout.addWidget(QLabel("Каким комиссариатом призван:"), 0, 0)
        self.drafted_by_commissariat_input = QLineEdit()
        group3_layout.addWidget(self.drafted_by_commissariat_input, 0, 1, 1, 3)
        
        group3_layout.addWidget(QLabel("Дата призыва:"), 1, 0)
        self.draft_date_input = QDateEdit()
        self.draft_date_input.setCalendarPopup(True)
        self.draft_date_input.setDate(QDate.currentDate())
        group3_layout.addWidget(self.draft_date_input, 1, 1)
        
        group3_layout.addWidget(QLabel("Каким ПОВСК отобран:"), 1, 2)
        self.povsk_input = QLineEdit()
        group3_layout.addWidget(self.povsk_input, 1, 3)
        
        group3_layout.addWidget(QLabel("Дата отбора:"), 2, 0)
        self.selection_date_input = QDateEdit()
        self.selection_date_input.setCalendarPopup(True)
        self.selection_date_input.setDate(QDate.currentDate())
        group3_layout.addWidget(self.selection_date_input, 2, 1)
        
        group3.setLayout(group3_layout)
        layout.addWidget(group3)
        
        # === Группа 4: Образование и судимость ===
        group4 = QGroupBox("Образование и судимость")
        group4.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group4_layout = QGridLayout()
        group4_layout.setSpacing(8)
        
        group4_layout.addWidget(QLabel("Образование:"), 0, 0)
        self.education_input = QLineEdit()
        group4_layout.addWidget(self.education_input, 0, 1, 1, 3)
        
        group4_layout.addWidget(QLabel("Сведения о судимости:"), 1, 0)
        self.criminal_record_input = QTextEdit()
        self.criminal_record_input.setMaximumHeight(60)
        group4_layout.addWidget(self.criminal_record_input, 1, 1, 1, 3)
        
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
        group5.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group5_layout = QGridLayout()
        group5_layout.setSpacing(8)
        
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
        group6.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group6_layout = QGridLayout()
        group6_layout.setSpacing(8)
        
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
        
        # === Группа 7: Внешность и фотографии ===
        group7 = QGroupBox("Особенности внешности и фотографии")
        group7.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group7_layout = QVBoxLayout()
        group7_layout.setSpacing(10)
        
        text_grid = QGridLayout()
        text_grid.setSpacing(8)
        
        text_grid.addWidget(QLabel("Особенности внешности:"), 0, 0)
        self.appearance_features_input = QTextEdit()
        self.appearance_features_input.setMaximumHeight(60)
        text_grid.addWidget(self.appearance_features_input, 0, 1, 1, 3)
        
        text_grid.addWidget(QLabel("Личные приметы:"), 1, 0)
        self.personal_marks_input = QTextEdit()
        self.personal_marks_input.setMaximumHeight(60)
        text_grid.addWidget(self.personal_marks_input, 1, 1, 1, 3)
        
        text_grid.addWidget(QLabel("Сведения о федеральном розыске:"), 2, 0)
        self.federal_search_info_input = QTextEdit()
        self.federal_search_info_input.setMaximumHeight(60)
        text_grid.addWidget(self.federal_search_info_input, 2, 1, 1, 3)
        
        text_grid.addWidget(QLabel("Контакты военнослужащего:"), 3, 0)
        self.military_contacts_input = QLineEdit()
        text_grid.addWidget(self.military_contacts_input, 3, 1, 1, 3)
        
        text_grid.addWidget(QLabel("Сведения о близких родственниках:"), 4, 0)
        self.relatives_info_input = QTextEdit()
        self.relatives_info_input.setMaximumHeight(60)
        text_grid.addWidget(self.relatives_info_input, 4, 1, 1, 3)
        
        group7_layout.addLayout(text_grid)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        group7_layout.addWidget(separator)
        
        photos_title = QLabel("Фотографии военнослужащего")
        photos_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        photos_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group7_layout.addWidget(photos_title)
        
        photos_grid = QGridLayout()
        photos_grid.setSpacing(15)
        
        # === ФОТО 1: Гражданская одежда ===
        photo1_layout = QVBoxLayout()
        photo1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo1_label = QLabel("Фото в гражданской одежде:")
        photo1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo1_layout.addWidget(photo1_label)
        
        # === ВАЖНО: Создаём все label для фото ===
        self.photo_civilian_label = QLabel("Нет фото")
        self.photo_civilian_label.setFixedSize(180, 240)
        self.photo_civilian_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                background-color: #f8f9fa;
                color: #6c757d;
                font-size: 12px;
            }
        """)
        self.photo_civilian_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo1_layout.addWidget(self.photo_civilian_label)
        
        civilian_btn = QPushButton("Загрузить фото")
        civilian_btn.setMinimumWidth(150)
        civilian_btn.clicked.connect(lambda: self.load_photo('civilian'))
        photo1_layout.addWidget(civilian_btn)
        
        civilian_export_btn = QPushButton("Выгрузить фото")
        civilian_export_btn.setMinimumWidth(150)
        civilian_export_btn.clicked.connect(lambda: self.export_photo('civilian'))
        photo1_layout.addWidget(civilian_export_btn)
        
        photos_grid.addLayout(photo1_layout, 0, 0)
        
        # === ФОТО 2: Военная форма с головным убором ===
        photo2_layout = QVBoxLayout()
        photo2_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo2_label = QLabel("Фото в военной форме\nс головным убором:")
        photo2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo2_layout.addWidget(photo2_label)
        
        # === ВАЖНО: Создаём label ===
        self.photo_military_headgear_label = QLabel("Нет фото")
        self.photo_military_headgear_label.setFixedSize(180, 240)
        self.photo_military_headgear_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                background-color: #f8f9fa;
                color: #6c757d;
                font-size: 12px;
            }
        """)
        self.photo_military_headgear_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo2_layout.addWidget(self.photo_military_headgear_label)
        
        military_headgear_btn = QPushButton("Загрузить фото")
        military_headgear_btn.setMinimumWidth(150)
        military_headgear_btn.clicked.connect(lambda: self.load_photo('military_headgear'))
        photo2_layout.addWidget(military_headgear_btn)
        
        military_headgear_export_btn = QPushButton("Выгрузить фото")
        military_headgear_export_btn.setMinimumWidth(150)
        military_headgear_export_btn.clicked.connect(lambda: self.export_photo('military_headgear'))
        photo2_layout.addWidget(military_headgear_export_btn)
        
        photos_grid.addLayout(photo2_layout, 0, 1)
        
        # === ФОТО 3: Военная форма без головного убора ===
        photo3_layout = QVBoxLayout()
        photo3_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo3_label = QLabel("Фото в военной форме\nбез головного убора:")
        photo3_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo3_layout.addWidget(photo3_label)
        
        # === ВАЖНО: Создаём label ===
        self.photo_military_no_headgear_label = QLabel("Нет фото")
        self.photo_military_no_headgear_label.setFixedSize(180, 240)
        self.photo_military_no_headgear_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                background-color: #f8f9fa;
                color: #6c757d;
                font-size: 12px;
            }
        """)
        self.photo_military_no_headgear_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo3_layout.addWidget(self.photo_military_no_headgear_label)
        
        military_no_headgear_btn = QPushButton("Загрузить фото")
        military_no_headgear_btn.setMinimumWidth(150)
        military_no_headgear_btn.clicked.connect(lambda: self.load_photo('military_no_headgear'))
        photo3_layout.addWidget(military_no_headgear_btn)
        
        military_no_headgear_export_btn = QPushButton("Выгрузить фото")
        military_no_headgear_export_btn.setMinimumWidth(150)
        military_no_headgear_export_btn.clicked.connect(lambda: self.export_photo('military_no_headgear'))
        photo3_layout.addWidget(military_no_headgear_export_btn)
        
        photos_grid.addLayout(photo3_layout, 0, 2)
        
        # === ФОТО 4: Отличительные приметы ===
        photo4_layout = QVBoxLayout()
        photo4_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo4_label = QLabel("Фото отличительных примет:\n(татуировки, шрамы,\nотсутствие зубов, пальцев и т.д.)")
        photo4_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo4_layout.addWidget(photo4_label)
        
        # === ВАЖНО: Создаём label ===
        self.photo_distinctive_marks_label = QLabel("Нет фото")
        self.photo_distinctive_marks_label.setFixedSize(180, 240)
        self.photo_distinctive_marks_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #999;
                background-color: #f8f9fa;
                color: #6c757d;
                font-size: 12px;
            }
        """)
        self.photo_distinctive_marks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo4_layout.addWidget(self.photo_distinctive_marks_label)
        
        distinctive_marks_btn = QPushButton("Загрузить фото")
        distinctive_marks_btn.setMinimumWidth(150)
        distinctive_marks_btn.clicked.connect(lambda: self.load_photo('distinctive_marks'))
        photo4_layout.addWidget(distinctive_marks_btn)
        
        distinctive_marks_export_btn = QPushButton("Выгрузить фото")
        distinctive_marks_export_btn.setMinimumWidth(150)
        distinctive_marks_export_btn.clicked.connect(lambda: self.export_photo('distinctive_marks'))
        photo4_layout.addWidget(distinctive_marks_export_btn)
        
        photos_grid.addLayout(photo4_layout, 0, 3)
        
        group7_layout.addLayout(photos_grid)
        group7.setLayout(group7_layout)
        layout.addWidget(group7)
        
        layout.addStretch()
        
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def setup_autocomplete_fields(self):
        """Настройка автодополнения для текстовых полей"""
        
        fields_config = [
            (self.surname_input, 'surname', 50),
            (self.name_input, 'name', 50),
            (self.patronymic_input, 'patronymic', 50),
            (self.tab_number_input, 'tab_number', 30),
            (self.personal_number_input, 'personal_number', 30),
            (self.birth_place_town_input, 'birth_place_town', 20),
            (self.birth_place_district_input, 'birth_place_district', 20),
            (self.birth_place_region_input, 'birth_place_region', 20),
            (self.birth_place_country_input, 'birth_place_country', 20),
            (self.drafted_by_commissariat_input, 'drafted_by_commissariat', 20),
            (self.povsk_input, 'povsk', 20),
            (self.education_input, 'education', 15),
            (self.social_media_account_input, 'social_media_account', 20),
            (self.bank_card_number_input, 'bank_card_number', 20),
            (self.passport_series_input, 'passport_series', 20),
            (self.passport_number_input, 'passport_number', 20),
            (self.passport_issued_by_input, 'passport_issued_by', 20),
            (self.military_id_series_input, 'military_id_series', 20),
            (self.military_id_number_input, 'military_id_number', 20),
            (self.military_id_issued_by_input, 'military_id_issued_by', 20),
            (self.military_contacts_input, 'military_contacts', 20),
        ]
        
        for field_widget, column_name, max_items in fields_config:
            self.autocomplete_helper.setup_autocomplete(
                field_widget, 
                'social_data',
                column_name,
                max_items=max_items,
                show_on_focus=True
            )
        
        print(f"✅ Автодополнение настроено для {len(fields_config)} полей")
    
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
    
    def load_data(self):
        """Загрузка данных из базы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT * FROM krd.social_data 
            WHERE krd_id = ?
            ORDER BY id DESC 
            LIMIT 1
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        if query.next():
            self.record = query.record()
            
            self.surname_input.setText(query.value("surname") or "")
            self.name_input.setText(query.value("name") or "")
            self.patronymic_input.setText(query.value("patronymic") or "")
            self.tab_number_input.setText(query.value("tab_number") or "")
            self.personal_number_input.setText(query.value("personal_number") or "")
            
            category_id = query.value("category_id")
            if category_id:
                index = self.category_combo.findData(category_id)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)
            
            rank_id = query.value("rank_id")
            if rank_id:
                index = self.rank_combo.findData(rank_id)
                if index >= 0:
                    self.rank_combo.setCurrentIndex(index)
            
            self.birth_place_town_input.setText(query.value("birth_place_town") or "")
            self.birth_place_district_input.setText(query.value("birth_place_district") or "")
            self.birth_place_region_input.setText(query.value("birth_place_region") or "")
            self.birth_place_country_input.setText(query.value("birth_place_country") or "")
            
            birth_date = query.value("birth_date")
            if birth_date:
                self.birth_date_input.setDate(birth_date)
            
            self.drafted_by_commissariat_input.setText(query.value("drafted_by_commissariat") or "")
            
            draft_date = query.value("draft_date")
            if draft_date:
                self.draft_date_input.setDate(draft_date)
            
            self.povsk_input.setText(query.value("povsk") or "")
            
            selection_date = query.value("selection_date")
            if selection_date:
                self.selection_date_input.setDate(selection_date)
            
            self.education_input.setText(query.value("education") or "")
            self.criminal_record_input.setPlainText(query.value("criminal_record") or "")
            self.social_media_account_input.setText(query.value("social_media_account") or "")
            self.bank_card_number_input.setText(query.value("bank_card_number") or "")
            
            self.passport_series_input.setText(query.value("passport_series") or "")
            self.passport_number_input.setText(query.value("passport_number") or "")
            
            passport_issue_date = query.value("passport_issue_date")
            if passport_issue_date:
                self.passport_issue_date_input.setDate(passport_issue_date)
            
            self.passport_issued_by_input.setText(query.value("passport_issued_by") or "")
            
            self.military_id_series_input.setText(query.value("military_id_series") or "")
            self.military_id_number_input.setText(query.value("military_id_number") or "")
            
            military_id_issue_date = query.value("military_id_issue_date")
            if military_id_issue_date:
                self.military_id_issue_date_input.setDate(military_id_issue_date)
            
            self.military_id_issued_by_input.setText(query.value("military_id_issued_by") or "")
            
            self.appearance_features_input.setPlainText(query.value("appearance_features") or "")
            self.personal_marks_input.setPlainText(query.value("personal_marks") or "")
            self.federal_search_info_input.setPlainText(query.value("federal_search_info") or "")
            self.military_contacts_input.setText(query.value("military_contacts") or "")
            self.relatives_info_input.setPlainText(query.value("relatives_info") or "")
            
            # === Загрузка фотографий ===
            self.load_photo_from_db(query, 'photo_civilian', self.photo_civilian_label, 'civilian')
            self.load_photo_from_db(query, 'photo_military_headgear', self.photo_military_headgear_label, 'military_headgear')
            self.load_photo_from_db(query, 'photo_military_no_headgear', self.photo_military_no_headgear_label, 'military_no_headgear')
            self.load_photo_from_db(query, 'photo_distinctive_marks', self.photo_distinctive_marks_label, 'distinctive_marks')
    
    def load_photo_from_db(self, query, field_name, label_widget, photo_type):
        """Загрузка фотографии из базы данных"""
        photo_data = query.value(field_name)
        self.original_photos[photo_type] = None
        
        if photo_data and (isinstance(photo_data, bytes) or hasattr(photo_data, 'data')):
            try:
                if hasattr(photo_data, 'data'):
                    photo_bytes = bytes(photo_data.data())
                else:
                    photo_bytes = bytes(photo_data)
                
                self.original_photos[photo_type] = photo_bytes
                
                pixmap = QPixmap()
                pixmap.loadFromData(photo_bytes)
                
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        180, 240, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    label_widget.setPixmap(scaled_pixmap)
                    label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    label_widget.setStyleSheet("QLabel { border: 2px solid #4CAF50; background-color: white; }")
                else:
                    label_widget.setText("Ошибка загрузки")
            
            except Exception as e:
                traceback.print_exc()
                label_widget.setText("Ошибка")
        else:
            label_widget.setText("Нет фото")
            label_widget.setStyleSheet("QLabel { border: 2px dashed #999; background-color: #f8f9fa; color: #6c757d; font-size: 12px; }")
    
    def load_photo(self, photo_type):
        """Загрузка фотографии из файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Выберите фотографию ({photo_type})",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp);;Все файлы (*)"
        )
        if file_path:
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 5 * 1024 * 1024:
                    QMessageBox.warning(self, "Ошибка", "Размер файла не должен превышать 5 МБ")
                    return
                
                pixmap = QPixmap(file_path)
                if pixmap.isNull():
                    QMessageBox.warning(self, "Ошибка", "Невозможно загрузить изображение.")
                    return
                
                scaled_pixmap = pixmap.scaled(
                    180, 240, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                
                label_map = {
                    'civilian': self.photo_civilian_label,
                    'military_headgear': self.photo_military_headgear_label,
                    'military_no_headgear': self.photo_military_no_headgear_label,
                    'distinctive_marks': self.photo_distinctive_marks_label
                }
                label_map[photo_type].setPixmap(scaled_pixmap)
                label_map[photo_type].setAlignment(Qt.AlignmentFlag.AlignCenter)
                label_map[photo_type].setStyleSheet("""
                    QLabel {
                        border: 2px solid #2196F3;
                        background-color: white;
                    }
                """)
                
                self.photo_paths[photo_type] = file_path
                print(f"✅ Фото '{photo_type}' загружено: {file_path}")
            
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки изображения:\n{str(e)}")
    
    def save_data(self):
        """Сохранение данных в базу"""
        validation_error = self.validate_required_fields()
        if validation_error:
            raise ValueError(validation_error)
        
        data = {
            "krd_id": self.krd_id,
            "surname": self.surname_input.text().strip(),
            "name": self.name_input.text().strip(),
            "patronymic": self.patronymic_input.text().strip(),
            "birth_date": self.birth_date_input.date(),
            "birth_place_town": self.birth_place_town_input.text().strip(),
            "birth_place_district": self.birth_place_district_input.text().strip(),
            "birth_place_region": self.birth_place_region_input.text().strip(),
            "birth_place_country": self.birth_place_country_input.text().strip(),
            "tab_number": self.tab_number_input.text().strip(),
            "personal_number": self.personal_number_input.text().strip(),
            "category_id": self.category_combo.currentData(),
            "rank_id": self.rank_combo.currentData(),
            "drafted_by_commissariat": self.drafted_by_commissariat_input.text().strip(),
            "draft_date": self.draft_date_input.date(),
            "povsk": self.povsk_input.text().strip(),
            "selection_date": self.selection_date_input.date(),
            "education": self.education_input.text().strip(),
            "criminal_record": self.criminal_record_input.toPlainText(),
            "social_media_account": self.social_media_account_input.text().strip(),
            "bank_card_number": self.bank_card_number_input.text().strip(),
            "passport_series": self.passport_series_input.text().strip(),
            "passport_number": self.passport_number_input.text().strip(),
            "passport_issue_date": self.passport_issue_date_input.date(),
            "passport_issued_by": self.passport_issued_by_input.text().strip(),
            "military_id_series": self.military_id_series_input.text().strip(),
            "military_id_number": self.military_id_number_input.text().strip(),
            "military_id_issue_date": self.military_id_issue_date_input.date(),
            "military_id_issued_by": self.military_id_issued_by_input.text().strip(),
            "appearance_features": self.appearance_features_input.toPlainText(),
            "personal_marks": self.personal_marks_input.toPlainText(),
            "federal_search_info": self.federal_search_info_input.toPlainText(),
            "military_contacts": self.military_contacts_input.text().strip(),
            "relatives_info": self.relatives_info_input.toPlainText()
        }
        
        photo_types = ['civilian', 'military_headgear', 'military_no_headgear', 'distinctive_marks']
        for photo_type in photo_types:
            field_name = f"photo_{photo_type}"
            final_photo_bytes = None
            
            new_path = self.photo_paths.get(photo_type)
            if new_path and os.path.exists(new_path):
                try:
                    with open(new_path, 'rb') as f:
                        final_photo_bytes = f.read()
                    if len(final_photo_bytes) > 5 * 1024 * 1024:
                        raise ValueError(f"Фото '{photo_type}' превышает 5 МБ")
                except Exception as e:
                    raise Exception(f"Ошибка обработки фото '{photo_type}': {str(e)}")
            elif self.original_photos.get(photo_type):
                final_photo_bytes = self.original_photos[photo_type]
            
            if final_photo_bytes:
                data[field_name] = QByteArray(final_photo_bytes)
            else:
                data[field_name] = QByteArray()
        
        query = QSqlQuery(self.db)
        
        if self.record:
            query.prepare("""
                UPDATE krd.social_data SET
                    surname = :surname, name = :name, patronymic = :patronymic,
                    birth_date = :birth_date, birth_place_town = :birth_place_town,
                    birth_place_district = :birth_place_district, birth_place_region = :birth_place_region,
                    birth_place_country = :birth_place_country, tab_number = :tab_number,
                    personal_number = :personal_number, category_id = :category_id,
                    rank_id = :rank_id, drafted_by_commissariat = :drafted_by_commissariat,
                    draft_date = :draft_date, povsk = :povsk, selection_date = :selection_date,
                    education = :education, criminal_record = :criminal_record,
                    social_media_account = :social_media_account, bank_card_number = :bank_card_number,
                    passport_series = :passport_series, passport_number = :passport_number,
                    passport_issue_date = :passport_issue_date, passport_issued_by = :passport_issued_by,
                    military_id_series = :military_id_series, military_id_number = :military_id_number,
                    military_id_issue_date = :military_id_issue_date, military_id_issued_by = :military_id_issued_by,
                    appearance_features = :appearance_features, personal_marks = :personal_marks,
                    federal_search_info = :federal_search_info, military_contacts = :military_contacts,
                    relatives_info = :relatives_info,
                    photo_civilian = :photo_civilian,
                    photo_military_headgear = :photo_military_headgear,
                    photo_military_no_headgear = :photo_military_no_headgear,
                    photo_distinctive_marks = :photo_distinctive_marks
                WHERE id = :id
            """)
            query.bindValue(":id", self.record.value("id"))
        else:
            query.prepare("""
                INSERT INTO krd.social_data (
                    krd_id, surname, name, patronymic, birth_date, birth_place_town,
                    birth_place_district, birth_place_region, birth_place_country, tab_number,
                    personal_number, category_id, rank_id, drafted_by_commissariat, draft_date,
                    povsk, selection_date, education, criminal_record, social_media_account,
                    bank_card_number, passport_series, passport_number, passport_issue_date,
                    passport_issued_by, military_id_series, military_id_number, military_id_issue_date,
                    military_id_issued_by, appearance_features, personal_marks, federal_search_info,
                    military_contacts, relatives_info,
                    photo_civilian, photo_military_headgear, 
                    photo_military_no_headgear, photo_distinctive_marks
                ) VALUES (
                    :krd_id, :surname, :name, :patronymic, :birth_date, :birth_place_town,
                    :birth_place_district, :birth_place_region, :birth_place_country, :tab_number,
                    :personal_number, :category_id, :rank_id, :drafted_by_commissariat, :draft_date,
                    :povsk, :selection_date, :education, :criminal_record, :social_media_account,
                    :bank_card_number, :passport_series, :passport_number, :passport_issue_date,
                    :passport_issued_by, :military_id_series, :military_id_number, :military_id_issue_date,
                    :military_id_issued_by, :appearance_features, :personal_marks, :federal_search_info,
                    :military_contacts, :relatives_info,
                    :photo_civilian, :photo_military_headgear,
                    :photo_military_no_headgear, :photo_distinctive_marks
                )
            """)
        
        for key, value in data.items():
            query.bindValue(f":{key}", value)
        
        if not query.exec():
            raise Exception(f"Ошибка сохранения данных: {query.lastError().text()}")
        
        # === ОБНОВЛЕНИЕ АВТОДОПОЛНЕНИЯ ===
        self.autocomplete_helper.refresh_all_fields()
        
        print(f"✅ Данные успешно сохранены для КРД-{self.krd_id}")
    
    def validate_required_fields(self):
        """Валидация обязательных полей"""
        if not self.surname_input.text().strip():
            return "Поле 'Фамилия' обязательно для заполнения"
        if not self.name_input.text().strip():
            return "Поле 'Имя' обязательно для заполнения"
        if not self.patronymic_input.text().strip():
            return "Поле 'Отчество' обязательно для заполнения"
        return None
    
    def export_photo(self, photo_type):
        """Выгрузка фотографии в файл"""
        photo_bytes = None
        
        new_path = self.photo_paths.get(photo_type)
        if new_path and os.path.exists(new_path):
            try:
                with open(new_path, 'rb') as f:
                    photo_bytes = f.read()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Невозможно прочитать файл:\n{str(e)}")
                return
        elif self.original_photos.get(photo_type):
            photo_bytes = self.original_photos[photo_type]
        
        if not photo_bytes:
            QMessageBox.information(self, "Информация", f"Фото '{photo_type}' отсутствует.")
            return
        
        default_name = f"КРД-{self.krd_id}_{photo_type}.jpg"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Сохранить фото ({photo_type})",
            default_name,
            "Изображения (*.jpg *.png *.bmp);;Все файлы (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'wb') as f:
                    f.write(photo_bytes)
                
                if self.audit_logger:
                    self.audit_logger.log_action(
                        action_type='PHOTO_EXPORT',
                        table_name='social_data',
                        record_id=self.krd_id,
                        krd_id=self.krd_id,
                        description=f'Выгружено фото "{photo_type}" для КРД-{self.krd_id}'
                    )
                
                QMessageBox.information(self, "Успешно", f"Фото сохранено:\n{file_path}")
                print(f"✅ Фото '{photo_type}' выгружено: {file_path}")
            
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{str(e)}")