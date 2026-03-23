"""
Диалоговое окно для добавления/редактирования эпизода СОЧ
С поддержкой автодополнения текстовых полей
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QDateEdit, QLabel, QPushButton,
    QMessageBox, QScrollArea, QWidget, QDialogButtonBox
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont

from autocomplete_helper import AutocompleteHelper


class SochEpisodeDialog(QDialog):
    """Диалог для добавления/редактирования эпизода СОЧ"""
    
    def __init__(self, db_connection, krd_id, episode_data=None, parent=None):
        """
        Args:
            db_connection: соединение с БД
            krd_id: ID карточки розыска
            episode_data: данные эпизода для редактирования (None для нового)
            parent: родительское окно
        """
        super().__init__(parent)
        self.db = db_connection
        self.krd_id = krd_id
        self.episode_data = episode_data
        self.is_edit = episode_data is not None
        self.episode_id = episode_data.get('id') if episode_data else None
        
        # === ИНИЦИАЛИЗАЦИЯ ПОМОЩНИКА АВТОДОПОЛНЕНИЯ ===
        self.autocomplete_helper = AutocompleteHelper(db_connection)
        
        self.setWindowTitle("✏️ Редактирование эпизода СОЧ" if self.is_edit else "➕ Добавление эпизода СОЧ")
        self.setMinimumSize(900, 750)
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
        title_label = QLabel("✏️ Редактирование эпизода СОЧ" if self.is_edit else "➕ Добавление эпизода СОЧ")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Область прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        form_layout = QVBoxLayout(container)
        form_layout.setSpacing(10)
        
        # === Группа 1: Основная информация ===
        group1 = QGroupBox("📋 Основная информация")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group1_layout = QGridLayout()
        group1_layout.setSpacing(8)
        
        group1_layout.addWidget(QLabel("Дата СОЧ *:"), 0, 0)
        self.soch_date_input = QDateEdit()
        self.soch_date_input.setCalendarPopup(True)
        self.soch_date_input.setDate(QDate.currentDate())
        group1_layout.addWidget(self.soch_date_input, 0, 1)
        
        group1_layout.addWidget(QLabel("Место СОЧ:"), 0, 2)
        self.soch_location_input = QLineEdit()
        self.soch_location_input.setPlaceholderText("Например: г. Москва, в/ч 12345")
        group1_layout.addWidget(self.soch_location_input, 0, 3)
        
        group1_layout.addWidget(QLabel("Дата и номер приказа о СОЧ:"), 1, 0)
        self.order_date_number_input = QLineEdit()
        self.order_date_number_input.setPlaceholderText("Например: №123 от 15.01.2024")
        group1_layout.addWidget(self.order_date_number_input, 1, 1, 1, 3)
        
        group1.setLayout(group1_layout)
        form_layout.addWidget(group1)
        
        # === Группа 2: Обстоятельства СОЧ ===
        group2 = QGroupBox("🔍 Обстоятельства СОЧ")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group2_layout = QGridLayout()
        group2_layout.setSpacing(8)
        
        group2_layout.addWidget(QLabel("Очевидцы СОЧ:"), 0, 0)
        self.witnesses_input = QTextEdit()
        self.witnesses_input.setMaximumHeight(60)
        self.witnesses_input.setPlaceholderText("ФИО очевидцев, контакты")
        group2_layout.addWidget(self.witnesses_input, 0, 1, 1, 3)
        
        group2_layout.addWidget(QLabel("Вероятные причины СОЧ:"), 1, 0)
        self.reasons_input = QTextEdit()
        self.reasons_input.setMaximumHeight(60)
        self.reasons_input.setPlaceholderText("Предполагаемые причины")
        group2_layout.addWidget(self.reasons_input, 1, 1, 1, 3)
        
        group2_layout.addWidget(QLabel("Сведения о наличии оружия:"), 2, 0)
        self.weapon_info_input = QTextEdit()
        self.weapon_info_input.setMaximumHeight(60)
        self.weapon_info_input.setPlaceholderText("Какое оружие имел при себе")
        group2_layout.addWidget(self.weapon_info_input, 2, 1, 1, 3)
        
        group2_layout.addWidget(QLabel("Во что был одет:"), 3, 0)
        self.clothing_input = QTextEdit()
        self.clothing_input.setMaximumHeight(60)
        self.clothing_input.setPlaceholderText("Описание одежды и обуви")
        group2_layout.addWidget(self.clothing_input, 3, 1, 1, 3)
        
        group2_layout.addWidget(QLabel("Варианты движения:"), 4, 0)
        self.movement_options_input = QTextEdit()
        self.movement_options_input.setMaximumHeight(60)
        self.movement_options_input.setPlaceholderText("Возможные направления движения")
        group2_layout.addWidget(self.movement_options_input, 4, 1, 1, 3)
        
        group2_layout.addWidget(QLabel("Другая значимая информация:"), 5, 0)
        self.other_info_input = QTextEdit()
        self.other_info_input.setMaximumHeight(60)
        self.other_info_input.setPlaceholderText("Дополнительная информация")
        group2_layout.addWidget(self.other_info_input, 5, 1, 1, 3)
        
        group2.setLayout(group2_layout)
        form_layout.addWidget(group2)
        
        # === Группа 3: Контакты и проверка ===
        group3 = QGroupBox("📞 Контакты и проверка")
        group3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group3_layout = QGridLayout()
        group3_layout.setSpacing(8)
        
        group3_layout.addWidget(QLabel("Контакт дежурного по ВК:"), 0, 0)
        self.duty_officer_commissariat_input = QLineEdit()
        self.duty_officer_commissariat_input.setPlaceholderText("ФИО, телефон")
        group3_layout.addWidget(self.duty_officer_commissariat_input, 0, 1, 1, 3)
        
        group3_layout.addWidget(QLabel("Контакт дежурного по ОМВД:"), 1, 0)
        self.duty_officer_omvd_input = QLineEdit()
        self.duty_officer_omvd_input.setPlaceholderText("ФИО, телефон")
        group3_layout.addWidget(self.duty_officer_omvd_input, 1, 1, 1, 3)
        
        group3_layout.addWidget(QLabel("Сведения о проверке:"), 2, 0)
        self.investigation_info_input = QTextEdit()
        self.investigation_info_input.setMaximumHeight(60)
        self.investigation_info_input.setPlaceholderText("Результаты проверки")
        group3_layout.addWidget(self.investigation_info_input, 2, 1, 1, 3)
        
        group3_layout.addWidget(QLabel("Сведения о прокуратуре:"), 3, 0)
        self.prosecution_info_input = QTextEdit()
        self.prosecution_info_input.setMaximumHeight(60)
        self.prosecution_info_input.setPlaceholderText("Информация из прокуратуры")
        group3_layout.addWidget(self.prosecution_info_input, 3, 1, 1, 3)
        
        group3_layout.addWidget(QLabel("Сведения об уголовном деле:"), 4, 0)
        self.criminal_case_info_input = QTextEdit()
        self.criminal_case_info_input.setMaximumHeight(60)
        self.criminal_case_info_input.setPlaceholderText("Номер дела, статья УК")
        group3_layout.addWidget(self.criminal_case_info_input, 4, 1, 1, 3)
        
        group3.setLayout(group3_layout)
        form_layout.addWidget(group3)
        
        # === Группа 4: Розыск и уведомление ===
        group4 = QGroupBox("🚔 Розыск и уведомление")
        group4.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group4_layout = QGridLayout()
        group4_layout.setSpacing(8)
        
        group4_layout.addWidget(QLabel("Дата розыска:"), 0, 0)
        self.search_date_input = QDateEdit()
        self.search_date_input.setCalendarPopup(True)
        self.search_date_input.setDate(QDate.currentDate())
        group4_layout.addWidget(self.search_date_input, 0, 1)
        
        group4_layout.addWidget(QLabel("Кем разыскан:"), 0, 2)
        self.found_by_input = QLineEdit()
        self.found_by_input.setPlaceholderText("Например: Полиция, ВК")
        group4_layout.addWidget(self.found_by_input, 0, 3)
        
        group4_layout.addWidget(QLabel("Обстоятельства розыска:"), 1, 0)
        self.search_circumstances_input = QTextEdit()
        self.search_circumstances_input.setMaximumHeight(60)
        self.search_circumstances_input.setPlaceholderText("Как и где был найден")
        group4_layout.addWidget(self.search_circumstances_input, 1, 1, 1, 3)
        
        group4_layout.addWidget(QLabel("Адресат уведомления:"), 2, 0)
        self.notification_recipient_input = QLineEdit()
        self.notification_recipient_input.setPlaceholderText("Кому направлено уведомление")
        group4_layout.addWidget(self.notification_recipient_input, 2, 1, 1, 3)
        
        group4_layout.addWidget(QLabel("Дата уведомления:"), 3, 0)
        self.notification_date_input = QDateEdit()
        self.notification_date_input.setCalendarPopup(True)
        self.notification_date_input.setDate(QDate.currentDate())
        group4_layout.addWidget(self.notification_date_input, 3, 1)
        
        group4_layout.addWidget(QLabel("Номер уведомления:"), 3, 2)
        self.notification_number_input = QLineEdit()
        self.notification_number_input.setPlaceholderText("Исходящий номер")
        group4_layout.addWidget(self.notification_number_input, 3, 3)
        
        group4.setLayout(group4_layout)
        form_layout.addWidget(group4)
        
        container.setLayout(form_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        save_btn = button_box.button(QDialogButtonBox.StandardButton.Save)
        save_btn.setText("💾 Сохранить")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; min-width: 100px; padding: 8px;")
        
        cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_btn.setText("❌ Отмена")
        cancel_btn.setStyleSheet("min-width: 100px; padding: 8px;")
        
        layout.addWidget(button_box)
    
    def setup_autocomplete_fields(self):
        """
        🎯 НАСТРОЙКА АВТОДОПОЛНЕНИЯ ДЛЯ ВСЕХ ТЕКСТОВЫХ ПОЛЕЙ
        ✅ QLineEdit - стандартное автодополнение (QCompleter)
        ✅ QTextEdit - кастомное всплывающее окно
        ❌ QDateEdit - без автодополнения (календарь)
        """
        
        # === QLineEdit ПОЛЯ (7 полей) ===
        line_edit_fields = [
            (self.soch_location_input, 'soch_location', 20),
            (self.order_date_number_input, 'order_date_number', 15),
            (self.duty_officer_commissariat_input, 'duty_officer_commissariat', 15),
            (self.duty_officer_omvd_input, 'duty_officer_omvd', 15),
            (self.found_by_input, 'found_by', 20),
            (self.notification_recipient_input, 'notification_recipient', 20),
            (self.notification_number_input, 'notification_number', 15),
        ]
        
        # === QTextEdit ПОЛЯ (10 полей) ===
        text_edit_fields = [
            (self.witnesses_input, 'witnesses', 30),
            (self.reasons_input, 'reasons', 30),
            (self.weapon_info_input, 'weapon_info', 30),
            (self.clothing_input, 'clothing', 30),
            (self.movement_options_input, 'movement_options', 30),
            (self.other_info_input, 'other_info', 30),
            (self.investigation_info_input, 'investigation_info', 30),
            (self.prosecution_info_input, 'prosecution_info', 30),
            (self.criminal_case_info_input, 'criminal_case_info', 30),
            (self.search_circumstances_input, 'search_circumstances', 30),
        ]
        
        # Настраиваем QLineEdit
        for field_widget, column_name, max_items in line_edit_fields:
            self.autocomplete_helper.setup_autocomplete(
                field_widget, 
                'soch_episodes',
                column_name,
                max_items=max_items,
                show_on_focus=True  # ← Показывать все варианты при фокусе
            )
        
        # Настраиваем QTextEdit
        for field_widget, column_name, max_items in text_edit_fields:
            self.autocomplete_helper.setup_autocomplete(
                field_widget, 
                'soch_episodes',
                column_name,
                max_items=max_items,
                show_on_focus=True  # ← Показывать все варианты при фокусе
            )
        
        total_fields = len(line_edit_fields) + len(text_edit_fields)
        print(f"✅ Автодополнение настроено для {total_fields} полей ({len(line_edit_fields)} QLineEdit + {len(text_edit_fields)} QTextEdit)")
    
    def load_data(self):
        """Загрузка данных эпизода для редактирования"""
        if not self.episode_data:
            return
        
        self.soch_date_input.setDate(self.episode_data.get('soch_date') or QDate.currentDate())
        self.soch_location_input.setText(self.episode_data.get('soch_location') or '')
        self.order_date_number_input.setText(self.episode_data.get('order_date_number') or '')
        self.witnesses_input.setPlainText(self.episode_data.get('witnesses') or '')
        self.reasons_input.setPlainText(self.episode_data.get('reasons') or '')
        self.weapon_info_input.setPlainText(self.episode_data.get('weapon_info') or '')
        self.clothing_input.setPlainText(self.episode_data.get('clothing') or '')
        self.movement_options_input.setPlainText(self.episode_data.get('movement_options') or '')
        self.other_info_input.setPlainText(self.episode_data.get('other_info') or '')
        self.duty_officer_commissariat_input.setText(self.episode_data.get('duty_officer_commissariat') or '')
        self.duty_officer_omvd_input.setText(self.episode_data.get('duty_officer_omvd') or '')
        self.investigation_info_input.setPlainText(self.episode_data.get('investigation_info') or '')
        self.prosecution_info_input.setPlainText(self.episode_data.get('prosecution_info') or '')
        self.criminal_case_info_input.setPlainText(self.episode_data.get('criminal_case_info') or '')
        self.search_date_input.setDate(self.episode_data.get('search_date') or QDate.currentDate())
        self.found_by_input.setText(self.episode_data.get('found_by') or '')
        self.search_circumstances_input.setPlainText(self.episode_data.get('search_circumstances') or '')
        self.notification_recipient_input.setText(self.episode_data.get('notification_recipient') or '')
        self.notification_date_input.setDate(self.episode_data.get('notification_date') or QDate.currentDate())
        self.notification_number_input.setText(self.episode_data.get('notification_number') or '')
    
    def get_data(self):
        """Получение данных из формы"""
        return {
            "krd_id": self.krd_id,
            "soch_date": self.soch_date_input.date().toString("yyyy-MM-dd"),
            "soch_location": self.soch_location_input.text().strip(),
            "order_date_number": self.order_date_number_input.text().strip(),
            "witnesses": self.witnesses_input.toPlainText(),
            "reasons": self.reasons_input.toPlainText(),
            "weapon_info": self.weapon_info_input.toPlainText(),
            "clothing": self.clothing_input.toPlainText(),
            "movement_options": self.movement_options_input.toPlainText(),
            "other_info": self.other_info_input.toPlainText(),
            "duty_officer_commissariat": self.duty_officer_commissariat_input.text().strip(),
            "duty_officer_omvd": self.duty_officer_omvd_input.text().strip(),
            "investigation_info": self.investigation_info_input.toPlainText(),
            "prosecution_info": self.prosecution_info_input.toPlainText(),
            "criminal_case_info": self.criminal_case_info_input.toPlainText(),
            "search_date": self.search_date_input.date().toString("yyyy-MM-dd"),
            "found_by": self.found_by_input.text().strip(),
            "search_circumstances": self.search_circumstances_input.toPlainText(),
            "notification_recipient": self.notification_recipient_input.text().strip(),
            "notification_date": self.notification_date_input.date().toString("yyyy-MM-dd"),
            "notification_number": self.notification_number_input.text().strip()
        }
    
    def accept(self):
        """Сохранение данных при нажатии OK"""
        data = self.get_data()
        
        if not data["soch_date"]:
            QMessageBox.warning(self, "Ошибка", "Поле 'Дата СОЧ' обязательно для заполнения")
            return
        
        try:
            query = QSqlQuery(self.db)
            self.db.transaction()
            
            if self.is_edit:
                # Обновление существующей записи
                query.prepare("""
                    UPDATE krd.soch_episodes SET
                        soch_date = :soch_date,
                        soch_location = :soch_location,
                        order_date_number = :order_date_number,
                        witnesses = :witnesses,
                        reasons = :reasons,
                        weapon_info = :weapon_info,
                        clothing = :clothing,
                        movement_options = :movement_options,
                        other_info = :other_info,
                        duty_officer_commissariat = :duty_officer_commissariat,
                        duty_officer_omvd = :duty_officer_omvd,
                        investigation_info = :investigation_info,
                        prosecution_info = :prosecution_info,
                        criminal_case_info = :criminal_case_info,
                        search_date = :search_date,
                        found_by = :found_by,
                        search_circumstances = :search_circumstances,
                        notification_recipient = :notification_recipient,
                        notification_date = :notification_date,
                        notification_number = :notification_number
                    WHERE id = :id
                """)
                query.bindValue(":id", self.episode_id)
            else:
                # Добавление новой записи
                query.prepare("""
                    INSERT INTO krd.soch_episodes (
                        krd_id, soch_date, soch_location, order_date_number, witnesses,
                        reasons, weapon_info, clothing, movement_options, other_info,
                        duty_officer_commissariat, duty_officer_omvd, investigation_info,
                        prosecution_info, criminal_case_info, search_date, found_by,
                        search_circumstances, notification_recipient, notification_date,
                        notification_number
                    ) VALUES (
                        :krd_id, :soch_date, :soch_location, :order_date_number, :witnesses,
                        :reasons, :weapon_info, :clothing, :movement_options, :other_info,
                        :duty_officer_commissariat, :duty_officer_omvd, :investigation_info,
                        :prosecution_info, :criminal_case_info, :search_date, :found_by,
                        :search_circumstances, :notification_recipient, :notification_date,
                        :notification_number
                    )
                """)
            
            for key, value in data.items():
                query.bindValue(f":{key}", value)
            
            if not query.exec():
                raise Exception(f"Ошибка SQL: {query.lastError().text()}")
            
            self.db.commit()
            
            # === ОБНОВЛЕНИЕ КЭША АВТОДОПОЛНЕНИЯ ПОСЛЕ СОХРАНЕНИЯ ===
            self.autocomplete_helper.clear_cache()
            
            QMessageBox.information(self, "Успех", "Эпизод СОЧ успешно " + ("обновлён" if self.is_edit else "добавлен"))
            super().accept()
            
        except Exception as e:
            self.db.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{str(e)}")