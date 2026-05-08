# run_app.py
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from config_manager import ConfigManager
from db_connector import DatabaseConnector 
from login_window import LoginWindow
from main_window import MainWindow
from setup_dialog import SetupDialog # Импорт вашего диалога настройки

def main():
    app = QApplication(sys.argv)
    config_manager = ConfigManager()

    # 1. Пытаемся загрузить существующую конфигурацию
    db_config = config_manager.load_config()

    # 2. Если настроек нет — показываем окно настройки
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
            sys.exit(0) # Пользователь отменил

    # 3. Пытаемся подключиться
    connector = DatabaseConnector(
        host=db_config['host'],
        port=db_config['port'],
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password'],
        ssl_mode="require"
    )

    success, msg = connector.connect()

    # 4. ЕСЛИ ПОДКЛЮЧЕНИЕ НЕ УДАЛОСЬ (Например, сменился пароль)
    if not success:
        # Спрашиваем пользователя, хочет ли он обновить настройки
        reply = QMessageBox.question(
            None,
            "Ошибка подключения",
            f"Не удалось подключиться к базе данных.\n\n{msg}\n\n"
            "Возможно, изменился пароль или настройки сервера.\n"
            "Хотите ввести новые данные прямо сейчас?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Показываем окно настройки снова (предварительно заполнив старые данные, если есть)
            dialog = SetupDialog()
            # (Опционально) Можно предзаполнить поля старыми данными из db_config
            # dialog.host_input.setText(db_config['host']) ...
            
            if dialog.exec():
                # Сохраняем НОВЫЕ данные (перезаписываем db_config.enc)
                config_manager.save_config(
                    dialog.host_input.text(),
                    dialog.port_input.text(),
                    dialog.db_input.text(),
                    dialog.user_input.text(),
                    dialog.pass_input.text()
                )
                
                # Перезапускаем приложение с новыми настройками
                # Самый надежный способ — просто вызвать sys.exit и пользователь запустит заново,
                # либо можно попробовать переподключиться здесь.
                QMessageBox.information(None, "Успех", "Настройки обновлены. Перезапустите программу.")
                sys.exit(0)
            else:
                sys.exit(1) # Пользователь отказался менять пароль
        else:
            sys.exit(1) # Пользователь не захотел менять настройки

    # 5. Если подключение успешно — запускаем приложение
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