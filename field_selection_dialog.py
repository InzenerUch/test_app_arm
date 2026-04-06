"""
Диалог выбора полей для отчета КРД
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, 
    QPushButton, QLabel, QScrollArea, QWidget, QGridLayout,
    QMessageBox, QDialogButtonBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import json


class FieldSelectionDialog(QDialog):
    """Диалог выбора полей для отчета"""
    
    AVAILABLE_FIELDS = {
        "social_data": {
            "title": "Социально-демографические данные",
            "fields": [
                ("krd_number", "№ КРД"),
                ("tab_number", "Табельный номер"),
                ("personal_number", "Личный номер"),
                ("category_name", "Категория военнослужащего"),
                ("rank_name", "Воинское звание"),
                ("surname", "Фамилия"),
                ("name", "Имя"),
                ("patronymic", "Отчество"),
                ("birth_date", "Дата рождения"),
                ("birth_place_town", "Населенный пункт места рождения"),
                ("birth_place_district", "Административный район места рождения"),
                ("birth_place_region", "Субъект (регион) места рождения"),
                ("birth_place_country", "Страна места рождения"),
                ("drafted_by_commissariat", "Наименование комиссариата"),
                ("draft_date", "Дата призыва"),
                ("povsk", "Наименование ПОВСК"),
                ("selection_date", "Дата отбора"),
                ("education", "Образование"),
                ("criminal_record", "Сведения о судимости"),
                ("social_media_account", "Аккаунт в социальных сетях"),
                ("bank_card_number", "Номер банковской карты"),
                ("passport_series", "Серия паспорта"),
                ("passport_number", "Номер паспорта"),
                ("passport_issue_date", "Дата выдачи паспорта"),
                ("passport_issued_by", "Кем выдан паспорт"),
                ("military_id_series", "Серия военного билета"),
                ("military_id_number", "Номер военного билета"),
                ("military_id_issue_date", "Дата выдачи военного билета"),
                ("military_id_issued_by", "Кем выдан военный билет"),
                ("appearance_features", "Особенности внешности"),
                ("personal_marks", "Личные приметы"),
                ("military_contacts", "Контакты в/с"),
                ("relatives_info", "Сведения о близких родственниках"),
            ]
        },
        "addresses": {
            "title": "Адреса проживания",
            "fields": [
                ("region", "Субъект РФ"),
                ("district", "Административный район"),
                ("town", "Населенный пункт"),
                ("street", "Улица"),
                ("house", "Дом"),
                ("building", "Корпус"),
                ("letter", "Литер"),
                ("apartment", "Квартира"),
                ("room", "Комната"),
                ("check_date", "Дата адресной проверки"),
                ("check_result", "Результат адресной проверки"),
            ]
        },
        "incoming_orders": {
            "title": "Входящие поручения на розыск",
            "fields": [
                ("initiator_full_name", "Инициатор розыска"),
                ("order_date", "Исходящая дата поручения"),
                ("order_number", "Исходящий номер поручения"),
                ("receipt_date", "Дата поступления в ВК"),
                ("receipt_number", "Входящий номер в ВК"),
                ("postal_index", "Индекс"),
                ("postal_region", "Субъект РФ"),
                ("postal_district", "Административный район"),
                ("postal_town", "Населенный пункт"),
                ("postal_street", "Улица"),
                ("postal_house", "Дом"),
                ("initiator_contacts", "Контакты источника"),
                ("our_response_date", "Дата ответа ВК"),
                ("our_response_number", "Исходящий номер ответа ВК"),
                ("military_unit_name", "Военное управление инициатора"),
            ]
        },
        "service_places": {
            "title": "Места службы",
            "fields": [
                ("place_name", "Наименование места службы"),
                ("military_unit_name", "Военное управление места службы"),
                ("garrison_name", "Гарнизон места службы"),
                ("position_name", "Воинская должность"),
                ("commanders", "Командиры (начальники)"),
                ("postal_index", "Индекс"),
                ("postal_region", "Субъект РФ"),
                ("postal_town", "Населенный пункт"),
                ("postal_street", "Улица"),
                ("postal_house", "Дом"),
                ("place_contacts", "Контакты места службы"),
            ]
        },
        "soch_episodes": {
            "title": "Сведения о СОЧ",
            "fields": [
                ("soch_date", "Дата СОЧ"),
                ("soch_location", "Место СОЧ"),
                ("order_date_number", "Дата и номер приказа о СОЧ"),
                ("witnesses", "Очевидцы СОЧ"),
                ("reasons", "Вероятные причины СОЧ"),
                ("weapon_info", "Сведения о наличии оружия"),
                ("clothing", "Во что был одет"),
                ("movement_options", "Варианты движения"),
                ("search_date", "Дата розыска"),
                ("found_by", "Кем разыскан"),
                ("notification_date", "Дата уведомления"),
                ("notification_number", "Номер уведомления"),
            ]
        },
        "outgoing_requests": {
            "title": "Исходящие запросы и поручения",
            "fields": [
                ("request_type_name", "Наименование запроса"),
                ("recipient_name", "Наименование адресата"),
                ("military_unit_name", "Военное управление адресата"),
                ("issue_date", "Исходящая дата"),
                ("issue_number", "Исходящий номер"),
                ("postal_index", "Индекс"),
                ("postal_region", "Субъект РФ"),
                ("postal_town", "Населенный пункт"),
                ("postal_street", "Улица"),
                ("postal_house", "Дом"),
                ("recipient_contacts", "Контакты"),
            ]
        }
    }
    
    def __init__(self, parent=None, config=None, template_name=None):
        super().__init__(parent)
        self.setWindowTitle("Редактор шаблона отчета")
        self.setMinimumSize(900, 700)
        
        self.template_name = template_name
        self.section_checkboxes = {}
        self.field_checkboxes = {}
        
        self.init_ui()
        
        if config:
            self.apply_config(config)
        else:
            self.select_recommended_fields()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # === Заголовок с именем шаблона ===
        title_layout = QHBoxLayout()
        
        if self.template_name:
            title_label = QLabel(f"✏️ Редактирование шаблона: {self.template_name}")
        else:
            title_label = QLabel("➕ Создание нового шаблона отчета")
        
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # === Поле имени шаблона ===
        if not self.template_name:
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Название шаблона:"))
            self.template_name_input = QLineEdit()
            self.template_name_input.setPlaceholderText("Введите название шаблона")
            name_layout.addWidget(self.template_name_input)
            layout.addLayout(name_layout)
        
        # === Инструкция ===
        info_label = QLabel("📌 Выберите секции и поля, которые будут включены в отчет")
        info_label.setStyleSheet("QLabel { color: #666; padding: 5px; border-radius: 3px; }")
        layout.addWidget(info_label)
        
        # === Скролл для всех секций ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        sections_layout = QVBoxLayout(container)
        sections_layout.setSpacing(15)
        
        for section_key, section_info in self.AVAILABLE_FIELDS.items():
            section_group = QGroupBox(section_info["title"])
            section_layout = QVBoxLayout(section_group)
            
            section_checkbox = QCheckBox("✓ Включить секцию")
            section_checkbox.setChecked(True)
            # === ИСПРАВЛЕНО: Используем int для сравнения ===
            section_checkbox.stateChanged.connect(
                lambda state, sk=section_key: self.on_section_toggled(sk, int(state))
            )
            section_layout.addWidget(section_checkbox)
            self.section_checkboxes[section_key] = section_checkbox
            
            fields_widget = QWidget()
            fields_layout = QGridLayout(fields_widget)
            fields_layout.setSpacing(5)
            
            self.field_checkboxes[section_key] = {}
            
            for i, (field_key, field_name) in enumerate(section_info["fields"]):
                checkbox = QCheckBox(field_name)
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(
                    lambda state, sk=section_key, fk=field_key: 
                    self.on_field_toggled(sk, fk, int(state))
                )
                
                row = i // 2
                col = i % 2
                fields_layout.addWidget(checkbox, row, col)
                
                self.field_checkboxes[section_key][field_key] = checkbox
            
            section_layout.addWidget(fields_widget)
            sections_layout.addWidget(section_group)
        
        sections_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # === Кнопки быстрого выбора ===
        quick_select_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Выбрать все")
        select_all_btn.clicked.connect(self.select_all_fields)
        quick_select_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Снять все")
        deselect_all_btn.clicked.connect(self.deselect_all_fields)
        quick_select_layout.addWidget(deselect_all_btn)
        
        select_recommended_btn = QPushButton("Рекомендуемый набор")
        select_recommended_btn.clicked.connect(self.select_recommended_fields)
        quick_select_layout.addWidget(select_recommended_btn)
        
        quick_select_layout.addStretch()
        layout.addLayout(quick_select_layout)
        
        # === Статистика ===
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; padding: 5px; }")
        self.update_stats()
        layout.addWidget(self.stats_label)
        
        # === Кнопки OK/Cancel ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_section_toggled(self, section_key, state):
        """Обработка включения/выключения секции"""
        # === ИСПРАВЛЕНО: Сравниваем с int значением (2 = Checked) ===
        is_checked = (state == 2)  # Qt.CheckState.Checked = 2
        
        print(f"🔧 Section {section_key}: state={state}, is_checked={is_checked}")
        
        if section_key in self.field_checkboxes:
            for checkbox in self.field_checkboxes[section_key].values():
                checkbox.setEnabled(is_checked)
                if not is_checked:
                    checkbox.setChecked(False)
        
        self.update_stats()
    
    def on_field_toggled(self, section_key, field_key, state):
        """Обработка включения/выключения поля"""
        self.update_stats()
    
    def update_stats(self):
        """Обновление статистики выбранных полей"""
        sections_count = 0
        fields_count = 0
        
        for section_key, section_checkbox in self.section_checkboxes.items():
            if section_checkbox.isChecked():
                sections_count += 1
                
                if section_key in self.field_checkboxes:
                    for checkbox in self.field_checkboxes[section_key].values():
                        if checkbox.isChecked() and checkbox.isEnabled():
                            fields_count += 1
        
        self.stats_label.setText(f"📊 Выбрано секций: {sections_count} | Всего полей: {fields_count}")
    
    def select_all_fields(self):
        """Выбрать все поля"""
        for section_key, section_checkbox in self.section_checkboxes.items():
            section_checkbox.setChecked(True)
            self.on_section_toggled(section_key, 2)  # 2 = Checked
            
            if section_key in self.field_checkboxes:
                for checkbox in self.field_checkboxes[section_key].values():
                    checkbox.setChecked(True)
        
        self.update_stats()
    
    def deselect_all_fields(self):
        """Снять выбор со всех полей"""
        for section_key, section_checkbox in self.section_checkboxes.items():
            section_checkbox.setChecked(False)
            self.on_section_toggled(section_key, 0)  # 0 = Unchecked
        
        self.update_stats()
    
    def select_recommended_fields(self):
        """Выбрать рекомендуемый набор полей"""
        self.deselect_all_fields()
        
        recommended_sections = ["social_data"]
        
        for section_key in recommended_sections:
            if section_key in self.section_checkboxes:
                self.section_checkboxes[section_key].setChecked(True)
                self.on_section_toggled(section_key, 2)  # 2 = Checked
        
        self.update_stats()
    
    def get_config(self):
        """Получение текущей конфигурации"""
        config = {
            "sections": [],
            "fields": {}
        }
        
        for section_key, section_checkbox in self.section_checkboxes.items():
            if section_checkbox.isChecked():
                config["sections"].append(section_key)
                
                selected_fields = []
                if section_key in self.field_checkboxes:
                    for field_key, checkbox in self.field_checkboxes[section_key].items():
                        if checkbox.isChecked() and checkbox.isEnabled():
                            selected_fields.append(field_key)
                
                config["fields"][section_key] = selected_fields
        
        return config
    
    def apply_config(self, config):
        """Применение конфигурации к чекбоксам"""
        sections = config.get("sections", [])
        fields_config = config.get("fields", {})
        
        for section_key, section_checkbox in self.section_checkboxes.items():
            is_in_sections = section_key in sections
            section_checkbox.setChecked(is_in_sections)
            self.on_section_toggled(section_key, 2 if is_in_sections else 0)
        
        for section_key, field_list in fields_config.items():
            if section_key in self.field_checkboxes:
                for field_key, checkbox in self.field_checkboxes[section_key].items():
                    if not field_list:
                        checkbox.setChecked(True)
                    else:
                        checkbox.setChecked(field_key in field_list)
        
        self.update_stats()
    
    def on_accept(self):
        """Обработка нажатия OK"""
        config = self.get_config()
        
        if not config.get("sections"):
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну секцию для отчета")
            return
        
        if not self.template_name and hasattr(self, 'template_name_input'):
            if not self.template_name_input.text().strip():
                QMessageBox.warning(self, "Ошибка", "Введите название шаблона")
                return
        
        self.accept()
    
    def get_template_name(self):
        """Получение имени шаблона (для новых шаблонов)"""
        if hasattr(self, 'template_name_input'):
            return self.template_name_input.text().strip()
        return self.template_name