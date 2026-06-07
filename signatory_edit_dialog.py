# signatory_edit_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QHBoxLayout, QMessageBox, QDialogButtonBox
)
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont

class SignatoryEditDialog(QDialog):
    def __init__(self, db, signatory_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.signatory_id = signatory_id
        self.setWindowTitle("✏️ Редактирование подписанта" if signatory_id else "➕ Новый подписант")
        self.setModal(True)
        self.resize(500, 350)
        self.init_ui()
        if self.signatory_id:
            self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        form.setSpacing(12)

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Например: И. Кувандыков")
        form.addRow("ФИО *:", self.full_name_input)

        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("Например: Врио военного коменданта...")
        form.addRow("Должность *:", self.position_input)

        self.rank_input = QLineEdit()
        self.rank_input.setPlaceholderText("Например: лейтенант юстиции")
        form.addRow("Звание:", self.rank_input)

        self.garrison_input = QLineEdit()
        self.garrison_input.setPlaceholderText("Например: г. Абакан")
        form.addRow("Гарнизон:", self.garrison_input)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Save).setText("💾 Сохранить")
        btn_box.button(QDialogButtonBox.StandardButton.Save).setProperty("role", "save")
        btn_box.accepted.connect(self.save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        self.setLayout(layout)

    def load_data(self):
        q = QSqlQuery(self.db)
        q.prepare("SELECT full_name, position, rank, garrison FROM krd.signatories WHERE id = :id")
        q.bindValue(":id", self.signatory_id)
        if q.exec() and q.next():
            self.full_name_input.setText(q.value(0) or "")
            self.position_input.setText(q.value(1) or "")
            self.rank_input.setText(q.value(2) or "")
            self.garrison_input.setText(q.value(3) or "")

    def save(self):
        full_name = self.full_name_input.text().strip()
        position = self.position_input.text().strip()
        if not full_name or not position:
            return QMessageBox.warning(self, "Ошибка", "ФИО и Должность обязательны для заполнения!")

        q = QSqlQuery(self.db)
        values = {
            "full_name": full_name,
            "position": position,
            "rank": self.rank_input.text().strip(),
            "garrison": self.garrison_input.text().strip()
        }

        if self.signatory_id:
            cols_set = ", ".join([f"{k} = :{k}" for k in values.keys()])
            q.prepare(f"UPDATE krd.signatories SET {cols_set} WHERE id = :id")
            for k, v in values.items():
                q.bindValue(f":{k}", v)
            q.bindValue(":id", self.signatory_id)
        else:
            cols = ", ".join(values.keys())
            placeholders = ", ".join([f":{k}" for k in values.keys()])
            q.prepare(f"INSERT INTO krd.signatories ({cols}) VALUES ({placeholders})")
            for k, v in values.items():
                q.bindValue(f":{k}", v)

        if q.exec():
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка сохранения:\n{q.lastError().text()}")