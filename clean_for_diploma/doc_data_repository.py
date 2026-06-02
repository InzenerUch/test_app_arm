from PyQt6.QtSql import QSqlQuery
try:
    from db_mappings import DB_COLUMNS_MAP
except ImportError:
    DB_COLUMNS_MAP = {}
class DocDataRepository:
    def __init__(self, db):
        self.db = db
    def load_request_types(self):
        q = QSqlQuery(self.db)
        q.prepare("SELECT id, name FROM krd.request_types ORDER BY name")
        result = []
        if q.exec():
            while q.next():
                result.append((q.value(0), q.value(1)))
        return result
    def load_templates(self):
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT id, name, description
            FROM krd.document_templates
            WHERE is_deleted = FALSE
            ORDER BY name
Получение данных шаблона (байты + имя)"""
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT template_data, name
            FROM krd.document_templates
            WHERE id = :id
Получение описания шаблона"""
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT description
            FROM krd.document_templates
            WHERE id = :id
Загрузка связанных записей"""
        result = {
            'addresses': [],
            'service_places': [],
            'soch_episodes': []
        }
        q_addr = QSqlQuery(self.db)
        q_addr.prepare("""
            SELECT id,
                COALESCE(region, '') || ', ' ||
                COALESCE(district, '') || ', ' ||
                COALESCE(town, '') || ', ' ||
                COALESCE(street, '') || ', ' ||
                COALESCE(house, '') as address_string
            FROM krd.addresses
            WHERE krd_id = :krd_id
            ORDER BY id DESC
            SELECT id,
                COALESCE(place_name, 'Без названия') ||
                ' (' || COALESCE(postal_town, '') || ')'
            FROM krd.service_places
            WHERE krd_id = :krd_id
            ORDER BY id DESC
            SELECT id,
                COALESCE(soch_date::text, '') || ' - ' ||
                COALESCE(soch_location, '')
            FROM krd.soch_episodes
            WHERE krd_id = :krd_id
            ORDER BY soch_date DESC
Структура колонок БД (загружается из единого источника)"""
        return DB_COLUMNS_MAP
    def get_used_tables(self, template_id):
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT table_name
            FROM krd.field_mappings
            WHERE template_id = :tid
        """)
        q.bindValue(":tid", template_id)
        tables = set()
        if q.exec():
            while q.next():
                tables.add(q.value(0))
        return tables