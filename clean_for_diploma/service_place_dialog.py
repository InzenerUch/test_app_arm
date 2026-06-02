from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QLabel, QPushButton, QComboBox,
    QMessageBox, QDialogButtonBox, QScrollArea, QWidget, QHBoxLayout
)
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont, QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression, Qt
from autocomplete_helper import AutocompleteHelper
from reference_editor_dialog import ReferenceEditorDialog
class ServicePlaceDialog(QDialog):
    def __init__(self, db_connection, krd_id, place_data=None, parent=None, read_only=False):
        super().__init__(parent)
        self.db = db_connection
        self.krd_id = krd_id
        self.place_data = place_data
        self.is_edit = place_data is not None
        self.place_id = place_data.get('id') if place_data else None
        self.read_only = read_only
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        if self.read_only:
            self.setWindowTitle("👁️ Просмотр места службы")
        else:
            self.setWindowTitle("✏️ Редактирование места службы" if self.is_edit else "➕ Добавление места службы")
        self.setMinimumSize(900, 750)
        self.setModal(True)
        self.init_ui()
        self.load_data()
        if self.read_only:
            self._apply_readonly_mode()
        else:
            self.setup_validators()
            self.setup_autocomplete_fields()
    def _apply_readonly_mode(self):
        for le in self.findChildren(QLineEdit):
            le.setReadOnly(True)
        for te in self.findChildren(QTextEdit):
            te.setReadOnly(True)
        for cb in self.findChildren(QComboBox):
            cb.setEnabled(False)
        for btn in self.findChildren(QPushButton):
            if "Сохранить" in btn.text():
                btn.hide()
            elif "Отмена" in btn.text():
                btn.setText("❌ Закрыть")
                btn.clicked.disconnect()
                btn.clicked.connect(self.accept)
            elif "⚙️" in btn.text():
                btn.hide()
    def _setup_ref_combo(self, combo, table_name, reload_func):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(combo, 1)
        btn = QPushButton("⚙️")
        btn.setToolTip(f"Настроить справочник: {table_name}")
        btn.setFixedSize(34, 34)
        btn.setProperty("role", "edit")
        btn.clicked.connect(lambda: self.open_ref_editor(table_name, reload_func))
        lay.addWidget(btn)
        return w
    def open_ref_editor(self, table_name, reload_func):
        dlg = ReferenceEditorDialog(self.db, self, initial_table=table_name)
        dlg.data_changed.connect(
            lambda changed_table: self._on_reference_changed(changed_table, table_name, reload_func)
        )
        dlg.exec()
    def _on_reference_changed(self, changed_table, expected_table, reload_func):
        if changed_table == expected_table:
            reload_func()
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        title_label = QLabel("✏️ Редактирование места службы" if self.is_edit else "➕ Добавление места службы")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        container = QWidget()
        form_layout = QVBoxLayout(container)
        form_layout.setSpacing(10)
        group1 = QGroupBox("📍 Основная информация")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group1_layout = QGridLayout()
        group1_layout.setSpacing(8)
        group1_layout.addWidget(QLabel("Наименование места службы *:"), 0, 0)
        self.place_name_input = QLineEdit()
        self.place_name_input.setPlaceholderText("Например: в/ч 12345")
        self.place_name_input.setMaxLength(255)
        group1_layout.addWidget(self.place_name_input, 0, 1, 1, 3)
        group1_layout.addWidget(QLabel("Военное управление:"), 1, 0)
        self.military_unit_combo = QComboBox()
        self.load_military_units()
        group1_layout.addWidget(self._setup_ref_combo(self.military_unit_combo, 'military_units', self.load_military_units), 1, 1)
        group1_layout.addWidget(QLabel("Гарнизон:"), 1, 2)
        self.garrison_combo = QComboBox()
        self.load_garrisons()
        group1_layout.addWidget(self._setup_ref_combo(self.garrison_combo, 'garrisons', self.load_garrisons), 1, 3)
        group1_layout.addWidget(QLabel("Воинская должность:"), 2, 0)
        self.position_combo = QComboBox()
        self.load_positions()
        group1_layout.addWidget(self._setup_ref_combo(self.position_combo, 'positions', self.load_positions), 2, 1)
        group1_layout.addWidget(QLabel("Номер воинской части:"), 2, 2)
        self.unit_number_input = QLineEdit()
        self.unit_number_input.setPlaceholderText("Например: в/ч 54321")
        self.unit_number_input.setMaxLength(50)
        group1_layout.addWidget(self.unit_number_input, 2, 3)
        group1_layout.addWidget(QLabel("Командиры (звание, ФИО, контакты):"), 3, 0)
        self.commanders_input = QTextEdit()
        self.commanders_input.setMaximumHeight(80)
        self.commanders_input.setPlaceholderText("Командир части, замполит и т.д.")
        group1_layout.addWidget(self.commanders_input, 3, 1, 1, 3)
        group1.setLayout(group1_layout)
        form_layout.addWidget(group1)
        group2 = QGroupBox("📮 Почтовый адрес места службы")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group2_layout = QGridLayout()
        group2_layout.setSpacing(8)
        group2_layout.addWidget(QLabel("Индекс:"), 0, 0)
        self.postal_index_input = QLineEdit()
        self.postal_index_input.setPlaceholderText("Например: 660000")
        self.postal_index_input.setMaxLength(20)
        group2_layout.addWidget(self.postal_index_input, 0, 1)
        group2_layout.addWidget(QLabel("Субъект РФ:"), 0, 2)
        self.postal_region_input = QLineEdit()
        self.postal_region_input.setPlaceholderText("Например: Красноярский край")
        self.postal_region_input.setMaxLength(100)
        group2_layout.addWidget(self.postal_region_input, 0, 3)
        group2_layout.addWidget(QLabel("Административный район:"), 1, 0)
        self.postal_district_input = QLineEdit()
        self.postal_district_input.setMaxLength(100)
        group2_layout.addWidget(self.postal_district_input, 1, 1)
        group2_layout.addWidget(QLabel("Населенный пункт:"), 1, 2)
        self.postal_town_input = QLineEdit()
        self.postal_town_input.setMaxLength(100)
        group2_layout.addWidget(self.postal_town_input, 1, 3)
        group2_layout.addWidget(QLabel("Улица:"), 2, 0)
        self.postal_street_input = QLineEdit()
        self.postal_street_input.setMaxLength(100)
        group2_layout.addWidget(self.postal_street_input, 2, 1)
        group2_layout.addWidget(QLabel("Дом:"), 2, 2)
        self.postal_house_input = QLineEdit()
        self.postal_house_input.setMaxLength(50)
        group2_layout.addWidget(self.postal_house_input, 2, 3)
        group2_layout.addWidget(QLabel("Корпус:"), 3, 0)
        self.postal_building_input = QLineEdit()
        self.postal_building_input.setMaxLength(50)
        group2_layout.addWidget(self.postal_building_input, 3, 1)
        group2_layout.addWidget(QLabel("Литер:"), 3, 2)
        self.postal_letter_input = QLineEdit()
        self.postal_letter_input.setMaxLength(10)
        group2_layout.addWidget(self.postal_letter_input, 3, 3)
        group2_layout.addWidget(QLabel("Квартира:"), 4, 0)
        self.postal_apartment_input = QLineEdit()
        self.postal_apartment_input.setMaxLength(50)
        group2_layout.addWidget(self.postal_apartment_input, 4, 1)
        group2_layout.addWidget(QLabel("Комната:"), 4, 2)
        self.postal_room_input = QLineEdit()
        self.postal_room_input.setMaxLength(50)
        group2_layout.addWidget(self.postal_room_input, 4, 3)
        group2.setLayout(group2_layout)
        form_layout.addWidget(group2)
        group3 = QGroupBox("📞 Контакты")
        group3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group3_layout = QGridLayout()
        group3_layout.setSpacing(8)
        group3_layout.addWidget(QLabel("Контакты места службы:"), 0, 0)
        self.place_contacts_input = QLineEdit()
        self.place_contacts_input.setPlaceholderText("Телефон, email, факс")
        self.place_contacts_input.setMaxLength(255)
        group3_layout.addWidget(self.place_contacts_input, 0, 1, 1, 3)
        group3.setLayout(group3_layout)
        form_layout.addWidget(group3)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        save_btn = button_box.button(QDialogButtonBox.StandardButton.Save)
        save_btn.setText("💾 Сохранить")
        save_btn.setProperty("role", "save")
        cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("❌ Отмена")
        cancel_btn.setProperty("role", "danger")
        layout.addWidget(button_box)
    def setup_validators(self):
        if self.read_only: return
        index_regex = QRegularExpression(r"^\d{0,20}$")
        self.postal_index_input.setValidator(QRegularExpressionValidator(index_regex))
        letter_regex = QRegularExpression(r"^[а-яА-Яa-zA-Z0-9]{0,10}$")
        self.postal_letter_input.setValidator(QRegularExpressionValidator(letter_regex))
    def load_military_units(self):
        current_id = self.military_unit_combo.currentData()
        self.military_unit_combo.clear()
        self.military_unit_combo.addItem("", None)
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.military_units ORDER BY name")
        while query.next():
            self.military_unit_combo.addItem(query.value(1), query.value(0))
        if current_id is not None:
            idx = self.military_unit_combo.findData(current_id)
            if idx >= 0: self.military_unit_combo.setCurrentIndex(idx)
    def load_garrisons(self):
        current_id = self.garrison_combo.currentData()
        self.garrison_combo.clear()
        self.garrison_combo.addItem("", None)
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.garrisons ORDER BY name")
        while query.next():
            self.garrison_combo.addItem(query.value(1), query.value(0))
        if current_id is not None:
            idx = self.garrison_combo.findData(current_id)
            if idx >= 0: self.garrison_combo.setCurrentIndex(idx)
    def load_positions(self):
        current_id = self.position_combo.currentData()
        self.position_combo.clear()
        self.position_combo.addItem("", None)
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.positions ORDER BY name")
        while query.next():
            self.position_combo.addItem(query.value(1), query.value(0))
        if current_id is not None:
            idx = self.position_combo.findData(current_id)
            if idx >= 0: self.position_combo.setCurrentIndex(idx)
    def setup_autocomplete_fields(self):
        if self.read_only: return
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
                field_widget, 'service_places', column_name, max_items=max_items, show_on_focus=True
            )
    def load_data(self):
        if not self.place_data:
            return
        self.place_name_input.setText(self.place_data.get('place_name') or '')
        if self.place_data.get('military_unit_id'):
            idx = self.military_unit_combo.findData(self.place_data['military_unit_id'])
            if idx >= 0: self.military_unit_combo.setCurrentIndex(idx)
        if self.place_data.get('garrison_id'):
            idx = self.garrison_combo.findData(self.place_data['garrison_id'])
            if idx >= 0: self.garrison_combo.setCurrentIndex(idx)
        if self.place_data.get('position_id'):
            idx = self.position_combo.findData(self.place_data['position_id'])
            if idx >= 0: self.position_combo.setCurrentIndex(idx)
        self.commanders_input.setPlainText(self.place_data.get('commanders') or '')
        self.postal_index_input.setText(self.place_data.get('postal_index') or '')
        self.postal_region_input.setText(self.place_data.get('postal_region') or '')
        self.unit_number_input.setText(self.place_data.get('military_unit_number') or '')
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
        return {
            "krd_id": self.krd_id,
            "place_name": self.place_name_input.text().strip(),
            "military_unit_number": self.unit_number_input.text().strip(),
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
        if self.read_only:
            super().accept()
            return
        data = self.get_data()
        if not data["place_name"]:
            QMessageBox.warning(self, "Ошибка", "⚠️ Поле 'Наименование места службы' обязательно")
            return
        try:
            query = QSqlQuery(self.db)
            self.db.transaction()
            if self.is_edit:
                query.prepare("""
                    UPDATE krd.service_places SET
                    place_name = :place_name,
                    military_unit_number = :military_unit_number,
                    military_unit_id = :military_unit_id,
                    garrison_id = :garrison_id, position_id = :position_id,
                    commanders = :commanders,
                    postal_index = :postal_index, postal_region = :postal_region,
                    postal_district = :postal_district, postal_town = :postal_town,
                    postal_street = :postal_street, postal_house = :postal_house,
                    postal_building = :postal_building, postal_letter = :postal_letter,
                    postal_apartment = :postal_apartment, postal_room = :postal_room,
                    place_contacts = :place_contacts
                    WHERE id = :id
                    INSERT INTO krd.service_places (
                        krd_id, place_name, military_unit_number, military_unit_id, garrison_id, position_id,
                        commanders, postal_index, postal_region, postal_district, postal_town,
                        postal_street, postal_house, postal_building, postal_letter,
                        postal_apartment, postal_room, place_contacts
                    ) VALUES (
                        :krd_id, :place_name, :military_unit_number, :military_unit_id, :garrison_id, :position_id,
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
            self.autocomplete_helper.clear_cache()
            QMessageBox.information(self, "Успех", "Место службы успешно сохранено")
            super().accept()
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {str(e)}")