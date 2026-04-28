"""
Диалоговое окно для добавления/редактирования адреса проживания
С поддержкой автодополнения
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QGridLayout,
    QLineEdit, QDateEdit, QTextEdit, QLabel, QPushButton,
    QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont

from autocomplete_helper import AutocompleteHelper


class AddressDialog(QDialog):
    """Диалог для добавления/редактирования адреса"""
    
    def __init__(self, db_connection, krd_id, address_data=None, parent=None):
        """
        Args:
            db_connection: соединение с БД
            krd_id: ID карточки розыска
            address_data: данные адреса для редактирования (None для нового)
            parent: родительское окно
        """
        super().__init__(parent)
        self.db = db_connection
        self.krd_id = krd_id
        self.address_data = address_data
        self.is_edit = address_data is not None
        self.address_id = address_data.get('id') if address_data else None
        
        # === ИНИЦИАЛИЗАЦИЯ ПОМОЩНИКА АВТОДОПОЛНЕНИЯ ===
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        
        self.setWindowTitle("✏️ Редактирование адреса" if self.is_edit else "➕ Добавление адреса")
        self.setMinimumSize(700, 600)
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
        title_label = QLabel("✏️ Редактирование адреса" if self.is_edit else "➕ Добавление адреса")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # === Группа: Адресные данные ===
        group = QGroupBox("📍 Адресные данные")
        group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        form_layout = QGridLayout()
        form_layout.setSpacing(8)
        
        form_layout.addWidget(QLabel("Субъект РФ:"), 0, 0)
        self.region_input = QLineEdit()
        self.region_input.setPlaceholderText("Например: Красноярский край")
        form_layout.addWidget(self.region_input, 0, 1)
        
        form_layout.addWidget(QLabel("Административный район:"), 0, 2)
        self.district_input = QLineEdit()
        self.district_input.setPlaceholderText("Например: Центральный район")
        form_layout.addWidget(self.district_input, 0, 3)
        
        form_layout.addWidget(QLabel("Населенный пункт *:"), 1, 0)
        self.town_input = QLineEdit()
        self.town_input.setPlaceholderText("Например: г. Красноярск")
        form_layout.addWidget(self.town_input, 1, 1)
        
        form_layout.addWidget(QLabel("Улица:"), 1, 2)
        self.street_input = QLineEdit()
        self.street_input.setPlaceholderText("Например: ул. Ленина")
        form_layout.addWidget(self.street_input, 1, 3)
        
        form_layout.addWidget(QLabel("Дом:"), 2, 0)
        self.house_input = QLineEdit()
        self.house_input.setPlaceholderText("Например: 10")
        form_layout.addWidget(self.house_input, 2, 1)
        
        form_layout.addWidget(QLabel("Корпус:"), 2, 2)
        self.building_input = QLineEdit()
        self.building_input.setPlaceholderText("Например: 2")
        form_layout.addWidget(self.building_input, 2, 3)
        
        form_layout.addWidget(QLabel("Литер:"), 3, 0)
        self.letter_input = QLineEdit()
        self.letter_input.setPlaceholderText("Например: А")
        form_layout.addWidget(self.letter_input, 3, 1)
        
        form_layout.addWidget(QLabel("Квартира:"), 3, 2)
        self.apartment_input = QLineEdit()
        self.apartment_input.setPlaceholderText("Например: 50")
        form_layout.addWidget(self.apartment_input, 3, 3)
        
        form_layout.addWidget(QLabel("Комната:"), 4, 0)
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("Например: 1")
        form_layout.addWidget(self.room_input, 4, 1)
        
        form_layout.addWidget(QLabel("Дата проверки:"), 5, 0)
        self.check_date_input = QDateEdit()
        self.check_date_input.setCalendarPopup(True)
        self.check_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.check_date_input, 5, 1)
        
        form_layout.addWidget(QLabel("Результат проверки:"), 6, 0)
        self.check_result_input = QTextEdit()
        self.check_result_input.setMaximumHeight(60)
        self.check_result_input.setPlaceholderText("Результаты проверки адреса")
        form_layout.addWidget(self.check_result_input, 6, 1, 1, 3)
        
        group.setLayout(form_layout)
        layout.addWidget(group)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        save_btn = button_box.button(QDialogButtonBox.StandardButton.Save)
        save_btn.setText("💾 Сохранить")
        save_btn.setProperty("role", "save")
        save_btn.setStyleSheet("")
        
        cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("❌ Отмена")
        cancel_btn.setProperty("role", "danger")
        cancel_btn.setStyleSheet("")
        
        layout.addWidget(button_box)
    
    def setup_autocomplete_fields(self):
        """Настройка автодополнения для всех текстовых полей"""
        
        fields_config = [
            (self.region_input, 'region', 20),
            (self.district_input, 'district', 20),
            (self.town_input, 'town', 20),
            (self.street_input, 'street', 30),
            (self.house_input, 'house', 15),
            (self.building_input, 'building', 15),
            (self.letter_input, 'letter', 10),
            (self.apartment_input, 'apartment', 15),
            (self.room_input, 'room', 15),
        ]
        
        for field_widget, column_name, max_items in fields_config:
            self.autocomplete_helper.setup_autocomplete(
                field_widget, 
                'addresses', 
                column_name,
                max_items=max_items,
                show_on_focus=True
            )
        
        print(f"✅ Автодополнение настроено для {len(fields_config)} полей адреса")
    
    def load_data(self):
        """Загрузка данных адреса для редактирования"""
        if not self.address_data:
            return
        
        self.region_input.setText(self.address_data.get('region') or '')
        self.district_input.setText(self.address_data.get('district') or '')
        self.town_input.setText(self.address_data.get('town') or '')
        self.street_input.setText(self.address_data.get('street') or '')
        self.house_input.setText(self.address_data.get('house') or '')
        self.building_input.setText(self.address_data.get('building') or '')
        self.letter_input.setText(self.address_data.get('letter') or '')
        self.apartment_input.setText(self.address_data.get('apartment') or '')
        self.room_input.setText(self.address_data.get('room') or '')
        
        check_date = self.address_data.get('check_date')
        if check_date:
            self.check_date_input.setDate(check_date)
        
        self.check_result_input.setPlainText(self.address_data.get('check_result') or '')
    
    def get_data(self):
        """Получение данных из формы"""
        return {
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
            "check_date": self.check_date_input.date().toString("yyyy-MM-dd"),
            "check_result": self.check_result_input.toPlainText()
        }
    
    def accept(self):
        """Сохранение данных при нажатии OK"""
        data = self.get_data()
        
        if not data["town"]:
            QMessageBox.warning(self, "Ошибка", "⚠️ Поле 'Населенный пункт' обязательно для заполнения")
            return
        
        try:
            query = QSqlQuery(self.db)
            self.db.transaction()
            
            if self.is_edit:
                # Обновление существующей записи
                query.prepare("""
                    UPDATE krd.addresses SET
                        region = :region,
                        district = :district,
                        town = :town,
                        street = :street,
                        house = :house,
                        building = :building,
                        letter = :letter,
                        apartment = :apartment,
                        room = :room,
                        check_date = :check_date,
                        check_result = :check_result
                    WHERE id = :id
                """)
                query.bindValue(":id", self.address_id)
            else:
                # Добавление новой записи
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
            
            if not query.exec():
                raise Exception(f"Ошибка SQL: {query.lastError().text()}")
            
            self.db.commit()
            
            # === ОБНОВЛЕНИЕ КЭША АВТОДОПОЛНЕНИЯ ПОСЛЕ СОХРАНЕНИЯ ===
            self.autocomplete_helper.clear_cache()
            
            QMessageBox.information(self, "Успех", "Адрес успешно " + ("обновлён" if self.is_edit else "добавлен"))
            super().accept()
            
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{str(e)}")