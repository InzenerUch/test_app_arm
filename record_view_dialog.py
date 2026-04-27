"""
Диалог просмотра записей с возможностью восстановления
✅ Вынесен в отдельный модуль для переиспользования
✅ Поддерживает КРД, Шаблоны и Запросы
✅ ИСПРАВЛЕНО: Корректная работа с QGridLayout
"""
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
    """
    Универсальный диалог просмотра записей
    Поддерживает: krd, templates, requests
    """
    
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
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("📋 Информация о записи")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title_label)
        
        # Область прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setSpacing(10)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.restore_btn = QPushButton("♻️ Восстановить запись")
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.restore_btn.clicked.connect(self.restore_record)
        button_layout.addWidget(self.restore_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def _add_field(self, layout, label_text, value, multiline=False, row=None):
        """
        Добавление поля в форму
        ✅ ИСПРАВЛЕНО: Поддержка как QVBoxLayout, так и QGridLayout
        """
        field_layout = QHBoxLayout()
        
        label = QLabel(f"{label_text}:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        label.setMinimumWidth(200)
        field_layout.addWidget(label)
        
        if multiline:
            value_widget = QTextEdit()
            value_widget.setPlainText(str(value) if value else "")
            value_widget.setReadOnly(True)
            value_widget.setMaximumHeight(80)
            value_widget.setStyleSheet("""
                QTextEdit {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    padding: 5px;
                }
            """)
        else:
            value_widget = QLineEdit()
            value_widget.setText(str(value) if value else "")
            value_widget.setReadOnly(True)
            value_widget.setStyleSheet("""
                QLineEdit {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    padding: 5px;
                }
            """)
        
        field_layout.addWidget(value_widget, 1)
        
        # ✅ ИСПРАВЛЕНО: Проверяем тип layout
        if isinstance(layout, QGridLayout) and row is not None:
            layout.addLayout(field_layout, row, 0)
        else:
            layout.addLayout(field_layout)
    
    def load_record_data(self):
        """Загрузка данных записи в зависимости от типа"""
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
        """Загрузка данных КРД"""
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
        """)
        query.addBindValue(self.record_id)
        
        if not query.exec() or not query.next():
            raise Exception("Запись КРД не найдена")
        
        # Группа: Основная информация
        group1 = QGroupBox("📋 Основная информация")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout1 = QVBoxLayout()  # ✅ ИСПРАВЛЕНО: Используем QVBoxLayout
        group1.setLayout(layout1)
        
        row = 0
        self._add_field(layout1, "ID КРД", query.value(0), row=row)
        self._add_field(layout1, "Номер КРД", query.value(1), row=row)
        self._add_field(layout1, "Фамилия", query.value(2), row=row)
        self._add_field(layout1, "Имя", query.value(3), row=row)
        self._add_field(layout1, "Отчество", query.value(4), row=row)
        self._add_field(layout1, "Дата рождения", query.value(5), row=row)
        self._add_field(layout1, "Место рождения", query.value(6), row=row)
        self._add_field(layout1, "Личный номер", query.value(7), row=row)
        self._add_field(layout1, "Табельный номер", query.value(8), row=row)
        self._add_field(layout1, "Категория", query.value(9), row=row)
        self._add_field(layout1, "Звание", query.value(10), row=row)
        
        self.content_layout.addWidget(group1)
        
        # Группа: Информация об удалении
        group2 = QGroupBox("🗑️ Информация об удалении")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout2 = QVBoxLayout()  # ✅ ИСПРАВЛЕНО: Используем QVBoxLayout
        group2.setLayout(layout2)
        
        self._add_field(layout2, "Дата удаления", query.value(11), row=row)
        self._add_field(layout2, "Удалил пользователь", query.value(12), row=row)
        
        self.content_layout.addWidget(group2)
        self.content_layout.addStretch()
    
    def _load_template_data(self):
        """Загрузка данных шаблона"""
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
        """)
        query.addBindValue(self.record_id)
        
        if not query.exec() or not query.next():
            raise Exception("Шаблон не найден")
        
        # Группа: Основная информация
        group1 = QGroupBox("📄 Информация о шаблоне")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout1 = QVBoxLayout()  # ✅ ИСПРАВЛЕНО: Используем QVBoxLayout
        group1.setLayout(layout1)
        
        self._add_field(layout1, "ID шаблона", query.value(0), row=0)
        self._add_field(layout1, "Название", query.value(1), row=0)
        self._add_field(layout1, "Описание", query.value(2), multiline=True, row=0)
        self._add_field(layout1, "Дата создания", query.value(3), row=0)
        self._add_field(layout1, "Дата обновления", query.value(4), row=0)
        self._add_field(layout1, "Размер файла", f"{query.value(7)} байт", row=0)
        
        self.content_layout.addWidget(group1)
        
        # Группа: Информация об удалении
        group2 = QGroupBox("🗑️ Информация об удалении")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout2 = QVBoxLayout()  # ✅ ИСПРАВЛЕНО: Используем QVBoxLayout
        group2.setLayout(layout2)
        
        self._add_field(layout2, "Дата удаления", query.value(5), row=0)
        self._add_field(layout2, "Удалил пользователь", query.value(6), row=0)
        
        self.content_layout.addWidget(group2)
        self.content_layout.addStretch()
    
    def _load_request_data(self):
        """Загрузка данных запроса"""
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
        """)
        query.addBindValue(self.record_id)
        
        if not query.exec() or not query.next():
            raise Exception("Запрос не найден")
        
        # Группа: Основная информация
        group1 = QGroupBox("📤 Информация о запросе")
        group1.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout1 = QVBoxLayout()  # ✅ ИСПРАВЛЕНО: Используем QVBoxLayout
        group1.setLayout(layout1)
        
        self._add_field(layout1, "ID запроса", query.value(0), row=0)
        self._add_field(layout1, "Номер запроса", query.value(1), row=0)
        self._add_field(layout1, "Тип запроса", query.value(2), row=0)
        self._add_field(layout1, "Адресат", query.value(3), row=0)
        self._add_field(layout1, "Дата запроса", query.value(4), row=0)
        self._add_field(layout1, "Текст запроса", query.value(5), multiline=True, row=0)
        self._add_field(layout1, "Должность подписанта", query.value(6), row=0)
        self._add_field(layout1, "Размер документа", f"{query.value(9)} байт", row=0)
        
        self.content_layout.addWidget(group1)
        
        # Группа: Информация об удалении
        group2 = QGroupBox("🗑️ Информация об удалении")
        group2.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout2 = QVBoxLayout()  # ✅ ИСПРАВЛЕНО: Используем QVBoxLayout
        group2.setLayout(layout2)
        
        self._add_field(layout2, "Дата удаления", query.value(7), row=0)
        self._add_field(layout2, "Удалил пользователь", query.value(8), row=0)
        
        self.content_layout.addWidget(group2)
        self.content_layout.addStretch()
    
    def restore_record(self):
        """Восстановление записи"""
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
                    # Обновляем список в родительском окне
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