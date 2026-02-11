"""
Модуль для работы с авторизацией пользователей
Содержит классы для работы с пользователями
"""

import bcrypt
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtCore import QDateTime
import logging


class AuthorizationManager:
    """
    Класс для управления авторизацией пользователей
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        # Убираем инициализацию базы данных из конструктора
    
    def get_available_roles(self):
        """
        Получение списка доступных ролей
        Возвращает список словарей с информацией о ролях
        """
        query = QSqlQuery(self.db)
        query.exec("SELECT id, role_name, description FROM krd.user_roles ORDER BY role_name")
        
        roles = []
        while query.next():
            role = {
                'id': query.value(0),
                'name': query.value(1),
                'description': query.value(2)
            }
            roles.append(role)
        
        return roles
    
    def register_user(self, username, password, full_name="", email="", role_id=None):
        """
        Регистрация нового пользователя
        Если role_id не указан, используется роль по умолчанию (обычный пользователь)
        """
        # Если role_id не указан, получаем ID роли 'user' по умолчанию
        if role_id is None:
            role_id = self._get_default_role_id()
        
        # Проверяем, существует ли пользователь
        query = QSqlQuery(self.db)
        query.prepare("SELECT id FROM krd.users WHERE username = ?")
        query.addBindValue(username)
        query.exec()
        
        if query.next():
            raise Exception("Пользователь с таким именем уже существует")
        
        # Проверяем, существует ли указанная роль
        query.prepare("SELECT id FROM krd.user_roles WHERE id = ?")
        query.addBindValue(role_id)
        query.exec()
        
        if not query.next():
            raise Exception(f"Роль с ID {role_id} не найдена")
        
        # Хешируем пароль
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Сохраняем пользователя
        query.prepare("""
            INSERT INTO krd.users (username, password_hash, role_id, full_name, email)
            VALUES (?, ?, ?, ?, ?)
        """)
        query.addBindValue(username)
        query.addBindValue(hashed_password.decode('utf-8'))
        query.addBindValue(role_id)
        query.addBindValue(full_name)
        query.addBindValue(email)
        
        if not query.exec():
            raise Exception(f"Ошибка регистрации пользователя: {query.lastError().text()}")
    
    def _get_default_role_id(self):
        """
        Получение ID роли по умолчанию (обычный пользователь)
        """
        query = QSqlQuery(self.db)
        query.prepare("SELECT id FROM krd.user_roles WHERE role_name = ?")
        query.addBindValue("user")
        query.exec()
        
        if query.next():
            return query.value(0)
        else:
            # Если роль 'user' не найдена, возвращаем первую доступную роль
            query.exec("SELECT id FROM krd.user_roles LIMIT 1")
            if query.next():
                return query.value(0)
            else:
                raise Exception("Нет доступных ролей для назначения")
    
    def authenticate_user(self, username, password):
        """
        Аутентификация пользователя
        Возвращает информацию о пользователе, если аутентификация успешна
        """
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT u.id, u.username, u.full_name, u.email, ur.role_name, u.is_active, u.password_hash
            FROM krd.users u
            JOIN krd.user_roles ur ON u.role_id = ur.id
            WHERE u.username = ? AND u.is_active = TRUE
        """)
        query.addBindValue(username)
        query.exec()
        
        if not query.next():
            return None  # Пользователь не найден или неактивен
        
        # Получаем сохраненный хеш пароля
        stored_hash = query.value(6)  # password_hash
        user_id = query.value(0)
        user_info = {
            'id': user_id,
            'username': query.value(1),
            'full_name': query.value(2),
            'email': query.value(3),
            'role': query.value(4),
            'is_active': query.value(5)
        }
        
        # Проверяем формат хеша и сверяем пароль
        try:
            if self._verify_password(password, stored_hash):
                # Создаем сессию
                self._create_user_session(user_id)
                # Обновляем время последнего входа
                self._update_last_login(user_id)
                return user_info
        except Exception as e:
            logging.error(f"Ошибка при проверке пароля: {str(e)}")
            return None
        
        return None
    
    def _verify_password(self, password, stored_hash):
        """
        Проверка пароля с обработкой возможных ошибок
        """
        try:
            # Убедимся, что stored_hash - это байтовая строка
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            
            # Проверяем пароль
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
        except ValueError as e:
            # Ошибка может возникнуть, если хеш в неправильном формате
            logging.error(f"Ошибка проверки пароля: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Неизвестная ошибка при проверке пароля: {str(e)}")
            return False
    
    def _create_user_session(self, user_id):
        """
        Создание новой сессии для пользователя
        """
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.user_sessions (user_id)
            VALUES (?)
        """)
        query.addBindValue(user_id)
        
        if not query.exec():
            raise Exception(f"Ошибка создания сессии: {query.lastError().text()}")
    
    def _update_last_login(self, user_id):
        """
        Обновление времени последнего входа
        """
        query = QSqlQuery(self.db)
        query.prepare("UPDATE krd.users SET last_login = NOW() WHERE id = ?")
        query.addBindValue(user_id)
        query.exec()
    
    def logout_user(self, user_id):
        """
        Завершение сессии пользователя
        """
        query = QSqlQuery(self.db)
        query.prepare("""
            UPDATE krd.user_sessions 
            SET logout_time = NOW(), is_active = FALSE 
            WHERE user_id = ? AND is_active = TRUE
            ORDER BY login_time DESC
            LIMIT 1
        """)
        query.addBindValue(user_id)
        query.exec()
    
    def get_user_login_history(self, user_id, limit=10):
        """
        Получение истории входов пользователя
        """
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT login_time, logout_time
            FROM krd.user_sessions
            WHERE user_id = ?
            ORDER BY login_time DESC
            LIMIT ?
        """)
        query.addBindValue(user_id)
        query.addBindValue(limit)
        query.exec()
        
        history = []
        while query.next():
            history.append({
                'login_time': query.value(0),
                'logout_time': query.value(1)
            })
        
        return history
    
    def change_password(self, username, old_password, new_password):
        """
        Смена пароля пользователя
        """
        # Сначала проверяем текущий пароль
        user_info = self.authenticate_user(username, old_password)
        if not user_info:
            raise Exception("Неверный текущий пароль")
        
        # Хешируем новый пароль
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Обновляем пароль
        query = QSqlQuery(self.db)
        query.prepare("UPDATE krd.users SET password_hash = ? WHERE username = ?")
        query.addBindValue(hashed_new_password.decode('utf-8'))
        query.addBindValue(username)
        
        if not query.exec():
            raise Exception(f"Ошибка смены пароля: {query.lastError().text()}")
    
    def get_user_by_id(self, user_id):
        """
        Получение информации о пользователе по ID
        """
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT u.id, u.username, u.full_name, u.email, ur.role_name, u.is_active, u.created_at, u.last_login
            FROM krd.users u
            JOIN krd.user_roles ur ON u.role_id = ur.id
            WHERE u.id = ?
        """)
        query.addBindValue(user_id)
        query.exec()
        
        if query.next():
            return {
                'id': query.value(0),
                'username': query.value(1),
                'full_name': query.value(2),
                'email': query.value(3),
                'role': query.value(4),
                'is_active': query.value(5),
                'created_at': query.value(6),
                'last_login': query.value(7)
            }
        
        return None