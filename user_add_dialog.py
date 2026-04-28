"""
Диалог добавления нового пользователя
"""

import bcrypt
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QComboBox, QLabel, QMessageBox,
    QGroupBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlQuery


class UserAddDialog(QDialog):
    """Диалог добавления нового пользователя"""
    
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.setWindowTitle("➕ Добавление нового пользователя")
        self.setMinimumSize(500, 600)
        self.setModal(True)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # === Заголовок ===
        title_label = QLabel("👤 Создание учётной записи пользователя")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # === Основная информация ===
        info_group = QGroupBox("📋 Основная информация")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(10)
        
        # Имя пользователя
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин для входа в систему")
        self.username_input.setToolTip("Только латинские буквы, цифры и символы _-")
        info_layout.addRow("Имя пользователя *:", self.username_input)
        
        # Пароль
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Минимум 6 символов")
        self.password_input.setToolTip("Пароль должен содержать минимум 6 символов")
        info_layout.addRow("Пароль *:", self.password_input)
        
        # Подтверждение пароля
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input.setPlaceholderText("Повторите пароль")
        info_layout.addRow("Подтверждение пароля *:", self.password_confirm_input)
        
        # ФИО
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Иванов Иван Иванович")
        info_layout.addRow("ФИО *:", self.full_name_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
        self.email_input.setToolTip("Введите корректный email адрес")
        info_layout.addRow("Email:", self.email_input)
        
        layout.addWidget(info_group)
        
        # === Роль и статус ===
        role_group = QGroupBox("🔐 Права доступа")
        role_layout = QFormLayout(role_group)
        role_layout.setSpacing(10)
        
        # Выбор роли
        self.role_combo = QComboBox()
        self.role_combo.setMinimumWidth(250)
        self.load_roles()
        role_layout.addRow("Роль *:", self.role_combo)
        
        # Статус
        self.status_combo = QComboBox()
        self.status_combo.addItem("✓ Активен", True)
        self.status_combo.addItem("✕ Заблокирован", False)
        role_layout.addRow("Статус учётной записи:", self.status_combo)
        
        layout.addWidget(role_group)
        
        # === Примечание ===
        note_label = QLabel("💡 Поля, отмеченные звёздочкой (*), обязательны для заполнения")
        note_label.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        layout.addWidget(note_label)
        
        # === Кнопки ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("➕ Добавить")
        button_box.button(QDialogButtonBox.StandardButton.Ok).setProperty("role", "info")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_roles(self):
        """Загрузка доступных ролей"""
        self.role_combo.clear()
        self.role_combo.addItem("— Выберите роль —", None)
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, role_name, description FROM krd.user_roles ORDER BY role_name")
        
        while query.next():
            role_id = query.value(0)
            role_name = query.value(1)
            description = query.value(2)
            self.role_combo.addItem(f"{role_name} ({description})", role_id)
    
    def validate_username(self, username):
        """Проверка имени пользователя"""
        if len(username) < 3:
            return False, "Имя пользователя должно содержать минимум 3 символа"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Имя пользователя может содержать только латинские буквы, цифры, _ и -"
        
        return True, ""
    
    def validate_password(self, password):
        """Проверка пароля"""
        if len(password) < 6:
            return False, "Пароль должен содержать минимум 6 символов"
        
        return True, ""
    
    def validate_email(self, email):
        """Проверка email"""
        if not email:
            return True, ""  # Email не обязателен
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Введите корректный email адрес"
        
        return True, ""
    
    def on_accept(self):
        """Обработка нажатия OK"""
        # Сбор данных
        username = self.username_input.text().strip()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        role_id = self.role_combo.currentData()
        is_active = self.status_combo.currentData()
        
        # Валидация
        errors = []
        
        if not username:
            errors.append("Введите имя пользователя")
        else:
            valid, msg = self.validate_username(username)
            if not valid:
                errors.append(msg)
        
        if not password:
            errors.append("Введите пароль")
        else:
            valid, msg = self.validate_password(password)
            if not valid:
                errors.append(msg)
        
        if password != password_confirm:
            errors.append("Пароли не совпадают")
        
        if not full_name:
            errors.append("Введите ФИО")
        
        valid, msg = self.validate_email(email)
        if not valid:
            errors.append(msg)
        
        if role_id is None:
            errors.append("Выберите роль")
        
        if errors:
            QMessageBox.critical(self, "Ошибка валидации", "\n".join(errors))
            return
        
        # Проверка на дубликат username
        check_query = QSqlQuery(self.db)
        check_query.prepare("SELECT id FROM krd.users WHERE username = ? AND is_deleted = FALSE")
        check_query.addBindValue(username)
        check_query.exec()
        
        if check_query.next():
            QMessageBox.critical(self, "Ошибка", "Пользователь с таким именем уже существует!")
            return
        
        try:
            # Хеширование пароля
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Вставка в БД
            insert_query = QSqlQuery(self.db)
            insert_query.prepare("""
                INSERT INTO krd.users 
                (username, password_hash, full_name, email, role_id, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """)
            insert_query.addBindValue(username)
            insert_query.addBindValue(hashed_password.decode('utf-8'))
            insert_query.addBindValue(full_name)
            insert_query.addBindValue(email)
            insert_query.addBindValue(role_id)
            insert_query.addBindValue(is_active)
            
            if not insert_query.exec():
                raise Exception(f"Ошибка БД: {insert_query.lastError().text()}")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении пользователя:\n{str(e)}")