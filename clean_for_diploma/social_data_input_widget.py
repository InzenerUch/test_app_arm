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
from autocomplete_helper import AutocompleteHelper
from reference_editor_dialog import ReferenceEditorDialog
class SocialDataInputWidget(QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.parent_window = parent
        self.audit_logger = getattr(parent, 'audit_logger', None)
        self.photo_paths = {
            'civilian': None, 'military_headgear': None,
            'military_no_headgear': None, 'distinctive_marks': None
        }
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        self.init_ui()
        self.load_combo_data()
        self._setup_validators_and_autocomplete()
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        g1 = QGroupBox("👤 Основные данные (все поля необязательны)")
        g1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l1 = QGridLayout(); l1.setSpacing(8)
        self.surname_input = QLineEdit(); self.surname_input.setPlaceholderText("Фамилия")
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("Имя")
        self.patronymic_input = QLineEdit(); self.patronymic_input.setPlaceholderText("Отчество")
        self.tab_number_input = QLineEdit(); self.tab_number_input.setPlaceholderText("Например: 123456")
        self.personal_number_input = QLineEdit(); self.personal_number_input.setPlaceholderText("Личный номер")
        self.category_combo = QComboBox()
        self.rank_combo = QComboBox()
        l1.addWidget(QLabel("Фамилия:"), 0, 0); l1.addWidget(self.surname_input, 0, 1)
        l1.addWidget(QLabel("Имя:"), 0, 2); l1.addWidget(self.name_input, 0, 3)
        l1.addWidget(QLabel("Отчество:"), 0, 4); l1.addWidget(self.patronymic_input, 0, 5)
        l1.addWidget(QLabel("Табельный номер:"), 1, 0); l1.addWidget(self.tab_number_input, 1, 1)
        l1.addWidget(QLabel("Личный номер:"), 1, 2); l1.addWidget(self.personal_number_input, 1, 3)
        l1.addWidget(QLabel("Категория:"), 2, 0)
        l1.addWidget(self._create_ref_combo_widget(self.category_combo, 'categories', self.load_categories), 2, 1)
        l1.addWidget(QLabel("Звание:"), 2, 2)
        l1.addWidget(self._create_ref_combo_widget(self.rank_combo, 'ranks', self.load_ranks), 2, 3)
        g1.setLayout(l1); layout.addWidget(g1)
        g2 = QGroupBox("🌍 Место рождения")
        g2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l2 = QGridLayout(); l2.setSpacing(8)
        self.birth_place_town_input = QLineEdit()
        self.birth_place_district_input = QLineEdit()
        self.birth_place_region_input = QLineEdit()
        self.birth_place_country_input = QLineEdit()
        self.birth_date_input = QDateEdit(); self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setMaximumDate(QDate.currentDate())
        self.birth_date_input.setSpecialValueText("Не указано")
        l2.addWidget(QLabel("Населенный пункт:"), 0, 0); l2.addWidget(self.birth_place_town_input, 0, 1)
        l2.addWidget(QLabel("Район:"), 0, 2); l2.addWidget(self.birth_place_district_input, 0, 3)
        l2.addWidget(QLabel("Регион:"), 1, 0); l2.addWidget(self.birth_place_region_input, 1, 1)
        l2.addWidget(QLabel("Страна:"), 1, 2); l2.addWidget(self.birth_place_country_input, 1, 3)
        l2.addWidget(QLabel("Дата рождения:"), 2, 0); l2.addWidget(self.birth_date_input, 2, 1)
        g2.setLayout(l2); layout.addWidget(g2)
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
        g4 = QGroupBox("📄 Паспортные данные")
        g4.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l4 = QGridLayout(); l4.setSpacing(8)
        self.passport_series_input = QLineEdit(); self.passport_series_input.setPlaceholderText("Серия (4 цифры)")
        self.passport_number_input = QLineEdit(); self.passport_number_input.setPlaceholderText("Номер (6 цифр)")
        self.passport_issue_date_input = QDateEdit(); self.passport_issue_date_input.setCalendarPopup(True)
        self.passport_issue_date_input.setMaximumDate(QDate.currentDate())
        self.passport_issued_by_input = QLineEdit()
        l4.addWidget(QLabel("Серия:"), 0, 0); l4.addWidget(self.passport_series_input, 0, 1)
        l4.addWidget(QLabel("Номер:"), 0, 2); l4.addWidget(self.passport_number_input, 0, 3)
        l4.addWidget(QLabel("Дата выдачи:"), 1, 0); l4.addWidget(self.passport_issue_date_input, 1, 1)
        l4.addWidget(QLabel("Кем выдан:"), 1, 2); l4.addWidget(self.passport_issued_by_input, 1, 3)
        g4.setLayout(l4); layout.addWidget(g4)
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
            photo_lbl.setStyleSheet("QLabel { border: 2px dashed
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
    def _create_ref_combo_widget(self, combo, table_name, reload_func):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(combo, 1)
        btn = QPushButton("⚙️")
        btn.setToolTip(f"Настроить справочник: {table_name}")
        btn.setFixedSize(32, 32)
        btn.setFont(QFont("Segoe UI Emoji", 12))
        btn.setProperty("role", "edit")
        btn.clicked.connect(lambda: self.open_ref_editor(table_name, reload_func))
        lay.addWidget(btn)
        return w
    def open_ref_editor(self, table_name, reload_func):
        try:
            parent_window = self.parent_window or self.parent()
            dialog = ReferenceEditorDialog(self.db, parent_window, initial_table=table_name)
            dialog.data_changed.connect(reload_func)
            dialog.exec()
        except Exception as e:
            print(f"⚠️ Ошибка открытия редактора справочников: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть справочник: {str(e)}")
    def load_categories(self):
        current_id = self.category_combo.currentData()
        self.category_combo.clear()
        self.category_combo.addItem("", None)
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.categories ORDER BY name")
        while q.next(): self.category_combo.addItem(q.value(1), q.value(0))
        if current_id is not None:
            idx = self.category_combo.findData(current_id)
            if idx >= 0: self.category_combo.setCurrentIndex(idx)
    def load_ranks(self):
        current_id = self.rank_combo.currentData()
        self.rank_combo.clear()
        self.rank_combo.addItem("", None)
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.ranks ORDER BY name")
        while q.next(): self.rank_combo.addItem(q.value(1), q.value(0))
        if current_id is not None:
            idx = self.rank_combo.findData(current_id)
            if idx >= 0: self.rank_combo.setCurrentIndex(idx)
    def load_combo_data(self):
        self.load_categories()
        self.load_ranks()
    def _setup_validators_and_autocomplete(self):
        for w, l in [(self.surname_input, 100), (self.name_input, 100), (self.patronymic_input, 100),
                     (self.birth_place_town_input, 100), (self.birth_place_district_input, 100),
                     (self.birth_place_region_input, 100), (self.birth_place_country_input, 100),
                     (self.tab_number_input, 50), (self.personal_number_input, 50),
                     (self.drafted_by_commissariat_input, 255), (self.povsk_input, 255),
                     (self.education_input, 255), (self.social_media_account_input, 255),
                     (self.military_contacts_input, 255), (self.passport_issued_by_input, 255),
                     (self.military_id_issued_by_input, 255), (self.passport_series_input, 4),
                     (self.passport_number_input, 6), (self.military_id_series_input, 10),
                     (self.military_id_number_input, 10), (self.bank_card_number_input, 19)]:
            w.setMaxLength(l)
        self.passport_series_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{4}$")))
        self.passport_number_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{6}$")))
        self.military_id_series_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[A-Za-z0-9\-]{1,10}$")))
        self.military_id_number_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{5,10}$")))
        self.bank_card_number_input.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[\d\s]{16,19}$")))
        autocomplete_config = [
            (self.surname_input, 'surname', 50), (self.name_input, 'name', 50),
            (self.patronymic_input, 'patronymic', 50), (self.birth_place_town_input, 'birth_place_town', 20),
            (self.birth_place_district_input, 'birth_place_district', 20), (self.birth_place_region_input, 'birth_place_region', 20),
            (self.birth_place_country_input, 'birth_place_country', 20), (self.tab_number_input, 'tab_number', 30),
            (self.personal_number_input, 'personal_number', 30), (self.drafted_by_commissariat_input, 'drafted_by_commissariat', 20),
            (self.povsk_input, 'povsk', 20), (self.education_input, 'education', 15),
            (self.social_media_account_input, 'social_media_account', 20), (self.bank_card_number_input, 'bank_card_number', 20),
            (self.passport_series_input, 'passport_series', 10), (self.passport_number_input, 'passport_number', 10),
            (self.passport_issued_by_input, 'passport_issued_by', 20), (self.military_id_series_input, 'military_id_series', 10),
            (self.military_id_number_input, 'military_id_number', 10), (self.military_id_issued_by_input, 'military_id_issued_by', 20),
            (self.military_contacts_input, 'military_contacts', 20),
        ]
        for widget, col, max_items in autocomplete_config:
            self.autocomplete_helper.setup_autocomplete(widget, 'social_data', col, max_items=max_items, show_on_focus=True)
    def load_photo(self, photo_type):
        path, _ = QFileDialog.getOpenFileName(self, f"Выберите фото ({photo_type})", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            try:
                if os.path.getsize(path) > 5 * 1024 * 1024: return QMessageBox.warning(self, "Ошибка", "Файл превышает 5 МБ")
                p = QPixmap(path)
                if p.isNull(): return
                lbl = getattr(self, f'photo_{photo_type}_label')
                lbl.setPixmap(p.scaled(150, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                lbl.setStyleSheet("QLabel { border: 2px solid
                self.photo_paths[photo_type] = path
            except Exception as e: QMessageBox.critical(self, "Ошибка", str(e))
    def _load_pixmap(self, path):
        p = QPixmap(path)
        if p.isNull(): return None
        return p.scaled(150, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    def validate_all_fields(self):
        errors = []
        def check_fmt(widget, regex, msg):
            txt = widget.text().strip()
            if txt and not QRegularExpressionValidator(QRegularExpression(regex)).validate(txt, 0)[0] == 0:
                errors.append(msg)
        check_fmt(self.passport_series_input, r"^\d{4}$", "Серия паспорта: ровно 4 цифры")
        check_fmt(self.passport_number_input, r"^\d{6}$", "Номер паспорта: ровно 6 цифр")
        check_fmt(self.military_id_series_input, r"^[A-Za-z0-9\-]{1,10}$", "Серия ВБ: буквы, цифры, дефис (1-10)")
        check_fmt(self.military_id_number_input, r"^\d{5,10}$", "Номер ВБ: цифры (5-10)")
        check_fmt(self.bank_card_number_input, r"^[\d\s]{16,19}$", "Карта: 16-19 цифр/пробелов")
        b, d, s = self.birth_date_input.date(), self.draft_date_input.date(), self.selection_date_input.date()
        if b.isValid() and d.isValid() and d < b: errors.append("Дата призыва раньше даты рождения")
        if b.isValid() and s.isValid() and s < b: errors.append("Дата отбора раньше даты рождения")
        if d.isValid() and s.isValid() and s < d: errors.append("Дата отбора раньше даты призыва")
        if errors: return False, "Обнаружены ошибки:\n" + "\n".join(f"• {e}" for e in errors)
        return True, ""
    def get_data(self):
        def safe_get(widget, is_text=True):
            val = widget.text().strip() if is_text else widget.toPlainText().strip()
            return val if val else None
        data = {
            'surname': safe_get(self.surname_input), 'name': safe_get(self.name_input),
            'patronymic': safe_get(self.patronymic_input), 'birth_date': self.birth_date_input.date() if self.birth_date_input.date().isValid() else None,
            'birth_place_town': safe_get(self.birth_place_town_input), 'birth_place_district': safe_get(self.birth_place_district_input),
            'birth_place_region': safe_get(self.birth_place_region_input), 'birth_place_country': safe_get(self.birth_place_country_input),
            'tab_number': safe_get(self.tab_number_input), 'personal_number': safe_get(self.personal_number_input),
            'category_id': self.category_combo.currentData(), 'rank_id': self.rank_combo.currentData(),
            'drafted_by_commissariat': safe_get(self.drafted_by_commissariat_input), 'draft_date': self.draft_date_input.date() if self.draft_date_input.date().isValid() else None,
            'povsk': safe_get(self.povsk_input), 'selection_date': self.selection_date_input.date() if self.selection_date_input.date().isValid() else None,
            'education': safe_get(self.education_input), 'criminal_record': safe_get(self.criminal_record_input, False),
            'social_media_account': safe_get(self.social_media_account_input), 'bank_card_number': safe_get(self.bank_card_number_input),
            'federal_search_info': safe_get(self.federal_search_info_input, False), 'military_contacts': safe_get(self.military_contacts_input),
            'relatives_info': safe_get(self.relatives_info_input, False), 'passport_series': safe_get(self.passport_series_input),
            'passport_number': safe_get(self.passport_number_input), 'passport_issue_date': self.passport_issue_date_input.date() if self.passport_issue_date_input.date().isValid() else None,
            'passport_issued_by': safe_get(self.passport_issued_by_input), 'military_id_series': safe_get(self.military_id_series_input),
            'military_id_number': safe_get(self.military_id_number_input), 'military_id_issue_date': self.military_id_issue_date_input.date() if self.military_id_issue_date_input.date().isValid() else None,
            'military_id_issued_by': safe_get(self.military_id_issued_by_input),
            'appearance_features': "", 'personal_marks': ""
        }
        for key in ['civilian', 'military_headgear', 'military_no_headgear', 'distinctive_marks']:
            path = self.photo_paths.get(key)
            if path and os.path.exists(path):
                with open(path, 'rb') as f: data[f'photo_{key}'] = QByteArray(f.read())
            else:
                data[f'photo_{key}'] = QByteArray()
        return data