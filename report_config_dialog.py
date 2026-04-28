"""
Диалог конфигурации отчета КРД с хранением шаблонов в БД
Поддерживает только массовый экспорт всех записей на один лист Excel
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
        
        # === ИСПРАВЛЕНО: Убран белый фон, оставлено синее выделение ===
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
        cancel_btn.setProperty("role", "danger")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.update_export_button()
    
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
        self.templates_list.clear()
        
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT id, name, description, template_type, usage_count, is_default
            FROM krd.report_templates 
            WHERE is_deleted = FALSE 
            ORDER BY is_default DESC, usage_count DESC, name ASC
        """)
        
        if query.exec():
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
                except:
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
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.report_templates (name, description, template_type, config_json)
            VALUES (:name, :desc, 'excel', :config)
        """)
        query.bindValue(":name", name.strip())
        query.bindValue(":desc", description.strip() if description else "")
        query.bindValue(":config", json.dumps(config, ensure_ascii=False))
        
        if query.exec():
            QMessageBox.information(self, "Успешно", f"Шаблон '{name}' сохранен в базу данных")
            self.load_templates_list()
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {query.lastError().text()}")
    
    def update_template_in_db(self, template_id, config):
        """Обновление шаблона в БД"""
        query = QSqlQuery(self.db)
        query.prepare("""
            UPDATE krd.report_templates 
            SET config_json = :config, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """)
        query.bindValue(":config", json.dumps(config, ensure_ascii=False))
        query.bindValue(":id", template_id)
        
        if query.exec():
            QMessageBox.information(self, "Успешно", "Шаблон обновлен")
            self.load_templates_list()
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления: {query.lastError().text()}")
    
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
        config = self.current_config.copy()
        
        if not config.get("sections"):
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну секцию для экспорта")
            return
        
        export_range, krd_ids = self.get_export_range()
        config["export_range"] = export_range
        config["krd_ids"] = krd_ids
        
        if not krd_ids:
            QMessageBox.warning(self, "Ошибка", "В базе данных нет записей КРД для экспорта")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение массового экспорта",
            f"Вы собираетесь экспортировать {len(krd_ids)} записей КРД.\n\n"
            f"⏱️ Это может занять несколько минут в зависимости от количества данных.\n\n"
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