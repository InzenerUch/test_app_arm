"""
Виджет выбора адресата (ComboBox + кнопка управления)
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QPushButton
from PyQt6.QtSql import QSqlQuery
from recipient_manager_dialog import RecipientManagerDialog

class RecipientWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_recipients()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.setMinimumWidth(280)
        self.combo.addItem("— Выберите адресата —", None)
        layout.addWidget(self.combo)
        manage_btn = QPushButton("👥 Управление адресатами")
        manage_btn.clicked.connect(self.open_manager)
        layout.addWidget(manage_btn)
        self.setLayout(layout)

    def load_recipients(self):
        self.combo.clear()
        self.combo.addItem("— Выберите адресата —", None)
        q = QSqlQuery(self.db)
        q.prepare("SELECT id, name FROM krd.recipients WHERE is_deleted = FALSE ORDER BY name")
        if q.exec():
            while q.next():
                self.combo.addItem(q.value(1), q.value(0))

    def open_manager(self):
        dialog = RecipientManagerDialog(self.db, self)
        if dialog.exec() == 1:
            self.load_recipients()

    def current_id(self):
        return self.combo.currentData()