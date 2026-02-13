"""
Тестовое главное окно для проверки
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtSql import QSqlDatabase

from main_window import MainWindow


def main():
    """
    Тестовая функция для проверки главного окна
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

    print("Подключение к базе данных успешно")

    # Тестовые данные пользователя
    user_info = {
        'id': 1,
        'username': 'admin',
        'full_name': 'Администратор системы',
        'role': 'admin'
    }

    print(f"Создание главного окна для пользователя: {user_info}")

    # Создание и показ главного окна
    main_window = MainWindow(user_info, db)
    print("Главное окно создано")
    
    main_window.show()
    print("Главное окно показано")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()