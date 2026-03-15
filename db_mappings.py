# db_mappings.py
# ⚠️ СТРОГО СООТВЕТСТВУЕТ schema_only.sql
# Технические поля (id, is_deleted, created_at, updated_at, deleted_*) исключены из UI-маппингов

TABLE_NAMES_RU = {
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

COLUMN_DESCRIPTIONS = {
    # === SOCIAL_DATA ===
    "surname": "👤 Фамилия военнослужащего",
    "name": "👤 Имя военнослужащего",
    "patronymic": "👤 Отчество военнослужащего",
    "birth_date": "📅 Дата рождения",
    "birth_place_town": "🌍 Населенный пункт места рождения",
    "birth_place_district": "🌍 Район места рождения",
    "birth_place_region": "🌍 Субъект РФ места рождения",
    "birth_place_country": "🌍 Страна места рождения",
    "tab_number": "🔢 Табельный номер",
    "personal_number": "🔢 Личный номер",
    "category_id": "📋 ID категории (справочник)",
    "rank_id": "⭐ ID воинского звания (справочник)",
    "drafted_by_commissariat": "🎖️ Наименование военкомата призыва",
    "draft_date": "📅 Дата призыва на военную службу",
    "povsk": "🎖️ Наименование ПОВСК",
    "selection_date": "📅 Дата отбора на военную службу",
    "education": "🎓 Образование военнослужащего",
    "criminal_record": "⚖️ Сведения о судимости",
    "social_media_account": "📱 Аккаунты в социальных сетях",
    "bank_card_number": "💳 Номер банковской карты",
    "passport_series": "📄 Серия паспорта",
    "passport_number": "📄 Номер паспорта",
    "passport_issue_date": "📅 Дата выдачи паспорта",
    "passport_issued_by": "📄 Кем выдан паспорт",
    "military_id_series": "🎫 Серия военного билета",
    "military_id_number": "🎫 Номер военного билета",
    "military_id_issue_date": "📅 Дата выдачи военного билета",
    "military_id_issued_by": "🎫 Кем выдан военный билет",
    "appearance_features": "👁️ Особенности внешности",
    "personal_marks": "👁️ Личные приметы (татуировки, шрамы)",
    "federal_search_info": "🔍 Сведения о федеральном розыске",
    "military_contacts": "📞 Контакты военнослужащего",
    "relatives_info": "👨‍👩‍👧 Сведения о близких родственниках",

    # === ADDRESSES ===
    "region": "📍 Субъект РФ (область, край, республика)",
    "district": "📍 Административный район",
    "town": "📍 Населенный пункт (город, село)",
    "street": "📍 Улица",
    "house": "🏠 Номер дома",
    "building": "🏢 Номер корпуса",
    "letter": "🔤 Литера здания",
    "apartment": "🚪 Номер квартиры",
    "room": "🚪 Номер комнаты",
    "check_date": "📅 Дата адресной проверки",
    "check_result": "✅ Результат проверки адреса",
    "postal_index": "📮 Почтовый индекс",

    # === SERVICE_PLACES ===
    "place_name": "🎖️ Наименование места службы",
    "military_unit_number": "🔢 Номер воинской части (в/ч)",
    "military_unit_id": "🎖️ ID военного управления (справочник)",
    "garrison_id": "🏢 ID гарнизона (справочник)",
    "position_id": "💼 ID воинской должности (справочник)",
    "commanders": "👨‍✈️ Командиры (ФИО, контакты)",
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

    # === SOCH_EPISODES ===
    "soch_date": "⚠️ Дата СОЧ",
    "soch_location": "⚠️ Место СОЧ",
    "order_date_number": "⚠️ Дата и номер приказа о СОЧ",
    "witnesses": "👥 Очевидцы СОЧ",
    "reasons": "💡 Вероятные причины СОЧ",
    "weapon_info": "🔫 Сведения о наличии оружия",
    "clothing": "🧥 Описание одежды",
    "movement_options": "🚶 Возможные направления движения",
    "other_info": "📝 Другая значимая информация",
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

    # === INCOMING_ORDERS ===
    "initiator_type_id": "📩 ID типа инициатора (справочник)",
    "initiator_full_name": "📩 Наименование инициатора",
    "military_unit_id": "🎖️ ID военного управления (справочник)",
    "order_date": "📩 Дата поручения",
    "order_number": "📩 Номер поручения",
    "receipt_date": "📩 Дата поступления",
    "receipt_number": "📩 Входящий номер",
    "initiator_contacts": "📩 Контакты инициатора",
    "our_response_date": "📩 Дата ответа",
    "our_response_number": "📩 Исходящий номер ответа",

    # === OUTGOING_REQUESTS ===
    "request_type_id": "📤 ID типа запроса (справочник)",
    "military_unit_id": "🎖️ ID военного управления адресата (справочник)",
    "issue_date": "📤 Дата запроса",
    "issue_number": "📤 Номер запроса",
    "request_text": "📤 Текст запроса",
    "signed_by_position": "📤 Должность подписанта",
    "recipient_id": "👥 ID адресата (справочник)",
    "response_date": "📅 Дата получения ответа",
    "response_number": "📬 Номер ответа",
    "response_status": "📊 Статус ответа",

    # === RECIPIENTS (⚠️ В БД поле называется name, а НЕ recipient_name!) ===
    "name": "👥 Наименование адресата",
    "contacts": "👥 Контакты адресата (телефон, email)",
    "postal_index": "👥 Почтовый индекс адресата",
    "postal_region": "👥 Субъект РФ адресата",
    "postal_district": "👥 Административный район адресата",
    "postal_town": "👥 Город/населенный пункт адресата",
    "postal_street": "👥 Улица адресата",
    "postal_house": "👥 Дом адресата",
    "postal_building": "👥 Корпус/строение адресата",
    "postal_letter": "👥 Литера адресата",
    "postal_apartment": "👥 Квартира адресата",
    "postal_room": "👥 Комната адресата",
    "request_type_id": "📤 ID типа запроса по умолчанию (справочник)",

    # === KRD (доп. поля) ===
    "status_id": "📊 ID статуса КРД (справочник)",
    "last_service_place_id": "🎖️ ID последнего места службы",
    "is_locked": "🔒 Заблокировано для редактирования",
    "locked_by": "👤 ID пользователя, заблокировавшего КРД",
    "locked_at": "📅 Дата и время блокировки"
}

# Группировка по таблицам (для Mapping Editor и Doc Generator)
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
    ]
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