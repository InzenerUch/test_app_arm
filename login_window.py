"""
Окно авторизации
Отвечает за UI, обработку сигналов и установку session-параметров БД
"""
import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

from authorization import SimpleAuthManager

class LoginWindow(QDialog):
    """Окно входа в систему"""
    login_successful = pyqtSignal(dict)

    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.auth_manager = SimpleAuthManager(self.db)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Авторизация")
        self.setFixedSize(400, 260)
        self.setModal(True)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_btn = QPushButton("Войти")
        login_btn.setProperty("role", "primary")
        login_btn.clicked.connect(self.attempt_login)

        form_layout.addRow("Имя пользователя:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)
        form_layout.addRow(login_btn)

        settings_btn = QPushButton("⚙️ Настройки подключения")
        settings_btn.setProperty("role", "normal")
        settings_btn.clicked.connect(self.open_db_settings)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(settings_btn)
        self.setLayout(main_layout)
        self.username_input.setFocus()

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        try:
            user_info = self.auth_manager.authenticate_user(username, password)
            if user_info:
                # 🔥 Устанавливаем application_name для отслеживания в pg_stat_activity
                safe_username = username.replace("'", "''")
                QSqlQuery(self.db).exec(f"SET application_name = '{safe_username}'")

                QMessageBox.information(self, "Успех", f"Добро пожаловать, {user_info['full_name']}!")
                self.login_successful.emit(user_info)
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка авторизации:\n{str(e)}")

    def open_db_settings(self):
        from setup_dialog import SetupDialog
        dialog = SetupDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Настройки", "Настройки сохранены. Перезапустите приложение.")


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     db = QSqlDatabase.addDatabase("QPSQL")
#     db.setHostName("localhost")
#     db.setDatabaseName("krd_system")
#     db.setUserName("arm_user")
#     db.setPassword("ArmUserSecurePass2026!")
    
#     if not db.open():
#         QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к БД:\n{db.lastError().text()}")
#         sys.exit(1)

#     win = LoginWindow(db)
#     win.login_successful.connect(lambda info: print(f"✅ Вход: {info['username']} ({info['role']})"))
#     win.show()
#     sys.exit(app.exec())