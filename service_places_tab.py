"""
Вкладка мест службы
Только таблица с кнопками добавления/удаления
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from service_place_dialog import ServicePlaceDialog


class ServicePlacesTab(QWidget):
    """Вкладка мест службы"""
    
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
        title_label = QLabel("📍 Места службы")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Таблица мест службы
        self.places_model = QSqlQueryModel()
        self.places_table = QTableView()
        self.places_table.setModel(self.places_model)
        self.places_table.setAlternatingRowColors(True)
        self.places_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.places_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.places_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.places_table.setSortingEnabled(True)
        
        # Настройка заголовков
        header = self.places_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Настройка высоты строк
        self.places_table.verticalHeader().setDefaultSectionSize(35)
        
        # Подключение двойного клика для редактирования
        self.places_table.doubleClicked.connect(self.on_place_double_clicked)
        
        layout.addWidget(self.places_table)
        
        # Кнопки внизу
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        add_btn = QPushButton("➕ Добавить место службы")
        add_btn.setProperty("role", "info")
        add_btn.clicked.connect(self.on_add_place)
        button_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("🗑️ Удалить место службы")
        delete_btn.setProperty("role", "danger")
        delete_btn.clicked.connect(self.on_delete_place)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
    
    def load_data(self):
        """Загрузка данных из базы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                id,
                place_name as "Место службы",
                military_unit_id as "Военное управление",
                garrison_id as "Гарнизон",
                position_id as "Должность",
                place_contacts as "Контакты"
            FROM krd.service_places
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        self.places_model.setQuery(query)
        
        # Скрыть ID колонку
        self.places_table.setColumnHidden(0, True)
    
    def on_add_place(self):
        """Обработчик кнопки добавления места службы"""
        dialog = ServicePlaceDialog(self.db, self.krd_id, parent=self)
        
        if dialog.exec() == 1:  # QDialog.Accepted
            # Обновить таблицу после добавления
            self.load_data()
            
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='SERVICE_PLACE_ADDED',
                    table_name='service_places',
                    krd_id=self.krd_id,
                    description='Добавлено новое место службы'
                )
    
    def on_place_double_clicked(self, index):
        """Обработчик двойного клика по записи"""
        row = index.row()
        
        # Получить ID места службы из скрытой колонки
        id_index = self.places_model.index(row, 0)
        place_id = self.places_model.data(id_index)
        
        if not place_id:
            return
        
        # Загрузить полные данные места службы
        place_data = self.load_place_data(place_id)
        
        if place_data:
            # Открыть диалог редактирования
            dialog = ServicePlaceDialog(self.db, self.krd_id, place_data, parent=self)
            
            if dialog.exec() == 1:  # QDialog.Accepted
                # Обновить таблицу после редактирования
                self.load_data()
                
                if self.audit_logger:
                    self.audit_logger.log_action(
                        action_type='SERVICE_PLACE_EDITED',
                        table_name='service_places',
                        record_id=place_id,
                        krd_id=self.krd_id,
                        description='Отредактировано место службы'
                    )
    
    def on_delete_place(self):
        """Обработчик кнопки удаления места службы"""
        # Получить выбранную строку
        selected_indexes = self.places_table.selectedIndexes()
        
        if not selected_indexes:
            QMessageBox.warning(self, "Предупреждение", "⚠️ Выберите место службы для удаления")
            return
        
        # Получить ID места службы
        row = selected_indexes[0].row()
        id_index = self.places_model.index(row, 0)
        place_id = self.places_model.data(id_index)
        
        if not place_id:
            return
        
        # Получить информацию о месте службы для отображения в подтверждении
        place_name_index = self.places_model.index(row, 1)  # Колонка "Место службы"
        place_name = self.places_model.data(place_name_index)
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить место службы?\n\n"
            f"📍 {place_name}\n\n"
            "Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = QSqlQuery(self.db)
                query.prepare("DELETE FROM krd.service_places WHERE id = ?")
                query.addBindValue(place_id)
                
                if query.exec():
                    QMessageBox.information(self, "Успех", "✅ Место службы успешно удалено")
                    self.load_data()
                    
                    if self.audit_logger:
                        self.audit_logger.log_action(
                            action_type='SERVICE_PLACE_DELETED',
                            table_name='service_places',
                            record_id=place_id,
                            krd_id=self.krd_id,
                            description=f'Удалено место службы: {place_name}'
                        )
                else:
                    raise Exception(f"Ошибка SQL: {query.lastError().text()}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"❌ Ошибка удаления места службы:\n{str(e)}")
    
    def load_place_data(self, place_id):
        """Загрузка полных данных места службы для редактирования"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                id,
                place_name,
                military_unit_id,
                garrison_id,
                position_id,
                commanders,
                postal_index,
                postal_region,
                postal_district,
                postal_town,
                postal_street,
                postal_house,
                postal_building,
                postal_letter,
                postal_apartment,
                postal_room,
                place_contacts
            FROM krd.service_places
            WHERE id = ?
        """)
        query.addBindValue(place_id)
        query.exec()
        
        if query.next():
            return {
                'id': query.value('id'),
                'place_name': query.value('place_name') or '',
                'military_unit_id': query.value('military_unit_id'),
                'garrison_id': query.value('garrison_id'),
                'position_id': query.value('position_id'),
                'commanders': query.value('commanders') or '',
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
                'place_contacts': query.value('place_contacts') or ''
            }
        
        return None