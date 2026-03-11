"""
Вкладка входящих поручений на розыск
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout,
    QLineEdit, QDateEdit, QTextEdit, QLabel, QPushButton, QComboBox,
    QTableView, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont


class IncomingOrdersTab(QWidget):
    """Вкладка входящих поручений на розыск"""
    
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
        
        # Таблица входящих поручений
        self.orders_model = QSqlQueryModel()
        self.orders_table = QTableView()
        self.orders_table.setModel(self.orders_model)
        self.orders_table.setAlternatingRowColors(True)
        
        header = self.orders_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(QLabel("Список входящих поручений:"))
        layout.addWidget(self.orders_table)
        
        # Форма добавления поручения
        form_group = QGroupBox("Добавить новое входящее поручение")
        form_layout = QGridLayout()
        
        # Инициатор розыска
        form_layout.addWidget(QLabel("Инициатор розыска *:"), 0, 0)
        self.initiator_type_combo = QComboBox()
        self.load_initiator_types()
        form_layout.addWidget(self.initiator_type_combo, 0, 1)
        
        form_layout.addWidget(QLabel("Полное наименование инициатора *:"), 0, 2)
        self.initiator_full_name_input = QLineEdit()
        form_layout.addWidget(self.initiator_full_name_input, 0, 3, 1, 3)
        
        form_layout.addWidget(QLabel("Военное управление инициатора *:"), 1, 0)
        self.initiator_military_unit_combo = QComboBox()
        self.load_military_units()
        form_layout.addWidget(self.initiator_military_unit_combo, 1, 1)
        
        form_layout.addWidget(QLabel("Исходящая дата поручения *:"), 2, 0)
        self.order_date_input = QDateEdit()
        self.order_date_input.setCalendarPopup(True)
        self.order_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.order_date_input, 2, 1)
        
        form_layout.addWidget(QLabel("Исходящий номер поручения *:"), 2, 2)
        self.order_number_input = QLineEdit()
        form_layout.addWidget(self.order_number_input, 2, 3)
        
        form_layout.addWidget(QLabel("Дата поступления в ВК *:"), 3, 0)
        self.receipt_date_input = QDateEdit()
        self.receipt_date_input.setCalendarPopup(True)
        self.receipt_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.receipt_date_input, 3, 1)
        
        form_layout.addWidget(QLabel("Входящий номер в ВК *:"), 3, 2)
        self.receipt_number_input = QLineEdit()
        form_layout.addWidget(self.receipt_number_input, 3, 3)
        
        # Почтовый адрес инициатора
        form_layout.addWidget(QLabel("Почтовый адрес инициатора:"), 4, 0, 1, 6)
        
        form_layout.addWidget(QLabel("Индекс:"), 5, 0)
        self.postal_index_input = QLineEdit()
        form_layout.addWidget(self.postal_index_input, 5, 1)
        
        form_layout.addWidget(QLabel("Субъект РФ:"), 5, 2)
        self.postal_region_input = QLineEdit()
        form_layout.addWidget(self.postal_region_input, 5, 3)
        
        form_layout.addWidget(QLabel("Административный район:"), 6, 0)
        self.postal_district_input = QLineEdit()
        form_layout.addWidget(self.postal_district_input, 6, 1)
        
        form_layout.addWidget(QLabel("Населенный пункт:"), 6, 2)
        self.postal_town_input = QLineEdit()
        form_layout.addWidget(self.postal_town_input, 6, 3)
        
        form_layout.addWidget(QLabel("Улица:"), 7, 0)
        self.postal_street_input = QLineEdit()
        form_layout.addWidget(self.postal_street_input, 7, 1)
        
        form_layout.addWidget(QLabel("Дом:"), 7, 2)
        self.postal_house_input = QLineEdit()
        form_layout.addWidget(self.postal_house_input, 7, 3)
        
        form_layout.addWidget(QLabel("Корпус:"), 8, 0)
        self.postal_building_input = QLineEdit()
        form_layout.addWidget(self.postal_building_input, 8, 1)
        
        form_layout.addWidget(QLabel("Литер:"), 8, 2)
        self.postal_letter_input = QLineEdit()
        form_layout.addWidget(self.postal_letter_input, 8, 3)
        
        form_layout.addWidget(QLabel("Квартира:"), 9, 0)
        self.postal_apartment_input = QLineEdit()
        form_layout.addWidget(self.postal_apartment_input, 9, 1)
        
        form_layout.addWidget(QLabel("Комната:"), 9, 2)
        self.postal_room_input = QLineEdit()
        form_layout.addWidget(self.postal_room_input, 9, 3)
        
        form_layout.addWidget(QLabel("Контакты источника:"), 10, 0)
        self.initiator_contacts_input = QLineEdit()
        form_layout.addWidget(self.initiator_contacts_input, 10, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Дата нашего ответа:"), 11, 0)
        self.our_response_date_input = QDateEdit()
        self.our_response_date_input.setCalendarPopup(True)
        self.our_response_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.our_response_date_input, 11, 1)
        
        form_layout.addWidget(QLabel("Исходящий номер нашего ответа:"), 11, 2)
        self.our_response_number_input = QLineEdit()
        form_layout.addWidget(self.our_response_number_input, 11, 3)
        
        add_btn = QPushButton("Добавить поручение")
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        add_btn.clicked.connect(self.add_order)
        form_layout.addWidget(add_btn, 12, 0, 1, 6)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def load_initiator_types(self):
        """Загрузка типов инициаторов"""
        self.initiator_type_combo.clear()
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.initiator_types ORDER BY name")
        
        while query.next():
            type_id = query.value(0)
            type_name = query.value(1)
            self.initiator_type_combo.addItem(type_name, type_id)
    
    def load_military_units(self):
        """Загрузка военных управлений"""
        self.initiator_military_unit_combo.clear()
        self.initiator_military_unit_combo.addItem("", None)
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.military_units ORDER BY name")
        
        while query.next():
            unit_id = query.value(0)
            unit_name = query.value(1)
            self.initiator_military_unit_combo.addItem(unit_name, unit_id)
    
    def load_data(self):
        """Загрузка данных из базы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                id,
                initiator_full_name as "Инициатор",
                order_date as "Дата поручения",
                order_number as "Номер поручения",
                receipt_date as "Дата поступления",
                receipt_number as "Входящий номер"
            FROM krd.incoming_orders
            WHERE krd_id = ?
            ORDER BY receipt_date DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        self.orders_model.setQuery(query)
    
    def add_order(self):
        """Добавление нового поручения"""
        # Валидация
        if not self.initiator_full_name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Полное наименование инициатора' обязательно для заполнения")
            return
        
        if not self.order_number_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Исходящий номер поручения' обязательно для заполнения")
            return
        
        # Подготовка данных
        data = {
            "krd_id": self.krd_id,
            "initiator_type_id": self.initiator_type_combo.currentData(),
            "initiator_full_name": self.initiator_full_name_input.text().strip(),
            "military_unit_id": self.initiator_military_unit_combo.currentData(),
            "order_date": self.order_date_input.date(),
            "order_number": self.order_number_input.text().strip(),
            "receipt_date": self.receipt_date_input.date(),
            "receipt_number": self.receipt_number_input.text().strip(),
            "postal_index": self.postal_index_input.text().strip(),
            "postal_region": self.postal_region_input.text().strip(),
            "postal_district": self.postal_district_input.text().strip(),
            "postal_town": self.postal_town_input.text().strip(),
            "postal_street": self.postal_street_input.text().strip(),
            "postal_house": self.postal_house_input.text().strip(),
            "postal_building": self.postal_building_input.text().strip(),
            "postal_letter": self.postal_letter_input.text().strip(),
            "postal_apartment": self.postal_apartment_input.text().strip(),
            "postal_room": self.postal_room_input.text().strip(),
            "initiator_contacts": self.initiator_contacts_input.text().strip(),
            "our_response_date": self.our_response_date_input.date(),
            "our_response_number": self.our_response_number_input.text().strip()
        }
        
        # Сохранение в базу
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.incoming_orders (
                krd_id, initiator_type_id, initiator_full_name, military_unit_id,
                order_date, order_number, receipt_date, receipt_number,
                postal_index, postal_region, postal_district, postal_town,
                postal_street, postal_house, postal_building, postal_letter,
                postal_apartment, postal_room, initiator_contacts,
                our_response_date, our_response_number
            ) VALUES (
                :krd_id, :initiator_type_id, :initiator_full_name, :military_unit_id,
                :order_date, :order_number, :receipt_date, :receipt_number,
                :postal_index, :postal_region, :postal_district, :postal_town,
                :postal_street, :postal_house, :postal_building, :postal_letter,
                :postal_apartment, :postal_room, :initiator_contacts,
                :our_response_date, :our_response_number
            )
        """)
        
        for key, value in data.items():
            query.bindValue(f":{key}", value)
        
        if query.exec():
            # Очистка формы
            self.initiator_full_name_input.clear()
            self.order_number_input.clear()
            self.postal_index_input.clear()
            self.postal_region_input.clear()
            self.postal_district_input.clear()
            self.postal_town_input.clear()
            self.postal_street_input.clear()
            self.postal_house_input.clear()
            self.postal_building_input.clear()
            self.postal_letter_input.clear()
            self.postal_apartment_input.clear()
            self.postal_room_input.clear()
            self.initiator_contacts_input.clear()
            self.our_response_number_input.clear()
            
            # Обновление таблицы
            self.load_data()
            
            QMessageBox.information(self, "Успех", "Поручение успешно добавлено")
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления поручения:\n{query.lastError().text()}")