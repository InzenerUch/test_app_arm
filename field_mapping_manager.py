"""
Менеджер для работы с сопоставлениями полей
✅ ДОБАВЛЕНО: Подробный вывод в консоль каждого сопоставления
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
        print(f"\n{'='*70}")
        print(f"🔄 FieldMappingManager.load_field_mappings(template_id={template_id})")
        print(f"{'='*70}")
        
        query = QSqlQuery(self.parent.db)
        query.prepare("""
            SELECT id, field_name, db_column, table_name, db_columns, is_composite
            FROM krd.field_mappings
            WHERE template_id = :template_id
            ORDER BY id
        """)
        query.bindValue(":template_id", template_id)
        
        if not query.exec():
            print(f"❌ Ошибка загрузки: {query.lastError().text()}")
            return
        
        row = 0
        total_loaded = 0
        
        print(f"\n📖 ЗАГРУЗКА СОПОСТАВЛЕНИЙ ИЗ БД:")
        print(f"{'─'*70}")
        
        while query.next():
            try:
                mapping_id = query.value("id")
                field_name = query.value("field_name")
                db_column_raw = query.value("db_column")
                table_name = query.value("table_name")
                db_columns_json = query.value("db_columns")
                is_composite = query.value("is_composite") or False
                
                print(f"\n📋 Запись #{row} (ID={mapping_id}):")
                print(f"   🔑 Переменная шаблона: '{field_name}'")
                print(f"   📦 db_column (сырое): '{db_column_raw}'")
                print(f"   📦 table_name: '{table_name}'")
                print(f"   📦 is_composite: {is_composite}")
                
                if is_composite and db_columns_json:
                    print(f"   📦 db_columns (JSON): {db_columns_json[:100]}...")
                    print(f"   ✅ Тип: СОСТАВНОЕ → add_composite_mapping_row()")
                    self.parent.add_composite_mapping_row(row, field_name, db_columns_json, table_name)
                    total_loaded += 1
                else:
                    # ✅ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: передаём ПОЛНЫЙ ПУТЬ table_name|db_column
                    if db_column_raw and "|" in db_column_raw:
                        stored_table, column_name = db_column_raw.split("|", 1)
                        full_path = db_column_raw  # "social_data|name"
                        print(f"   🔍 Разбор 'table|column': table='{stored_table}', column='{column_name}'")
                    else:
                        # Фоллбэк для старых записей
                        column_name = db_column_raw
                        full_path = f"{table_name}|{db_column_raw}"
                        print(f"   🔍 Только column_name: '{column_name}' → полный путь='{full_path}'")
                    
                    print(f"   ✅ Тип: ПРОСТОЕ → add_simple_mapping_row(field='{field_name}', col='{full_path}', table='{table_name}')")
                    # ✅ Передаём полный путь вместо просто имени колонки
                    self.parent.add_simple_mapping_row(row, field_name, full_path, table_name)
                    total_loaded += 1
                
                row += 1
                
            except Exception as e:
                print(f"❌ Ошибка обработки строки {row}: {e}")
                traceback.print_exc()
        
        print(f"\n{'─'*70}")
        print(f"✅ ВСЕГО ЗАГРУЖЕНО: {total_loaded} сопоставлений")
        print(f"{'='*70}\n")
    
    def save_field_mappings(self, template_id):
        """
        ✅ ИСПРАВЛЕНО: Реальное сохранение сопоставлений из UI в БД
        Поддерживает новый формат данных ComboBox: "table_name|db_column"
        """
        print(f"\n{'='*70}")
        print(f"💾 FieldMappingManager.save_field_mappings(template_id={template_id})")
        print(f"{'='*70}")
        
        if not hasattr(self.parent, 'mapping_table') or not self.parent.mapping_table:
            print("❌ Ошибка: mapping_table не найден")
            return False

        mapping_table = self.parent.mapping_table
        row_count = mapping_table.rowCount()
        
        print(f"\n📊 Всего строк в таблице UI: {row_count}")
        
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
            
            print(f"\n🗑️ Старые сопоставления удалены. Сохранение {row_count} новых...")
            print(f"{'─'*70}")

            # 3. Читаем UI и сохраняем
            saved_count = 0
            
            for row in range(row_count):
                var_widget = mapping_table.cellWidget(row, 0)
                val_widget = mapping_table.cellWidget(row, 1)
                type_widget = mapping_table.cellWidget(row, 2)
                
                if not var_widget or not val_widget:
                    print(f"\n⚠️ Строка {row}: пропущена (нет виджетов)")
                    continue
                
                var_name = var_widget.currentText()
                type_text = type_widget.text() if type_widget else ""
                is_composite = "Составное" in type_text
                
                print(f"\n📝 Строка {row}:")
                print(f"   🔑 Переменная: '{var_name}'")
                print(f"   📦 Тип: '{type_text}' (составное={is_composite})")
                
                if is_composite:
                    # Составное поле: извлекаем JSON через виджет
                    if hasattr(self.parent, 'composite_widget'):
                        db_columns = self.parent.composite_widget.get_composite_columns(val_widget)
                        if db_columns:
                            print(f"   📦 Составные колонки: {db_columns}")
                            self._save_composite_mapping(template_id, var_name, db_columns)
                            saved_count += 1
                            print(f"   ✅ СОХРАНЕНО (составное)")
                        else:
                            print(f"   ⚠️ Нет колонок в составном поле")
                else:
                    # Простое поле: берем currentData из ComboBox
                    if hasattr(val_widget, 'currentData'):
                        raw_data = val_widget.currentData()
                        print(f"   📦 raw_data из ComboBox: '{raw_data}' (тип={type(raw_data).__name__})")
                        
                        if raw_data:
                            # НОВЫЙ ФОРМАТ: "table_name|db_column"
                            if "|" in str(raw_data):
                                table_name, db_column = str(raw_data).split("|", 1)
                                print(f"   🔍 Разбор 'table|column': table='{table_name}', column='{db_column}'")
                            else:
                                # Фоллбэк для старых сопоставлений (только имя колонки)
                                db_column = str(raw_data)
                                table_name = self._get_table_name_for_column(db_column)
                                print(f"   🔍 Только column_name: '{db_column}' → table='{table_name}' (автоопределение)")
                            
                            print(f"   💾 ЗАПИСЬ В БД: field='{var_name}', table='{table_name}', column='{db_column}', full_path='{table_name}|{db_column}'")
                            self._save_simple_mapping(template_id, var_name, db_column, table_name)
                            saved_count += 1
                            print(f"   ✅ СОХРАНЕНО (простое)")
                        else:
                            print(f"   ⚠️ raw_data пустой")
                    else:
                        print(f"   ⚠️ Нет метода currentData")
            
            # 4. Коммит
            if not self.parent.db.commit():
                raise Exception(f"Ошибка коммита: {self.parent.db.lastError().text()}")
                
            print(f"\n{'─'*70}")
            print(f"✅ УСПЕШНО СОХРАНЕНО: {saved_count} из {row_count} сопоставлений")
            print(f"{'='*70}\n")
            return True
            
        except Exception as e:
            self.parent.db.rollback()
            print(f"\n❌ ОШИБКА СОХРАНЕНИЯ: {e}")
            traceback.print_exc()
            print(f"{'='*70}\n")
            return False

    def _get_table_name_for_column(self, col_name):
        """Определение таблицы по имени колонки (использует данные родителя)"""
        print(f"      🔎 Поиск таблицы для колонки '{col_name}'...")
        if hasattr(self.parent, 'db_columns'):
            for table, cols in self.parent.db_columns.items():
                if col_name in cols:
                    print(f"         ✅ Найдено в таблице '{table}'")
                    return table
        print(f"         ⚠️ Не найдено, используем fallback 'social_data'")
        return "social_data"

    def _save_composite_mapping(self, template_id, field_name, db_columns):
        print(f"      📦 Сохранение составного поля: {field_name}")
        print(f"         Колонки: {db_columns}")
        
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
        
        print(f"         ✅ Сохранено")
    
    def _save_simple_mapping(self, template_id, field_name, db_column, table_name):
        print(f"      📦 Сохранение простого поля: {field_name} → {table_name}.{db_column}")
        
        ins_query = QSqlQuery(self.parent.db)
        ins_query.prepare("""
        INSERT INTO krd.field_mappings
        (template_id, field_name, db_column, table_name, is_composite)
        VALUES (:template_id, :field_name, :db_column, :table_name, FALSE)
        """)
        ins_query.bindValue(":template_id", template_id)
        ins_query.bindValue(":field_name", field_name)
        # СОХРАНЯЕМ ПОЛНЫЙ ПУТЬ: "table_name|column_name"
        full_path = f"{table_name}|{db_column}"
        ins_query.bindValue(":db_column", full_path)
        ins_query.bindValue(":table_name", table_name)
        
        if not ins_query.exec():
            raise Exception(f"Ошибка сохранения простого поля: {ins_query.lastError().text()}")
        
        print(f"         ✅ Записано в БД: db_column='{full_path}'")