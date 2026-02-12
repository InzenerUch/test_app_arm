"""
Модуль для административной вкладки добавления пользователей
"""

import bcrypt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QMessageBox, QComboBox, QLabel
)
from PyQt6.QtSql import QSqlQuery


class AdminUserManagementTab(QWidget):
    """
    Административная вкладка для управления пользователями
    """
    
    def __init__(self, db_connection):
        """
        Инициализация административной вкладки
        
        Args:
            db_connection: соединение с базой данных
        """
        super().__init__()
        self.db = db_connection
        
        self.init_ui()
    
    def init_ui(self):
        """
        Инициализация пользовательского интерфейса
        """
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Добавление новых пользователей")
        title_font = self.font()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Форма для добавления пользователя
        form_layout = QFormLayout()
        
        # Поля ввода
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.full_name_input = QLineEdit()
        self.email_input = QLineEdit()
        
        # Комбобокс для выбора роли
        self.role_combo = QComboBox()
        self.load_roles()
        
        # Кнопка добавления
        add_user_button = QPushButton("Добавить пользователя")
        add_user_button.clicked.connect(self.add_user)
        
        # Добавляем поля в форму
        form_layout.addRow("Имя пользователя:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)
        form_layout.addRow("ФИО:", self.full_name_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Роль:", self.role_combo)
        form_layout.addRow(add_user_button)
        
        layout.addLayout(form_layout)
        self.setLayout(layout)
    
    def load_roles(self):
        """
        Загрузка доступных ролей из базы данных
        """
        query = QSqlQuery(self.db)
        query.exec("SELECT id, role_name, description FROM krd.user_roles ORDER BY role_name")
        
        while query.next():
            role_id = query.value(0)
            role_name = query.value(1)
            description = query.value(2)
            self.role_combo.addItem(f"{role_name} ({description})", role_id)
    
    def add_user(self):
        """
        Добавление нового пользователя
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        role_id = self.role_combo.currentData()
        
        # Проверка валидности данных
        if not username or not password or not full_name:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все обязательные поля")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Ошибка", "Пароль должен содержать не менее 6 символов")
            return
        
        if role_id is None:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите роль для пользователя")
            return
        
        try:
            # Хешируем пароль
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Проверяем, существует ли пользователь с таким именем
            check_query = QSqlQuery(self.db)
            check_query.prepare("SELECT id FROM krd.users WHERE username = ?")
            check_query.addBindValue(username)
            check_query.exec()
            
            if check_query.next():
                raise Exception("Пользователь с таким именем уже существует")
            
            # Добавляем нового пользователя
            insert_query = QSqlQuery(self.db)
            insert_query.prepare("""
                INSERT INTO krd.users (username, password_hash, full_name, email, role_id)
                VALUES (?, ?, ?, ?, ?)
            """)
            insert_query.addBindValue(username)
            insert_query.addBindValue(hashed_password.decode('utf-8'))
            insert_query.addBindValue(full_name)
            insert_query.addBindValue(email)
            insert_query.addBindValue(role_id)
            
            if not insert_query.exec():
                raise Exception(f"Ошибка при добавлении пользователя: {insert_query.lastError().text()}")
            
            QMessageBox.information(self, "Успех", "Пользователь успешно добавлен!")
            
            # Очищаем поля ввода
            self.username_input.clear()
            self.password_input.clear()
            self.full_name_input.clear()
            self.email_input.clear()
            self.role_combo.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении пользователя:\n{str(e)}")