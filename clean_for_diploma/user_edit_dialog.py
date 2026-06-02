import bcrypt
import re
import traceback
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QLabel, QMessageBox,
    QGroupBox, QDialogButtonBox, QCheckBox, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlQuery
class UserEditDialog(QDialog):
    def __init__(self, db_connection, user_id: int, parent=None):
        print(f"\n🔍 [UserEditDialog] ИНИЦИАЛИЗАЦИЯ | user_id={user_id}")
        super().__init__(parent)
        self.db = db_connection
        self.user_id = user_id
        self.current_user_role: Optional[str] = None
        self.editing_user_role: Optional[str] = None
        self.setWindowTitle("✏️ Редактирование пользователя")
        self.setMinimumSize(550, 600)
        self.resize(600, 650)
        self.setModal(True)
        self.original_username = ""
        self.is_user_active = True
        self.status_buttons_visible = True
        self.init_ui()
        self.load_user_data()
    def _log(self, message: str, level: str = "INFO") -> None:
        prefix = {
            "INFO": "📝", "DEBUG": "🔧", "WARN": "⚠️",
            "ERROR": "❌", "SUCCESS": "✅", "SQL": "🗄️"
        }.get(level, "•")
        print(f"{prefix} [{level}] {message}")
    def init_ui(self) -> None:
        self._log("init_ui(): Начало", "DEBUG")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(15, 15, 15, 15)
        title_label = QLabel("👤 Редактирование учётной записи")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        content_layout.addWidget(title_label)
        info_group = QGroupBox("📋 Основная информация")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(15, 15, 15, 15)
        self.id_label = QLabel("")
        self.id_label.setStyleSheet("QLabel { color:
        info_layout.addRow("ID пользователя:", self.id_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин для входа")
        self.username_input.setMinimumHeight(32)
        info_layout.addRow("Имя пользователя *:", self.username_input)
        password_group = QGroupBox("🔐 Смена пароля (поставьте галочку для активации)")
        password_group.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 2px solid
            QGroupBox::title { subcontrol-origin: margin; left: 15px; color:
            QLabel { padding: 8px; border-radius: 4px; font-weight: bold; background-color:
            QLabel[status="inactive"] { background-color:
Создание кнопок активации/деактивации пользователя"""
        status_buttons_group = QGroupBox("⚡ Управление статусом")
        status_buttons_layout = QHBoxLayout(status_buttons_group)
        status_buttons_layout.setSpacing(10)
        status_buttons_layout.setContentsMargins(10, 10, 10, 10)
        self.deactivate_btn = QPushButton("⏸️ Деактивировать")
        self.deactivate_btn.setStyleSheet(
            "QPushButton { background-color:
            "padding: 10px; border-radius: 5px; min-height: 36px; } "
            "QPushButton:hover { background-color:
            "QPushButton:disabled { background-color:
        )
        self.deactivate_btn.clicked.connect(self.on_deactivate_user)
        status_buttons_layout.addWidget(self.deactivate_btn)
        self.activate_btn = QPushButton("✅ Активировать")
        self.activate_btn.setStyleSheet(
            "QPushButton { background-color:
            "padding: 10px; border-radius: 5px; min-height: 36px; } "
            "QPushButton:hover { background-color:
            "QPushButton:disabled { background-color:
        )
        self.activate_btn.clicked.connect(self.on_activate_user)
        status_buttons_layout.addWidget(self.activate_btn)
        layout.addWidget(status_buttons_group)
        self.status_buttons_visible = True
    def on_password_change_toggled(self, state: int) -> None:
        is_checked = state == Qt.CheckState.Checked.value
        self.password_input.setEnabled(is_checked)
        self.password_confirm_input.setEnabled(is_checked)
        if not is_checked:
            self.password_input.clear()
            self.password_confirm_input.clear()
    def load_roles(self) -> None:
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
        self._log(f"load_user_data(): Начинаю загрузку для user_id={self.user_id}", "DEBUG")
        if self.user_id is None:
            self._log("load_user_data(): ❌ user_id равен None!", "ERROR")
            QMessageBox.critical(self, "Ошибка", "ID пользователя не передан!")
            self.reject()
            return
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT u.id, u.username, u.full_name, u.email, u.role_id,
                   u.is_active, u.created_at, u.last_login, u.is_deleted,
                   r.role_name
            FROM krd.users u
            LEFT JOIN krd.user_roles r ON u.role_id = r.id
            WHERE u.id = :user_id
Обновление отображения статуса пользователя"""
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
            query.prepare("""
                UPDATE krd.users
                SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP
                WHERE id = :id
Валидация имени пользователя"""
        if len(username) < 3:
            return False, "Минимум 3 символа"
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Только латиница, цифры, _ и -"
        return True, ""
    def validate_password(self, password: str) -> tuple[bool, str]:
        if len(password) < 6:
            return False, "Минимум 6 символов"
        return True, ""
    def validate_email(self, email: str) -> tuple[bool, str]:
        if not email:
            return True, ""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Некорректный формат email"
        return True, ""
    def on_accept(self) -> None:
        self._log("on_accept(): Начало", "DEBUG")
        username = self.username_input.text().strip()
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        role_id = self.role_combo.currentData()
        is_active = self.is_user_active
        change_password = self.change_password_checkbox.isChecked()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
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
        if username != self.original_username:
            check = QSqlQuery(self.db)
            check.prepare("SELECT id FROM krd.users WHERE username = :username AND id != :id")
            check.bindValue(":username", username)
            check.bindValue(":id", self.user_id)
            if check.exec() and check.next():
                QMessageBox.critical(self, "Ошибка", "Пользователь с таким именем уже существует!")
                return
        try:
            query = QSqlQuery(self.db)
            if change_password:
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                query.prepare("""
                    UPDATE krd.users
                    SET username = :username,
                        password_hash = :password_hash,
                        full_name = :full_name,
                        email = :email,
                        role_id = :role_id,
                        is_active = :is_active
                    WHERE id = :id
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