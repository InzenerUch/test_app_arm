"""
Вкладка запросов и поручений с генерацией документов из шаблонов
Хранение документов в базе данных в виде байтов (BYTEA)
Мягкое удаление запросов (скрытие от пользователя, но сохранение в БД)
✅ ДОБАВЛЕНО: Загрузка, просмотр и хранение ответов на запросы
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QGridLayout,
    QLineEdit, QTextEdit, QDateEdit, QLabel, QPushButton, QComboBox,
    QTableView, QMessageBox, QFileDialog, QMenu, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, QPoint, QTime, QByteArray
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
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Установка ширины колонок
        self.requests_table.setColumnWidth(0, 60)   # ID
        self.requests_table.setColumnWidth(1, 120)  # Тип запроса
        self.requests_table.setColumnWidth(2, 200)  # Адресат
        self.requests_table.setColumnWidth(3, 100)  # Дата
        self.requests_table.setColumnWidth(4, 100)  # Номер
        self.requests_table.setColumnWidth(5, 100)  # Статус ответа

        layout.addWidget(self.requests_table)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.clicked.connect(self.load_requests)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()

        self.upload_resp_btn = QPushButton("📤 Загрузить ответ")
        self.upload_resp_btn.setProperty("role", "info")
        self.upload_resp_btn.clicked.connect(self.on_upload_response_clicked)
        btn_layout.addWidget(self.upload_resp_btn)

        self.view_resp_btn = QPushButton("👁️ Просмотреть ответ")
        self.view_resp_btn.setProperty("role", "edit")
        self.view_resp_btn.clicked.connect(self.on_view_response_clicked)
        btn_layout.addWidget(self.view_resp_btn)

        delete_btn = QPushButton("🗑️ Удаление запроса")
        delete_btn.setProperty("role", "danger")
        delete_btn.clicked.connect(self.delete_selected_request)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        return widget

    def show_context_menu(self, position: QPoint):
        index = self.requests_table.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        open_action = QAction("📄 Открыть запрос", self)
        open_action.triggered.connect(lambda: self.on_request_double_clicked(index))
        menu.addAction(open_action)

        resp_action = QAction("📤 Загрузить ответ", self)
        resp_action.triggered.connect(lambda: self.upload_response_for_index(index))
        menu.addAction(resp_action)

        view_resp_action = QAction("👁️ Просмотреть ответ", self)
        view_resp_action.triggered.connect(lambda: self.view_response_for_index(index))
        menu.addAction(view_resp_action)

        menu.addSeparator()

        delete_action = QAction("🗑️ Удаление запроса", self)
        delete_action.triggered.connect(lambda: self.delete_request(index))
        menu.addAction(delete_action)

        menu.exec(self.requests_table.mapToGlobal(position))

    def on_request_double_clicked(self, index):
        """Обработка двойного клика - выгрузка и открытие документа запроса"""
        request_id = self.requests_model.data(self.requests_model.index(index.row(), 0))
        if not request_id:
            return
        
        # ✅ Вызываем новый метод сохранения
        self.save_and_open_request_doc(request_id)

    def save_and_open_request_doc(self, request_id):
        """
        Диалог сохранения документа запроса с последующим открытием
        """
        try:
            query = QSqlQuery(self.db)
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

            doc_bytes = self._to_bytes(document_bytes)
            
            # ✅ 1. ДИАЛОГ ВЫБОРА МЕСТА СОХРАНЕНИЯ
            safe_issue_number = re.sub(r'[<>:"/\\|?*]', '_', str(issue_number))
            default_filename = f"Запрос_{safe_issue_number}.docx"
            
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить документ запроса",
                default_filename,
                "Документы Word (*.docx);;Все файлы (*)"
            )
            
            # Если пользователь нажал "Отмена"
            if not save_path:
                return

            # ✅ 2. СОХРАНЕНИЕ ФАЙЛА
            with open(save_path, 'wb') as f:
                f.write(doc_bytes)
            
            print(f"✅ Документ сохранен: {save_path}")

            # ✅ 3. ОТКРЫТИЕ ФАЙЛА ОС
            self._open_file_with_os(save_path)

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")

    def _open_file_with_os(self, filepath):
        """Открывает файл средствами операционной системы"""
        try:
            if sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', filepath])
            else:  # Linux
                subprocess.call(['xdg-open', filepath])
        except Exception as e:
            print(f"⚠️ Не удалось открыть файл автоматически: {e}")
            QMessageBox.warning(self, "Информация", f"Файл сохранен:\n{filepath}\n\nНе удалось открыть автоматически.")

    def download_and_open_request_doc(self, request_id):
        """Скачивание и открытие документа запроса"""
        try:
            query = QSqlQuery(self.db)
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

            doc_bytes = self._to_bytes(document_bytes)
            safe_issue_number = re.sub(r'[<>:"/\\|?*]', '_', str(issue_number))
            default_filename = f"Запрос_{safe_issue_number}_{request_id}.docx"
            self._save_and_open_file(doc_bytes, default_filename)

        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выгрузке запроса: {str(e)}")

    def on_upload_response_clicked(self):
        """Обработчик кнопки загрузки ответа"""
        self.upload_response_for_row()

    def upload_response_for_row(self):
        """Загрузка ответа для выбранной строки"""
        selection = self.requests_table.selectionModel()
        if not selection.hasSelection():
            QMessageBox.warning(self, "Внимание", "Выберите запрос для загрузки ответа")
            return
        index = selection.selectedRows()[0]
        self.upload_response_for_index(index)

    def upload_response_for_index(self, index):
        """Загрузка файла ответа в БД"""
        request_id = self.requests_model.data(self.requests_model.index(index.row(), 0))
        issue_number = self.requests_model.data(self.requests_model.index(index.row(), 4))

        if not request_id: return

        # Выбор файла
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите документ ответа", "", "Документы (*.docx *.pdf *.jpg *.png);;Все файлы (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Вопрос о номере ответа
            response_number, ok = QMessageBox.getText(
                self, "Номер ответа",
                f"Введите входящий номер ответа на запрос №{issue_number}:",
                QLineEdit.EchoMode.Normal, ""
            )

            if not ok:
                return

            query = QSqlQuery(self.db)
            query.prepare("""
                UPDATE krd.outgoing_requests 
                SET response_data = :data, 
                    response_date = CURRENT_DATE, 
                    response_number = :num,
                    response_status = 'Получен'
                WHERE id = :id
            """)
            query.bindValue(":data", QByteArray(file_data))
            query.bindValue(":num", response_number)
            query.bindValue(":id", request_id)

            if query.exec() and query.numRowsAffected() > 0:
                QMessageBox.information(self, "Успех", "Ответ успешно загружен!")
                self.load_requests()
                if self.audit_logger:
                    self.audit_logger.log_action(
                        action_type='RESPONSE_UPLOADED', table_name='outgoing_requests',
                        record_id=request_id, krd_id=self.krd_id,
                        description=f'Загружен ответ на запрос №{issue_number}'
                    )
            else:
                raise Exception(query.lastError().text())

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки ответа: {str(e)}")

    def on_view_response_clicked(self):
        """Обработчик кнопки просмотра ответа"""
        self.view_response_for_row()

    def view_response_for_row(self):
        """Просмотр ответа для выбранной строки"""
        selection = self.requests_table.selectionModel()
        if not selection.hasSelection():
            QMessageBox.warning(self, "Внимание", "Выберите запрос для просмотра ответа")
            return
        index = selection.selectedRows()[0]
        self.view_response_for_index(index)

    def view_response_for_index(self, index):
        """Просмотр загруженного ответа"""
        request_id = self.requests_model.data(self.requests_model.index(index.row(), 0))
        issue_number = self.requests_model.data(self.requests_model.index(index.row(), 4))

        try:
            query = QSqlQuery(self.db)
            query.prepare("""
                SELECT response_data, response_number 
                FROM krd.outgoing_requests 
                WHERE id = :id
            """)
            query.bindValue(":id", request_id)

            if not query.exec() or not query.next():
                QMessageBox.warning(self, "Ошибка", "Запрос не найден")
                return

            response_data = query.value(0)
            response_number = query.value(1) or "без номера"

            if response_data is None:
                QMessageBox.information(self, "Информация", f"Ответ на запрос №{issue_number} еще не загружен")
                return

            doc_bytes = self._to_bytes(response_data)

            # Определяем расширение по сигнатуре или берем по умолчанию .docx
            ext = ".docx"
            if doc_bytes.startswith(b'%PDF'):
                ext = ".pdf"
            elif doc_bytes.startswith(b'\xff\xd8'):
                ext = ".jpg"
            elif doc_bytes.startswith(b'\x89PNG'):
                ext = ".png"

            filename = f"Ответ_на_{issue_number}_{response_number}{ext}"
            self._save_and_open_file(doc_bytes, filename)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка просмотра ответа: {str(e)}")

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
        """Загрузка списка сформированных запросов"""
        try:
            query = QSqlQuery(self.db)
            sql = """
                SELECT o.id as "ID", rt.name as "Тип запроса", 
                       COALESCE(r.name, 'Не указан') as "Адресат", 
                       o.issue_date as "Дата", o.issue_number as "Номер",
                       o.response_status as "Статус ответа"
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

    def _to_bytes(self, data):
        """Вспомогательный метод для преобразования данных из БД в bytes"""
        if isinstance(data, QByteArray):
            return bytes(data.data())
        elif isinstance(data, memoryview):
            return data.tobytes()
        return bytes(data)

    def _save_and_open_file(self, data_bytes, filename):
        """Сохраняет данные во временный файл и открывает его"""
        if not data_bytes or len(data_bytes) == 0:
            QMessageBox.warning(self, "Ошибка", "Файл пустой")
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(data_bytes)
            tmp_path = tmp.name

        try:
            if sys.platform == 'win32':
                os.startfile(tmp_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', tmp_path])
            else:
                subprocess.run(['xdg-open', tmp_path])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")