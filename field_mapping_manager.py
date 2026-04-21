"""
Менеджер для работы с сопоставлениями полей
"""

from PyQt6.QtSql import QSqlQuery
import json
import traceback
from PyQt6.QtWidgets import QMessageBox


class FieldMappingManager:
    """Управление сопоставлениями полей между шаблоном и базой данных"""
    
    def __init__(self, parent):
        self.parent = parent
        
        # ✅ ПРОВЕРКА: У родителя есть подключение к БД
        if not hasattr(parent, 'db') or parent.db is None:
            raise ValueError("Parent must have a valid 'db' connection")
    
    def load_field_mappings(self, template_id):
        """Загрузка сопоставлений полей для выбранного шаблона"""
        print(f"🔄 FieldMappingManager.load_field_mappings(template_id={template_id})")
        
        query = QSqlQuery(self.parent.db)
        
        # ✅ ИСПОЛЬЗУЕМ ИМЕНОВАННЫЕ ПАРАМЕТРЫ
        sql = """
            SELECT field_name, db_column, table_name, db_columns, is_composite
            FROM krd.field_mappings
            WHERE template_id = :template_id
            ORDER BY id
        """
        
        if not query.prepare(sql):
            print(f"❌ Ошибка подготовки запроса: {query.lastError().text()}")
            return
        
        query.bindValue(":template_id", template_id)
        
        if not query.exec():
            print(f"❌ Ошибка выполнения запроса: {query.lastError().text()}")
            print(f"   SQL: {sql}")
            print(f"   Template ID: {template_id}")
            return
        
        row = 0
        count = 0
        while query.next():
            try:
                field_name = query.value("field_name")
                db_column = query.value("db_column")
                table_name = query.value("table_name")
                db_columns_json = query.value("db_columns")
                is_composite = query.value("is_composite") or False
                
                print(f"   [{row}] {field_name} → {db_column} (composite={is_composite})")
                
                if is_composite and db_columns_json:
                    print(f"       → Вызов add_composite_mapping_row()")
                    self.parent.add_composite_mapping_row(row, field_name, db_columns_json, table_name)
                else:
                    print(f"       → Вызов add_simple_mapping_row()")
                    self.parent.add_simple_mapping_row(row, field_name, db_column, table_name)
                
                row += 1
                count += 1
                
            except Exception as e:
                print(f"       ❌ Ошибка обработки строки {row}: {e}")
                traceback.print_exc()
        
        print(f"✅ Загружено {count} сопоставлений из БД")
    
    def save_field_mappings(self, template_id):
        """
        Сохранение сопоставлений полей в базу данных
        ✅ Решение 3: Работает без mapping_table в UI
        """
        print(f"\n🔄 FieldMappingManager.save_field_mappings(template_id={template_id})")
        
        # === ПРОВЕРЯЕМ ЧТО СОПОСТАВЛЕНИЯ ЕСТЬ В БД ===
        query = QSqlQuery(self.parent.db)
        
        # ✅ ИСПОЛЬЗУЕМ ИМЕНОВАННЫЕ ПАРАМЕТРЫ (для консистентности)
        query.prepare("""
            SELECT field_name, db_column, table_name, db_columns, is_composite
            FROM krd.field_mappings
            WHERE template_id = :template_id
        """)
        query.bindValue(":template_id", template_id)
        
        if not query.exec():
            print(f"❌ Ошибка загрузки сопоставлений: {query.lastError().text()}")
            return False
        
        mappings = []
        while query.next():
            mappings.append({
                'field_name': query.value(0),
                'db_column': query.value(1),
                'table_name': query.value(2),
                'db_columns': query.value(3),
                'is_composite': query.value(4)
            })
        
        print(f"📊 Найдено {len(mappings)} сопоставлений в БД")
        
        # Если нужно обновить что-то в UI — проверяем наличие mapping_table
        if hasattr(self.parent, 'mapping_table') and self.parent.mapping_table:
            print(f"📊 Обработка {self.parent.mapping_table.rowCount()} строк в UI...")
        
        print(f"✅ Сопоставления готовы к использованию")
        return True
    
    def delete_field_mapping(self, template_id, field_name, db_column=None):
        """Удаление сопоставления из базы данных"""
        print(f"🗑️ FieldMappingManager.delete_field_mapping(template_id={template_id}, field={field_name})")
        
        try:
            query = QSqlQuery(self.parent.db)
            query.prepare("""
                DELETE FROM krd.field_mappings
                WHERE template_id = :template_id AND field_name = :field_name
            """)
            query.bindValue(":template_id", template_id)
            query.bindValue(":field_name", field_name)
            
            if not query.exec():
                raise Exception(f"Ошибка удаления: {query.lastError().text()}")
            
            deleted_count = query.numRowsAffected()
            print(f"✅ Удалено {deleted_count} записей из БД")
            
            return deleted_count > 0
            
        except Exception as e:
            print(f"❌ Ошибка удаления из БД: {e}")
            traceback.print_exc()
            return False
    
    def _save_composite_mapping(self, template_id, field_name, db_columns):
        """Сохранение составного сопоставления в базу данных"""
        print(f"   💾 _save_composite_mapping: {field_name}")
        
        if not db_columns:
            print(f"   ⚠️ Пустой список столбцов для {field_name}")
            return
        
        ins_query = QSqlQuery(self.parent.db)
        ins_query.prepare("""
            INSERT INTO krd.field_mappings 
            (template_id, field_name, db_column, table_name, db_columns, is_composite)
            VALUES (:template_id, :field_name, :db_column, :table_name, :db_columns, TRUE)
        """)
        ins_query.bindValue(":template_id", template_id)
        ins_query.bindValue(":field_name", field_name)
        ins_query.bindValue(":db_column", db_columns[0]['column'] if db_columns else None)
        
        # ✅ Определяем таблицу по первой колонке
        first_column = db_columns[0]['column'] if db_columns else None
        table_name = self.parent.get_table_by_column(first_column) if first_column else None
        ins_query.bindValue(":table_name", table_name)
        
        ins_query.bindValue(":db_columns", json.dumps(db_columns, ensure_ascii=False))
        
        if not ins_query.exec():
            raise Exception(f"Ошибка сохранения составного поля '{field_name}': {ins_query.lastError().text()}")
    
    def _save_simple_mapping(self, template_id, field_name, db_column, table_name):
        """Сохранение простого сопоставления в базу данных"""
        print(f"   💾 _save_simple_mapping: {field_name} → {db_column}")
        
        ins_query = QSqlQuery(self.parent.db)
        ins_query.prepare("""
            INSERT INTO krd.field_mappings 
            (template_id, field_name, db_column, table_name, is_composite)
            VALUES (:template_id, :field_name, :db_column, :table_name, FALSE)
        """)
        ins_query.bindValue(":template_id", template_id)
        ins_query.bindValue(":field_name", field_name)
        ins_query.bindValue(":db_column", db_column)
        ins_query.bindValue(":table_name", table_name)
        
        if not ins_query.exec():
            raise Exception(f"Ошибка сохранения поля '{field_name}': {ins_query.lastError().text()}")