"""
Виджет для управления составными полями
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import json
import traceback


# === СПРАВОЧНИК: DB колонка → Русское описание ===
COLUMN_DESCRIPTIONS = {
    # ========================
    # СОЦИАЛЬНО-ДЕМОГРАФИЧЕСКИЕ ДАННЫЕ (social_data)
    # ========================
    "surname": "Фамилия военнослужащего",
    "name": "Имя военнослужащего",
    "patronymic": "Отчество военнослужащего",
    "birth_date": "Дата рождения",
    "birth_place_town": "Населенный пункт места рождения (город, село)",
    "birth_place_district": "Район места рождения",
    "birth_place_region": "Субъект РФ места рождения (область, край, республика)",
    "birth_place_country": "Страна места рождения",
    "tab_number": "Табельный номер",
    "personal_number": "Личный номер",
    "category_name": "Категория военнослужащего (офицер, солдат и т.д.)",
    "rank_name": "Воинское звание",
    "drafted_by_commissariat": "Наименование военкомата призыва",
    "draft_date": "Дата призыва на военную службу",
    "povsk": "Наименование ПОВСК (пункт отбора на военную службу по контракту)",
    "selection_date": "Дата отбора на военную службу",
    "education": "Образование военнослужащего",
    "criminal_record": "Сведения о судимости",
    "social_media_account": "Аккаунты в социальных сетях",
    "bank_card_number": "Номер банковской карты",
    "passport_series": "Серия паспорта",
    "passport_number": "Номер паспорта",
    "passport_issue_date": "Дата выдачи паспорта",
    "passport_issued_by": "Кем выдан паспорт (наименование органа)",
    "military_id_series": "Серия военного билета",
    "military_id_number": "Номер военного билета",
    "military_id_issue_date": "Дата выдачи военного билета",
    "military_id_issued_by": "Кем выдан военный билет",
    "appearance_features": "Особенности внешности (рост, телосложение и т.д.)",
    "personal_marks": "Личные приметы (татуировки, шрамы, родимые пятна)",
    "federal_search_info": "Сведения о федеральном розыске",
    "military_contacts": "Контакты военнослужащего (телефон, email)",
    "relatives_info": "Сведения о близких родственниках (ФИО, контакты, адреса)",
    
    # ========================
    # АДРЕСА ПРОЖИВАНИЯ (addresses) - ВСЕ ПОЛЯ
    # ========================
    "region": "📍 Субъект РФ (область, край, республика, автономный округ)",
    "district": "📍 Административный район (район области/края)",
    "town": "📍 Населенный пункт (город, посёлок, село, деревня)",
    "street": "📍 Улица (наименование улицы, проспекта, переулка)",
    "house": "📍 Номер дома (основной номер здания)",
    "building": "📍 Номер корпуса (корпус, строение, владение)",
    "letter": "📍 Литера (буквенное обозначение здания: А, Б, В и т.д.)",
    "apartment": "📍 Номер квартиры (номер жилого помещения)",
    "room": "📍 Номер комнаты (номер комнаты в коммунальной квартире/общежитии)",
    "check_date": "📅 Дата проведения адресной проверки (когда проверяли адрес)",
    "check_result": "✅ Результат адресной проверки (найден, не найден, выбыл, иное)",
    
    # ========================
    # МЕСТА СЛУЖБЫ (service_places)
    # ========================
    "place_name": "🎖️ Наименование места службы (воинская часть, подразделение)",
    "military_unit_name": "🎖️ Воинское управление (ЦВО, ЮВО, ЗВО, ВДВ и т.д.)",
    "garrison_name": "🎖️ Гарнизон (наименование военного гарнизона)",
    "position_name": "🎖️ Воинская должность (наименование должности)",
    "commanders": "🎖️ Командиры (начальники) с контактами (ФИО, телефоны)",
    "postal_index": "📮 Почтовый индекс (цифровой код почтового отделения)",
    "postal_region": "📮 Субъект РФ почтового адреса (для корреспонденции)",
    "postal_district": "📮 Район почтового адреса",
    "postal_town": "📮 Населенный пункт почтового адреса (город для почты)",
    "postal_street": "📮 Улица почтового адреса",
    "postal_house": "📮 Дом почтового адреса",
    "postal_building": "📮 Корпус почтового адреса",
    "postal_letter": "📮 Литера почтового адреса",
    "postal_apartment": "📮 Квартира почтового адреса",
    "postal_room": "📮 Комната почтового адреса",
    "place_contacts": "📞 Контакты места службы (телефоны, email)",
    
    # ========================
    # ЭПИЗОДЫ СОЧ (soch_episodes)
    # ========================
    "soch_date": "⚠️ Дата самовольного оставления части (когда ушёл)",
    "soch_location": "⚠️ Место СОЧ (откуда ушёл: часть, КПП, увольнение и т.д.)",
    "order_date_number": "⚠️ Дата и номер приказа о СОЧ (приказ об объявлении в розыск)",
    "witnesses": "⚠️ Очевидцы СОЧ (ФИО, контакты свидетелей)",
    "reasons": "⚠️ Вероятные причины СОЧ (мотивы, обстоятельства)",
    "weapon_info": "⚠️ Сведения о наличии оружия (что было при себе)",
    "clothing": "⚠️ Описание одежды (во что был одет при уходе)",
    "movement_options": "⚠️ Возможные направления движения (куда мог направиться)",
    "other_info": "⚠️ Другая значимая информация (дополнительные сведения)",
    "duty_officer_commissariat": "📞 Дежурный по военкомату (ФИО, телефон)",
    "duty_officer_omvd": "📞 Дежурный по ОМВД (ФИО, телефон)",
    "investigation_info": "📋 Сведения о проверке (кто проводит, статус)",
    "prosecution_info": "📋 Сведения о прокуратуре (контакты, номер дела)",
    "criminal_case_info": "📋 Сведения об уголовном деле (номер, статья УК)",
    "search_date": "🔍 Дата розыска (когда начаты розыскные мероприятия)",
    "found_by": "✅ Кем разыскан (кто обнаружил: полиция, часть, граждане)",
    "search_circumstances": "🔍 Обстоятельства розыска (где и как найден)",
    "notification_recipient": "📬 Адресат уведомления (кому отправлено уведомление)",
    "notification_date": "📅 Дата уведомления (когда отправлено)",
    "notification_number": "📬 Номер уведомления (исходящий номер документа)"
}

# === ОБРАТНЫЙ СПРАВОЧНИК: Русское описание → DB колонка ===
DESCRIPTION_TO_COLUMN = {v: k for k, v in COLUMN_DESCRIPTIONS.items()}


class CompositeFieldWidget:
    """Управление интерфейсом составных полей"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def _create_column_combo(self, selected_column=None, table_name=None):
        """Создание ComboBox с русскими описаниями колонок"""
        combo = QComboBox()
        combo.setEditable(False)
        combo.setMinimumWidth(200)
        
        # Собираем все доступные колонки
        all_columns = []
        
        if table_name and table_name in self.parent.db_columns:
            # Если указана таблица, используем только её колонки
            for col in self.parent.db_columns[table_name]:
                if col in COLUMN_DESCRIPTIONS:
                    all_columns.append((col, COLUMN_DESCRIPTIONS[col]))
                else:
                    all_columns.append((col, col))
        else:
            # Иначе используем все колонки из всех таблиц
            for table, columns in self.parent.db_columns.items():
                for col in columns:
                    if col in COLUMN_DESCRIPTIONS:
                        all_columns.append((col, COLUMN_DESCRIPTIONS[col]))
                    else:
                        all_columns.append((col, col))
        
        # Сортируем по описанию
        all_columns.sort(key=lambda x: x[1])
        
        # Добавляем в ComboBox: отображаем описание, храним имя колонки
        for col_name, col_description in all_columns:
            combo.addItem(col_description, col_name)
        
        # Выбираем нужную колонку
        if selected_column:
            index = combo.findData(selected_column)
            if index >= 0:
                combo.setCurrentIndex(index)
        
        return combo
    
    def create_composite_field_row(self, row, field_name, db_columns_json, table_name, mapping_table):
        """Создание строки для составного сопоставления"""
        print(f"📝 CompositeFieldWidget.create_composite_field_row(row={row}, field={field_name})")
        
        try:
            # ✅ ВАЖНО: Сначала вставляем строку в таблицу!
            mapping_table.insertRow(row)
            print(f"   ✅ Строка {row} вставлена в таблицу")
            
            # 1. Переменная из шаблона
            var_combo = QComboBox()
            var_combo.addItems(self.parent.template_variables)
            var_combo.setCurrentText(field_name)
            
            # 2. Контейнер для составных столбцов
            composite_widget = QWidget()
            composite_layout = QVBoxLayout(composite_widget)
            composite_layout.setContentsMargins(5, 5, 5, 5)
            composite_layout.setSpacing(5)
            
            db_columns = json.loads(db_columns_json) if isinstance(db_columns_json, str) else db_columns_json
            if not db_columns:
                db_columns = [{'column': '', 'separator': ', '}]
            
            print(f"   Столбцов в JSON: {len(db_columns)}")
            
            for idx, col_info in enumerate(db_columns):
                # ✅ ИСПРАВЛЕНО: Используем _create_column_combo с русскими описаниями
                col_widget = self._create_composite_column_widget(
                    row, idx, col_info, table_name, use_russian_descriptions=True
                )
                composite_layout.addWidget(col_widget)
            
            # 3. Кнопка добавления столбца
            self._add_add_column_button(composite_layout, row, table_name)
            
            # 4. Установка виджетов в таблицу
            mapping_table.setCellWidget(row, 0, var_combo)
            mapping_table.setCellWidget(row, 1, composite_widget)
            mapping_table.setCellWidget(row, 2, self._create_type_label("Составное"))
            mapping_table.resizeRowToContents(row)
            
            # ✅ ПРОВЕРКА: что было создано
            var_w = mapping_table.cellWidget(row, 0)
            col_w = mapping_table.cellWidget(row, 1)
            type_w = mapping_table.cellWidget(row, 2)
            
            if var_w and col_w and type_w:
                print(f"✅ Строка создана успешно")
                print(f"   var_combo: {var_w.currentText()}")
                print(f"   composite_widget: {col_w}")
                print(f"   type_label: {type_w.text()}")
            else:
                print(f"❌ ОШИБКА: виджеты не созданы!")
                print(f"   var_w={var_w}, col_w={col_w}, type_w={type_w}")
            
        except Exception as e:
            print(f"❌ Ошибка создания строки: {e}")
            traceback.print_exc()
    
    def _create_composite_column_widget(self, row, idx, col_info, table_name, use_russian_descriptions=True):
        """Создание виджета одного столбца в составном поле"""
        col_widget = QWidget()
        col_layout = QHBoxLayout(col_widget)
        col_layout.setContentsMargins(8, 5, 8, 5)
        col_layout.setSpacing(8)
        
        # Номер столбца
        num_label = QLabel(f"{idx + 1}.")
        num_label.setStyleSheet("font-weight: bold; color: #2196F3; min-width: 20px;")
        num_label.setObjectName(f"num_{row}_{idx}")
        col_layout.addWidget(num_label)
        
        # ✅ ИСПРАВЛЕНО: Выбор столбца БД с русскими описаниями
        if use_russian_descriptions:
            col_combo = self._create_column_combo(
                selected_column=col_info.get('column', ''),
                table_name=table_name
            )
        else:
            # Старый режим (технические имена)
            col_combo = QComboBox()
            col_combo.setMinimumWidth(150)
            if table_name in self.parent.db_columns:
                col_combo.addItems(self.parent.db_columns[table_name])
            col_combo.setCurrentText(col_info.get('column', ''))
        
        col_combo.setObjectName(f"col_{row}_{idx}")
        col_layout.addWidget(col_combo, 2)
        
        # Разделитель
        sep_label = QLabel("Разделитель:")
        sep_label.setStyleSheet("color: #666; font-size: 10px;")
        col_layout.addWidget(sep_label)
        
        sep_input = QLineEdit()
        sep_input.setText(col_info.get('separator', ', '))
        sep_input.setFixedWidth(70)
        sep_input.setObjectName(f"sep_{row}_{idx}")
        sep_input.setStyleSheet("QLineEdit { border: 1px solid #ddd; border-radius: 3px; padding: 2px; }")
        col_layout.addWidget(sep_input)
        
        # Кнопка удаления
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(26, 26)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border-radius: 13px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        
        remove_btn.clicked.connect(
            lambda checked=False, r=row, i=idx, w=col_widget: self._remove_composite_column(r, i, w)
        )
        col_layout.addWidget(remove_btn)
        
        return col_widget
    
    def _remove_composite_column(self, row, idx, widget_to_remove):
        """Удаление столбца из составного поля"""
        print(f"🗑️ Удаление столбца #{idx + 1} из строки {row}")
        
        composite_widget = self.parent.mapping_table.cellWidget(row, 1)
        if not composite_widget:
            print("❌ Ошибка: composite_widget не найден")
            return
        
        layout = composite_widget.layout()
        if not layout:
            print("❌ Ошибка: layout не найден")
            return
        
        if layout.count() <= 2:
            QMessageBox.warning(self.parent, "Внимание", "Нельзя удалить последний столбец.")
            return
        
        layout.removeWidget(widget_to_remove)
        widget_to_remove.deleteLater()
        self._update_column_numbers(layout)
        self.parent.mapping_table.resizeRowToContents(row)
        print(f"✅ Столбец #{idx + 1} удален")
    
    def _update_column_numbers(self, layout):
        """Обновление номеров всех столбцов"""
        for i in range(layout.count() - 1):
            widget = layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                col_layout = widget.layout()
                if col_layout and col_layout.count() > 0:
                    num_label = col_layout.itemAt(0).widget()
                    if isinstance(num_label, QLabel):
                        num_label.setText(f"{i + 1}.")
    
    def _add_add_column_button(self, layout, row, table_name=None):
        """Добавление кнопки добавления столбца"""
        add_btn_container = QWidget()
        add_btn_layout = QHBoxLayout(add_btn_container)
        add_btn_layout.setContentsMargins(0, 8, 0, 0)
        
        # ✅ ИСПРАВЛЕНО: PyQt6 синтаксис для QSizePolicy
        add_btn_layout.addSpacerItem(QSpacerItem(40, 20, 
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Minimum
        ))
        
        add_col_btn = QPushButton("+ Добавить столбец")
        add_col_btn.setFixedSize(140, 28)
        add_col_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """)
        add_col_btn.clicked.connect(lambda checked=False, r=row: self.add_composite_column(r, table_name))
        add_btn_layout.addWidget(add_col_btn)
        
        layout.addWidget(add_btn_container)
        layout.addStretch()
    
    def add_composite_column(self, row, table_name=None):
        """Добавление нового столбца в составное сопоставление"""
        print(f"➕ Добавление столбца в строку {row}")
        
        composite_widget = self.parent.mapping_table.cellWidget(row, 1)
        if not composite_widget:
            print("❌ Ошибка: composite_widget не найден")
            return
        
        layout = composite_widget.layout()
        if not layout:
            print("❌ Ошибка: layout не найден")
            return
        
        idx = layout.count() - 2 if layout.count() >= 2 else 0
        col_info = {'column': '', 'separator': ', '}
        
        # ✅ ИСПРАВЛЕНО: Используем _create_column_combo с русскими описаниями
        col_widget = self._create_composite_column_widget(
            row, idx, col_info, table_name or self.parent.current_table_name,
            use_russian_descriptions=True
        )
        
        button_container = layout.itemAt(layout.count() - 2).widget() if layout.count() >= 2 else None
        if button_container:
            layout.insertWidget(layout.count() - 2, col_widget)
        else:
            layout.addWidget(col_widget)
        
        self._update_column_numbers(layout)
        self.parent.mapping_table.resizeRowToContents(row)
        print(f"✅ Столбец добавлен")
    
    def add_composite_field_mapping(self, row):
        """Добавление составного сопоставления"""
        print(f"📝 CompositeFieldWidget.add_composite_field_mapping(row={row})")
        
        mapping_table = self.parent.mapping_table
        
        # ✅ ВАЖНО: Сначала вставляем строку в таблицу!
        mapping_table.insertRow(row)
        print(f"   ✅ Строка {row} вставлена в таблицу")
        
        # Переменная из шаблона
        var_combo = QComboBox()
        var_combo.addItems(self.parent.template_variables)
        mapping_table.setCellWidget(row, 0, var_combo)
        
        # Контейнер для составных столбцов
        composite_widget = QWidget()
        composite_layout = QVBoxLayout(composite_widget)
        composite_layout.setContentsMargins(5, 5, 5, 5)
        composite_layout.setSpacing(5)
        
        # Добавляем первый столбец
        col_info = {'column': '', 'separator': ', '}
        
        # ✅ ИСПРАВЛЕНО: Используем _create_column_combo с русскими описаниями
        col_widget = self._create_composite_column_widget(
            row, 0, col_info, self.parent.current_table_name,
            use_russian_descriptions=True
        )
        composite_layout.addWidget(col_widget)
        
        # Кнопка добавления столбца
        self._add_add_column_button(composite_layout, row, self.parent.current_table_name)
        
        mapping_table.setCellWidget(row, 1, composite_widget)
        mapping_table.setCellWidget(row, 2, self._create_type_label("Составное"))
        mapping_table.resizeRowToContents(row)
        mapping_table.selectRow(row)
        
        print(f"✅ Составное поле добавлено")
    
    def _create_type_label(self, text):
        """Создание метки типа сопоставления"""
        type_label = QLabel(text)
        type_label.setStyleSheet(
            "color: #4CAF50; font-weight: bold; font-size: 10px;" if text == "Составное" 
            else "color: #666; font-size: 10px;"
        )
        return type_label
    
    def get_composite_columns(self, composite_widget):
        """Получение списка составных столбцов из виджета"""
        print(f"🔍 get_composite_columns()")
        
        db_columns = []
        layout = composite_widget.layout()
        
        if not layout:
            print("   ⚠️ layout не найден")
            return db_columns
        
        print(f"   Элементов в layout: {layout.count()}")
        
        for i in range(layout.count() - 1):
            col_widget = layout.itemAt(i).widget()
            if not col_widget:
                print(f"   [{i}] ⚠️ col_widget не найден")
                continue
            
            col_layout = col_widget.layout()
            if not col_layout:
                print(f"   [{i}] ⚠️ col_layout не найден")
                continue
            
            print(f"   [{i}] Элементов в col_layout: {col_layout.count()}")
            
            col_combo = None
            sep_input = None
            
            for j in range(col_layout.count()):
                item = col_layout.itemAt(j)
                if item:
                    widget = item.widget()
                    if isinstance(widget, QComboBox):
                        col_combo = widget
                        # ✅ ИСПРАВЛЕНО: Используем currentData() для получения технического имени
                        print(f"       [{j}] QComboBox: {widget.currentText()} ( {widget.currentData()})")
                    elif isinstance(widget, QLineEdit):
                        sep_input = widget
                        print(f"       [{j}] QLineEdit: {widget.text() if widget else 'None'}")
            
            if col_combo and sep_input:
                # ✅ ИСПРАВЛЕНО: Используем currentData() вместо currentText()
                column_name = col_combo.currentData() if col_combo.currentData() else col_combo.currentText()
                separator = sep_input.text()
                print(f"   [{i}] ✅ {column_name} (sep: '{separator}')")
                if column_name:
                    db_columns.append({'column': column_name, 'separator': separator})
            else:
                print(f"   [{i}] ⚠️ col_combo={col_combo}, sep_input={sep_input}")
        
        print(f"   ✅ Возвращено {len(db_columns)} столбцов")
        return db_columns