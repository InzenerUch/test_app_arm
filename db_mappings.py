# db_mappings.py
"""
Единый справочник маппингов БД
⚠️ СТРОГО СООТВЕТСТВУЕТ schema_only.sql
✅ ИСПРАВЛЕНО: Все ключи уникальны (формат: table_column)
✅ ДОБАВЛЕНО: Безопасный резолвер описаний для UI
"""

# 📋 Русские названия таблиц
TABLE_NAMES_RU = {
    'signatories': 'Подписанты документов',
    'social_data': 'Социально-демографические данные',
    'addresses': 'Адреса проживания',
    'service_places': 'Места службы',
    'soch_episodes': 'Эпизоды СОЧ',
    'incoming_orders': 'Входящие поручения',
    'outgoing_requests': 'Исходящие запросы',
    'recipients': 'Адресаты',
    'categories': 'Категории военнослужащих',
    'ranks': 'Воинские звания',
    'statuses': 'Статусы КРД',
    'request_types': 'Типы запросов',
    'initiator_types': 'Типы инициаторов',
    'military_units': 'Военные управления',
    'garrisons': 'Гарнизоны',
    'positions': 'Воинские должности',
    'krd': 'Карточки розыска (КРД)'
}

# 📝 Описания полей (уникальные ключи: table_column)
COLUMN_DESCRIPTIONS = {
    # === SOCIAL_DATA ===
    "social_data_surname": "👤 Фамилия военнослужащего",
    "social_data_name": "👤 Имя военнослужащего",
    "social_data_patronymic": "👤 Отчество военнослужащего",
    "social_data_birth_date": "📅 Дата рождения",
    "social_data_birth_place_town": "🌍 Населенный пункт места рождения",
    "social_data_birth_place_district": "🌍 Район места рождения",
    "social_data_birth_place_region": "🌍 Субъект РФ места рождения",
    "social_data_birth_place_country": "🌍 Страна места рождения",
    "social_data_tab_number": "🔢 Табельный номер",
    "social_data_personal_number": "🔢 Личный номер",
    "social_data_category_id": "📋 ID категории (справочник)",
    "social_data_rank_id": "⭐ ID воинского звания (справочник)",
    "social_data_drafted_by_commissariat": "🎖️ Наименование военкомата призыва",
    "social_data_draft_date": "📅 Дата призыва на военную службу",
    "social_data_povsk": "🎖️ Наименование ПОВСК",
    "social_data_selection_date": "📅 Дата отбора на военную службу",
    "social_data_education": "🎓 Образование военнослужащего",
    "social_data_criminal_record": "⚖️ Сведения о судимости",
    "social_data_social_media_account": "📱 Аккаунты в социальных сетях",
    "social_data_bank_card_number": "💳 Номер банковской карты",
    "social_data_passport_series": "📄 Серия паспорта",
    "social_data_passport_number": "📄 Номер паспорта",
    "social_data_passport_issue_date": "📅 Дата выдачи паспорта",
    "social_data_passport_issued_by": "📄 Кем выдан паспорт",
    "social_data_military_id_series": "🎫 Серия военного билета",
    "social_data_military_id_number": "🎫 Номер военного билета",
    "social_data_military_id_issue_date": "📅 Дата выдачи военного билета",
    "social_data_military_id_issued_by": "🎫 Кем выдан военный билет",
    "social_data_appearance_features": "👁️ Особенности внешности",
    "social_data_personal_marks": "👁️ Личные приметы (татуировки, шрамы)",
    "social_data_federal_search_info": "🔍 Сведения о федеральном розыске",
    "social_data_military_contacts": "📞 Контакты военнослужащего",
    "social_data_relatives_info": "👨‍👩‍👧 Сведения о близких родственниках",

    # === ADDRESSES ===
    "addresses_region": "📍 Субъект РФ (область, край, республика)",
    "addresses_district": "📍 Административный район",
    "addresses_town": "📍 Населенный пункт (город, село)",
    "addresses_street": "📍 Улица",
    "addresses_house": "🏠 Номер дома",
    "addresses_building": "🏢 Номер корпуса",
    "addresses_letter": "🔤 Литера здания",
    "addresses_apartment": "🚪 Номер квартиры",
    "addresses_room": "🚪 Номер комнаты",
    "addresses_check_date": "📅 Дата адресной проверки",
    "addresses_check_result": "✅ Результат проверки адреса",
    "addresses_postal_index": "📮 Почтовый индекс (проживание)",

    # === SERVICE_PLACES ===
    "service_places_place_name": "🎖️ Наименование места службы",
    "service_places_military_unit_number": "🔢 Номер воинской части (в/ч)",
    "service_places_military_unit_id": "🎖️ ID военного управления (место службы)",
    "service_places_garrison_id": "🏢 ID гарнизона (справочник)",
    "service_places_position_id": "💼 ID воинской должности (справочник)",
    "service_places_commanders": "👨‍✈️ Командиры (ФИО, контакты)",
    "service_places_postal_index": "📮 Почтовый индекс (почтовый адрес части)",
    "service_places_postal_region": "📮 Субъект РФ почтового адреса",
    "service_places_postal_district": "📮 Район почтового адреса",
    "service_places_postal_town": "📮 Город почтового адреса",
    "service_places_postal_street": "📮 Улица почтового адреса",
    "service_places_postal_house": "📮 Дом почтового адреса",
    "service_places_postal_building": "📮 Корпус почтового адреса",
    "service_places_postal_letter": "📮 Литера почтового адреса",
    "service_places_postal_apartment": "📮 Квартира почтового адреса",
    "service_places_postal_room": "📮 Комната почтового адреса",
    "service_places_place_contacts": "📞 Контакты места службы",

    # === SOCH_EPISODES ===
    "soch_episodes_soch_date": "⚠️ Дата СОЧ",
    "soch_episodes_soch_location": "⚠️ Место СОЧ",
    "soch_episodes_order_date_number": "⚠️ Дата и номер приказа о СОЧ",
    "soch_episodes_witnesses": "👥 Очевидцы СОЧ",
    "soch_episodes_reasons": "💡 Вероятные причины СОЧ",
    "soch_episodes_weapon_info": "🔫 Сведения о наличии оружия",
    "soch_episodes_clothing": "🧥 Описание одежды",
    "soch_episodes_movement_options": "🚶 Возможные направления движения",
    "soch_episodes_other_info": "📝 Другая значимая информация",
    "soch_episodes_duty_officer_commissariat": "📞 Дежурный по военкомату",
    "soch_episodes_duty_officer_omvd": "📞 Дежурный по ОМВД",
    "soch_episodes_investigation_info": "📋 Сведения о проверке",
    "soch_episodes_prosecution_info": "📋 Сведения о прокуратуре",
    "soch_episodes_criminal_case_info": "📋 Сведения об уголовном деле",
    "soch_episodes_search_date": "🔍 Дата розыска",
    "soch_episodes_found_by": "✅ Кем разыскан",
    "soch_episodes_search_circumstances": "🔍 Обстоятельства розыска",
    "soch_episodes_notification_recipient": "📬 Адресат уведомления",
    "soch_episodes_notification_date": "📅 Дата уведомления",
    "soch_episodes_notification_number": "📬 Номер уведомления",

    # === INCOMING_ORDERS ===
    "incoming_orders_initiator_type_id": "📩 ID типа инициатора (справочник)",
    "incoming_orders_initiator_full_name": "📩 Наименование инициатора",
    "incoming_orders_military_unit_id": "🎖️ ID военного управления (инициатор)",
    "incoming_orders_order_date": "📩 Дата поручения",
    "incoming_orders_order_number": "📩 Номер поручения",
    "incoming_orders_receipt_date": "📩 Дата поступления",
    "incoming_orders_receipt_number": "📩 Входящий номер",
    "incoming_orders_postal_index": "📮 Почтовый индекс (адрес инициатора)",
    "incoming_orders_postal_region": "📮 Субъект РФ (адрес инициатора)",
    "incoming_orders_postal_district": "📮 Район (адрес инициатора)",
    "incoming_orders_postal_town": "📮 Город (адрес инициатора)",
    "incoming_orders_postal_street": "📮 Улица (адрес инициатора)",
    "incoming_orders_postal_house": "📮 Дом (адрес инициатора)",
    "incoming_orders_postal_building": "📮 Корпус (адрес инициатора)",
    "incoming_orders_postal_letter": "📮 Литера (адрес инициатора)",
    "incoming_orders_postal_apartment": "📮 Квартира (адрес инициатора)",
    "incoming_orders_postal_room": "📮 Комната (адрес инициатора)",
    "incoming_orders_initiator_contacts": "📩 Контакты инициатора",
    "incoming_orders_our_response_date": "📩 Дата ответа",
    "incoming_orders_our_response_number": "📩 Исходящий номер ответа",

    # === OUTGOING_REQUESTS ===
    "outgoing_requests_request_type_id": "📤 ID типа запроса (справочник)",
    "outgoing_requests_military_unit_id": "🎖️ ID военного управления адресата (справочник)",
    "outgoing_requests_issue_date": "📤 Дата запроса",
    "outgoing_requests_issue_number": "📤 Номер запроса",
    "outgoing_requests_request_text": "📤 Текст запроса",
    "outgoing_requests_signed_by_position": "📤 Должность подписанта",
    "outgoing_requests_recipient_id": "👥 ID адресата (справочник)",
    "outgoing_requests_response_date": "📅 Дата получения ответа",
    "outgoing_requests_response_number": "📬 Номер ответа",
    "outgoing_requests_response_status": "📊 Статус ответа",

    # === RECIPIENTS ===
    "recipients_name": "👥 Наименование адресата",
    "recipients_contacts": "👥 Контакты адресата (телефон, email)",
    "recipients_postal_index": "👥 Почтовый индекс адресата",
    "recipients_postal_region": "👥 Субъект РФ адресата",
    "recipients_postal_district": "👥 Административный район адресата",
    "recipients_postal_town": "👥 Город/населенный пункт адресата",
    "recipients_postal_street": "👥 Улица адресата",
    "recipients_postal_house": "👥 Дом адресата",
    "recipients_postal_building": "👥 Корпус/строение адресата",
    "recipients_postal_letter": "👥 Литера адресата",
    "recipients_postal_apartment": "👥 Квартира адресата",
    "recipients_postal_room": "👥 Комната адресата",
    "recipients_request_type_id": "📤 ID типа запроса по умолчанию (справочник)",

    # === KRD (доп. поля) ===
    "krd_status_id": "📊 ID статуса КРД (справочник)",
    "krd_last_service_place_id": "🎖️ ID последнего места службы",
    "krd_is_locked": "🔒 Заблокировано для редактирования",
    "krd_locked_by": "👤 ID пользователя, заблокировавшего КРД",
    "krd_locked_at": "📅 Дата и время блокировки",
    # === Справочник подписантов ===
    "signatories_full_name": "👤 ФИО подписанта (например: И. Кувандыков)",
    "signatories_position": "💼 Должность подписанта",
    "signatories_rank": "⭐ Звание подписанта",
    "signatories_garrison": "🏢 Гарнизон/Город",
    }

# 🗂️ Группировка по таблицам (для Mapping Editor и Doc Generator)
DB_COLUMNS_MAP = {
    "social_data": [
        "surname", "name", "patronymic", "birth_date", "birth_place_town",
        "birth_place_district", "birth_place_region", "birth_place_country",
        "tab_number", "personal_number", "category_id", "rank_id",
        "drafted_by_commissariat", "draft_date", "povsk", "selection_date",
        "education", "criminal_record", "social_media_account", "bank_card_number",
        "passport_series", "passport_number", "passport_issue_date", "passport_issued_by",
        "military_id_series", "military_id_number", "military_id_issue_date", "military_id_issued_by",
        "appearance_features", "personal_marks", "federal_search_info", "military_contacts", "relatives_info"
    ],
    "addresses": [
        "region", "district", "town", "street", "house",
        "building", "letter", "apartment", "room", "check_date", "check_result", "postal_index"
    ],
    "service_places": [
        "place_name","military_unit_number", "military_unit_id", "garrison_id", "position_id", "commanders",
        "postal_index", "postal_region", "postal_district", "postal_town", "postal_street",
        "postal_house", "postal_building", "postal_letter", "postal_apartment", "postal_room", "place_contacts"
    ],
    "soch_episodes": [
        "soch_date", "soch_location", "order_date_number", "witnesses",
        "reasons", "weapon_info", "clothing", "movement_options", "other_info",
        "duty_officer_commissariat", "duty_officer_omvd", "investigation_info",
        "prosecution_info", "criminal_case_info", "search_date", "found_by",
        "search_circumstances", "notification_recipient", "notification_date", "notification_number"
    ],
    "incoming_orders": [
        "initiator_type_id", "initiator_full_name", "military_unit_id",
        "order_date", "order_number", "receipt_date", "receipt_number",
        "postal_index", "postal_region", "postal_district", "postal_town",
        "postal_street", "postal_house", "postal_building", "postal_letter",
        "postal_apartment", "postal_room", "initiator_contacts",
        "our_response_date", "our_response_number"
    ],
    "outgoing_requests": [
        "request_type_id", "military_unit_id", "issue_date", "issue_number",
        "request_text", "signed_by_position", "recipient_id",
        "response_date", "response_number", "response_status"
    ],
    "recipients": [
        "name", "contacts", "postal_index", "postal_region",
        "postal_district", "postal_town", "postal_street", "postal_house",
        "postal_building", "postal_letter", "postal_apartment", "postal_room",
        "request_type_id"
    ],
    "krd": [
        "status_id", "last_service_place_id", "is_locked", "locked_by", "locked_at"
    ],
    "signatories": [
    "full_name", "position", "rank", "garrison"
    ],
}

# 🔍 Карта справочников: поле ID -> (Таблица справочника, Колонка с названием)
LOOKUP_TABLES = {
    'category_id': ('krd.categories', 'name'),
    'rank_id': ('krd.ranks', 'name'),
    'status_id': ('krd.statuses', 'name'),
    'request_type_id': ('krd.request_types', 'name'),
    'initiator_type_id': ('krd.initiator_types', 'name'),
    'military_unit_id': ('krd.military_units', 'name'),
    'garrison_id': ('krd.garrisons', 'name'),
    'position_id': ('krd.positions', 'name'),
    'recipient_id': ('krd.recipients', 'name')
}

# 🛠️ ВСПОМОГАТЕЛЬНЫЙ РЕЗОЛВЕР (использовать в UI вместо прямого доступа к словарю)
def get_field_description(table_name: str, column_name: str) -> str:
    """
    Безопасно получает описание поля с учетом контекста таблицы.
    Алгоритм: 1) table_column -> 2) column -> 3) column_name (fallback)
    """
    return COLUMN_DESCRIPTIONS.get(f"{table_name}_{column_name}", 
           COLUMN_DESCRIPTIONS.get(column_name, column_name))