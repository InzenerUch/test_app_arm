import sys
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QApplication, QMessageBox
def init_database():
    app = QApplication(sys.argv)
    db = QSqlDatabase.addDatabase("QPSQL")
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")
    if not db.open():
        print(f"Не удалось подключиться к базе данных:\n{db.lastError().text()}")
        return False
    query = QSqlQuery(db)
    query.exec("""
        CREATE TABLE IF NOT EXISTS krd.users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            email VARCHAR(255),
            role_id INTEGER REFERENCES krd.user_roles(id) ON DELETE SET NULL ON UPDATE CASCADE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS krd.user_roles (
            id SERIAL PRIMARY KEY,
            role_name VARCHAR(50) UNIQUE NOT NULL,
            description TEXT
        );
        CREATE TABLE IF NOT EXISTS krd.user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES krd.users(id) ON DELETE CASCADE ON UPDATE CASCADE,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_time TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
            INSERT INTO krd.users (username, password_hash, full_name, role_id, is_active)
            VALUES (?, ?, ?, 2, TRUE)
        """)
        query.addBindValue("admin")
        query.addBindValue(password_hash)
        query.addBindValue("Администратор системы")
        query.exec()
        print("Создан пользователь admin с паролем admin123")
    print("База данных инициализирована успешно")
    return True
if __name__ == "__main__":
    init_database()