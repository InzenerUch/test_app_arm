from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from soch_episode_dialog import SochEpisodeDialog
from ui_helpers import is_reader
class SochEpisodesTab(QWidget):
    data_changed = pyqtSignal()
    def __init__(self, krd_id, db_connection, audit_logger=None, user_info=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.user_info = user_info or {}
        self.is_read_only = is_reader(self.user_info)
        self.init_ui()
        self.load_data()
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        title_text = "📋 Эпизоды самовольного оставления части (СОЧ)"
        if self.is_read_only:
            title_text += " — [Просмотр]"
        title_label = QLabel(title_text)
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        self.episodes_model = QSqlQueryModel()
        self.episodes_table = QTableView()
        self.episodes_table.setModel(self.episodes_model)
        self.episodes_table.setAlternatingRowColors(True)
        self.episodes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.episodes_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.episodes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.episodes_table.setSortingEnabled(True)
        header = self.episodes_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.episodes_table.verticalHeader().setDefaultSectionSize(35)
        self.episodes_table.doubleClicked.connect(self.on_episode_double_clicked)
        layout.addWidget(self.episodes_table)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        if not self.is_read_only:
            add_btn = QPushButton("➕ Добавить эпизод СОЧ")
            add_btn.setProperty("role", "info")
            add_btn.clicked.connect(self.on_add_episode)
            button_layout.addWidget(add_btn)
            self.delete_btn = QPushButton("🗑️ Удалить эпизод")
            self.delete_btn.setProperty("role", "danger")
            self.delete_btn.clicked.connect(self.on_delete_episode)
            self.delete_btn.setEnabled(False)
            button_layout.addWidget(self.delete_btn)
        else:
            info_lbl = QLabel("🔒 Режим только для просмотра. Изменения недоступны.")
            info_lbl.setStyleSheet("color:
            button_layout.addWidget(info_lbl)
            button_layout.addStretch()
        layout.addLayout(button_layout)
        if not self.is_read_only:
            self.episodes_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    def on_selection_changed(self, selected, deselected):
        has_selection = self.episodes_table.selectionModel().hasSelection()
        self.delete_btn.setEnabled(has_selection)
    def load_data(self):
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
            WHERE krd_id = ? AND (is_deleted = FALSE OR is_deleted IS NULL)
            ORDER BY soch_date DESC
                    UPDATE krd.soch_episodes
                    SET is_deleted = TRUE,
                        deleted_at = CURRENT_TIMESTAMP,
                        deleted_by = :user_id
                    WHERE id = :id AND krd_id = :krd_id
Обработчик двойного клика по записи"""
        row = index.row()
        episode_id = self.episodes_model.data(self.episodes_model.index(row, 0))
        if not episode_id: return
        episode_data = self.load_episode_data(episode_id)
        if episode_data:
            dialog = SochEpisodeDialog(self.db, self.krd_id, episode_data, parent=self, read_only=self.is_read_only)
            if dialog.exec() == 1:
                self.load_data()
                self.data_changed.emit()
                if self.audit_logger and not self.is_read_only:
                    self.audit_logger.log_action(
                        action_type='SOCH_EDITED',
                        table_name='soch_episodes',
                        record_id=episode_id,
                        krd_id=self.krd_id,
                        description='Отредактирован эпизод СОЧ'
                    )
    def load_episode_data(self, episode_id):
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT id, soch_date, soch_location, order_date_number, witnesses, reasons,
                   weapon_info, clothing, movement_options, other_info,
                   duty_officer_commissariat, duty_officer_omvd, investigation_info,
                   prosecution_info, criminal_case_info, search_date, found_by,
                   search_circumstances, notification_recipient, notification_date, notification_number
            FROM krd.soch_episodes WHERE id = ?
        """)
        query.addBindValue(episode_id)
        query.exec()
        if query.next():
            return {
                'id': query.value('id'), 'soch_date': query.value('soch_date'),
                'soch_location': query.value('soch_location') or '',
                'order_date_number': query.value('order_date_number') or '',
                'witnesses': query.value('witnesses') or '',
                'reasons': query.value('reasons') or '', 'weapon_info': query.value('weapon_info') or '',
                'clothing': query.value('clothing') or '', 'movement_options': query.value('movement_options') or '',
                'other_info': query.value('other_info') or '', 'duty_officer_commissariat': query.value('duty_officer_commissariat') or '',
                'duty_officer_omvd': query.value('duty_officer_omvd') or '', 'investigation_info': query.value('investigation_info') or '',
                'prosecution_info': query.value('prosecution_info') or '', 'criminal_case_info': query.value('criminal_case_info') or '',
                'search_date': query.value('search_date'), 'found_by': query.value('found_by') or '',
                'search_circumstances': query.value('search_circumstances') or '', 'notification_recipient': query.value('notification_recipient') or '',
                'notification_date': query.value('notification_date'), 'notification_number': query.value('notification_number') or ''
            }
        return None