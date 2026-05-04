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
    """
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_table = None
        self.config = None

    def get_table_config(self, table_name: str) -> Optional[Dict]:
        return REFERENCE_TABLES.get(table_name)

    def get_all_tables(self) -> List[str]:
        return list(REFERENCE_TABLES.keys())

    def load_data(self, table_name: str, search_text: str = "") -> Optional[QSqlQueryModel]:
        self.current_table = table_name
        self.config = self.get_table_config(table_name)
        if not self.config:
            print(f"❌ Таблица '{table_name}' не найдена в конфигурации")
            return None

        try:
            model = QSqlQueryModel()
            columns = ", ".join(self.config["columns"])
            has_soft_delete = self._has_soft_delete(table_name)

            if search_text:
                search_conditions = [f"{col} ILIKE :search" for col in self.config["editable_columns"]]
                where_clause = " AND ".join(search_conditions)
                if has_soft_delete: where_clause += " AND is_deleted = FALSE"
                sql = f"SELECT {columns} FROM krd.{table_name} WHERE {where_clause} ORDER BY id"
                query = QSqlQuery(self.db)
                query.prepare(sql)
                query.bindValue(":search", f"%{search_text}%")
                query.exec()
                if query.lastError().isValid(): return None
                model.setQuery(query)
            else:
                where = "WHERE is_deleted = FALSE" if has_soft_delete else ""
                sql = f"SELECT {columns} FROM krd.{table_name} {where} ORDER BY id"
                model.setQuery(sql, self.db)
                if model.lastError().isValid(): return None

            print(f"✅ Загружено {model.rowCount()} записей из {table_name}")
            return model
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            traceback.print_exc()
            return None

    def _has_soft_delete(self, table_name: str) -> bool:
        query = QSqlQuery(self.db)
        query.prepare("SELECT column_name FROM information_schema.columns WHERE table_schema='krd' AND table_name=:table AND column_name='is_deleted'")
        query.bindValue(":table", table_name)
        return query.exec() and query.next()

    # ✅ ИСПРАВЛЕНО: добавлено имя параметра `data:`
    def add_record(self, table_name: str, data: Dict) -> Tuple[bool, int]:
        config = self.get_table_config(table_name)
        if not config: return False, 0
        for req in config["required_columns"]:
            if req not in data or not data[req]: return False, 0

        cols = list(data.keys())
        placeholders = ", ".join([f":{c}" for c in cols])
        sql = f"INSERT INTO krd.{table_name} ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id"

        q = QSqlQuery(self.db)
        q.prepare(sql)
        for k, v in data.items(): q.bindValue(f":{k}", v)

        if q.exec() and q.next(): return True, q.value(0)
        return False, 0

    # ✅ ИСПРАВЛЕНО: добавлено имя параметра `data:`
    def update_record(self, table_name: str, record_id: int, data: Dict) -> bool:
        config = self.get_table_config(table_name)
        if not config: return False

        valid_data = {k: v for k, v in data.items() if k in config["editable_columns"]}

        if not valid_data:
            print("⚠️ Нет данных для обновления")
            return False

        sets = ", ".join([f"{k}=:{k}" for k in valid_data.keys()])
        sql = f"UPDATE krd.{table_name} SET {sets} WHERE id=:id"

        q = QSqlQuery(self.db)
        q.prepare(sql)
        for k, v in valid_data.items(): q.bindValue(f":{k}", v)
        q.bindValue(":id", record_id)

        return q.exec() and q.numRowsAffected() > 0

    def delete_record(self, table_name: str, record_id: int, soft_delete: bool = True) -> bool:
        has_soft = self._has_soft_delete(table_name)
        if soft_delete and has_soft:
            sql = f"UPDATE krd.{table_name} SET is_deleted=TRUE, deleted_at=CURRENT_TIMESTAMP WHERE id=:id"
        else:
            sql = f"DELETE FROM krd.{table_name} WHERE id=:id"
            
        q = QSqlQuery(self.db)
        q.prepare(sql)
        q.bindValue(":id", record_id)
        return q.exec() and q.numRowsAffected() > 0

    def get_record(self, table_name: str, record_id: int) -> Optional[Dict]:
        config = self.get_table_config(table_name)
        if not config: return None
        q = QSqlQuery(self.db)
        q.prepare(f"SELECT {', '.join(config['columns'])} FROM krd.{table_name} WHERE id=:id")
        q.bindValue(":id", record_id)
        
        if q.exec() and q.next():
            return {col: q.value(i) for i, col in enumerate(config["columns"])}
        return None

    def get_combo_data(self, table_name: str) -> List[Tuple[int, str]]:
        config = self.get_table_config(table_name)
        if not config: return []
        try:
            has_soft = self._has_soft_delete(table_name)
            where = "WHERE is_deleted = FALSE" if has_soft else ""
            display_col = "name" if "name" in config["columns"] else config["editable_columns"][0]
            
            q = QSqlQuery(self.db)
            q.exec(f"SELECT id, {display_col} FROM krd.{table_name} {where} ORDER BY {display_col}")
            return [(q.value(0), q.value(1)) for _ in range(q.size()) if q.next()]
        except Exception as e:
            print(f"❌ Ошибка получения данных для ComboBox: {e}")
            return []