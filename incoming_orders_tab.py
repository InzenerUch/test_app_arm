# incoming_orders_tab.py
"""
Вкладка входящих поручений на розыск
✅ АДАПТИРОВАНО: Поддержка роли 'reader' (только просмотр)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtCore import Qt, pyqtSignal 
from PyQt6.QtGui import QFont
from incoming_order_dialog import IncomingOrderDialog
from ui_helpers import is_reader  # 🔒 Импорт проверки роли

class IncomingOrdersTab(QWidget):
    """Вкладка входящих поручений на розыск"""
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
        title_text = "📬 Входящие поручения на розыск" + (" — [Просмотр]" if self.is_read_only else "")
        title_label = QLabel(title_text)
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Таблица входящих поручений
        self.orders_model = QSqlQueryModel()
        self.orders_table = QTableView()
        self.orders_table.setModel(self.orders_model)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.orders_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.orders_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.orders_table.setSortingEnabled(True)
        
        # Настройка заголовков
        header = self.orders_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Настройка высоты строк
        self.orders_table.verticalHeader().setDefaultSectionSize(35)
        
        # 🔒 Двойной клик для редактирования только если НЕ читатель
        if not self.is_read_only:
            self.orders_table.doubleClicked.connect(self.on_order_double_clicked)
            
        layout.addWidget(self.orders_table)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if not self.is_read_only:
            # 🟢 Кнопки видны только для редакторов/админов
            add_btn = QPushButton("➕ Добавить поручение")
            add_btn.setProperty("role", "info")
            add_btn.clicked.connect(self.on_add_order)
            button_layout.addWidget(add_btn)
            
            delete_btn = QPushButton("🗑️ Удалить поручение")
            delete_btn.setProperty("role", "danger")
            delete_btn.clicked.connect(self.on_delete_order)
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
                initiator_full_name as "Инициатор",
                order_date as "Дата поручения",
                order_number as "Номер поручения",
                receipt_date as "Дата поступления",
                receipt_number as "Входящий номер"
            FROM krd.incoming_orders
            WHERE krd_id = ?
            ORDER BY receipt_date DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        self.orders_model.setQuery(query)
        
        # Скрыть ID колонку
        self.orders_table.setColumnHidden(0, True)
    
    def on_add_order(self):
        """Обработчик кнопки добавления поручения"""
        if self.is_read_only: return  # 🔒 Защита
        dialog = IncomingOrderDialog(self.db, self.krd_id, parent=self)
        if dialog.exec() == 1:
            self.load_data()
            self.data_changed.emit()
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='INCOMING_ORDER_ADDED',
                    table_name='incoming_orders',
                    krd_id=self.krd_id,
                    description='Добавлено новое входящее поручение'
                )
    
    def on_order_double_clicked(self, index):
        """Обработчик двойного клика по записи"""
        if self.is_read_only: return  # 🔒 Защита
        row = index.row()
        id_index = self.orders_model.index(row, 0)
        order_id = self.orders_model.data(id_index)
        if not order_id: return
            
        order_data = self.load_order_data(order_id)
        if order_data:
            dialog = IncomingOrderDialog(self.db, self.krd_id, order_data, parent=self)
            if dialog.exec() == 1:
                self.load_data()
                self.data_changed.emit()
                if self.audit_logger:
                    self.audit_logger.log_action(
                        action_type='INCOMING_ORDER_EDITED',
                        table_name='incoming_orders',
                        record_id=order_id,
                        krd_id=self.krd_id,
                        description='Отредактировано входящее поручение'
                    )
    
    def on_delete_order(self):
        """Обработчик кнопки удаления поручения"""
        if self.is_read_only: return  # 🔒 Защита
        
        selected_indexes = self.orders_table.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Предупреждение", "⚠️ Выберите поручение для удаления")
            return
        
        row = selected_indexes[0].row()
        id_index = self.orders_model.index(row, 0)
        order_id = self.orders_model.data(id_index)
        if not order_id: return
        
        initiator_index = self.orders_model.index(row, 1)
        order_number_index = self.orders_model.index(row, 3)
        initiator = self.orders_model.data(initiator_index)
        order_number = self.orders_model.data(order_number_index)
        
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы действительно хотите удалить поручение?\n\n"
            f"📬 Инициатор: {initiator}\n"
            f"📋 Номер: {order_number}\n\n"
            "Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = QSqlQuery(self.db)
                query.prepare("DELETE FROM krd.incoming_orders WHERE id = ?")
                query.addBindValue(order_id)
                if query.exec():
                    QMessageBox.information(self, "Успех", "✅ Поручение успешно удалено")
                    self.load_data()
                    self.data_changed.emit()
                    if self.audit_logger:
                        self.audit_logger.log_action(
                            action_type='INCOMING_ORDER_DELETED',
                            table_name='incoming_orders',
                            record_id=order_id,
                            krd_id=self.krd_id,
                            description=f'Удалено поручение: {order_number}'
                        )
                else:
                    raise Exception(f"Ошибка SQL: {query.lastError().text()}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"❌ Ошибка удаления поручения:\n{str(e)}")
    
    def load_order_data(self, order_id):
        """Загрузка полных данных поручения для редактирования"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                id, initiator_type_id, initiator_full_name, military_unit_id,
                order_date, order_number, receipt_date, receipt_number,
                postal_index, postal_region, postal_district, postal_town,
                postal_street, postal_house, postal_building, postal_letter,
                postal_apartment, postal_room, initiator_contacts,
                our_response_date, our_response_number
            FROM krd.incoming_orders
            WHERE id = ?
        """)
        query.addBindValue(order_id)
        query.exec()
        
        if query.next():
            return {
                'id': query.value('id'),
                'initiator_type_id': query.value('initiator_type_id'),
                'initiator_full_name': query.value('initiator_full_name') or '',
                'military_unit_id': query.value('military_unit_id'),
                'order_date': query.value('order_date'),
                'order_number': query.value('order_number') or '',
                'receipt_date': query.value('receipt_date'),
                'receipt_number': query.value('receipt_number') or '',
                'postal_index': query.value('postal_index') or '',
                'postal_region': query.value('postal_region') or '',
                'postal_district': query.value('postal_district') or '',
                'postal_town': query.value('postal_town') or '',
                'postal_street': query.value('postal_street') or '',
                'postal_house': query.value('postal_house') or '',
                'postal_building': query.value('postal_building') or '',
                'postal_letter': query.value('postal_letter') or '',
                'postal_apartment': query.value('postal_apartment') or '',
                'postal_room': query.value('postal_room') or '',
                'initiator_contacts': query.value('initiator_contacts') or '',
                'our_response_date': query.value('our_response_date'),
                'our_response_number': query.value('our_response_number') or ''
            }
        return None