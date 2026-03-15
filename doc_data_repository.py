"""
Репозиторий данных для генератора документов
Загрузка шаблонов, типов запросов, связанных записей
✅ ИСПРАВЛЕНО: Все SQL-запросы переведены на именованные параметры (:name) для QPSQL
✅ ИНТЕГРИРОВАНО: Использование DB_COLUMNS_MAP из db_mappings.py (единый источник истины)
✅ ОПТИМИЗИРОВАНО: Разделены экземпляры QSqlQuery для связанных таблиц во избежание конфликтов драйвера
"""
from PyQt6.QtSql import QSqlQuery

# ✅ БЕЗОПАСНЫЙ ИМПОРТ ЕДИНОГО СПРАВОЧНИКА
try:
    from db_mappings import DB_COLUMNS_MAP
except ImportError:
    # Fallback на случай, если файл еще не создан или не импортирован
    DB_COLUMNS_MAP = {}

class DocDataRepository:
    """Репозиторий для работы с данными генерации документов"""
    
    def __init__(self, db):
        self.db = db
        
    def load_request_types(self):
        """Загрузка типов запросов"""
        q = QSqlQuery(self.db)
        q.prepare("SELECT id, name FROM krd.request_types ORDER BY name")
        result = []
        if q.exec():
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
        result = []
        if q.exec():
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
            WHERE id = :id
        """)
        q.bindValue(":id", template_id)
        
        if q.exec() and q.next():
            return q.value(0), q.value(1)
        raise Exception("Шаблон не найден")
        
    def get_template_description(self, template_id):
        """Получение описания шаблона"""
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT description 
            FROM krd.document_templates 
            WHERE id = :id
        """)
        q.bindValue(":id", template_id)
        
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
        
        # ✅ Адреса (отдельный экземпляр запроса)
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
        """)
        q_addr.bindValue(":krd_id", krd_id)
        if q_addr.exec():
            while q_addr.next():
                result['addresses'].append((q_addr.value(0), f"🏠 {q_addr.value(1)}"))
                
        # ✅ Места службы (отдельный экземпляр запроса)
        q_svc = QSqlQuery(self.db)
        q_svc.prepare("""
            SELECT id, 
                COALESCE(place_name, 'Без названия') || 
                ' (' || COALESCE(postal_town, '') || ')'
            FROM krd.service_places
            WHERE krd_id = :krd_id
            ORDER BY id DESC
        """)
        q_svc.bindValue(":krd_id", krd_id)
        if q_svc.exec():
            while q_svc.next():
                result['service_places'].append((q_svc.value(0), f"🎖️ {q_svc.value(1)}"))
                
        # ✅ Эпизоды СОЧ (отдельный экземпляр запроса)
        q_soch = QSqlQuery(self.db)
        q_soch.prepare("""
            SELECT id, 
                COALESCE(soch_date::text, '') || ' - ' || 
                COALESCE(soch_location, '')
            FROM krd.soch_episodes
            WHERE krd_id = :krd_id
            ORDER BY soch_date DESC
        """)
        q_soch.bindValue(":krd_id", krd_id)
        if q_soch.exec():
            while q_soch.next():
                result['soch_episodes'].append((q_soch.value(0), f"⚠️ {q_soch.value(1)}"))
                
        return result
        
    def get_db_columns(self):
        """Структура колонок БД (загружается из единого источника)"""
        return DB_COLUMNS_MAP
        
    def get_used_tables(self, template_id):
        """Получение списка таблиц, используемых в шаблоне"""
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