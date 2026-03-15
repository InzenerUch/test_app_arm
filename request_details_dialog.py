import os
import subprocess
import platform
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QFormLayout, QHBoxLayout,
    QLabel, QPushButton, QDateEdit, QLineEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtSql import QSqlQuery

class RequestDetailsDialog(QDialog):
    def __init__(self, db, request_id, audit_logger=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.request_id = request_id
        self.audit_logger = audit_logger
        self.setWindowTitle(f"Запрос #{request_id} — Детали")
        self.resize(650, 480)
        self.init_ui()
        self.load_request_data()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # === Информация о запросе ===
        g_info = QGroupBox("Информация о запросе")
        f_info = QFormLayout()
        self.lbl_type = QLabel(); self.lbl_recipient = QLabel()
        self.lbl_date = QLabel(); self.lbl_number = QLabel(); self.lbl_status = QLabel()
        
        for w in (self.lbl_type, self.lbl_recipient, self.lbl_date, self.lbl_number, self.lbl_status):
            w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            
        f_info.addRow("Тип:", self.lbl_type)
        f_info.addRow("Адресат:", self.lbl_recipient)
        f_info.addRow("Дата:", self.lbl_date)
        f_info.addRow("Номер:", self.lbl_number)
        f_info.addRow("Статус:", self.lbl_status)
        g_info.setLayout(f_info)
        layout.addWidget(g_info)

        # === Работа с файлами ===
        g_files = QGroupBox("Работа с файлами")
        f_files = QHBoxLayout()

        self.btn_dl_req = QPushButton("📥 Выгрузить запрос (.docx)")
        self.btn_dl_req.clicked.connect(lambda: self._download_file("document_data", f"Запрос_{self.lbl_number.text()}.docx"))
        f_files.addWidget(self.btn_dl_req)

        self.btn_dl_resp = QPushButton("📥 Выгрузить ответ")
        self.btn_dl_resp.setEnabled(False)
        self.btn_dl_resp.setToolTip("Ответ еще не загружен в систему")
        self.btn_dl_resp.clicked.connect(lambda: self._download_file("response_data", f"Ответ_на_{self.lbl_number.text()}.docx"))
        f_files.addWidget(self.btn_dl_resp)

        g_files.setLayout(f_files)
        layout.addWidget(g_files)

        # === Загрузка ответа ===
        g_resp = QGroupBox("Загрузка ответа")
        f_resp = QFormLayout()
        self.input_date = QDateEdit()
        self.input_date.setCalendarPopup(True)
        self.input_num = QLineEdit()

        f_resp.addRow("Дата получения:", self.input_date)
        f_resp.addRow("Входящий №:", self.input_num)

        self.btn_up_resp = QPushButton("📤 Загрузить ответ из файла")
        self.btn_up_resp.clicked.connect(self.upload_response)
        f_resp.addRow(self.btn_up_resp)

        g_resp.setLayout(f_resp)
        layout.addWidget(g_resp)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def load_request_data(self):
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT rt.name, COALESCE(r.name, ''), o.issue_date, o.issue_number, o.response_status,
                   o.response_date, o.response_number, o.response_data
            FROM krd.outgoing_requests o
            LEFT JOIN krd.request_types rt ON o.request_type_id = rt.id
            LEFT JOIN krd.recipients r ON o.recipient_id = r.id
            WHERE o.id = :id
        """)
        q.bindValue(":id", self.request_id)

        if q.exec() and q.next():
            self.lbl_type.setText(q.value(0) or "Не указан")
            self.lbl_recipient.setText(q.value(1) or "Не указан")
            self.lbl_date.setText(q.value(2).toString("dd.MM.yyyy") if hasattr(q.value(2), 'toString') else str(q.value(2) or ""))
            self.lbl_number.setText(q.value(3) or "Без номера")
            self.lbl_status.setText(q.value(4) or "Ожидание")

            if q.value(5): self.input_date.setDate(q.value(5))
            if q.value(6): self.input_num.setText(q.value(6) or "")

            response_data = q.value(7)
            if response_data is not None and (isinstance(response_data, bytes) or hasattr(response_data, 'data')):
                self.btn_dl_resp.setEnabled(True)
                self.btn_dl_resp.setToolTip("Нажмите, чтобы сохранить ответ на диск")
            else:
                self.btn_dl_resp.setEnabled(False)
                self.btn_dl_resp.setToolTip("Ответ еще не загружен")

    def _download_file(self, column, default_name):
        q = QSqlQuery(self.db)
        q.prepare(f"SELECT {column} FROM krd.outgoing_requests WHERE id = :id")
        q.bindValue(":id", self.request_id)

        if not q.exec() or not q.next() or q.value(0) is None:
            return QMessageBox.information(self, "Информация", "Файл отсутствует в базе данных.")

        raw_data = q.value(0)
        try:
            file_bytes = bytes(raw_data.data()) if hasattr(raw_data, 'data') else bytes(raw_data)
        except Exception as e:
            return QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать данные файла: {e}")

        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", default_name, "Все файлы (*)")
        if path:
            try:
                with open(path, 'wb') as f:
                    f.write(file_bytes)
                # ✅ АВТООТКРЫТИЕ ФАЙЛА СРЕДСТВАМИ ОС
                self._open_file_with_os(path)
                QMessageBox.information(self, "Успех", f"✅ Файл сохранён и открыт:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка сохранения", f"Не удалось записать файл:\n{e}")

    def _open_file_with_os(self, filepath):
        """Открывает файл в стандартном приложении ОС"""
        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":
                subprocess.call(["open", filepath])
            else:
                subprocess.call(["xdg-open", filepath])
        except Exception as e:
            print(f"⚠️ Не удалось открыть файл через ОС: {e}")

    def upload_response(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл ответа", "", "Документы (*.docx *.pdf *.jpg *.png);;Все файлы (*)")
        if not file_path: return

        try:
            with open(file_path, 'rb') as f: data = f.read()

            q = QSqlQuery(self.db)
            q.prepare("""
                UPDATE krd.outgoing_requests
                SET response_data = :data, response_date = :date, response_number = :num, response_status = 'Получен'
                WHERE id = :id
            """)
            q.bindValue(":data", QByteArray(data))
            q.bindValue(":date", self.input_date.date())
            q.bindValue(":num", self.input_num.text())
            q.bindValue(":id", self.request_id)

            if q.exec():
                QMessageBox.information(self, "Успех", "Ответ успешно загружен!")
                self.load_request_data() # Обновляет UI (активирует кнопку выгрузки)
                if self.parent() and hasattr(self.parent(), 'load_requests'): 
                    self.parent().load_requests()
                if self.audit_logger:
                    self.audit_logger.log_action('RESPONSE_UPLOADED', 'outgoing_requests', self.request_id, description='Ответ загружен через диалог')
            else:
                QMessageBox.critical(self, "Ошибка БД", q.lastError().text())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))