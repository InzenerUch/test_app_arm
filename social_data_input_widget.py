from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QDateEdit, QComboBox, QFileDialog,
    QPushButton, QScrollArea, QFrame, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QDate, QByteArray, QRegularExpression
from PyQt6.QtGui import QFont, QPixmap, QRegularExpressionValidator
from PyQt6.QtSql import QSqlQuery
import os
import traceback

# Импорт вспомогательного модуля из проекта
from autocomplete_helper import AutocompleteHelper


class SocialDataInputWidget(QWidget):
    """Виджет ввода социально-демографических данных для создания КРД"""
    
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.parent_window = parent # Сохраняем ссылку на родительское окно
        self.photo_paths = {
            'civilian': None, 'military_headgear': None,
            'military_no_headgear': None, 'distinctive_marks': None
        }
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        
        self.init_ui()
        self.load_combo_data()
        self._setup_validators_and_autocomplete()

    def init_ui(self):
        """Инициализация интерфейса"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # === Группа 1: Основные данные ===
        g1 = QGroupBox("👤 Основные данные (поля со знаком * обязательны)")
        g1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l1 = QGridLayout(); l1.setSpacing(8)
        
        self.surname_input = QLineEdit(); self.surname_input.setPlaceholderText("Фамилия")
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Имя")
        self.patronymic_input = QLineEdit(); self.patronymic_input.setPlaceholderText("Отчество")
        self.tab_number_input = QLineEdit(); self.tab_number_input.setPlaceholderText("Например: 123456")
        self.personal_number_input = QLineEdit(); self.personal_number_input.setPlaceholderText("Личный номер")
        self.category_combo = QComboBox()
        self.rank_combo = QComboBox()
        
        l1.addWidget(QLabel("Фамилия *:"), 0, 0); l1.addWidget(self.surname_input, 0, 1)
        l1.addWidget(QLabel("Имя *:"), 0, 2); l1.addWidget(self.name_input, 0, 3)
        l1.addWidget(QLabel("Отчество *:"), 0, 4); l1.addWidget(self.patronymic_input, 0, 5)
        l1.addWidget(QLabel("Табельный номер:"), 1, 0); l1.addWidget(self.tab_number_input, 1, 1)
        l1.addWidget(QLabel("Личный номер:"), 1, 2); l1.addWidget(self.personal_number_input, 1, 3)
        
        # ✅ ИЗМЕНЕНО: Добавляем кнопки настроек для Категории
        l1.addWidget(QLabel("Категория:"), 2, 0)
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(self.category_combo)
        btn_cat = QPushButton("⚙️")
        btn_cat.setToolTip("Настроить справочник категорий")
        btn_cat.setFixedSize(32, 32)
        btn_cat.setStyleSheet("QPushButton { font-weight: bold; }")
        btn_cat.clicked.connect(lambda: self.open_ref_editor('categories'))
        cat_layout.addWidget(btn_cat)
        l1.addLayout(cat_layout, 2, 1)
        
        # ✅ ИЗМЕНЕНО: Добавляем кнопки настроек для Звания
        l1.addWidget(QLabel("Звание:"), 2, 2)
        rank_layout = QHBoxLayout()
        rank_layout.addWidget(self.rank_combo)
        btn_rank = QPushButton("⚙️")
        btn_rank.setToolTip("Настроить справочник званий")
        btn_rank.setFixedSize(32, 32)
        btn_rank.setStyleSheet("QPushButton { font-weight: bold; }")
        btn_rank.clicked.connect(lambda: self.open_ref_editor('ranks'))
        rank_layout.addWidget(btn_rank)
        l1.addLayout(rank_layout, 2, 3)
        
        g1.setLayout(l1); layout.addWidget(g1)

        # === Группа 2: Место рождения ===
        g2 = QGroupBox("🌍 Место рождения")
        g2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l2 = QGridLayout(); l2.setSpacing(8)
        
        self.birth_place_town_input = QLineEdit()
        self.birth_place_district_input = QLineEdit()
        self.birth_place_region_input = QLineEdit()
        self.birth_place_country_input = QLineEdit()
        self.birth_date_input = QDateEdit(); self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setMaximumDate(QDate.currentDate())
        
        l2.addWidget(QLabel("Населенный пункт:"), 0, 0); l2.addWidget(self.birth_place_town_input, 0, 1)
        l2.addWidget(QLabel("Район:"), 0, 2); l2.addWidget(self.birth_place_district_input, 0, 3)
        l2.addWidget(QLabel("Регион:"), 1, 0); l2.addWidget(self.birth_place_region_input, 1, 1)
        l2.addWidget(QLabel("Страна:"), 1, 2); l2.addWidget(self.birth_place_country_input, 1, 3)
        l2.addWidget(QLabel("Дата рождения:"), 2, 0); l2.addWidget(self.birth_date_input, 2, 1)
        g2.setLayout(l2); layout.addWidget(g2)

        # === Группа 3: Призыв и отбор ===
        g3 = QGroupBox("🎖️ Призыв и отбор")
        g3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l3 = QGridLayout(); l3.setSpacing(8)
        
        self.drafted_by_commissariat_input = QLineEdit()
        self.draft_date_input = QDateEdit(); self.draft_date_input.setCalendarPopup(True)
        self.draft_date_input.setMaximumDate(QDate.currentDate())
        self.povsk_input = QLineEdit()
        self.selection_date_input = QDateEdit(); self.selection_date_input.setCalendarPopup(True)
        self.selection_date_input.setMaximumDate(QDate.currentDate())
        
        l3.addWidget(QLabel("Комиссариат:"), 0, 0); l3.addWidget(self.drafted_by_commissariat_input, 0, 1, 1, 3)
        l3.addWidget(QLabel("Дата призыва:"), 1, 0); l3.addWidget(self.draft_date_input, 1, 1)
        l3.addWidget(QLabel("ПОВСК:"), 1, 2); l3.addWidget(self.povsk_input, 1, 3)
        l3.addWidget(QLabel("Дата отбора:"), 2, 0); l3.addWidget(self.selection_date_input, 2, 1)
        g3.setLayout(l3); layout.addWidget(g3)

        # === Группа 4: 📄 Паспортные данные (ВЫНЕСЕНО ОТДЕЛЬНО) ===
        g4 = QGroupBox("📄 Паспортные данные")
        g4.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l4 = QGridLayout(); l4.setSpacing(8)
        
        self.passport_series_input = QLineEdit(); self.passport_series_input.setPlaceholderText("Серия (напр. 0000)")
        self.passport_number_input = QLineEdit(); self.passport_number_input.setPlaceholderText("Номер")
        self.passport_issue_date_input = QDateEdit(); self.passport_issue_date_input.setCalendarPopup(True)
        self.passport_issue_date_input.setMaximumDate(QDate.currentDate())
        self.passport_issued_by_input = QLineEdit()
        
        l4.addWidget(QLabel("Серия:"), 0, 0); l4.addWidget(self.passport_series_input, 0, 1)
        l4.addWidget(QLabel("Номер:"), 0, 2); l4.addWidget(self.passport_number_input, 0, 3)
        l4.addWidget(QLabel("Дата выдачи:"), 1, 0); l4.addWidget(self.passport_issue_date_input, 1, 1)
        l4.addWidget(QLabel("Кем выдан:"), 1, 2); l4.addWidget(self.passport_issued_by_input, 1, 3)
        g4.setLayout(l4); layout.addWidget(g4)

        # === Группа 5: 🎫 Данные военного билета (ВЫНЕСЕНО ОТДЕЛЬНО) ===
        g5 = QGroupBox("🎫 Данные военного билета")
        g5.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l5 = QGridLayout(); l5.setSpacing(8)
        
        self.military_id_series_input = QLineEdit(); self.military_id_series_input.setPlaceholderText("Серия ВБ")
        self.military_id_number_input = QLineEdit(); self.military_id_number_input.setPlaceholderText("Номер ВБ")
        self.military_id_issue_date_input = QDateEdit(); self.military_id_issue_date_input.setCalendarPopup(True)
        self.military_id_issue_date_input.setMaximumDate(QDate.currentDate())
        self.military_id_issued_by_input = QLineEdit()
        
        l5.addWidget(QLabel("Серия ВБ:"), 0, 0); l5.addWidget(self.military_id_series_input, 0, 1)
        l5.addWidget(QLabel("Номер ВБ:"), 0, 2); l5.addWidget(self.military_id_number_input, 0, 3)
        l5.addWidget(QLabel("Дата выдачи:"), 1, 0); l5.addWidget(self.military_id_issue_date_input, 1, 1)
        l5.addWidget(QLabel("Кем выдан:"), 1, 2); l5.addWidget(self.military_id_issued_by_input, 1, 3)
        g5.setLayout(l5); layout.addWidget(g5)

        # === Группа 6: 📝 Дополнительная информация ===
        g6 = QGroupBox("📝 Дополнительная информация")
        g6.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l6 = QGridLayout(); l6.setSpacing(8)
        
        self.education_input = QLineEdit()
        self.criminal_record_input = QTextEdit(); self.criminal_record_input.setMaximumHeight(60)
        self.social_media_account_input = QLineEdit()
        self.bank_card_number_input = QLineEdit()
        self.federal_search_info_input = QTextEdit(); self.federal_search_info_input.setMaximumHeight(60)
        self.military_contacts_input = QLineEdit()
        self.relatives_info_input = QTextEdit(); self.relatives_info_input.setMaximumHeight(60)
        
        l6.addWidget(QLabel("Образование:"), 0, 0); l6.addWidget(self.education_input, 0, 1, 1, 3)
        l6.addWidget(QLabel("Судимость:"), 1, 0); l6.addWidget(self.criminal_record_input, 1, 1, 1, 3)
        l6.addWidget(QLabel("Соцсети:"), 2, 0); l6.addWidget(self.social_media_account_input, 2, 1)
        l6.addWidget(QLabel("Банковская карта:"), 2, 2); l6.addWidget(self.bank_card_number_input, 2, 3)
        l6.addWidget(QLabel("Фед. розыск:"), 3, 0); l6.addWidget(self.federal_search_info_input, 3, 1, 1, 3)
        l6.addWidget(QLabel("Контакты в/с:"), 4, 0); l6.addWidget(self.military_contacts_input, 4, 1, 1, 3)
        l6.addWidget(QLabel("Родные:"), 5, 0); l6.addWidget(self.relatives_info_input, 5, 1, 1, 3)
        g6.setLayout(l6); layout.addWidget(g6)

        # === Группа 7: 📷 Фотографии ===
        g7 = QGroupBox("📷 Фотографии")
        g7.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l7 = QGridLayout(); l7.setSpacing(15)
        
        photo_types = [
            ('civilian', 'Гражданская одежда'),
            ('military_headgear', 'Форма с головным убором'),
            ('military_no_headgear', 'Форма без головного убора'),
            ('distinctive_marks', 'Отличительные приметы')
        ]
        
        for i, (key, label_text) in enumerate(photo_types):
            v_layout = QVBoxLayout()
            lbl = QLabel(f"{label_text}:"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v_layout.addWidget(lbl)
            
            photo_lbl = QLabel("Нет фото")
            photo_lbl.setFixedSize(150, 200)
            photo_lbl.setStyleSheet("QLabel { border: 2px dashed #999; background: #f8f9fa; color: #6c757d; font-size: 11px; }")
            photo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            setattr(self, f'photo_{key}_label', photo_lbl)
            v_layout.addWidget(photo_lbl)
            
            btn = QPushButton("Загрузить")
            btn.clicked.connect(lambda checked=False, k=key: self.load_photo(k))
            v_layout.addWidget(btn)
            l7.addLayout(v_layout, 0, i)
        g7.setLayout(l7); layout.addWidget(g7)

        layout.addStretch()
        scroll.setWidget(container)
        main = QVBoxLayout(self)
        main.addWidget(scroll)

    def open_ref_editor(self, table_name: str):
        """Открытие редактора справочников на нужной вкладке с последующим обновлением"""
        try:
            from reference_editor_dialog import ReferenceEditorDialog
            # Передаем table_name, чтобы справочник открылся сразу на нужной вкладке
            # Если у виджета есть родительское окно, передаем его как parent
            parent_window = self.parent_window or self.parent()
            dialog = ReferenceEditorDialog(self.db, parent_window, table_name)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Если что-то изменили, обновляем данные в ComboBox
                print(f"🔄 Обновление справочника '{table_name}'...")
                self.load_combo_data()
        except Exception as e:
            print(f"⚠️ Ошибка открытия редактора справочников: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть справочник: {str(e)}")

    def _setup_validators_and_autocomplete(self):
        """Настройка валидаторов и автодополнения по схеме БД"""
        # 1. Ограничения по длине (VARCHAR) согласно schema_only.sql
        self.surname_input.setMaxLength(100)
        self.name_input.setMaxLength(100)
        self.patronymic_input.setMaxLength(100)
        self.birth_place_town_input.setMaxLength(100)
        self.birth_place_district_input.setMaxLength(100)
        self.birth_place_region_input.setMaxLength(100)
        self.birth_place_country_input.setMaxLength(100)
        self.tab_number_input.setMaxLength(50)
        self.personal_number_input.setMaxLength(50)
        self.drafted_by_commissariat_input.setMaxLength(255)
        self.povsk_input.setMaxLength(255)
        self.education_input.setMaxLength(255)
        self.social_media_account_input.setMaxLength(255)
        self.military_contacts_input.setMaxLength(255)
        self.passport_issued_by_input.setMaxLength(255)
        self.military_id_issued_by_input.setMaxLength(255)
        
        self.passport_series_input.setMaxLength(10)
        self.passport_number_input.setMaxLength(20)
        self.military_id_series_input.setMaxLength(10)
        self.military_id_number_input.setMaxLength(20)
        self.bank_card_number_input.setMaxLength(50)

        # 2. Форматные валидаторы (RegEx)
        # Только цифры для номера карты
        card_regex = QRegularExpression(r"^[0-9]+$")
        self.bank_card_number_input.setValidator(QRegularExpressionValidator(card_regex))
        
        # Серия и номер паспорта/ВБ: цифры и латиница/кириллица
        doc_regex = QRegularExpression(r"^[a-zA-Zа-яА-Я0-9\-]+$")
        self.passport_series_input.setValidator(QRegularExpressionValidator(doc_regex))
        self.passport_number_input.setValidator(QRegularExpressionValidator(doc_regex))
        self.military_id_series_input.setValidator(QRegularExpressionValidator(doc_regex))
        self.military_id_number_input.setValidator(QRegularExpressionValidator(doc_regex))

        # 3. Автодополнение из БД (используем ваш AutocompleteHelper)
        autocomplete_config = [
            (self.surname_input, 'surname', 50),
            (self.name_input, 'name', 50),
            (self.patronymic_input, 'patronymic', 50),
            (self.birth_place_town_input, 'birth_place_town', 20),
            (self.birth_place_district_input, 'birth_place_district', 20),
            (self.birth_place_region_input, 'birth_place_region', 20),
            (self.birth_place_country_input, 'birth_place_country', 20),
            (self.tab_number_input, 'tab_number', 30),
            (self.personal_number_input, 'personal_number', 30),
            (self.drafted_by_commissariat_input, 'drafted_by_commissariat', 20),
            (self.povsk_input, 'povsk', 20),
            (self.education_input, 'education', 15),
            (self.social_media_account_input, 'social_media_account', 20),
            (self.bank_card_number_input, 'bank_card_number', 20),
            (self.passport_series_input, 'passport_series', 10),
            (self.passport_number_input, 'passport_number', 10),
            (self.passport_issued_by_input, 'passport_issued_by', 20),
            (self.military_id_series_input, 'military_id_series', 10),
            (self.military_id_number_input, 'military_id_number', 10),
            (self.military_id_issued_by_input, 'military_id_issued_by', 20),
            (self.military_contacts_input, 'military_contacts', 20),
        ]
        for widget, col, max_items in autocomplete_config:
            self.autocomplete_helper.setup_autocomplete(
                widget, 'social_data', col, max_items=max_items, show_on_focus=True
            )

    def load_combo_data(self):
        """Загрузка данных в комбобоксы"""
        # Очистка и заполнение Категории
        self.category_combo.clear()
        self.category_combo.addItem("", None)
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.categories ORDER BY name")
        while q.next(): self.category_combo.addItem(q.value(1), q.value(0))
        
        # Очистка и заполнение Звания
        self.rank_combo.clear()
        self.rank_combo.addItem("", None)
        q.exec("SELECT id, name FROM krd.ranks ORDER BY name")
        while q.next(): self.rank_combo.addItem(q.value(1), q.value(0))

    def load_photo(self, photo_type):
        """Загрузка фотографии"""
        path, _ = QFileDialog.getOpenFileName(self, f"Выберите фото ({photo_type})", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            try:
                if os.path.getsize(path) > 5 * 1024 * 1024:
                    return QMessageBox.warning(self, "Ошибка", "Файл превышает 5 МБ")
                pixmap = self._load_pixmap(path)
                if not pixmap: return
                lbl = getattr(self, f'photo_{photo_type}_label')
                lbl.setPixmap(pixmap)
                lbl.setStyleSheet("QLabel { border: 2px solid #2196F3; background: white; }")
                self.photo_paths[photo_type] = path
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _load_pixmap(self, path):
        """Масштабирование изображения"""
        p = QPixmap(path)
        if p.isNull(): return None
        return p.scaled(150, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def validate_required_fields(self):
        """Валидация обязательных полей"""
        if not self.surname_input.text().strip(): return False, "Введите фамилию"
        if not self.name_input.text().strip(): return False, "Введите имя"
        if not self.patronymic_input.text().strip(): return False, "Введите отчество"
        
        # Доп. валидация формата
        if self.bank_card_number_input.text().strip() and not self.bank_card_number_input.hasAcceptableInput():
            return False, "Номер карты должен содержать только цифры"
        return True, ""

    def get_data(self):
        """Получение данных из формы"""
        data = {
            'surname': self.surname_input.text().strip(),
            'name': self.name_input.text().strip(),
            'patronymic': self.patronymic_input.text().strip(),
            'birth_date': self.birth_date_input.date(),
            'birth_place_town': self.birth_place_town_input.text().strip(),
            'birth_place_district': self.birth_place_district_input.text().strip(),
            'birth_place_region': self.birth_place_region_input.text().strip(),
            'birth_place_country': self.birth_place_country_input.text().strip(),
            'tab_number': self.tab_number_input.text().strip(),
            'personal_number': self.personal_number_input.text().strip(),
            'category_id': self.category_combo.currentData(),
            'rank_id': self.rank_combo.currentData(),
            'drafted_by_commissariat': self.drafted_by_commissariat_input.text().strip(),
            'draft_date': self.draft_date_input.date(),
            'povsk': self.povsk_input.text().strip(),
            'selection_date': self.selection_date_input.date(),
            'education': self.education_input.text().strip(),
            'criminal_record': self.criminal_record_input.toPlainText(),
            'social_media_account': self.social_media_account_input.text().strip(),
            'bank_card_number': self.bank_card_number_input.text().strip(),
            'federal_search_info': self.federal_search_info_input.toPlainText(),
            'military_contacts': self.military_contacts_input.text().strip(),
            'relatives_info': self.relatives_info_input.toPlainText(),
            'passport_series': self.passport_series_input.text().strip(),
            'passport_number': self.passport_number_input.text().strip(),
            'passport_issue_date': self.passport_issue_date_input.date(),
            'passport_issued_by': self.passport_issued_by_input.text().strip(),
            'military_id_series': self.military_id_series_input.text().strip(),
            'military_id_number': self.military_id_number_input.text().strip(),
            'military_id_issue_date': self.military_id_issue_date_input.date(),
            'military_id_issued_by': self.military_id_issued_by_input.text().strip(),
            'appearance_features': "",
            'personal_marks': ""
        }
        for key in ['civilian', 'military_headgear', 'military_no_headgear', 'distinctive_marks']:
            path = self.photo_paths.get(key)
            if path and os.path.exists(path):
                with open(path, 'rb') as f: data[f'photo_{key}'] = QByteArray(f.read())
            else:
                data[f'photo_{key}'] = QByteArray()
        return data