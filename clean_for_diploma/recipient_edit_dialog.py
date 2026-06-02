from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLineEdit, QLabel,
    QPushButton, QHBoxLayout, QMessageBox, QWidget,QComboBox
)
from reference_editor_dialog import ReferenceEditorDialog
from PyQt6.QtSql import QSqlQuery
class RecipientEditDialog(QDialog):
    def __init__(self, db, recipient_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.recipient_id = recipient_id
        self.setWindowTitle("✏️ Редактирование адресата" if recipient_id else "➕ Новый адресат")
        self.setModal(True)
        self.resize(650, 550)
        self.fields = {}
        self.init_ui()
        if self.recipient_id:
            self.load_data()
    def init_ui(self):
        layout = QVBoxLayout()
        form = QGridLayout()
        form.setHorizontalSpacing(15)
        form.setVerticalSpacing(10)
        cols = [
            ("name", "Наименование адресата *", True),
            ("contacts", "Контакты (телефон, email)", False),
            ("postal_index", "Почтовый индекс", False),
            ("postal_region", "Субъект РФ", False),
            ("postal_district", "Район", False),
            ("postal_town", "Город/Населенный пункт", False),
            ("postal_street", "Улица", False),
            ("postal_house", "Дом", False),
            ("postal_building", "Корпус/Строение", False),
            ("postal_letter", "Литера", False),
            ("postal_apartment", "Квартира", False),
            ("postal_room", "Комната", False)
        ]
        for i, (col, label, req) in enumerate(cols):
            lbl = QLabel(label)
            edit = QLineEdit()
            edit.setPlaceholderText("Обязательно" if req else "")
            self.fields[col] = edit
            form.addWidget(lbl, i, 0)
            form.addWidget(edit, i, 1)
        req_type_label = QLabel("Тип запроса по умолчанию:")
        req_widget = QWidget()
        req_layout = QHBoxLayout(req_widget)
        req_layout.setContentsMargins(0, 0, 0, 0)
        self.request_type_combo = QComboBox()
        self.request_type_combo.setMinimumWidth(220)
        self.load_request_types()
        req_layout.addWidget(self.request_type_combo, 1)
        gear_btn = QPushButton("⚙️")
        gear_btn.setFixedSize(32, 32)
        gear_btn.setToolTip("Открыть справочник типов запросов")
        gear_btn.setProperty("role", "edit")
        gear_btn.clicked.connect(self.open_type_editor)
        req_layout.addWidget(gear_btn)
        form.addWidget(req_type_label, len(cols), 0)
        form.addWidget(req_widget, len(cols), 1)
        layout.addLayout(form)
        btns = QHBoxLayout()
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setStyleSheet("background-color:
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        self.setLayout(layout)
    def load_data(self):
        q = QSqlQuery(self.db)
        q.prepare("SELECT * FROM krd.recipients WHERE id = :id")
        q.bindValue(":id", self.recipient_id)
        if q.exec() and q.next():
            for col in self.fields:
                val = q.value(col)
                if val is not None:
                    self.fields[col].setText(str(val))
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить данные адресата")
    def save(self):
        name = self.fields["name"].text().strip()
        if not name:
            return QMessageBox.warning(self, "Ошибка", "Наименование адресата обязательно!")
        q = QSqlQuery(self.db)
        values = {col: self.fields[col].text().strip() for col in self.fields}
        if self.recipient_id:
            cols_set = ", ".join([f"{k} = :{k}" for k in values.keys()])
            q.prepare(f"UPDATE krd.recipients SET {cols_set}, updated_at=CURRENT_TIMESTAMP WHERE id=:id")
            for k, v in values.items():
                q.bindValue(f":{k}", v)
            q.bindValue(":id", self.recipient_id)
        else:
            cols = ", ".join(values.keys())
            placeholders = ", ".join([f":{k}" for k in values.keys()])
            q.prepare(f"INSERT INTO krd.recipients ({cols}) VALUES ({placeholders})")
            for k, v in values.items():
                q.bindValue(f":{k}", v)
        if q.exec():
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка сохранения:\n{q.lastError().text()}")
    def load_request_types(self):
        current_id = self.request_type_combo.currentData()
        self.request_type_combo.clear()
        self.request_type_combo.addItem("— Не выбрано —", None)
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.request_types ORDER BY name")
        while q.next():
            self.request_type_combo.addItem(q.value(1), q.value(0))
        if current_id is not None:
            idx = self.request_type_combo.findData(current_id)
            if idx >= 0: self.request_type_combo.setCurrentIndex(idx)
    def open_type_editor(self):
        dlg = ReferenceEditorDialog(self.db, self, initial_table='request_types')
        dlg.data_changed.connect(self.load_request_types)
        dlg.exec()
    def save(self):
        name = self.fields["name"].text().strip()
        if not name:
            return QMessageBox.warning(self, "Ошибка", "Наименование адресата обязательно!")
        q = QSqlQuery(self.db)
        values = {col: self.fields[col].text().strip() for col in self.fields}
        values["request_type_id"] = self.request_type_combo.currentData()
        if self.recipient_id:
            cols_set = ", ".join([f"{k} = :{k}" for k in values.keys()])
            q.prepare(f"UPDATE krd.recipients SET {cols_set}, updated_at=CURRENT_TIMESTAMP WHERE id=:id")
            for k, v in values.items(): q.bindValue(f":{k}", v)
            q.bindValue(":id", self.recipient_id)
        else:
            cols = ", ".join(values.keys())
            placeholders = ", ".join([f":{k}" for k in values.keys()])
            q.prepare(f"INSERT INTO krd.recipients ({cols}) VALUES ({placeholders})")
            for k, v in values.items(): q.bindValue(f":{k}", v)
        if q.exec():
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка сохранения:\n{q.lastError().text()}")