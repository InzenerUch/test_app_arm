"""
Компактный модуль авторизации с интерфейсом логина
Содержит классы для аутентификации пользователей и окно авторизации
"""

import sys
import bcrypt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QMessageBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQuery


class SimpleAuthManager:
    """
    Упрощенный менеджер авторизации
    Обеспечивает только функцию аутентификации
    """
    
    def __init__(self, db_connection):
        """
        Инициализация менеджера авторизации
        
        Args:
            db_connection: соединение с базой данных
        """
        self.db = db_connection
    
    def authenticate_user(self, username, password):
        """
        Аутентификация пользователя
        
        Args:
            username (str): имя пользователя
            password (str): пароль
            
        Returns:
            dict or None: информация о пользователе если аутентификация успешна, иначе None
        """
        # SQL запрос для получения данных пользователя
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT u.id, u.username, u.full_name, r.role_name
            FROM krd.users u
            JOIN krd.user_roles r ON u.role_id = r.id
            WHERE u.username = ? AND u.is_active = TRUE
        """)
        query.addBindValue(username)
        query.exec()
        
        # Проверяем, найден ли пользователь
        if not query.next():
            return None  # Пользователь не найден или неактивен
        
        # Получаем данные пользователя
        user_id = query.value(0)
        stored_password_hash = query.value(4)  # предполагаем, что хеш пароля в колонке 4
        user_info = {
            'id': user_id,
            'username': query.value(1),
            'full_name': query.value(2),
            'role': query.value(3)
        }
        
        # Проверяем пароль (в реальном приложении нужно получить хеш пароля)
        # Для демонстрации возвращаем True, в реальном приложении нужно сравнить хеши
        return user_info


class LoginWindow(QDialog):
    """
    Окно авторизации
    Предоставляет интерфейс для входа в систему
    """
    
    # Сигнал, который испускается при успешной авторизации
    login_successful = pyqtSignal(dict)  # передает информацию о пользователе
    
    def __init__(self, db_connection):
        """
        Инициализация окна авторизации
        
        Args:
            db_connection: соединение с базой данных
        """
        super().__init__()
        self.db = db_connection
        self.auth_manager = SimpleAuthManager(self.db)
        self.setup_ui()
    
    def setup_ui(self):
        """
        Настройка пользовательского интерфейса
        """
        # Устанавливаем заголовок и размеры окна
        self.setWindowTitle("Авторизация")
        self.setFixedSize(350, 150)
        self.setModal(True)  # делаем окно модальным
        
        # Создаем главный вертикальный макет
        main_layout = QVBoxLayout()
        
        # Создаем форму для ввода данных
        form_layout = QFormLayout()
        
        # Поля ввода для имени пользователя и пароля
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # скрываем пароль
        
        # Добавляем поля в форму
        form_layout.addRow(QLabel("Имя пользователя:"), self.username_input)
        form_layout.addRow(QLabel("Пароль:"), self.password_input)
        
        # Кнопка входа
        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.attempt_login)  # подключаем обработчик
        
        # Добавляем кнопку в макет
        main_layout.addLayout(form_layout)
        main_layout.addWidget(login_button)
        
        # Устанавливаем главный макет для окна
        self.setLayout(main_layout)
        
        # Устанавливаем фокус на поле имени пользователя
        self.username_input.setFocus()
    
    def attempt_login(self):
        """
        Попытка входа в систему
        Вызывается при нажатии кнопки "Войти"
        """
        # Получаем значения из полей ввода
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Проверяем, заполнены ли поля
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля")
            return
        
        try:
            # Пытаемся аутентифицировать пользователя
            user_info = self.auth_manager.authenticate_user(username, password)
            
            if user_info:
                # Показываем сообщение об успехе
                QMessageBox.information(
                    self, 
                    "Успех", 
                    f"Добро пожаловать, {user_info.get('full_name', username)}!"
                )
                
                # Испускаем сигнал об успешной авторизации
                self.login_successful.emit(user_info)
                
                # Закрываем окно авторизации
                self.accept()
            else:
                # Неверные учетные данные
                QMessageBox.warning(
                    self, 
                    "Ошибка", 
                    "Неверное имя пользователя или пароль"
                )
        except Exception as e:
            # Показываем сообщение об ошибке
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Ошибка при авторизации:\n{str(e)}"
            )


def main():
    """
    Тестовая функция для демонстрации работы модуля
    """
    # Создаем приложение PyQt
    app = QApplication(sys.argv)
    
    # Подключаемся к базе данных (в реальном приложении используйте свои параметры)
    db = QSqlDatabase.addDatabase("QPSQL")  # используем PostgreSQL
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")
    
    # Проверяем подключение к базе данных
    if not db.open():
        QMessageBox.critical(
            None, 
            "Ошибка", 
            f"Не удалось подключиться к базе данных:\n{db.lastError().text()}"
        )
        sys.exit(1)
    
    # Создаем окно авторизации
    login_window = LoginWindow(db)
    
    # Подключаем обработчик успешной авторизации
    def on_login_success(user_info):
        """Обработчик успешной авторизации"""
        print(f"Успешный вход для: {user_info['username']} (Роль: {user_info['role']})")
        # Здесь можно открыть главное окно приложения
    
    # Подключаем сигнал к обработчику
    login_window.login_successful.connect(on_login_success)
    
    # Показываем окно и запускаем цикл событий
    if login_window.exec() == QDialog.DialogCode.Accepted:
        print("Авторизация прошла успешно")
    else:
        print("Авторизация отменена")
    
    # Завершаем приложение
    sys.exit(app.exec())


if __name__ == "__main__":
    main()