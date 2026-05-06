"""
Файл запуска приложения АРМ Сотрудника дознания
✅ ИСПРАВЛЕНО: Использование DatabaseConnector с SSL
"""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from db_connector import DatabaseConnector
from login_window import LoginWindow
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # ✅ Подключение через коннектор с SSL
    connector = DatabaseConnector(
        host="localhost",
        port=5432,
        dbname="krd_system",
        user="arm_user",
        password="ArmUserSecurePass2026!",
        ssl_mode="require"
    )
    
    success, msg = connector.connect()
    if not success:
        QMessageBox.critical(None, "Ошибка", msg)
        sys.exit(1)
        
    db = connector.get_connection()

    # Создание и отображение окна авторизации
    login_window = LoginWindow(db)
    main_window = None

    def open_main_window(user_info):
        nonlocal main_window
        from theme_manager import ThemeManager
        user_id = user_info.get('id')
        print(f"🔍 [DEBUG] user_id из user_info: {user_id}")
        tm = ThemeManager(db, user_id)
        tm.load_and_apply()
        main_window = MainWindow(user_info, db)
        main_window.theme_manager = tm
        main_window.show()
        login_window.close()

    login_window.login_successful.connect(open_main_window)
    login_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()