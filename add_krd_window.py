from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QLabel
)
from PyQt6.QtCore import Qt, QDate, QByteArray
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlQuery
import os
import traceback

from social_data_input_widget import SocialDataInputWidget


class AddKrdWindow(QDialog):
    """Окно быстрого создания КРД (только соц. данные)"""
    def __init__(self, db_connection, audit_logger=None):
        super().__init__()
        self.db = db_connection
        self.audit_logger = audit_logger
        self.setWindowTitle("➕ Добавление новой карточки розыска (КРД)")
        self.setModal(True)
        self.resize(1000, 850)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("➕ Создание новой карточки розыска")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        info = QLabel("💡 Заполните основные социально-демографические данные. "
                      "Адреса, поручения, места службы и эпизоды СОЧ можно добавить позже в окне редактирования.")
        info.setWordWrap(True)
        info.setStyleSheet("QLabel { color: #666; background: #f0f0f0; padding: 10px; border-radius: 5px; }")
        layout.addWidget(info)
        
        self.social_widget = SocialDataInputWidget(self.db)
        layout.addWidget(self.social_widget)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("💾 Создать КРД")
        save_btn.setMinimumHeight(45)
        save_btn.setProperty("role", "save")
        save_btn.clicked.connect(self.save_krd)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setProperty("role", "danger")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_krd(self):
        valid, msg = self.social_widget.validate_required_fields()
        if not valid:
            return QMessageBox.warning(self, "Ошибка валидации", msg)
            
        reply = QMessageBox.question(self, "Подтверждение", 
            "Создать новую карточку розыска?\nОстальные данные можно будет заполнить позже.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return

        try:
            if not self.db.transaction():
                raise Exception("Не удалось начать транзакцию")
            
            # 1. Создаём КРД
            q = QSqlQuery(self.db)
            q.prepare("INSERT INTO krd.krd DEFAULT VALUES RETURNING id")
            if not q.exec() or not q.next():
                raise Exception("Ошибка создания КРД")
            krd_id = q.value(0)
            
            # 2. Сохраняем соц. данные
            data = self.social_widget.get_data()
            data['krd_id'] = krd_id
            
            q2 = QSqlQuery(self.db)
            q2.prepare("""
                INSERT INTO krd.social_data (
                    krd_id, surname, name, patronymic, birth_date, birth_place_town,
                    birth_place_district, birth_place_region, birth_place_country, tab_number,
                    personal_number, category_id, rank_id, drafted_by_commissariat, draft_date,
                    povsk, selection_date, education, criminal_record, social_media_account,
                    bank_card_number, federal_search_info, military_contacts, relatives_info,
                    passport_series, passport_number, passport_issue_date, passport_issued_by,
                    military_id_series, military_id_number, military_id_issue_date, military_id_issued_by,
                    appearance_features, personal_marks,
                    photo_civilian, photo_military_headgear, photo_military_no_headgear, photo_distinctive_marks
                ) VALUES (
                    :krd_id, :surname, :name, :patronymic, :birth_date, :birth_place_town,
                    :birth_place_district, :birth_place_region, :birth_place_country, :tab_number,
                    :personal_number, :category_id, :rank_id, :drafted_by_commissariat, :draft_date,
                    :povsk, :selection_date, :education, :criminal_record, :social_media_account,
                    :bank_card_number, :federal_search_info, :military_contacts, :relatives_info,
                    :passport_series, :passport_number, :passport_issue_date, :passport_issued_by,
                    :military_id_series, :military_id_number, :military_id_issue_date, :military_id_issued_by,
                    :appearance_features, :personal_marks,
                    :photo_civilian, :photo_military_headgear, :photo_military_no_headgear, :photo_distinctive_marks
                )
            """)
            for k, v in data.items():
                q2.bindValue(f":{k}", v)
            if not q2.exec():
                raise Exception(f"Ошибка сохранения соц. данных: {q2.lastError().text()}")
            
            if not self.db.commit():
                raise Exception("Ошибка коммита")
                
            if self.audit_logger:
                self.audit_logger.log_krd_create(krd_id, {
                    'surname': data.get('surname'), 'name': data.get('name'), 'patronymic': data.get('patronymic')
                })
                
            QMessageBox.information(self, "Успех", f"✅ КРД-{krd_id} успешно создана!\nЗаполните остальные данные позже.")
            self.accept()
            
        except Exception as e:
            self.db.rollback()
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать КРД:\n{str(e)}")