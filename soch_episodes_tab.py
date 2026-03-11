"""
Вкладка сведений о самовольном оставлении части (СОЧ)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QDateEdit, QLabel, QPushButton,
    QTableView, QMessageBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel


class SochEpisodesTab(QWidget):
    """Вкладка сведений о СОЧ"""
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Таблица эпизодов СОЧ
        self.episodes_model = QSqlQueryModel()
        self.episodes_table = QTableView()
        self.episodes_table.setModel(self.episodes_model)
        self.episodes_table.setAlternatingRowColors(True)
        
        header = self.episodes_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(QLabel("Список эпизодов СОЧ:"))
        layout.addWidget(self.episodes_table)
        
        # Форма добавления эпизода СОЧ
        form_group = QGroupBox("Добавить новый эпизод СОЧ")
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("Дата СОЧ:"), 0, 0)
        self.soch_date_input = QDateEdit()
        self.soch_date_input.setCalendarPopup(True)
        self.soch_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.soch_date_input, 0, 1)
        
        form_layout.addWidget(QLabel("Место СОЧ:"), 0, 2)
        self.soch_location_input = QLineEdit()
        form_layout.addWidget(self.soch_location_input, 0, 3)
        
        form_layout.addWidget(QLabel("Дата и номер приказа о СОЧ:"), 1, 0)
        self.order_date_number_input = QLineEdit()
        form_layout.addWidget(self.order_date_number_input, 1, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Очевидцы СОЧ:"), 2, 0)
        self.witnesses_input = QTextEdit()
        self.witnesses_input.setMaximumHeight(60)
        form_layout.addWidget(self.witnesses_input, 2, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Вероятные причины СОЧ:"), 3, 0)
        self.reasons_input = QTextEdit()
        self.reasons_input.setMaximumHeight(60)
        form_layout.addWidget(self.reasons_input, 3, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Сведения о наличии оружия:"), 4, 0)
        self.weapon_info_input = QTextEdit()
        self.weapon_info_input.setMaximumHeight(60)
        form_layout.addWidget(self.weapon_info_input, 4, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Во что был одет:"), 5, 0)
        self.clothing_input = QTextEdit()
        self.clothing_input.setMaximumHeight(60)
        form_layout.addWidget(self.clothing_input, 5, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Варианты движения:"), 6, 0)
        self.movement_options_input = QTextEdit()
        self.movement_options_input.setMaximumHeight(60)
        form_layout.addWidget(self.movement_options_input, 6, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Другая значимая информация:"), 7, 0)
        self.other_info_input = QTextEdit()
        self.other_info_input.setMaximumHeight(60)
        form_layout.addWidget(self.other_info_input, 7, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Контакт дежурного по ВК:"), 8, 0)
        self.duty_officer_commissariat_input = QLineEdit()
        form_layout.addWidget(self.duty_officer_commissariat_input, 8, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Контакт дежурного по ОМВД:"), 9, 0)
        self.duty_officer_omvd_input = QLineEdit()
        form_layout.addWidget(self.duty_officer_omvd_input, 9, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Сведения о проверке:"), 10, 0)
        self.investigation_info_input = QTextEdit()
        self.investigation_info_input.setMaximumHeight(60)
        form_layout.addWidget(self.investigation_info_input, 10, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Сведения о прокуратуре:"), 11, 0)
        self.prosecution_info_input = QTextEdit()
        self.prosecution_info_input.setMaximumHeight(60)
        form_layout.addWidget(self.prosecution_info_input, 11, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Сведения об уголовном деле:"), 12, 0)
        self.criminal_case_info_input = QTextEdit()
        self.criminal_case_info_input.setMaximumHeight(60)
        form_layout.addWidget(self.criminal_case_info_input, 12, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Сведения о федеральном розыске:"), 13, 0)
        self.federal_search_input = QTextEdit()
        self.federal_search_input.setMaximumHeight(60)
        form_layout.addWidget(self.federal_search_input, 13, 1, 1, 3)
        
        # Данные о розыске
        form_layout.addWidget(QLabel("Дата розыска:"), 14, 0)
        self.search_date_input = QDateEdit()
        self.search_date_input.setCalendarPopup(True)
        self.search_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.search_date_input, 14, 1)
        
        form_layout.addWidget(QLabel("Кем разыскан:"), 14, 2)
        self.found_by_input = QLineEdit()
        form_layout.addWidget(self.found_by_input, 14, 3)
        
        form_layout.addWidget(QLabel("Обстоятельства розыска:"), 15, 0)
        self.search_circumstances_input = QTextEdit()
        self.search_circumstances_input.setMaximumHeight(60)
        form_layout.addWidget(self.search_circumstances_input, 15, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Адресат уведомления:"), 16, 0)
        self.notification_recipient_input = QLineEdit()
        form_layout.addWidget(self.notification_recipient_input, 16, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Дата уведомления:"), 17, 0)
        self.notification_date_input = QDateEdit()
        self.notification_date_input.setCalendarPopup(True)
        self.notification_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.notification_date_input, 17, 1)
        
        form_layout.addWidget(QLabel("Номер уведомления:"), 17, 2)
        self.notification_number_input = QLineEdit()
        form_layout.addWidget(self.notification_number_input, 17, 3)
        
        add_btn = QPushButton("Добавить эпизод СОЧ")
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        add_btn.clicked.connect(self.add_episode)
        form_layout.addWidget(add_btn, 18, 0, 1, 4)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def load_data(self):
        """Загрузка данных из базы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                id,
                soch_date as "Дата СОЧ",
                soch_location as "Место СОЧ",
                search_date as "Дата розыска",
                found_by as "Кем разыскан"
            FROM krd.soch_episodes
            WHERE krd_id = ?
            ORDER BY soch_date DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        self.episodes_model.setQuery(query)
    
    def add_episode(self):
        """Добавление нового эпизода СОЧ"""
        # Подготовка данных
        data = {
            "krd_id": self.krd_id,
            "soch_date": self.soch_date_input.date(),
            "soch_location": self.soch_location_input.text().strip(),
            "order_date_number": self.order_date_number_input.text().strip(),
            "witnesses": self.witnesses_input.toPlainText(),
            "reasons": self.reasons_input.toPlainText(),
            "weapon_info": self.weapon_info_input.toPlainText(),
            "clothing": self.clothing_input.toPlainText(),
            "movement_options": self.movement_options_input.toPlainText(),
            "other_info": self.other_info_input.toPlainText(),
            "duty_officer_commissariat": self.duty_officer_commissariat_input.text().strip(),
            "duty_officer_omvd": self.duty_officer_omvd_input.text().strip(),
            "investigation_info": self.investigation_info_input.toPlainText(),
            "prosecution_info": self.prosecution_info_input.toPlainText(),
            "criminal_case_info": self.criminal_case_info_input.toPlainText(),
            "federal_search_info": self.federal_search_input.toPlainText(),
            "search_date": self.search_date_input.date(),
            "found_by": self.found_by_input.text().strip(),
            "search_circumstances": self.search_circumstances_input.toPlainText(),
            "notification_recipient": self.notification_recipient_input.text().strip(),
            "notification_date": self.notification_date_input.date(),
            "notification_number": self.notification_number_input.text().strip()
        }
        
        # Сохранение в базу
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.soch_episodes (
                krd_id, soch_date, soch_location, order_date_number, witnesses,
                reasons, weapon_info, clothing, movement_options, other_info,
                duty_officer_commissariat, duty_officer_omvd, investigation_info,
                prosecution_info, criminal_case_info, federal_search_info,
                search_date, found_by, search_circumstances, notification_recipient,
                notification_date, notification_number
            ) VALUES (
                :krd_id, :soch_date, :soch_location, :order_date_number, :witnesses,
                :reasons, :weapon_info, :clothing, :movement_options, :other_info,
                :duty_officer_commissariat, :duty_officer_omvd, :investigation_info,
                :prosecution_info, :criminal_case_info, :federal_search_info,
                :search_date, :found_by, :search_circumstances, :notification_recipient,
                :notification_date, :notification_number
            )
        """)
        
        for key, value in data.items():
            query.bindValue(f":{key}", value)
        
        if query.exec():
            # Очистка формы
            self.soch_location_input.clear()
            self.order_date_number_input.clear()
            self.witnesses_input.clear()
            self.reasons_input.clear()
            self.weapon_info_input.clear()
            self.clothing_input.clear()
            self.movement_options_input.clear()
            self.other_info_input.clear()
            self.duty_officer_commissariat_input.clear()
            self.duty_officer_omvd_input.clear()
            self.investigation_info_input.clear()
            self.prosecution_info_input.clear()
            self.criminal_case_info_input.clear()
            self.federal_search_input.clear()
            self.found_by_input.clear()
            self.search_circumstances_input.clear()
            self.notification_recipient_input.clear()
            self.notification_number_input.clear()
            
            # Обновление таблицы
            self.load_data()
            
            QMessageBox.information(self, "Успех", "Эпизод СОЧ успешно добавлен")
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления эпизода СОЧ:\n{query.lastError().text()}")