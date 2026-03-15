"""
Вкладка генерации документов
✅ ИСПОЛЬЗУЕТ ЕДИНУЮ КАРТУ КОЛОНОК ИЗ db_mappings.py
✅ АВТООБНОВЛЕНИЕ СПИСКОВ С repaint() И blockSignals()
✅ ПОЛНАЯ СОВМЕСТИМОСТЬ С QPSQL (:param вместо ?)
✅ КОРРЕКТНАЯ ПЕРЕДАЧА ID АДРЕСАТА В ДВИЖОК
"""
import os
import json
import re
import traceback
from docx.shared import Pt, Cm
from docx import Document
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QComboBox,
    QGridLayout, QMessageBox, QTabWidget, QTableView, QHeaderView, QAbstractItemView, QApplication
)
from PyQt6.QtCore import Qt, QByteArray, QDate, pyqtSignal
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont

# Импорт модулей проекта
from template_manager import TemplateManager
from recipient_widgets import RecipientWidget
from mapping_editor_dialog import MappingEditorDialog
from composite_field_widget import CompositeFieldWidget
from field_mapping_manager import FieldMappingManager
from database_handler import DatabaseHandler
from doc_generation_engine import DocGenerationEngine

# ✅ ИМПОРТ ЕДИНОЙ КАРТЫ КОЛОНОК
try:
    from db_mappings import DB_COLUMNS_MAP
except ImportError:
    DB_COLUMNS_MAP = {}

class DocumentGeneratorTab(QWidget):
    """Главная вкладка генерации документов с автообновлением списков"""
    request_saved = pyqtSignal()

    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        self.template_variables = []
        self.db_columns = DB_COLUMNS_MAP.copy() # ✅ ЗАГРУЖАЕМ ИЗ ЕДИНОГО ИСТОЧНИКА
        self.current_template_id = None
        self.current_table_name = "social_data"
        self.used_tables_in_mappings = set()
        
        self.selected_address_id = None
        self.selected_service_place_id = None
        self.selected_soch_episode_id = None
        self.selected_incoming_order_id = None

        self.tmpl_mgr = TemplateManager(db_connection)
        self.recipient_widget = RecipientWidget(db_connection, self)
        self.composite_widget = CompositeFieldWidget(self)
        self.mapping_manager = FieldMappingManager(self)
        self.db_handler = DatabaseHandler(self.db)
        self.engine = DocGenerationEngine(db_connection, krd_id, audit_logger)
        self.engine.set_columns_map(self.db_columns)
        
        self.tmpl_mgr.template_changed.connect(self.load_document_templates)
        self.init_ui()
        self.load_document_templates()
        self.load_related_records()
        
    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        tabs.addTab(self.create_generate_tab(), "Генерация документов")
        tabs.addTab(self.create_templates_tab(), "Управление шаблонами")
        layout.addWidget(tabs)
        self.setLayout(layout)

    def create_generate_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Генерация документов из шаблонов", font=QFont("Arial", 12, QFont.Weight.Bold)))

        records_group = QGroupBox("📋 Выбор записей для подстановки")
        records_layout = QGridLayout(records_group)
        records_layout.setSpacing(10)

        records_layout.addWidget(QLabel("🏠 Адрес проживания:"), 0, 0)
        self.address_combo = QComboBox()
        self.address_combo.addItem("— Не выбрано —", None)
        self.address_combo.currentIndexChanged.connect(self.on_address_selected)
        records_layout.addWidget(self.address_combo, 0, 1)

        records_layout.addWidget(QLabel("🎖️ Место службы:"), 0, 2)
        self.service_place_combo = QComboBox()
        self.service_place_combo.addItem("— Не выбрано —", None)
        self.service_place_combo.currentIndexChanged.connect(self.on_service_place_selected)
        records_layout.addWidget(self.service_place_combo, 0, 3)

        records_layout.addWidget(QLabel("⚠️ Эпизод СОЧ:"), 1, 0)
        self.soch_episode_combo = QComboBox()
        self.soch_episode_combo.addItem("— Не выбрано —", None)
        self.soch_episode_combo.currentIndexChanged.connect(self.on_soch_episode_selected)
        records_layout.addWidget(self.soch_episode_combo, 1, 1)
        
        records_layout.addWidget(QLabel("Входящее поручение:"), 1, 2)
        self.incoming_order_combo = QComboBox()
        self.incoming_order_combo.setMinimumWidth(300)
        self.incoming_order_combo.addItem("— Не выбрано —", None)
        self.incoming_order_combo.currentIndexChanged.connect(self.on_incoming_order_selected) 
        records_layout.addWidget(self.incoming_order_combo, 1, 3)

        records_layout.addWidget(QPushButton("🔄 Обновить списки", clicked=self.load_related_records), 2, 2, 2, 2)
        layout.addWidget(records_group)

        template_group = QGroupBox("📄 Выбор шаблона")
        template_layout = QGridLayout(template_group)
        template_layout.addWidget(QLabel("Шаблон:"), 0, 0)
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(300)
        self.template_combo.currentIndexChanged.connect(self.on_template_changed)
        template_layout.addWidget(self.template_combo, 0, 1)
        template_layout.addWidget(QPushButton("✏️ Сопоставления", clicked=self.open_mapping_editor), 0, 2)
        layout.addWidget(template_group)

        metadata_group = QGroupBox("📝 Метаданные запроса")
        metadata_layout = QGridLayout(metadata_group)
        metadata_layout.addWidget(QLabel("Адресат *:"), 0, 0)
        metadata_layout.addWidget(self.recipient_widget, 0, 1)
        layout.addWidget(metadata_group)
        
        btn = QPushButton("📄 Сформировать и сохранить в базу")
        btn.setMinimumHeight(60)
        btn.setProperty("role", "save")
        btn.clicked.connect(self.generate_and_save_document)
        layout.addWidget(btn)
        layout.addStretch()
        return widget

    def create_templates_tab(self):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.addWidget(QLabel("📄 Управление шаблонами", font=QFont("Arial", 14, QFont.Weight.Bold)))
        btns = QHBoxLayout()
        for lbl, fn, prop in [("➕ Добавить", lambda: self.tmpl_mgr.add_template_dialog(self), "info"),
                              ("✏️ Редактировать", lambda: self.tmpl_mgr.edit_template_dialog(self), "edit"),
                              ("🗑️ Удалить", lambda: self.tmpl_mgr.delete_selected(self), "danger"),
                              ("🔄 Обновить", self.tmpl_mgr.load_templates, "info")]:
            b = QPushButton(lbl)
            if prop: b.setProperty("role", prop)
            b.clicked.connect(fn)
            btns.addWidget(b)
        lay.addLayout(btns)
        tbl = QTableView()
        self.tmpl_mgr.bind_view(tbl)
        self.tmpl_mgr.load_templates()
        lay.addWidget(tbl)
        return widget

    def load_related_records(self):
        """Перезагружает выпадающие списки с защитой от рекурсии сигналов"""
        if not hasattr(self, 'address_combo'): return
        
        print(f"\n🔄 [AUTO-UPDATE] Начало обновления ComboBox для КРД-{self.krd_id}")
        queries = [
            (self.address_combo, "SELECT id, COALESCE(region,'')||', '||COALESCE(town,'')||', '||COALESCE(street,'')||', '||COALESCE(house,'') FROM krd.addresses WHERE krd_id=:krd_id AND (is_deleted = FALSE OR is_deleted IS NULL) ORDER BY id DESC", "🏠"),
            (self.service_place_combo, "SELECT id, COALESCE(place_name,'')||' ('||COALESCE(postal_town,'')||')' FROM krd.service_places WHERE krd_id=:krd_id AND (is_deleted = FALSE OR is_deleted IS NULL) ORDER BY id DESC", "🎖️"),
            (self.soch_episode_combo, "SELECT id, COALESCE(soch_date::text,'')||' - '||COALESCE(soch_location,'') FROM krd.soch_episodes WHERE krd_id=:krd_id AND (is_deleted = FALSE OR is_deleted IS NULL) ORDER BY soch_date DESC", "⚠️"),
            (self.incoming_order_combo, "SELECT id, CONCAT(order_number, ' от ', order_date::text, ' (', initiator_full_name, ')') FROM krd.incoming_orders WHERE krd_id=:krd_id AND (is_deleted = FALSE OR is_deleted IS NULL) ORDER BY id DESC", "📥")
        ]
        
        for combo, sql, label in queries:
            combo.blockSignals(True)
            current_id = combo.currentData()
            combo.clear()
            combo.addItem("— Не выбрано —", None)
            
            q = QSqlQuery(self.db)
            q.prepare(sql)
            q.bindValue(":krd_id", self.krd_id)
            if q.exec():
                while q.next(): combo.addItem(f"{label} {q.value(1)}", q.value(0))
            
            if current_id is not None:
                idx = combo.findData(current_id)
                if idx >= 0: combo.setCurrentIndex(idx)
            combo.blockSignals(False)
            combo.repaint()
        print("✅ [AUTO-UPDATE] Обновление завершено\n")

    def on_incoming_order_selected(self, index): self.selected_incoming_order_id = self.incoming_order_combo.currentData()
    def on_address_selected(self, index): self.selected_address_id = self.address_combo.currentData()
    def on_service_place_selected(self, index): self.selected_service_place_id = self.service_place_combo.currentData()
    def on_soch_episode_selected(self, index): self.selected_soch_episode_id = self.soch_episode_combo.currentData()

    def on_template_changed(self):
        self.current_template_id = self.template_combo.currentData()
        self.used_tables_in_mappings = self.get_used_tables(self.current_template_id) if self.current_template_id else set()

    def open_mapping_editor(self):
        if not self.current_template_id:
            return QMessageBox.warning(self, "Ошибка", "Выберите шаблон")
        dlg = MappingEditorDialog(self, krd_id=self.krd_id, db_connection=self.db, template_id=self.current_template_id, audit_logger=self.audit_logger)
        if dlg.exec() == 1:
            self.used_tables_in_mappings = self.get_used_tables(self.current_template_id)
            QMessageBox.information(self, "Успех", "Сопоставления обновлены")

    def get_used_tables(self, template_id):
        q = QSqlQuery(self.db)
        q.prepare("SELECT table_name FROM krd.field_mappings WHERE template_id=:tid")
        q.bindValue(":tid", template_id)
        tables = set()
        if q.exec():
            while q.next(): tables.add(q.value(0))
        return tables

    def load_document_templates(self):
        self.template_combo.clear()
        self.template_combo.addItem("— Не выбрано —", None)
        q = QSqlQuery(self.db)
        q.prepare("SELECT id, name FROM krd.document_templates WHERE is_deleted=FALSE ORDER BY name")
        if q.exec():
            while q.next(): self.template_combo.addItem(q.value(1), q.value(0))

    def _get_default_request_type_id(self):
        q = QSqlQuery(self.db)
        q.prepare("SELECT id FROM krd.request_types ORDER BY name LIMIT 1")
        if q.exec() and q.next(): return q.value(0)
        return None

    def _get_used_source_tables(self, template_id):
        query = QSqlQuery(self.db)
        # ✅ ИМЕНОВАННЫЙ ПАРАМЕТР
        query.prepare("SELECT DISTINCT table_name FROM krd.field_mappings WHERE template_id = :tid")
        query.bindValue(":tid", template_id)
        used_tables = set()
        if query.exec():
            while query.next(): used_tables.add(query.value(0))
        return used_tables

    def generate_and_save_document(self):
        tid = self.current_template_id
        rec_id = self.recipient_widget.current_id()
        
        if not tid: return QMessageBox.warning(self, "Ошибка", "Выберите шаблон")
        
        rt_id = None
        if rec_id:
            q = QSqlQuery(self.db)
            q.prepare("SELECT request_type_id FROM krd.recipients WHERE id = :rid")
            q.bindValue(":rid", rec_id)
            if q.exec() and q.next(): rt_id = q.value(0)
                
        if not rt_id: rt_id = self._get_default_request_type_id()
        if not rt_id: return QMessageBox.warning(self, "Ошибка", "Справочник типов запросов пуст!")
        
        used_tables = self._get_used_source_tables(tid)
        table_to_attr = {
            'addresses': 'selected_address_id', 'incoming_orders': 'selected_incoming_order_id',
            'soch_episodes': 'selected_soch_episode_id', 'service_places': 'selected_service_place_id'
        }
        
        for table, attr in table_to_attr.items():
            if table in used_tables and getattr(self, attr) is None:
                return QMessageBox.warning(self, "Требуется выбор", f"Шаблон использует данные из таблицы «{table}», но список не выбран.")
                
        selections = {
            "addresses": self.selected_address_id if 'addresses' in used_tables else None,
            "service_places": self.selected_service_place_id if 'service_places' in used_tables else None,
            "soch_episodes": self.selected_soch_episode_id if 'soch_episodes' in used_tables else None,
            "incoming_orders": self.selected_incoming_order_id if 'incoming_orders' in used_tables else None,
            "recipients": rec_id if 'recipients' in used_tables else None
        }
        
        try:
            q = QSqlQuery(self.db)
            q.prepare("SELECT template_data, name FROM krd.document_templates WHERE id = :tid")
            q.bindValue(":tid", tid)
            if not q.exec() or not q.next(): raise Exception("Шаблон не найден в БД")
                
            tpl_name = q.value(1)
            tpl_data = bytes(q.value(0)) if not isinstance(q.value(0), bytes) else q.value(0)
            
            context = self.engine.build_context(tid, selections)
            output_path, replacements = self.engine.apply_to_docx(tpl_data, context)
            
            num = self.engine.generate_issue_number()
            with open(output_path, 'rb') as f: doc_bytes = f.read()
                
            request_id = self.engine.save_to_database(rt_id, rec_id, num, doc_bytes)
            os.unlink(output_path)
            
            QMessageBox.information(self, "Успех", f"Документ успешно сгенерирован!\n📄 Шаблон: {tpl_name}\n🔢 Номер: {num}\n🔄 Заменено переменных: {replacements}")
            self.request_saved.emit()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка генерации", str(e))

    def load_db_columns(self):
        # ✅ ТЕПЕРЬ ВОЗВРАЩАЕМ ЕДИНУЮ КАРТУ ВМЕСТО ХАРДКОДА
        return self.db_columns