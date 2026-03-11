"""
Вкладка социально-демографических данных
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QDateEdit, QComboBox, QLabel
)
from PyQt6.QtCore import QDate
from PyQt6.QtSql import QSqlQuery


class SocialDataTab(QWidget):
    """Вкладка социально-демографических данных"""
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.record = None
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # === Группа 1: Основные данные ===
        group1 = QGroupBox("Основные данные (поля со знаком * обязательны)")
        group1_layout = QGridLayout()
        
        group1_layout.addWidget(QLabel("Фамилия *:"), 0, 0)
        self.surname_input = QLineEdit()
        group1_layout.addWidget(self.surname_input, 0, 1)
        
        group1_layout.addWidget(QLabel("Имя *:"), 0, 2)
        self.name_input = QLineEdit()
        group1_layout.addWidget(self.name_input, 0, 3)
        
        group1_layout.addWidget(QLabel("Отчество *:"), 0, 4)
        self.patronymic_input = QLineEdit()
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
        group4_layout = QGridLayout()
        
        group4_layout.addWidget(QLabel("Образование:"), 0, 0)
        self.education_input = QLineEdit()
        group4_layout.addWidget(self.education_input, 0, 1, 1, 3)
        
        group4_layout.addWidget(QLabel("Сведения о судимости:"), 1, 0)
        self.criminal_record_input = QTextEdit()
        self.criminal_record_input.setMaximumHeight(80)
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
        group7_layout.addWidget(self.appearance_features_input, 0, 1, 1, 3)
        
        group7_layout.addWidget(QLabel("Личные приметы:"), 1, 0)
        self.personal_marks_input = QTextEdit()
        self.personal_marks_input.setMaximumHeight(80)
        group7_layout.addWidget(self.personal_marks_input, 1, 1, 1, 3)
        
        group7_layout.addWidget(QLabel("Сведения о федеральном розыске:"), 2, 0)
        self.federal_search_info_input = QTextEdit()
        self.federal_search_info_input.setMaximumHeight(80)
        group7_layout.addWidget(self.federal_search_info_input, 2, 1, 1, 3)
        
        group7_layout.addWidget(QLabel("Контакты военнослужащего:"), 3, 0)
        self.military_contacts_input = QLineEdit()
        group7_layout.addWidget(self.military_contacts_input, 3, 1, 1, 3)
        
        group7_layout.addWidget(QLabel("Сведения о близких родственниках:"), 4, 0)
        self.relatives_info_input = QTextEdit()
        self.relatives_info_input.setMaximumHeight(80)
        group7_layout.addWidget(self.relatives_info_input, 4, 1, 1, 3)
        
        group7.setLayout(group7_layout)
        layout.addWidget(group7)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
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
    
    def save_data(self):
        """Сохранение данных в базу"""
        # Проверка обязательных полей
        if not self.surname_input.text().strip():
            raise ValueError("Поле 'Фамилия' обязательно для заполнения")
        if not self.name_input.text().strip():
            raise ValueError("Поле 'Имя' обязательно для заполнения")
        if not self.patronymic_input.text().strip():
            raise ValueError("Поле 'Отчество' обязательно для заполнения")
        
        # Подготовка данных
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
        
        # Сохранение в базу
        query = QSqlQuery(self.db)
        
        if self.record:
            # Обновление существующей записи
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
                    relatives_info = :relatives_info
                WHERE id = :id
            """)
            query.bindValue(":id", self.record.value("id"))
        else:
            # Создание новой записи
            query.prepare("""
                INSERT INTO krd.social_data (
                    krd_id, surname, name, patronymic, birth_date, birth_place_town,
                    birth_place_district, birth_place_region, birth_place_country, tab_number,
                    personal_number, category_id, rank_id, drafted_by_commissariat, draft_date,
                    povsk, selection_date, education, criminal_record, social_media_account,
                    bank_card_number, passport_series, passport_number, passport_issue_date,
                    passport_issued_by, military_id_series, military_id_number, military_id_issue_date,
                    military_id_issued_by, appearance_features, personal_marks, federal_search_info,
                    military_contacts, relatives_info
                ) VALUES (
                    :krd_id, :surname, :name, :patronymic, :birth_date, :birth_place_town,
                    :birth_place_district, :birth_place_region, :birth_place_country, :tab_number,
                    :personal_number, :category_id, :rank_id, :drafted_by_commissariat, :draft_date,
                    :povsk, :selection_date, :education, :criminal_record, :social_media_account,
                    :bank_card_number, :passport_series, :passport_number, :passport_issue_date,
                    :passport_issued_by, :military_id_series, :military_id_number, :military_id_issue_date,
                    :military_id_issued_by, :appearance_features, :personal_marks, :federal_search_info,
                    :military_contacts, :relatives_info
                )
            """)
        
        # Привязка значений
        for key, value in data.items():
            query.bindValue(f":{key}", value)
        
        if not query.exec():
            raise Exception(f"Ошибка сохранения данных: {query.lastError().text()}")
        
        return True