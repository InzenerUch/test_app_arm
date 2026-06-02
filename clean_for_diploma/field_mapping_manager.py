from PyQt6.QtSql import QSqlQuery
import json
import traceback
from PyQt6.QtWidgets import QMessageBox
class FieldMappingManager:
    def __init__(self, parent):
        self.parent = parent
        if not hasattr(parent, 'db') or parent.db is None:
            raise ValueError("Parent must have a valid 'db' connection")
    def load_field_mappings(self, template_id):
        print(f"🔄 FieldMappingManager.load_field_mappings(template_id={template_id})")
        query = QSqlQuery(self.parent.db)
        query.prepare("""
            SELECT field_name, db_column, table_name, db_columns, is_composite
            FROM krd.field_mappings
            WHERE template_id = :template_id
            ORDER BY id
        ✅ ИСПРАВЛЕНО: Реальное сохранение сопоставлений из UI в БД
        Поддерживает новый формат данных ComboBox: "table_name|db_column"
Определение таблицы по имени колонки (использует данные родителя)"""
        if hasattr(self.parent, 'db_columns'):
            for table, cols in self.parent.db_columns.items():
                if col_name in cols:
                    return table
        return "social_data"
    def _save_composite_mapping(self, template_id, field_name, db_columns):
        ins_query = QSqlQuery(self.parent.db)
        ins_query.prepare("""
            INSERT INTO krd.field_mappings
            (template_id, field_name, db_column, table_name, db_columns, is_composite)
            VALUES (:template_id, :field_name, :db_column, :table_name, :db_columns, TRUE)
            INSERT INTO krd.field_mappings
            (template_id, field_name, db_column, table_name, is_composite)
            VALUES (:template_id, :field_name, :db_column, :table_name, FALSE)
        """)
        ins_query.bindValue(":template_id", template_id)
        ins_query.bindValue(":field_name", field_name)
        ins_query.bindValue(":db_column", db_column)
        ins_query.bindValue(":table_name", table_name)
        if not ins_query.exec():
            raise Exception(f"Ошибка сохранения простого поля: {ins_query.lastError().text()}")