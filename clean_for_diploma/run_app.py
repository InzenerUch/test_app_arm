import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from config_manager import ConfigManager
from db_connector import DatabaseConnector
from login_window import LoginWindow
from main_window import MainWindow
from setup_dialog import SetupDialog
def main():
    app = QApplication(sys.argv)
    config_manager = ConfigManager()
    db_config = config_manager.load_config()
    if not db_config:
        dialog = SetupDialog()
        if dialog.exec():
            config_manager.save_config(
                dialog.host_input.text(),
                dialog.port_input.text(),
                dialog.db_input.text(),
                dialog.user_input.text(),
                dialog.pass_input.text()
            )
            db_config = config_manager.load_config()
        else:
            sys.exit(0)
    connector = DatabaseConnector(
        host=db_config['host'],
        port=db_config['port'],
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password'],
        ssl_mode="require"
    )
    success, msg = connector.connect()
    if not success:
        reply = QMessageBox.question(
            None,
            "Ошибка подключения",
            f"Не удалось подключиться к базе данных.\n\n{msg}\n\n"
            "Возможно, изменился пароль или настройки сервера.\n"
            "Хотите ввести новые данные прямо сейчас?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            dialog = SetupDialog()
            if dialog.exec():
                config_manager.save_config(
                    dialog.host_input.text(),
                    dialog.port_input.text(),
                    dialog.db_input.text(),
                    dialog.user_input.text(),
                    dialog.pass_input.text()
                )
                QMessageBox.information(None, "Успех", "Настройки обновлены. Перезапустите программу.")
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            sys.exit(1)
    db = connector.get_connection()
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