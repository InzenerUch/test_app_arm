"""
Виджет для управления составными полями (Composite Fields)
✅ Динамическая загрузка колонок, поддержка русских описаний, прокрутка, безопасное управление layout
✅ ДОБАВЛЕНО: SearchableComboBox для поиска полей
"""
import json
import traceback
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from searchable_combo import SearchableComboBox  # ✅ ИМПОРТ НОВОГО КЛАССА

# === СПРАВОЧНИК: DB колонка → Русское описание ===
COLUMN_DESCRIPTIONS = {
    # ========================
    # СОЦИАЛЬНО-ДЕМОГРАФИЧЕСКИЕ ДАННЫЕ (social_data) - 38 полей
    # ========================
    "id": "ID записи",
    "krd_id": "ID карточки розыска",
    "surname": "Фамилия военнослужащего",
    "name": "Имя военнослужащего",
    "patronymic": "Отчество военнослужащего",
    "birth_date": "Дата рождения",
    "birth_place_town": "Населенный пункт места рождения",
    "birth_place_district": "Район места рождения",
    "birth_place_region": "Субъект РФ места рождения",
    "birth_place_country": "Страна места рождения",
    "tab_number": "Табельный номер",
    "personal_number": "Личный номер",
    "category_id": "ID категории военнослужащего",
    "rank_id": "ID воинского звания",
    "drafted_by_commissariat": "Наименование военкомата призыва",
    "draft_date": "Дата призыва на военную службу",
    "povsk": "Наименование ПОВСК",
    "selection_date": "Дата отбора на военную службу",
    "education": "Образование военнослужащего",
    "criminal_record": "Сведения о судимости",
    "social_media_account": "Аккаунты в социальных сетях",
    "bank_card_number": "Номер банковской карты",
    "passport_series": "Серия паспорта",
    "passport_number": "Номер паспорта",
    "passport_issue_date": "Дата выдачи паспорта",
    "passport_issued_by": "Кем выдан паспорт",
    "military_id_series": "Серия военного билета",
    "military_id_number": "Номер военного билета",
    "military_id_issue_date": "Дата выдачи военного билета",
    "military_id_issued_by": "Кем выдан военный билет",
    "appearance_features": "Особенности внешности",
    "personal_marks": "Личные приметы (татуировки, шрамы)",
    "federal_search_info": "Сведения о федеральном розыске",
    "military_contacts": "Контакты военнослужащего",
    "relatives_info": "Сведения о близких родственниках",
    "photo_civilian": "Фото в гражданской одежде",
    "photo_military_headgear": "Фото в форме с головным убором",
    "photo_military_no_headgear": "Фото в форме без головного убора",
    "photo_distinctive_marks": "Фото отличительных примет",
    # ========================
    # АДРЕСА ПРОЖИВАНИЯ (addresses) - 13 полей
    # ========================
    "region": "📍 Субъект РФ (область, край, республика)",
    "district": "📍 Административный район",
    "town": "📍 Населенный пункт (город, село)",
    "street": "📍 Улица",
    "house": "📍 Номер дома",
    "building": "📍 Номер корпуса",
    "letter": "📍 Литера здания",
    "apartment": "📍 Номер квартиры",
    "room": "📍 Номер комнаты",
    "check_date": "📅 Дата адресной проверки",
    "check_result": "✅ Результат проверки",
    # ========================
    # МЕСТА СЛУЖБЫ (service_places) - 18 полей
    # ========================
    "place_name": "🎖️ Наименование места службы",
    "military_unit_id": "🎖️ ID военного управления",
    "garrison_id": "🎖️ ID гарнизона",
    "position_id": "🎖️ ID воинской должности",
    "commanders": "🎖️ Командиры (ФИО, контакты)",
    "postal_index": "📮 Почтовый индекс",
    "postal_region": "📮 Субъект РФ почтового адреса",
    "postal_district": "📮 Район почтового адреса",
    "postal_town": "📮 Город почтового адреса",
    "postal_street": "📮 Улица почтового адреса",
    "postal_house": "📮 Дом почтового адреса",
    "postal_building": "📮 Корпус почтового адреса",
    "postal_letter": "📮 Литера почтового адреса",
    "postal_apartment": "📮 Квартира почтового адреса",
    "postal_room": "📮 Комната почтового адреса",
    "place_contacts": "📞 Контакты места службы",
    # ========================
    # ЭПИЗОДЫ СОЧ (soch_episodes) - 22 поля
    # ========================
    "soch_date": "⚠️ Дата СОЧ",
    "soch_location": "⚠️ Место СОЧ",
    "order_date_number": "⚠️ Дата и номер приказа о СОЧ",
    "witnesses": "⚠️ Очевидцы СОЧ",
    "reasons": "⚠️ Вероятные причины СОЧ",
    "weapon_info": "⚠️ Сведения о наличии оружия",
    "clothing": "⚠️ Описание одежды",
    "movement_options": "⚠️ Возможные направления движения",
    "other_info": "⚠️ Другая значимая информация",
    "duty_officer_commissariat": "📞 Дежурный по военкомату",
    "duty_officer_omvd": "📞 Дежурный по ОМВД",
    "investigation_info": "📋 Сведения о проверке",
    "prosecution_info": "📋 Сведения о прокуратуре",
    "criminal_case_info": "📋 Сведения об уголовном деле",
    "search_date": "🔍 Дата розыска",
    "found_by": "✅ Кем разыскан",
    "search_circumstances": "🔍 Обстоятельства розыска",
    "notification_recipient": "📬 Адресат уведомления",
    "notification_date": "📅 Дата уведомления",
    "notification_number": "📬 Номер уведомления",
    # ========================
    # ВХОДЯЩИЕ ПОРУЧЕНИЯ (incoming_orders) - 22 поля
    # ========================
    "initiator_type_id": "📩 ID типа инициатора",
    "initiator_full_name": "📩 Наименование инициатора",
    "military_unit_id": "📩 ID военного управления",
    "order_date": "📩 Дата поручения",
    "order_number": "📩 Номер поручения",
    "receipt_date": "📩 Дата поступления",
    "receipt_number": "📩 Входящий номер",
    "initiator_contacts": "📩 Контакты инициатора",
    "our_response_date": "📩 Дата ответа",
    "our_response_number": "📩 Исходящий номер ответа",
    # ========================
    # ИСХОДЯЩИЕ ЗАПРОСЫ (outgoing_requests) - 23 поля
    # ========================
    "request_type_id": "📤 ID типа запроса",
    "recipient_name": "📤 Наименование адресата",
    "issue_date": "📤 Дата запроса",
    "issue_number": "📤 Номер запроса",
    "request_text": "📤 Текст запроса",
    "signed_by_position": "📤 Должность подписанта",
    "document_data": "📄 Данные документа",
    "recipient_contacts": "📬 Контакты адресата",
}

# === ОБРАТНЫЙ СПРАВОЧНИК: Русское описание → DB колонка ===
DESCRIPTION_TO_COLUMN = {v: k for k, v in COLUMN_DESCRIPTIONS.items()}


class CompositeFieldWidget:
    """Управление интерфейсом составных полей"""
    
    def __init__(self, parent):
        self.parent = parent
        if not hasattr(parent, 'db_columns'):
            print("⚠️ [CompositeFieldWidget] Предупреждение: у родителя нет атрибута 'db_columns'")
            parent.db_columns = {}
    
    def _create_column_combo(self, selected_column=None, table_name=None):
        """Создание ComboBox с русскими описаниями колонок и поиском"""
        try:
            print(f"\n{'='*60}")
            print(f"🔧 СОЗДАНИЕ COMBOBOX ДЛЯ СОСТАВНОГО ПОЛЯ")
            print(f"{'='*60}")
            
            combo = SearchableComboBox()
            
            if combo is None:
                print("❌ ОШИБКА: Не удалось создать SearchableComboBox!")
                return None
            
            print(f"✅ SearchableComboBox создан: {combo}")
            print(f"   Тип: {type(combo).__name__}")
            print(f"   Редактируемый: {combo.isEditable()}")
            
            combo.setMaxVisibleItems(50)
            combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            combo.view().setMinimumHeight(400)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumWidth(350)
            combo.setMaximumWidth(600)
            
            # ✅ ИСПРАВЛЕНО: completer() — это метод в PyQt6!
            completer = combo.completer()
            if completer:
                print(f"✅ Completer настроен")
                print(f"   CaseSensitivity: {completer.caseSensitivity()}")
                print(f"   FilterMode: {completer.filterMode()}")
                print(f"   CompletionMode: {completer.completionMode()}")
            else:
                print("❌ ОШИБКА: Completer не создан!")
            
            all_columns = []
            seen = set()
            
            target_tables = self.parent.db_columns.keys()
            print(f"🔍 Загрузка колонок из таблиц: {list(target_tables)}")
            
            for tbl in target_tables:
                columns = self.parent.db_columns.get(tbl, [])
                print(f"   📊 Таблица {tbl}: {len(columns)} колонок")
                for col in columns:
                    if col in seen:
                        continue
                    seen.add(col)
                    desc = COLUMN_DESCRIPTIONS.get(col, col)
                    all_columns.append((col, desc))
            
            all_columns.sort(key=lambda x: x[1])
            
            print(f"\n📊 Добавление {len(all_columns)} колонок в ComboBox...")
            
            for col_name, col_desc in all_columns:
                combo.addItem(col_desc, col_name)
            
            print(f"✅ [COMBO] Загружено: {combo.count()} столбцов (ВСЕ таблицы)")
            
            if selected_column:
                idx = combo.findData(selected_column.strip())
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                    print(f"✅ Выбран элемент: {combo.currentText()} (data={combo.currentData()})")
                else:
                    print(f"⚠️ Колонка '{selected_column}' не найдена в списке!")
            
            if combo.count() == 0:
                print("❌ ОШИБКА: ComboBox пуст!")
            else:
                print(f"✅ ComboBox готов к использованию")
                print(f"   Всего элементов: {combo.count()}")
            
            print(f"{'='*60}\n")
            return combo
            
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при создании ComboBox: {e}")
            import traceback
            traceback.print_exc()
            
            print("⚠️ Создаем fallback ComboBox...")
            combo = QComboBox()
            combo.addItem("Ошибка загрузки", None)
            return combo
    
    def create_composite_field_row(self, row, field_name, db_columns_json, table_name, mapping_table):
        """Создание строки для составного сопоставления (при загрузке из БД)"""
        try:
            mapping_table.insertRow(row)
            
            # 1. Переменная из шаблона
            var_combo = QComboBox()
            vars_list = getattr(self.parent, 'template_variables', [])
            var_combo.addItems(vars_list if vars_list else [])
            var_combo.setCurrentText(field_name)
            var_combo.setMinimumWidth(200)
            
            # 2. Контейнер для составных столбцов
            composite_widget = QWidget()
            composite_layout = QVBoxLayout(composite_widget)
            composite_layout.setContentsMargins(5, 5, 5, 5)
            composite_layout.setSpacing(5)
            
            # Парсим JSON
            db_columns = json.loads(db_columns_json) if isinstance(db_columns_json, str) else db_columns_json
            if not db_columns:
                db_columns = [{'column': '', 'separator': ', '}]
            
            for idx, col_info in enumerate(db_columns):
                col_widget = self._create_composite_column_widget(row, idx, col_info, table_name)
                composite_layout.addWidget(col_widget)
            
            self._add_add_column_button(composite_layout, row, table_name)
            
            # 3. Установка в таблицу
            mapping_table.setCellWidget(row, 0, var_combo)
            mapping_table.setCellWidget(row, 1, composite_widget)
            mapping_table.setCellWidget(row, 2, self._create_type_label("Составное"))
            mapping_table.resizeRowToContents(row)
            
        except Exception as e:
            print(f"❌ Ошибка создания строки составного поля: {e}")
            traceback.print_exc()
    
    def _create_composite_column_widget(self, row, idx, col_info, table_name):
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
        
        # ✅ ComboBox с колонками (теперь показывает ВСЕ таблицы с поиском)
        col_combo = self._create_column_combo(
            selected_column=col_info.get('column', ''),
            table_name=None  # ← Игнорируем table_name, показываем все таблицы
        )
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
        composite_widget = self.parent.mapping_table.cellWidget(row, 1)
        if not composite_widget:
            return
        
        layout = composite_widget.layout()
        if not layout:
            return
        
        # Защита: не удаляем, если остался 1 столбец (плюс контейнер кнопки и stretch)
        if layout.count() <= 3:
            QMessageBox.warning(self.parent, "Внимание", "Нельзя удалить последний столбец.")
            return
        
        layout.removeWidget(widget_to_remove)
        widget_to_remove.deleteLater()
        self._update_column_numbers(layout)
        self.parent.mapping_table.resizeRowToContents(row)
    
    def _update_column_numbers(self, layout):
        """Обновление номеров всех столбцов после удаления/добавления"""
        num_idx = 1
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue
            w = item.widget()
            if not w:
                continue
            # Проверяем, является ли виджет контейнером столбца (есть вложенный layout с номером)
            if w.layout() and w.layout().count() > 0:
                num_label = w.layout().itemAt(0).widget()
                if isinstance(num_label, QLabel) and num_label.text().endswith('.'):
                    num_label.setText(f"{num_idx}.")
                    num_label.setObjectName(f"num_updated_{num_idx}")
                    num_idx += 1
    
    def _add_add_column_button(self, layout, row, table_name=None):
        """Добавление кнопки добавления столбца в конец layout"""
        add_btn_container = QWidget()
        add_btn_layout = QHBoxLayout(add_btn_container)
        add_btn_layout.setContentsMargins(0, 8, 0, 0)
        add_btn_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
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
            QPushButton:hover { 
                background-color: #45a049; 
            }
            QPushButton:pressed { 
                background-color: #3d8b40; 
            }
        """)
        add_col_btn.clicked.connect(lambda checked=False, r=row: self.add_composite_column(r, table_name))
        add_btn_layout.addWidget(add_col_btn)
        layout.addWidget(add_btn_container)
        layout.addStretch()
    
    def add_composite_column(self, row, table_name=None):
        """Добавление нового столбца в составное сопоставление"""
        composite_widget = self.parent.mapping_table.cellWidget(row, 1)
        if not composite_widget:
            return
        
        layout = composite_widget.layout()
        if not layout:
            return
        
        # Определяем текущий индекс (количество столбцов минус кнопка и stretch)
        current_idx = layout.count() - 2 if layout.count() >= 2 else 0
        col_info = {'column': '', 'separator': ', '}
        
        # Безопасное получение имени таблицы
        tbl_name = table_name or getattr(self.parent, 'current_table_name', 'social_data')
        col_widget = self._create_composite_column_widget(row, current_idx, col_info, tbl_name)
        
        # Вставляем ПЕРЕД кнопкой добавления
        button_container_idx = -2
        layout.insertWidget(button_container_idx, col_widget)
        self._update_column_numbers(layout)
        self.parent.mapping_table.resizeRowToContents(row)
    
    def add_composite_field_mapping(self, row):
        """Добавление составного сопоставления (новая строка)"""
        mapping_table = self.parent.mapping_table
        mapping_table.insertRow(row)
        
        # Переменная
        var_combo = QComboBox()
        vars_list = getattr(self.parent, 'template_variables', [])
        var_combo.addItems(vars_list if vars_list else [])
        var_combo.setMinimumWidth(200)
        mapping_table.setCellWidget(row, 0, var_combo)
        
        # Контейнер
        composite_widget = QWidget()
        composite_layout = QVBoxLayout(composite_widget)
        composite_layout.setContentsMargins(5, 5, 5, 5)
        composite_layout.setSpacing(5)
        
        tbl_name = getattr(self.parent, 'current_table_name', 'social_data')
        col_info = {'column': '', 'separator': ', '}
        col_widget = self._create_composite_column_widget(row, 0, col_info, tbl_name)
        composite_layout.addWidget(col_widget)
        self._add_add_column_button(composite_layout, row, tbl_name)
        
        mapping_table.setCellWidget(row, 1, composite_widget)
        mapping_table.setCellWidget(row, 2, self._create_type_label("Составное"))
        mapping_table.resizeRowToContents(row)
        mapping_table.selectRow(row)
    
    def _create_type_label(self, text):
        """Создание метки типа сопоставления"""
        type_label = QLabel(text)
        type_label.setStyleSheet(
            "color: #4CAF50; font-weight: bold; font-size: 10px;" if text == "Составное"
            else "color: #666; font-size: 10px;"
        )
        return type_label
    
    def get_composite_columns(self, composite_widget):
        """
        Получение списка составных столбцов из виджета (для сохранения в БД)
        Возвращает: [{'column': 'town', 'separator': ', '}, ...]
        """
        db_columns = []
        layout = composite_widget.layout()
        if not layout:
            return db_columns
        
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue
            col_widget = item.widget()
            if not col_widget or not col_widget.layout():
                continue
            
            col_combo = None
            sep_input = None
            
            for j in range(col_widget.layout().count()):
                w = col_widget.layout().itemAt(j).widget()
                if isinstance(w, QComboBox):
                    col_combo = w
                elif isinstance(w, QLineEdit):
                    sep_input = w
            
            if col_combo and sep_input:
                # ✅ currentData() возвращает техническое имя колонки (скрытое в addItem)
                col_name = col_combo.currentData()
                if not col_name and col_combo.count() > 0:
                    col_name = col_combo.currentText()  # Fallback
                separator = sep_input.text()
                if col_name:
                    db_columns.append({'column': col_name.strip(), 'separator': separator})
        
        return db_columns