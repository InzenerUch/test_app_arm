"""
Диалоговое окно для добавления/редактирования входящего поручения
С поддержкой автодополнения
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QGridLayout,
    QLineEdit, QDateEdit, QLabel, QPushButton, QComboBox,
    QMessageBox, QDialogButtonBox, QScrollArea, QWidget
)
from PyQt6.QtCore import QDate
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont

from autocomplete_helper import AutocompleteHelper


class IncomingOrderDialog(QDialog):
    """Диалог для добавления/редактирования входящего поручения"""
    
    def __init__(self, db_connection, krd_id, order_data=None, parent=None):
        """
        Args:
            db_connection: соединение с БД
            krd_id: ID карточки розыска
            order_ данные поручения для редактирования (None для нового)
            parent: родительское окно
        """
        super().__init__(parent)
        self.db = db_connection
        self.krd_id = krd_id
        self.order_data = order_data
        self.is_edit = order_data is not None
        self.order_id = order_data.get('id') if order_data else None
        
        # === ИНИЦИАЛИЗАЦИЯ ПОМОЩНИКА АВТОДОПОЛНЕНИЯ ===
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        
        self.setWindowTitle("✏️ Редактирование поручения" if self.is_edit else "➕ Добавление поручения")
        self.setMinimumSize(900, 750)
        self.setModal(True)
        
        self.init_ui()
        self.load_data()
        
        # === НАСТРОЙКА АВТОДОПОЛНЕНИЯ ПОСЛЕ ЗАГРУЗКИ ДАННЫХ ===
        self.setup_autocomplete_fields()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("✏️ Редактирование поручения" if self.is_edit else "➕ Добавление поручения")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Область прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        form_layout = QVBoxLayout(container)
        form_layout.setSpacing(10)
        
        # === Группа 1: Инициатор поручения ===
        group1 = QGroupBox("📬 Инициатор поручения")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group1_layout = QGridLayout()
        group1_layout.setSpacing(8)
        
        group1_layout.addWidget(QLabel("Тип инициатора *:"), 0, 0)
        self.initiator_type_combo = QComboBox()
        self.load_initiator_types()
        group1_layout.addWidget(self.initiator_type_combo, 0, 1)
        
        group1_layout.addWidget(QLabel("Полное наименование инициатора *:"), 0, 2)
        self.initiator_full_name_input = QLineEdit()
        self.initiator_full_name_input.setPlaceholderText("Например: Военная прокуратура гарнизона")
        group1_layout.addWidget(self.initiator_full_name_input, 0, 3, 1, 3)
        
        group1_layout.addWidget(QLabel("Военное управление инициатора *:"), 1, 0)
        self.initiator_military_unit_combo = QComboBox()
        self.load_military_units()
        group1_layout.addWidget(self.initiator_military_unit_combo, 1, 1)
        
        group1.setLayout(group1_layout)
        form_layout.addWidget(group1)
        
        # === Группа 2: Реквизиты поручения ===
        group2 = QGroupBox("📋 Реквизиты поручения")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group2_layout = QGridLayout()
        group2_layout.setSpacing(8)
        
        group2_layout.addWidget(QLabel("Исходящая дата поручения *:"), 0, 0)
        self.order_date_input = QDateEdit()
        self.order_date_input.setCalendarPopup(True)
        self.order_date_input.setDate(QDate.currentDate())
        group2_layout.addWidget(self.order_date_input, 0, 1)
        
        group2_layout.addWidget(QLabel("Исходящий номер поручения *:"), 0, 2)
        self.order_number_input = QLineEdit()
        self.order_number_input.setPlaceholderText("Например: №123")
        group2_layout.addWidget(self.order_number_input, 0, 3)
        
        group2_layout.addWidget(QLabel("Дата поступления в ВК *:"), 1, 0)
        self.receipt_date_input = QDateEdit()
        self.receipt_date_input.setCalendarPopup(True)
        self.receipt_date_input.setDate(QDate.currentDate())
        group2_layout.addWidget(self.receipt_date_input, 1, 1)
        
        group2_layout.addWidget(QLabel("Входящий номер в ВК *:"), 1, 2)
        self.receipt_number_input = QLineEdit()
        self.receipt_number_input.setPlaceholderText("Например: №456")
        group2_layout.addWidget(self.receipt_number_input, 1, 3)
        
        group2.setLayout(group2_layout)
        form_layout.addWidget(group2)
        
        # === Группа 3: Почтовый адрес инициатора ===
        group3 = QGroupBox("📍 Почтовый адрес инициатора")
        group3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group3_layout = QGridLayout()
        group3_layout.setSpacing(8)
        
        group3_layout.addWidget(QLabel("Индекс:"), 0, 0)
        self.postal_index_input = QLineEdit()
        self.postal_index_input.setPlaceholderText("Например: 660000")
        group3_layout.addWidget(self.postal_index_input, 0, 1)
        
        group3_layout.addWidget(QLabel("Субъект РФ:"), 0, 2)
        self.postal_region_input = QLineEdit()
        self.postal_region_input.setPlaceholderText("Например: Красноярский край")
        group3_layout.addWidget(self.postal_region_input, 0, 3)
        
        group3_layout.addWidget(QLabel("Административный район:"), 1, 0)
        self.postal_district_input = QLineEdit()
        group3_layout.addWidget(self.postal_district_input, 1, 1)
        
        group3_layout.addWidget(QLabel("Населенный пункт:"), 1, 2)
        self.postal_town_input = QLineEdit()
        group3_layout.addWidget(self.postal_town_input, 1, 3)
        
        group3_layout.addWidget(QLabel("Улица:"), 2, 0)
        self.postal_street_input = QLineEdit()
        group3_layout.addWidget(self.postal_street_input, 2, 1)
        
        group3_layout.addWidget(QLabel("Дом:"), 2, 2)
        self.postal_house_input = QLineEdit()
        group3_layout.addWidget(self.postal_house_input, 2, 3)
        
        group3_layout.addWidget(QLabel("Корпус:"), 3, 0)
        self.postal_building_input = QLineEdit()
        group3_layout.addWidget(self.postal_building_input, 3, 1)
        
        group3_layout.addWidget(QLabel("Литер:"), 3, 2)
        self.postal_letter_input = QLineEdit()
        group3_layout.addWidget(self.postal_letter_input, 3, 3)
        
        group3_layout.addWidget(QLabel("Квартира:"), 4, 0)
        self.postal_apartment_input = QLineEdit()
        group3_layout.addWidget(self.postal_apartment_input, 4, 1)
        
        group3_layout.addWidget(QLabel("Комната:"), 4, 2)
        self.postal_room_input = QLineEdit()
        group3_layout.addWidget(self.postal_room_input, 4, 3)
        
        group3.setLayout(group3_layout)
        form_layout.addWidget(group3)
        
        # === Группа 4: Контакты и ответ ===
        group4 = QGroupBox("📞 Контакты и ответ")
        group4.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group4_layout = QGridLayout()
        group4_layout.setSpacing(8)
        
        group4_layout.addWidget(QLabel("Контакты источника:"), 0, 0)
        self.initiator_contacts_input = QLineEdit()
        self.initiator_contacts_input.setPlaceholderText("Телефон, email")
        group4_layout.addWidget(self.initiator_contacts_input, 0, 1, 1, 3)
        
        group4_layout.addWidget(QLabel("Дата нашего ответа:"), 1, 0)
        self.our_response_date_input = QDateEdit()
        self.our_response_date_input.setCalendarPopup(True)
        self.our_response_date_input.setDate(QDate.currentDate())
        group4_layout.addWidget(self.our_response_date_input, 1, 1)
        
        group4_layout.addWidget(QLabel("Исходящий номер нашего ответа:"), 1, 2)
        self.our_response_number_input = QLineEdit()
        self.our_response_number_input.setPlaceholderText("Например: №789")
        group4_layout.addWidget(self.our_response_number_input, 1, 3)
        
        group4.setLayout(group4_layout)
        form_layout.addWidget(group4)
        
        container.setLayout(form_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        save_btn = button_box.button(QDialogButtonBox.StandardButton.Save)
        save_btn.setText("💾 Сохранить")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; min-width: 100px; padding: 8px;")
        
        cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("❌ Отмена")
        cancel_btn.setStyleSheet("min-width: 100px; padding: 8px;")
        
        layout.addWidget(button_box)
    
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
    
    def setup_autocomplete_fields(self):
        """Настройка автодополнения для почтовых полей"""
        
        fields_config = [
            (self.initiator_full_name_input, 'initiator_full_name', 30),
            (self.postal_region_input, 'postal_region', 20),
            (self.postal_district_input, 'postal_district', 20),
            (self.postal_town_input, 'postal_town', 20),
            (self.postal_street_input, 'postal_street', 30),
            (self.postal_house_input, 'postal_house', 15),
            (self.postal_building_input, 'postal_building', 15),
            (self.postal_letter_input, 'postal_letter', 10),
            (self.postal_apartment_input, 'postal_apartment', 15),
            (self.postal_room_input, 'postal_room', 15),
            (self.initiator_contacts_input, 'initiator_contacts', 20),
            (self.our_response_number_input, 'our_response_number', 15),
        ]
        
        for field_widget, column_name, max_items in fields_config:
            self.autocomplete_helper.setup_autocomplete(
                field_widget, 
                'incoming_orders', 
                column_name,
                max_items=max_items,
                show_on_focus=True
            )
        
        print(f"✅ Автодополнение настроено для {len(fields_config)} полей поручения")
    
    def load_data(self):
        """Загрузка данных поручения для редактирования"""
        if not self.order_data:
            return
        
        # Тип инициатора
        initiator_type_id = self.order_data.get('initiator_type_id')
        if initiator_type_id:
            index = self.initiator_type_combo.findData(initiator_type_id)
            if index >= 0:
                self.initiator_type_combo.setCurrentIndex(index)
        
        self.initiator_full_name_input.setText(self.order_data.get('initiator_full_name') or '')
        
        # Военное управление
        military_unit_id = self.order_data.get('military_unit_id')
        if military_unit_id:
            index = self.initiator_military_unit_combo.findData(military_unit_id)
            if index >= 0:
                self.initiator_military_unit_combo.setCurrentIndex(index)
        
        order_date = self.order_data.get('order_date')
        if order_date:
            self.order_date_input.setDate(order_date)
        
        self.order_number_input.setText(self.order_data.get('order_number') or '')
        
        receipt_date = self.order_data.get('receipt_date')
        if receipt_date:
            self.receipt_date_input.setDate(receipt_date)
        
        self.receipt_number_input.setText(self.order_data.get('receipt_number') or '')
        
        self.postal_index_input.setText(self.order_data.get('postal_index') or '')
        self.postal_region_input.setText(self.order_data.get('postal_region') or '')
        self.postal_district_input.setText(self.order_data.get('postal_district') or '')
        self.postal_town_input.setText(self.order_data.get('postal_town') or '')
        self.postal_street_input.setText(self.order_data.get('postal_street') or '')
        self.postal_house_input.setText(self.order_data.get('postal_house') or '')
        self.postal_building_input.setText(self.order_data.get('postal_building') or '')
        self.postal_letter_input.setText(self.order_data.get('postal_letter') or '')
        self.postal_apartment_input.setText(self.order_data.get('postal_apartment') or '')
        self.postal_room_input.setText(self.order_data.get('postal_room') or '')
        self.initiator_contacts_input.setText(self.order_data.get('initiator_contacts') or '')
        
        our_response_date = self.order_data.get('our_response_date')
        if our_response_date:
            self.our_response_date_input.setDate(our_response_date)
        
        self.our_response_number_input.setText(self.order_data.get('our_response_number') or '')
    
    def get_data(self):
        """Получение данных из формы"""
        return {
            "krd_id": self.krd_id,
            "initiator_type_id": self.initiator_type_combo.currentData(),
            "initiator_full_name": self.initiator_full_name_input.text().strip(),
            "military_unit_id": self.initiator_military_unit_combo.currentData(),
            "order_date": self.order_date_input.date().toString("yyyy-MM-dd"),
            "order_number": self.order_number_input.text().strip(),
            "receipt_date": self.receipt_date_input.date().toString("yyyy-MM-dd"),
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
            "our_response_date": self.our_response_date_input.date().toString("yyyy-MM-dd"),
            "our_response_number": self.our_response_number_input.text().strip()
        }
    
    def accept(self):
        """Сохранение данных при нажатии OK"""
        data = self.get_data()
        
        if not data["initiator_full_name"]:
            QMessageBox.warning(self, "Ошибка", "⚠️ Поле 'Полное наименование инициатора' обязательно для заполнения")
            return
        
        if not data["order_number"]:
            QMessageBox.warning(self, "Ошибка", "⚠️ Поле 'Исходящий номер поручения' обязательно для заполнения")
            return
        
        try:
            query = QSqlQuery(self.db)
            self.db.transaction()
            
            if self.is_edit:
                # Обновление существующей записи
                query.prepare("""
                    UPDATE krd.incoming_orders SET
                        initiator_type_id = :initiator_type_id,
                        initiator_full_name = :initiator_full_name,
                        military_unit_id = :military_unit_id,
                        order_date = :order_date,
                        order_number = :order_number,
                        receipt_date = :receipt_date,
                        receipt_number = :receipt_number,
                        postal_index = :postal_index,
                        postal_region = :postal_region,
                        postal_district = :postal_district,
                        postal_town = :postal_town,
                        postal_street = :postal_street,
                        postal_house = :postal_house,
                        postal_building = :postal_building,
                        postal_letter = :postal_letter,
                        postal_apartment = :postal_apartment,
                        postal_room = :postal_room,
                        initiator_contacts = :initiator_contacts,
                        our_response_date = :our_response_date,
                        our_response_number = :our_response_number
                    WHERE id = :id
                """)
                query.bindValue(":id", self.order_id)
            else:
                # Добавление новой записи
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
            
            if not query.exec():
                raise Exception(f"Ошибка SQL: {query.lastError().text()}")
            
            self.db.commit()
            
            # === ОБНОВЛЕНИЕ КЭША АВТОДОПОЛНЕНИЯ ПОСЛЕ СОХРАНЕНИЯ ===
            self.autocomplete_helper.clear_cache()
            
            QMessageBox.information(self, "Успех", "Поручение успешно " + ("обновлено" if self.is_edit else "добавлено"))
            super().accept()
            
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{str(e)}")