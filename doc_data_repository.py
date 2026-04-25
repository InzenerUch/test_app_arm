"""
Репозиторий данных для генератора документов
Загрузка шаблонов, типов запросов, связанных записей
"""
from PyQt6.QtSql import QSqlQuery

class DocDataRepository:
    """Репозиторий для работы с данными генерации документов"""
    
    def __init__(self, db):
        self.db = db
        
    def load_request_types(self):
        """Загрузка типов запросов"""
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.request_types ORDER BY name")
        result = []
        while q.next():
            result.append((q.value(0), q.value(1)))
        return result
        
    def load_templates(self):
        """Загрузка шаблонов"""
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT id, name, description 
            FROM krd.document_templates 
            WHERE is_deleted = FALSE 
            ORDER BY name
        """)
        q.exec()
        result = []
        while q.next():
            result.append({
                'id': q.value(0),
                'name': q.value(1),
                'description': q.value(2) or ''
            })
        return result
        
    def get_template_data(self, template_id):
        """Получение данных шаблона (байты + имя)"""
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT template_data, name 
            FROM krd.document_templates 
            WHERE id = ?
        """)
        q.addBindValue(template_id)
        
        if q.exec() and q.next():
            return q.value(0), q.value(1)
        raise Exception("Шаблон не найден")
        
    def get_template_description(self, template_id):
        """Получение описания шаблона"""
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT description 
            FROM krd.document_templates 
            WHERE id = ?
        """)
        q.addBindValue(template_id)
        
        if q.exec() and q.next():
            return q.value(0) or ''
        return ''
        
    def load_related_records(self, krd_id):
        """Загрузка связанных записей"""
        result = {
            'addresses': [],
            'service_places': [],
            'soch_episodes': []
        }
        
        # Адреса
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT id, 
                COALESCE(region, '') || ', ' || 
                COALESCE(district, '') || ', ' || 
                COALESCE(town, '') || ', ' || 
                COALESCE(street, '') || ', ' || 
                COALESCE(house, '') as address_string
            FROM krd.addresses
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        q.addBindValue(krd_id)
        if q.exec():
            while q.next():
                result['addresses'].append((q.value(0), f"🏠 {q.value(1)}"))
                
        # Места службы
        q.prepare("""
            SELECT id, 
                COALESCE(place_name, 'Без названия') || 
                ' (' || COALESCE(postal_town, '') || ')'
            FROM krd.service_places
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        q.addBindValue(krd_id)
        if q.exec():
            while q.next():
                result['service_places'].append((q.value(0), f"🎖️ {q.value(1)}"))
                
        # Эпизоды СОЧ
        q.prepare("""
            SELECT id, 
                COALESCE(soch_date::text, '') || ' - ' || 
                COALESCE(soch_location, '')
            FROM krd.soch_episodes
            WHERE krd_id = ?
            ORDER BY soch_date DESC
        """)
        q.addBindValue(krd_id)
        if q.exec():
            while q.next():
                result['soch_episodes'].append((q.value(0), f"⚠️ {q.value(1)}"))
                
        return result
        
    def get_db_columns(self):
        """Структура колонок БД"""
        return {
            "social_data": [
                "surname", "name", "patronymic", "birth_date", 
                "birth_place_town", "birth_place_district", "birth_place_region", 
                "birth_place_country", "tab_number", "personal_number", 
                "category_id", "rank_id", "drafted_by_commissariat", 
                "draft_date", "povsk", "selection_date", "education", 
                "criminal_record", "social_media_account", "bank_card_number", 
                "passport_series", "passport_number", "passport_issue_date", 
                "passport_issued_by", "military_id_series", "military_id_number", 
                "military_id_issue_date", "military_id_issued_by", 
                "appearance_features", "personal_marks", "federal_search_info", 
                "military_contacts", "relatives_info"
            ],
            "addresses": [
                "region", "district", "town", "street", "house", 
                "building", "letter", "apartment", "room", 
                "check_date", "check_result"
            ],
            "service_places": [
                "place_name", "military_unit_id", "garrison_id", 
                "position_id", "commanders", "postal_index", 
                "postal_region", "postal_district", "postal_town", 
                "postal_street", "postal_house", "postal_building", 
                "postal_letter", "postal_apartment", "postal_room", 
                "place_contacts"
            ],
            "soch_episodes": [
                "soch_date", "soch_location", "order_date_number", 
                "witnesses", "reasons", "weapon_info", "clothing", 
                "movement_options", "other_info", "duty_officer_commissariat", 
                "duty_officer_omvd", "investigation_info", "prosecution_info", 
                "criminal_case_info", "search_date", "found_by", 
                "search_circumstances", "notification_recipient", 
                "notification_date", "notification_number"
            ]
        }
        
    def get_used_tables(self, template_id):
        """Получение списка таблиц, используемых в шаблоне"""
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT table_name 
            FROM krd.field_mappings 
            WHERE template_id = ?
        """)
        q.addBindValue(template_id)
        
        tables = set()
        if q.exec():
            while q.next():
                tables.add(q.value(0))
        return tables