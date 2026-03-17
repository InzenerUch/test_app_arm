"""
Обработчик базы данных для работы с сопоставлениями
"""

from PyQt6.QtSql import QSqlQuery
import json

class DatabaseHandler:
    """Управление запросами к базе данных"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def load_field_mappings(self, template_id):
        """Загрузка сопоставлений полей для выбранного шаблона"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT field_name, db_column, table_name, db_columns, is_composite
            FROM krd.field_mappings
            WHERE template_id = ?
            ORDER BY field_name
        """)
        query.addBind(template_id)
        query.exec()
        
        mappings = []
        while query.next():
            field_name = query.value(0)
            db_column = query.value(1)
            table_name = query.value(2)
            db_columns_json = query.value(3)
            is_composite = query.value(4) or False
            
            mappings.append({
                'field_name': field_name,
                'db_column': db_column,
                'table_name': table_name,
                'db_columns_json': db_columns_json,
                'is_composite': is_composite
            })
        
        return mappings
    
    def save_field_mappings(self, template_id, mappings):
        """Сохранение сопоставлений полей в базу данных"""
        try:
            if not self.db.transaction():
                raise Exception(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
            
            # Удаляем старые сопоставления
            del_query = QSqlQuery(self.db)
            del_query.prepare("DELETE FROM krd.field_mappings WHERE template_id = ?")
            del_query.addBindValue(template_id)
            if not del_query.exec():
                raise Exception(f"Ошибка удаления старых сопоставлений: {del_query.lastError().text()}")
            
            saved_count = 0
            for mapping in mappings:
                if mapping['is_composite'] and mapping['db_columns_json']:
                    # Составное сопоставление
                    db_columns = json.loads(mapping['db_columns_json']) if isinstance(mapping['db_columns_json'], str) else mapping['db_columns_json']
                    self._save_composite_mapping(template_id, mapping, db_columns)
                else:
                    # Простое сопоставление
                    self._save_simple_mapping(template_id, mapping)
                
                saved_count += 1
            
            if not self.db.commit():
                raise Exception(f"Ошибка коммита: {self.db.lastError().text()}")
            
            print(f"✅ Сохранено {saved_count} сопоставлений для шаблона {template_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Ошибка сохранения сопоставлений: {str(e)}")
    
    def _save_composite_mapping(self, template_id, mapping, db_columns):
        """Сохранение составного сопоставления в базу данных"""
        ins_query = QSqlQuery(self.db)
        ins_query.prepare("""
            INSERT INTO krd.field_mappings 
            (template_id, field_name, db_column, table_name, db_columns, is_composite)
 VALUES (?, ?, ?, ?, ?, TRUE)
        """)
        ins_query.addBindValue(template_id)
        ins_query.addBindValue(mapping['field_name'])
        ins_query.addBindValue(db_columns[0]['column'] if db_columns else None)
        ins_query.addBindValue(mapping['table_name'])
        ins_query.addBindValue(json.dumps(db_columns))
        ins_query.addBindValue(True)
        
        if not ins_query.exec():
            raise Exception(f"Ошибка сохранения составного поля: {ins_query.lastError().text()}")
    
    def _save_simple_mapping(self, template_id, mapping):
        """Сохранение простого сопоставления в базу данных"""
        ins_query = QSqlQuery(self.db)
        ins_query.prepare("""
            INSERT INTO krd.field_mappings 
            (template_id, field_name, db_column, table_name, is_composite)
            VALUES (?, ?, ?, ?, FALSE)
        """)
        ins_query.addBindValue(template_id)
        ins_query.addBindValue(mapping['field_name'])
        ins_query.addBindValue(mapping['db_column'])
        ins_query.addBindValue(mapping['table_name'])
        ins_query.addBindValue(False)
        
        if not ins_query.exec():
            raise Exception(f"Ошибка сохранения простого поля: {ins_query.lastError().text()}")