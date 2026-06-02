from PyQt6.QtSql import QSqlQuery
import json
class DatabaseHandler:
    def __init__(self, db_connection):
        self.db = db_connection
    def load_field_mappings(self, template_id):
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT field_name, db_column, table_name, db_columns, is_composite
            FROM krd.field_mappings
            WHERE template_id = ?
            ORDER BY field_name
Сохранение сопоставлений полей в базу данных"""
        try:
            if not self.db.transaction():
                raise Exception(f"Не удалось начать транзакцию: {self.db.lastError().text()}")
            del_query = QSqlQuery(self.db)
            del_query.prepare("DELETE FROM krd.field_mappings WHERE template_id = ?")
            del_query.addBindValue(template_id)
            if not del_query.exec():
                raise Exception(f"Ошибка удаления старых сопоставлений: {del_query.lastError().text()}")
            saved_count = 0
            for mapping in mappings:
                if mapping['is_composite'] and mapping['db_columns_json']:
                    db_columns = json.loads(mapping['db_columns_json']) if isinstance(mapping['db_columns_json'], str) else mapping['db_columns_json']
                    self._save_composite_mapping(template_id, mapping, db_columns)
                else:
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
        ins_query = QSqlQuery(self.db)
        ins_query.prepare("""
            INSERT INTO krd.field_mappings
            (template_id, field_name, db_column, table_name, db_columns, is_composite)
 VALUES (?, ?, ?, ?, ?, TRUE)
Сохранение простого сопоставления в базу данных"""
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