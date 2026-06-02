import sys
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QMessageBox
class DatabaseConnector:
    def __init__(self, host="localhost", port=5432, dbname="krd_system",
                 user="arm_user", password="", ssl_mode="require"):
        self.host = host
        self.port = int(port) if port is not None else 5432
        self.dbname = dbname
        self.user = user
        self.password = password
        self.ssl_mode = ssl_mode
        self.db = None
    def connect(self):
        try:
            self.db = QSqlDatabase.addDatabase("QPSQL")
            self.db.setHostName(self.host)
            self.db.setPort(int(self.port))
            self.db.setDatabaseName(self.dbname)
            self.db.setUserName(self.user)
            self.db.setPassword(self.password)
            if self.ssl_mode:
                print(f"🔒 [DB] Включаю SSL-шифрование (sslmode={self.ssl_mode})...")
                self.db.setConnectOptions(f"sslmode={self.ssl_mode}")
            if not self.db.open():
                error_text = self.db.lastError().text()
                if "SSL" in error_text or "sslmode" in error_text.lower():
                    error_text += "\n💡 Возможно, на сервере PostgreSQL не настроен SSL."
                return False, f"Ошибка подключения: {error_text}"
            query = QSqlQuery(self.db)
            if not query.exec("SELECT 1"):
                return False, "База данных не отвечает на запросы."
            print("✅ [DB] Подключение к базе данных установлено успешно.")
            return True, "Подключено"
        except ValueError as e:
            return False, f"Ошибка типа данных (порт): {str(e)}\n💡 Убедитесь, что порт указан как число (например, 5432)"
        except Exception as e:
            return False, f"Критическая ошибка: {str(e)}"
    def get_connection(self):
        return self.db
    def close(self):
        if self.db and self.db.isOpen():
            self.db.close()
            print("🔌 [DB] Подключение закрыто.")