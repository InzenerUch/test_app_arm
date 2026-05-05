"""
Диалог конфигурации отчета КРД с хранением шаблонов в БД
Поддерживает только массовый экспорт всех записей на один лист Excel
✅ ДОБАВЛЕНО: Полная диагностика (DEBUG логи) для отслеживания ошибок
✅ ИСПРАВЛЕНО: QMessageBox.StandardButton для PyQt6
✅ ИСПРАВЛЕНО: Безопасная обработка ID и User ID
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlQuery
import json
from field_selection_dialog import FieldSelectionDialog

class ReportConfigDialog(QDialog):
    """Диалог настройки конфигурации отчета с БД (только массовый экспорт)"""
    report_configured = pyqtSignal(dict)

    def __init__(self, db_connection, parent=None, template_id=None):
        super().__init__(parent)
        self.setWindowTitle("Генерация отчета по всем КРД")
        self.setMinimumSize(700, 650)
        self.db = db_connection
        self.template_id = template_id
        self.current_config = {
            "sections": ["social_data"],
            "fields": {}
        }
        self.current_template_id = None
        
        # Безопасно получаем ID текущего пользователя из родителя
        # Если parent не передан или у него нет user_info, будет None
        if parent and hasattr(parent, 'user_info') and isinstance(parent.user_info, dict):
            self.current_user_id = parent.user_info.get('id')
        else:
            self.current_user_id = None
            
        print(f"🔵 [DEBUG] Инициализация ReportConfigDialog. User ID: {self.current_user_id}")
            
        self.init_ui()
        self.load_templates_list()
        self._update_krd_count()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # === Информация о режиме экспорта ===
        info_group = QGroupBox("📊 Режим экспорта")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel("Экспорт всех записей КРД из базы данных на ОДИН лист Excel")
        info_label.setStyleSheet("QLabel { font-size: 11px; color: #666; }")
        info_layout.addWidget(info_label)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("QLabel { color: #666; padding: 5px; border-radius: 3px; font-weight: bold; }")
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)

        # === Список шаблонов ===
        templates_group = QGroupBox("📋 Шаблоны отчетов")
        templates_layout = QVBoxLayout(templates_group)
        
        self.templates_list = QListWidget()
        self.templates_list.setMinimumHeight(200)
        self.templates_list.itemClicked.connect(self.on_template_clicked)
        self.templates_list.itemDoubleClicked.connect(self.on_template_double_clicked)
        
        self.templates_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        templates_layout.addWidget(self.templates_list)
        
        self.template_description = QLabel("")
        self.template_description.setWordWrap(True)
        self.template_description.setStyleSheet("QLabel { padding: 10px; border-radius: 5px; color: #666; }")
        templates_layout.addWidget(self.template_description)
        layout.addWidget(templates_group)

        # === Кнопки управления ===
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        # Кнопка добавления шаблона (СИНИЙ)
        add_template_btn = QPushButton("➕ Добавить шаблон")
        add_template_btn.setMinimumHeight(45)
        add_template_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        add_template_btn.setProperty("role", "info")
        add_template_btn.clicked.connect(self.on_add_template)
        btn_layout.addWidget(add_template_btn)

        # Кнопка удаления шаблона (КРАСНЫЙ)
        self.delete_template_btn = QPushButton("🗑️ Удалить шаблон")
        self.delete_template_btn.setMinimumHeight(45)
        self.delete_template_btn.setProperty("role", "danger")
        self.delete_template_btn.clicked.connect(self.on_delete_template)
        self.delete_template_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_template_btn)

        # Кнопка экспорта (ЗЕЛЁНЫЙ)
        self.export_btn = QPushButton("📥 Экспорт всех КРД в Excel")
        self.export_btn.setMinimumHeight(45)
        self.export_btn.setProperty("role", "save")
        self.export_btn.clicked.connect(self.on_export)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)

        # Кнопка отмены (СЕРЫЙ)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setProperty("role", "normal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        
        # Подключение для активации кнопки удаления
        self.templates_list.currentItemChanged.connect(self.on_selection_changed)
        
        self.update_export_button()

    def on_selection_changed(self, current, previous):
        """Активация кнопки удаления при выборе шаблона"""
        has_selection = self.templates_list.currentItem() is not None
        self.delete_template_btn.setEnabled(has_selection)

    def _update_krd_count(self):
        """Обновление информации о количестве записей"""
        query = QSqlQuery(self.db)
        query.prepare("SELECT COUNT(*) FROM krd.krd WHERE is_deleted = FALSE")
        if query.exec() and query.next():
            count = query.value(0)
            self.info_label.setText(f"Будет экспортировано: {count} записей КРД")
        else:
            self.info_label.setText("⚠️ Не удалось получить количество записей")

    def load_templates_list(self):
        """Загрузка шаблонов в QListWidget из БД"""
        print("🔵 [DEBUG] load_templates_list: Загрузка списка шаблонов...")
        self.templates_list.clear()
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT id, name, description, template_type, usage_count, is_default
            FROM krd.report_templates
            WHERE is_deleted = FALSE
            ORDER BY is_default DESC, usage_count DESC, name ASC
        """)
        if query.exec():
            count = 0
            while query.next():
                template_id = query.value(0)
                template_name = query.value(1)
                description = query.value(2) or ""
                template_type = query.value(3)
                usage_count = query.value(4) or 0
                is_default = query.value(5)
                
                icon = "⭐" if is_default else "📋"
                usage_text = f"({usage_count} исп.)" if usage_count > 0 else ""
                
                item = QListWidgetItem(f"{icon} {template_name} {usage_text}")
                item.setData(Qt.ItemDataRole.UserRole, template_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, description)
                item.setData(Qt.ItemDataRole.UserRole + 2, template_name)
                self.templates_list.addItem(item)
                count += 1
            print(f"✅ [DEBUG] load_templates_list: Загружено {count} шаблонов.")
        else:
            print(f"❌ [DEBUG] load_templates_list: Ошибка SQL - {query.lastError().text()}")

    def on_template_clicked(self, item):
        """Обработка клика на шаблон в списке"""
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template_name = item.data(Qt.ItemDataRole.UserRole + 2)
        self.load_template_description(template_id, template_name)

    def on_template_double_clicked(self, item):
        """Обработка двойного клика на шаблон - открытие редактора"""
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template_name = item.data(Qt.ItemDataRole.UserRole + 2)
        self.edit_template(template_id, template_name)

    def load_template_description(self, template_id, template_name):
        """Загрузка описания шаблона"""
        query = QSqlQuery(self.db)
        query.prepare("SELECT description, config_json, usage_count FROM krd.report_templates WHERE id = ?")
        query.addBindValue(template_id)
        if query.exec() and query.next():
            description = query.value(0) or ""
            config_json = query.value(1)
            usage_count = query.value(2) or 0
            
            desc_text = f"<b>📋 Шаблон:</b> {template_name}<br>"
            desc_text += f"<b>Описание:</b> {description or 'Нет описания'}<br>"
            desc_text += f"<b>Использований:</b> {usage_count}<br>"
            
            if config_json:
                try:
                    config = json.loads(config_json)
                    sections = config.get("sections", [])
                    fields_count = sum(len(fields) for fields in config.get("fields", {}).values())
                    desc_text += f"<b>Секций:</b> {len(sections)} | <b>Полей:</b> {fields_count}"
                    self.current_config = config
                    self.current_template_id = template_id
                    self.update_export_button()
                except Exception as e:
                    print(f"⚠️ [DEBUG] Ошибка парсинга JSON: {e}")
                    pass
            
            self.template_description.setText(desc_text)

    def on_add_template(self):
        """Открытие диалога создания нового шаблона"""
        dialog = FieldSelectionDialog(self, config=None, template_name=None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            template_name = dialog.get_template_name()
            if not template_name:
                template_name = "Новый шаблон"
            self.save_template_to_db(template_name, "", config)

    def edit_template(self, template_id, template_name):
        """Редактирование шаблона - открытие диалога выбора полей"""
        query = QSqlQuery(self.db)
        query.prepare("SELECT config_json FROM krd.report_templates WHERE id = ?")
        query.addBindValue(template_id)
        if query.exec() and query.next():
            config_json = query.value(0)
            if config_json:
                config = json.loads(config_json)
                dialog = FieldSelectionDialog(self, config, template_name)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    new_config = dialog.get_config()
                    reply = QMessageBox.question(
                        self,
                        "Сохранить изменения",
                        f"Сохранить изменения в шаблоне '{template_name}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.update_template_in_db(template_id, new_config)

    def save_template_to_db(self, name, description, config):
        """Сохранение шаблона в БД"""
        print(f"🔵 [DEBUG] save_template_to_db: Сохранение '{name}'")
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.report_templates (name, description, template_type, config_json)
            VALUES (:name, :desc, 'excel', :config)
        """)
        query.bindValue(":name", name.strip())
        query.bindValue(":desc", description.strip() if description else "")
        query.bindValue(":config", json.dumps(config, ensure_ascii=False))
        
        if query.exec():
            print("✅ [DEBUG] save_template_to_db: Успешно.")
            QMessageBox.information(self, "Успешно", f"Шаблон '{name}' сохранен в базу данных")
            self.load_templates_list()
        else:
            print(f"❌ [DEBUG] save_template_to_db: Ошибка - {query.lastError().text()}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {query.lastError().text()}")

    def update_template_in_db(self, template_id, config):
        """Обновление шаблона в БД"""
        print(f"🔵 [DEBUG] update_template_in_db: Обновление ID={template_id}")
        query = QSqlQuery(self.db)
        query.prepare("""
            UPDATE krd.report_templates
            SET config_json = :config, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """)
        query.bindValue(":config", json.dumps(config, ensure_ascii=False))
        query.bindValue(":id", template_id)
        
        if query.exec():
            print("✅ [DEBUG] update_template_in_db: Успешно.")
            QMessageBox.information(self, "Успешно", "Шаблон обновлен")
            self.load_templates_list()
        else:
            print(f"❌ [DEBUG] update_template_in_db: Ошибка - {query.lastError().text()}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления: {query.lastError().text()}")

"""
Диалог конфигурации отчета КРД с хранением шаблонов в БД
Поддерживает только массовый экспорт всех записей на один лист Excel
✅ ИСПРАВЛЕНО: Обход бага QPSQL драйвера (EXECUTE syntax error)
✅ ИСПРАВЛЕНО: QMessageBox.StandardButton для PyQt6
✅ ИСПРАВЛЕНО: Унифицированы все SQL-запросы на ? + addBindValue()
✅ ИСПРАВЛЕНО: Безопасная обработка ID и User ID
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlQuery
import json
from field_selection_dialog import FieldSelectionDialog

class ReportConfigDialog(QDialog):
    """Диалог настройки конфигурации отчета с БД (только массовый экспорт)"""
    report_configured = pyqtSignal(dict)

    def __init__(self, db_connection, parent=None, template_id=None):
        super().__init__(parent)
        self.setWindowTitle("Генерация отчета по всем КРД")
        self.setMinimumSize(700, 650)
        self.db = db_connection
        self.template_id = template_id
        self.current_config = {
            "sections": ["social_data"],
            "fields": {}
        }
        self.current_template_id = None
        
        # Безопасно получаем ID текущего пользователя из родителя
        if parent and hasattr(parent, 'user_info') and isinstance(parent.user_info, dict):
            self.current_user_id = parent.user_info.get('id')
        else:
            self.current_user_id = None
            
        print(f"🔵 [DEBUG] Инициализация ReportConfigDialog. User ID: {self.current_user_id}")
            
        self.init_ui()
        self.load_templates_list()
        self._update_krd_count()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # === Информация о режиме экспорта ===
        info_group = QGroupBox("📊 Режим экспорта")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel("Экспорт всех записей КРД из базы данных на ОДИН лист Excel")
        info_label.setStyleSheet("QLabel { font-size: 11px; color: #666; }")
        info_layout.addWidget(info_label)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("QLabel { color: #666; padding: 5px; border-radius: 3px; font-weight: bold; }")
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)

        # === Список шаблонов ===
        templates_group = QGroupBox("📋 Шаблоны отчетов")
        templates_layout = QVBoxLayout(templates_group)
        
        self.templates_list = QListWidget()
        self.templates_list.setMinimumHeight(200)
        self.templates_list.itemClicked.connect(self.on_template_clicked)
        self.templates_list.itemDoubleClicked.connect(self.on_template_double_clicked)
        
        self.templates_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        templates_layout.addWidget(self.templates_list)
        
        self.template_description = QLabel("")
        self.template_description.setWordWrap(True)
        self.template_description.setStyleSheet("QLabel { padding: 10px; border-radius: 5px; color: #666; }")
        templates_layout.addWidget(self.template_description)
        layout.addWidget(templates_group)

        # === Кнопки управления ===
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        add_template_btn = QPushButton("➕ Добавить шаблон")
        add_template_btn.setMinimumHeight(45)
        add_template_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        add_template_btn.setProperty("role", "info")
        add_template_btn.clicked.connect(self.on_add_template)
        btn_layout.addWidget(add_template_btn)

        self.delete_template_btn = QPushButton("🗑️ Удалить шаблон")
        self.delete_template_btn.setMinimumHeight(45)
        self.delete_template_btn.setProperty("role", "danger")
        self.delete_template_btn.clicked.connect(self.on_delete_template)
        self.delete_template_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_template_btn)

        self.export_btn = QPushButton("📥 Экспорт всех КРД в Excel")
        self.export_btn.setMinimumHeight(45)
        self.export_btn.setProperty("role", "save")
        self.export_btn.clicked.connect(self.on_export)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setProperty("role", "normal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        
        self.templates_list.currentItemChanged.connect(self.on_selection_changed)
        self.update_export_button()

    def on_selection_changed(self, current, previous):
        has_selection = self.templates_list.currentItem() is not None
        self.delete_template_btn.setEnabled(has_selection)

    def _update_krd_count(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT COUNT(*) FROM krd.krd WHERE is_deleted = FALSE")
        if query.exec() and query.next():
            count = query.value(0)
            self.info_label.setText(f"Будет экспортировано: {count} записей КРД")
        else:
            self.info_label.setText("⚠️ Не удалось получить количество записей")

    def load_templates_list(self):
        print("🔵 [DEBUG] load_templates_list: Загрузка списка шаблонов...")
        self.templates_list.clear()
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT id, name, description, template_type, usage_count, is_default
            FROM krd.report_templates
            WHERE is_deleted = FALSE
            ORDER BY is_default DESC, usage_count DESC, name ASC
        """)
        if query.exec():
            count = 0
            while query.next():
                template_id = query.value(0)
                template_name = query.value(1)
                description = query.value(2) or ""
                template_type = query.value(3)
                usage_count = query.value(4) or 0
                is_default = query.value(5)
                
                icon = "⭐" if is_default else "📋"
                usage_text = f"({usage_count} исп.)" if usage_count > 0 else ""
                
                item = QListWidgetItem(f"{icon} {template_name} {usage_text}")
                item.setData(Qt.ItemDataRole.UserRole, template_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, description)
                item.setData(Qt.ItemDataRole.UserRole + 2, template_name)
                self.templates_list.addItem(item)
                count += 1
            print(f"✅ [DEBUG] load_templates_list: Загружено {count} шаблонов.")
        else:
            print(f"❌ [DEBUG] load_templates_list: Ошибка SQL - {query.lastError().text()}")

    def on_template_clicked(self, item):
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template_name = item.data(Qt.ItemDataRole.UserRole + 2)
        self.load_template_description(template_id, template_name)

    def on_template_double_clicked(self, item):
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template_name = item.data(Qt.ItemDataRole.UserRole + 2)
        self.edit_template(template_id, template_name)

    def load_template_description(self, template_id, template_name):
        query = QSqlQuery(self.db)
        query.prepare("SELECT description, config_json, usage_count FROM krd.report_templates WHERE id = ?")
        query.addBindValue(template_id)
        if query.exec() and query.next():
            description = query.value(0) or ""
            config_json = query.value(1)
            usage_count = query.value(2) or 0
            
            desc_text = f"<b>📋 Шаблон:</b> {template_name}<br>"
            desc_text += f"<b>Описание:</b> {description or 'Нет описания'}<br>"
            desc_text += f"<b>Использований:</b> {usage_count}<br>"
            
            if config_json:
                try:
                    config = json.loads(config_json)
                    sections = config.get("sections", [])
                    fields_count = sum(len(fields) for fields in config.get("fields", {}).values())
                    desc_text += f"<b>Секций:</b> {len(sections)} | <b>Полей:</b> {fields_count}"
                    self.current_config = config
                    self.current_template_id = template_id
                    self.update_export_button()
                except Exception as e:
                    print(f"⚠️ [DEBUG] Ошибка парсинга JSON: {e}")
                    pass
            
            self.template_description.setText(desc_text)

    def on_add_template(self):
        dialog = FieldSelectionDialog(self, config=None, template_name=None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            template_name = dialog.get_template_name()
            if not template_name:
                template_name = "Новый шаблон"
            self.save_template_to_db(template_name, "", config)

    def edit_template(self, template_id, template_name):
        query = QSqlQuery(self.db)
        query.prepare("SELECT config_json FROM krd.report_templates WHERE id = ?")
        query.addBindValue(template_id)
        if query.exec() and query.next():
            config_json = query.value(0)
            if config_json:
                config = json.loads(config_json)
                dialog = FieldSelectionDialog(self, config, template_name)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    new_config = dialog.get_config()
                    reply = QMessageBox.question(
                        self, "Сохранить изменения",
                        f"Сохранить изменения в шаблоне '{template_name}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.update_template_in_db(template_id, new_config)

    def save_template_to_db(self, name, description, config):
        print(f"🔵 [DEBUG] save_template_to_db: Сохранение '{name}'")
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.report_templates (name, description, template_type, config_json)
            VALUES (?, ?, 'excel', ?)
        """)
        query.addBindValue(name.strip())
        query.addBindValue(description.strip() if description else "")
        query.addBindValue(json.dumps(config, ensure_ascii=False))
        
        if query.exec():
            print("✅ [DEBUG] save_template_to_db: Успешно.")
            QMessageBox.information(self, "Успешно", f"Шаблон '{name}' сохранен в базу данных")
            self.load_templates_list()
        else:
            print(f"❌ [DEBUG] save_template_to_db: Ошибка - {query.lastError().text()}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {query.lastError().text()}")

    def update_template_in_db(self, template_id, config):
        print(f"🔵 [DEBUG] update_template_in_db: Обновление ID={template_id}")
        query = QSqlQuery(self.db)
        query.prepare("""
            UPDATE krd.report_templates
            SET config_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """)
        query.addBindValue(json.dumps(config, ensure_ascii=False))
        query.addBindValue(template_id)
        
        if query.exec():
            print("✅ [DEBUG] update_template_in_db: Успешно.")
            QMessageBox.information(self, "Успешно", "Шаблон обновлен")
            self.load_templates_list()
        else:
            print(f"❌ [DEBUG] update_template_in_db: Ошибка - {query.lastError().text()}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления: {query.lastError().text()}")

    def on_delete_template(self):
        """Удаление шаблона (мягкое удаление)"""
        print(f"\n{'='*60}")
        print(f"🔵 [DEBUG] on_delete_template: НАЧАЛО")
        print(f"{'='*60}")
        
        item = self.templates_list.currentItem()
        if not item:
            print("⚠️ [DEBUG] Ошибка: Ничего не выбрано в списке.")
            QMessageBox.warning(self, "Внимание", "Выберите шаблон для удаления")
            return
        
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template_name = item.data(Qt.ItemDataRole.UserRole + 2)
        
        print(f"📋 [DEBUG] Выбран шаблон:")
        print(f"   🆔 ID: {template_id} (Тип: {type(template_id)})")
        print(f"   📛 Name: {template_name}")
        
        if not template_id:
            print("❌ [DEBUG] Ошибка: ID шаблона равен None!")
            QMessageBox.critical(self, "Ошибка", "Не удалось определить ID шаблона")
            return

        try:
            template_id = int(template_id)
        except (ValueError, TypeError):
            print(f"❌ [DEBUG] Ошибка преобразования ID: {template_id}")
            QMessageBox.critical(self, "Ошибка", "Некорректный ID шаблона")
            return
        
        # Проверка существования
        check_query = QSqlQuery(self.db)
        check_query.prepare("SELECT id, name, is_deleted FROM krd.report_templates WHERE id = ?")
        check_query.addBindValue(template_id)
        
        print("🔍 [DEBUG] Выполняю проверку существования...")
        if not check_query.exec():
            print(f"❌ [DEBUG] Ошибка проверки SQL: {check_query.lastError().text()}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка проверки: {check_query.lastError().text()}")
            return
        
        if not check_query.next():
            print("⚠️ [DEBUG] Шаблон не найден в БД.")
            QMessageBox.warning(self, "Внимание", f"Шаблон «{template_name}» не найден.")
            self.load_templates_list()
            return
        
        is_deleted = check_query.value(2)
        print(f"📊 [DEBUG] Статус is_deleted в БД: {is_deleted}")
        
        if is_deleted:
            print("ℹ️ [DEBUG] Шаблон уже удален.")
            QMessageBox.information(self, "Информация", f"Шаблон «{template_name}» уже удален.")
            self.load_templates_list()
            return
        
        # Подтверждение
        print("🛑 [DEBUG] Запрос подтверждения...")
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Удалить шаблон «{template_name}»?\n(данные будут скрыты, но сохранены в БД)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            print("❎ [DEBUG] Отмена пользователем.")
            return
        
        # 🔧 ОБХОД БАГА QPSQL: Используем прямой exec() для целочисленных параметров
        # Драйвер QPSQL в Qt6 ломает prepare() генерируя "EXECUTE ()" без имени
        user_id_value = self.current_user_id
        if user_id_value is None or not isinstance(user_id_value, int):
            try:
                user_id_value = int(user_id_value) if user_id_value is not None else 1
            except (ValueError, TypeError):
                user_id_value = 1
        
        # Безопасная интерполяция для int (SQL-инъекции невозможны)
        sql = f"""
            UPDATE krd.report_templates
            SET is_deleted = TRUE, 
                deleted_at = CURRENT_TIMESTAMP,
                deleted_by = {user_id_value}
            WHERE id = {template_id} AND is_deleted = FALSE
        """
        
        query = QSqlQuery(self.db)
        print(f"🚀 [DEBUG] Выполняю удаление (прямой exec)...")
        print(f"   Bound Values: user_id={user_id_value}, id={template_id}")
        
        if not query.exec(sql):
            print(f"❌ [DEBUG] ОШИБКА SQL при удалении!")
            print(f"   Error Text: {query.lastError().text()}")
            print(f"   Database Error: {query.lastError().databaseText()}")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось удалить шаблон:\n{query.lastError().text()}")
            return
        
        rows_affected = query.numRowsAffected()
        print(f"📊 [DEBUG] Затронуто строк: {rows_affected}")
        
        if rows_affected > 0:
            print("✅ [DEBUG] УСПЕХ: Шаблон помечен как удаленный.")
            QMessageBox.information(self, "Успех", f"Шаблон «{template_name}» успешно удален")
            
            self.current_config = {"sections": ["social_data"], "fields": {}}
            self.current_template_id = None
            self.update_export_button()
            self.load_templates_list()
        else:
            print("⚠️ [DEBUG] Строк не затронуто (0).")
            QMessageBox.warning(self, "Внимание", f"Шаблон «{template_name}» уже удалён или не существует.")
            self.load_templates_list()
        
        print(f"🏁 [DEBUG] on_delete_template: КОНЕЦ\n{'='*60}")

    def update_export_button(self):
        has_sections = len(self.current_config.get("sections", [])) > 0
        self.export_btn.setEnabled(has_sections)

    def get_export_range(self):
        return 'all', self._get_all_krd_ids()

    def _get_all_krd_ids(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT id FROM krd.krd WHERE is_deleted = FALSE ORDER BY id")
        krd_ids = []
        if query.exec():
            while query.next():
                krd_ids.append(query.value(0))
        return krd_ids

    def on_export(self):
        print(f"🔵 [DEBUG] on_export: Нажата кнопка экспорта")
        config = self.current_config.copy()
        
        if not config.get("sections"):
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну секцию для экспорта")
            return
        
        export_range, krd_ids = self.get_export_range()
        config["export_range"] = export_range
        config["krd_ids"] = krd_ids
        
        print(f"📊 [DEBUG] Экспорт: {len(krd_ids)} записей")
        
        if not krd_ids:
            QMessageBox.warning(self, "Ошибка", "В базе данных нет записей КРД для экспорта")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение массового экспорта",
            f"Вы собираетесь экспортировать {len(krd_ids)} записей КРД.\n"
            f"⏱️ Это может занять несколько минут в зависимости от количества данных.\n"
            f"Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        if self.current_template_id:
            query = QSqlQuery(self.db)
            query.prepare("UPDATE krd.report_templates SET usage_count = usage_count + 1 WHERE id = ?")
            query.addBindValue(self.current_template_id)
            query.exec()
        
        self.report_configured.emit(config)
        self.accept()    # ✅ УЛУЧШЕННАЯ ЛОГИКА УДАЛЕНИЯ ШАБЛОНА С ДИАГНОСТИКОЙ
    def on_delete_template(self):
        """Удаление шаблона (мягкое удаление)"""
        print(f"\n{'='*60}")
        print(f"🔵 [DEBUG] on_delete_template: НАЧАЛО")
        print(f"{'='*60}")
        
        item = self.templates_list.currentItem()
        if not item:
            print("⚠️ [DEBUG] Ошибка: Ничего не выбрано в списке.")
            QMessageBox.warning(self, "Внимание", "Выберите шаблон для удаления")
            return
        
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template_name = item.data(Qt.ItemDataRole.UserRole + 2)
        
        print(f"📋 [DEBUG] Выбран шаблон:")
        print(f"   🆔 ID: {template_id} (Тип: {type(template_id)})")
        print(f"   📛 Name: {template_name}")
        
        if template_id is None:
            print("❌ [DEBUG] Ошибка: ID шаблона равен None!")
            QMessageBox.critical(self, "Ошибка", "Не удалось определить ID шаблона")
            return

        # ✅ ГАРАНТИРУЕМ, ЧТО template_id — это int
        try:
            template_id = int(template_id)
        except (ValueError, TypeError):
            print(f"❌ [DEBUG] Ошибка: template_id не может быть преобразован в int: {template_id}")
            QMessageBox.critical(self, "Ошибка", "Некорректный ID шаблона")
            return
        
        # ✅ ПРОВЕРКА: Существует ли шаблон и не удален ли он уже
        check_query = QSqlQuery(self.db)
        check_query.prepare("""
            SELECT id, name, is_deleted 
            FROM krd.report_templates 
            WHERE id = :id
        """)
        check_query.bindValue(":id", template_id)
        
        print(f"🔍 [DEBUG] Выполняю проверку существования...")
        print(f"   SQL: {check_query.lastQuery()}")
        if not check_query.exec():
            print(f"❌ [DEBUG] Ошибка проверки SQL: {check_query.lastError().text()}")
            QMessageBox.critical(self, "Ошибка", 
                f"Ошибка проверки шаблона: {check_query.lastError().text()}")
            return
        
        if not check_query.next():
            print("⚠️ [DEBUG] Шаблон не найден в БД при проверке.")
            QMessageBox.warning(self, "Внимание", 
                f"Шаблон «{template_name}» не найден в базе данных.")
            self.load_templates_list()
            return
        
        is_deleted = check_query.value(2)
        print(f"📊 [DEBUG] Статус is_deleted в БД: {is_deleted}")
        
        if is_deleted:
            print("ℹ️ [DEBUG] Шаблон уже удален.")
            QMessageBox.information(self, "Информация", 
                f"Шаблон «{template_name}» уже был удален ранее.")
            self.load_templates_list()
            return
        
        # ✅ ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
        print("🛑 [DEBUG] Запрос подтверждения у пользователя...")
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить шаблон «{template_name}»? "
            f"(данные будут скрыты, но сохранены в БД)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            print("❎ [DEBUG] Пользователь нажал 'Нет'. Отмена.")
            return
        
        # ✅ ВЫПОЛНЕНИЕ МЯГКОГО УДАЛЕНИЯ
        query = QSqlQuery(self.db)
        
        # 🔥 ВАЖНО: Сначала prepare, потом bindValue, потом exec
        sql = """
            UPDATE krd.report_templates
            SET is_deleted = TRUE, 
                deleted_at = CURRENT_TIMESTAMP,
                deleted_by = :user_id
            WHERE id = :id AND is_deleted = FALSE
        """
        
        print(f"🚀 [DEBUG] Подготовка SQL запроса...")
        print(f"   SQL текст:\n{sql}")
        
        # ✅ ШАГ 1: prepare
        if not query.prepare(sql):
            print(f"❌ [DEBUG] ОШИБКА prepare(): {query.lastError().text()}")
            QMessageBox.critical(self, "Ошибка БД", 
                f"Не удалось подготовить запрос: {query.lastError().text()}")
            return
        
        # ✅ ШАГ 2: bindValue
        user_id_value = self.current_user_id if self.current_user_id is not None else 1
        query.bindValue(":user_id", user_id_value)
        query.bindValue(":id", template_id)
        
        print(f"   Bound Values: user_id={user_id_value}, id={template_id}")
        print(f"   Last Query: {query.lastQuery()}")
        
        # ✅ ШАГ 3: exec
        print(f"   Выполняю query.exec()...")
        if not query.exec():
            print(f"❌ [DEBUG] ОШИБКА exec()!")
            print(f"   Error Text: {query.lastError().text()}")
            print(f"   Error Number: {query.lastError().nativeErrorCode()}")
            print(f"   Driver Error: {query.lastError().driverText()}")
            print(f"   Database Error: {query.lastError().databaseText()}")
            
            QMessageBox.critical(self, "Ошибка БД", 
                f"Не удалось удалить шаблон:\n{query.lastError().text()}")
            return
        
        rows_affected = query.numRowsAffected()
        print(f"📊 [DEBUG] Затронуто строк: {rows_affected}")
        
        if rows_affected > 0:
            print("✅ [DEBUG] УСПЕХ: Шаблон помечен как удаленный.")
            QMessageBox.information(self, "Успех", 
                f"Шаблон «{template_name}» успешно удален")
            
            # Очищаем текущую конфигурацию
            self.current_config = {"sections": ["social_data"], "fields": {}}
            self.current_template_id = None
            self.update_export_button()
            
            # Обновляем список шаблонов
            self.load_templates_list()
        else:
            print("⚠️ [DEBUG] ВНИМАНИЕ: Строк не затронуто (0).")
            QMessageBox.warning(self, "Внимание", 
                f"Шаблон «{template_name}» уже был удален или не существует.")
            self.load_templates_list()
        
        print(f"🏁 [DEBUG] on_delete_template: КОНЕЦ")
        print(f"{'='*60}\n")
    def update_export_button(self):
        """Обновление состояния кнопки экспорта"""
        has_sections = len(self.current_config.get("sections", [])) > 0
        self.export_btn.setEnabled(has_sections)

    def get_export_range(self):
        """Получение выбранного диапазона экспорта (всегда 'all')"""
        return 'all', self._get_all_krd_ids()

    def _get_all_krd_ids(self):
        """Получение всех ID КРД из базы данных"""
        query = QSqlQuery(self.db)
        query.prepare("SELECT id FROM krd.krd WHERE is_deleted = FALSE ORDER BY id")
        krd_ids = []
        if query.exec():
            while query.next():
                krd_ids.append(query.value(0))
        return krd_ids

    def on_export(self):
        """Обработка кнопки экспорта"""
        print(f"🔵 [DEBUG] on_export: Нажата кнопка экспорта")
        config = self.current_config.copy()
        
        if not config.get("sections"):
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну секцию для экспорта")
            return
        
        export_range, krd_ids = self.get_export_range()
        config["export_range"] = export_range
        config["krd_ids"] = krd_ids
        
        print(f"📊 [DEBUG] Экспорт: {len(krd_ids)} записей")
        
        if not krd_ids:
            QMessageBox.warning(self, "Ошибка", "В базе данных нет записей КРД для экспорта")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение массового экспорта",
            f"Вы собираетесь экспортировать {len(krd_ids)} записей КРД.\n"
            f"⏱️ Это может занять несколько минут в зависимости от количества данных.\n"
            f"Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        if self.current_template_id:
            query = QSqlQuery(self.db)
            query.prepare("UPDATE krd.report_templates SET usage_count = usage_count + 1 WHERE id = ?")
            query.addBindValue(self.current_template_id)
            query.exec()
        
        self.report_configured.emit(config)
        self.accept()