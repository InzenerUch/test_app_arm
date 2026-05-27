# krd_version_preview_window.py
"""
Легковесное окно для предпросмотра версии КРД.
Полностью изолировано: без блокировок, без автосохранения, только чтение.
"""
import json
import traceback
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QMessageBox,
    QComboBox, QPushButton, QLabel, QWidget, QAbstractItemView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtCore import Qt,QTimer

from social_data_tab import SocialDataTab
from addresses_tab import AddressesTab
from incoming_orders_tab import IncomingOrdersTab
from service_places_tab import ServicePlacesTab
from soch_episodes_tab import SochEpisodesTab
from outgoing_requests_tab import OutgoingRequestsTab
from ui_helpers import apply_readonly_mode

class KrdVersionPreviewWindow(QDialog):
    def __init__(self, db_connection, krd_id, version_id, user_info, audit_logger=None, parent=None):
        super().__init__(parent)  # ✅ Передаем родителя
        print(f"🟢 [PREVIEW] Инициализация окна для версии #{version_id}")
        
        self.db = db_connection
        self.krd_id = krd_id
        self.version_id = version_id
        self.user_info = user_info
        self.audit_logger = audit_logger

        self.setWindowTitle(f"Карточка розыска №{krd_id} — [Просмотр версии #{version_id}]")
        
        # ✅ УБРАН WindowStaysOnTopHint (вызывает Z-order fighting и блокировку фокуса)
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint | 
            Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(1100, 750)
        
        self._init_ui()
        QTimer.singleShot(50, self.load_version_data)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        header_widget = QWidget()
        header_widget.setProperty("role", "header")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        title_label = QLabel(f"📋 <b>Карточка розыска №{self.krd_id}</b>")
        title_label.setStyleSheet("font-size: 16px; margin-right: 20px;")
        header_layout.addWidget(title_label)
        header_layout.addWidget(QLabel("📌 Статус:"))
        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(200)
        self.status_combo.setEnabled(False)
        header_layout.addWidget(self.status_combo)
        header_layout.addStretch()
        main_layout.addWidget(header_widget)
        self.load_statuses()

        self.banner = QLabel("⏳ Загрузка данных...")
        self.banner.setStyleSheet("background-color: #e3f2fd; color: #0d47a1; padding: 10px; font-weight: bold; text-align: center;")
        self.banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.banner)

        self.tabs = QTabWidget()
        self.social_data_tab = SocialDataTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.addresses_tab = AddressesTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.incoming_orders_tab = IncomingOrdersTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.service_places_tab = ServicePlacesTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        self.soch_episodes_tab = SochEpisodesTab(self.krd_id, self.db, self.audit_logger, self.user_info)
        
        self.tabs.addTab(self.social_data_tab, "👤 Социально-демографические данные")
        self.tabs.addTab(self.addresses_tab, "🏠 Адреса проживания")
        self.tabs.addTab(self.incoming_orders_tab, "📬 Входящие поручения")
        self.tabs.addTab(self.service_places_tab, "🎖️ Места службы")
        self.tabs.addTab(self.soch_episodes_tab, "⚠️ Сведения о СОЧ")
        
        main_layout.addWidget(self.tabs)

    def load_statuses(self):
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.statuses ORDER BY id")
        q2 = QSqlQuery(self.db)
        q2.prepare("SELECT status_id FROM krd.krd WHERE id = :id")
        q2.bindValue(":id", self.krd_id)
        current = q2.value(0) if q2.exec() and q2.next() else 1
        while q.next():
            self.status_combo.addItem(q.value(1), q.value(0))
        idx = self.status_combo.findData(current)
        if idx >= 0: self.status_combo.setCurrentIndex(idx)

    def load_version_data(self):
        print(f"🟢 [PREVIEW] Загрузка данных для версии #{self.version_id}")
        try:
            q = QSqlQuery(self.db)
            q.prepare("SELECT snapshot_data FROM krd.krd_versions WHERE id = :id")
            q.bindValue(":id", self.version_id)
            if q.exec() and q.next():
                snapshot = json.loads(q.value(0))
                self.banner.setText("👁️ РЕЖИМ ПРЕДПРОСМОТРА: Историческая версия данных. Доступно только для чтения.")
                self.banner.setStyleSheet("background-color: #fff3cd; color: #856404; padding: 10px; font-weight: bold; text-align: center;")
                apply_readonly_mode(self, True)
                self.apply_snapshot(snapshot)
            else:
                self.banner.setText("❌ Версия не найдена в БД.")
        except Exception as e:
            self.banner.setText(f"❌ Ошибка: {e}")
            traceback.print_exc()

    def apply_snapshot(self, snapshot: dict):
        if 'social_data' in snapshot:
            for key, val in snapshot['social_data'].items():
                w_name = f"{key}_input"
                if hasattr(self.social_data_tab, w_name) and val is not None:
                    w = getattr(self.social_data_tab, w_name)
                    if hasattr(w, 'setText') and not hasattr(w, 'setDate'): w.setText(str(val))
                    elif hasattr(w, 'setPlainText'): w.setPlainText(str(val))

        for tab_attr, table_attr in [('addresses_tab', 'addresses_table'), ('service_places_tab', 'places_table'), ('soch_episodes_tab', 'episodes_table'), ('incoming_orders_tab', 'orders_table')]:
            key = tab_attr.replace('_tab', '')
            if key in snapshot:
                tv = getattr(self, tab_attr, None)
                if tv: tv = getattr(tv, table_attr)
                if tv: self._fill_table(tv, snapshot[key])

    def _fill_table(self, table_view, data_list):
        if not data_list: return
        m = QStandardItemModel()
        h = list(data_list[0].keys())
        m.setHorizontalHeaderLabels(h)
        for r in data_list: m.appendRow([QStandardItem(str(r.get(hh, ""))) for hh in h])
        table_view.setModel(m)
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_view.resizeColumnsToContents()