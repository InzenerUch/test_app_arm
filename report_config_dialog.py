"""
Диалог конфигурации отчета КРД с хранением шаблонов в БД.
Поддерживает только массовый экспорт всех записей на один лист Excel.
✅ ИСПРАВЛЕНО: Экспорт выполняется ПРЯМО ЗДЕСЬ, без передачи сигналов в MainWindow.
✅ ИСПРАВЛЕНО: QMessageBox.StandardButton для PyQt6
✅ ИСПРАВЛЕНО: Унифицированы все SQL-запросы на именованные параметры (:name)
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QMessageBox, QFileDialog, QProgressDialog, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from PyQt6.QtSql import QSqlQuery
import json
import traceback

from field_selection_dialog import FieldSelectionDialog
from export_helper import KrdExcelExporter  # ✅ Импортируем экспортер
from ui_helpers import BaseDialog


class ReportConfigDialog(BaseDialog):
    """Диалог настройки конфигурации отчета с БД (только массовый-export)"""
    
    def __init__(self, db_connection, parent=None, template_id=None, audit_logger=None):
        super().__init__(parent)
        self.setWindowTitle("Генерация отчета по всем КРД")
        self.setMinimumSize(700, 650)
        self.db = db_connection
        self.template_id = template_id
        self.audit_logger = audit_logger  # ✅ Сохраняем логгер для записи действия
        
        self.current_config = {
            "sections": ["social_data"],
            "fields": {}
        }
        self.current_template_id = None
        
        if parent and hasattr(parent, 'user_info') and isinstance(parent.user_info, dict):
            self.current_user_id = parent.user_info.get('id')
        else:
            self.current_user_id = None
            
        print(f"🔵 [DEBUG] Инициализация ReportConfigDialog. User ID: {self.current_user_id}")
        
        self.init_ui()
        self.load_templates_list()
        self._update_krd_count()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        info_group = QGroupBox("📊 Режим экспорта")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel("Экспорт всех записей КРД из базы данных на ОДИН лист Excel")
        info_label.setStyleSheet("QLabel { font-size: 11px; color: #666; }")
        info_layout.addWidget(info_label)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("QLabel { color: #2196F3; padding: 5px; border-radius: 3px; font-weight: bold; }")
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)

        templates_group = QGroupBox("📋 Шаблоны отчетов")
        templates_layout = QVBoxLayout(templates_group)
        
        self.templates_list = QListWidget()
        self.templates_list.setMinimumHeight(200)
        self.templates_list.itemClicked.connect(self.on_template_clicked)
        self.templates_list.itemDoubleClicked.connect(self.on_template_double_clicked)
        self.templates_list.setStyleSheet("""
            QListWidget { border: 1px solid #ccc; border-radius: 5px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #eee; }
            QListWidget::item:selected { background-color: #2196F3; color: white; }
            QListWidget::item:hover { background-color: #e3f2fd; }
        """)
        templates_layout.addWidget(self.templates_list)
        
        self.template_description = QLabel("")
        self.template_description.setWordWrap(True)
        self.template_description.setStyleSheet("QLabel { padding: 10px; border-radius: 5px; color: #666; background-color: #f9f9f9; }")
        templates_layout.addWidget(self.template_description)
        layout.addWidget(templates_group)

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
        self.export_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
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

    def on_selection_changed(self, current, previous):
        has_selection = self.templates_list.currentItem() is not None
        self.delete_template_btn.setEnabled(has_selection)

    def _update_krd_count(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT COUNT(*) FROM krd.krd WHERE is_deleted = FALSE")
        if query.exec() and query.next():
            self.info_label.setText(f"Будет экспортировано: {query.value(0)} записей КРД")
        else:
            self.info_label.setText("⚠️ Не удалось получить количество записей")

    def load_templates_list(self):
        print("🔵 [DEBUG] load_templates_list: Загрузка списка шаблонов...")
        self.templates_list.clear()
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT id, name, description, template_type, usage_count, is_default
            FROM krd.report_templates WHERE is_deleted = FALSE
            ORDER BY is_default DESC, usage_count DESC, name ASC
        """)
        if query.exec():
            count = 0
            while query.next():
                template_id = query.value(0)
                template_name = query.value(1)
                description = query.value(2) or ""
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
        query.prepare("SELECT description, config_json, usage_count FROM krd.report_templates WHERE id = :id")
        query.bindValue(":id", template_id)
        
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
            self.template_description.setText(desc_text)

    def on_add_template(self):
        dialog = FieldSelectionDialog(self, config=None, template_name=None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            template_name = dialog.get_template_name() or "Новый шаблон"
            self.save_template_to_db(template_name, "", config)

    def edit_template(self, template_id, template_name):
        query = QSqlQuery(self.db)
        query.prepare("SELECT config_json FROM krd.report_templates WHERE id = :id")
        query.bindValue(":id", template_id)
        if query.exec() and query.next() and query.value(0):
            config = json.loads(query.value(0))
            dialog = FieldSelectionDialog(self, config, template_name)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                if QMessageBox.question(self, "Сохранить изменения", f"Сохранить изменения в шаблоне '{template_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    self.update_template_in_db(template_id, dialog.get_config())

    def save_template_to_db(self, name, description, config):
        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO krd.report_templates (name, description, template_type, config_json) VALUES (:name, :desc, 'excel', :config)")
        query.bindValue(":name", name.strip())
        query.bindValue(":desc", description.strip())
        query.bindValue(":config", json.dumps(config, ensure_ascii=False))
        if query.exec():
            QMessageBox.information(self, "Успешно", f"Шаблон '{name}' сохранен")
            self.load_templates_list()
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {query.lastError().text()}")

    def update_template_in_db(self, template_id, config):
        query = QSqlQuery(self.db)
        query.prepare("UPDATE krd.report_templates SET config_json = :config, updated_at = CURRENT_TIMESTAMP WHERE id = :id")
        query.bindValue(":config", json.dumps(config, ensure_ascii=False))
        query.bindValue(":id", template_id)
        if query.exec():
            QMessageBox.information(self, "Успешно", "Шаблон обновлен")
            self.load_templates_list()
        else:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обновления: {query.lastError().text()}")

    def on_delete_template(self):
        item = self.templates_list.currentItem()
        if not item: return
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template_name = item.data(Qt.ItemDataRole.UserRole + 2)
        
        try:
            template_id = int(template_id)
        except (ValueError, TypeError):
            return

        check_query = QSqlQuery(self.db)
        check_query.prepare("SELECT is_deleted FROM krd.report_templates WHERE id = :id")
        check_query.bindValue(":id", template_id)
        if check_query.exec() and check_query.next() and check_query.value(0):
            QMessageBox.information(self, "Информация", "Шаблон уже был удален ранее.")
            self.load_templates_list()
            return

        if QMessageBox.question(self, "Подтверждение удаления", f"Удалить шаблон «{template_name}»?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            query = QSqlQuery(self.db)
            query.prepare("UPDATE krd.report_templates SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP, deleted_by = :user_id WHERE id = :id AND is_deleted = FALSE")
            query.bindValue(":user_id", self.current_user_id or 1)
            query.bindValue(":id", template_id)
            if query.exec() and query.numRowsAffected() > 0:
                QMessageBox.information(self, "Успех", "Шаблон успешно удален")
                self.current_config = {"sections": ["social_data"], "fields": {}}
                self.current_template_id = None
                self.update_export_button()
                self.load_templates_list()

    def update_export_button(self):
        self.export_btn.setEnabled(len(self.current_config.get("sections", [])) > 0)

    def get_export_range(self):
        """Получение всех ID КРД из базы данных"""
        query = QSqlQuery(self.db)
        query.prepare("SELECT id FROM krd.krd WHERE is_deleted = FALSE ORDER BY id")
        
        krd_ids = []
        if query.exec():
            while query.next():
                krd_ids.append(query.value(0))
        else:
            print(f"❌ [DEBUG] Ошибка получения списка КРД: {query.lastError().text()}")
            
        return 'all', krd_ids

    # ========================================================================
    # ✅ ГЛАВНОЕ ИЗМЕНЕНИЕ: ЭКСПОРТ ВЫПОЛНЯЕТСЯ ПРЯМО ЗДЕСЬ
    # ========================================================================
    def on_export(self):
        print("🔵 [DEBUG] on_export: Нажата кнопка экспорта")
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
            f"Вы собираетесь экспортировать {len(krd_ids)} записей КРД.\nЭто может занять несколько минут.\nПродолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 1. Выбираем файл ПРЯМО ЗДЕСЬ
        default_filename = f"КРД_ВСЕ_отчет_{QDate.currentDate().toString('yyyy-MM-dd')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчеты по всем КРД", default_filename, "Excel файлы (*.xlsx);;Все файлы (*)"
        )
        
        if not file_path:
            print("⚠️ [DEBUG] Путь не выбран. Экспорт прерван.")
            return
            
        # 2. Обновляем счетчик шаблона
        if self.current_template_id:
            q = QSqlQuery(self.db)
            q.prepare("UPDATE krd.report_templates SET usage_count = usage_count + 1 WHERE id = :id")
            q.bindValue(":id", self.current_template_id)
            q.exec()
            
        # 3. Запускаем экспорт ПРЯМО ЗДЕСЬ
        try:
            print("⏳ [DEBUG] Показываю индикатор прогресса...")
            progress_msg = QProgressDialog("Генерация отчета...\nПожалуйста, подождите.", "Отмена", 0, 0, self)
            progress_msg.setWindowTitle("Генерация отчета")
            progress_msg.setWindowModality(Qt.WindowModality.WindowModal)
            progress_msg.show()
            QApplication.processEvents() # ✅ Критически важно для отрисовки прогресс-бара
            
            print("🔄 [DEBUG] Запускаю KrdExcelExporter...")
            exporter = KrdExcelExporter(self.db, report_config=config)
            exporter.export_multiple_krd_to_excel(file_path, krd_ids)
            
            progress_msg.close()
            
            # 4. Логируем действие (если логгер передан)
            if self.audit_logger:
                self.audit_logger.log_action('REPORT_EXPORT', 'krd', description=f'Экспорт {len(krd_ids)} КРД')
                
            QMessageBox.information(self, "Успешно", f"✅ Отчеты сохранены:\n📊 КРД: {len(krd_ids)}\n📁 {file_path}")
            
            # 5. Закрываем диалог ТОЛЬКО после успешного экспорта
            print("🟢 [DEBUG] Экспорт завершен, закрываю диалог (accept)...")
            self.accept()
            
        except Exception as e:
            progress_msg.close()
            print(f"❌ [DEBUG] КРИТИЧЕСКАЯ ОШИБКА экспорта: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"❌ Ошибка генерации:\n{str(e)}")
            # Диалог НЕ закрывается при ошибке, чтобы пользователь мог попробовать снова