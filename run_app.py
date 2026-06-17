# run_app.py
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from config_manager import ConfigManager
from db_connector import DatabaseConnector
from login_window import LoginWindow
from main_window import MainWindow
from setup_dialog import SetupDialog
from logger import init_global_logging


def get_resource_path(relative_path):
    """Возвращает корректный путь к ресурсу: работает и при запуске .py, и в собранном .exe"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    init_global_logging()

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("АРМ Сотрудника дознания")

        # 🎨 === УСТАНОВКА ИКОНКИ ПРИЛОЖЕНИЯ ===
        icon_path = get_resource_path("assets/app_icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            print(f"✅ Иконка приложения установлена: {icon_path}")
        else:
            print(f"⚠️ Иконка не найдена по пути: {icon_path}")
        # ======================================

        config_manager = ConfigManager()
        db_config = config_manager.load_config()

        if not db_config:
            dialog = SetupDialog()
            if dialog.exec():
                # ✅ ВАЖНО: читаем поля ДО того, как dialog будет удалён
                host = dialog.host_input.text()
                port = dialog.port_input.text()
                dbname = dialog.db_input.text()
                user = dialog.user_input.text()
                password = dialog.pass_input.text()
                config_manager.save_config(host, port, dbname, user, password)
                db_config = config_manager.load_config()
            else:
                sys.exit(0)

        connector = DatabaseConnector(
            host=db_config['host'], port=db_config['port'],
            dbname=db_config['dbname'], user=db_config['user'],
            password=db_config['password'], ssl_mode="require"
        )

        success, msg = connector.connect()

        if not success:
            reply = QMessageBox.question(
                None, "Ошибка подключения",
                f"Не удалось подключиться к базе данных.\n{msg}\n\nХотите ввести новые данные?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                dialog = SetupDialog()
                if dialog.exec():
                    host = dialog.host_input.text()
                    port = dialog.port_input.text()
                    dbname = dialog.db_input.text()
                    user = dialog.user_input.text()
                    password = dialog.pass_input.text()
                    config_manager.save_config(host, port, dbname, user, password)
                    QMessageBox.information(None, "Успех", "Настройки обновлены. Перезапустите программу.")
                sys.exit(0)
            else:
                sys.exit(1)

        db = connector.get_connection()
        login_window = LoginWindow(db)

        #  === ИКОНКА ДЛЯ ОКНА АВТОРИЗАЦИИ ===
        if os.path.exists(icon_path):
            login_window.setWindowIcon(QIcon(icon_path))
        # =======================================

        main_window = None

        def open_main_window(user_info):
            nonlocal main_window
            try:
                from theme_manager import ThemeManager
                user_id = user_info.get('id')
                tm = ThemeManager(db, user_id)
                tm.load_and_apply()

                main_window = MainWindow(user_info, db)
                main_window.theme_manager = tm

                #  === ИКОНКА ДЛЯ ГЛАВНОГО ОКНА ===
                if os.path.exists(icon_path):
                    main_window.setWindowIcon(QIcon(icon_path))
                # ===================================

                main_window.show()
                login_window.close()
            except Exception as e:
                QMessageBox.critical(None, "Критическая ошибка",
                    f"Не удалось открыть главное окно:\n{e}\n\nПодробности в файле app_errors.log")
                sys.exit(1)

        login_window.login_successful.connect(open_main_window)
        login_window.show()

        sys.exit(app.exec())

    except Exception as e:
        logging.getLogger("KRD_Application").critical(
            "ФАТАЛЬНАЯ ОШИБКА на этапе запуска приложения", exc_info=True)
        QMessageBox.critical(None, "Фатальная ошибка",
            f"Приложение не может быть запущено:\n\n{e}\n\nПодробности записаны в файл app_errors.log")
        sys.exit(1)


if __name__ == "__main__":
    main()