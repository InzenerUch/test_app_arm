"""
Менеджер для работы с сопоставлениями полей
✅ ИСПРАВЛЕНО: Реализовано реальное сохранение данных из UI в БД
"""
from PyQt6.QtSql import QSqlQuery
import json
import traceback
from PyQt6.QtWidgets import QMessageBox

class FieldMappingManager:
    """Управление сопоставлениями полей между шаблоном и базой данных"""
    
    def __init__(self, parent):
        self.parent = parent
        
        if not hasattr(parent, 'db') or parent.db is None:
            raise ValueError("Parent must have a valid 'db' connection")
    
    def load_field_mappings(self, template_id):
        """Загрузка сопоставлений из БД в таблицу UI"""
        print(f"🔄 FieldMappingManager.load_field_mappings(template_id={template_id})")
        
        query = QSqlQuery(self.parent.db)
        query.prepare("""
            SELECT field_name, db_column, table_name, db_columns, is_composite
            FROM krd.field_mappings
            WHERE template_id = :template_id
            ORDER BY id
        """)
        query.bindValue(":template_id", template_id)
        
        if not query.exec():
            print(f"❌ Ошибка загрузки: {query.lastError().text()}")
            return
        
        row = 0
        while query.next():
            try:
                field_name = query.value("field_name")
                db_column = query.value("db_column")
                table_name = query.value("table_name")
                db_columns_json = query.value("db_columns")
                is_composite = query.value("is_composite") or False
                
                if is_composite and db_columns_json:
                    self.parent.add_composite_mapping_row(row, field_name, db_columns_json, table_name)
                else:
                    self.parent.add_simple_mapping_row(row, field_name, db_column, table_name)
                row += 1
            except Exception as e:
                print(f"❌ Ошибка обработки строки: {e}")

    def save_field_mappings(self, template_id):
        """
        ✅ ИСПРАВЛЕНО: Реальное сохранение сопоставлений из UI в БД
        """
        print(f"💾 FieldMappingManager.save_field_mappings(template_id={template_id})")
        
        if not hasattr(self.parent, 'mapping_table') or not self.parent.mapping_table:
            print("❌ Ошибка: mapping_table не найден")
            return False

        mapping_table = self.parent.mapping_table
        row_count = mapping_table.rowCount()
        
        try:
            # 1. Транзакция
            if not self.parent.db.transaction():
                raise Exception(f"Не удалось начать транзакцию: {self.parent.db.lastError().text()}")
            
            # 2. Удаляем старые сопоставления
            del_query = QSqlQuery(self.parent.db)
            del_query.prepare("DELETE FROM krd.field_mappings WHERE template_id = :template_id")
            del_query.bindValue(":template_id", template_id)
            if not del_query.exec():
                raise Exception(f"Ошибка удаления старых данных: {del_query.lastError().text()}")
            
            print(f"🗑️ Старые сопоставления удалены. Сохранение {row_count} новых...")

            # 3. Читаем UI и сохраняем
            for row in range(row_count):
                var_widget = mapping_table.cellWidget(row, 0)
                val_widget = mapping_table.cellWidget(row, 1)
                type_widget = mapping_table.cellWidget(row, 2)
                
                if not var_widget or not val_widget: continue
                
                var_name = var_widget.currentText()
                type_text = type_widget.text() if type_widget else ""
                is_composite = "Составное" in type_text
                
                if is_composite:
                    # Составное поле: извлекаем JSON через виджет
                    if hasattr(self.parent, 'composite_widget'):
                        db_columns = self.parent.composite_widget.get_composite_columns(val_widget)
                        if db_columns:
                            self._save_composite_mapping(template_id, var_name, db_columns)
                else:
                    # Простое поле: берем currentData из ComboBox
                    if hasattr(val_widget, 'currentData'):
                        db_column = val_widget.currentData()
                        if db_column:
                            table_name = self._get_table_name_for_column(db_column)
                            self._save_simple_mapping(template_id, var_name, db_column, table_name)
            
            # 4. Коммит
            if not self.parent.db.commit():
                raise Exception(f"Ошибка коммита: {self.parent.db.lastError().text()}")
                
            print(f"✅ Успешно сохранено {row_count} сопоставлений")
            return True
            
        except Exception as e:
            self.parent.db.rollback()
            print(f"❌ Ошибка сохранения: {e}")
            traceback.print_exc()
            return False

    def _get_table_name_for_column(self, col_name):
        """Определение таблицы по имени колонки (использует данные родителя)"""
        if hasattr(self.parent, 'db_columns'):
            for table, cols in self.parent.db_columns.items():
                if col_name in cols:
                    return table
        return "social_data" # Fallback

    def _save_composite_mapping(self, template_id, field_name, db_columns):
        ins_query = QSqlQuery(self.parent.db)
        ins_query.prepare("""
            INSERT INTO krd.field_mappings 
            (template_id, field_name, db_column, table_name, db_columns, is_composite)
            VALUES (:template_id, :field_name, :db_column, :table_name, :db_columns, TRUE)
        """)
        ins_query.bindValue(":template_id", template_id)
        ins_query.bindValue(":field_name", field_name)
        ins_query.bindValue(":db_column", db_columns[0]['column'])
        
        table_name = self._get_table_name_for_column(db_columns[0]['column'])
        ins_query.bindValue(":table_name", table_name)
        ins_query.bindValue(":db_columns", json.dumps(db_columns, ensure_ascii=False))
        
        if not ins_query.exec():
            raise Exception(f"Ошибка сохранения составного поля: {ins_query.lastError().text()}")
    
    def _save_simple_mapping(self, template_id, field_name, db_column, table_name):
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
            raise Exception(f"Ошибка сохранения простого поля: {ins_query.lastError().text()}")