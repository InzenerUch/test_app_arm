"""
Модуль для административной вкладки управления пользователями
✅ ИСПРАВЛЕНО: Проверка существования и is_deleted перед открытием диалога
✅ ИСПРАВЛЕНО: Фильтрация удалённых пользователей в основном запросе
✅ ДОБАВЛЕНО: Автоматическое обновление таблицы при обнаружении рассинхронизации
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QMessageBox, QAbstractItemView, QHeaderView,
    QGroupBox, QLineEdit, QFrame, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont
from user_edit_dialog import UserEditDialog
from user_add_dialog import UserAddDialog

logger = logging.getLogger(__name__)

class AdminUserManagementTab(QWidget):
    """Административная вкладка для управления пользователями"""
    
    def __init__(self, db_connection, current_user_id=None):
        super().__init__()
        self.db = db_connection
        self.current_user_id = current_user_id
        print(f"\n🔧 [DEBUG] AdminUserManagementTab инициализирован")
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title_group = QGroupBox("👥 Управление пользователями системы")
        title_layout = QVBoxLayout(title_group)
        title_layout.addWidget(QLabel("Администрирование учётных записей пользователей", font=QFont("Arial", 12, QFont.Weight.Bold)))
        layout.addWidget(title_group)
        
        toolbar_layout = QHBoxLayout()
        self.add_user_btn = QPushButton("➕ Добавить пользователя")
        self.add_user_btn.setProperty("role", "info")
        self.add_user_btn.clicked.connect(self.on_add_user)
        toolbar_layout.addWidget(self.add_user_btn)
        
        self.edit_user_btn = QPushButton("✏️ Редактировать")
        self.edit_user_btn.setProperty("role", "edit")
        self.edit_user_btn.clicked.connect(self.on_edit_user)
        self.edit_user_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_user_btn)
        
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ФИО, username, email...")
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_input)
        layout.addLayout(toolbar_layout)
        
        self.stats_label = QLabel("")
        layout.addWidget(self.stats_label)
        layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))
        
        self.users_table = QTableView()
        self.users_model = QSqlQueryModel()
        self.users_table.setModel(self.users_model)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.users_table.doubleClicked.connect(self.on_edit_user)
        self.users_table.selectionModel().selectionChanged.connect(self.update_buttons_state)
        layout.addWidget(self.users_table)
    
    def load_users(self, search_query=""):
        """Загрузка пользователей с фильтрацией удалённых записей"""
        print(f"\n🔄 [LOAD] Загрузка пользователей (поиск: '{search_query}')")
        query = QSqlQuery(self.db)
        base_sql = """
            SELECT u.id, u.username, u.full_name, u.email, r.role_name,
                   CASE WHEN u.is_active THEN '✓ Активен' ELSE '⏸️ Деактивирован' END,
                   u.created_at
            FROM krd.users u
            LEFT JOIN krd.user_roles r ON u.role_id = r.id
            WHERE (u.is_deleted = FALSE OR u.is_deleted IS NULL)
        """
        
        if search_query:
            query.prepare(base_sql + """
                AND (LOWER(u.username) LIKE LOWER(?) 
                OR LOWER(u.full_name) LIKE LOWER(?) 
                OR LOWER(u.email) LIKE LOWER(?)) 
                ORDER BY u.created_at DESC
            """)
            query.addBindValue(f"%{search_query}%")
            query.addBindValue(f"%{search_query}%")
            query.addBindValue(f"%{search_query}%")
        else:
            query.prepare(base_sql + " ORDER BY u.created_at DESC")
            
        if not query.exec():
            print(f"❌ [SQL] Ошибка: {query.lastError().text()}")
            return
            
        self.users_model.setQuery(query)
        self.users_table.setColumnHidden(0, True)
        
        count = self.users_model.rowCount()
        print(f"✅ [LOAD] Загружено {count} пользователей")
        self.stats_label.setText(f"📊 Всего: {count}")
        self.update_buttons_state()
    
    def update_buttons_state(self):
        has_selection = self.users_table.selectionModel().hasSelection()
        self.edit_user_btn.setEnabled(has_selection)
        print(f"🔘 [UI] Кнопка edit={has_selection}")
    
    def on_search_changed(self, text):
        self.load_users(text.strip())
    
    def get_selected_user_id(self):
        selection = self.users_table.selectionModel()
        if not selection.hasSelection():
            return None
        row = selection.selectedRows()[0].row()
        user_id = self.users_model.data(self.users_model.index(row, 0))
        try:
            return int(user_id) if user_id else None
        except:
            return None
    
    def on_add_user(self):
        print(f"\n➕ [ACTION] Запрос на добавление пользователя")
        dialog = UserAddDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            print(f"✅ [ACTION] Пользователь успешно добавлен")
            self.load_users()
            self._log_action('USER_CREATED', None, 'Пользователь добавлен через админ-панель')
    
    def on_edit_user(self):
        """Редактирование пользователя с проверкой существования и is_deleted"""
        user_id = self.get_selected_user_id()
        if not user_id:
            print(f"⚠️ [EDIT] Нет выделения")
            return

        if self.current_user_id and int(self.current_user_id) == int(user_id):
            print(f"⚠️ [EDIT] Нельзя редактировать себя")
            QMessageBox.warning(self, "Внимание", "Нельзя редактировать свою учётную запись")
            return

        # ✅ ПРОВЕРКА: Существует ли пользователь в БД прямо сейчас
        print(f"✏️ [ACTION] Проверка перед редактированием ID={user_id}")
        check_query = QSqlQuery(self.db)
        check_query.prepare("SELECT username, is_deleted FROM krd.users WHERE id = ?")
        check_query.addBindValue(user_id)
        
        if not check_query.exec() or not check_query.next():
            QMessageBox.warning(self, "Пользователь не найден", 
                f"Пользователь с ID {user_id} отсутствует в базе данных.\n"
                f"Список будет обновлён автоматически.")
            self.load_users()  # 🔄 Обновляем таблицу
            return
            
        username = check_query.value(0)
        is_deleted = check_query.value(1)
        
        if is_deleted:
            QMessageBox.warning(self, "Пользователь удалён", 
                f"Пользователь '{username}' был удалён.\n"
                f"Редактирование невозможно.")
            self.load_users()
            return

        print(f"✅ [EDIT] Пользователь '{username}' существует. Открываю диалог...")
        dialog = UserEditDialog(self.db, user_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            print(f"✅ [ACTION] Данные пользователя обновлены")
            self.load_users()
            self._log_action('USER_EDITED', user_id, 'Данные пользователя отредактированы')
    
    def _log_action(self, action_type: str, user_id: int, description: str):
        if self.parent() and hasattr(self.parent(), 'audit_logger'):
            self.parent().audit_logger.log_action(action_type, 'users', user_id, None, description)
            print(f"📝 [AUDIT] Записано: {action_type} | user_id={user_id}")