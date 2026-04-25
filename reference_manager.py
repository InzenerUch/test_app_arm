"""
Универсальный менеджер для работы со справочниками
Поддерживает все справочники из схемы БД
"""

from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtWidgets import QMessageBox
from typing import Dict, List, Optional, Tuple
import traceback


# === КОНФИГУРАЦИЯ СПРАВОЧНИКОВ ===
REFERENCE_TABLES = {
    "categories": {
        "title": "Категории военнослужащих",
        "columns": ["id", "name"],
        "editable_columns": ["name"],
        "required_columns": ["name"],
        "icon": "📋"
    },
    "ranks": {
        "title": "Воинские звания",
        "columns": ["id", "name"],
        "editable_columns": ["name"],
        "required_columns": ["name"],
        "icon": "⭐"
    },
    "statuses": {
        "title": "Статусы КРД",
        "columns": ["id", "name"],
        "editable_columns": ["name"],
        "required_columns": ["name"],
        "icon": "📊"
    },
    "military_units": {
        "title": "Военные управления",
        "columns": ["id", "name"],
        "editable_columns": ["name"],
        "required_columns": ["name"],
        "icon": "🎖️"
    },
    "garrisons": {
        "title": "Гарнизоны",
        "columns": ["id", "name"],
        "editable_columns": ["name"],
        "required_columns": ["name"],
        "icon": "🏢"
    },
    "positions": {
        "title": "Воинские должности",
        "columns": ["id", "name"],
        "editable_columns": ["name"],
        "required_columns": ["name"],
        "icon": "💼"
    },
    "request_types": {
        "title": "Типы запросов",
        "columns": ["id", "name"],
        "editable_columns": ["name"],
        "required_columns": ["name"],
        "icon": "📤"
    },
    "initiator_types": {
        "title": "Типы инициаторов",
        "columns": ["id", "name"],
        "editable_columns": ["name"],
        "required_columns": ["name"],
        "icon": "📩"
    },
    "user_roles": {
        "title": "Роли пользователей",
        "columns": ["id", "role_name", "description"],
        "editable_columns": ["role_name", "description"],
        "required_columns": ["role_name"],
        "icon": "👥"
    }
}


class ReferenceManager:
    """
    Универсальный менеджер для управления справочниками
    
    Поддерживает:
    - Загрузку данных из любого справочника
    - Добавление новых записей
    - Редактирование существующих
    - Удаление (мягкое если есть is_deleted)
    - Поиск и фильтрацию
    """
    
    def __init__(self, db_connection):
        """
        Инициализация менеджера
        
        Args:
            db_connection: Подключение к базе данных
        """
        self.db = db_connection
        self.current_table = None
        self.config = None
    
    def get_table_config(self, table_name: str) -> Optional[Dict]:
        """Получение конфигурации таблицы"""
        return REFERENCE_TABLES.get(table_name)
    
    def get_all_tables(self) -> List[str]:
        """Получение списка всех доступных таблиц-справочников"""
        return list(REFERENCE_TABLES.keys())
    
    def load_data(self, table_name: str, search_text: str = "") -> Optional[QSqlQueryModel]:
        """
        Загрузка данных из справочника
        
        Args:
            table_name: Имя таблицы
            search_text: Текст для поиска (опционально)
            
        Returns:
            QSqlQueryModel с данными или None при ошибке
        """
        self.current_table = table_name
        self.config = self.get_table_config(table_name)
        
        if not self.config:
            print(f"❌ Таблица '{table_name}' не найдена в конфигурации")
            return None
        
        try:
            model = QSqlQueryModel()
            columns = ", ".join(self.config["columns"])
            
            # Проверяем есть ли soft delete
            has_soft_delete = self._has_soft_delete(table_name)
            
            if search_text:
                # Поиск по всем текстовым полям
                search_conditions = []
                for col in self.config["editable_columns"]:
                    search_conditions.append(f"{col} ILIKE :search")
                
                where_clause = " AND ".join(search_conditions)
                if has_soft_delete:
                    where_clause += " AND is_deleted = FALSE"
                
                sql = f"""
                    SELECT {columns}
                    FROM krd.{table_name}
                    WHERE {where_clause}
                    ORDER BY id
                """
                
                query = QSqlQuery(self.db)
                query.prepare(sql)
                query.bindValue(":search", f"%{search_text}%")
                query.exec()
                
                if query.lastError().isValid():
                    print(f"❌ Ошибка поиска: {query.lastError().text()}")
                    return None
                
                model.setQuery(query)
            else:
                # Без поиска
                where = "WHERE is_deleted = FALSE" if has_soft_delete else ""
                sql = f"""
                    SELECT {columns}
                    FROM krd.{table_name}
                    {where}
                    ORDER BY id
                """
                
                model.setQuery(sql, self.db)
                
                if model.lastError().isValid():
                    print(f"❌ Ошибка загрузки: {model.lastError().text()}")
                    return None
            
            print(f"✅ Загружено {model.rowCount()} записей из {table_name}")
            return model
            
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            traceback.print_exc()
            return None
    
    def _has_soft_delete(self, table_name: str) -> bool:
        """Проверка наличия мягкого удаления в таблице"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'krd' 
            AND table_name = :table 
            AND column_name = 'is_deleted'
        """)
        query.bindValue(":table", table_name)
        query.exec()
        return query.next()
    
    def add_record(self, table_name: str,  Dict) -> Tuple[bool, int]:
        """
        Добавление новой записи
        
        Args:
            table_name: Имя таблицы
            data: Словарь с данными {column: value}
            
        Returns:
            (успех, ID новой записи)
        """
        config = self.get_table_config(table_name)
        if not config:
            return False, 0
        
        try:
            # Проверка обязательных полей
            for required in config["required_columns"]:
                if required not in data or not data[required]:
                    print(f"❌ Обязательное поле '{required}' не заполнено")
                    return False, 0
            
            columns = list(data.keys())
            placeholders = [f":{col}" for col in columns]
            
            sql = f"""
                INSERT INTO krd.{table_name} ({", ".join(columns)})
                VALUES ({", ".join(placeholders)})
                RETURNING id
            """
            
            query = QSqlQuery(self.db)
            query.prepare(sql)
            
            for col, value in data.items():
                query.bindValue(f":{col}", value)
            
            if not query.exec():
                print(f"❌ Ошибка добавления: {query.lastError().text()}")
                return False, 0
            
            # Получаем ID новой записи
            if query.next():
                new_id = query.value(0)
                print(f"✅ Добавлена запись ID={new_id} в {table_name}")
                return True, new_id
            else:
                print("❌ Не удалось получить ID новой записи")
                return False, 0
                
        except Exception as e:
            print(f"❌ Ошибка добавления записи: {e}")
            traceback.print_exc()
            return False, 0
    
    def update_record(self, table_name: str, record_id: int,  Dict) -> bool:
        """
        Обновление записи
        
        Args:
            table_name: Имя таблицы
            record_id: ID записи
             Словарь с данными для обновления
            
        Returns:
            Успешность операции
        """
        config = self.get_table_config(table_name)
        if not config:
            return False
        
        try:
            # Разрешаем обновлять только editable_columns
            valid_data = {k: v for k, v in data.items() if k in config["editable_columns"]}
            
            if not valid_data:
                print("⚠️ Нет данных для обновления")
                return False
            
            set_clause = ", ".join([f"{col} = :{col}" for col in valid_data.keys()])
            
            sql = f"""
                UPDATE krd.{table_name}
                SET {set_clause}
                WHERE id = :id
            """
            
            query = QSqlQuery(self.db)
            query.prepare(sql)
            
            for col, value in valid_data.items():
                query.bindValue(f":{col}", value)
            
            query.bindValue(":id", record_id)
            
            if not query.exec():
                print(f"❌ Ошибка обновления: {query.lastError().text()}")
                return False
            
            if query.numRowsAffected() > 0:
                print(f"✅ Обновлена запись ID={record_id} в {table_name}")
                return True
            else:
                print(f"⚠️ Запись ID={record_id} не найдена")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка обновления записи: {e}")
            traceback.print_exc()
            return False
    
    def delete_record(self, table_name: str, record_id: int, soft_delete: bool = True) -> bool:
        """
        Удаление записи
        
        Args:
            table_name: Имя таблицы
            record_id: ID записи
            soft_delete: Использовать мягкое удаление
            
        Returns:
            Успешность операции
        """
        try:
            has_soft = self._has_soft_delete(table_name)
            
            if soft_delete and has_soft:
                # Мягкое удаление
                sql = f"""
                    UPDATE krd.{table_name}
                    SET is_deleted = TRUE,
                        deleted_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """
            else:
                # Полное удаление
                sql = f"""
                    DELETE FROM krd.{table_name}
                    WHERE id = :id
                """
            
            query = QSqlQuery(self.db)
            query.prepare(sql)
            query.bindValue(":id", record_id)
            
            if not query.exec():
                print(f"❌ Ошибка удаления: {query.lastError().text()}")
                return False
            
            if query.numRowsAffected() > 0:
                delete_type = "Мягкое" if (soft_delete and has_soft) else "Полное"
                print(f"✅ {delete_type} удаление записи ID={record_id} из {table_name}")
                return True
            else:
                print(f"⚠️ Запись ID={record_id} не найдена")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка удаления записи: {e}")
            traceback.print_exc()
            return False
    
    def get_record(self, table_name: str, record_id: int) -> Optional[Dict]:
        """Получение одной записи по ID"""
        config = self.get_table_config(table_name)
        if not config:
            return None
        
        try:
            columns = ", ".join(config["columns"])
            
            sql = f"""
                SELECT {columns}
                FROM krd.{table_name}
                WHERE id = :id
            """
            
            query = QSqlQuery(self.db)
            query.prepare(sql)
            query.bindValue(":id", record_id)
            
            if not query.exec() or not query.next():
                return None
            
            record = {}
            for i, col in enumerate(config["columns"]):
                record[col] = query.value(i)
            
            return record
            
        except Exception as e:
            print(f"❌ Ошибка получения записи: {e}")
            return None
    
    def get_combo_data(self, table_name: str) -> List[Tuple[int, str]]:
        """
        Получение данных для ComboBox (id, name)
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            Список кортежей (id, name)
        """
        config = self.get_table_config(table_name)
        if not config:
            return []
        
        try:
            has_soft = self._has_soft_delete(table_name)
            where = "WHERE is_deleted = FALSE" if has_soft else ""
            
            # Определяем колонку для отображения
            display_column = "name" if "name" in config["columns"] else config["editable_columns"][0]
            
            sql = f"""
                SELECT id, {display_column}
                FROM krd.{table_name}
                {where}
                ORDER BY {display_column}
            """
            
            query = QSqlQuery(self.db)
            query.exec(sql)
            
            result = []
            while query.next():
                result.append((query.value(0), query.value(1)))
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка получения данных для ComboBox: {e}")
            return []