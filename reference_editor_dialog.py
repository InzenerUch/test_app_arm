"""
Диалог для редактирования справочников
✅ ДОСТУПНО ВСЕМ ПОЛЬЗОВАТЕЛЯМ
✅ ИСПРАВЛЕНО: Безопасное получение ID через Qt.UserRole (защита от ValueError)
✅ ИСПРАВЛЕНО: RecordEditDialog вынесен в отдельный файл (record_edit_dialog.py)
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QMessageBox,
    QComboBox, QHeaderView, QGroupBox, QAbstractItemView, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from reference_manager import ReferenceManager, REFERENCE_TABLES
from record_edit_dialog import RecordEditDialog  # ✅ Импорт вынесенного класса


class ReferenceEditorDialog(QDialog):
    """Диалог для управления справочниками"""

    def __init__(self, db_connection, parent=None, initial_table=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Управление справочниками")
        self.setMinimumSize(900, 700)
        self.setModal(True)

        self.db = db_connection
        self.parent_window = parent
        self.manager = ReferenceManager(db_connection)
        self.current_table = initial_table

        self.current_user_id = None
        self.current_username = ""
        if parent and hasattr(parent, 'user_info'):
            self.current_user_id = parent.user_info.get('id')
            self.current_username = parent.user_info.get('username', 'unknown')

        self.init_ui()
        if initial_table:
            self.load_table(initial_table)

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # === Выбор справочника ===
        select_group = QGroupBox("📋 Выбор справочника")
        select_layout = QHBoxLayout(select_group)
        select_layout.addWidget(QLabel("Справочник:"))
        
        self.table_combo = QComboBox()
        self.table_combo.setMinimumWidth(300)
        for table_name, config in REFERENCE_TABLES.items():
            display_name = f"{config['icon']} {config['title']} ({table_name})"
            self.table_combo.addItem(display_name, table_name)
        self.table_combo.currentIndexChanged.connect(self.on_table_changed)
        select_layout.addWidget(self.table_combo)
        select_layout.addStretch()
        layout.addWidget(select_group)

        # === Панель инструментов ===
        toolbar_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; } QPushButton:hover { background-color: #45a049; }")
        self.add_btn.clicked.connect(self.add_record)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; } QPushButton:hover { background-color: #1976D2; } QPushButton:disabled { background-color: #cccccc; }")
        self.edit_btn.clicked.connect(self.edit_record)
        self.edit_btn.setEnabled(False)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px 15px; border-radius: 5px; } QPushButton:hover { background-color: #d32f2f; } QPushButton:disabled { background-color: #cccccc; }")
        self.delete_btn.clicked.connect(self.delete_record)
        self.delete_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addStretch()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Поиск:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.setMinimumWidth(250)
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.refresh_data)
        search_layout.addWidget(refresh_btn)

        toolbar_layout.addLayout(search_layout)
        layout.addLayout(toolbar_layout)

        # === Таблица данных ===
        self.data_table = QTableWidget()
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.data_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.data_table.doubleClicked.connect(self.edit_record)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.data_table)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def on_table_changed(self, index):
        """Обработка смены таблицы"""
        table_name = self.table_combo.currentData()
        if table_name:
            self.load_table(table_name)

    def on_search_changed(self, text):
        """Обработка поиска"""
        if self.current_table:
            self.load_table(self.current_table)

    def on_selection_changed(self):
        """Обработка выделения строки"""
        has_selection = self.data_table.selectionModel().hasSelection()
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def refresh_data(self):
        """Обновление данных"""
        if self.current_table:
            self.load_table(self.current_table)

    def load_table(self, table_name: str):
        """Загрузка данных таблицы"""
        config = self.manager.get_table_config(table_name)
        if not config:
            return

        self.current_table = table_name
        display_columns = [col for col in config["columns"] if col != "id"]
        self.data_table.setColumnCount(len(display_columns))
        self.data_table.setHorizontalHeaderLabels(display_columns)

        model = self.manager.load_data(table_name, self.search_input.text())
        if model:
            self.data_table.setRowCount(model.rowCount())
            for row in range(model.rowCount()):
                # ✅ ID всегда в колонке 0 результата SQL
                record_id = model.data(model.index(row, 0))

                for col in range(len(display_columns)):
                    # Пропускаем колонку ID (она под индексом 0), поэтому +1
                    value = model.data(model.index(row, col + 1))
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # ✅ ПРИВЯЗЫВАЕМ ID К КАЖДОЙ ЯЧЕЙКЕ СТРОКИ через UserRole
                    item.setData(Qt.ItemDataRole.UserRole, record_id)
                    self.data_table.setItem(row, col, item)
            self.data_table.resizeRowsToContents()

    def _get_selected_record_id(self):
        """Безопасное получение ID выбранной записи"""
        selected = self.data_table.selectedItems()
        if not selected:
            return None
        # Берём ID из UserRole первой выбранной ячейки (защита от парсинга текста)
        return selected[0].data(Qt.ItemDataRole.UserRole)

    def add_record(self):
        """Добавление новой записи"""
        if not self.current_table:
            return
        config = self.manager.get_table_config(self.current_table)
        if not config:
            return

        dialog = RecordEditDialog(self, self.current_table, config, record_data=None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            success, new_id = self.manager.add_record(self.current_table, data)
            if success:
                QMessageBox.information(self, "Успех", f"✅ Запись добавлена!\nID: {new_id}")
                self.log_action('REFERENCE_CREATE', new_id, data)
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Ошибка", "❌ Не удалось добавить запись")

    def edit_record(self):
        """Редактирование записи"""
        record_id = self._get_selected_record_id()
        if not record_id:
            return

        config = self.manager.get_table_config(self.current_table)
        record = self.manager.get_record(self.current_table, record_id)
        if not record:
            QMessageBox.critical(self, "Ошибка", "Запись не найдена в базе данных")
            return

        dialog = RecordEditDialog(self, self.current_table, config, record_data=record)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            success = self.manager.update_record(self.current_table, record_id, data)
            if success:
                QMessageBox.information(self, "Успех", "✅ Запись обновлена!")
                self.log_action('REFERENCE_UPDATE', record_id, data)
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Ошибка", "❌ Не удалось обновить запись")

    def delete_record(self):
        """Удаление записи"""
        record_id = self._get_selected_record_id()
        if not record_id:
            return

        row = self.data_table.currentRow()
        record_name = self.data_table.item(row, 0).text() if self.data_table.item(row, 0) else "Без имени"

        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы действительно хотите удалить запись?\n\n"
            f"ID: {record_id}\nНазвание: {record_name}\n\n"
            f"⚠️ Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.manager.delete_record(self.current_table, record_id)
            if success:
                QMessageBox.information(self, "Успех", "✅ Запись удалена!")
                self.log_action('REFERENCE_DELETE', record_id, {'name': record_name})
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Ошибка", "❌ Не удалось удалить запись")

    def log_action(self, action_type: str, record_id: int, data: dict):
        """Логирование действий со справочниками"""
        if not self.parent_window or not hasattr(self.parent_window, 'audit_logger'):
            return
        try:
            self.parent_window.audit_logger.log_action(
                action_type=action_type,
                table_name=self.current_table,
                record_id=record_id,
                krd_id=None,
                description=f"Изменение справочника {self.current_table}: {action_type} (ID={record_id})"
            )
        except Exception as e:
            print(f"⚠️ Ошибка логирования: {e}")