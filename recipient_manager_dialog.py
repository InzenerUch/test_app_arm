"""
Окно управления списком адресатов (CRUD)
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtSql import QSqlQuery
from recipient_edit_dialog import RecipientEditDialog

class RecipientManagerDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("👥 Управление адресатами")
        self.resize(950, 650)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Наименование", "Контакты", "Город", "Полный адрес"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        btns = QHBoxLayout()
        for label, slot, style in [
            ("➕ Добавить", self.add_recipient, None),
            ("✏️ Изменить", self.edit_recipient, None),
            ("🗑️ Удалить", self.delete_recipient, "background-color: #ff6b6b; color: white;"),
            ("🔄 Обновить", self.load_data, None),
            ("Закрыть", self.accept, "background-color: #2196F3; color: white; font-weight: bold;")
        ]:
            btn = QPushButton(label)
            if style: btn.setStyleSheet(style)
            btn.clicked.connect(slot)
            btns.addWidget(btn)
        layout.addLayout(btns)
        self.setLayout(layout)

    def load_data(self):
        self.table.setRowCount(0)
        q = QSqlQuery(self.db)
        q.prepare("""SELECT id, name, contacts, postal_town,
                     COALESCE(postal_town, '') || ', ' || COALESCE(postal_street, '') || ', ' || COALESCE(postal_house, '')
                     FROM krd.recipients WHERE is_deleted = FALSE ORDER BY name""")
        if q.exec():
            while q.next():
                row = self.table.rowCount()
                self.table.insertRow(row)
                for i in range(5):
                    val = q.value(i)
                    self.table.setItem(row, i, QTableWidgetItem(str(val) if val is not None else ""))

    def get_selected_id(self):
        sel = self.table.selectionModel().selectedRows()
        return int(self.table.item(sel[0].row(), 0).text()) if sel else None

    def add_recipient(self):
        if RecipientEditDialog(self.db, parent=self).exec() == 1:
            self.load_data()

    def edit_recipient(self):
        rid = self.get_selected_id()
        if not rid:
            return QMessageBox.warning(self, "Внимание", "Выберите адресата для редактирования")
        if RecipientEditDialog(self.db, recipient_id=rid, parent=self).exec() == 1:
            self.load_data()

    def delete_recipient(self):
        rid = self.get_selected_id()
        if not rid:
            return QMessageBox.warning(self, "Внимание", "Выберите адресата для удаления")
        if QMessageBox.question(self, "Подтверждение", "Выполнить мягкое удаление адресата?") == QMessageBox.StandardButton.Yes:
            q = QSqlQuery(self.db)
            q.prepare("UPDATE krd.recipients SET is_deleted=TRUE WHERE id=?")
            q.addBindValue(rid)
            if q.exec():
                self.load_data()
            else:
                QMessageBox.critical(self, "Ошибка БД", q.lastError().text())