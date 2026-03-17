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
    
    def load_field_mappings(self, template_id):
        """Загрузка сопоставлений полей для выбранного шаблона"""
        print(f"🔄 FieldMappingManager.load_field_mappings(template_id={template_id})")
        
        # ✅ ИСПРАВЛЕНО: Передаем БД в конструктор
        query = QSqlQuery(self.parent.db)
        
        # ✅ ИСПРАВЛЕНО: Используем именованные параметры
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
        """Сохранение сопоставлений полей с поддержкой составных полей"""
        print(f"🔄 FieldMappingManager.save_field_mappings(template_id={template_id})")
        
        try:
            if not self.parent.db.transaction():
                raise Exception(f"Не удалось начать транзакцию: {self.parent.db.lastError().text()}")
            
            print(f"🗑️ Удаление старых сопоставлений...")
            
            # ✅ ИСПРАВЛЕНО: Передаем БД в конструктор
            del_query = QSqlQuery(self.parent.db)
            del_query.prepare("DELETE FROM krd.field_mappings WHERE template_id = :template_id")
            del_query.bindValue(":template_id", template_id)
            
            if not del_query.exec():
                raise Exception(f"Ошибка удаления старых сопоставлений: {del_query.lastError().text()}")
            
            deleted_count = del_query.numRowsAffected()
            print(f"   Удалено {deleted_count} старых записей")
            
            saved_count = 0
            print(f"📊 Обработка {self.parent.mapping_table.rowCount()} строк...")
            
            for row in range(self.parent.mapping_table.rowCount()):
                var_w = self.parent.mapping_table.cellWidget(row, 0)
                if not var_w:
                    print(f"   [{row}] ⚠️ Пропущено (нет виджета переменной)")
                    continue
                
                field_name = var_w.currentText().strip()
                composite_widget = self.parent.mapping_table.cellWidget(row, 1)
                
                if not composite_widget:
                    print(f"   [{row}] ⚠️ Пропущено (нет виджета столбца)")
                    continue
                
                if hasattr(composite_widget, 'layout') and composite_widget.layout():
                    print(f"   [{row}] 📝 Составное поле: {field_name}")
                    db_columns = self.parent.composite_widget.get_composite_columns(composite_widget)
                    print(f"       Столбцов: {len(db_columns)}")
                    
                    if db_columns:
                        self._save_composite_mapping(template_id, field_name, db_columns)
                        saved_count += 1
                        print(f"       ✅ Сохранено")
                    else:
                        print(f"       ⚠️ Пропущено (нет столбцов)")
                else:
                    col_w = composite_widget
                    db_column = col_w.currentText().strip()
                    print(f"   [{row}] 📝 Простое поле: {field_name} → {db_column}")
                    
                    table_name = self.parent.get_table_by_column(db_column)
                    
                    if field_name and db_column and table_name:
                        self._save_simple_mapping(template_id, field_name, db_column, table_name)
                        saved_count += 1
                        print(f"       ✅ Сохранено")
                    else:
                        print(f"       ⚠️ Пропущено (неполные данные)")
            
            if not self.parent.db.commit():
                raise Exception(f"Ошибка коммита: {self.parent.db.lastError().text()}")
            
            print(f"✅ Сохранено {saved_count} сопоставлений для шаблона {template_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            self.parent.db.rollback()
            traceback.print_exc()
            QMessageBox.critical(self.parent, "Ошибка сохранения", 
                               f"Не удалось сохранить сопоставления:\n{str(e)}")
            return False
    
    def delete_field_mapping(self, template_id, field_name, db_column=None):
        """Удаление сопоставления из базы данных"""
        print(f"🗑️ FieldMappingManager.delete_field_mapping(template_id={template_id}, field={field_name})")
        
        try:
            # ✅ ИСПРАВЛЕНО: Передаем БД в конструктор
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
        
        # ✅ ИСПРАВЛЕНО: Передаем БД в конструктор
        ins_query = QSqlQuery(self.parent.db)
        ins_query.prepare("""
            INSERT INTO krd.field_mappings 
            (template_id, field_name, db_column, table_name, db_columns, is_composite)
            VALUES (:template_id, :field_name, :db_column, :table_name, :db_columns, TRUE)
        """)
        ins_query.bindValue(":template_id", template_id)
        ins_query.bindValue(":field_name", field_name)
        ins_query.bindValue(":db_column", db_columns[0]['column'] if db_columns else None)
        ins_query.bindValue(":table_name", self.parent.get_table_by_column(db_columns[0]['column']) if db_columns else None)
        ins_query.bindValue(":db_columns", json.dumps(db_columns))
        
        if not ins_query.exec():
            raise Exception(f"Ошибка сохранения составного поля '{field_name}': {ins_query.lastError().text()}")
    
    def _save_simple_mapping(self, template_id, field_name, db_column, table_name):
        """Сохранение простого сопоставления в базу данных"""
        print(f"   💾 _save_simple_mapping: {field_name} → {db_column}")
        
        # ✅ ИСПРАВЛЕНО: Передаем БД в конструктор
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