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
        info_label.setStyleSheet("QLabel { font-size: 11px; color:
        info_layout.addWidget(info_label)
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("QLabel { color:
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)
        templates_group = QGroupBox("📋 Шаблоны отчетов")
        templates_layout = QVBoxLayout(templates_group)
        self.templates_list = QListWidget()
        self.templates_list.setMinimumHeight(200)
        self.templates_list.itemClicked.connect(self.on_template_clicked)
        self.templates_list.itemDoubleClicked.connect(self.on_template_double_clicked)
        self.templates_list.setStyleSheet("""
            QListWidget {
                border: 1px solid
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid
            }
            QListWidget::item:selected {
                background-color:
                color: white;
            }
            QListWidget::item:hover {
                background-color:
            }
Активация кнопки удаления при выборе шаблона"""
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
Обработка клика на шаблон в списке"""
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
                        self,
                        "Сохранить изменения",
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
            VALUES (:name, :desc, 'excel', :config)
Обновление шаблона в БД"""
        print(f"🔵 [DEBUG] update_template_in_db: Обновление ID={template_id}")
        query = QSqlQuery(self.db)
        query.prepare("""
            UPDATE krd.report_templates
            SET config_json = :config, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
Диалог конфигурации отчета КРД с хранением шаблонов в БД
Поддерживает только массовый экспорт всех записей на один лист Excel
✅ ИСПРАВЛЕНО: Обход бага QPSQL драйвера (EXECUTE syntax error)
✅ ИСПРАВЛЕНО: QMessageBox.StandardButton для PyQt6
✅ ИСПРАВЛЕНО: Унифицированы все SQL-запросы на ? + addBindValue()
✅ ИСПРАВЛЕНО: Безопасная обработка ID и User ID
Диалог настройки конфигурации отчета с БД (только массовый экспорт)"""
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
        info_label.setStyleSheet("QLabel { font-size: 11px; color:
        info_layout.addWidget(info_label)
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("QLabel { color:
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)
        templates_group = QGroupBox("📋 Шаблоны отчетов")
        templates_layout = QVBoxLayout(templates_group)
        self.templates_list = QListWidget()
        self.templates_list.setMinimumHeight(200)
        self.templates_list.itemClicked.connect(self.on_template_clicked)
        self.templates_list.itemDoubleClicked.connect(self.on_template_double_clicked)
        self.templates_list.setStyleSheet("""
            QListWidget {
                border: 1px solid
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid
            }
            QListWidget::item:selected {
                background-color:
                color: white;
            }
            QListWidget::item:hover {
                background-color:
            }
            SELECT id, name, description, template_type, usage_count, is_default
            FROM krd.report_templates
            WHERE is_deleted = FALSE
            ORDER BY is_default DESC, usage_count DESC, name ASC
            INSERT INTO krd.report_templates (name, description, template_type, config_json)
            VALUES (?, ?, 'excel', ?)
            UPDATE krd.report_templates
            SET config_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
Удаление шаблона (мягкое удаление)"""
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
        user_id_value = self.current_user_id
        if user_id_value is None or not isinstance(user_id_value, int):
            try:
                user_id_value = int(user_id_value) if user_id_value is not None else 1
            except (ValueError, TypeError):
                user_id_value = 1
        sql = f"""
            UPDATE krd.report_templates
            SET is_deleted = TRUE,
                deleted_at = CURRENT_TIMESTAMP,
                deleted_by = {user_id_value}
            WHERE id = {template_id} AND is_deleted = FALSE
Удаление шаблона (мягкое удаление)"""
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
        try:
            template_id = int(template_id)
        except (ValueError, TypeError):
            print(f"❌ [DEBUG] Ошибка: template_id не может быть преобразован в int: {template_id}")
            QMessageBox.critical(self, "Ошибка", "Некорректный ID шаблона")
            return
        check_query = QSqlQuery(self.db)
        check_query.prepare("""
            SELECT id, name, is_deleted
            FROM krd.report_templates
            WHERE id = :id
            UPDATE krd.report_templates
            SET is_deleted = TRUE,
                deleted_at = CURRENT_TIMESTAMP,
                deleted_by = :user_id
            WHERE id = :id AND is_deleted = FALSE
Обновление состояния кнопки экспорта"""
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