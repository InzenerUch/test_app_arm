"""
Модуль для окна просмотра и редактирования данных КРД
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, 
    QLineEdit, QTextEdit, QDateEdit, QSpinBox, 
    QPushButton, QMessageBox, QGroupBox, QComboBox,
    QScrollArea, QWidget, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtSql import QSqlTableModel, QSqlRecord, QSqlQuery
from PyQt6.QtGui import QIntValidator

# Добавляем импорт логгера аудита
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
        self.audit_logger = audit_logger  # Сохраняем логгер аудита
        
        self.setWindowTitle(f"Данные КРД #{krd_id}")
        self.setModal(True)
        self.resize(650, 500)
        
        # Создаем модель для данных
        self.model = QSqlTableModel(db=self.db)
        self.model.setTable("krd.social_data")
        self.model.setFilter(f"krd_id = {krd_id}")
        self.model.select()
        
        # Проверяем, есть ли данные
        if self.model.rowCount() == 0:
            # Если записи нет, создаем новую
            self.create_new_record()
        
        # Получаем запись
        self.record = self.model.record(0)
        
        # Сохраняем старые значения для логирования изменений
        self.old_data = self._get_current_data()
        
        self.init_ui()
        self.setup_data_mapping()
    
    def create_new_record(self):
        """
        Создание новой записи, если она не существует
        """
        row = self.model.rowCount()
        self.model.insertRow(row)
        record = self.model.record(row)
        record.setValue("krd_id", self.krd_id)
        self.model.setRecord(row, record)
    
    def _get_current_data(self):
        """
        Получение текущих данных для логирования
        
        Returns:
            dict: словарь с текущими значениями полей
        """
        data = {}
        
        # Основные данные
        data['surname'] = self.record.value("surname") if self.record else ""
        data['name'] = self.record.value("name") if self.record else ""
        data['patronymic'] = self.record.value("patronymic") if self.record else ""
        data['birth_date'] = self.record.value("birth_date").toString("yyyy-MM-dd") if self.record and self.record.value("birth_date") else ""
        data['birth_place_town'] = self.record.value("birth_place_town") if self.record else ""
        data['birth_place_district'] = self.record.value("birth_place_district") if self.record else ""
        data['birth_place_region'] = self.record.value("birth_place_region") if self.record else ""
        data['birth_place_country'] = self.record.value("birth_place_country") if self.record else ""
        data['tab_number'] = self.record.value("tab_number") if self.record else ""
        data['personal_number'] = self.record.value("personal_number") if self.record else ""
        
        # Категория и звание
        data['category_id'] = self.record.value("category_id") if self.record else None
        data['rank_id'] = self.record.value("rank_id") if self.record else None
        
        # Призыв
        data['drafted_by_commissariat'] = self.record.value("drafted_by_commissariat") if self.record else ""
        data['draft_date'] = self.record.value("draft_date").toString("yyyy-MM-dd") if self.record and self.record.value("draft_date") else ""
        data['povsk'] = self.record.value("povsk") if self.record else ""
        data['selection_date'] = self.record.value("selection_date").toString("yyyy-MM-dd") if self.record and self.record.value("selection_date") else ""
        
        # Образование и судимость
        data['education'] = self.record.value("education") if self.record else ""
        data['criminal_record'] = self.record.value("criminal_record") if self.record else ""
        data['social_media_account'] = self.record.value("social_media_account") if self.record else ""
        data['bank_card_number'] = self.record.value("bank_card_number") if self.record else ""
        
        # Паспортные данные
        data['passport_series'] = self.record.value("passport_series") if self.record else ""
        data['passport_number'] = self.record.value("passport_number") if self.record else ""
        data['passport_issue_date'] = self.record.value("passport_issue_date").toString("yyyy-MM-dd") if self.record and self.record.value("passport_issue_date") else ""
        data['passport_issued_by'] = self.record.value("passport_issued_by") if self.record else ""
        
        # Военный билет
        data['military_id_series'] = self.record.value("military_id_series") if self.record else ""
        data['military_id_number'] = self.record.value("military_id_number") if self.record else ""
        data['military_id_issue_date'] = self.record.value("military_id_issue_date").toString("yyyy-MM-dd") if self.record and self.record.value("military_id_issue_date") else ""
        data['military_id_issued_by'] = self.record.value("military_id_issued_by") if self.record else ""
        
        # Внешность
        data['appearance_features'] = self.record.value("appearance_features") if self.record else ""
        data['personal_marks'] = self.record.value("personal_marks") if self.record else ""
        data['federal_search_info'] = self.record.value("federal_search_info") if self.record else ""
        data['military_contacts'] = self.record.value("military_contacts") if self.record else ""
        data['relatives_info'] = self.record.value("relatives_info") if self.record else ""
        
        return data
    
    def init_ui(self):
        """
        Инициализация пользовательского интерфейса
        """
        main_layout = QVBoxLayout()
        
        # Создаем вкладки
        tabs = QTabWidget()
        
        # Вкладка с основными данными
        main_data_widget = QWidget()
        main_data_layout = QVBoxLayout(main_data_widget)
        
        # Создаем область прокрутки для основных данных
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Создаем центральный виджет для области прокрутки
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Создаем форму для отображения данных
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
        self.draft_date_input.setCalendarPopup(True)
        
        self.povsk_input = QLineEdit()
        self.selection_date_input = QDateEdit()
        self.selection_date_input.setCalendarPopup(True)
        
        self.education_input = QLineEdit()
        self.criminal_record_input = QTextEdit()
        self.social_media_account_input = QLineEdit()
        self.bank_card_number_input = QLineEdit()
        
        # Паспортные данные
        self.passport_series_input = QLineEdit()
        self.passport_number_input = QLineEdit()
        self.passport_issue_date_input = QDateEdit()
        self.passport_issue_date_input.setCalendarPopup(True)
        self.passport_issued_by_input = QLineEdit()
        
        # Военный билет
        self.military_id_series_input = QLineEdit()
        self.military_id_number_input = QLineEdit()
        self.military_id_issue_date_input = QDateEdit()
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
        scroll_area.setWidget(scroll_widget)
        
        main_data_layout.addWidget(scroll_area)
        
        # Кнопки сохранения и удаления
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_changes)
        
        delete_button = QPushButton("Удалить КРД")
        delete_button.setStyleSheet("background-color: #ff6b6b; color: white;")
        delete_button.clicked.connect(self.delete_krd)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(cancel_button)
        
        main_data_layout.addLayout(button_layout)
        
        tabs.addTab(main_data_widget, "Основные данные")
        
        # Вкладка с запросом в миграционную службу
        from migration_request_tab import MigrationRequestTab
        migration_tab = MigrationRequestTab(self.krd_id, self.db)
        tabs.addTab(migration_tab, "Запрос в миграцию")
        
        # Вкладка с документами и шаблонами
        from document_generator_tab import DocumentGeneratorTab
        documents_tab = DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger)
        tabs.addTab(documents_tab, "Формирование запросов")
        
        # Добавляем вкладки в основной макет
        main_layout.addWidget(tabs)
        
        self.setLayout(main_layout)
    
    def setup_data_mapping(self):
        """
        Настройка сопоставления данных между моделью и виджетами
        """
        # Устанавливаем значения из записи в виджеты
        self.surname_input.setText(self.record.value("surname"))
        self.name_input.setText(self.record.value("name"))
        self.patronymic_input.setText(self.record.value("patronymic"))
        
        # Устанавливаем дату рождения
        birth_date = self.record.value("birth_date")
        if birth_date:
            self.birth_date_input.setDate(birth_date)
        else:
            self.birth_date_input.setDate(QDate.currentDate())
        
        self.birth_place_town_input.setText(self.record.value("birth_place_town"))
        self.birth_place_district_input.setText(self.record.value("birth_place_district"))
        self.birth_place_region_input.setText(self.record.value("birth_place_region"))
        self.birth_place_country_input.setText(self.record.value("birth_place_country"))
        self.tab_number_input.setText(self.record.value("tab_number"))
        self.personal_number_input.setText(self.record.value("personal_number"))
        
        # Устанавливаем категорию
        category_id = self.record.value("category_id")
        if category_id:
            index = self.category_combo.findData(category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        
        # Устанавливаем звание
        rank_id = self.record.value("rank_id")
        if rank_id:
            index = self.rank_combo.findData(rank_id)
            if index >= 0:
                self.rank_combo.setCurrentIndex(index)
        
        self.drafted_by_commissariat_input.setText(self.record.value("drafted_by_commissariat"))
        
        # Устанавливаем дату призыва
        draft_date = self.record.value("draft_date")
        if draft_date:
            self.draft_date_input.setDate(draft_date)
        else:
            self.draft_date_input.setDate(QDate.currentDate())
        
        self.povsk_input.setText(self.record.value("povsk"))
        
        # Устанавливаем дату отбора
        selection_date = self.record.value("selection_date")
        if selection_date:
            self.selection_date_input.setDate(selection_date)
        else:
            self.selection_date_input.setDate(QDate.currentDate())
        
        self.education_input.setText(self.record.value("education"))
        self.criminal_record_input.setPlainText(self.record.value("criminal_record") or "")
        self.social_media_account_input.setText(self.record.value("social_media_account"))
        self.bank_card_number_input.setText(self.record.value("bank_card_number"))
        self.passport_series_input.setText(self.record.value("passport_series"))
        self.passport_number_input.setText(self.record.value("passport_number"))
        
        # Устанавливаем дату выдачи паспорта
        passport_issue_date = self.record.value("passport_issue_date")
        if passport_issue_date:
            self.passport_issue_date_input.setDate(passport_issue_date)
        else:
            self.passport_issue_date_input.setDate(QDate.currentDate())
        
        self.passport_issued_by_input.setText(self.record.value("passport_issued_by"))
        self.military_id_series_input.setText(self.record.value("military_id_series"))
        self.military_id_number_input.setText(self.record.value("military_id_number"))
        
        # Устанавливаем дату выдачи воен. билета
        military_id_issue_date = self.record.value("military_id_issue_date")
        if military_id_issue_date:
            self.military_id_issue_date_input.setDate(military_id_issue_date)
        else:
            self.military_id_issue_date_input.setDate(QDate.currentDate())
        
        self.military_id_issued_by_input.setText(self.record.value("military_id_issued_by"))
        self.appearance_features_input.setPlainText(self.record.value("appearance_features") or "")
        self.personal_marks_input.setPlainText(self.record.value("personal_marks") or "")
        self.federal_search_info_input.setPlainText(self.record.value("federal_search_info") or "")
        self.military_contacts_input.setText(self.record.value("military_contacts"))
        self.relatives_info_input.setPlainText(self.record.value("relatives_info") or "")
    
    def load_categories(self):
        """
        Загрузка категорий из базы данных
        """
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.categories ORDER BY name")
        
        # Добавляем пустой элемент для возможности сброса
        self.category_combo.addItem("", None)
        
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
        
        # Добавляем пустой элемент для возможности сброса
        self.rank_combo.addItem("", None)
        
        while query.next():
            rank_id = query.value(0)
            rank_name = query.value(1)
            self.rank_combo.addItem(rank_name, rank_id)
    
    def save_changes(self):
        """
        Сохранение изменений в базе данных с аудитом
        """
        try:
            # Получаем новые значения
            new_data = {
                'surname': self.surname_input.text().strip(),
                'name': self.name_input.text().strip(),
                'patronymic': self.patronymic_input.text().strip(),
                'birth_date': self.birth_date_input.date().toString("yyyy-MM-dd"),
                'birth_place_town': self.birth_place_town_input.text().strip(),
                'birth_place_district': self.birth_place_district_input.text().strip(),
                'birth_place_region': self.birth_place_region_input.text().strip(),
                'birth_place_country': self.birth_place_country_input.text().strip(),
                'tab_number': self.tab_number_input.text().strip(),
                'personal_number': self.personal_number_input.text().strip(),
                'category_id': self.category_combo.currentData(),
                'rank_id': self.rank_combo.currentData(),
                'drafted_by_commissariat': self.drafted_by_commissariat_input.text().strip(),
                'draft_date': self.draft_date_input.date().toString("yyyy-MM-dd"),
                'povsk': self.povsk_input.text().strip(),
                'selection_date': self.selection_date_input.date().toString("yyyy-MM-dd"),
                'education': self.education_input.text().strip(),
                'criminal_record': self.criminal_record_input.toPlainText(),
                'social_media_account': self.social_media_account_input.text().strip(),
                'bank_card_number': self.bank_card_number_input.text().strip(),
                'passport_series': self.passport_series_input.text().strip(),
                'passport_number': self.passport_number_input.text().strip(),
                'passport_issue_date': self.passport_issue_date_input.date().toString("yyyy-MM-dd"),
                'passport_issued_by': self.passport_issued_by_input.text().strip(),
                'military_id_series': self.military_id_series_input.text().strip(),
                'military_id_number': self.military_id_number_input.text().strip(),
                'military_id_issue_date': self.military_id_issue_date_input.date().toString("yyyy-MM-dd"),
                'military_id_issued_by': self.military_id_issued_by_input.text().strip(),
                'appearance_features': self.appearance_features_input.toPlainText(),
                'personal_marks': self.personal_marks_input.toPlainText(),
                'federal_search_info': self.federal_search_info_input.toPlainText(),
                'military_contacts': self.military_contacts_input.text().strip(),
                'relatives_info': self.relatives_info_input.toPlainText()
            }
            
            # Обновляем запись
            self.record.setValue("surname", new_data['surname'])
            self.record.setValue("name", new_data['name'])
            self.record.setValue("patronymic", new_data['patronymic'])
            self.record.setValue("birth_date", self.birth_date_input.date())
            self.record.setValue("birth_place_town", new_data['birth_place_town'])
            self.record.setValue("birth_place_district", new_data['birth_place_district'])
            self.record.setValue("birth_place_region", new_data['birth_place_region'])
            self.record.setValue("birth_place_country", new_data['birth_place_country'])
            self.record.setValue("tab_number", new_data['tab_number'])
            self.record.setValue("personal_number", new_data['personal_number'])
            
            # Получаем ID выбранной категории и звания
            category_id = self.category_combo.currentData()
            rank_id = self.rank_combo.currentData()
            
            self.record.setValue("category_id", category_id if category_id is not None else None)
            self.record.setValue("rank_id", rank_id if rank_id is not None else None)
            
            self.record.setValue("drafted_by_commissariat", new_data['drafted_by_commissariat'])
            self.record.setValue("draft_date", self.draft_date_input.date())
            self.record.setValue("povsk", new_data['povsk'])
            self.record.setValue("selection_date", self.selection_date_input.date())
            self.record.setValue("education", new_data['education'])
            self.record.setValue("criminal_record", new_data['criminal_record'])
            self.record.setValue("social_media_account", new_data['social_media_account'])
            self.record.setValue("bank_card_number", new_data['bank_card_number'])
            self.record.setValue("passport_series", new_data['passport_series'])
            self.record.setValue("passport_number", new_data['passport_number'])
            self.record.setValue("passport_issue_date", self.passport_issue_date_input.date())
            self.record.setValue("passport_issued_by", new_data['passport_issued_by'])
            self.record.setValue("military_id_series", new_data['military_id_series'])
            self.record.setValue("military_id_number", new_data['military_id_number'])
            self.record.setValue("military_id_issue_date", self.military_id_issue_date_input.date())
            self.record.setValue("military_id_issued_by", new_data['military_id_issued_by'])
            self.record.setValue("appearance_features", new_data['appearance_features'])
            self.record.setValue("personal_marks", new_data['personal_marks'])
            self.record.setValue("federal_search_info", new_data['federal_search_info'])
            self.record.setValue("military_contacts", new_data['military_contacts'])
            self.record.setValue("relatives_info", new_data['relatives_info'])
            
            # Обновляем запись в модели
            if not self.model.setRecord(0, self.record):
                raise Exception(f"Ошибка при обновлении записи: {self.model.lastError().text()}")
            
            # Подтверждаем изменения в базе данных
            if not self.model.submitAll():
                raise Exception(f"Ошибка при сохранении изменений: {self.model.lastError().text()}")
            
            # Логирование обновления
            if self.audit_logger:
                self.audit_logger.log_krd_update(self.krd_id, self.old_data, new_data)
            
            QMessageBox.information(self, "Успех", "Данные успешно сохранены")
            
            # Обновляем старые данные
            self.old_data = new_data
            
            # Закрываем окно
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении данных:\n{str(e)}")
    
    def delete_krd(self):
        """
        Удаление КРД с подтверждением и аудитом
        """
        try:
            # Получаем фамилию и имя для информативного сообщения
            surname = self.surname_input.text().strip() or "Неизвестно"
            name = self.name_input.text().strip() or ""
            patronymic = self.patronymic_input.text().strip() or ""
            
            full_name = f"{surname} {name} {patronymic}".strip()
            
            # Показываем диалог подтверждения
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Вы действительно хотите удалить КРД №{self.krd_id}?\n\n"
                f"Военнослужащий: {full_name}\n\n"
                f"⚠️ Внимание: Запись будет скрыта из списка, но сохранена в базе данных.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            # Если пользователь подтвердил удаление
            if reply == QMessageBox.StandardButton.Yes:
                # Получаем данные для логирования
                old_data = self._get_current_data()
                
                # Обновляем запись, помечая её как удаленную
                query = QSqlQuery(self.db)
                query.prepare("""
                    UPDATE krd.krd 
                    SET is_deleted = TRUE, 
                        deleted_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """)
                query.addBindValue(self.krd_id)
                
                if not query.exec():
                    raise Exception(f"Ошибка при удалении КРД: {query.lastError().text()}")
                
                # Логирование удаления
                if self.audit_logger:
                    self.audit_logger.log_krd_delete(self.krd_id, old_data)
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"КРД №{self.krd_id} успешно скрыт из списка!\n"
                    f"Запись сохранена в базе данных для истории."
                )
                
                # Закрываем окно
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Ошибка при удалении КРД:\n{str(e)}"
            )
    
    def reject(self):
        """
        Отмена изменений
        """
        # Откатываем изменения в модели
        self.model.revertAll()
        super().reject()