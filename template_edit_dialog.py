"""
Диалог редактирования/добавления шаблона документа
✅ ИСПРАВЛЕНО: Убраны случайные логи из импортов, исправлен оператор if
✅ ИСПРАВЛЕНО: Именованные параметры (:name) для совместимости с PostgreSQL
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QPushButton, QTextEdit, QMessageBox, QFileDialog
)
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtCore import QByteArray

class TemplateEditDialog(QDialog):
    def __init__(self, db, template_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.template_id = template_id
        self.setWindowTitle("✏️ Редактирование шаблона" if template_id else "➕ Новый шаблон")
        self.setModal(True)
        self.resize(600, 450)
        self.selected_file_path = None
        self.current_file_bytes = None
        self.init_ui()
        if self.template_id:
            self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        layout.addWidget(QLabel("Название шаблона *:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Запрос в ЗАГС")
        layout.addWidget(self.name_input)
        
        layout.addWidget(QLabel("Описание:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setPlaceholderText("Краткое описание назначения шаблона...")
        layout.addWidget(self.desc_input)
        
        layout.addWidget(QLabel("Файл шаблона (.docx) *:"))
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл не выбран")
        self.file_label.setStyleSheet("QLabel { color: #666; padding: 5px; border: 1px dashed #ccc; background-color: #f9f9f9; }")
        file_layout.addWidget(self.file_label, 1)
        
        btn_layout = QVBoxLayout()
        self.choose_file_btn = QPushButton("📂 Выбрать файл")
        self.choose_file_btn.clicked.connect(self.choose_file)
        btn_layout.addWidget(self.choose_file_btn)
        
        self.download_file_btn = QPushButton("⬇️ Скачать")
        self.download_file_btn.clicked.connect(self.download_file)
        self.download_file_btn.setEnabled(False)
        btn_layout.addWidget(self.download_file_btn)
        file_layout.addLayout(btn_layout)
        layout.addLayout(file_layout)
        
        btn_box = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setProperty("role", "save") 
        save_btn.clicked.connect(self.save)
        
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setProperty("role", "danger")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)
        self.setLayout(layout)

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл шаблона", "", "Word документы (*.docx)")
        if path:
            self.selected_file_path = path
            size = os.path.getsize(path)
            self.file_label.setText(f"✅ {os.path.basename(path)} ({size} байт)")
            self.file_label.setStyleSheet("QLabel { color: green; font-weight: bold; background-color: #e8f5e9; padding: 5px; border: 1px solid #4CAF50; }")
            self.download_file_btn.setEnabled(False)

    def download_file(self):
        if self.template_id and self.current_file_bytes:
            path, _ = QFileDialog.getSaveFileName(self, "Сохранить шаблон на диск", f"template_{self.template_id}.docx", "Word документы (*.docx)")
            if path:
                try:
                    with open(path, 'wb') as f:
                        f.write(self.current_file_bytes)
                    QMessageBox.information(self, "Успех", f"Шаблон сохранён:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения:\n{str(e)}")

    def load_data(self):
        query = QSqlQuery(self.db)
        # ✅ ИСПРАВЛЕНО: Именованный параметр :id
        query.prepare("SELECT name, description, template_data FROM krd.document_templates WHERE id = :id")
        query.bindValue(":id", self.template_id)
        
        if query.exec() and query.next():
            self.name_input.setText(query.value(0) or "")
            self.desc_input.setPlainText(query.value(1) or "")
            data = query.value(2)
            
            # ✅ ИСПРАВЛЕНО: Добавлено условие проверки данных (if data:)
            if data:
                self.current_file_bytes = bytes(data) if not isinstance(data, bytes) else data
                size = len(self.current_file_bytes)
                self.file_label.setText(f"✅ Текущий шаблон в БД ({size} байт)")
                self.file_label.setStyleSheet("QLabel { color: blue; font-weight: bold; background-color: #e3f2fd; padding: 5px; border: 1px solid #2196F3; }")
                self.download_file_btn.setEnabled(True)

    def save(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        if not name:
            return QMessageBox.warning(self, "Ошибка", "Введите название шаблона!")
            
        file_bytes = self.current_file_bytes
        if self.selected_file_path:
            try:
                with open(self.selected_file_path, 'rb') as f:
                    file_bytes = f.read()
            except Exception as e:
                return QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл:\n{str(e)}")
                
        if not file_bytes:
            return QMessageBox.warning(self, "Ошибка", "Выберите файл шаблона!")
            
        query = QSqlQuery(self.db)
        try:
            if self.template_id:
                # ✅ ИСПРАВЛЕНО: Именованные параметры для UPDATE
                query.prepare("""
                    UPDATE krd.document_templates 
                    SET name = :name, description = :desc, template_data = :data, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = :id
                """)
                query.bindValue(":name", name)
                query.bindValue(":desc", desc)
                query.bindValue(":data", QByteArray(file_bytes))
                query.bindValue(":id", self.template_id)
            else:
                # ✅ ИСПРАВЛЕНО: Именованные параметры для INSERT
                query.prepare("""
                    INSERT INTO krd.document_templates (name, description, template_data, is_deleted) 
                    VALUES (:name, :desc, :data, FALSE)
                """)
                query.bindValue(":name", name)
                query.bindValue(":desc", desc)
                query.bindValue(":data", QByteArray(file_bytes))
                
            if query.exec():
                QMessageBox.information(self, "Успех", "Шаблон успешно сохранён!")
                self.accept()
            else:
                raise Exception(query.lastError().text())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить:\n{str(e)}")