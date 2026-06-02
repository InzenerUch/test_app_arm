from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit,
    QMessageBox, QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont
import traceback
class RecordViewDialog(QDialog):
    def __init__(self, db, record_type, record_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.record_type = record_type
        self.record_id = record_id
        self.record_data = {}
        self.setWindowTitle("📋 Просмотр записи")
        self.setMinimumSize(800, 650)
        self.setModal(True)
        self.init_ui()
        self.load_record_data()
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        title_label = QLabel("📋 Информация о записи")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        container = QWidget()
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setSpacing(10)
        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        button_layout = QHBoxLayout()
        self.restore_btn = QPushButton("♻️ Восстановить запись")
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color:
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color:
            }
            QPushButton {
                background-color:
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color:
            }
        Добавление поля в форму
        ✅ ИСПРАВЛЕНО: Поддержка как QVBoxLayout, так и QGridLayout
                QTextEdit {
                    background-color:
                    border: 1px solid
                    border-radius: 3px;
                    padding: 5px;
                }
                QLineEdit {
                    background-color:
                    border: 1px solid
                    border-radius: 3px;
                    padding: 5px;
                }
Загрузка данных записи в зависимости от типа"""
        try:
            if self.record_type in ["krd", "КРД"]:
                self._load_krd_data()
            elif self.record_type in ["templates", "Шаблон"]:
                self._load_template_data()
            elif self.record_type in ["requests", "Запрос"]:
                self._load_request_data()
            else:
                QMessageBox.warning(self, "Ошибка", f"Неизвестный тип записи: {self.record_type}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных:\n{str(e)}")
    def _load_krd_data(self):
        self.setWindowTitle(f"📋 Просмотр КРД-{self.record_id}")
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT
                k.id,
                CONCAT('КРД-', k.id),
                COALESCE(s.surname, ''),
                COALESCE(s.name, ''),
                COALESCE(s.patronymic, ''),
                s.birth_date,
                s.birth_place_town,
                s.personal_number,
                s.tab_number,
                COALESCE(c.name, ''),
                COALESCE(r.name, ''),
                k.deleted_at,
                COALESCE(u.username, 'Неизвестно')
            FROM krd.krd k
            LEFT JOIN krd.social_data s ON k.id = s.krd_id
            LEFT JOIN krd.categories c ON s.category_id = c.id
            LEFT JOIN krd.ranks r ON s.rank_id = r.id
            LEFT JOIN krd.users u ON k.deleted_by = u.id
            WHERE k.id = ?
Загрузка данных шаблона"""
        self.setWindowTitle(f"📋 Просмотр шаблона (ID={self.record_id})")
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT
                id,
                name,
                COALESCE(description, ''),
                created_at,
                updated_at,
                deleted_at,
                COALESCE(u.username, 'Неизвестно'),
                LENGTH(template_data)
            FROM krd.document_templates
            LEFT JOIN krd.users u ON deleted_by = u.id
            WHERE id = ?
Загрузка данных запроса"""
        self.setWindowTitle(f"📋 Просмотр запроса (ID={self.record_id})")
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT
                o.id,
                o.issue_number,
                COALESCE(rt.name, 'Не указан'),
                COALESCE(r.name, 'Не указан'),
                o.issue_date,
                o.request_text,
                o.signed_by_position,
                o.deleted_at,
                COALESCE(u.username, 'Неизвестно'),
                LENGTH(o.document_data)
            FROM krd.outgoing_requests o
            LEFT JOIN krd.request_types rt ON o.request_type_id = rt.id
            LEFT JOIN krd.recipients r ON o.recipient_id = r.id
            LEFT JOIN krd.users u ON o.deleted_by = u.id
            WHERE o.id = ?
Восстановление записи"""
        record_name = self.windowTitle().replace("📋 Просмотр ", "")
        reply = QMessageBox.question(
            self,
            "Подтверждение восстановления",
            f"Вы действительно хотите восстановить запись?\n\n{record_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.record_type in ["krd", "КРД"]:
                    table = "krd.krd"
                elif self.record_type in ["templates", "Шаблон"]:
                    table = "krd.document_templates"
                elif self.record_type in ["requests", "Запрос"]:
                    table = "krd.outgoing_requests"
                else:
                    QMessageBox.warning(self, "Ошибка", "Неизвестный тип записи")
                    return
                query = QSqlQuery(self.db)
                query.prepare(f"""
                    UPDATE {table}
                    SET is_deleted = FALSE,
                        deleted_at = NULL,
                        deleted_by = NULL
                    WHERE id = ?
                """)
                query.addBindValue(self.record_id)
                if query.exec() and query.numRowsAffected() > 0:
                    QMessageBox.information(
                        self,
                        "Успех",
                        f"Запись \"{record_name}\" успешно восстановлена!"
                    )
                    self.accept()
                    if self.parent() and hasattr(self.parent(), 'load_deleted_records'):
                        self.parent().load_deleted_records()
                else:
                    raise Exception("Запись не найдена или уже восстановлена")
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Ошибка при восстановлении записи:\n{str(e)}"
                )