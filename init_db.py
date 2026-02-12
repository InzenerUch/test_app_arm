"""
Файл инициализации базы данных
"""

import sys
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QApplication, QMessageBox


def init_database():
    """
    Инициализация базы данных с начальными данными
    """
    # Создаем приложение для работы с Qt SQL
    app = QApplication(sys.argv)
    
    # Подключение к базе данных
    db = QSqlDatabase.addDatabase("QPSQL")
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")
    
    if not db.open():
        print(f"Не удалось подключиться к базе данных:\n{db.lastError().text()}")
        return False
    
    # Создание таблицы пользователей, если не существует
    query = QSqlQuery(db)
    
    # Создаем таблицу пользователей
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
    """)
    
    # Создаем таблицу ролей пользователей
    query.exec("""
        CREATE TABLE IF NOT EXISTS krd.user_roles (
            id SERIAL PRIMARY KEY,
            role_name VARCHAR(50) UNIQUE NOT NULL,
            description TEXT
        );
    """)
    
    # Добавляем базовые роли
    query.exec("INSERT INTO krd.user_roles (role_name, description) VALUES ('user', 'Обычный пользователь') ON CONFLICT (role_name) DO NOTHING;")
    query.exec("INSERT INTO krd.user_roles (role_name, description) VALUES ('admin', 'Администратор') ON CONFLICT (role_name) DO NOTHING;")
    
    # Создаем таблицу сессий пользователей
    query.exec("""
        CREATE TABLE IF NOT EXISTS krd.user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES krd.users(id) ON DELETE CASCADE ON UPDATE CASCADE,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_time TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)
    
    # Проверяем, есть ли уже пользователь admin
    query.prepare("SELECT id FROM krd.users WHERE username = ?")
    query.addBindValue("admin")
    query.exec()
    
    if not query.next():
        # Создаем пользователя admin с хешем пароля для "admin123"
        import bcrypt
        password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        query.prepare("""
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