# addresses_tab.py
"""
Вкладка адресов проживания
АДАПТИРОВАНО: Поддержка роли 'reader' (только просмотр)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from address_dialog import AddressDialog
from ui_helpers import is_reader  # 🔒 Импорт проверки роли

class AddressesTab(QWidget):
    """Вкладка адресов проживания"""
    data_changed = pyqtSignal()

    def __init__(self, krd_id, db_connection, audit_logger=None, user_info=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.user_info = user_info or {}
        self.is_read_only = is_reader(self.user_info)  # 🔒 Флаг режима чтения
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок (добавляем метку режима для читателя)
        title_text = "📍 Адреса проживания" + (" — [Просмотр]" if self.is_read_only else "")
        title_label = QLabel(title_text)
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Таблица адресов
        self.addresses_model = QSqlQueryModel()
        self.addresses_table = QTableView()
        self.addresses_table.setModel(self.addresses_model)
        self.addresses_table.setAlternatingRowColors(True)
        self.addresses_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.addresses_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.addresses_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.addresses_table.setSortingEnabled(True)
        
        # Настройка заголовков
        header = self.addresses_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Настройка высоты строк
        self.addresses_table.verticalHeader().setDefaultSectionSize(35)
        
        # 🔒 Двойной клик для редактирования только если НЕ читатель
        if not self.is_read_only:
            self.addresses_table.doubleClicked.connect(self.on_address_double_clicked)
            
        layout.addWidget(self.addresses_table)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if not self.is_read_only:
            # 🟢 Кнопки видны только для редакторов/админов
            add_btn = QPushButton("➕ Добавить адрес")
            add_btn.setProperty("role", "info") 
            add_btn.clicked.connect(self.on_add_address)
            button_layout.addWidget(add_btn)
            
            delete_btn = QPushButton("🗑️ Удалить адрес")
            delete_btn.setProperty("role", "danger")
            delete_btn.clicked.connect(self.on_delete_address)
            button_layout.addWidget(delete_btn)
        else:
            # 🔒 Для читателя показываем информационную метку
            info_lbl = QLabel("🔒 Режим только для просмотра. Изменения недоступны.")
            info_lbl.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
            button_layout.addWidget(info_lbl)
            button_layout.addStretch()
            
        layout.addLayout(button_layout)

    def load_data(self):
        """Загрузка данных из базы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT
                id,
                region as "Субъект РФ",
                district as "Район",
                town as "Населенный пункт",
                street as "Улица",
                house as "Дом",
                building as "Корпус",
                letter as "Литер",
                apartment as "Квартира",
                room as "Комната",
                check_date as "Дата проверки",
                check_result as "Результат"
            FROM krd.addresses
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        self.addresses_model.setQuery(query)
        # Скрыть ID колонку
        self.addresses_table.setColumnHidden(0, True)

    def on_add_address(self):
        """Обработчик кнопки добавления адреса"""
        if self.is_read_only: return  # 🔒 Защита от вызова
        dialog = AddressDialog(self.db, self.krd_id, parent=self)
        if dialog.exec() == 1:  
            self.load_data()
            self.data_changed.emit()
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='ADDRESS_ADDED',
                    table_name='addresses',
                    krd_id=self.krd_id,
                    description='Добавлен новый адрес проживания'
                )

    def on_address_double_clicked(self, index):
        """Обработчик двойного клика по записи"""
        if self.is_read_only: return  # 🔒 Защита от вызова
        row = index.row()
        id_index = self.addresses_model.index(row, 0)
        address_id = self.addresses_model.data(id_index)
        if not address_id:
            return
            
        address_data = self.load_address_data(address_id)
        if address_data:
            dialog = AddressDialog(self.db, self.krd_id, address_data, parent=self)
            if dialog.exec() == 1:  
                self.load_data()
                self.data_changed.emit()
                if self.audit_logger:
                    self.audit_logger.log_action(
                        action_type='ADDRESS_EDITED',
                        table_name='addresses',
                        record_id=address_id,
                        krd_id=self.krd_id,
                        description='Отредактирован адрес проживания'
                    )

    def on_delete_address(self):
        """Обработчик кнопки удаления адреса"""
        if self.is_read_only: return  # 🔒 Защита от вызова
        selected_indexes = self.addresses_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Предупреждение", "⚠️ Выберите адрес для удаления")
            return
            
        row = selected_indexes[0].row()
        id_index = self.addresses_model.index(row, 0)
        address_id = self.addresses_model.data(id_index)
        if not address_id:
            return
            
        town_index = self.addresses_model.index(row, 3)  
        town = self.addresses_model.data(town_index)
        
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить адрес?\n📍 {town}\nЭто действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = QSqlQuery(self.db)
                query.prepare("DELETE FROM krd.addresses WHERE id = ?")
                query.addBindValue(address_id)
                if query.exec():
                    QMessageBox.information(self, "Успех", "✅ Адрес успешно удалён")
                    self.load_data()
                    self.data_changed.emit()
                    if self.audit_logger:
                        self.audit_logger.log_action(
                            action_type='ADDRESS_DELETED',
                            table_name='addresses',
                            record_id=address_id,
                            krd_id=self.krd_id,
                            description=f'Удалён адрес: {town}'
                        )
                else:
                    raise Exception(f"Ошибка SQL: {query.lastError().text()}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"❌ Ошибка удаления адреса:\n{str(e)}")

    def load_address_data(self, address_id):
        """Загрузка полных данных адреса для редактирования"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT id, region, district, town, street, house, building,
                   letter, apartment, room, check_date, check_result
            FROM krd.addresses WHERE id = ?
        """)
        query.addBindValue(address_id)
        query.exec()
        if query.next():
            return {
                'id': query.value('id'),
                'region': query.value('region') or '', 'district': query.value('district') or '',
                'town': query.value('town') or '', 'street': query.value('street') or '',
                'house': query.value('house') or '', 'building': query.value('building') or '',
                'letter': query.value('letter') or '', 'apartment': query.value('apartment') or '',
                'room': query.value('room') or '', 'check_date': query.value('check_date'),
                'check_result': query.value('check_result') or ''
            }
        return None