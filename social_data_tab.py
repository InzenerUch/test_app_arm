"""
Вкладка социально-демографических данных с поддержкой изображений и строгой валидацией
Соответствует структуре из шаблона "Шаблон проги.xlsx" и схеме БД
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QGridLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QDateEdit, QComboBox, QLabel, QPushButton, QFileDialog,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, QByteArray, QTimer, QRegularExpression
from PyQt6.QtGui import QPixmap, QFont, QRegularExpressionValidator
from PyQt6.QtSql import QSqlQuery
import os
import traceback
from autocomplete_helper import AutocompleteHelper
from reference_editor_dialog import ReferenceEditorDialog

class SocialDataTab(QWidget):
    """Вкладка социально-демографических данных с поддержкой изображений"""
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.record = None
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        self.photo_paths = {'civilian': None, 'military_headgear': None, 'military_no_headgear': None, 'distinctive_marks': None}
        self.original_photos = {'civilian': None, 'military_headgear': None, 'military_no_headgear': None, 'distinctive_marks': None}
        
        self.init_ui()
        self.load_data()
        self.setup_auto_save()
        self.setup_autocomplete_fields()
        
        # ✅ НОВОЕ: Настройка валидаторов согласно схеме БД
        self.setup_validators()

    def setup_validators(self):
        """
        Настройка валидации полей ввода согласно схеме базы данных
        """
        # 1. Валидатор для ФИО и Наименований (Буквы, цифры, пробелы, дефис)
        # Разрешает кириллицу, латиницу, цифры, пробелы и дефисы
        name_regex = QRegularExpression(r"^[а-яА-Яa-zA-Z0-9\s\-]+$")
        validator_names = QRegularExpressionValidator(name_regex)

        # 2. Валидатор для Банковской карты (Только цифры и пробелы)
        card_regex = QRegularExpression(r"^[0-9\s]+$")
        validator_card = QRegularExpressionValidator(card_regex)

        # 3. Валидатор для Паспортных данных (Буквы и цифры)
        doc_regex = QRegularExpression(r"^[а-яА-Яa-zA-Z0-9\s\-]+$")
        validator_doc = QRegularExpressionValidator(doc_regex)

        # === ПРИМЕНЕНИЕ ОГРАНИЧЕНИЙ (MaxLength + Validator) ===
        
        # --- ФИО и Личные данные (VARCHAR 100) ---
        self.surname_input.setMaxLength(100)
        self.surname_input.setValidator(validator_names)
        
        self.name_input.setMaxLength(100)
        self.name_input.setValidator(validator_names)
        
        self.patronymic_input.setMaxLength(100)
        self.patronymic_input.setValidator(validator_names)

        # --- Место рождения (VARCHAR 100) ---
        fields_100 = [
            self.birth_place_town_input, 
            self.birth_place_district_input, 
            self.birth_place_region_input, 
            self.birth_place_country_input
        ]
        for field in fields_100:
            field.setMaxLength(100)
            field.setValidator(validator_names)

        # --- Номера (VARCHAR 50) ---
        self.tab_number_input.setMaxLength(50)
        self.personal_number_input.setMaxLength(50)
        # Разрешим цифры и дефис для табельного номера
        num_regex = QRegularExpression(r"^[0-9\-]+$")
        self.tab_number_input.setValidator(QRegularExpressionValidator(num_regex))
        self.personal_number_input.setValidator(QRegularExpressionValidator(num_regex))

        # --- Военкоматы и ПОВСК (VARCHAR 255) ---
        fields_255 = [
            self.drafted_by_commissariat_input, 
            self.povsk_input, 
            self.education_input,
            self.passport_issued_by_input,
            self.military_id_issued_by_input,
            self.military_contacts_input
        ]
        for field in fields_255:
            field.setMaxLength(255)
            field.setValidator(validator_names)

        # --- Банковская карта (VARCHAR 50, только цифры) ---
        self.bank_card_number_input.setMaxLength(50)
        self.bank_card_number_input.setValidator(validator_card)

        # --- Соцсети (VARCHAR 255, допустим латиницу и спецсимволы для ссылок) ---
        social_regex = QRegularExpression(r"^[a-zA-Z0-9\-\.\_\@\:\?\/\&\=]+$")
        self.social_media_account_input.setMaxLength(255)
        self.social_media_account_input.setValidator(QRegularExpressionValidator(social_regex))

        # --- Паспортные данные ---
        # Серия паспорта (VARCHAR 10)
        self.passport_series_input.setMaxLength(10)
        self.passport_series_input.setValidator(validator_doc)
        
        # Номер паспорта (VARCHAR 20)
        self.passport_number_input.setMaxLength(20)
        self.passport_number_input.setValidator(validator_doc)

        # --- Военный билет ---
        # Серия ВБ (VARCHAR 10)
        self.military_id_series_input.setMaxLength(10)
        self.military_id_series_input.setValidator(validator_doc)
        
        # Номер ВБ (VARCHAR 20)
        self.military_id_number_input.setMaxLength(20)
        self.military_id_number_input.setValidator(validator_doc)

        print("✅ Валидаторы настроены согласно схеме БД")

    def _create_ref_combo_widget(self, combo, table_name, reload_func):
        """Вспомогательный метод: ComboBox + кнопка ⚙️"""
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(combo)
        
        btn = QPushButton("⚙️")
        btn.setToolTip(f"Настроить справочник: {table_name}")
        btn.setFixedSize(32, 32)
        btn.setStyleSheet("QPushButton { font-weight: bold; font-size: 15px; border-radius: 4px; background: #f8f9fa; border: 1px solid #ced4da; } QPushButton:hover { background: #e9ecef; }")
        
        def open_ref():
            dlg = ReferenceEditorDialog(self.db, self, initial_table=table_name)
            if dlg.exec() == 1:
                reload_func()
                
        btn.clicked.connect(open_ref)
        lay.addWidget(btn)
        return w

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

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
        
        g1.addWidget(QLabel("Категория военнослужащего:"), 2, 0)
        self.category_combo = QComboBox(); self.load_categories()
        g1.addWidget(self._create_ref_combo_widget(self.category_combo, 'categories', self.load_categories), 2, 1)
        
        g1.addWidget(QLabel("Воинское звание:"), 2, 2)
        self.rank_combo = QComboBox(); self.load_ranks()
        g1.addWidget(self._create_ref_combo_widget(self.rank_combo, 'ranks', self.load_ranks), 2, 3)
        
        group1.setLayout(g1); layout.addWidget(group1)

        group2 = QGroupBox("Место рождения")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g2 = QGridLayout(); g2.setSpacing(8)
        g2.addWidget(QLabel("Населенный пункт:"), 0, 0); self.birth_place_town_input = QLineEdit(); g2.addWidget(self.birth_place_town_input, 0, 1)
        g2.addWidget(QLabel("Административный район:"), 0, 2); self.birth_place_district_input = QLineEdit(); g2.addWidget(self.birth_place_district_input, 0, 3)
        g2.addWidget(QLabel("Субъект (регион):"), 1, 0); self.birth_place_region_input = QLineEdit(); g2.addWidget(self.birth_place_region_input, 1, 1)
        g2.addWidget(QLabel("Страна:"), 1, 2); self.birth_place_country_input = QLineEdit(); g2.addWidget(self.birth_place_country_input, 1, 3)
        g2.addWidget(QLabel("Дата рождения:"), 2, 0); self.birth_date_input = QDateEdit(); self.birth_date_input.setCalendarPopup(True); self.birth_date_input.setDate(QDate.currentDate()); g2.addWidget(self.birth_date_input, 2, 1)
        group2.setLayout(g2); layout.addWidget(group2)

        group3 = QGroupBox("Призыв")
        group3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g3 = QGridLayout(); g3.setSpacing(8)
        g3.addWidget(QLabel("Каким комиссариатом призван:"), 0, 0); self.drafted_by_commissariat_input = QLineEdit(); g3.addWidget(self.drafted_by_commissariat_input, 0, 1, 1, 3)
        g3.addWidget(QLabel("Дата призыва:"), 1, 0); self.draft_date_input = QDateEdit(); self.draft_date_input.setCalendarPopup(True); self.draft_date_input.setDate(QDate.currentDate()); g3.addWidget(self.draft_date_input, 1, 1)
        g3.addWidget(QLabel("Каким ПОВСК отобран:"), 1, 2); self.povsk_input = QLineEdit(); g3.addWidget(self.povsk_input, 1, 3)
        g3.addWidget(QLabel("Дата отбора:"), 2, 0); self.selection_date_input = QDateEdit(); self.selection_date_input.setCalendarPopup(True); self.selection_date_input.setDate(QDate.currentDate()); g3.addWidget(self.selection_date_input, 2, 1)
        group3.setLayout(g3); layout.addWidget(group3)

        group4 = QGroupBox("Образование и судимость")
        group4.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g4 = QGridLayout(); g4.setSpacing(8)
        g4.addWidget(QLabel("Образование:"), 0, 0); self.education_input = QLineEdit(); g4.addWidget(self.education_input, 0, 1, 1, 3)
        g4.addWidget(QLabel("Сведения о судимости:"), 1, 0); self.criminal_record_input = QTextEdit(); self.criminal_record_input.setMaximumHeight(60); g4.addWidget(self.criminal_record_input, 1, 1, 1, 3)
        g4.addWidget(QLabel("Аккаунт в соцсетях:"), 2, 0); self.social_media_account_input = QLineEdit(); g4.addWidget(self.social_media_account_input, 2, 1)
        g4.addWidget(QLabel("Номер банковской карты:"), 2, 2); self.bank_card_number_input = QLineEdit(); g4.addWidget(self.bank_card_number_input, 2, 3)
        group4.setLayout(g4); layout.addWidget(group4)

        group5 = QGroupBox("Паспортные данные")
        group5.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g5 = QGridLayout(); g5.setSpacing(8)
        g5.addWidget(QLabel("Серия паспорта:"), 0, 0); self.passport_series_input = QLineEdit(); g5.addWidget(self.passport_series_input, 0, 1)
        g5.addWidget(QLabel("Номер паспорта:"), 0, 2); self.passport_number_input = QLineEdit(); g5.addWidget(self.passport_number_input, 0, 3)
        g5.addWidget(QLabel("Дата выдачи:"), 1, 0); self.passport_issue_date_input = QDateEdit(); self.passport_issue_date_input.setCalendarPopup(True); self.passport_issue_date_input.setDate(QDate.currentDate()); g5.addWidget(self.passport_issue_date_input, 1, 1)
        g5.addWidget(QLabel("Кем выдан:"), 1, 2); self.passport_issued_by_input = QLineEdit(); g5.addWidget(self.passport_issued_by_input, 1, 3)
        group5.setLayout(g5); layout.addWidget(group5)

        group6 = QGroupBox("Военный билет (удостоверение личности)")
        group6.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        g6 = QGridLayout(); g6.setSpacing(8)
        g6.addWidget(QLabel("Серия:"), 0, 0); self.military_id_series_input = QLineEdit(); g6.addWidget(self.military_id_series_input, 0, 1)
        g6.addWidget(QLabel("Номер:"), 0, 2); self.military_id_number_input = QLineEdit(); g6.addWidget(self.military_id_number_input, 0, 3)
        g6.addWidget(QLabel("Дата выдачи:"), 1, 0); self.military_id_issue_date_input = QDateEdit(); self.military_id_issue_date_input.setCalendarPopup(True); self.military_id_issue_date_input.setDate(QDate.currentDate()); g6.addWidget(self.military_id_issue_date_input, 1, 1)
        g6.addWidget(QLabel("Кем выдан:"), 1, 2); self.military_id_issued_by_input = QLineEdit(); g6.addWidget(self.military_id_issued_by_input, 1, 3)
        group6.setLayout(g6); layout.addWidget(group6)

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
        layout.addStretch(); scroll.setWidget(container); main = QVBoxLayout(self); main.addWidget(scroll)

    def setup_autocomplete_fields(self):
        fields = [(self.surname_input, 'surname', 50), (self.name_input, 'name', 50), (self.patronymic_input, 'patronymic', 50), (self.tab_number_input, 'tab_number', 30), (self.personal_number_input, 'personal_number', 30), (self.birth_place_town_input, 'birth_place_town', 20), (self.birth_place_district_input, 'birth_place_district', 20), (self.birth_place_region_input, 'birth_place_region', 20), (self.birth_place_country_input, 'birth_place_country', 20), (self.drafted_by_commissariat_input, 'drafted_by_commissariat', 20), (self.povsk_input, 'povsk', 20), (self.education_input, 'education', 15), (self.social_media_account_input, 'social_media_account', 20), (self.bank_card_number_input, 'bank_card_number', 20), (self.passport_series_input, 'passport_series', 20), (self.passport_number_input, 'passport_number', 20), (self.passport_issued_by_input, 'passport_issued_by', 20), (self.military_id_series_input, 'military_id_series', 20), (self.military_id_number_input, 'military_id_number', 20), (self.military_id_issued_by_input, 'military_id_issued_by', 20), (self.military_contacts_input, 'military_contacts', 20)]
        for w, c, m in fields: self.autocomplete_helper.setup_autocomplete(w, 'social_data', c, max_items=m, show_on_focus=True)

    def load_categories(self):
        self.category_combo.clear(); self.category_combo.addItem("", None)
        q = QSqlQuery(self.db); q.exec("SELECT id, name FROM krd.categories ORDER BY name")
        while q.next(): self.category_combo.addItem(q.value(1), q.value(0))

    def load_ranks(self):
        self.rank_combo.clear(); self.rank_combo.addItem("", None)
        q = QSqlQuery(self.db); q.exec("SELECT id, name FROM krd.ranks ORDER BY name")
        while q.next(): self.rank_combo.addItem(q.value(1), q.value(0))

    def load_data(self):
        q = QSqlQuery(self.db); q.prepare("SELECT * FROM krd.social_data WHERE krd_id = ? ORDER BY id DESC LIMIT 1"); q.addBindValue(self.krd_id); q.exec()
        if q.next():
            self.record = q.record()
            self.surname_input.setText(q.value("surname") or ""); self.name_input.setText(q.value("name") or ""); self.patronymic_input.setText(q.value("patronymic") or ""); self.tab_number_input.setText(q.value("tab_number") or ""); self.personal_number_input.setText(q.value("personal_number") or "")
            c = q.value("category_id"); i = self.category_combo.findData(c) if c else -1; self.category_combo.setCurrentIndex(i) if i >= 0 else None
            r = q.value("rank_id"); i = self.rank_combo.findData(r) if r else -1; self.rank_combo.setCurrentIndex(i) if i >= 0 else None
            self.birth_place_town_input.setText(q.value("birth_place_town") or ""); self.birth_place_district_input.setText(q.value("birth_place_district") or ""); self.birth_place_region_input.setText(q.value("birth_place_region") or ""); self.birth_place_country_input.setText(q.value("birth_place_country") or "")
            bd = q.value("birth_date"); self.birth_date_input.setDate(bd) if bd else None
            self.drafted_by_commissariat_input.setText(q.value("drafted_by_commissariat") or ""); dd = q.value("draft_date"); self.draft_date_input.setDate(dd) if dd else None
            self.povsk_input.setText(q.value("povsk") or ""); sd = q.value("selection_date"); self.selection_date_input.setDate(sd) if sd else None
            self.education_input.setText(q.value("education") or ""); self.criminal_record_input.setPlainText(q.value("criminal_record") or ""); self.social_media_account_input.setText(q.value("social_media_account") or ""); self.bank_card_number_input.setText(q.value("bank_card_number") or "")
            self.passport_series_input.setText(q.value("passport_series") or ""); self.passport_number_input.setText(q.value("passport_number") or ""); pid = q.value("passport_issue_date"); self.passport_issue_date_input.setDate(pid) if pid else None; self.passport_issued_by_input.setText(q.value("passport_issued_by") or "")
            self.military_id_series_input.setText(q.value("military_id_series") or ""); self.military_id_number_input.setText(q.value("military_id_number") or ""); mid = q.value("military_id_issue_date"); self.military_id_issue_date_input.setDate(mid) if mid else None; self.military_id_issued_by_input.setText(q.value("military_id_issued_by") or "")
            self.appearance_features_input.setPlainText(q.value("appearance_features") or ""); self.personal_marks_input.setPlainText(q.value("personal_marks") or ""); self.federal_search_info_input.setPlainText(q.value("federal_search_info") or ""); self.military_contacts_input.setText(q.value("military_contacts") or ""); self.relatives_info_input.setPlainText(q.value("relatives_info") or "")
            self.load_photo_from_db(q, 'photo_civilian', self.photo_civilian_label, 'civilian')
            self.load_photo_from_db(q, 'photo_military_headgear', self.photo_military_headgear_label, 'military_headgear')
            self.load_photo_from_db(q, 'photo_military_no_headgear', self.photo_military_no_headgear_label, 'military_no_headgear')
            self.load_photo_from_db(q, 'photo_distinctive_marks', self.photo_distinctive_marks_label, 'distinctive_marks')

    def load_photo_from_db(self, query, field_name, label_widget, photo_type):
        pd = query.value(field_name); self.original_photos[photo_type] = None
        if pd and (isinstance(pd, bytes) or hasattr(pd, 'data')):
            try:
                b = bytes(pd.data()) if hasattr(pd, 'data') else bytes(pd)
                self.original_photos[photo_type] = b
                p = QPixmap(); p.loadFromData(b)
                if not p.isNull(): label_widget.setPixmap(p.scaled(180, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)); label_widget.setStyleSheet("QLabel { border: 2px solid #4CAF50; background-color: white; }")
                else: label_widget.setText("Ошибка загрузки")
            except: label_widget.setText("Ошибка")
        else: label_widget.setText("Нет фото"); label_widget.setStyleSheet("QLabel { border: 2px dashed #999; background-color: #f8f9fa; color: #6c757d; font-size: 12px; }")

    def load_photo(self, photo_type):
        path, _ = QFileDialog.getOpenFileName(self, f"Выберите фотографию ({photo_type})", "", "Изображения (*.png *.jpg *.jpeg *.bmp);;Все файлы (*)")
        if path:
            try:
                if os.path.getsize(path) > 5 * 1024 * 1024: return QMessageBox.warning(self, "Ошибка", "Размер файла не должен превышать 5 МБ")
                p = QPixmap(path); p = p.scaled(180, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                getattr(self, f'photo_{photo_type}_label').setPixmap(p); getattr(self, f'photo_{photo_type}_label').setStyleSheet("QLabel { border: 2px solid #2196F3; background-color: white; }")
                self.photo_paths[photo_type] = path
            except Exception as e: QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {e}")

    def export_photo(self, photo_type):
        b = None
        if self.photo_paths.get(photo_type) and os.path.exists(self.photo_paths[photo_type]):
            with open(self.photo_paths[photo_type], 'rb') as f: b = f.read()
        elif self.original_photos.get(photo_type): b = self.original_photos[photo_type]
        if not b: return QMessageBox.information(self, "Информация", f"Фото '{photo_type}' отсутствует.")
        path, _ = QFileDialog.getSaveFileName(self, f"Сохранить фото ({photo_type})", f"КРД-{self.krd_id}_{photo_type}.jpg", "Изображения (*.jpg *.png *.bmp);;Все файлы (*)")
        if path:
            try:
                with open(path, 'wb') as f: f.write(b)
                QMessageBox.information(self, "Успешно", f"Фото сохранено: {path}")
                if self.audit_logger: self.audit_logger.log_action('PHOTO_EXPORT', 'social_data', self.krd_id, self.krd_id, f'Выгружено фото "{photo_type}"')
            except Exception as e: QMessageBox.critical(self, "Ошибка", str(e))

    def save_data(self):
        err = self.validate_required_fields()
        if err: raise ValueError(err)
        
        # Дополнительная проверка длины для QTextEdit (так как у них нет setMaxLength)
        if len(self.criminal_record_input.toPlainText()) > 5000: # TEXT limit check example
             raise ValueError("Поле 'Сведения о судимости' слишком длинное")

        data = {"krd_id": self.krd_id, "surname": self.surname_input.text().strip(), "name": self.name_input.text().strip(), "patronymic": self.patronymic_input.text().strip(), "birth_date": self.birth_date_input.date(), "birth_place_town": self.birth_place_town_input.text().strip(), "birth_place_district": self.birth_place_district_input.text().strip(), "birth_place_region": self.birth_place_region_input.text().strip(), "birth_place_country": self.birth_place_country_input.text().strip(), "tab_number": self.tab_number_input.text().strip(), "personal_number": self.personal_number_input.text().strip(), "category_id": self.category_combo.currentData(), "rank_id": self.rank_combo.currentData(), "drafted_by_commissariat": self.drafted_by_commissariat_input.text().strip(), "draft_date": self.draft_date_input.date(), "povsk": self.povsk_input.text().strip(), "selection_date": self.selection_date_input.date(), "education": self.education_input.text().strip(), "criminal_record": self.criminal_record_input.toPlainText(), "social_media_account": self.social_media_account_input.text().strip(), "bank_card_number": self.bank_card_number_input.text().strip(), "passport_series": self.passport_series_input.text().strip(), "passport_number": self.passport_number_input.text().strip(), "passport_issue_date": self.passport_issue_date_input.date(), "passport_issued_by": self.passport_issued_by_input.text().strip(), "military_id_series": self.military_id_series_input.text().strip(), "military_id_number": self.military_id_number_input.text().strip(), "military_id_issue_date": self.military_id_issue_date_input.date(), "military_id_issued_by": self.military_id_issued_by_input.text().strip(), "appearance_features": self.appearance_features_input.toPlainText(), "personal_marks": self.personal_marks_input.toPlainText(), "federal_search_info": self.federal_search_info_input.toPlainText(), "military_contacts": self.military_contacts_input.text().strip(), "relatives_info": self.relatives_info_input.toPlainText()}
        
        for pt in ['civilian', 'military_headgear', 'military_no_headgear', 'distinctive_marks']:
            p = self.photo_paths.get(pt); fb = None
            if p and os.path.exists(p):
                with open(p, 'rb') as f: fb = f.read()
            elif self.original_photos.get(pt): fb = self.original_photos[pt]
            data[f"photo_{pt}"] = QByteArray(fb) if fb else QByteArray()
            
        q = QSqlQuery(self.db)
        if self.record:
            q.prepare("""UPDATE krd.social_data SET surname=:surname, name=:name, patronymic=:patronymic, birth_date=:birth_date, birth_place_town=:birth_place_town, birth_place_district=:birth_place_district, birth_place_region=:birth_place_region, birth_place_country=:birth_place_country, tab_number=:tab_number, personal_number=:personal_number, category_id=:category_id, rank_id=:rank_id, drafted_by_commissariat=:drafted_by_commissariat, draft_date=:draft_date, povsk=:povsk, selection_date=:selection_date, education=:education, criminal_record=:criminal_record, social_media_account=:social_media_account, bank_card_number=:bank_card_number, passport_series=:passport_series, passport_number=:passport_number, passport_issue_date=:passport_issue_date, passport_issued_by=:passport_issued_by, military_id_series=:military_id_series, military_id_number=:military_id_number, military_id_issue_date=:military_id_issue_date, military_id_issued_by=:military_id_issued_by, appearance_features=:appearance_features, personal_marks=:personal_marks, federal_search_info=:federal_search_info, military_contacts=:military_contacts, relatives_info=:relatives_info, photo_civilian=:photo_civilian, photo_military_headgear=:photo_military_headgear, photo_military_no_headgear=:photo_military_no_headgear, photo_distinctive_marks=:photo_distinctive_marks WHERE id=:id""")
            q.bindValue(":id", self.record.value("id"))
        else:
            q.prepare("""INSERT INTO krd.social_data (krd_id, surname, name, patronymic, birth_date, birth_place_town, birth_place_district, birth_place_region, birth_place_country, tab_number, personal_number, category_id, rank_id, drafted_by_commissariat, draft_date, povsk, selection_date, education, criminal_record, social_media_account, bank_card_number, passport_series, passport_number, passport_issue_date, passport_issued_by, military_id_series, military_id_number, military_id_issue_date, military_id_issued_by, appearance_features, personal_marks, federal_search_info, military_contacts, relatives_info, photo_civilian, photo_military_headgear, photo_military_no_headgear, photo_distinctive_marks) VALUES (:krd_id, :surname, :name, :patronymic, :birth_date, :birth_place_town, :birth_place_district, :birth_place_region, :birth_place_country, :tab_number, :personal_number, :category_id, :rank_id, :drafted_by_commissariat, :draft_date, :povsk, :selection_date, :education, :criminal_record, :social_media_account, :bank_card_number, :passport_series, :passport_number, :passport_issue_date, :passport_issued_by, :military_id_series, :military_id_number, :military_id_issue_date, :military_id_issued_by, :appearance_features, :personal_marks, :federal_search_info, :military_contacts, :relatives_info, :photo_civilian, :photo_military_headgear, :photo_military_no_headgear, :photo_distinctive_marks)""")
            
        for k, v in data.items(): q.bindValue(f":{k}", v)
        if not q.exec(): raise Exception(f"Ошибка сохранения: {q.lastError().text()}")
        self.autocomplete_helper.refresh_all_fields()

    def validate_required_fields(self):
        if not self.surname_input.text().strip(): return "Поле 'Фамилия' обязательно"
        if not self.name_input.text().strip(): return "Поле 'Имя' обязательно"
        if not self.patronymic_input.text().strip(): return "Поле 'Отчество' обязательно"
        return None

    def setup_auto_save(self):
        self._auto_save_timer = QTimer(self); self._auto_save_timer.setSingleShot(True); self._auto_save_timer.timeout.connect(self._perform_auto_save)
        for w in [self.surname_input, self.name_input, self.patronymic_input, self.tab_number_input, self.personal_number_input, self.birth_place_town_input, self.birth_place_district_input, self.birth_place_region_input, self.birth_place_country_input, self.drafted_by_commissariat_input, self.povsk_input, self.education_input, self.social_media_account_input, self.bank_card_number_input, self.passport_series_input, self.passport_number_input, self.passport_issued_by_input, self.military_id_series_input, self.military_id_number_input, self.military_id_issued_by_input, self.military_contacts_input, self.criminal_record_input, self.appearance_features_input, self.personal_marks_input, self.federal_search_info_input, self.relatives_info_input]: w.textChanged.connect(self._on_field_changed)
        for w in [self.birth_date_input, self.draft_date_input, self.selection_date_input, self.passport_issue_date_input, self.military_id_issue_date_input]: w.dateChanged.connect(self._on_field_changed)
        for w in [self.category_combo, self.rank_combo]: w.currentIndexChanged.connect(self._on_field_changed)
    def _on_field_changed(self): self._auto_save_timer.start(400)
    def _perform_auto_save(self):
        try: self.save_data()
        except ValueError: pass
        except Exception as e: print(f"⚠️ Ошибка автосохранения: {e}")