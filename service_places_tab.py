"""
Вкладка мест службы
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QLabel, QPushButton, QComboBox,
    QTableView, QMessageBox
)
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel


class ServicePlacesTab(QWidget):
    """Вкладка мест службы"""
    
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
        
        # Таблица мест службы
        self.places_model = QSqlQueryModel()
        self.places_table = QTableView()
        self.places_table.setModel(self.places_model)
        self.places_table.setAlternatingRowColors(True)
        
        header = self.places_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(QLabel("Список мест службы:"))
        layout.addWidget(self.places_table)
        
        # Форма добавления места службы
        form_group = QGroupBox("Добавить новое место службы")
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("Наименование места службы *:"), 0, 0)
        self.place_name_input = QLineEdit()
        form_layout.addWidget(self.place_name_input, 0, 1, 1, 3)
        
        form_layout.addWidget(QLabel("Военное управление:"), 1, 0)
        self.military_unit_combo = QComboBox()
        self.load_military_units()
        form_layout.addWidget(self.military_unit_combo, 1, 1)
        
        form_layout.addWidget(QLabel("Гарнизон:"), 1, 2)
        self.garrison_combo = QComboBox()
        self.load_garrisons()
        form_layout.addWidget(self.garrison_combo, 1, 3)
        
        form_layout.addWidget(QLabel("Воинская должность:"), 2, 0)
        self.position_combo = QComboBox()
        self.load_positions()
        form_layout.addWidget(self.position_combo, 2, 1)
        
        form_layout.addWidget(QLabel("Командиры (звание, ФИО, контакты):"), 3, 0)
        self.commanders_input = QTextEdit()
        self.commanders_input.setMaximumHeight(80)
        form_layout.addWidget(self.commanders_input, 3, 1, 1, 3)
        
        # Почтовый адрес места службы
        form_layout.addWidget(QLabel("Почтовый адрес места службы:"), 4, 0, 1, 4)
        
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
        
        form_layout.addWidget(QLabel("Контакты места службы:"), 10, 0)
        self.place_contacts_input = QLineEdit()
        form_layout.addWidget(self.place_contacts_input, 10, 1, 1, 3)
        
        add_btn = QPushButton("Добавить место службы")
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        add_btn.clicked.connect(self.add_service_place)
        form_layout.addWidget(add_btn, 11, 0, 1, 4)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        layout.addStretch()
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def load_military_units(self):
        """Загрузка военных управлений"""
        self.military_unit_combo.clear()
        self.military_unit_combo.addItem("", None)
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.military_units ORDER BY name")
        
        while query.next():
            unit_id = query.value(0)
            unit_name = query.value(1)
            self.military_unit_combo.addItem(unit_name, unit_id)
    
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
        """Загрузка данных из базы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                id,
                place_name as "Место службы",
                military_unit_id as "Военное управление",
                garrison_id as "Гарнизон",
                position_id as "Должность"
            FROM krd.service_places
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        self.places_model.setQuery(query)
    
    def add_service_place(self):
        """Добавление нового места службы"""
        # Валидация
        if not self.place_name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Поле 'Наименование места службы' обязательно для заполнения")
            return
        
        # Подготовка данных
        data = {
            "krd_id": self.krd_id,
            "place_name": self.place_name_input.text().strip(),
            "military_unit_id": self.military_unit_combo.currentData(),
            "garrison_id": self.garrison_combo.currentData(),
            "position_id": self.position_combo.currentData(),
            "commanders": self.commanders_input.toPlainText(),
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
            "place_contacts": self.place_contacts_input.text().strip()
        }
        
        # Сохранение в базу
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.service_places (
                krd_id, place_name, military_unit_id, garrison_id, position_id,
                commanders, postal_index, postal_region, postal_district, postal_town,
                postal_street, postal_house, postal_building, postal_letter,
                postal_apartment, postal_room, place_contacts
            ) VALUES (
                :krd_id, :place_name, :military_unit_id, :garrison_id, :position_id,
                :commanders, :postal_index, :postal_region, :postal_district, :postal_town,
                :postal_street, :postal_house, :postal_building, :postal_letter,
                :postal_apartment, :postal_room, :place_contacts
            )
        """)
        
        for key, value in data.items():
            query.bindValue(f":{key}", value)
        
        if query.exec():
            # Очистка формы
            self.place_name_input.clear()
            self.commanders_input.clear()
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
            self.place_contacts_input.clear()
            
            # Обновление таблицы
            self.load_data()
            
            QMessageBox.information(self, "Успех", "Место службы успешно добавлено")
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления места службы:\n{query.lastError().text()}")