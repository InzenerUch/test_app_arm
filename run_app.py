import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from config_manager import ConfigManager
from db_connector import DatabaseConnector # Ваш коннектор
from login_window import LoginWindow
from main_window import MainWindow
# Импорт вашего диалога настройки
from setup_dialog import SetupDialog 

def main():
    app = QApplication(sys.argv)
    config_manager = ConfigManager()
    
    # 1. Проверяем, есть ли настройки
    db_config = config_manager.load_config()
    
    if not db_config:
        # Настроек нет, открываем окно настройки
        dialog = SetupDialog()
        if dialog.exec():
            # Пользователь нажал "Сохранить"
            config_manager.save_config(
                dialog.host_input.text(),
                dialog.port_input.text(),
                dialog.db_input.text(),
                dialog.user_input.text(),
                dialog.pass_input.text()
            )
            db_config = config_manager.load_config()
        else:
            sys.exit(0) # Пользователь отменил

    # 2. Подключаемся к БД
    connector = DatabaseConnector(
        host=db_config['host'],
        port=db_config['port'],
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password'],
        ssl_mode="require" # Или prefer
    )
    
    success, msg = connector.connect()
    if not success:
        # Если пароль изменили или сервер недоступен
        QMessageBox.critical(None, "Ошибка БД", msg)
        # Можно предложить открыть SetupDialog заново
        sys.exit(1)

    db = connector.get_connection()

    # 3. Запускаем авторизацию пользователя
    login_window = LoginWindow(db)
    main_window = None

    def open_main_window(user_info):
        nonlocal main_window
        from theme_manager import ThemeManager
        user_id = user_info.get('id')
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