"""
Файл запуска приложения АРМ Сотрудника дознания
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtSql import QSqlDatabase

from login_window import LoginWindow
from main_window import MainWindow


def main():
    """
    Основная функция запуска приложения
    """
    app = QApplication(sys.argv)

    # Подключение к базе данных
    db = QSqlDatabase.addDatabase("QPSQL")
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")

    if not db.open():
        QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных:\n{db.lastError().text()}")
        sys.exit(1)

    # Создание и отображение окна авторизации
    login_window = LoginWindow(db)

    # Создаем переменную для хранения главного окна
    main_window = None

    # Подключение сигнала успешной авторизации к открытию главного окна
    def open_main_window(user_info):
        nonlocal main_window
        
        # ✅ ДОБАВЬТЕ ЭТИ СТРОКИ
        from theme_manager import ThemeManager
        user_id = user_info.get('id')
        print(f"🔍 [DEBUG] user_id из user_info: {user_id}")
        
        tm = ThemeManager(db, user_id)
        tm.load_and_apply()  # <-- ЭТОТ ВЫЗОВ ОБЯЗАТЕЛЕН!
        
        main_window = MainWindow(user_info, db)
        main_window.theme_manager = tm
        main_window.show()
        login_window.close()

    login_window.login_successful.connect(open_main_window)

    # Показываем окно авторизации
    login_window.show()

    # Запускаем цикл событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()