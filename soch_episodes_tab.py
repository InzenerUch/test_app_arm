"""
Вкладка сведений о самовольном оставлении части (СОЧ)
С диалоговыми окнами для добавления/редактирования
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor

from soch_episode_dialog import SochEpisodeDialog


class SochEpisodesTab(QWidget):
    """Вкладка сведений о СОЧ"""
    
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
        title_label = QLabel("📋 Эпизоды самовольного оставления части (СОЧ)")
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Таблица эпизодов
        self.episodes_model = QSqlQueryModel()
        self.episodes_table = QTableView()
        self.episodes_table.setModel(self.episodes_model)
        self.episodes_table.setAlternatingRowColors(True)
        self.episodes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.episodes_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.episodes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.episodes_table.setSortingEnabled(True)
        
        # Настройка заголовков
        header = self.episodes_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
        # Настройка высоты строк
        self.episodes_table.verticalHeader().setDefaultSectionSize(35)
        
        # Подключение двойного клика
        self.episodes_table.doubleClicked.connect(self.on_episode_double_clicked)
        
        layout.addWidget(self.episodes_table)
        
        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        add_btn = QPushButton("➕ Добавить эпизод СОЧ")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self.on_add_episode)
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
    
    def load_data(self):
        """Загрузка данных из базы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                id,
                soch_date as "Дата СОЧ",
                soch_location as "Место СОЧ",
                order_date_number as "Приказ",
                found_by as "Кем разыскан",
                search_date as "Дата розыска",
                notification_number as "Уведомление"
            FROM krd.soch_episodes
            WHERE krd_id = ?
            ORDER BY soch_date DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        self.episodes_model.setQuery(query)
        
        # Настройка заголовков
        self.episodes_model.setHeaderData(0, Qt.Orientation.Horizontal, "ID")
        
        # Скрыть ID колонку
        self.episodes_table.setColumnHidden(0, True)
    
    def on_add_episode(self):
        """Обработчик кнопки добавления эпизода"""
        dialog = SochEpisodeDialog(self.db, self.krd_id, parent=self)
        
        if dialog.exec() == 1:  # QDialog.Accepted
            # Обновить таблицу после добавления
            self.load_data()
            
            if self.audit_logger:
                self.audit_logger.log_action(
                    action_type='SOCH_ADDED',
                    table_name='soch_episodes',
                    krd_id=self.krd_id,
                    description='Добавлен новый эпизод СОЧ'
                )
    
    def on_episode_double_clicked(self, index):
        """Обработчик двойного клика по записи"""
        row = index.row()
        
        # Получить ID эпизода из скрытой колонки
        id_index = self.episodes_model.index(row, 0)
        episode_id = self.episodes_model.data(id_index)
        
        if not episode_id:
            return
        
        # Загрузить полные данные эпизода
        episode_data = self.load_episode_data(episode_id)
        
        if episode_data:
            # Открыть диалог редактирования
            dialog = SochEpisodeDialog(self.db, self.krd_id, episode_data, parent=self)
            
            if dialog.exec() == 1:  # QDialog.Accepted
                # Обновить таблицу после редактирования
                self.load_data()
                
                if self.audit_logger:
                    self.audit_logger.log_action(
                        action_type='SOCH_EDITED',
                        table_name='soch_episodes',
                        record_id=episode_id,
                        krd_id=self.krd_id,
                        description='Отредактирован эпизод СОЧ'
                    )
    
    def load_episode_data(self, episode_id):
        """Загрузка полных данных эпизода для редактирования"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                id,
                soch_date,
                soch_location,
                order_date_number,
                witnesses,
                reasons,
                weapon_info,
                clothing,
                movement_options,
                other_info,
                duty_officer_commissariat,
                duty_officer_omvd,
                investigation_info,
                prosecution_info,
                criminal_case_info,
                search_date,
                found_by,
                search_circumstances,
                notification_recipient,
                notification_date,
                notification_number
            FROM krd.soch_episodes
            WHERE id = ?
        """)
        query.addBindValue(episode_id)
        query.exec()
        
        if query.next():
            return {
                'id': query.value('id'),
                'soch_date': query.value('soch_date'),
                'soch_location': query.value('soch_location') or '',
                'order_date_number': query.value('order_date_number') or '',
                'witnesses': query.value('witnesses') or '',
                'reasons': query.value('reasons') or '',
                'weapon_info': query.value('weapon_info') or '',
                'clothing': query.value('clothing') or '',
                'movement_options': query.value('movement_options') or '',
                'other_info': query.value('other_info') or '',
                'duty_officer_commissariat': query.value('duty_officer_commissariat') or '',
                'duty_officer_omvd': query.value('duty_officer_omvd') or '',
                'investigation_info': query.value('investigation_info') or '',
                'prosecution_info': query.value('prosecution_info') or '',
                'criminal_case_info': query.value('criminal_case_info') or '',
                'search_date': query.value('search_date'),
                'found_by': query.value('found_by') or '',
                'search_circumstances': query.value('search_circumstances') or '',
                'notification_recipient': query.value('notification_recipient') or '',
                'notification_date': query.value('notification_date'),
                'notification_number': query.value('notification_number') or ''
            }
        
        return None