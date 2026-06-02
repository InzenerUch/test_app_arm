import bcrypt
from PyQt6.QtSql import QSqlQuery
class SimpleAuthManager:
    def __init__(self, db_connection):
        self.db = db_connection
    def authenticate_user(self, username: str, password: str) -> dict | None:
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT u.id, u.username, u.full_name, r.role_name, u.password_hash
            FROM krd.users u
            JOIN krd.user_roles r ON u.role_id = r.id
            WHERE u.username = ? AND u.is_active = TRUE
        """)
        query.addBindValue(username)
        if not query.exec() or not query.next():
            return None
        user_id = query.value(0)
        stored_hash = query.value(4)
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            try:
                upd = QSqlQuery(self.db)
                upd.prepare("UPDATE krd.users SET last_login = CURRENT_TIMESTAMP WHERE id = ?")
                upd.addBindValue(user_id)
                upd.exec()
            except Exception as e:
                print(f"⚠️ Ошибка обновления last_login: {e}")
            return {
                'id': int(user_id),
                'username': query.value(1),
                'full_name': query.value(2),
                'role': query.value(3)
            }
        return None