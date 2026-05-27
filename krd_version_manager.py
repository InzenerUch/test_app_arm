"""
Менеджер версионирования КРД
Отвечает за создание снапшотов, получение истории и транзакционный откат.
"""
from PyQt6.QtSql import QSqlQuery
import json
import traceback

class KrdVersionManager:
    def __init__(self, db_connection):
        self.db = db_connection

    def capture_snapshot(self, krd_id: int, user_id: int, description: str = "Автосохранение") -> bool:
        """Создаёт JSONB-снапшот всей КРД и сохраняет в krd_versions"""
        try:
            q = QSqlQuery(self.db)
            q.prepare("SELECT COALESCE(MAX(version_number), 0) + 1 FROM krd.krd_versions WHERE krd_id = :krd_id")
            q.bindValue(":krd_id", krd_id)
            if q.exec() and q.next():
                new_ver = q.value(0)
            else:
                return False

            q2 = QSqlQuery(self.db)
            q2.prepare("""
                SELECT jsonb_build_object(
                    'krd', (SELECT row_to_json(k) FROM krd.krd k WHERE id = :krd_id),
                    'social_data', (SELECT row_to_json(s) FROM krd.social_data s WHERE krd_id = :krd_id),
                    'addresses', (SELECT jsonb_agg(row_to_json(a)) FROM krd.addresses a WHERE krd_id = :krd_id),
                    'service_places', (SELECT jsonb_agg(row_to_json(sp)) FROM krd.service_places sp WHERE krd_id = :krd_id),
                    'soch_episodes', (SELECT jsonb_agg(row_to_json(so)) FROM krd.soch_episodes so WHERE krd_id = :krd_id),
                    'incoming_orders', (SELECT jsonb_agg(row_to_json(io)) FROM krd.incoming_orders io WHERE krd_id = :krd_id)
                )
            """)
            q2.bindValue(":krd_id", krd_id)
            if not (q2.exec() and q2.next()):
                return False
            snapshot_json = q2.value(0)

            q3 = QSqlQuery(self.db)
            q3.prepare("""
                INSERT INTO krd.krd_versions (krd_id, version_number, created_by, description, snapshot_data)
                VALUES (:krd_id, :version, :user_id, :desc, :snapshot)
            """)
            q3.bindValue(":krd_id", krd_id)
            q3.bindValue(":version", new_ver)
            q3.bindValue(":user_id", user_id)
            q3.bindValue(":desc", description)
            q3.bindValue(":snapshot", snapshot_json)
            return q3.exec()
        except Exception as e:
            print(f"❌ [VERSION] Ошибка создания снапшота: {e}")
            traceback.print_exc()
            return False

    def get_versions(self, krd_id: int) -> list[dict]:
        """Возвращает список версий для КРД"""
        versions = []
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT v.id, v.version_number, v.created_at, u.username, v.description
            FROM krd.krd_versions v
            LEFT JOIN krd.users u ON v.created_by = u.id
            WHERE v.krd_id = :krd_id
            ORDER BY v.version_number DESC
        """)
        q.bindValue(":krd_id", krd_id)
        if q.exec():
            while q.next():
                versions.append({
                    "id": q.value(0),
                    "version": q.value(1),
                    "created_at": q.value(2),
                    "author": q.value(3) or "Система",
                    "description": q.value(4)
                })
        return versions

    def rollback_to(self, version_id: int, krd_id: int) -> bool:
        """Транзакционный откат КРД к указанной версии"""
        if not self.db.transaction():
            return False
        try:
            q = QSqlQuery(self.db)
            q.prepare("SELECT snapshot_data FROM krd.krd_versions WHERE id = :id")
            q.bindValue(":id", version_id)
            if not (q.exec() and q.next()):
                self.db.rollback()
                return False

            data = json.loads(q.value(0))

            # 1:1 таблицы
            if data.get('social_data'):
                sd = data['social_data']
                sd.pop('id', None)
                sets = ", ".join([f"{k}=:{k}" for k in sd.keys()])
                uq = QSqlQuery(self.db)
                uq.prepare(f"UPDATE krd.social_data SET {sets} WHERE krd_id = :krd_id")
                for k, v in sd.items(): uq.bindValue(f":{k}", v)
                uq.bindValue(":krd_id", krd_id)
                uq.exec()

            # 1:N таблицы (полная замена)
            for table, key in [('krd.addresses', 'addresses'), ('krd.service_places', 'service_places'),
                               ('krd.soch_episodes', 'soch_episodes'), ('krd.incoming_orders', 'incoming_orders')]:
                if data.get(key):
                    dq = QSqlQuery(self.db)
                    dq.prepare(f"DELETE FROM {table} WHERE krd_id = :krd_id")
                    dq.bindValue(":krd_id", krd_id)
                    dq.exec()
                    for row_data in data[key]:
                        iq = QSqlQuery(self.db)
                        cols = ", ".join(row_data.keys())
                        placeholders = ", ".join([f":{k}" for k in row_data.keys()])
                        iq.prepare(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})")
                        for k, v in row_data.items(): iq.bindValue(f":{k}", v)
                        iq.exec()

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"❌ [VERSION] Ошибка отката: {e}")
            traceback.print_exc()
            return False