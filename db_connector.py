"""
Модуль для безопасного подключения к PostgreSQL с поддержкой SSL
"""
import sys
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QMessageBox

class DatabaseConnector:
    """
    Класс для управления подключением к базе данных.
    По умолчанию включает SSL-шифрование трафика.
    """
    def __init__(self, host="localhost", port=5432, dbname="krd_system", 
                 user="arm_user", password="", ssl_mode="require"):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.ssl_mode = ssl_mode
        self.db = None

    def connect(self):
        """
        Устанавливает подключение к БД.
        Returns:
            tuple: (bool, str) - (Успех, Сообщение)
        """
        try:
            self.db = QSqlDatabase.addDatabase("QPSQL")
            self.db.setHostName(self.host)
            self.db.setPort(self.port)
            self.db.setDatabaseName(self.dbname)
            self.db.setUserName(self.user)
            self.db.setPassword(self.password)
            
            # ✅ НАСТРОЙКА SSL ШИФРОВАНИЯ
            # require: Обязательно использовать SSL. Если сервер не поддерживает - ошибка.
            # verify-full: Обязательно SSL + проверка сертификата сервера (требует настройки сертификатов).
            if self.ssl_mode:
                print(f"🔒 [DB] Включаю SSL-шифрование (sslmode={self.ssl_mode})...")
                self.db.setConnectOptions(f"sslmode={self.ssl_mode}")
            
            if not self.db.open():
                error_text = self.db.lastError().text()
                # Специальная обработка ошибок SSL
                if "SSL" in error_text or "sslmode" in error_text.lower():
                    error_text += "\n\n💡 Возможно, на сервере PostgreSQL не настроен SSL."
                return False, f"Ошибка подключения: {error_text}"
            
            # ✅ ТЕСТОВОЕ ЗАПИСЬ ДЛЯ ПРОВЕРКИ СОЕДИНЕНИЯ
            query = QSqlQuery(self.db)
            if not query.exec("SELECT 1"):
                return False, "База данных не отвечает на запросы."
                
            print("✅ [DB] Подключение к базе данных установлено успешно.")
            return True, "Подключено"
            
        except Exception as e:
            return False, f"Критическая ошибка: {str(e)}"

    def get_connection(self):
        """Возвращает объект подключения QSqlDatabase"""
        return self.db

    def close(self):
        """Закрывает подключение"""
        if self.db and self.db.isOpen():
            self.db.close()
            print("🔌 [DB] Подключение закрыто.")