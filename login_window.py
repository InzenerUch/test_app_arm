"""
Модуль для окна авторизации
Содержит класс LoginWindow для аутентификации пользователей
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtSql import QSqlDatabase

from authorization import SimpleAuthManager


class LoginWindow(QDialog):
    """
    Класс окна авторизации
    """
    # Сигнал, который испускается при успешной авторизации
    login_successful = pyqtSignal(dict)  # информация о пользователе

    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.auth_manager = SimpleAuthManager(self.db)
        self.init_ui()

    def init_ui(self):
        """
        Инициализация пользовательского интерфейса
        """
        self.setWindowTitle("Авторизация")
        self.setFixedSize(400, 200)
        self.setModal(True)

        # Создаем основной макет
        main_layout = QVBoxLayout()

        # Вкладка входа
        login_layout = self.create_login_form()
        main_layout.addLayout(login_layout)

        self.setLayout(main_layout)

    def create_login_form(self):
        """
        Создание формы для входа
        """
        layout = QFormLayout()

        # Поля ввода
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Чекбокс "Запомнить меня"
        self.remember_checkbox = QCheckBox("Запомнить меня")

        # Кнопка входа
        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.attempt_login)

        # Добавление виджетов в форму
        layout.addRow("Имя пользователя:", self.username_input)
        layout.addRow("Пароль:", self.password_input)
        layout.addRow(self.remember_checkbox)
        layout.addRow(login_button)

        return layout

    def attempt_login(self):
        """
        Попытка входа в систему
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля")
            return

        try:
            # Пытаемся аутентифицировать пользователя
            user_info = self.auth_manager.authenticate_user(username, password)

            if user_info:
                QMessageBox.information(self, "Успех", f"Добро пожаловать, {user_info['full_name']}!")

                # Испускаем сигнал об успешной авторизации
                self.login_successful.emit(user_info)

                # Закрываем окно авторизации
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверное имя пользователя или пароль")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при авторизации:\n{str(e)}")


def main():
    """
    Функция для тестирования окна авторизации
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

    # Создание окна авторизации
    login_window = LoginWindow(db)

    # Подключение сигнала успешной авторизации
    def on_login_success(user_info):
        print(f"Успешный вход для пользователя: {user_info['username']}")
        # Здесь можно открыть главное окно приложения

    login_window.login_successful.connect(on_login_success)

    # Показ окна
    if login_window.exec() == QDialog.DialogCode.Accepted:
        print("Авторизация прошла успешно")
    else:
        print("Авторизация отменена")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()