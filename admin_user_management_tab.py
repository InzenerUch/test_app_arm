"""
Модуль для административной вкладки управления пользователями
С таблицей пользователей, редактированием и добавлением через диалоги
"""

import bcrypt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTableView, QMessageBox, QMenu, QAbstractItemView, QHeaderView,
    QGroupBox, QLineEdit, QFrame,QDialog
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery
from PyQt6.QtGui import QAction, QFont, QContextMenuEvent

from user_edit_dialog import UserEditDialog
from user_add_dialog import UserAddDialog


class AdminUserManagementTab(QWidget):
    """
    Административная вкладка для управления пользователями
    """
    
    def __init__(self, db_connection, current_user_id=None):
        super().__init__()
        self.db = db_connection
        self.current_user_id = current_user_id
        
        print("🔧 [DEBUG] AdminUserManagementTab инициализирован")
        print(f"🔧 [DEBUG] current_user_id = {current_user_id}")
        
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # === Заголовок ===
        title_group = QGroupBox("👥 Управление пользователями системы")
        title_layout = QVBoxLayout(title_group)
        
        title_label = QLabel("Администрирование учётных записей пользователей")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        info_label = QLabel("📌 Здесь вы можете добавлять, редактировать и деактивировать пользователей системы")
        info_label.setStyleSheet("QLabel { color: #666; padding: 5px; }")
        title_layout.addWidget(info_label)
        
        layout.addWidget(title_group)
        
        # === Панель инструментов ===
        toolbar_layout = QHBoxLayout()
        
        self.add_user_btn = QPushButton("➕ Добавить пользователя")
        self.add_user_btn.setMinimumHeight(40)
        self.add_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_user_btn.clicked.connect(self.on_add_user)
        toolbar_layout.addWidget(self.add_user_btn)
        
        self.edit_user_btn = QPushButton("✏️ Редактировать")
        self.edit_user_btn.setMinimumHeight(40)
        self.edit_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.edit_user_btn.clicked.connect(self.on_edit_user)
        self.edit_user_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_user_btn)
        
        self.delete_user_btn = QPushButton("⏸️ Деактивировать")
        self.delete_user_btn.setMinimumHeight(40)
        self.delete_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.delete_user_btn.clicked.connect(self.on_toggle_active)
        self.delete_user_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_user_btn)
        
        toolbar_layout.addStretch()
        
        search_label = QLabel("🔍 Поиск:")
        search_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        toolbar_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ФИО, username, email...")
        self.search_input.setMinimumWidth(250)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_input)
        
        layout.addLayout(toolbar_layout)
        
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("QLabel { color: #666; padding: 5px; font-weight: bold; }")
        layout.addWidget(self.stats_label)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        self.users_table = QTableView()
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.users_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.users_table.customContextMenuRequested.connect(self.show_context_menu)
        self.users_table.doubleClicked.connect(self.on_edit_user)
        
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.users_table)
        self.setLayout(layout)
    
    def load_users(self, search_query=""):
        """Загрузка списка пользователей"""
        print(f"\n🔍 [DEBUG] load_users вызван, search_query='{search_query}'")
        
        self.users_model = QSqlQueryModel()
        
        # Проверка количества записей
        count_query = QSqlQuery(self.db)
        count_query.exec("SELECT COUNT(*) FROM krd.users")
        if count_query.next():
            total_count = count_query.value(0)
            print(f"📊 [DEBUG] Всего записей в krd.users: {total_count}")
        
        # === ОСНОВНОЙ ЗАПРОС (БЕЗ is_deleted - его нет в схеме!) ===
        if search_query:
            query_str = """
                SELECT 
                    u.id AS "ID",
                    u.username AS "Имя пользователя",
                    u.full_name AS "ФИО",
                    u.email AS "Email",
                    r.role_name AS "Роль",
                    CASE WHEN u.is_active THEN '✓ Активен' ELSE '⏸️ Деактивирован' END AS "Статус",
                    u.created_at AS "Дата создания"
                FROM krd.users u
                LEFT JOIN krd.user_roles r ON u.role_id = r.id
                WHERE (
                    LOWER(u.username) LIKE LOWER(:search) OR
                    LOWER(u.full_name) LIKE LOWER(:search) OR
                    LOWER(u.email) LIKE LOWER(:search)
                )
                ORDER BY u.created_at DESC
            """
            query = QSqlQuery(self.db)
            query.prepare(query_str)
            query.bindValue(":search", f"%{search_query}%")
            
            if not query.exec():
                print(f"❌ [DEBUG] Ошибка выполнения запроса: {query.lastError().text()}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки пользователей:\n{query.lastError().text()}")
                return
            
            self.users_model.setQuery(query)
        else:
            query_str = """
                SELECT 
                    u.id AS "ID",
                    u.username AS "Имя пользователя",
                    u.full_name AS "ФИО",
                    u.email AS "Email",
                    r.role_name AS "Роль",
                    CASE WHEN u.is_active THEN '✓ Активен' ELSE '⏸️ Деактивирован' END AS "Статус",
                    u.created_at AS "Дата создания"
                FROM krd.users u
                LEFT JOIN krd.user_roles r ON u.role_id = r.id
                ORDER BY u.created_at DESC
            """
            
            print(f"📝 [DEBUG] Выполняю запрос")
            
            # === ПРЯМОЕ ВЫПОЛНЕНИЕ ЗАПРОСА ===
            query = QSqlQuery(self.db)
            if not query.exec(query_str):
                print(f"❌ [DEBUG] Ошибка query.exec: {query.lastError().text()}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки пользователей:\n{query.lastError().text()}")
                return
            
            self.users_model.setQuery(query)
        
        count = self.users_model.rowCount()
        print(f"✅ [DEBUG] Запрос вернул {count} записей")
        
        if count > 0:
            print("📋 [DEBUG] Первые записи:")
            for i in range(min(count, 5)):
                row_data = []
                for j in range(self.users_model.columnCount()):
                    row_data.append(str(self.users_model.data(self.users_model.index(i, j))))
                print(f"   Строка {i}: {row_data}")
        
        self.users_table.setModel(self.users_model)
        
        self.users_table.setColumnWidth(0, 50)
        self.users_table.setColumnWidth(1, 150)
        self.users_table.setColumnWidth(2, 200)
        self.users_table.setColumnWidth(3, 200)
        self.users_table.setColumnWidth(4, 120)
        self.users_table.setColumnWidth(5, 120)
        
        self.users_table.hideColumn(0)
        
        if search_query:
            self.stats_label.setText(f"🔍 Найдено пользователей: {count}")
        else:
            self.stats_label.setText(f"📊 Всего пользователей в системе: {count}")
        
        self.update_buttons_state()
        
        if count == 0:
            print("⚠️ [DEBUG] Записей не найдено! Проверяю таблицу напрямую...")
            self._check_users_table_directly()
    
    def _check_users_table_directly(self):
        """Прямая проверка таблицы пользователей"""
        query = QSqlQuery(self.db)
        query.exec("SELECT id, username, full_name, is_active FROM krd.users")
        
        print("\n🔍 [DEBUG] Прямая проверка таблицы krd.users:")
        while query.next():
            user_id = query.value(0)
            username = query.value(1)
            full_name = query.value(2)
            is_active = query.value(3)
            print(f"   ID={user_id}, username={username}, full_name={full_name}, is_active={is_active}")
    
    def update_buttons_state(self):
        """Обновление состояния кнопок"""
        has_selection = self.users_table.selectionModel().hasSelection()
        self.edit_user_btn.setEnabled(has_selection)
        self.delete_user_btn.setEnabled(has_selection)
    
    def on_search_changed(self, text):
        """Обработка изменения поискового запроса"""
        self.load_users(text.strip())
    
    def show_context_menu(self, position: QPoint):
        """Показ контекстного меню"""
        index = self.users_table.indexAt(position)
        
        if not index.isValid():
            return
        
        menu = QMenu(self)
        
        edit_action = QAction("✏️ Редактировать пользователя", self)
        edit_action.triggered.connect(self.on_edit_user)
        menu.addAction(edit_action)
        
        user_id = self.get_selected_user_id()
        is_active = self._get_user_active_status(user_id)
        
        if is_active:
            deactivate_action = QAction("⏸️ Деактивировать пользователя", self)
            deactivate_action.triggered.connect(self.on_toggle_active)
            menu.addAction(deactivate_action)
        else:
            activate_action = QAction("✅ Активировать пользователя", self)
            activate_action.triggered.connect(self.on_toggle_active)
            menu.addAction(activate_action)
        
        menu.addSeparator()
        
        reset_password_action = QAction("🔑 Сбросить пароль", self)
        reset_password_action.triggered.connect(self.on_reset_password)
        menu.addAction(reset_password_action)
        
        menu.exec(self.users_table.mapToGlobal(position))
    
    def _get_user_active_status(self, user_id):
        """Получение статуса активности пользователя"""
        if not user_id:
            return True
        
        query = QSqlQuery(self.db)
        query.prepare("SELECT is_active FROM krd.users WHERE id = ?")
        query.addBindValue(user_id)
        
        if query.exec() and query.next():
            return query.value(0)
        return True
    
    def get_selected_user_id(self):
        """Получение ID выбранного пользователя"""
        selection = self.users_table.selectionModel()
        if not selection.hasSelection():
            return None
        
        index = selection.selectedRows()[0]
        user_id = self.users_model.data(self.users_model.index(index.row(), 0))
        
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return None
    
    def on_add_user(self):
        """Открытие диалога добавления пользователя"""
        dialog = UserAddDialog(self.db, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()
            QMessageBox.information(self, "Успешно", "Пользователь успешно добавлен!")
    
    def on_edit_user(self):
        """Открытие диалога редактирования пользователя"""
        user_id = self.get_selected_user_id()
        
        if not user_id:
            QMessageBox.warning(self, "Внимание", "Выберите пользователя для редактирования")
            return
        
        if user_id == self.current_user_id:
            QMessageBox.warning(self, "Внимание", "Вы не можете редактировать свою собственную учётную запись")
            return
        
        dialog = UserEditDialog(self.db, user_id, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_users()
            QMessageBox.information(self, "Успешно", "Данные пользователя обновлены!")
    
    def on_toggle_active(self):
        """Деактивация/активация пользователя"""
        user_id = self.get_selected_user_id()
        
        if not user_id:
            QMessageBox.warning(self, "Внимание", "Выберите пользователя")
            return
        
        if user_id == self.current_user_id:
            QMessageBox.critical(self, "Ошибка", "Вы не можете деактивировать свою собственную учётную запись!")
            return
        
        query = QSqlQuery(self.db)
        query.prepare("SELECT username, full_name, is_active FROM krd.users WHERE id = ?")
        query.addBindValue(user_id)
        query.exec()
        
        if query.next():
            username = query.value(0)
            full_name = query.value(1)
            is_active = query.value(2)
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
            return
        
        if is_active:
            reply = QMessageBox.question(
                self,
                "Подтверждение деактивации",
                f"Вы действительно хотите деактивировать пользователя?\n\n"
                f"👤 Username: {username}\n"
                f"📋 ФИО: {full_name}\n\n"
                f"⚠️ Пользователь потеряет доступ к системе!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    update_query = QSqlQuery(self.db)
                    update_query.prepare("UPDATE krd.users SET is_active = FALSE WHERE id = ?")
                    update_query.addBindValue(user_id)
                    
                    if not update_query.exec():
                        raise Exception(f"Ошибка при деактивации: {update_query.lastError().text()}")
                    
                    self.load_users()
                    QMessageBox.information(self, "Успешно", f"Пользователь '{username}' деактивирован!")
                    
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка при деактивации пользователя:\n{str(e)}")
        else:
            reply = QMessageBox.question(
                self,
                "Подтверждение активации",
                f"Вы действительно хотите активировать пользователя?\n\n"
                f"👤 Username: {username}\n"
                f"📋 ФИО: {full_name}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    update_query = QSqlQuery(self.db)
                    update_query.prepare("UPDATE krd.users SET is_active = TRUE WHERE id = ?")
                    update_query.addBindValue(user_id)
                    
                    if not update_query.exec():
                        raise Exception(f"Ошибка при активации: {update_query.lastError().text()}")
                    
                    self.load_users()
                    QMessageBox.information(self, "Успешно", f"Пользователь '{username}' активирован!")
                    
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка при активации пользователя:\n{str(e)}")
    
    def on_reset_password(self):
        """Сброс пароля пользователя"""
        user_id = self.get_selected_user_id()
        
        if not user_id:
            QMessageBox.warning(self, "Внимание", "Выберите пользователя")
            return
        
        if user_id == self.current_user_id:
            QMessageBox.warning(self, "Внимание", "Вы не можете сбросить свой собственный пароль через эту функцию")
            return
        
        reply = QMessageBox.question(
            self,
            "Сброс пароля",
            "Сбросить пароль пользователю и показать временный пароль?\n\n"
            "⚠️ Временный пароль будет показан только один раз!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import random
            import string
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            hashed_password = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt())
            
            query = QSqlQuery(self.db)
            query.prepare("UPDATE krd.users SET password_hash = ? WHERE id = ?")
            query.addBindValue(hashed_password.decode('utf-8'))
            query.addBindValue(user_id)
            
            if query.exec():
                QMessageBox.information(
                    self,
                    "Пароль сброшен",
                    f"Временный пароль: {temp_password}\n\n"
                    f"⚠️ Скопируйте пароль сейчас! Он не будет показан повторно."
                )
            else:
                QMessageBox.critical(self, "Ошибка", f"Ошибка сброса пароля: {query.lastError().text()}")