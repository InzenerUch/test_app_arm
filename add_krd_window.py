"""
Модуль для окна добавления новой КРД и социальных данных
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, 
    QLineEdit, QTextEdit, QDateEdit, QSpinBox, 
    QPushButton, QMessageBox, QGroupBox, QComboBox,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlQuery


class AddKrdWindow(QDialog):
    """
    Окно для добавления новой КРД и социальных данных
    """
    
    def __init__(self, db_connection):
        """
        Инициализация окна добавления КРД
        
        Args:
            db_connection: соединение с базой данных
        """
        super().__init__()
        self.db = db_connection
        
        self.setWindowTitle("Добавить новую КРД")
        self.setModal(True)
        self.resize(650, 500)  # Уменьшили начальный размер
        
        self.init_ui()
    
    def init_ui(self):
        """
        Инициализация пользовательского интерфейса
        """
        main_layout = QVBoxLayout()
        
        # Создаем область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Позволяет содержимому растягиваться
        
        # Создаем центральный виджет для области прокрутки
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Создаем форму для ввода данных
        form_layout = QFormLayout()
        
        # Обязательные поля
        self.surname_input = QLineEdit()
        self.name_input = QLineEdit()
        self.patronymic_input = QLineEdit()
        
        # Добавляем обязательные поля в форму
        form_layout.addRow("Фамилия*:", self.surname_input)
        form_layout.addRow("Имя*:", self.name_input)
        form_layout.addRow("Отчество*:", self.patronymic_input)
        
        # Дополнительные поля социальных данных
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setDate(QDate.currentDate())
        self.birth_date_input.setCalendarPopup(True)
        
        self.birth_place_town_input = QLineEdit()
        self.birth_place_district_input = QLineEdit()
        self.birth_place_region_input = QLineEdit()
        self.birth_place_country_input = QLineEdit()
        
        self.tab_number_input = QLineEdit()
        self.personal_number_input = QLineEdit()
        
        # Выпадающий список для категории
        self.category_combo = QComboBox()
        self.load_categories()
        
        # Выпадающий список для звания
        self.rank_combo = QComboBox()
        self.load_ranks()
        
        self.drafted_by_commissariat_input = QLineEdit()
        self.draft_date_input = QDateEdit()
        self.draft_date_input.setDate(QDate.currentDate())
        self.draft_date_input.setCalendarPopup(True)
        
        self.povsk_input = QLineEdit()
        self.selection_date_input = QDateEdit()
        self.selection_date_input.setDate(QDate.currentDate())
        self.selection_date_input.setCalendarPopup(True)
        
        self.education_input = QLineEdit()
        self.criminal_record_input = QTextEdit()
        self.social_media_account_input = QLineEdit()
        self.bank_card_number_input = QLineEdit()
        
        # Паспортные данные
        self.passport_series_input = QLineEdit()
        self.passport_number_input = QLineEdit()
        self.passport_issue_date_input = QDateEdit()
        self.passport_issue_date_input.setDate(QDate.currentDate())
        self.passport_issue_date_input.setCalendarPopup(True)
        self.passport_issued_by_input = QLineEdit()
        
        # Военный билет
        self.military_id_series_input = QLineEdit()
        self.military_id_number_input = QLineEdit()
        self.military_id_issue_date_input = QDateEdit()
        self.military_id_issue_date_input.setDate(QDate.currentDate())
        self.military_id_issue_date_input.setCalendarPopup(True)
        self.military_id_issued_by_input = QLineEdit()
        
        # Внешность
        self.appearance_features_input = QTextEdit()
        self.personal_marks_input = QTextEdit()
        self.federal_search_info_input = QTextEdit()
        self.military_contacts_input = QLineEdit()
        self.relatives_info_input = QTextEdit()
        
        # Добавляем дополнительные поля в форму
        form_layout.addRow("Дата рождения:", self.birth_date_input)
        form_layout.addRow("Место рождения (город):", self.birth_place_town_input)
        form_layout.addRow("Место рождения (район):", self.birth_place_district_input)
        form_layout.addRow("Место рождения (регион):", self.birth_place_region_input)
        form_layout.addRow("Место рождения (страна):", self.birth_place_country_input)
        form_layout.addRow("Табельный номер:", self.tab_number_input)
        form_layout.addRow("Личный номер:", self.personal_number_input)
        form_layout.addRow("Категория:", self.category_combo)
        form_layout.addRow("Воинское звание:", self.rank_combo)
        form_layout.addRow("Призван военкоматом:", self.drafted_by_commissariat_input)
        form_layout.addRow("Дата призыва:", self.draft_date_input)
        form_layout.addRow("ПВО/ПВС:", self.povsk_input)
        form_layout.addRow("Дата отбора:", self.selection_date_input)
        form_layout.addRow("Образование:", self.education_input)
        form_layout.addRow("Судимость:", self.criminal_record_input)
        form_layout.addRow("Соцсети:", self.social_media_account_input)
        form_layout.addRow("Банковская карта:", self.bank_card_number_input)
        form_layout.addRow("Серия паспорта:", self.passport_series_input)
        form_layout.addRow("Номер паспорта:", self.passport_number_input)
        form_layout.addRow("Дата выдачи паспорта:", self.passport_issue_date_input)
        form_layout.addRow("Кем выдан паспорт:", self.passport_issued_by_input)
        form_layout.addRow("Серия воен. билета:", self.military_id_series_input)
        form_layout.addRow("Номер воен. билета:", self.military_id_number_input)
        form_layout.addRow("Дата выдачи воен. билета:", self.military_id_issue_date_input)
        form_layout.addRow("Кем выдан воен. билет:", self.military_id_issued_by_input)
        form_layout.addRow("Особенности внешности:", self.appearance_features_input)
        form_layout.addRow("Особые приметы:", self.personal_marks_input)
        form_layout.addRow("Инф. о федеральном розыске:", self.federal_search_info_input)
        form_layout.addRow("Военные контакты:", self.military_contacts_input)
        form_layout.addRow("Информация о родных:", self.relatives_info_input)
        
        scroll_layout.addLayout(form_layout)
        
        # Устанавливаем виджет в область прокрутки
        scroll_area.setWidget(scroll_widget)
        
        main_layout.addWidget(scroll_area)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_krd)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_categories(self):
        """
        Загрузка категорий из базы данных
        """
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.categories ORDER BY name")
        
        while query.next():
            category_id = query.value(0)
            category_name = query.value(1)
            self.category_combo.addItem(category_name, category_id)
    
    def load_ranks(self):
        """
        Загрузка воинских званий из базы данных
        """
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.ranks ORDER BY name")
        
        while query.next():
            rank_id = query.value(0)
            rank_name = query.value(1)
            self.rank_combo.addItem(rank_name, rank_id)
    
    def save_krd(self):
        """
        Сохранение новой КРД и социальных данных
        """
        # Проверяем обязательные поля
        if not self.validate_inputs():
            return
        
        try:
            # Начинаем транзакцию
            self.db.transaction()
            
            # Создаем новую запись в таблице krd
            krd_query = QSqlQuery(self.db)
            krd_query.prepare("INSERT INTO krd.krd DEFAULT VALUES RETURNING id")
            krd_query.exec()
            
            if not krd_query.next():
                raise Exception("Не удалось создать новую КРД")
            
            krd_id = krd_query.value(0)
            
            # Создаем запись в таблице social_data
            social_query = QSqlQuery(self.db)
            social_query.prepare("""
                INSERT INTO krd.social_data (
                    krd_id, surname, name, patronymic, birth_date, 
                    birth_place_town, birth_place_district, birth_place_region, birth_place_country,
                    tab_number, personal_number, category_id, rank_id,
                    drafted_by_commissariat, draft_date, povsk, selection_date,
                    education, criminal_record, social_media_account, bank_card_number,
                    passport_series, passport_number, passport_issue_date, passport_issued_by,
                    military_id_series, military_id_number, military_id_issue_date, military_id_issued_by,
                    appearance_features, personal_marks, federal_search_info, military_contacts, relatives_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
            
            # Привязываем значения
            social_query.addBindValue(krd_id)
            social_query.addBindValue(self.surname_input.text().strip())
            social_query.addBindValue(self.name_input.text().strip())
            social_query.addBindValue(self.patronymic_input.text().strip())
            social_query.addBindValue(self.birth_date_input.date())
            
            social_query.addBindValue(self.birth_place_town_input.text().strip())
            social_query.addBindValue(self.birth_place_district_input.text().strip())
            social_query.addBindValue(self.birth_place_region_input.text().strip())
            social_query.addBindValue(self.birth_place_country_input.text().strip())
            
            social_query.addBindValue(self.tab_number_input.text().strip())
            social_query.addBindValue(self.personal_number_input.text().strip())
            
            # Получаем ID выбранной категории и звания
            category_id = self.category_combo.currentData()
            rank_id = self.rank_combo.currentData()
            
            social_query.addBindValue(category_id if category_id is not None else None)
            social_query.addBindValue(rank_id if rank_id is not None else None)
            
            social_query.addBindValue(self.drafted_by_commissariat_input.text().strip())
            social_query.addBindValue(self.draft_date_input.date())
            social_query.addBindValue(self.povsk_input.text().strip())
            social_query.addBindValue(self.selection_date_input.date())
            
            social_query.addBindValue(self.education_input.text().strip())
            social_query.addBindValue(self.criminal_record_input.toPlainText())
            social_query.addBindValue(self.social_media_account_input.text().strip())
            social_query.addBindValue(self.bank_card_number_input.text().strip())
            
            social_query.addBindValue(self.passport_series_input.text().strip())
            social_query.addBindValue(self.passport_number_input.text().strip())
            social_query.addBindValue(self.passport_issue_date_input.date())
            social_query.addBindValue(self.passport_issued_by_input.text().strip())
            
            social_query.addBindValue(self.military_id_series_input.text().strip())
            social_query.addBindValue(self.military_id_number_input.text().strip())
            social_query.addBindValue(self.military_id_issue_date_input.date())
            social_query.addBindValue(self.military_id_issued_by_input.text().strip())
            
            social_query.addBindValue(self.appearance_features_input.toPlainText())
            social_query.addBindValue(self.personal_marks_input.toPlainText())
            social_query.addBindValue(self.federal_search_info_input.toPlainText())
            social_query.addBindValue(self.military_contacts_input.text().strip())
            social_query.addBindValue(self.relatives_info_input.toPlainText())
            
            if not social_query.exec():
                raise Exception(f"Ошибка при сохранении социальных данных: {social_query.lastError().text()}")
            
            # Фиксируем транзакцию
            self.db.commit()
            
            QMessageBox.information(self, "Успех", f"Новая КРД создана с ID: {krd_id}")
            
            # Закрываем окно
            self.accept()
            
        except Exception as e:
            # Откатываем транзакцию в случае ошибки
            self.db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении данных:\n{str(e)}")
    
    def validate_inputs(self):
        """
        Проверка обязательных полей
        """
        if not self.surname_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите фамилию")
            self.surname_input.setFocus()
            return False
        
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите имя")
            self.name_input.setFocus()
            return False
        
        if not self.patronymic_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите отчество")
            self.patronymic_input.setFocus()
            return False
        
        return True