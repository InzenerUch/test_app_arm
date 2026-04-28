"""
Вкладка адресов проживания
Только таблица с кнопками добавления/удаления
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from address_dialog import AddressDialog


class AddressesTab(QWidget):
    """Вкладка адресов проживания"""
    
    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("📍 Адреса проживания")
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
        
        # Подключение двойного клика для редактирования
        self.addresses_table.doubleClicked.connect(self.on_address_double_clicked)
        
        layout.addWidget(self.addresses_table)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        add_btn = QPushButton("➕ Добавить адрес")
        add_btn.setProperty("role", "info") 
        add_btn.clicked.connect(self.on_add_address)
        button_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("🗑️ Удалить адрес")
        delete_btn.setProperty("role", "danger")
        delete_btn.clicked.connect(self.on_delete_address)
        button_layout.addWidget(delete_btn)
        
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
        dialog = AddressDialog(self.db, self.krd_id, parent=self)
        
        if dialog.exec() == 1:  # QDialog.Accepted
            # Обновить таблицу после добавления
            self.load_data()
            
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='ADDRESS_ADDED',
                    table_name='addresses',
                    krd_id=self.krd_id,
                    description='Добавлен новый адрес проживания'
                )
    
    def on_address_double_clicked(self, index):
        """Обработчик двойного клика по записи"""
        row = index.row()
        
        # Получить ID адреса из скрытой колонки
        id_index = self.addresses_model.index(row, 0)
        address_id = self.addresses_model.data(id_index)
        
        if not address_id:
            return
        
        # Загрузить полные данные адреса
        address_data = self.load_address_data(address_id)
        
        if address_data:
            # Открыть диалог редактирования
            dialog = AddressDialog(self.db, self.krd_id, address_data, parent=self)
            
            if dialog.exec() == 1:  # QDialog.Accepted
                # Обновить таблицу после редактирования
                self.load_data()
                
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
        # Получить выбранную строку
        selected_indexes = self.addresses_table.selectedIndexes()
        
        if not selected_indexes:
            QMessageBox.warning(self, "Предупреждение", "⚠️ Выберите адрес для удаления")
            return
        
        # Получить ID адреса
        row = selected_indexes[0].row()
        id_index = self.addresses_model.index(row, 0)
        address_id = self.addresses_model.data(id_index)
        
        if not address_id:
            return
        
        # Получить адрес для отображения в подтверждении
        town_index = self.addresses_model.index(row, 3)  # Колонка "Населенный пункт"
        town = self.addresses_model.data(town_index)
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить адрес?\n\n📍 {town}\n\nЭто действие нельзя отменить!",
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
            SELECT 
                id,
                region,
                district,
                town,
                street,
                house,
                building,
                letter,
                apartment,
                room,
                check_date,
                check_result
            FROM krd.addresses
            WHERE id = ?
        """)
        query.addBindValue(address_id)
        query.exec()
        
        if query.next():
            return {
                'id': query.value('id'),
                'region': query.value('region') or '',
                'district': query.value('district') or '',
                'town': query.value('town') or '',
                'street': query.value('street') or '',
                'house': query.value('house') or '',
                'building': query.value('building') or '',
                'letter': query.value('letter') or '',
                'apartment': query.value('apartment') or '',
                'room': query.value('room') or '',
                'check_date': query.value('check_date'),
                'check_result': query.value('check_result') or ''
            }
        
        return None