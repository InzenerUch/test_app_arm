"""
Вкладка адресов проживания
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout,
    QLineEdit, QDateEdit, QTextEdit, QLabel, QPushButton,QTableView
)
from PyQt6.QtCore import QDate
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont


class AddressesTab(QWidget):
    """Вкладка адресов проживания"""
    
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
        
        # Таблица адресов
        self.addresses_model = QSqlQueryModel()
        self.addresses_table = QTableView()
        self.addresses_table.setModel(self.addresses_model)
        self.addresses_table.setAlternatingRowColors(True)
        
        # Настройка заголовков
        header = self.addresses_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(QLabel("Список адресов проживания:"))
        layout.addWidget(self.addresses_table)
        
        # Форма добавления адреса
        form_group = QGroupBox("Добавить новый адрес")
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("Субъект РФ:"), 0, 0)
        self.region_input = QLineEdit()
        form_layout.addWidget(self.region_input, 0, 1)
        
        form_layout.addWidget(QLabel("Административный район:"), 0, 2)
        self.district_input = QLineEdit()
        form_layout.addWidget(self.district_input, 0, 3)
        
        form_layout.addWidget(QLabel("Населенный пункт:"), 1, 0)
        self.town_input = QLineEdit()
        form_layout.addWidget(self.town_input, 1, 1)
        
        form_layout.addWidget(QLabel("Улица:"), 1, 2)
        self.street_input = QLineEdit()
        form_layout.addWidget(self.street_input, 1, 3)
        
        form_layout.addWidget(QLabel("Дом:"), 2, 0)
        self.house_input = QLineEdit()
        form_layout.addWidget(self.house_input, 2, 1)
        
        form_layout.addWidget(QLabel("Корпус:"), 2, 2)
        self.building_input = QLineEdit()
        form_layout.addWidget(self.building_input, 2, 3)
        
        form_layout.addWidget(QLabel("Литер:"), 3, 0)
        self.letter_input = QLineEdit()
        form_layout.addWidget(self.letter_input, 3, 1)
        
        form_layout.addWidget(QLabel("Квартира:"), 3, 2)
        self.apartment_input = QLineEdit()
        form_layout.addWidget(self.apartment_input, 3, 3)
        
        form_layout.addWidget(QLabel("Комната:"), 4, 0)
        self.room_input = QLineEdit()
        form_layout.addWidget(self.room_input, 4, 1)
        
        form_layout.addWidget(QLabel("Дата проверки:"), 5, 0)
        self.check_date_input = QDateEdit()
        self.check_date_input.setCalendarPopup(True)
        self.check_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.check_date_input, 5, 1)
        
        form_layout.addWidget(QLabel("Результат проверки:"), 6, 0)
        self.check_result_input = QTextEdit()
        self.check_result_input.setMaximumHeight(60)
        form_layout.addWidget(self.check_result_input, 6, 1, 1, 3)
        
        add_btn = QPushButton("Добавить адрес")
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        add_btn.clicked.connect(self.add_address)
        form_layout.addWidget(add_btn, 7, 0, 1, 4)
        
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
                region as "Субъект РФ",
                district as "Район",
                town as "Населенный пункт",
                street as "Улица",
                house as "Дом",
                building as "Корпус",
                letter as "Литер",
                apartment as "Квартира",
                room as "Комната",
                check_date as "Дата проверки",
                check_result as "Результат"
            FROM krd.addresses
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        self.addresses_model.setQuery(query)
    
    def add_address(self):
        """Добавление нового адреса"""
        # Валидация
        if not self.town_input.text().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Ошибка", "Поле 'Населенный пункт' обязательно для заполнения")
            return
        
        # Подготовка данных
        data = {
            "krd_id": self.krd_id,
            "region": self.region_input.text().strip(),
            "district": self.district_input.text().strip(),
            "town": self.town_input.text().strip(),
            "street": self.street_input.text().strip(),
            "house": self.house_input.text().strip(),
            "building": self.building_input.text().strip(),
            "letter": self.letter_input.text().strip(),
            "apartment": self.apartment_input.text().strip(),
            "room": self.room_input.text().strip(),
            "check_date": self.check_date_input.date(),
            "check_result": self.check_result_input.toPlainText()
        }
        
        # Сохранение в базу
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.addresses (
                krd_id, region, district, town, street, house, building,
                letter, apartment, room, check_date, check_result
            ) VALUES (
                :krd_id, :region, :district, :town, :street, :house, :building,
                :letter, :apartment, :room, :check_date, :check_result
            )
        """)
        
        for key, value in data.items():
            query.bindValue(f":{key}", value)
        
        if query.exec():
            # Очистка формы
            self.region_input.clear()
            self.district_input.clear()
            self.town_input.clear()
            self.street_input.clear()
            self.house_input.clear()
            self.building_input.clear()
            self.letter_input.clear()
            self.apartment_input.clear()
            self.room_input.clear()
            self.check_result_input.clear()
            
            # Обновление таблицы
            self.load_data()
            
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Успех", "Адрес успешно добавлен")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления адреса:\n{query.lastError().text()}")