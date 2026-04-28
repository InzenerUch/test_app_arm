"""
Диалог редактирования данных пользователя
"""

import bcrypt
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QComboBox, QLabel, QMessageBox,
    QGroupBox, QDialogButtonBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlQuery


class UserEditDialog(QDialog):
    """Диалог редактирования пользователя"""
    
    def __init__(self, db_connection, user_id, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.user_id = user_id
        self.setWindowTitle("✏️ Редактирование пользователя")
        self.setMinimumSize(500, 650)
        self.setModal(True)
        
        self.original_username = ""
        
        self.init_ui()
        self.load_user_data()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # === Заголовок ===
        title_label = QLabel("👤 Редактирование учётной записи")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # === Основная информация ===
        info_group = QGroupBox("📋 Основная информация")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(10)
        
        # ID (только для просмотра)
        self.id_label = QLabel("")
        self.id_label.setStyleSheet("QLabel { color: #666; }")
        info_layout.addRow("ID пользователя:", self.id_label)
        
        # Имя пользователя
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин для входа в систему")
        info_layout.addRow("Имя пользователя *:", self.username_input)
        
        # Смена пароля
        password_group = QGroupBox("🔑 Смена пароля")
        password_layout = QFormLayout(password_group)
        
        self.change_password_checkbox = QCheckBox("Изменить пароль")
        self.change_password_checkbox.stateChanged.connect(self.on_password_change_toggled)
        password_layout.addRow(self.change_password_checkbox)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setEnabled(False)
        self.password_input.setPlaceholderText("Новый пароль")
        password_layout.addRow("Новый пароль:", self.password_input)
        
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input.setEnabled(False)
        self.password_confirm_input.setPlaceholderText("Подтвердите пароль")
        password_layout.addRow("Подтверждение:", self.password_confirm_input)
        
        info_layout.addRow(password_group)
        
        # ФИО
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Иванов Иван Иванович")
        info_layout.addRow("ФИО *:", self.full_name_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
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
        
        # Дата создания
        self.created_at_label = QLabel("")
        role_layout.addRow("Дата создания:", self.created_at_label)
        
        # Последний вход
        self.last_login_label = QLabel("")
        role_layout.addRow("Последний вход:", self.last_login_label)
        
        layout.addWidget(role_group)
        
        # === Кнопки ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("💾 Сохранить")
        button_box.button(QDialogButtonBox.StandardButton.Ok).setProperty("role","save")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def on_password_change_toggled(self, state):
        """Обработка переключения смены пароля"""
        is_checked = state == Qt.CheckState.Checked
        self.password_input.setEnabled(is_checked)
        self.password_confirm_input.setEnabled(is_checked)
        
        if not is_checked:
            self.password_input.clear()
            self.password_confirm_input.clear()
    
    def load_roles(self):
        """Загрузка доступных ролей"""
        self.role_combo.clear()
        
        query = QSqlQuery(self.db)
        query.exec("SELECT id, role_name, description FROM krd.user_roles ORDER BY role_name")
        
        while query.next():
            role_id = query.value(0)
            role_name = query.value(1)
            description = query.value(2)
            self.role_combo.addItem(f"{role_name} ({description})", role_id)
    
    def load_user_data(self):
        """Загрузка данных пользователя"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                u.id,
                u.username,
                u.full_name,
                u.email,
                u.role_id,
                u.is_active,
                u.created_at,
                u.last_login
            FROM krd.users u
            WHERE u.id = ? AND u.is_deleted = FALSE
        """)
        query.addBindValue(self.user_id)
        
        if not query.exec():
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {query.lastError().text()}")
            self.reject()
            return
        
        if not query.next():
            QMessageBox.critical(self, "Ошибка", "Пользователь не найден")
            self.reject()
            return
        
        # Заполнение полей
        self.id_label.setText(str(query.value(0)))
        self.username_input.setText(query.value(1) or "")
        self.original_username = query.value(1) or ""
        self.full_name_input.setText(query.value(2) or "")
        self.email_input.setText(query.value(3) or "")
        
        # Выбор роли
        role_id = query.value(4)
        if role_id:
            index = self.role_combo.findData(role_id)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
        
        # Статус
        is_active = query.value(5)
        index = self.status_combo.findData(is_active)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        
        # Даты
        created_at = query.value(6)
        if created_at:
            self.created_at_label.setText(str(created_at))
        
        last_login = query.value(7)
        if last_login:
            self.last_login_label.setText(str(last_login))
        else:
            self.last_login_label.setText("Никогда")
    
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
            return True, ""
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Введите корректный email адрес"
        
        return True, ""
    
    def on_accept(self):
        """Обработка нажатия OK"""
        # Сбор данных
        username = self.username_input.text().strip()
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        role_id = self.role_combo.currentData()
        is_active = self.status_combo.currentData()
        change_password = self.change_password_checkbox.isChecked()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
        
        # Валидация
        errors = []
        
        if not username:
            errors.append("Введите имя пользователя")
        else:
            valid, msg = self.validate_username(username)
            if not valid:
                errors.append(msg)
        
        if not full_name:
            errors.append("Введите ФИО")
        
        valid, msg = self.validate_email(email)
        if not valid:
            errors.append(msg)
        
        if role_id is None:
            errors.append("Выберите роль")
        
        if change_password:
            if not password:
                errors.append("Введите новый пароль")
            else:
                valid, msg = self.validate_password(password)
                if not valid:
                    errors.append(msg)
            
            if password != password_confirm:
                errors.append("Пароли не совпадают")
        
        if errors:
            QMessageBox.critical(self, "Ошибка валидации", "\n".join(errors))
            return
        
        # Проверка на дубликат username (если изменили)
        if username != self.original_username:
            check_query = QSqlQuery(self.db)
            check_query.prepare("SELECT id FROM krd.users WHERE username = ? AND id != ? AND is_deleted = FALSE")
            check_query.addBindValue(username)
            check_query.addBindValue(self.user_id)
            check_query.exec()
            
            if check_query.next():
                QMessageBox.critical(self, "Ошибка", "Пользователь с таким именем уже существует!")
                return
        
        try:
            # Обновление данных
            if change_password:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                update_query = QSqlQuery(self.db)
                update_query.prepare("""
                    UPDATE krd.users 
                    SET username = ?,
                        password_hash = ?,
                        full_name = ?,
                        email = ?,
                        role_id = ?,
                        is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """)
                update_query.addBindValue(username)
                update_query.addBindValue(hashed_password.decode('utf-8'))
                update_query.addBindValue(full_name)
                update_query.addBindValue(email)
                update_query.addBindValue(role_id)
                update_query.addBindValue(is_active)
                update_query.addBindValue(self.user_id)
            else:
                update_query = QSqlQuery(self.db)
                update_query.prepare("""
                    UPDATE krd.users 
                    SET username = ?,
                        full_name = ?,
                        email = ?,
                        role_id = ?,
                        is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """)
                update_query.addBindValue(username)
                update_query.addBindValue(full_name)
                update_query.addBindValue(email)
                update_query.addBindValue(role_id)
                update_query.addBindValue(is_active)
                update_query.addBindValue(self.user_id)
            
            if not update_query.exec():
                raise Exception(f"Ошибка БД: {update_query.lastError().text()}")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении:\n{str(e)}")