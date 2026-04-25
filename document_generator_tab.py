"""
Главная вкладка генерации документов
Интегрирует шаблоны, адресаты, маппинги и генерацию через DocGenerationEngine
"""
import os
import tempfile
import json
import re
import traceback
from docx.shared import Pt, Cm
from docx import Document
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QComboBox,
    QGridLayout, QMessageBox, QTabWidget, QTableView, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QByteArray, QDate, pyqtSignal
from PyQt6.QtSql import QSqlQuery, QSqlQueryModel
from PyQt6.QtGui import QFont
from template_manager import TemplateManager
from recipient_widgets import RecipientWidget
from mapping_editor_dialog import MappingEditorDialog
from composite_field_widget import CompositeFieldWidget
from field_mapping_manager import FieldMappingManager
from database_handler import DatabaseHandler
from doc_generation_engine import DocGenerationEngine  # ✅ Импорт движка

class DocumentGeneratorTab(QWidget):
    request_saved = pyqtSignal()

    def __init__(self, krd_id, db_connection, audit_logger=None):
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        self.audit_logger = audit_logger
        
        self.template_variables = []
        self.db_columns = {}
        self.generated_doc_path = None
        self.selected_file_path = None
        self.current_template_id = None
        self.current_table_name = "social_data"
        self.selected_address_id = None
        self.selected_service_place_id = None
        self.selected_soch_episode_id = None
        self.used_tables_in_mappings = set()
        
        self.tmpl_mgr = TemplateManager(db_connection)
        self.recipient_widget = RecipientWidget(db_connection, self)
        
        self.init_ui()
        
        self.composite_widget = CompositeFieldWidget(self)
        self.mapping_manager = FieldMappingManager(self)
        self.db_handler = DatabaseHandler(self.db)
        
        # ✅ Инициализация движка генерации
        self.engine = DocGenerationEngine(db_connection, krd_id, audit_logger)
        # ✅ Передаем карту колонок движку (чтобы он знал, где искать поля)
        # Загружаем колонки перед передачей
        self.load_db_columns() 
        self.engine.set_columns_map(self.db_columns)
        
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

        records_layout.addWidget(QPushButton("🔄 Обновить списки", clicked=self.load_related_records), 1, 2, 1, 2)
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
        metadata_layout.addWidget(QLabel("Тип запроса *:"), 0, 0)
        self.request_type_combo = QComboBox()
        self.load_request_types()
        metadata_layout.addWidget(self.request_type_combo, 0, 1)
        metadata_layout.addWidget(QLabel("Адресат *:"), 0, 2)
        metadata_layout.addWidget(self.recipient_widget, 0, 3)
        layout.addWidget(metadata_group)

        btn = QPushButton("📄 Сформировать и сохранить в базу")
        btn.setMinimumHeight(60)
        btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px; border-radius: 5px; padding: 20px; } QPushButton:hover { background-color: #45a049; }")
        btn.clicked.connect(self.generate_and_save_document)
        layout.addWidget(btn)
        layout.addStretch()
        return widget

    def create_templates_tab(self):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.addWidget(QLabel("📄 Управление шаблонами", font=QFont("Arial", 14, QFont.Weight.Bold)))
        btns = QHBoxLayout()
        for lbl, fn, style in [("➕ Добавить", lambda: self.tmpl_mgr.add_template_dialog(self), None),
                               ("✏️ Редактировать", lambda: self.tmpl_mgr.edit_template_dialog(self), None),
                               ("🗑️ Удалить", lambda: self.tmpl_mgr.delete_selected(self), "background-color:#ff6b6b;color:white;"),
                               ("🔄 Обновить", self.tmpl_mgr.load_templates, None)]:
            b = QPushButton(lbl)
            if style: b.setStyleSheet(style)
            b.clicked.connect(fn)
            btns.addWidget(b)
        lay.addLayout(btns)
        tbl = QTableView()
        self.tmpl_mgr.bind_view(tbl)
        self.tmpl_mgr.load_templates()
        lay.addWidget(tbl)
        return widget

    def load_related_records(self):
        for combo, sql, label in [
            (self.address_combo, "SELECT id, COALESCE(region,'')||', '||COALESCE(town,'')||', '||COALESCE(street,'')||', '||COALESCE(house,'') FROM krd.addresses WHERE krd_id=:krd_id ORDER BY id DESC", "🏠"),
            (self.service_place_combo, "SELECT id, COALESCE(place_name,'')||' ('||COALESCE(postal_town,'')||')' FROM krd.service_places WHERE krd_id=:krd_id ORDER BY id DESC", "🎖️"),
            (self.soch_episode_combo, "SELECT id, COALESCE(soch_date::text,'')||' - '||COALESCE(soch_location,'') FROM krd.soch_episodes WHERE krd_id=:krd_id ORDER BY soch_date DESC", "⚠️")
        ]:
            combo.clear()
            combo.addItem("— Не выбрано —", None)
            q = QSqlQuery(self.db)
            q.prepare(sql)
            q.bindValue(":krd_id", self.krd_id)
            if q.exec():
                while q.next():
                    combo.addItem(f"{label} {q.value(1)}", q.value(0))

    def load_request_types(self):
        self.request_type_combo.clear()
        q = QSqlQuery(self.db)
        q.exec("SELECT id, name FROM krd.request_types ORDER BY name")
        while q.next():
            self.request_type_combo.addItem(q.value(1), q.value(0))

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
        q.exec("SELECT id, name FROM krd.document_templates WHERE is_deleted=FALSE ORDER BY name")
        while q.next():
            self.template_combo.addItem(q.value(1), q.value(0))

    def on_address_selected(self, index): self.selected_address_id = self.address_combo.currentData()
    def on_service_place_selected(self, index): self.selected_service_place_id = self.service_place_combo.currentData()
    def on_soch_episode_selected(self, index): self.selected_soch_episode_id = self.soch_episode_combo.currentData()

    # ==========================================
    # ✅ ОБНОВЛЕННЫЙ МЕТОД ГЕНЕРАЦИИ (Использует Engine)
    # ==========================================
    def generate_and_save_document(self):
        tid = self.current_template_id
        rt_id = self.request_type_combo.currentData()
        rec_id = self.recipient_widget.current_id()
        
        if not tid: return QMessageBox.warning(self, "Ошибка", "Выберите шаблон")
        if not rt_id: return QMessageBox.warning(self, "Ошибка", "Выберите тип запроса")
        if not rec_id: return QMessageBox.warning(self, "Ошибка", "Выберите адресата")

        errs = []
        if "addresses" in self.used_tables_in_mappings and not self.selected_address_id: errs.append("Адрес")
        if "service_places" in self.used_tables_in_mappings and not self.selected_service_place_id: errs.append("Место службы")
        if "soch_episodes" in self.used_tables_in_mappings and not self.selected_soch_episode_id: errs.append("Эпизод СОЧ")
        if errs: return QMessageBox.warning(self, "Требуется выбор", f"Не выбрано: {', '.join(errs)}")

        try:
            # 1. Загружаем шаблон
            q = QSqlQuery(self.db)
            q.prepare("SELECT template_data, name FROM krd.document_templates WHERE id = ?")
            q.addBindValue(tid)
            if not q.exec() or not q.next(): 
                raise Exception("Шаблон не найден в БД")
            
            tpl_name = q.value(1)
            tpl_data = bytes(q.value(0)) if not isinstance(q.value(0), bytes) else q.value(0)
            
            # 2. Готовим выборки записей
            selections = {
                "addresses": self.selected_address_id,
                "service_places": self.selected_service_place_id,
                "soch_episodes": self.selected_soch_episode_id
            }
            
            # 3. Движок собирает контекст и применяет его к шаблону
            context = self.engine.build_context(tid, selections)
            output_path, replacements = self.engine.apply_to_docx(tpl_data, context)
            
            # 4. Сохраняем в БД
            num = self.engine.generate_issue_number()
            with open(output_path, 'rb') as f: 
                doc_bytes = f.read()
                
            request_id = self.engine.save_to_database(rt_id, rec_id, num, doc_bytes)
            os.unlink(output_path)  # Удаляем временный файл
            
            QMessageBox.information(self, "Успех", 
                f"Документ успешно сгенерирован!\n"
                f"📄 Шаблон: {tpl_name}\n"
                f"🔢 Номер: {num}\n"
                f"🔄 Заменено переменных: {replacements}")
            
            self.request_saved.emit()
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка генерации", str(e))

    def load_db_columns(self):
        self.db_columns = {
            "social_data": ["surname","name","patronymic","birth_date","birth_place_town","birth_place_district","birth_place_region","birth_place_country","tab_number","personal_number","category_id","rank_id","drafted_by_commissariat","draft_date","povsk","selection_date","education","criminal_record","social_media_account","bank_card_number","passport_series","passport_number","passport_issue_date","passport_issued_by","military_id_series","military_id_number","military_id_issue_date","military_id_issued_by","appearance_features","personal_marks","federal_search_info","military_contacts","relatives_info"],
            "addresses": ["region","district","town","street","house","building","letter","apartment","room","check_date","check_result"],
            "service_places": ["place_name","military_unit_id","garrison_id","position_id","commanders","postal_index","postal_region","postal_district","postal_town","postal_street","postal_house","postal_building","postal_letter","postal_apartment","postal_room","place_contacts"],
            "soch_episodes": ["soch_date","soch_location","order_date_number","witnesses","reasons","weapon_info","clothing","movement_options","other_info","duty_officer_commissariat","duty_officer_omvd","investigation_info","prosecution_info","criminal_case_info","search_date","found_by","search_circumstances","notification_recipient","notification_date","notification_number"]
        }