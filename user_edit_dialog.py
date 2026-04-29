"""
Диалог редактирования данных пользователя
✅ СООТВЕТСТВИЕ СХЕМЕ: krd.users (без updated_at, с is_deleted/deleted_at)
✅ PostgreSQL-совместимые именованные параметры :param
✅ Мягкое удаление через is_deleted = TRUE
✅ Полная валидация и диагностика
"""
import bcrypt
import re
import traceback
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QComboBox, QLabel, QMessageBox,
    QGroupBox, QDialogButtonBox, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlQuery


class UserEditDialog(QDialog):
    """Диалог редактирования пользователя с полной диагностикой и корректной работой с PostgreSQL"""
    
    def __init__(self, db_connection, user_id: int, parent=None):
        print(f"\n🔍 [UserEditDialog] ИНИЦИАЛИЗАЦИЯ | user_id={user_id}")
        super().__init__(parent)
        self.db = db_connection
        self.user_id = user_id
        self.current_user_role: Optional[str] = None
        self.editing_user_role: Optional[str] = None
        
        self.setWindowTitle("✏️ Редактирование пользователя")
        self.setMinimumSize(500, 650)
        self.setModal(True)
        
        self.original_username = ""
        self.is_user_active = True
        self.status_buttons_visible = True
        
        self.init_ui()
        self.load_user_data()
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Внутренний логгер для отладки"""
        prefix = {
            "INFO": "📝", "DEBUG": "🔧", "WARN": "⚠️", 
            "ERROR": "❌", "SUCCESS": "✅", "SQL": "🗄️"
        }.get(level, "•")
        print(f"{prefix} [{level}] {message}")
    
    def init_ui(self) -> None:
        """Инициализация интерфейса"""
        self._log("init_ui(): Начало", "DEBUG")
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Заголовок
        title_label = QLabel("👤 Редактирование учётной записи")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # === Основная информация ===
        info_group = QGroupBox("📋 Основная информация")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(15, 15, 15, 15)
        
        self.id_label = QLabel("")
        self.id_label.setStyleSheet("QLabel { color: #666; padding: 4px; }")
        info_layout.addRow("ID пользователя:", self.id_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин для входа")
        self.username_input.setMinimumHeight(32)
        info_layout.addRow("Имя пользователя *:", self.username_input)
        
        # === Смена пароля ===
        password_group = QGroupBox("🔑 Смена пароля")
        password_layout = QFormLayout(password_group)
        password_layout.setSpacing(10)
        password_layout.setContentsMargins(10, 10, 10, 10)
        
        self.change_password_checkbox = QCheckBox("Изменить пароль")
        self.change_password_checkbox.stateChanged.connect(self.on_password_change_toggled)
        password_layout.addRow(self.change_password_checkbox)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setEnabled(False)
        self.password_input.setPlaceholderText("Новый пароль")
        self.password_input.setMinimumHeight(32)
        password_layout.addRow("Новый пароль:", self.password_input)
        
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm_input.setEnabled(False)
        self.password_confirm_input.setPlaceholderText("Подтвердите пароль")
        self.password_confirm_input.setMinimumHeight(32)
        password_layout.addRow("Подтверждение:", self.password_confirm_input)
        
        info_layout.addRow(password_group)
        
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Иванов Иван Иванович")
        self.full_name_input.setMinimumHeight(32)
        info_layout.addRow("ФИО *:", self.full_name_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
        self.email_input.setMinimumHeight(32)
        info_layout.addRow("Email:", self.email_input)
        
        layout.addWidget(info_group)
        
        # === Права доступа ===
        role_group = QGroupBox("🔐 Права доступа")
        role_layout = QFormLayout(role_group)
        role_layout.setSpacing(12)
        role_layout.setContentsMargins(15, 15, 15, 15)
        
        self.role_combo = QComboBox()
        self.role_combo.setMinimumWidth(280)
        self.role_combo.setMinimumHeight(32)
        self.load_roles()
        role_layout.addRow("Роль *:", self.role_combo)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel { padding: 8px; border-radius: 4px; font-weight: bold; background-color: #E8F5E9; color: #2E7D32; }
            QLabel[status="inactive"] { background-color: #FFEBEE; color: #C62828; }
        """)
        role_layout.addRow("Статус учётной записи:", self.status_label)
        
        self.created_at_label = QLabel("")
        self.created_at_label.setStyleSheet("QLabel { padding: 4px; }")
        role_layout.addRow("Дата создания:", self.created_at_label)
        
        self.last_login_label = QLabel("")
        self.last_login_label.setStyleSheet("QLabel { padding: 4px; }")
        role_layout.addRow("Последний вход:", self.last_login_label)
        
        layout.addWidget(role_group)
        
        # === Кнопки управления статусом (скрыты для админов) ===
        if self.editing_user_role != 'admin':
            self._create_status_buttons(layout)
        
        # Разделитель
        separator = QHBoxLayout()
        line = QLabel("────────────────────────────────────────")
        line.setStyleSheet("QLabel { color: #999; font-size: 16px; }")
        separator.addWidget(line)
        layout.addLayout(separator)
        
        # === Опасная зона ===
        delete_group = QGroupBox("🗑️ Опасная зона")
        delete_layout = QHBoxLayout(delete_group)
        delete_layout.setContentsMargins(10, 10, 10, 10)
        
        self.delete_btn = QPushButton("🗑️ Удалить пользователя")
        self.delete_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; font-weight: bold; "
            "padding: 12px; border-radius: 5px; min-height: 42px; font-size: 13px; } "
            "QPushButton:hover { background-color: #da190b; }"
        )
        self.delete_btn.clicked.connect(self.on_delete_user)
        delete_layout.addWidget(self.delete_btn)
        layout.addWidget(delete_group)
        
        # === Кнопки диалога ===
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("💾 Сохранить")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        self._log("init_ui(): Завершено", "SUCCESS")
    
    def _create_status_buttons(self, layout: QVBoxLayout) -> None:
        """Создание кнопок активации/деактивации пользователя"""
        status_buttons_group = QGroupBox("⚡ Управление статусом")
        status_buttons_layout = QHBoxLayout(status_buttons_group)
        status_buttons_layout.setSpacing(10)
        status_buttons_layout.setContentsMargins(10, 10, 10, 10)
        
        self.deactivate_btn = QPushButton("⏸️ Деактивировать")
        self.deactivate_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; font-weight: bold; "
            "padding: 10px; border-radius: 5px; min-height: 36px; } "
            "QPushButton:hover { background-color: #F57C00; } "
            "QPushButton:disabled { background-color: #cccccc; }"
        )
        self.deactivate_btn.clicked.connect(self.on_deactivate_user)
        status_buttons_layout.addWidget(self.deactivate_btn)
        
        self.activate_btn = QPushButton("✅ Активировать")
        self.activate_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; "
            "padding: 10px; border-radius: 5px; min-height: 36px; } "
            "QPushButton:hover { background-color: #45a049; } "
            "QPushButton:disabled { background-color: #cccccc; }"
        )
        self.activate_btn.clicked.connect(self.on_activate_user)
        status_buttons_layout.addWidget(self.activate_btn)
        
        layout.addWidget(status_buttons_group)
        self.status_buttons_visible = True
    
    def on_password_change_toggled(self, state: int) -> None:
        """Обработчик переключения чекбокса смены пароля"""
        is_checked = state == Qt.CheckState.Checked.value
        self.password_input.setEnabled(is_checked)
        self.password_confirm_input.setEnabled(is_checked)
        if not is_checked:
            self.password_input.clear()
            self.password_confirm_input.clear()
    
    def load_roles(self) -> None:
        """Загрузка списка ролей в ComboBox"""
        self.role_combo.clear()
        query = QSqlQuery(self.db)
        
        if not query.exec("SELECT id, role_name, description FROM krd.user_roles ORDER BY role_name"):
            self._log(f"load_roles(): ❌ Ошибка: {query.lastError().text()}", "ERROR")
            return
        
        while query.next():
            role_name = query.value(1) or ""
            description = query.value(2) or ""
            self.role_combo.addItem(f"{role_name} ({description})", query.value(0))
    
    def load_user_data(self) -> None:
        """Загрузка данных пользователя с полной диагностикой"""
        self._log(f"load_user_data(): Начинаю загрузку для user_id={self.user_id}", "DEBUG")

        if self.user_id is None:
            self._log("load_user_data(): ❌ user_id равен None!", "ERROR")
            QMessageBox.critical(self, "Ошибка", "ID пользователя не передан!")
            self.reject()
            return

        query = QSqlQuery(self.db)
        # 🔥 Именованные параметры :param для PostgreSQL
        # ⚠️ В схеме krd.users НЕТ поля updated_at!
        query.prepare("""
            SELECT u.id, u.username, u.full_name, u.email, u.role_id,
                   u.is_active, u.created_at, u.last_login, u.is_deleted,
                   r.role_name
            FROM krd.users u
            LEFT JOIN krd.user_roles r ON u.role_id = r.id
            WHERE u.id = :user_id
        """)
        query.bindValue(":user_id", self.user_id)

        if not query.exec():
            err = query.lastError().text()
            self._log(f"load_user_data(): ❌ Ошибка SQL: {err}", "ERROR")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось выполнить запрос:\n{err}")
            self.reject()
            return

        if not query.next():
            self._log(f"load_user_data(): ❌ Пользователь с ID {self.user_id} не найден", "ERROR")
            QMessageBox.warning(
                self, "Пользователь не найден", 
                f"Пользователь с ID {self.user_id} отсутствует в базе данных."
            )
            self.reject()
            return

        # Проверка на логическое удаление
        if query.value(8):  # is_deleted
            self._log(f"load_user_data(): ⚠️ Пользователь помечен как удалённый", "WARN")
            QMessageBox.warning(self, "Внимание", "Этот пользователь был удалён. Редактирование недоступно.")
            self.reject()
            return

        self._log("load_user_data(): ✅ Запись найдена, заполняю форму", "SUCCESS")

        # Заполнение полей формы
        self.id_label.setText(str(query.value(0)))
        self.username_input.setText(query.value(1) or "")
        self.original_username = query.value(1) or ""
        self.full_name_input.setText(query.value(2) or "")
        self.email_input.setText(query.value(3) or "")

        # Обработка роли
        role_id = query.value(4)
        role_name = query.value(9) or ""
        self.editing_user_role = role_name.lower() if role_name else None
        self._log(f"load_user_data(): role_id={role_id}, role_name='{role_name}'", "DEBUG")

        if role_id:
            index = self.role_combo.findData(role_id)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
            else:
                self._log(f"load_user_data(): ⚠️ Роль id={role_id} не найдена в списке", "WARN")

        self.is_user_active = bool(query.value(5))
        self.update_status_display()

        # Форматирование дат
        for i, (val, label) in enumerate([(query.value(6), self.created_at_label),
                                           (query.value(7), self.last_login_label)]):
            if val and hasattr(val, 'toString'):
                label.setText(val.toString("dd.MM.yyyy hh:mm:ss"))
            else:
                label.setText("—" if i == 0 else "Никогда")

        self._log("load_user_data(): ✅ Загрузка завершена успешно", "SUCCESS")
    
    def update_status_display(self) -> None:
        """Обновление отображения статуса пользователя"""
        if self.is_user_active:
            self.status_label.setText("✓ Активен")
            self.status_label.setProperty("status", "active")
        else:
            self.status_label.setText("✕ Заблокирован")
            self.status_label.setProperty("status", "inactive")
        
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
        if hasattr(self, 'deactivate_btn'):
            self.deactivate_btn.setEnabled(self.is_user_active)
        if hasattr(self, 'activate_btn'):
            self.activate_btn.setEnabled(not self.is_user_active)
    
    def on_deactivate_user(self) -> None:
        """Деактивация пользователя"""
        if self.editing_user_role == 'admin':
            QMessageBox.warning(self, "Запрещено", "Нельзя деактивировать администратора!")
            return
        
        if QMessageBox.question(
            self, "Подтверждение", 
            f"Деактивировать пользователя «{self.username_input.text()}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        
        try:
            query = QSqlQuery(self.db)
            query.prepare("UPDATE krd.users SET is_active = FALSE WHERE id = :id")
            query.bindValue(":id", self.user_id)
            
            if not query.exec():
                raise Exception(query.lastError().text())
            
            self.is_user_active = False
            self.update_status_display()
            QMessageBox.information(self, "Успех", "Пользователь деактивирован!")
            
        except Exception as e:
            self._log(f"on_deactivate_user(): ❌ {str(e)}", "ERROR")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при деактивации: {str(e)}")
    
    def on_activate_user(self) -> None:
        """Активация пользователя"""
        if self.editing_user_role == 'admin':
            QMessageBox.warning(self, "Запрещено", "Нельзя изменить статус администратора!")
            return
        
        if QMessageBox.question(
            self, "Подтверждение",
            f"Активировать пользователя «{self.username_input.text()}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        
        try:
            query = QSqlQuery(self.db)
            query.prepare("UPDATE krd.users SET is_active = TRUE WHERE id = :id")
            query.bindValue(":id", self.user_id)
            
            if not query.exec():
                raise Exception(query.lastError().text())
            
            self.is_user_active = True
            self.update_status_display()
            QMessageBox.information(self, "Успех", "Пользователь активирован!")
            
        except Exception as e:
            self._log(f"on_activate_user(): ❌ {str(e)}", "ERROR")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при активации: {str(e)}")
    
    def on_delete_user(self) -> None:
        """Мягкое удаление пользователя (is_deleted = TRUE)"""
        if self.editing_user_role == 'admin':
            QMessageBox.warning(self, "Запрещено", "Нельзя удалить администратора!")
            return
        
        username = self.username_input.text()
        if QMessageBox.question(
            self, "⚠️ Удаление",
            f"Удалить пользователя «{username}»? Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        
        # Подтверждение вводом имени пользователя
        confirm, ok = QMessageBox.getText(
            self, "Подтверждение",
            f"Введите «{username}» для подтверждения удаления:",
            QLineEdit.EchoMode.Normal, ""
        )
        
        if not ok or confirm != username:
            QMessageBox.warning(self, "Не подтверждено", "Удаление отменено.")
            return
        
        try:
            query = QSqlQuery(self.db)
            # 🔥 МЯГКОЕ УДАЛЕНИЕ согласно схеме: is_deleted = TRUE, deleted_at = NOW()
            query.prepare("""
                UPDATE krd.users 
                SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP 
                WHERE id = :id
            """)
            query.bindValue(":id", self.user_id)
            
            if not query.exec():
                raise Exception(query.lastError().text())
            
            QMessageBox.information(self, "Успех", "Пользователь удалён!")
            self.accept()
            
        except Exception as e:
            self._log(f"on_delete_user(): ❌ {str(e)}", "ERROR")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
    
    # === Валидаторы ===
    
    def validate_username(self, username: str) -> tuple[bool, str]:
        """Валидация имени пользователя"""
        if len(username) < 3:
            return False, "Минимум 3 символа"
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Только латиница, цифры, _ и -"
        return True, ""
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """Валидация пароля"""
        if len(password) < 6:
            return False, "Минимум 6 символов"
        return True, ""
    
    def validate_email(self, email: str) -> tuple[bool, str]:
        """Валидация email"""
        if not email:
            return True, ""  # Email необязателен
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Некорректный формат email"
        return True, ""
    
    def on_accept(self) -> None:
        """Обработчик сохранения данных"""
        self._log("on_accept(): Начало", "DEBUG")
        
        # Сбор данных из формы
        username = self.username_input.text().strip()
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        role_id = self.role_combo.currentData()
        is_active = self.is_user_active
        change_password = self.change_password_checkbox.isChecked()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
        
        # === Валидация ===
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
            QMessageBox.critical(self, "Ошибка валидации", "\n".join(f"• {e}" for e in errors))
            return
        
        # === Проверка уникальности username ===
        if username != self.original_username:
            check = QSqlQuery(self.db)
            check.prepare("SELECT id FROM krd.users WHERE username = :username AND id != :id")
            check.bindValue(":username", username)
            check.bindValue(":id", self.user_id)
            
            if check.exec() and check.next():
                QMessageBox.critical(self, "Ошибка", "Пользователь с таким именем уже существует!")
                return
        
        # === Сохранение в БД ===
        try:
            query = QSqlQuery(self.db)
            
            if change_password:
                # Хеширование пароля
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                # 🔥 UPDATE с паролем — БЕЗ updated_at (нет в схеме!)
                query.prepare("""
                    UPDATE krd.users 
                    SET username = :username,
                        password_hash = :password_hash,
                        full_name = :full_name,
                        email = :email,
                        role_id = :role_id,
                        is_active = :is_active
                    WHERE id = :id
                """)
                query.bindValue(":username", username)
                query.bindValue(":password_hash", hashed.decode('utf-8'))
                query.bindValue(":full_name", full_name)
                query.bindValue(":email", email)
                query.bindValue(":role_id", role_id)
                query.bindValue(":is_active", is_active)
                query.bindValue(":id", self.user_id)
                
            else:
                # 🔥 UPDATE без пароля — БЕЗ updated_at (нет в схеме!)
                query.prepare("""
                    UPDATE krd.users 
                    SET username = :username,
                        full_name = :full_name,
                        email = :email,
                        role_id = :role_id,
                        is_active = :is_active
                    WHERE id = :id
                """)
                query.bindValue(":username", username)
                query.bindValue(":full_name", full_name)
                query.bindValue(":email", email)
                query.bindValue(":role_id", role_id)
                query.bindValue(":is_active", is_active)
                query.bindValue(":id", self.user_id)
            
            # Отладочный лог
            self._log(f"SQL: {query.lastQuery()}", "SQL")
            self._log(f"boundValues: {query.boundValues()}", "DEBUG")
            
            if not query.exec():
                raise Exception(f"{query.lastError().text()}")
            
            self._log("on_accept(): ✅ Успешно сохранено", "SUCCESS")
            QMessageBox.information(self, "Успех", "Данные пользователя обновлены!")
            self.accept()
            
        except Exception as e:
            self._log(f"❌ Исключение: {str(e)}", "ERROR")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить данные:\n{str(e)}")