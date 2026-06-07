# signatory_manager_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableView,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QLabel
)
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont
from signatory_edit_dialog import SignatoryEditDialog

class SignatoryManagerDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("👥 Управление подписантами документов")
        self.resize(800, 500)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        
        info_lbl = QLabel("Дважды кликните по записи для редактирования")
        info_lbl.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_lbl)

        self.table = QTableView()
        self.model = QSqlQueryModel()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self.edit_selected)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        add_btn = QPushButton("➕ Добавить")
        add_btn.setProperty("role", "info")
        add_btn.clicked.connect(self.add_signatory)
        
        edit_btn = QPushButton("✏️ Изменить")
        edit_btn.setProperty("role", "edit")
        edit_btn.clicked.connect(self.edit_selected)
        
        delete_btn = QPushButton("🗑️ Удалить")
        delete_btn.setProperty("role", "danger")
        delete_btn.clicked.connect(self.delete_signatory)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)

        for btn in (add_btn, edit_btn, delete_btn, close_btn):
            btns.addWidget(btn)
            
        layout.addLayout(btns)
        self.setLayout(layout)

    def load_data(self):
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT id, full_name AS "ФИО", position AS "Должность", rank AS "Звание", garrison AS "Гарнизон"
            FROM krd.signatories 
            WHERE is_deleted = FALSE 
            ORDER BY full_name
        """)
        if q.exec():
            self.model.setQuery(q)
            self.table.setColumnHidden(0, True) # Скрываем ID

    def get_selected_id(self):
        sel = self.table.selectionModel().selectedRows()
        if sel:
            # ID находится в скрытой колонке 0
            return self.model.data(self.model.index(sel[0].row(), 0))
        return None

    def add_signatory(self):
        if SignatoryEditDialog(self.db, parent=self).exec() == 1:
            self.load_data()

    def edit_selected(self):
        sid = self.get_selected_id()
        if not sid:
            return QMessageBox.warning(self, "Внимание", "Выберите подписанта для редактирования")
        if SignatoryEditDialog(self.db, signatory_id=sid, parent=self).exec() == 1:
            self.load_data()

    def delete_signatory(self):
        sid = self.get_selected_id()
        if not sid:
            return QMessageBox.warning(self, "Внимание", "Выберите подписанта для удаления")
        
        name = self.model.data(self.model.index(self.table.selectionModel().selectedRows()[0].row(), 1))
        if QMessageBox.question(self, "Подтверждение", f"Выполнить удаление подписанта '{name}'?") == QMessageBox.StandardButton.Yes:
            q = QSqlQuery(self.db)
            q.prepare("UPDATE krd.signatories SET is_deleted = TRUE WHERE id = :id")
            q.bindValue(":id", sid)
            if q.exec():
                self.load_data()
            else:
                QMessageBox.critical(self, "Ошибка БД", q.lastError().text())