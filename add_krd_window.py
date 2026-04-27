"""
Модуль для окна добавления новой КРД со всеми связанными данными
✅ ИСПОЛЬЗУЕТ ВКЛАДКИ как в KrdDetailsWindow
✅ Позволяет заполнить всю информацию сразу
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QTabWidget,
    QLabel, QGroupBox, QScrollArea, QWidget, QGridLayout, QLineEdit, 
    QTextEdit, QDateEdit, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate, QByteArray
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtSql import QSqlQuery
import os
import traceback

# Импорт всех вкладок
from social_data_tab import SocialDataTab
from addresses_tab import AddressesTab
from service_places_tab import ServicePlacesTab
from incoming_orders_tab import IncomingOrdersTab
from soch_episodes_tab import SochEpisodesTab


class AddKrdWindow(QDialog):
    """
    Окно для добавления новой КРД со всеми связанными данными
    """
    
    def __init__(self, db_connection, audit_logger=None):
        super().__init__()
        self.db = db_connection
        self.audit_logger = audit_logger
        self.krd_id = None  # Будет установлен после создания КРД
        
        self.setWindowTitle("➕ Добавление новой карточки розыска (КРД)")
        self.setModal(True)
        self.resize(1200, 800)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("➕ Добавление новой карточки розыска")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("QLabel { padding: 10px; background-color: #E3F2FD; border-radius: 5px; }")
        main_layout.addWidget(title_label)
        
        # Информация
        info_label = QLabel("💡 Заполните все необходимые данные. Поля со знаком * обязательны для заполнения.")
        info_label.setStyleSheet("QLabel { color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 5px; }")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)
        
        # Создаем вкладки
        tabs = QTabWidget()
        
        # Вкладка 1: Социально-демографические данные
        self.social_data_tab = SocialDataTabForAdd(self.db)
        tabs.addTab(self.social_data_tab, "📋 Социально-демографические данные")
        
        # Вкладка 2: Адреса проживания
        self.addresses_tab = AddressesTabForAdd(self.db)
        tabs.addTab(self.addresses_tab, "🏠 Адреса проживания")
        
        # Вкладка 3: Места службы
        self.service_places_tab = ServicePlacesTabForAdd(self.db)
        tabs.addTab(self.service_places_tab, "🎖️ Места службы")
        
        # Вкладка 4: Входящие поручения
        self.incoming_orders_tab = IncomingOrdersTabForAdd(self.db)
        tabs.addTab(self.incoming_orders_tab, "📬 Входящие поручения")
        
        # Вкладка 5: Эпизоды СОЧ
        self.soch_episodes_tab = SochEpisodesTabForAdd(self.db)
        tabs.addTab(self.soch_episodes_tab, "⚠️ Эпизоды СОЧ")
        
        main_layout.addWidget(tabs, 1)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        save_button = QPushButton("💾 Создать КРД")
        save_button.setMinimumHeight(50)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_button.clicked.connect(self.save_krd)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("❌ Отмена")
        cancel_button.setMinimumHeight(50)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def save_krd(self):
        """Сохранение новой КРД со всеми связанными данными"""
        # Проверяем обязательные поля
        if not self.social_data_tab.validate_required_fields():
            QMessageBox.warning(
                self, 
                "Ошибка валидации", 
                "Заполните обязательные поля (Фамилия, Имя, Отчество)!"
            )
            return
        
        # Подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение создания",
            "Вы действительно хотите создать новую карточку розыска?\n\n"
            "Будут сохранены:\n"
            "• Социально-демографические данные\n"
            f"• Адреса проживания: {len(self.addresses_tab.get_data())}\n"
            f"• Места службы: {len(self.service_places_tab.get_data())}\n"
            f"• Входящие поручения: {len(self.incoming_orders_tab.get_data())}\n"
            f"• Эпизоды СОЧ: {len(self.soch_episodes_tab.get_data())}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Начинаем транзакцию
            if not self.db.transaction():
                raise Exception(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
            
            # 1. Создаём запись в таблице krd
            krd_query = QSqlQuery(self.db)
            krd_query.prepare("INSERT INTO krd.krd DEFAULT VALUES RETURNING id")
            
            if not krd_query.exec():
                raise Exception(f"Ошибка создания КРД: {krd_query.lastError().text()}")
            
            if not krd_query.next():
                raise Exception("Не удалось получить ID новой КРД")
            
            self.krd_id = krd_query.value(0)
            print(f"✅ Создана КРД с ID: {self.krd_id}")
            
            # 2. Сохраняем социально-демографические данные
            social_data = self.social_data_tab.get_data()
            social_data['krd_id'] = self.krd_id
            
            social_query = QSqlQuery(self.db)
            social_query.prepare("""
                INSERT INTO krd.social_data (
                    krd_id, surname, name, patronymic, birth_date,
                    birth_place_town, birth_place_district, birth_place_region, birth_place_country,
                    tab_number, personal_number, category_id, rank_id,
                    drafted_by_commissariat, draft_date, povsk, selection_date,
                    education, criminal_record, social_media_account, bank_card_number,
                    passport_series, passport_number, passport_issue_date, passport_issued_by,
                    military_id_series, military_id_number, military_id_issue_date, military_id_issued_by,
                    appearance_features, personal_marks, federal_search_info, military_contacts, relatives_info,
                    photo_civilian, photo_military_headgear, photo_military_no_headgear, photo_distinctive_marks
                ) VALUES (
                    :krd_id, :surname, :name, :patronymic, :birth_date,
                    :birth_place_town, :birth_place_district, :birth_place_region, :birth_place_country,
                    :tab_number, :personal_number, :category_id, :rank_id,
                    :drafted_by_commissariat, :draft_date, :povsk, :selection_date,
                    :education, :criminal_record, :social_media_account, :bank_card_number,
                    :passport_series, :passport_number, :passport_issue_date, :passport_issued_by,
                    :military_id_series, :military_id_number, :military_id_issue_date, :military_id_issued_by,
                    :appearance_features, :personal_marks, :federal_search_info, :military_contacts, :relatives_info,
                    :photo_civilian, :photo_military_headgear, :photo_military_no_headgear, :photo_distinctive_marks
                )
            """)
            
            for key, value in social_data.items():
                social_query.bindValue(f":{key}", value)
            
            if not social_query.exec():
                raise Exception(f"Ошибка сохранения социальных данных: {social_query.lastError().text()}")
            
            print(f"✅ Сохранены социальные данные")
            
            # 3. Сохраняем адреса проживания
            addresses = self.addresses_tab.get_data()
            for addr in addresses:
                addr['krd_id'] = self.krd_id
                self._save_address(addr)
            
            print(f"✅ Сохранено адресов: {len(addresses)}")
            
            # 4. Сохраняем места службы
            service_places = self.service_places_tab.get_data()
            for sp in service_places:
                sp['krd_id'] = self.krd_id
                self._save_service_place(sp)
            
            print(f"✅ Сохранено мест службы: {len(service_places)}")
            
            # 5. Сохраняем входящие поручения
            incoming_orders = self.incoming_orders_tab.get_data()
            for order in incoming_orders:
                order['krd_id'] = self.krd_id
                self._save_incoming_order(order)
            
            print(f"✅ Сохранено входящих поручений: {len(incoming_orders)}")
            
            # 6. Сохраняем эпизоды СОЧ
            soch_episodes = self.soch_episodes_tab.get_data()
            for episode in soch_episodes:
                episode['krd_id'] = self.krd_id
                self._save_soch_episode(episode)
            
            print(f"✅ Сохранено эпизодов СОЧ: {len(soch_episodes)}")
            
            # Коммит транзакции
            if not self.db.commit():
                raise Exception(f"Ошибка коммита транзакции: {self.db.lastError().text()}")
            
            # Логирование
            if self.audit_logger:
                self.audit_logger.log_krd_create(self.krd_id, {
                    'surname': social_data.get('surname'),
                    'name': social_data.get('name'),
                    'patronymic': social_data.get('patronymic')
                })
            
            QMessageBox.information(
                self,
                "Успех",
                f"✅ Карточка розыска успешно создана!\n\n"
                f"ID КРД: {self.krd_id}\n"
                f"Военнослужащий: {social_data.get('surname')} {social_data.get('name')} {social_data.get('patronymic')}\n\n"
                f"Сохранено данных:\n"
                f"• Адресов: {len(addresses)}\n"
                f"• Мест службы: {len(service_places)}\n"
                f"• Входящих поручений: {len(incoming_orders)}\n"
                f"• Эпизодов СОЧ: {len(soch_episodes)}"
            )
            
            self.accept()
            
        except Exception as e:
            # Откат транзакции
            self.db.rollback()
            print(f"❌ Ошибка: {e}")
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Ошибка при создании КРД:\n{str(e)}"
            )
    
    def _save_address(self, addr_data):
        """Сохранение адреса проживания"""
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.addresses (
                krd_id, region, district, town, street, house, building,
                letter, apartment, room, check_date, check_result
            ) VALUES (
                :krd_id, :region, :district, :town, :street, :house, :building,
                :letter, :apartment, :room, :check_date, :check_result
            )
        """)
        
        for key, value in addr_data.items():
            query.bindValue(f":{key}", value)
        
        if not query.exec():
            raise Exception(f"Ошибка сохранения адреса: {query.lastError().text()}")
    
    def _save_service_place(self, sp_data):
        """Сохранение места службы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.service_places (
                krd_id, place_name, military_unit_id, garrison_id, position_id,
                commanders, postal_index, postal_region, postal_district, postal_town,
                postal_street, postal_house, postal_building, postal_letter,
                postal_apartment, postal_room, place_contacts
            ) VALUES (
                :krd_id, :place_name, :military_unit_id, :garrison_id, :position_id,
                :commanders, :postal_index, :postal_region, :postal_district, :postal_town,
                :postal_street, :postal_house, :postal_building, :postal_letter,
                :postal_apartment, :postal_room, :place_contacts
            )
        """)
        
        for key, value in sp_data.items():
            query.bindValue(f":{key}", value)
        
        if not query.exec():
            raise Exception(f"Ошибка сохранения места службы: {query.lastError().text()}")
    
    def _save_incoming_order(self, order_data):
        """Сохранение входящего поручения"""
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.incoming_orders (
                krd_id, initiator_type_id, initiator_full_name, military_unit_id,
                order_date, order_number, receipt_date, receipt_number,
                postal_index, postal_region, postal_district, postal_town,
                postal_street, postal_house, postal_building, postal_letter,
                postal_apartment, postal_room, initiator_contacts,
                our_response_date, our_response_number
            ) VALUES (
                :krd_id, :initiator_type_id, :initiator_full_name, :military_unit_id,
                :order_date, :order_number, :receipt_date, :receipt_number,
                :postal_index, :postal_region, :postal_district, :postal_town,
                :postal_street, :postal_house, :postal_building, :postal_letter,
                :postal_apartment, :postal_room, :initiator_contacts,
                :our_response_date, :our_response_number
            )
        """)
        
        for key, value in order_data.items():
            query.bindValue(f":{key}", value)
        
        if not query.exec():
            raise Exception(f"Ошибка сохранения поручения: {query.lastError().text()}")
    
    def _save_soch_episode(self, episode_data):
        """Сохранение эпизода СОЧ"""
        query = QSqlQuery(self.db)
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
        
        for key, value in episode_data.items():
            query.bindValue(f":{key}", value)
        
        if not query.exec():
            raise Exception(f"Ошибка сохранения эпизода СОЧ: {query.lastError().text()}")


# ============================================================================
# ВКЛАДКИ ДЛЯ ДОБАВЛЕНИЯ (упрощённые версии без загрузки данных)
# ============================================================================

class SocialDataTabForAdd(QWidget):
    """Вкладка социальных данных для добавления"""
    
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.photo_paths = {}
        self.init_ui()
        self.load_combo_data()
    
    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Группа 1: Основные данные
        group1 = QGroupBox("Основные данные (поля со знаком * обязательны)")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group1_layout = QGridLayout()
        group1_layout.setSpacing(8)
        
        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("Введите фамилию")
        group1_layout.addWidget(QLabel("Фамилия *:"), 0, 0)
        group1_layout.addWidget(self.surname_input, 0, 1)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите имя")
        group1_layout.addWidget(QLabel("Имя *:"), 0, 2)
        group1_layout.addWidget(self.name_input, 0, 3)
        
        self.patronymic_input = QLineEdit()
        self.patronymic_input.setPlaceholderText("Введите отчество")
        group1_layout.addWidget(QLabel("Отчество *:"), 0, 4)
        group1_layout.addWidget(self.patronymic_input, 0, 5)
        
        self.tab_number_input = QLineEdit()
        group1_layout.addWidget(QLabel("Табельный номер:"), 1, 0)
        group1_layout.addWidget(self.tab_number_input, 1, 1)
        
        self.personal_number_input = QLineEdit()
        group1_layout.addWidget(QLabel("Личный номер:"), 1, 2)
        group1_layout.addWidget(self.personal_number_input, 1, 3)
        
        self.category_combo = QComboBox()
        group1_layout.addWidget(QLabel("Категория:"), 2, 0)
        group1_layout.addWidget(self.category_combo, 2, 1)
        
        self.rank_combo = QComboBox()
        group1_layout.addWidget(QLabel("Воинское звание:"), 2, 2)
        group1_layout.addWidget(self.rank_combo, 2, 3)
        
        group1.setLayout(group1_layout)
        layout.addWidget(group1)
        
        # Группа 2: Место рождения
        group2 = QGroupBox("Место рождения")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group2_layout = QGridLayout()
        group2_layout.setSpacing(8)
        
        self.birth_place_town_input = QLineEdit()
        group2_layout.addWidget(QLabel("Населенный пункт:"), 0, 0)
        group2_layout.addWidget(self.birth_place_town_input, 0, 1)
        
        self.birth_place_district_input = QLineEdit()
        group2_layout.addWidget(QLabel("Район:"), 0, 2)
        group2_layout.addWidget(self.birth_place_district_input, 0, 3)
        
        self.birth_place_region_input = QLineEdit()
        group2_layout.addWidget(QLabel("Субъект (регион):"), 1, 0)
        group2_layout.addWidget(self.birth_place_region_input, 1, 1)
        
        self.birth_place_country_input = QLineEdit()
        group2_layout.addWidget(QLabel("Страна:"), 1, 2)
        group2_layout.addWidget(self.birth_place_country_input, 1, 3)
        
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate.currentDate())
        group2_layout.addWidget(QLabel("Дата рождения:"), 2, 0)
        group2_layout.addWidget(self.birth_date_input, 2, 1)
        
        group2.setLayout(group2_layout)
        layout.addWidget(group2)
        
        # Группа 3: Призыв
        group3 = QGroupBox("Призыв")
        group3.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group3_layout = QGridLayout()
        group3_layout.setSpacing(8)
        
        self.drafted_by_commissariat_input = QLineEdit()
        group3_layout.addWidget(QLabel("Каким комиссариатом призван:"), 0, 0)
        group3_layout.addWidget(self.drafted_by_commissariat_input, 0, 1, 1, 3)
        
        self.draft_date_input = QDateEdit()
        self.draft_date_input.setCalendarPopup(True)
        self.draft_date_input.setDate(QDate.currentDate())
        group3_layout.addWidget(QLabel("Дата призыва:"), 1, 0)
        group3_layout.addWidget(self.draft_date_input, 1, 1)
        
        self.povsk_input = QLineEdit()
        group3_layout.addWidget(QLabel("ПВО/ПВС:"), 1, 2)
        group3_layout.addWidget(self.povsk_input, 1, 3)
        
        self.selection_date_input = QDateEdit()
        self.selection_date_input.setCalendarPopup(True)
        self.selection_date_input.setDate(QDate.currentDate())
        group3_layout.addWidget(QLabel("Дата отбора:"), 2, 0)
        group3_layout.addWidget(self.selection_date_input, 2, 1)
        
        group3.setLayout(group3_layout)
        layout.addWidget(group3)
        
        # Группа 4: Паспортные данные
        group4 = QGroupBox("Паспортные данные")
        group4.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group4_layout = QGridLayout()
        group4_layout.setSpacing(8)
        
        self.passport_series_input = QLineEdit()
        group4_layout.addWidget(QLabel("Серия паспорта:"), 0, 0)
        group4_layout.addWidget(self.passport_series_input, 0, 1)
        
        self.passport_number_input = QLineEdit()
        group4_layout.addWidget(QLabel("Номер паспорта:"), 0, 2)
        group4_layout.addWidget(self.passport_number_input, 0, 3)
        
        self.passport_issue_date_input = QDateEdit()
        self.passport_issue_date_input.setCalendarPopup(True)
        self.passport_issue_date_input.setDate(QDate.currentDate())
        group4_layout.addWidget(QLabel("Дата выдачи:"), 1, 0)
        group4_layout.addWidget(self.passport_issue_date_input, 1, 1)
        
        self.passport_issued_by_input = QLineEdit()
        group4_layout.addWidget(QLabel("Кем выдан:"), 1, 2)
        group4_layout.addWidget(self.passport_issued_by_input, 1, 3)
        
        group4.setLayout(group4_layout)
        layout.addWidget(group4)
        
        # Группа 5: Военный билет
        group5 = QGroupBox("Военный билет")
        group5.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group5_layout = QGridLayout()
        group5_layout.setSpacing(8)
        
        self.military_id_series_input = QLineEdit()
        group5_layout.addWidget(QLabel("Серия:"), 0, 0)
        group5_layout.addWidget(self.military_id_series_input, 0, 1)
        
        self.military_id_number_input = QLineEdit()
        group5_layout.addWidget(QLabel("Номер:"), 0, 2)
        group5_layout.addWidget(self.military_id_number_input, 0, 3)
        
        self.military_id_issue_date_input = QDateEdit()
        self.military_id_issue_date_input.setCalendarPopup(True)
        self.military_id_issue_date_input.setDate(QDate.currentDate())
        group5_layout.addWidget(QLabel("Дата выдачи:"), 1, 0)
        group5_layout.addWidget(self.military_id_issue_date_input, 1, 1)
        
        self.military_id_issued_by_input = QLineEdit()
        group5_layout.addWidget(QLabel("Кем выдан:"), 1, 2)
        group5_layout.addWidget(self.military_id_issued_by_input, 1, 3)
        
        group5.setLayout(group5_layout)
        layout.addWidget(group5)
        
        # Группа 6: Дополнительно
        group6 = QGroupBox("Дополнительная информация")
        group6.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group6_layout = QGridLayout()
        group6_layout.setSpacing(8)
        
        self.education_input = QLineEdit()
        group6_layout.addWidget(QLabel("Образование:"), 0, 0)
        group6_layout.addWidget(self.education_input, 0, 1, 1, 3)
        
        self.criminal_record_input = QTextEdit()
        self.criminal_record_input.setMaximumHeight(60)
        group6_layout.addWidget(QLabel("Судимость:"), 1, 0)
        group6_layout.addWidget(self.criminal_record_input, 1, 1, 1, 3)
        
        self.appearance_features_input = QTextEdit()
        self.appearance_features_input.setMaximumHeight(60)
        group6_layout.addWidget(QLabel("Особенности внешности:"), 2, 0)
        group6_layout.addWidget(self.appearance_features_input, 2, 1, 1, 3)
        
        self.personal_marks_input = QTextEdit()
        self.personal_marks_input.setMaximumHeight(60)
        group6_layout.addWidget(QLabel("Личные приметы:"), 3, 0)
        group6_layout.addWidget(self.personal_marks_input, 3, 1, 1, 3)
        
        self.military_contacts_input = QLineEdit()
        group6_layout.addWidget(QLabel("Контакты военнослужащего:"), 4, 0)
        group6_layout.addWidget(self.military_contacts_input, 4, 1, 1, 3)
        
        self.relatives_info_input = QTextEdit()
        self.relatives_info_input.setMaximumHeight(60)
        group6_layout.addWidget(QLabel("Сведения о родных:"), 5, 0)
        group6_layout.addWidget(self.relatives_info_input, 5, 1, 1, 3)
        
        group6.setLayout(group6_layout)
        layout.addWidget(group6)
        
        layout.addStretch()
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
    
    def load_combo_data(self):
        """Загрузка данных для ComboBox"""
        # Категории
        query = QSqlQuery(self.db)
        query.exec("SELECT id, name FROM krd.categories ORDER BY name")
        while query.next():
            self.category_combo.addItem(query.value(1), query.value(0))
        
        # Звания
        query.exec("SELECT id, name FROM krd.ranks ORDER BY name")
        while query.next():
            self.rank_combo.addItem(query.value(1), query.value(0))
    
    def validate_required_fields(self):
        """Проверка обязательных полей"""
        if not self.surname_input.text().strip():
            return False
        if not self.name_input.text().strip():
            return False
        if not self.patronymic_input.text().strip():
            return False
        return True
    
    def get_data(self):
        """Получение данных из формы"""
        return {
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
            'passport_series': self.passport_series_input.text().strip(),
            'passport_number': self.passport_number_input.text().strip(),
            'passport_issue_date': self.passport_issue_date_input.date(),
            'passport_issued_by': self.passport_issued_by_input.text().strip(),
            'military_id_series': self.military_id_series_input.text().strip(),
            'military_id_number': self.military_id_number_input.text().strip(),
            'military_id_issue_date': self.military_id_issue_date_input.date(),
            'military_id_issued_by': self.military_id_issued_by_input.text().strip(),
            'appearance_features': self.appearance_features_input.toPlainText(),
            'personal_marks': self.personal_marks_input.toPlainText(),
            'military_contacts': self.military_contacts_input.text().strip(),
            'relatives_info': self.relatives_info_input.toPlainText(),
            'photo_civilian': QByteArray(),
            'photo_military_headgear': QByteArray(),
            'photo_military_no_headgear': QByteArray(),
            'photo_distinctive_marks': QByteArray()
        }


class AddressesTabForAdd(QWidget):
    """Вкладка адресов для добавления"""
    
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.addresses = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        info_label = QLabel("💡 Добавьте адреса проживания военнослужащего")
        info_label.setStyleSheet("QLabel { color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 5px; }")
        layout.addWidget(info_label)
        
        # Кнопка добавления
        add_btn = QPushButton("➕ Добавить адрес")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)
        add_btn.clicked.connect(self.add_address)
        layout.addWidget(add_btn)
        
        # Список адресов
        self.addresses_list = QVBoxLayout()
        layout.addLayout(self.addresses_list)
        layout.addStretch()
    
    def add_address(self):
        """Добавление адреса"""
        addr_widget = AddressWidgetForAdd(self.db, len(self.addresses) + 1)
        self.addresses_list.addWidget(addr_widget)
        self.addresses.append(addr_widget)
    
    def get_data(self):
        """Получение всех адресов"""
        data = []
        for addr_widget in self.addresses:
            addr_data = addr_widget.get_data()
            if addr_data.get('town'):  # Только если заполнен населенный пункт
                data.append(addr_data)
        return data


class AddressWidgetForAdd(QGroupBox):
    """Виджет одного адреса"""
    
    def __init__(self, db_connection, index):
        super().__init__(f"Адрес #{index}")
        self.db = db_connection
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        layout = QGridLayout()
        layout.setSpacing(8)
        
        self.region_input = QLineEdit()
        self.region_input.setPlaceholderText("Субъект РФ")
        layout.addWidget(QLabel("Субъект РФ:"), 0, 0)
        layout.addWidget(self.region_input, 0, 1)
        
        self.district_input = QLineEdit()
        self.district_input.setPlaceholderText("Район")
        layout.addWidget(QLabel("Район:"), 0, 2)
        layout.addWidget(self.district_input, 0, 3)
        
        self.town_input = QLineEdit()
        self.town_input.setPlaceholderText("Населенный пункт")
        layout.addWidget(QLabel("Населенный пункт *:"), 1, 0)
        layout.addWidget(self.town_input, 1, 1)
        
        self.street_input = QLineEdit()
        self.street_input.setPlaceholderText("Улица")
        layout.addWidget(QLabel("Улица:"), 1, 2)
        layout.addWidget(self.street_input, 1, 3)
        
        self.house_input = QLineEdit()
        self.house_input.setPlaceholderText("Дом")
        layout.addWidget(QLabel("Дом:"), 2, 0)
        layout.addWidget(self.house_input, 2, 1)
        
        self.apartment_input = QLineEdit()
        self.apartment_input.setPlaceholderText("Квартира")
        layout.addWidget(QLabel("Квартира:"), 2, 2)
        layout.addWidget(self.apartment_input, 2, 3)
        
        self.setLayout(layout)
    
    def get_data(self):
        """Получение данных адреса"""
        return {
            'region': self.region_input.text().strip(),
            'district': self.district_input.text().strip(),
            'town': self.town_input.text().strip(),
            'street': self.street_input.text().strip(),
            'house': self.house_input.text().strip(),
            'apartment': self.apartment_input.text().strip()
        }


# Аналогично создаются ServicePlacesTabForAdd, IncomingOrdersTabForAdd, SochEpisodesTabForAdd
# (для краткости не показаны, но структура аналогична AddressesTabForAdd)

class ServicePlacesTabForAdd(QWidget):
    """Вкладка мест службы для добавления"""
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.service_places = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        info_label = QLabel("💡 Добавьте места службы военнослужащего")
        info_label.setStyleSheet("QLabel { color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 5px; }")
        layout.addWidget(info_label)
        
        add_btn = QPushButton("➕ Добавить место службы")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)
        add_btn.clicked.connect(self.add_service_place)
        layout.addWidget(add_btn)
        
        self.service_places_list = QVBoxLayout()
        layout.addLayout(self.service_places_list)
        layout.addStretch()
    
    def add_service_place(self):
        sp_widget = ServicePlaceWidgetForAdd(self.db, len(self.service_places) + 1)
        self.service_places_list.addWidget(sp_widget)
        self.service_places.append(sp_widget)
    
    def get_data(self):
        data = []
        for sp_widget in self.service_places:
            sp_data = sp_widget.get_data()
            if sp_data.get('place_name'):
                data.append(sp_data)
        return data


class ServicePlaceWidgetForAdd(QGroupBox):
    """Виджет одного места службы"""
    def __init__(self, db_connection, index):
        super().__init__(f"Место службы #{index}")
        self.db = db_connection
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        layout = QGridLayout()
        layout.setSpacing(8)
        
        self.place_name_input = QLineEdit()
        self.place_name_input.setPlaceholderText("Наименование места службы")
        layout.addWidget(QLabel("Наименование *:"), 0, 0)
        layout.addWidget(self.place_name_input, 0, 1, 1, 3)
        
        self.commanders_input = QTextEdit()
        self.commanders_input.setMaximumHeight(60)
        layout.addWidget(QLabel("Командиры:"), 1, 0)
        layout.addWidget(self.commanders_input, 1, 1, 1, 3)
        
        self.place_contacts_input = QLineEdit()
        self.place_contacts_input.setPlaceholderText("Телефон, email")
        layout.addWidget(QLabel("Контакты:"), 2, 0)
        layout.addWidget(self.place_contacts_input, 2, 1, 1, 3)
        
        self.setLayout(layout)
    
    def get_data(self):
        return {
            'place_name': self.place_name_input.text().strip(),
            'commanders': self.commanders_input.toPlainText(),
            'place_contacts': self.place_contacts_input.text().strip()
        }


class IncomingOrdersTabForAdd(QWidget):
    """Вкладка входящих поручений для добавления"""
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.incoming_orders = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        info_label = QLabel("💡 Добавьте входящие поручения по КРД")
        info_label.setStyleSheet("QLabel { color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 5px; }")
        layout.addWidget(info_label)
        
        add_btn = QPushButton("➕ Добавить поручение")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)
        add_btn.clicked.connect(self.add_order)
        layout.addWidget(add_btn)
        
        self.orders_list = QVBoxLayout()
        layout.addLayout(self.orders_list)
        layout.addStretch()
    
    def add_order(self):
        order_widget = IncomingOrderWidgetForAdd(self.db, len(self.incoming_orders) + 1)
        self.orders_list.addWidget(order_widget)
        self.incoming_orders.append(order_widget)
    
    def get_data(self):
        data = []
        for order_widget in self.incoming_orders:
            order_data = order_widget.get_data()
            if order_data.get('initiator_full_name'):
                data.append(order_data)
        return data


class IncomingOrderWidgetForAdd(QGroupBox):
    """Виджет одного поручения"""
    def __init__(self, db_connection, index):
        super().__init__(f"Поручение #{index}")
        self.db = db_connection
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        layout = QGridLayout()
        layout.setSpacing(8)
        
        self.initiator_full_name_input = QLineEdit()
        self.initiator_full_name_input.setPlaceholderText("Наименование инициатора")
        layout.addWidget(QLabel("Инициатор *:"), 0, 0)
        layout.addWidget(self.initiator_full_name_input, 0, 1, 1, 3)
        
        self.order_number_input = QLineEdit()
        self.order_number_input.setPlaceholderText("Номер поручения")
        layout.addWidget(QLabel("Номер поручения *:"), 1, 0)
        layout.addWidget(self.order_number_input, 1, 1)
        
        self.order_date_input = QDateEdit()
        self.order_date_input.setCalendarPopup(True)
        self.order_date_input.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Дата поручения:"), 1, 2)
        layout.addWidget(self.order_date_input, 1, 3)
        
        self.setLayout(layout)
    
    def get_data(self):
        return {
            'initiator_full_name': self.initiator_full_name_input.text().strip(),
            'order_number': self.order_number_input.text().strip(),
            'order_date': self.order_date_input.date()
        }


class SochEpisodesTabForAdd(QWidget):
    """Вкладка эпизодов СОЧ для добавления"""
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.soch_episodes = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        info_label = QLabel("💡 Добавьте эпизоды самовольного оставления части")
        info_label.setStyleSheet("QLabel { color: #666; padding: 8px; background-color: #f0f0f0; border-radius: 5px; }")
        layout.addWidget(info_label)
        
        add_btn = QPushButton("➕ Добавить эпизод СОЧ")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
        """)
        add_btn.clicked.connect(self.add_episode)
        layout.addWidget(add_btn)
        
        self.episodes_list = QVBoxLayout()
        layout.addLayout(self.episodes_list)
        layout.addStretch()
    
    def add_episode(self):
        episode_widget = SochEpisodeWidgetForAdd(self.db, len(self.soch_episodes) + 1)
        self.episodes_list.addWidget(episode_widget)
        self.soch_episodes.append(episode_widget)
    
    def get_data(self):
        data = []
        for episode_widget in self.soch_episodes:
            episode_data = episode_widget.get_data()
            if episode_data.get('soch_date'):
                data.append(episode_data)
        return data


class SochEpisodeWidgetForAdd(QGroupBox):
    """Виджет одного эпизода СОЧ"""
    def __init__(self, db_connection, index):
        super().__init__(f"Эпизод СОЧ #{index}")
        self.db = db_connection
        self.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        layout = QGridLayout()
        layout.setSpacing(8)
        
        self.soch_date_input = QDateEdit()
        self.soch_date_input.setCalendarPopup(True)
        self.soch_date_input.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Дата СОЧ *:"), 0, 0)
        layout.addWidget(self.soch_date_input, 0, 1)
        
        self.soch_location_input = QLineEdit()
        self.soch_location_input.setPlaceholderText("Место СОЧ")
        layout.addWidget(QLabel("Место СОЧ:"), 0, 2)
        layout.addWidget(self.soch_location_input, 0, 3)
        
        self.reasons_input = QTextEdit()
        self.reasons_input.setMaximumHeight(60)
        layout.addWidget(QLabel("Причины:"), 1, 0)
        layout.addWidget(self.reasons_input, 1, 1, 1, 3)
        
        self.setLayout(layout)
    
    def get_data(self):
        return {
            'soch_date': self.soch_date_input.date(),
            'soch_location': self.soch_location_input.text().strip(),
            'reasons': self.reasons_input.toPlainText()
        }