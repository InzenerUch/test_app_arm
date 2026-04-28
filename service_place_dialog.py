"""
Диалоговое окно для добавления/редактирования места службы
С поддержкой автодополнения
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QLabel, QPushButton, QComboBox,
    QMessageBox, QDialogButtonBox, QScrollArea, QWidget
)
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont

from autocomplete_helper import AutocompleteHelper


class ServicePlaceDialog(QDialog):
    """Диалог для добавления/редактирования места службы"""
    
    def __init__(self, db_connection, krd_id, place_data=None, parent=None):
        """
        Args:
            db_connection: соединение с БД
            krd_id: ID карточки розыска
            place_ данные места службы для редактирования (None для нового)
            parent: родительское окно
        """
        super().__init__(parent)
        self.db = db_connection
        self.krd_id = krd_id
        self.place_data = place_data
        self.is_edit = place_data is not None
        self.place_id = place_data.get('id') if place_data else None
        
        # === ИНИЦИАЛИЗАЦИЯ ПОМОЩНИКА АВТОДОПОЛНЕНИЯ ===
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        
        self.setWindowTitle("✏️ Редактирование места службы" if self.is_edit else "➕ Добавление места службы")
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
        title_label = QLabel("✏️ Редактирование места службы" if self.is_edit else "➕ Добавление места службы")
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
        
        # === Группа 1: Основная информация ===
        group1 = QGroupBox("📍 Основная информация")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group1_layout = QGridLayout()
        group1_layout.setSpacing(8)
        
        group1_layout.addWidget(QLabel("Наименование места службы *:"), 0, 0)
        self.place_name_input = QLineEdit()
        self.place_name_input.setPlaceholderText("Например: в/ч 12345")
        group1_layout.addWidget(self.place_name_input, 0, 1, 1, 3)
        
        group1_layout.addWidget(QLabel("Военное управление:"), 1, 0)
        self.military_unit_combo = QComboBox()
        self.load_military_units()
        group1_layout.addWidget(self.military_unit_combo, 1, 1)
        
        group1_layout.addWidget(QLabel("Гарнизон:"), 1, 2)
        self.garrison_combo = QComboBox()
        self.load_garrisons()
        group1_layout.addWidget(self.garrison_combo, 1, 3)
        
        group1_layout.addWidget(QLabel("Воинская должность:"), 2, 0)
        self.position_combo = QComboBox()
        self.load_positions()
        group1_layout.addWidget(self.position_combo, 2, 1)
        
        group1_layout.addWidget(QLabel("Командиры (звание, ФИО, контакты):"), 3, 0)
        self.commanders_input = QTextEdit()
        self.commanders_input.setMaximumHeight(80)
        self.commanders_input.setPlaceholderText("Командир части, замполит и т.д.")
        group1_layout.addWidget(self.commanders_input, 3, 1, 1, 3)
        
        group1.setLayout(group1_layout)
        form_layout.addWidget(group1)
        
        # === Группа 2: Почтовый адрес места службы ===
        group2 = QGroupBox("📮 Почтовый адрес места службы")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group2_layout = QGridLayout()
        group2_layout.setSpacing(8)
        
        group2_layout.addWidget(QLabel("Индекс:"), 0, 0)
        self.postal_index_input = QLineEdit()
        self.postal_index_input.setPlaceholderText("Например: 660000")
        group2_layout.addWidget(self.postal_index_input, 0, 1)
        
        group2_layout.addWidget(QLabel("Субъект РФ:"), 0, 2)
        self.postal_region_input = QLineEdit()
        self.postal_region_input.setPlaceholderText("Например: Красноярский край")
        group2_layout.addWidget(self.postal_region_input, 0, 3)
        
        group2_layout.addWidget(QLabel("Административный район:"), 1, 0)
        self.postal_district_input = QLineEdit()
        group2_layout.addWidget(self.postal_district_input, 1, 1)
        
        group2_layout.addWidget(QLabel("Населенный пункт:"), 1, 2)
        self.postal_town_input = QLineEdit()
        group2_layout.addWidget(self.postal_town_input, 1, 3)
        
        group2_layout.addWidget(QLabel("Улица:"), 2, 0)
        self.postal_street_input = QLineEdit()
        group2_layout.addWidget(self.postal_street_input, 2, 1)
        
        group2_layout.addWidget(QLabel("Дом:"), 2, 2)
        self.postal_house_input = QLineEdit()
        group2_layout.addWidget(self.postal_house_input, 2, 3)
        
        group2_layout.addWidget(QLabel("Корпус:"), 3, 0)
        self.postal_building_input = QLineEdit()
        group2_layout.addWidget(self.postal_building_input, 3, 1)
        
        group2_layout.addWidget(QLabel("Литер:"), 3, 2)
        self.postal_letter_input = QLineEdit()
        group2_layout.addWidget(self.postal_letter_input, 3, 3)
        
        group2_layout.addWidget(QLabel("Квартира:"), 4, 0)
        self.postal_apartment_input = QLineEdit()
        group2_layout.addWidget(self.postal_apartment_input, 4, 1)
        
        group2_layout.addWidget(QLabel("Комната:"), 4, 2)
        self.postal_room_input = QLineEdit()
        group2_layout.addWidget(self.postal_room_input, 4, 3)
        
        group2.setLayout(group2_layout)
        form_layout.addWidget(group2)
        
        # === Группа 3: Контакты ===
        group3 = QGroupBox("📞 Контакты")
        group3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group3_layout = QGridLayout()
        group3_layout.setSpacing(8)
        
        group3_layout.addWidget(QLabel("Контакты места службы:"), 0, 0)
        self.place_contacts_input = QLineEdit()
        self.place_contacts_input.setPlaceholderText("Телефон, email, факс")
        group3_layout.addWidget(self.place_contacts_input, 0, 1, 1, 3)
        
        group3.setLayout(group3_layout)
        form_layout.addWidget(group3)
        
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
        save_btn.setProperty("role","save")
        save_btn.setStyleSheet("")
        
        cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("❌ Отмена")
        cancel_btn.setProperty("role", "danger")
        cancel_btn.setStyleSheet("")
        
        layout.addWidget(button_box)
    
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
    
    def setup_autocomplete_fields(self):
        """Настройка автодополнения для почтовых полей"""
        
        fields_config = [
            (self.postal_region_input, 'postal_region', 20),
            (self.postal_district_input, 'postal_district', 20),
            (self.postal_town_input, 'postal_town', 20),
            (self.postal_street_input, 'postal_street', 30),
            (self.postal_house_input, 'postal_house', 15),
            (self.postal_building_input, 'postal_building', 15),
            (self.postal_letter_input, 'postal_letter', 10),
            (self.postal_apartment_input, 'postal_apartment', 15),
            (self.postal_room_input, 'postal_room', 15),
            (self.commanders_input, 'commanders', 20),
            (self.place_contacts_input, 'place_contacts', 20),
        ]
        
        for field_widget, column_name, max_items in fields_config:
            self.autocomplete_helper.setup_autocomplete(
                field_widget, 
                'service_places', 
                column_name,
                max_items=max_items,
                show_on_focus=True
            )
        
        print(f"✅ Автодополнение настроено для {len(fields_config)} полей места службы")
    
    def load_data(self):
        """Загрузка данных места службы для редактирования"""
        if not self.place_data:
            return
        
        self.place_name_input.setText(self.place_data.get('place_name') or '')
        
        # Военное управление
        military_unit_id = self.place_data.get('military_unit_id')
        if military_unit_id:
            index = self.military_unit_combo.findData(military_unit_id)
            if index >= 0:
                self.military_unit_combo.setCurrentIndex(index)
        
        # Гарнизон
        garrison_id = self.place_data.get('garrison_id')
        if garrison_id:
            index = self.garrison_combo.findData(garrison_id)
            if index >= 0:
                self.garrison_combo.setCurrentIndex(index)
        
        # Должность
        position_id = self.place_data.get('position_id')
        if position_id:
            index = self.position_combo.findData(position_id)
            if index >= 0:
                self.position_combo.setCurrentIndex(index)
        
        self.commanders_input.setPlainText(self.place_data.get('commanders') or '')
        self.postal_index_input.setText(self.place_data.get('postal_index') or '')
        self.postal_region_input.setText(self.place_data.get('postal_region') or '')
        self.postal_district_input.setText(self.place_data.get('postal_district') or '')
        self.postal_town_input.setText(self.place_data.get('postal_town') or '')
        self.postal_street_input.setText(self.place_data.get('postal_street') or '')
        self.postal_house_input.setText(self.place_data.get('postal_house') or '')
        self.postal_building_input.setText(self.place_data.get('postal_building') or '')
        self.postal_letter_input.setText(self.place_data.get('postal_letter') or '')
        self.postal_apartment_input.setText(self.place_data.get('postal_apartment') or '')
        self.postal_room_input.setText(self.place_data.get('postal_room') or '')
        self.place_contacts_input.setText(self.place_data.get('place_contacts') or '')
    
    def get_data(self):
        """Получение данных из формы"""
        return {
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
    
    def accept(self):
        """Сохранение данных при нажатии OK"""
        data = self.get_data()
        
        if not data["place_name"]:
            QMessageBox.warning(self, "Ошибка", "⚠️ Поле 'Наименование места службы' обязательно для заполнения")
            return
        
        try:
            query = QSqlQuery(self.db)
            self.db.transaction()
            
            if self.is_edit:
                # Обновление существующей записи
                query.prepare("""
                    UPDATE krd.service_places SET
                        place_name = :place_name,
                        military_unit_id = :military_unit_id,
                        garrison_id = :garrison_id,
                        position_id = :position_id,
                        commanders = :commanders,
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
                        place_contacts = :place_contacts
                    WHERE id = :id
                """)
                query.bindValue(":id", self.place_id)
            else:
                # Добавление новой записи
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
            
            if not query.exec():
                raise Exception(f"Ошибка SQL: {query.lastError().text()}")
            
            self.db.commit()
            
            # === ОБНОВЛЕНИЕ КЭША АВТОДОПОЛНЕНИЯ ПОСЛЕ СОХРАНЕНИЯ ===
            self.autocomplete_helper.clear_cache()
            
            QMessageBox.information(self, "Успех", "Место службы успешно " + ("обновлено" if self.is_edit else "добавлено"))
            super().accept()
            
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{str(e)}")