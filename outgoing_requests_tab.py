"""
Вкладка запросов и поручений с генерацией документов из шаблонов
Хранение документов в базе данных в виде байтов (BYTEA)
Мягкое удаление запросов (скрытие от пользователя, но сохранение в БД)
✅ ИСПРАВЛЕНО: Заменены все ? на именованные параметры (:name) для стабильной работы QPSQL
✅ ДОБАВЛЕНО: Автообновление списка при сохранении нового документа через сигнал
✅ ДОБАВЛЕНО: JOIN с krd.recipients для отображения имени адресата
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QDateEdit, QLabel, QPushButton, QComboBox,
    QTableView, QMessageBox, QFileDialog, QMenu
)
from PyQt6.QtCore import Qt, QDate, QPoint, QTime
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont, QAction
import os
import tempfile
import re
import subprocess
import sys
import traceback
from audit_logger import AuditLogger
from document_generator_tab import DocumentGeneratorTab

class OutgoingRequestsTab(QWidget):
    """Вкладка запросов и поручений с генерацией документов"""
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        
        if self.krd_id is None:
            QMessageBox.critical(self, "Ошибка инициализации", "ID КРД не может быть None")
            return
            
        self.init_ui()
        self.load_requests()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout()
        tabs = QTabWidget()
        
        # Вкладка 1: Генерация запросов
        generator_tab = DocumentGeneratorTab(self.krd_id, self.db, self.audit_logger)
        
        # 🔥 ПОДКЛЮЧАЕМ АВТООБНОВЛЕНИЕ: при сигнале request_saved вызываем load_requests()
        generator_tab.request_saved.connect(self.load_requests)
        
        tabs.addTab(generator_tab, "Генерация запросов")
        
        # Вкладка 2: Список сформированных запросов
        tabs.addTab(self.create_requests_list_tab(), "Список запросов")
        
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)
        
    def create_requests_list_tab(self):
        """Создание вкладки списка сформированных запросов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title_label = QLabel("Список сформированных запросов и поручений")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        self.requests_model = QSqlQueryModel()
        self.requests_table = QTableView()
        self.requests_table.setModel(self.requests_model)
        self.requests_table.setAlternatingRowColors(True)
        self.requests_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.requests_table.doubleClicked.connect(self.on_request_double_clicked)
        self.requests_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.requests_table.customContextMenuRequested.connect(self.show_context_menu)
        
        header = self.requests_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # Установка ширины колонок
        self.requests_table.setColumnWidth(0, 60)   # ID
        self.requests_table.setColumnWidth(1, 120)  # Тип запроса
        self.requests_table.setColumnWidth(2, 200)  # Адресат
        self.requests_table.setColumnWidth(3, 100)  # Дата
        self.requests_table.setColumnWidth(4, 100)  # Номер
        
        layout.addWidget(self.requests_table)
        
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Обновить список")
        refresh_btn.clicked.connect(self.load_requests)
        btn_layout.addWidget(refresh_btn)
        
        delete_btn = QPushButton("Удаление")
        delete_btn.setStyleSheet("background-color: #ff6b6b; color: white; font-weight: bold;")
        delete_btn.clicked.connect(self.delete_selected_request)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        return widget
        
    def show_context_menu(self, position: QPoint):
        index = self.requests_table.indexAt(position)
        if not index.isValid():
            return
            
        menu = QMenu(self)
        open_action = QAction("Открыть документ", self)
        open_action.triggered.connect(lambda: self.on_request_double_clicked(index))
        menu.addAction(open_action)
        
        delete_action = QAction("Удаление", self)
        delete_action.triggered.connect(lambda: self.delete_request(index))
        menu.addAction(delete_action)
        
        menu.exec(self.requests_table.mapToGlobal(position))
        
    def on_request_double_clicked(self, index):
        """Обработка двойного клика - выгрузка и открытие документа"""
        from PyQt6.QtCore import QByteArray
        request_id = self.requests_model.data(self.requests_model.index(index.row(), 0))
        if not request_id:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить ID запроса")
            return
            
        try:
            print("\n" + "="*60)
            print("📂 ВЫГРУЗКА ДОКУМЕНТА ИЗ БАЗЫ ДАННЫХ")
            print("="*60)
            print(f"🔍 Request ID: {request_id}")
            # 1. Получение данных из БД
            query = QSqlQuery(self.db)
            # ✅ ИМЕНОВАННЫЕ ПАРАМЕТРЫ
            query.prepare("""
                SELECT document_data, issue_number 
                FROM krd.outgoing_requests 
                WHERE id = :request_id AND is_deleted = FALSE
            """)
            query.bindValue(":request_id", request_id)
            
            if not query.exec() or not query.next():
                QMessageBox.warning(self, "Ошибка", "Документ не найден или был скрыт")
                return
                
            document_bytes = query.value(0)
            issue_number = query.value(1)
            
            if document_bytes is None:
                QMessageBox.information(self, "Информация", f"Документ для запроса №{issue_number} отсутствует")
                return
                
            if isinstance(document_bytes, QByteArray):
                document_bytes = bytes(document_bytes.data())
            elif isinstance(document_bytes, memoryview):
                document_bytes = document_bytes.tobytes()
            else:
                document_bytes = bytes(document_bytes)
                
            if not document_bytes or len(document_bytes) == 0:
                QMessageBox.warning(self, "Ошибка", f"Документ №{issue_number} пустой")
                return
                
            if not document_bytes.startswith(b'PK'):
                QMessageBox.warning(self, "Ошибка", "Файл поврежден или не является DOCX")
                return
                
            safe_issue_number = re.sub(r'[<>:"/\\|?*]', '_', str(issue_number))
            default_filename = f"Запрос_{safe_issue_number}_{request_id}.docx"
            
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить документ", default_filename, "Word документы (*.docx);;Все файлы (*)"
            )
            if not save_path:
                return
                
            if not save_path.lower().endswith('.docx'):
                save_path += '.docx'
                
            with open(save_path, 'wb') as f:
                f.write(document_bytes)
                f.flush()
                os.fsync(f.fileno())
                
            if sys.platform == 'win32':
                os.startfile(save_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', save_path])
            else:
                subprocess.run(['xdg-open', save_path])
                
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='DOCUMENT_OPEN', table_name='outgoing_requests',
                    record_id=request_id, krd_id=self.krd_id,
                    description=f'Выгружен и открыт документ запроса №{issue_number}'
                )
            print(f"✅ Документ успешно сохранён и открыт: {save_path}")
            print("="*60 + "\n")
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выгрузке: {str(e)}")
            
    def delete_request(self, index):
        request_id = self.requests_model.data(self.requests_model.index(index.row(), 0))
        if request_id:
            self.delete_request_by_id(request_id)
            
    def delete_selected_request(self):
        selection = self.requests_table.selectionModel()
        if not selection.hasSelection():
            QMessageBox.warning(self, "Внимание", "Выберите запрос для скрытия")
            return
        index = selection.selectedRows()[0]
        self.delete_request(index)
        
    def delete_request_by_id(self, request_id):
        query = QSqlQuery(self.db)
        # ✅ ИМЕНОВАННЫЙ ПАРАМЕТР
        query.prepare("SELECT issue_number FROM krd.outgoing_requests WHERE id = :id AND is_deleted = FALSE")
        query.bindValue(":id", request_id)
        
        issue_number = "неизвестный"
        if query.exec() and query.next():
            issue_number = query.value(0)
        else:
            QMessageBox.warning(self, "Ошибка", "Запрос не найден или уже скрыт")
            return
            
        reply = QMessageBox.question(
            self, "Подтверждение скрытия запроса",
            f"Скрыть запрос №{issue_number}?\n"
            "Запрос останется в базе для истории и будет доступен администратору.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                q = QSqlQuery(self.db)
                q.prepare("""
                    UPDATE krd.outgoing_requests 
                    SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP, deleted_by = :user_id
                    WHERE id = :id AND is_deleted = FALSE
                """)
                user_id = self.audit_logger.user_info.get('id') if self.audit_logger else None
                q.bindValue(":user_id", user_id)
                q.bindValue(":id", request_id)
                
                if q.exec() and q.numRowsAffected() > 0:
                    QMessageBox.information(self, "Успех", f"Запрос №{issue_number} успешно скрыт!")
                    self.load_requests()
                    if self.audit_logger:
                        self.audit_logger.log_action(
                            action_type='REQUEST_SOFT_DELETE', table_name='outgoing_requests',
                            record_id=request_id, krd_id=self.krd_id,
                            description=f'Скрыт запрос №{issue_number}'
                        )
                else:
                    raise Exception(q.lastError().text())
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при скрытии: {str(e)}")
                
    def load_requests(self):
        """Загрузка списка сформированных запросов (✅ ИСПРАВЛЕНО: JOIN + именованные параметры)"""
        try:
            query = QSqlQuery(self.db)
            # ✅ ИСПОЛЬЗУЕМ ИМЕНОВАННЫЙ ПАРАМЕТР :krd_id
            # ✅ JOIN С krd.recipients ДЛЯ ПОЛУЧЕНИЯ АКТУАЛЬНОГО ИМЕНИ АДРЕСАТА
            sql = """
                SELECT o.id as "ID", rt.name as "Тип запроса", 
                       COALESCE(r.name, 'Не указан') as "Адресат", 
                       o.issue_date as "Дата", o.issue_number as "Номер"
                FROM krd.outgoing_requests o
                LEFT JOIN krd.request_types rt ON o.request_type_id = rt.id
                LEFT JOIN krd.recipients r ON o.recipient_id = r.id
                WHERE o.krd_id = :krd_id AND o.is_deleted = FALSE
                ORDER BY o.issue_date DESC, o.id DESC
            """
            
            if not query.prepare(sql):
                print(f"⚠️ Ошибка подготовки запроса: {query.lastError().text()}")
                return
                
            query.bindValue(":krd_id", self.krd_id)
            
            if not query.exec():
                print(f"⚠️ Ошибка выполнения запроса load_requests: {query.lastError().text()}")
                return
                
            self.requests_model.setQuery(query)
            
            count = self.requests_model.rowCount()
            parent = self.parent()
            if parent and hasattr(parent, 'setWindowTitle'):
                parent.setWindowTitle(f"Запросы и поручения (КРД-{self.krd_id}) - {count} запросов")
                
        except Exception as e:
            traceback.print_exc()
            print(f"⚠️ Ошибка в load_requests: {e}")