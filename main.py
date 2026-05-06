"""
Основной файл запуска приложения
✅ ИСПРАВЛЕНО: Использование DatabaseConnector с SSL
"""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtSql import QSqlDatabase

# Импорт коннектора
from db_connector import DatabaseConnector
from login_window import LoginWindow
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # ✅ СОЗДАНИЕ КОННЕКТОРА С SSL
    # ssl_mode="require" заставит Qt использовать шифрованный канал.
    connector = DatabaseConnector(
        host="localhost",
        port=5432,
        dbname="krd_system",
        user="arm_user",
        password="ArmUserSecurePass2026!",
        ssl_mode="require"  # 🔒 Включено шифрование
    )
    
    # Попытка подключения
    success, msg = connector.connect()
    
    if not success:
        QMessageBox.critical(None, "Ошибка подключения к БД", msg)
        sys.exit(1)
        
    db = connector.get_connection()
    print(f"📡 [Network] Данные передаются через защищенный SSL-туннель.")
    
    # Создание и отображение окна авторизации
    login_window = LoginWindow(db)
    main_window = None
    
    def open_main_window(user_info):
        nonlocal main_window
        # Создаем главное окно с информацией о пользователе и передаем DB
        main_window = MainWindow(user_info, db)
        main_window.show()
        login_window.close()
        
    login_window.login_successful.connect(open_main_window)
    login_window.show()
    
    # Запускаем цикл событий
    sys.exit(app.exec())

if __name__ == "__main__":
    main()