from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton,
    QLabel, QLineEdit, QHeaderView, QMessageBox, QMenu, QGridLayout
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtSql import QSqlQueryModel, QSqlQuery
from PyQt6.QtGui import QFont, QAction
from request_filter_proxy import RequestFilterProxyModel
from request_details_dialog import RequestDetailsDialog

class OutgoingRequestsListTab(QWidget):
    def __init__(self, krd_id, db_connection, audit_logger=None, parent=None):
        super().__init__(parent)
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.source_model = QSqlQueryModel()
        self.proxy_model = RequestFilterProxyModel()
        self.proxy_model.setSourceModel(self.source_model)
        self.init_ui()
        self.load_requests()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Список сформированных запросов и поручений", font=QFont("Arial", 12, QFont.Weight.Bold)))
        
        search_layout = QGridLayout()
        self.search_recipient = QLineEdit(); self.search_recipient.setPlaceholderText("Поиск по адресату...")
        self.search_recipient.textChanged.connect(lambda t: self.proxy_model.set_recipient_filter(t))
        self.search_date = QLineEdit(); self.search_date.setPlaceholderText("Поиск по дате...")
        self.search_date.textChanged.connect(lambda t: self.proxy_model.set_date_filter(t))
        self.search_number = QLineEdit(); self.search_number.setPlaceholderText("Поиск по номеру/ID...")
        self.search_number.textChanged.connect(lambda t: self.proxy_model.set_number_filter(t))
        
        # ✅ НОВОЕ: Поле поиска по номеру ответа
        self.search_response = QLineEdit(); self.search_response.setPlaceholderText("Поиск по номеру ответа...")
        self.search_response.textChanged.connect(lambda t: self.proxy_model.set_response_filter(t))

        search_layout.addWidget(QLabel("Адресат:"), 0, 0); search_layout.addWidget(self.search_recipient, 0, 1)
        search_layout.addWidget(QLabel("Дата:"), 1, 0); search_layout.addWidget(self.search_date, 1, 1)
        search_layout.addWidget(QLabel("Номер/ID:"), 0, 2); search_layout.addWidget(self.search_number, 0, 3)
        search_layout.addWidget(QLabel("Номер ответа:"), 1, 2); search_layout.addWidget(self.search_response, 1, 3)
        layout.addLayout(search_layout)

        self.requests_table = QTableView()
        self.requests_table.setModel(self.proxy_model)
        self.requests_table.setAlternatingRowColors(True)
        self.requests_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.requests_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.requests_table.customContextMenuRequested.connect(self.show_context_menu)
        self.requests_table.doubleClicked.connect(self.on_request_double_clicked)
        
        header = self.requests_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.requests_table.setColumnWidth(0, 60); self.requests_table.setColumnWidth(1, 100)
        self.requests_table.setColumnWidth(2, 180); self.requests_table.setColumnWidth(3, 90)
        self.requests_table.setColumnWidth(4, 100); self.requests_table.setColumnWidth(5, 100)
        self.requests_table.setColumnWidth(6, 110)  # ✅ Ширина для новой колонки
        layout.addWidget(self.requests_table)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("🔄 Обновить список", clicked=self.load_requests))
        btn_layout.addStretch()
        btn_layout.addWidget(QPushButton("📋 Открыть детали", clicked=self.open_selected_details))
        layout.addLayout(btn_layout)

    def load_requests(self):
        # ✅ ДОБАВЛЕНО: o.response_number как 7-я колонка (индекс 6)
        sql = """
            SELECT o.id as "ID", rt.name as "Тип запроса", COALESCE(r.name, 'Не указан') as "Адресат",
                   o.issue_date as "Дата", o.issue_number as "Номер", o.response_status as "Статус ответа",
                   COALESCE(o.response_number, '') as "Номер ответа"
            FROM krd.outgoing_requests o
            LEFT JOIN krd.request_types rt ON o.request_type_id = rt.id
            LEFT JOIN krd.recipients r ON o.recipient_id = r.id
            WHERE o.krd_id = :krd_id AND o.is_deleted = FALSE
            ORDER BY o.issue_date DESC, o.id DESC
        """
        q = QSqlQuery(self.db)
        q.prepare(sql); q.bindValue(":krd_id", self.krd_id)
        if q.exec():
            self.source_model.setQuery(q)
        else:
            print(f"⚠️ Ошибка load_requests: {q.lastError().text()}")

    def _get_source_id(self, proxy_index):
        source_idx = self.proxy_model.mapToSource(proxy_index)
        return self.source_model.data(self.source_model.index(source_idx.row(), 0))

    def on_request_double_clicked(self, proxy_index):
        req_id = self._get_source_id(proxy_index)
        if req_id: self.open_details_dialog(req_id)

    def open_selected_details(self):
        selected = self.requests_table.selectionModel().selectedRows()
        if selected: self.open_details_dialog(self._get_source_id(selected[0]))
        else: QMessageBox.information(self, "Внимание", "Выберите запрос.")

    def open_details_dialog(self, request_id):
        dlg = RequestDetailsDialog(self.db, request_id, self.audit_logger, self)
        dlg.exec()

    def show_context_menu(self, position: QPoint):
        index = self.requests_table.indexAt(position)
        if not index.isValid(): return
        req_id = self._get_source_id(index)
        menu = QMenu(self)
        menu.addAction("📋 Открыть детали", lambda: self.open_details_dialog(req_id))
        menu.addSeparator()
        menu.addAction("🗑️ Удалить запрос", lambda: self.delete_request(index))
        menu.exec(self.requests_table.mapToGlobal(position))

    def delete_request(self, proxy_index):
        req_id = self._get_source_id(proxy_index)
        src_idx = self.proxy_model.mapToSource(proxy_index)
        issue_num = self.source_model.data(self.source_model.index(src_idx.row(), 4)) or "неизвестный"
        reply = QMessageBox.question(self, "Подтверждение", f"Скрыть запрос №{issue_num}?")
        if reply == QMessageBox.StandardButton.Yes:
            q = QSqlQuery(self.db)
            q.prepare("UPDATE krd.outgoing_requests SET is_deleted=TRUE, deleted_at=CURRENT_TIMESTAMP, deleted_by=:uid WHERE id=:id AND is_deleted=FALSE")
            q.bindValue(":uid", self.audit_logger.user_info.get('id') if self.audit_logger else None)
            q.bindValue(":id", req_id)
            if q.exec() and q.numRowsAffected() > 0:
                QMessageBox.information(self, "Успех", f"Запрос №{issue_num} скрыт!")
                self.load_requests()
                if self.audit_logger:
                    self.audit_logger.log_action('REQUEST_SOFT_DELETE', 'outgoing_requests', record_id=req_id, description=f'Скрыт запрос №{issue_num}')
            else:
                QMessageBox.warning(self, "Внимание", "Запрос не найден или уже удалён.")