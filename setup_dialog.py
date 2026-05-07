# setup_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QLabel
from PyQt6.QtSql import QSqlDatabase

class SetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройка подключения к базе данных")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.host_input = QLineEdit("localhost")
        self.port_input = QLineEdit("5432")
        self.db_input = QLineEdit("krd_system")
        self.user_input = QLineEdit("arm_user")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("Хост:", self.host_input)
        form.addRow("Порт:", self.port_input)
        form.addRow("База данных:", self.db_input)
        form.addRow("Пользователь БД:", self.user_input)
        form.addRow("Пароль БД:", self.pass_input)
        
        layout.addLayout(form)
        
        self.btn_test = QPushButton("Проверить подключение")
        self.btn_save = QPushButton("Сохранить и войти")
        self.btn_save.setEnabled(False)
        
        self.btn_test.clicked.connect(self.test_connection)
        self.btn_save.clicked.connect(self.accept)
        
        layout.addWidget(self.btn_test)
        layout.addWidget(self.btn_save)
        self.setLayout(layout)

    def test_connection(self):
        db = QSqlDatabase.addDatabase("QPSQL", "test_conn")
        db.setHostName(self.host_input.text())
        db.setPort(int(self.port_input.text()))
        db.setDatabaseName(self.db_input.text())
        db.setUserName(self.user_input.text())
        db.setPassword(self.pass_input.text())
        
        if db.open():
            QMessageBox.information(self, "Успех", "Подключение успешно!")
            self.btn_save.setEnabled(True)
            db.close()
        else:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться: {db.lastError().text()}")