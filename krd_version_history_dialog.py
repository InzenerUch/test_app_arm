# krd_version_history_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtSql import QSqlQuery

class KrdVersionHistoryDialog(QDialog):
    """Диалог выбора версии КРД для предпросмотра или восстановления"""
    preview_requested = pyqtSignal(int)  # version_id
    restore_requested = pyqtSignal(int)  # version_id

    def __init__(self, db, krd_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.krd_id = krd_id
        self.setWindowTitle(f"📜 История версий КРД-{krd_id}")
        self.resize(850, 500)
        self.setModal(True)
        self.init_ui()
        self.load_versions()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("📜 Сохраненные версии карточки:"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["№ Версии", "Дата создания", "Автор", "Описание", "ID"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # ✅ Настройка ширины колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Описание растягивается
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnHidden(4, True)  # Скрываем ID
        
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        
        self.btn_preview = QPushButton("👁️ Предпросмотр (без сохранения)")
        self.btn_preview.setProperty("role", "info")  # ✅ Стилизация под тему проекта
        self.btn_preview.clicked.connect(self.on_preview)
        self.btn_preview.setEnabled(False)
        
        self.btn_restore = QPushButton("⏪ Восстановить в БД")
        self.btn_restore.setProperty("role", "danger")
        self.btn_restore.clicked.connect(self.on_restore)
        self.btn_restore.setEnabled(False)
        
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def load_versions(self):
        self.table.setRowCount(0)
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT v.version_number, v.created_at, u.username, v.description, v.id
            FROM krd.krd_versions v
            LEFT JOIN krd.users u ON v.created_by = u.id
            WHERE v.krd_id = :krd_id
            ORDER BY v.version_number DESC
        """)
        query.bindValue(":krd_id", self.krd_id)
        
        if query.exec():
            while query.next():
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # 0. Номер версии
                self.table.setItem(row, 0, QTableWidgetItem(str(query.value(0) or "")))
                
                # 1. Дата создания (✅ Форматируем QDateTime в читаемый вид)
                created_at = query.value(1)
                if isinstance(created_at, QDateTime):
                    date_str = created_at.toString("dd.MM.yyyy HH:mm:ss")
                else:
                    date_str = str(created_at) if created_at else ""
                self.table.setItem(row, 1, QTableWidgetItem(date_str))
                
                # 2. Автор
                author = query.value(2)
                self.table.setItem(row, 2, QTableWidgetItem(str(author) if author else "Система"))
                
                # 3. Описание
                desc = query.value(3)
                self.table.setItem(row, 3, QTableWidgetItem(str(desc) if desc else ""))
                
                # 4. ID (сохраняем в UserRole для быстрого доступа)
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, query.value(4))
        else:
            QMessageBox.warning(self, "Ошибка БД", f"Не удалось загрузить историю:\n{query.lastError().text()}")

    def on_selection_changed(self):
        has_sel = self.table.selectionModel().hasSelection()
        self.btn_preview.setEnabled(has_sel)
        self.btn_restore.setEnabled(has_sel)

    def on_preview(self):
        row = self.table.currentRow()
        if row >= 0:
            vid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.preview_requested.emit(vid)
            self.accept()

    def on_restore(self):
        row = self.table.currentRow()
        if row >= 0:
            vid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            ver_num = self.table.item(row, 0).text()
            reply = QMessageBox.question(self, "⚠️ Подтверждение отката",
                f"Текущие данные КРД будут полностью заменены данными версии #{ver_num}.\n"
                "Все изменения, сделанные после этой версии, будут потеряны.\n\nПродолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.restore_requested.emit(vid)
                self.accept()