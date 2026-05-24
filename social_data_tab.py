from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QDateEdit, QComboBox, QLabel, QPushButton, QFileDialog,
    QMessageBox, QFrame, QDialog
)
from PyQt6.QtCore import Qt, QDate, QByteArray, QTimer, QRegularExpression
from PyQt6.QtGui import QPixmap, QFont, QRegularExpressionValidator
from PyQt6.QtSql import QSqlQuery
import os
import traceback

from autocomplete_helper import AutocompleteHelper
from reference_editor_dialog import ReferenceEditorDialog
# 🔒 ИМПОРТ ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ ДЛЯ РОЛИ ЧИТАТЕЛЯ
from ui_helpers import is_reader, apply_readonly_mode

class SocialDataTab(QWidget):
    """Вкладка социально-демографических данных с поддержкой изображений"""
    
    def __init__(self, krd_id, db_connection, audit_logger=None, user_info=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.user_info = user_info or {}
        
        # 🔒 Флаг режима чтения
        self.is_read_only = is_reader(self.user_info)
        
        self.record = None
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        self.photo_paths = {
            'civilian': None, 'military_headgear': None,
            'military_no_headgear': None, 'distinctive_marks': None
        }
        self.original_photos = {
            'civilian': None, 'military_headgear': None,
            'military_no_headgear': None, 'distinctive_marks': None
        }
        self.max_text_length = 5000

        # 1. Создание интерфейса
        self.init_ui()
        # 2. Загрузка справочников
        self.load_combo_data()
        # 3. Загрузка данных из БД
        self.load_data()
        # 4. Настройка автосохранения, автодополнения и валидаторов
        self.setup_auto_save()
        self.setup_autocomplete_fields()
        self.setup_validators()
        
        # 🔒 БЛОКИРОВКА ИНТЕРФЕЙСА ДЛЯ ЧИТАТЕЛЯ (вызывается ПОСЛЕ полной инициализации)
        if self.is_read_only:
            apply_readonly_mode(self.scroll_area, True)
            if hasattr(self, '_auto_save_timer'):
                self._auto_save_timer.stop()
            print(f"👁️ [READ-ONLY] Режим просмотра активирован для КРД-{self.krd_id}")

    def init_ui(self):
        """Инициализация интерфейса"""
        # ✅ СОХРАНЯЕМ scroll_area В АТРИБУТ КЛАССА, чтобы apply_readonly_mode мог его найти
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # === Группа 1: Основные данные ===
        group1 = QGroupBox("Основные данные (поля со знаком * обязательны)")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g1 = QGridLayout(); g1.setSpacing(8)
        
        g1.addWidget(QLabel("Фамилия *:"), 0, 0)
        self.surname_input = QLineEdit(); self.surname_input.setPlaceholderText("Введите фамилию")
        g1.addWidget(self.surname_input, 0, 1)
        
        g1.addWidget(QLabel("Имя *:"), 0, 2)
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Введите имя")
        g1.addWidget(self.name_input, 0, 3)
        
        g1.addWidget(QLabel("Отчество *:"), 0, 4)
        self.patronymic_input = QLineEdit(); self.patronymic_input.setPlaceholderText("Введите отчество")
        g1.addWidget(self.patronymic_input, 0, 5)
        
        g1.addWidget(QLabel("Табельный номер:"), 1, 0)
        self.tab_number_input = QLineEdit()
        g1.addWidget(self.tab_number_input, 1, 1)
        
        g1.addWidget(QLabel("Личный номер:"), 1, 2)
        self.personal_number_input = QLineEdit()
        g1.addWidget(self.personal_number_input, 1, 3)
        
        # Категория (со справочником)
        g1.addWidget(QLabel("Категория военнослужащего:"), 2, 0)
        self.category_combo = QComboBox()
        g1.addWidget(self._create_ref_combo_widget(self.category_combo, 'categories', self.load_categories), 2, 1)
        
        # Звание (со справочником)
        g1.addWidget(QLabel("Воинское звание:"), 2, 2)
        self.rank_combo = QComboBox()
        g1.addWidget(self._create_ref_combo_widget(self.rank_combo, 'ranks', self.load_ranks), 2, 3)
        
        group1.setLayout(g1); layout.addWidget(group1)

        # === Группа 2: Место рождения ===
        group2 = QGroupBox("Место рождения")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g2 = QGridLayout(); g2.setSpacing(8)
        
        g2.addWidget(QLabel("Населенный пункт:"), 0, 0); self.birth_place_town_input = QLineEdit(); g2.addWidget(self.birth_place_town_input, 0, 1)
        g2.addWidget(QLabel("Административный район:"), 0, 2); self.birth_place_district_input = QLineEdit(); g2.addWidget(self.birth_place_district_input, 0, 3)
        g2.addWidget(QLabel("Субъект (регион):"), 1, 0); self.birth_place_region_input = QLineEdit(); g2.addWidget(self.birth_place_region_input, 1, 1)
        g2.addWidget(QLabel("Страна:"), 1, 2); self.birth_place_country_input = QLineEdit(); g2.addWidget(self.birth_place_country_input, 1, 3)
        g2.addWidget(QLabel("Дата рождения:"), 2, 0); self.birth_date_input = QDateEdit(); self.birth_date_input.setCalendarPopup(True); self.birth_date_input.setDate(QDate.currentDate()); g2.addWidget(self.birth_date_input, 2, 1)
        
        group2.setLayout(g2); layout.addWidget(group2)

        # === Группа 3: Призыв ===
        group3 = QGroupBox("Призыв")
        group3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g3 = QGridLayout(); g3.setSpacing(8)
        
        g3.addWidget(QLabel("Каким комиссариатом призван:"), 0, 0); self.drafted_by_commissariat_input = QLineEdit(); g3.addWidget(self.drafted_by_commissariat_input, 0, 1, 1, 3)
        g3.addWidget(QLabel("Дата призыва:"), 1, 0); self.draft_date_input = QDateEdit(); self.draft_date_input.setCalendarPopup(True); self.draft_date_input.setDate(QDate.currentDate()); g3.addWidget(self.draft_date_input, 1, 1)
        g3.addWidget(QLabel("Каким ПОВСК отобран:"), 1, 2); self.povsk_input = QLineEdit(); g3.addWidget(self.povsk_input, 1, 3)
        g3.addWidget(QLabel("Дата отбора:"), 2, 0); self.selection_date_input = QDateEdit(); self.selection_date_input.setCalendarPopup(True); self.selection_date_input.setDate(QDate.currentDate()); g3.addWidget(self.selection_date_input, 2, 1)
        
        group3.setLayout(g3); layout.addWidget(group3)

        # === Группа 4: Образование и судимость ===
        group4 = QGroupBox("Образование и судимость")
        group4.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g4 = QGridLayout(); g4.setSpacing(8)
        
        g4.addWidget(QLabel("Образование:"), 0, 0); self.education_input = QLineEdit(); g4.addWidget(self.education_input, 0, 1, 1, 3)
        g4.addWidget(QLabel("Сведения о судимости:"), 1, 0); self.criminal_record_input = QTextEdit(); self.criminal_record_input.setMaximumHeight(60); g4.addWidget(self.criminal_record_input, 1, 1, 1, 3)
        g4.addWidget(QLabel("Аккаунт в соцсетях:"), 2, 0); self.social_media_account_input = QLineEdit(); g4.addWidget(self.social_media_account_input, 2, 1)
        g4.addWidget(QLabel("Номер банковской карты:"), 2, 2); self.bank_card_number_input = QLineEdit(); g4.addWidget(self.bank_card_number_input, 2, 3)
        
        group4.setLayout(g4); layout.addWidget(group4)

        # === Группа 5: Паспортные данные ===
        group5 = QGroupBox("Паспортные данные")
        group5.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g5 = QGridLayout(); g5.setSpacing(8)
        
        g5.addWidget(QLabel("Серия паспорта:"), 0, 0); self.passport_series_input = QLineEdit(); g5.addWidget(self.passport_series_input, 0, 1)
        g5.addWidget(QLabel("Номер паспорта:"), 0, 2); self.passport_number_input = QLineEdit(); g5.addWidget(self.passport_number_input, 0, 3)
        g5.addWidget(QLabel("Дата выдачи:"), 1, 0); self.passport_issue_date_input = QDateEdit(); self.passport_issue_date_input.setCalendarPopup(True); self.passport_issue_date_input.setDate(QDate.currentDate()); g5.addWidget(self.passport_issue_date_input, 1, 1)
        g5.addWidget(QLabel("Кем выдан:"), 1, 2); self.passport_issued_by_input = QLineEdit(); g5.addWidget(self.passport_issued_by_input, 1, 3)
        
        group5.setLayout(g5); layout.addWidget(group5)

        # === Группа 6: Военный билет ===
        group6 = QGroupBox("Военный билет (удостоверение личности)")
        group6.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g6 = QGridLayout(); g6.setSpacing(8)
        
        g6.addWidget(QLabel("Серия:"), 0, 0); self.military_id_series_input = QLineEdit(); g6.addWidget(self.military_id_series_input, 0, 1)
        g6.addWidget(QLabel("Номер:"), 0, 2); self.military_id_number_input = QLineEdit(); g6.addWidget(self.military_id_number_input, 0, 3)
        g6.addWidget(QLabel("Дата выдачи:"), 1, 0); self.military_id_issue_date_input = QDateEdit(); self.military_id_issue_date_input.setCalendarPopup(True); self.military_id_issue_date_input.setDate(QDate.currentDate()); g6.addWidget(self.military_id_issue_date_input, 1, 1)
        g6.addWidget(QLabel("Кем выдан:"), 1, 2); self.military_id_issued_by_input = QLineEdit(); g6.addWidget(self.military_id_issued_by_input, 1, 3)
        
        group6.setLayout(g6); layout.addWidget(group6)

        # === Группа 7: Внешность и фотографии ===
        group7 = QGroupBox("Особенности внешности и фотографии")
        group7.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g7 = QVBoxLayout(); g7.setSpacing(10)
        
        tg = QGridLayout(); tg.setSpacing(8)
        tg.addWidget(QLabel("Особенности внешности:"), 0, 0); self.appearance_features_input = QTextEdit(); self.appearance_features_input.setMaximumHeight(60); tg.addWidget(self.appearance_features_input, 0, 1, 1, 3)
        tg.addWidget(QLabel("Личные приметы:"), 1, 0); self.personal_marks_input = QTextEdit(); self.personal_marks_input.setMaximumHeight(60); tg.addWidget(self.personal_marks_input, 1, 1, 1, 3)
        tg.addWidget(QLabel("Сведения о федеральном розыске:"), 2, 0); self.federal_search_info_input = QTextEdit(); self.federal_search_info_input.setMaximumHeight(60); tg.addWidget(self.federal_search_info_input, 2, 1, 1, 3)
        tg.addWidget(QLabel("Контакты военнослужащего:"), 3, 0); self.military_contacts_input = QLineEdit(); tg.addWidget(self.military_contacts_input, 3, 1, 1, 3)
        tg.addWidget(QLabel("Сведения о близких родственниках:"), 4, 0); self.relatives_info_input = QTextEdit(); self.relatives_info_input.setMaximumHeight(60); tg.addWidget(self.relatives_info_input, 4, 1, 1, 3)
        g7.addLayout(tg)
        
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setFrameShadow(QFrame.Shadow.Sunken); g7.addWidget(sep)
        pt = QLabel("Фотографии военнослужащего"); pt.setFont(QFont("Arial", 10, QFont.Weight.Bold)); pt.setAlignment(Qt.AlignmentFlag.AlignCenter); g7.addWidget(pt)
        
        pg = QGridLayout(); pg.setSpacing(15)
        for i, (key, label) in enumerate([('civilian','Гражданская одежда'), ('military_headgear','Форма с головным убором'), ('military_no_headgear','Форма без головного убора'), ('distinctive_marks','Отличительные приметы')]):
            v = QVBoxLayout(); v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(QLabel(label, alignment=Qt.AlignmentFlag.AlignCenter))
            lbl = QLabel("Нет фото"); lbl.setFixedSize(180, 240); lbl.setStyleSheet("QLabel { border: 2px dashed #999; background-color: #f8f9fa; color: #6c757d; font-size: 12px; }"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            setattr(self, f'photo_{key}_label', lbl); v.addWidget(lbl)
            b1 = QPushButton("Загрузить фото"); b1.setMinimumWidth(150); b1.clicked.connect(lambda c, k=key: self.load_photo(k)); v.addWidget(b1)
            b2 = QPushButton("Выгрузить фото"); b2.setMinimumWidth(150); b2.clicked.connect(lambda c, k=key: self.export_photo(k)); v.addWidget(b2)
            pg.addLayout(v, 0, i)
        g7.addLayout(pg); group7.setLayout(g7); layout.addWidget(group7)
        
        layout.addStretch()
        self.scroll_area.setWidget(container)

        # ✅ УСТАНОВКА ГЛАВНОГО LAYOUT'А
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
    def _create_ref_combo_widget(self, combo, table_name, reload_func):
        """Вспомогательный метод: ComboBox + кнопка ⚙️ с автообновлением"""
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(combo, 1)
        
        btn = QPushButton("⚙️")
        btn.setToolTip(f"Настроить справочник: {table_name}")
        btn.setFixedSize(32, 32)
        btn.setProperty("role","edit")
        
        def open_ref():
            dlg = ReferenceEditorDialog(self.db, self, initial_table=table_name)
            dlg.data_changed.connect(lambda tbl: self._on_reference_changed(tbl, reload_func))
            dlg.exec()
            
        btn.clicked.connect(open_ref)
        lay.addWidget(btn)
        return w

    def _on_reference_changed(self, changed_table, reload_func):
        """Обработчик изменения справочника"""
        print(f"🔄 Справочник '{changed_table}' изменён, перезагрузка...")
        reload_func()

    def setup_validators(self):
        """Настройка валидаторов и ограничений длины согласно схеме БД krd.social_data"""
        name_place_regex = QRegularExpression(r"^[а-яА-Яa-zA-Z0-9\s\-\.']+$")
        self.val_name_place = QRegularExpressionValidator(name_place_regex)

        num_id_regex = QRegularExpression(r"^[0-9\-]+$")
        self.val_num_id = QRegularExpressionValidator(num_id_regex)

        card_regex = QRegularExpression(r"^(?:\d[\s]?){15,18}\d$")
        self.val_card = QRegularExpressionValidator(card_regex)

        pass_series_regex = QRegularExpression(r"^\d{4}$")
        self.val_pass_series = QRegularExpressionValidator(pass_series_regex)

        pass_num_regex = QRegularExpression(r"^\d{6}$")
        self.val_pass_num = QRegularExpressionValidator(pass_num_regex)

        mil_series_regex = QRegularExpression(r"^[A-Za-z0-9\-]{1,8}$")
        self.val_mil_series = QRegularExpressionValidator(mil_series_regex)

        mil_num_regex = QRegularExpression(r"^\d{5,10}$")
        self.val_mil_num = QRegularExpressionValidator(mil_num_regex)

        contact_info_regex = QRegularExpression(r"^[a-zA-Z0-9а-яА-Я\s\-\.\/\,\@\:\?\#\&\=\+\(\)]+$")
        self.val_contact = QRegularExpressionValidator(contact_info_regex)

        # VARCHAR(100): ФИО, Место рождения
        for f in [self.surname_input, self.name_input, self.patronymic_input,
                  self.birth_place_town_input, self.birth_place_district_input,
                  self.birth_place_region_input, self.birth_place_country_input]:
            f.setMaxLength(100)
            f.setValidator(self.val_name_place)

        # VARCHAR(50): Табельный, Личный номер
        for f in [self.tab_number_input, self.personal_number_input]:
            f.setMaxLength(50)
            f.setValidator(self.val_num_id)

        # VARCHAR(19): Банковская карта
        self.bank_card_number_input.setMaxLength(19)
        self.bank_card_number_input.setValidator(self.val_card)

        # VARCHAR(4/6): Паспорт
        self.passport_series_input.setMaxLength(4)
        self.passport_series_input.setValidator(self.val_pass_series)
        self.passport_number_input.setMaxLength(6)
        self.passport_number_input.setValidator(self.val_pass_num)

        # VARCHAR(255): Военкомат, ПОВСК, Образование, Кем выдан, Контакты, Соцсети
        for f in [self.drafted_by_commissariat_input, self.povsk_input, self.education_input,
                  self.passport_issued_by_input, self.military_id_issued_by_input,
                  self.military_contacts_input, self.social_media_account_input]:
            f.setMaxLength(255)
            f.setValidator(self.val_contact)

        # VARCHAR(8/10): ВБ
        self.military_id_series_input.setMaxLength(8)
        self.military_id_series_input.setValidator(self.val_mil_series)
        self.military_id_number_input.setMaxLength(10)
        self.military_id_number_input.setValidator(self.val_mil_num)

        # Даты
        max_date = QDate.currentDate()
        min_date = QDate(1900, 1, 1)
        for d in [self.birth_date_input, self.draft_date_input, self.selection_date_input,
                  self.passport_issue_date_input, self.military_id_issue_date_input]:
            d.setCalendarPopup(True)
            d.setMaximumDate(max_date)
            d.setMinimumDate(min_date)

        print("✅ Валидаторы и ограничения длины настроены согласно схеме БД")

    def validate_all_fields(self):
        """Мягкая валидация: проверяет формат ТОЛЬКО если поле заполнено"""
        errors = []

        # 1. ✅ ФИО больше не обязательны (по вашему запросу)

        # 2. Проверка формата (срабатывает только при вводе данных)
        format_checks = [
            (self.tab_number_input, "Табельный номер", r"^[0-9\-]+$"),
            (self.personal_number_input, "Личный номер", r"^[0-9\-]+$"),
            (self.bank_card_number_input, "Номер банковской карты", r"^[\d\s]{16,19}$"),
            (self.passport_series_input, "Серия паспорта", r"^\d{4}$"),
            (self.passport_number_input, "Номер паспорта", r"^\d{6}$"),
            (self.military_id_series_input, "Серия ВБ", r"^[A-Za-z0-9\-]{1,8}$"),
            (self.military_id_number_input, "Номер ВБ", r"^\d{5,10}$")
        ]
        
        for widget, name, regex in format_checks:
            text = widget.text().strip()
            if text:  # ✅ Проверяем только если поле не пустое
                if not QRegularExpression(regex).match(text).hasMatch():
                    errors.append(f"Неверный формат в поле '{name}'")

        # 3. Проверка длины TEXT полей
        text_fields = [
            (self.criminal_record_input, "Сведения о судимости"),
            (self.appearance_features_input, "Особенности внешности"),
            (self.personal_marks_input, "Личные приметы"),
            (self.federal_search_info_input, "Федеральный розыск"),
            (self.relatives_info_input, "Близкие родственники")
        ]
        for widget, name in text_fields:
            if len(widget.toPlainText()) > self.max_text_length:
                errors.append(f"Поле '{name}' слишком длинное (макс. {self.max_text_length} символов)")

        # 4. Логическая проверка дат
        draft = self.draft_date_input.date()
        birth = self.birth_date_input.date()
        if draft.isValid() and birth.isValid() and draft < birth:
            errors.append("Дата призыва не может быть раньше даты рождения")

        return ";\n".join(errors) if errors else None

    def setup_autocomplete_fields(self):
        if self.is_read_only:
            print("🔒 [AUTO-COMPLETE] Отключено для режима чтения.")
            return
        fields = [
            (self.surname_input, 'surname', 50), (self.name_input, 'name', 50), (self.patronymic_input, 'patronymic', 50),
            (self.tab_number_input, 'tab_number', 30), (self.personal_number_input, 'personal_number', 30),
            (self.birth_place_town_input, 'birth_place_town', 20), (self.birth_place_district_input, 'birth_place_district', 20),
            (self.birth_place_region_input, 'birth_place_region', 20), (self.birth_place_country_input, 'birth_place_country', 20),
            (self.drafted_by_commissariat_input, 'drafted_by_commissariat', 20), (self.povsk_input, 'povsk', 20),
            (self.education_input, 'education', 15), (self.social_media_account_input, 'social_media_account', 20),
            (self.bank_card_number_input, 'bank_card_number', 20), (self.passport_series_input, 'passport_series', 20),
            (self.passport_number_input, 'passport_number', 20), (self.passport_issued_by_input, 'passport_issued_by', 20),
            (self.military_id_series_input, 'military_id_series', 20), (self.military_id_number_input, 'military_id_number', 20),
            (self.military_id_issued_by_input, 'military_id_issued_by', 20), (self.military_contacts_input, 'military_contacts', 20)
        ]
        for w, c, m in fields:
            self.autocomplete_helper.setup_autocomplete(w, 'social_data', c, max_items=m, show_on_focus=True)

    def load_categories(self):
        """Загрузка категорий с сохранением текущего выбора"""
        current_id = self.category_combo.currentData()
        self.category_combo.clear()
        self.category_combo.addItem("", None)
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.categories ORDER BY name")
        while q.next():
            self.category_combo.addItem(q.value(1), q.value(0))
        if current_id is not None:
            idx = self.category_combo.findData(current_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)

    def load_ranks(self):
        """Загрузка званий с сохранением текущего выбора"""
        current_id = self.rank_combo.currentData()
        self.rank_combo.clear()
        self.rank_combo.addItem("", None)
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.ranks ORDER BY name")
        while q.next():
            self.rank_combo.addItem(q.value(1), q.value(0))
        if current_id is not None:
            idx = self.rank_combo.findData(current_id)
            if idx >= 0:
                self.rank_combo.setCurrentIndex(idx)

    def load_combo_data(self):
        """Первичная загрузка данных в комбобоксы при инициализации"""
        self.load_categories()
        self.load_ranks()

    def load_data(self):
        q = QSqlQuery(self.db)
        q.prepare("SELECT * FROM krd.social_data WHERE krd_id = ? ORDER BY id DESC LIMIT 1")
        q.addBindValue(self.krd_id)
        q.exec()
        if q.next():
            self.record = q.record()
            self.surname_input.setText(q.value("surname") or "")
            self.name_input.setText(q.value("name") or "")
            self.patronymic_input.setText(q.value("patronymic") or "")
            self.tab_number_input.setText(q.value("tab_number") or "")
            self.personal_number_input.setText(q.value("personal_number") or "")
            
            c = q.value("category_id")
            if c is not None:
                idx = self.category_combo.findData(c)
                if idx >= 0: self.category_combo.setCurrentIndex(idx)
                
            r = q.value("rank_id")
            if r is not None:
                idx = self.rank_combo.findData(r)
                if idx >= 0: self.rank_combo.setCurrentIndex(idx)
                
            self.birth_place_town_input.setText(q.value("birth_place_town") or "")
            self.birth_place_district_input.setText(q.value("birth_place_district") or "")
            self.birth_place_region_input.setText(q.value("birth_place_region") or "")
            self.birth_place_country_input.setText(q.value("birth_place_country") or "")
            bd = q.value("birth_date")
            if bd: self.birth_date_input.setDate(bd)
            
            self.drafted_by_commissariat_input.setText(q.value("drafted_by_commissariat") or "")
            dd = q.value("draft_date")
            if dd: self.draft_date_input.setDate(dd)
            self.povsk_input.setText(q.value("povsk") or "")
            sd = q.value("selection_date")
            if sd: self.selection_date_input.setDate(sd)
            
            self.education_input.setText(q.value("education") or "")
            self.criminal_record_input.setPlainText(q.value("criminal_record") or "")
            self.social_media_account_input.setText(q.value("social_media_account") or "")
            self.bank_card_number_input.setText(q.value("bank_card_number") or "")
            self.passport_series_input.setText(q.value("passport_series") or "")
            self.passport_number_input.setText(q.value("passport_number") or "")
            pid = q.value("passport_issue_date")
            if pid: self.passport_issue_date_input.setDate(pid)
            self.passport_issued_by_input.setText(q.value("passport_issued_by") or "")
            self.military_id_series_input.setText(q.value("military_id_series") or "")
            self.military_id_number_input.setText(q.value("military_id_number") or "")
            mid = q.value("military_id_issue_date")
            if mid: self.military_id_issue_date_input.setDate(mid)
            self.military_id_issued_by_input.setText(q.value("military_id_issued_by") or "")
            self.appearance_features_input.setPlainText(q.value("appearance_features") or "")
            self.personal_marks_input.setPlainText(q.value("personal_marks") or "")
            self.federal_search_info_input.setPlainText(q.value("federal_search_info") or "")
            self.military_contacts_input.setText(q.value("military_contacts") or "")
            self.relatives_info_input.setPlainText(q.value("relatives_info") or "")
            
            self.load_photo_from_db(q, 'photo_civilian', self.photo_civilian_label, 'civilian')
            self.load_photo_from_db(q, 'photo_military_headgear', self.photo_military_headgear_label, 'military_headgear')
            self.load_photo_from_db(q, 'photo_military_no_headgear', self.photo_military_no_headgear_label, 'military_no_headgear')
            self.load_photo_from_db(q, 'photo_distinctive_marks', self.photo_distinctive_marks_label, 'distinctive_marks')

    def load_photo_from_db(self, query, field_name, label_widget, photo_type):
        pd = query.value(field_name)
        self.original_photos[photo_type] = None
        if pd and (isinstance(pd, bytes) or hasattr(pd, 'data')):
            try:
                b = bytes(pd.data()) if hasattr(pd, 'data') else bytes(pd)
                self.original_photos[photo_type] = b
                p = QPixmap()
                p.loadFromData(b)
                if not p.isNull():
                    label_widget.setPixmap(p.scaled(180, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    label_widget.setStyleSheet("QLabel { border: 2px solid #4CAF50; background-color: white; }")
                else:
                    label_widget.setText("Ошибка загрузки")
            except Exception:
                label_widget.setText("Ошибка")
        else:
            label_widget.setText("Нет фото")
            label_widget.setStyleSheet("QLabel { border: 2px dashed #999; background-color: #f8f9fa; color: #6c757d; font-size: 12px; }")

    def load_photo(self, photo_type):
        path, _ = QFileDialog.getOpenFileName(self, f"Выберите фотографию ({photo_type})", "", "Изображения (*.png *.jpg *.jpeg *.bmp);;Все файлы (*)")
        if path:
            try:
                if os.path.getsize(path) > 5 * 1024 * 1024:
                    return QMessageBox.warning(self, "Ошибка", "Размер файла не должен превышать 5 МБ")
                p = QPixmap(path)
                p = p.scaled(180, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                getattr(self, f'photo_{photo_type}_label').setPixmap(p)
                getattr(self, f'photo_{photo_type}_label').setStyleSheet("QLabel { border: 2px solid #2196F3; background-color: white; }")
                self.photo_paths[photo_type] = path
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {e}")

    def export_photo(self, photo_type):
        b = None
        if self.photo_paths.get(photo_type) and os.path.exists(self.photo_paths[photo_type]):
            with open(self.photo_paths[photo_type], 'rb') as f:
                b = f.read()
        elif self.original_photos.get(photo_type):
            b = self.original_photos[photo_type]
            
        if not b:
            return QMessageBox.information(self, "Информация", f"Фото '{photo_type}' отсутствует.")
            
        path, _ = QFileDialog.getSaveFileName(self, f"Сохранить фото ({photo_type})", f"КРД-{self.krd_id}_{photo_type}.jpg", "Изображения (*.jpg *.png *.bmp);;Все файлы (*)")
        if path:
            try:
                with open(path, 'wb') as f:
                    f.write(b)
                QMessageBox.information(self, "Успешно", f"Фото сохранено: {path}")
                if self.audit_logger:
                    self.audit_logger.log_action('PHOTO_EXPORT', 'social_data', self.krd_id, self.krd_id, f'Выгружено фото "{photo_type}"')
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def save_data(self):
        err = self.validate_all_fields()
        if err:
            raise ValueError(err)

        # ✅ Очистка: пустые строки → None (чтобы БД не падала на CHECK-ограничениях)
        def clean_text(val):
            if isinstance(val, str):
                stripped = val.strip()
                return stripped if stripped else None
            return val

        data = {
            "krd_id": self.krd_id,
            "surname": clean_text(self.surname_input.text()),
            "name": clean_text(self.name_input.text()),
            "patronymic": clean_text(self.patronymic_input.text()),
            "birth_date": self.birth_date_input.date() if self.birth_date_input.date().isValid() else None,
            "birth_place_town": clean_text(self.birth_place_town_input.text()),
            "birth_place_district": clean_text(self.birth_place_district_input.text()),
            "birth_place_region": clean_text(self.birth_place_region_input.text()),
            "birth_place_country": clean_text(self.birth_place_country_input.text()),
            "tab_number": clean_text(self.tab_number_input.text()),
            "personal_number": clean_text(self.personal_number_input.text()),
            "category_id": self.category_combo.currentData(),
            "rank_id": self.rank_combo.currentData(),
            "drafted_by_commissariat": clean_text(self.drafted_by_commissariat_input.text()),
            "draft_date": self.draft_date_input.date() if self.draft_date_input.date().isValid() else None,
            "povsk": clean_text(self.povsk_input.text()),
            "selection_date": self.selection_date_input.date() if self.selection_date_input.date().isValid() else None,
            "education": clean_text(self.education_input.text()),
            "criminal_record": self.criminal_record_input.toPlainText(),
            "social_media_account": clean_text(self.social_media_account_input.text()),
            "bank_card_number": clean_text(self.bank_card_number_input.text()),
            "passport_series": clean_text(self.passport_series_input.text()),
            "passport_number": clean_text(self.passport_number_input.text()),
            "passport_issue_date": self.passport_issue_date_input.date() if self.passport_issue_date_input.date().isValid() else None,
            "passport_issued_by": clean_text(self.passport_issued_by_input.text()),
            "military_id_series": clean_text(self.military_id_series_input.text()),
            "military_id_number": clean_text(self.military_id_number_input.text()),
            "military_id_issue_date": self.military_id_issue_date_input.date() if self.military_id_issue_date_input.date().isValid() else None,
            "military_id_issued_by": clean_text(self.military_id_issued_by_input.text()),
            "appearance_features": self.appearance_features_input.toPlainText(),
            "personal_marks": self.personal_marks_input.toPlainText(),
            "federal_search_info": self.federal_search_info_input.toPlainText(),
            "military_contacts": clean_text(self.military_contacts_input.text()),
            "relatives_info": self.relatives_info_input.toPlainText()
        }
        
        # Обработка фото
        for pt in ['civilian', 'military_headgear', 'military_no_headgear', 'distinctive_marks']:
            p = self.photo_paths.get(pt)
            fb = None
            if p and os.path.exists(p):
                with open(p, 'rb') as f: fb = f.read()
            elif self.original_photos.get(pt): 
                fb = self.original_photos[pt]
            data[f"photo_{pt}"] = QByteArray(fb) if fb else QByteArray()
            
        q = QSqlQuery(self.db)
        
        if self.record:
            # UPDATE существующей записи
            q.prepare("""UPDATE krd.social_data SET 
                surname=:surname, name=:name, patronymic=:patronymic, birth_date=:birth_date,
                birth_place_town=:birth_place_town, birth_place_district=:birth_place_district,
                birth_place_region=:birth_place_region, birth_place_country=:birth_place_country,
                tab_number=:tab_number, personal_number=:personal_number, category_id=:category_id,
                rank_id=:rank_id, drafted_by_commissariat=:drafted_by_commissariat, draft_date=:draft_date,
                povsk=:povsk, selection_date=:selection_date, education=:education,
                criminal_record=:criminal_record, social_media_account=:social_media_account,
                bank_card_number=:bank_card_number, passport_series=:passport_series,
                passport_number=:passport_number, passport_issue_date=:passport_issue_date,
                passport_issued_by=:passport_issued_by, military_id_series=:military_id_series,
                military_id_number=:military_id_number, military_id_issue_date=:military_id_issue_date,
                military_id_issued_by=:military_id_issued_by, appearance_features=:appearance_features,
                personal_marks=:personal_marks, federal_search_info=:federal_search_info,
                military_contacts=:military_contacts, relatives_info=:relatives_info,
                photo_civilian=:photo_civilian, photo_military_headgear=:photo_military_headgear,
                photo_military_no_headgear=:photo_military_no_headgear, photo_distinctive_marks=:photo_distinctive_marks
                WHERE id=:id""")
            q.bindValue(":id", self.record.value("id"))
        else:
            # INSERT новой записи
            q.prepare("""INSERT INTO krd.social_data (krd_id, surname, name, patronymic, birth_date,
                birth_place_town, birth_place_district, birth_place_region, birth_place_country, tab_number,
                personal_number, category_id, rank_id, drafted_by_commissariat, draft_date, povsk,
                selection_date, education, criminal_record, social_media_account, bank_card_number,
                passport_series, passport_number, passport_issue_date, passport_issued_by, military_id_series,
                military_id_number, military_id_issue_date, military_id_issued_by, appearance_features,
                personal_marks, federal_search_info, military_contacts, relatives_info, photo_civilian,
                photo_military_headgear, photo_military_no_headgear, photo_distinctive_marks)
                VALUES (:krd_id, :surname, :name, :patronymic, :birth_date, :birth_place_town,
                :birth_place_district, :birth_place_region, :birth_place_country, :tab_number,
                :personal_number, :category_id, :rank_id, :drafted_by_commissariat, :draft_date, :povsk,
                :selection_date, :education, :criminal_record, :social_media_account, :bank_card_number,
                :passport_series, :passport_number, :passport_issue_date, :passport_issued_by,
                :military_id_series, :military_id_number, :military_id_issue_date, :military_id_issued_by,
                :appearance_features, :personal_marks, :federal_search_info, :military_contacts,
                :relatives_info, :photo_civilian, :photo_military_headgear, :photo_military_no_headgear,
                :photo_distinctive_marks)""")
                
        for k, v in data.items():
            q.bindValue(f":{k}", v)
            
        if not q.exec():
            raise Exception(f"Ошибка сохранения: {q.lastError().text()}")
            
        self.autocomplete_helper.refresh_all_fields()
        print("✅ [SAVE] Данные успешно сохранены в БД!")

    def setup_auto_save(self):
        """Настройка таймера автосохранения"""
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True) # Ждем 400мс после последнего изменения
        self._auto_save_timer.timeout.connect(self._perform_auto_save)
        
        line_edits = [self.surname_input, self.name_input, self.patronymic_input, self.tab_number_input,
                      self.personal_number_input, self.birth_place_town_input, self.birth_place_district_input,
                      self.birth_place_region_input, self.birth_place_country_input, self.drafted_by_commissariat_input,
                      self.povsk_input, self.education_input, self.social_media_account_input, self.bank_card_number_input,
                      self.passport_series_input, self.passport_number_input, self.passport_issued_by_input,
                      self.military_id_series_input, self.military_id_number_input, self.military_id_issued_by_input,
                      self.military_contacts_input]
        text_edits = [self.criminal_record_input, self.appearance_features_input, self.personal_marks_input,
                      self.federal_search_info_input, self.relatives_info_input]
        date_edits = [self.birth_date_input, self.draft_date_input, self.selection_date_input,
                      self.passport_issue_date_input, self.military_id_issue_date_input]
        combos = [self.category_combo, self.rank_combo]
        
        # Подключаем сигналы изменений к таймеру
        for w in line_edits + text_edits:
            w.textChanged.connect(self._on_field_changed)
        for w in date_edits + combos:
            if hasattr(w, 'dateChanged'): w.dateChanged.connect(self._on_field_changed)
            if hasattr(w, 'currentIndexChanged'): w.currentIndexChanged.connect(self._on_field_changed)
            
    def _on_field_changed(self):
        """Перезапуск таймера при изменении поля"""
        self._auto_save_timer.start(400) # Сохранить через 400мс после прекращения ввода
        
    def _perform_auto_save(self):
        """Выполнение автосохранения с логированием"""
        try:
            print(f"\n💾 [AUTO-SAVE] Начало автосохранения для КРД-{self.krd_id}")
            print(f"💾 [AUTO-SAVE] Данные формы:")
            print(f"   - Фамилия: {self.surname_input.text()}")
            print(f"   - Имя: {self.name_input.text()}")
            print(f"   - Отчество: {self.patronymic_input.text()}")
            print(f"   - Серия паспорта: {self.passport_series_input.text()}")
            print(f"   - Номер паспорта: {self.passport_number_input.text()}")
            
            self.save_data()
            print(f"✅ [AUTO-SAVE] Автосохранение успешно завершено\n")
        except ValueError as e:
            # Ошибка валидации - не критична для автосохранения
            print(f"⚠️ [AUTO-SAVE] Ошибка валидации (игнорируется): {e}")
        except Exception as e:
            print(f"❌ [AUTO-SAVE] КРИТИЧЕСКАЯ ОШИБКА автосохранения: {e}")
            import traceback
            traceback.print_exc()