"""
Виджет для управления составными полями (Composite Fields)
✅ ИСПОЛЬЗУЕТ: ЕДИНЫЙ СПРАВОЧНИК из db_mappings.py
✅ ИСПРАВЛЕНО: Убраны дубликаты и несуществующие колонки
"""
import json
import traceback
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QMessageBox, QCompleter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from searchable_combo import SearchableComboBox

# ✅ ПОДКЛЮЧЕНИЕ: Импорт словарей и функции описания
try:
    from db_mappings import TABLE_NAMES_RU, COLUMN_DESCRIPTIONS, get_field_description
except ImportError:
    TABLE_NAMES_RU = {}
    COLUMN_DESCRIPTIONS = {}
    def get_field_description(t, c): return c  # Фоллбэк
    print("⚠️ Не удалось импортировать db_mappings.py. Описания полей будут использоваться по умолчанию.")

class CompositeFieldWidget:
    def __init__(self, parent):
        self.parent = parent
        if not hasattr(parent, 'db_columns'):
            try:
                from db_mappings import DB_COLUMNS_MAP
                parent.db_columns = DB_COLUMNS_MAP
            except ImportError:
                parent.db_columns = {}

    def _create_column_combo(self, selected_column=None, table_name=None):
        try:
            combo = SearchableComboBox()
            if combo is None: return None
            
            combo.setMaxVisibleItems(50)
            combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            combo.view().setMinimumHeight(400)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumWidth(350)
            combo.setMaximumWidth(600)
            
            completer = combo.completer()
            if completer:
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
                completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

            all_columns = []
            target_tables = self.parent.db_columns.keys()
            
            for tbl in target_tables:
                columns = self.parent.db_columns.get(tbl, [])
                for col in columns:
                    # ✅ ИСПОЛЬЗУЕМ get_field_description для получения русского названия
                    desc = get_field_description(tbl, col)
                    table_name_ru = TABLE_NAMES_RU.get(tbl, tbl)
                    display_desc = f"[{table_name_ru}] {desc}"
                    all_columns.append((f"{tbl}|{col}", display_desc))
            
            all_columns.sort(key=lambda x: x[1])

            for col_data, col_desc in all_columns:
                combo.addItem(col_desc, col_data)

            if selected_column:
                search_val = selected_column.strip()
                idx = -1
                if table_name:
                    idx = combo.findData(f"{table_name}|{search_val}")
                if idx < 0:
                    for i in range(combo.count()):
                        item_data = combo.itemData(i)
                        if item_data and item_data.endswith(f"|{search_val}"):
                            idx = i
                            break
                if idx >= 0: combo.setCurrentIndex(idx)
            
            return combo
        except Exception as e:
            print(f"❌ Ошибка создания ComboBox: {e}")
            combo = QComboBox()
            combo.addItem("Ошибка загрузки", None)
            return combo

    def create_composite_field_row(self, row, field_name, db_columns_json, table_name, mapping_table):
        try:
            mapping_table.insertRow(row)
            var_combo = QComboBox()
            vars_list = getattr(self.parent, 'template_variables', [])
            var_combo.addItems(vars_list if vars_list else [])
            var_combo.setCurrentText(field_name)
            var_combo.setMinimumWidth(200)

            composite_widget = QWidget()
            composite_layout = QVBoxLayout(composite_widget)
            composite_layout.setContentsMargins(5, 5, 5, 5)
            composite_layout.setSpacing(5)

            db_columns = json.loads(db_columns_json) if isinstance(db_columns_json, str) else db_columns_json
            if not db_columns: db_columns = [{'column': '', 'separator': ', '}]

            for idx, col_info in enumerate(db_columns):
                col_widget = self._create_composite_column_widget(row, idx, col_info, table_name)
                composite_layout.addWidget(col_widget)

            self._add_add_column_button(composite_layout, row, table_name)

            mapping_table.setCellWidget(row, 0, var_combo)
            mapping_table.setCellWidget(row, 1, composite_widget)
            mapping_table.setCellWidget(row, 2, self._create_type_label("Составное"))
            mapping_table.resizeRowToContents(row)
        except Exception as e:
            print(f"❌ Ошибка создания строки: {e}")

    def _create_composite_column_widget(self, row, idx, col_info, table_name):
        col_widget = QWidget()
        col_widget.setObjectName(f"col_widget_{row}_{idx}")
        col_layout = QHBoxLayout(col_widget)
        col_layout.setContentsMargins(8, 5, 8, 5)
        col_layout.setSpacing(8)

        num_label = QLabel(f"{idx + 1}.")
        num_label.setStyleSheet("font-weight: bold; color: #2196F3; min-width: 20px;")
        col_layout.addWidget(num_label)

        col_combo = self._create_column_combo(col_info.get('column', ''), None)
        col_combo.setObjectName(f"col_{row}_{idx}")
        col_layout.addWidget(col_combo, 2)

        sep_label = QLabel("Разделитель:")
        sep_label.setStyleSheet("color: #666; font-size: 10px;")
        col_layout.addWidget(sep_label)

        sep_input = QLineEdit()
        sep_input.setText(col_info.get('separator', ', '))
        sep_input.setFixedWidth(70)
        sep_input.setObjectName(f"sep_{row}_{idx}")
        col_layout.addWidget(sep_input)

        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(26, 26)
        remove_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; border-radius: 13px; }")
        remove_btn.clicked.connect(lambda checked=False, r=row, i=idx, w=col_widget: self._remove_composite_column(r, i, w))
        col_layout.addWidget(remove_btn)

        return col_widget

    def _remove_composite_column(self, row, idx, widget_to_remove):
        composite_widget = self.parent.mapping_table.cellWidget(row, 1)
        if not composite_widget: return
        layout = composite_widget.layout()
        if not layout: return

        if layout.count() <= 2: 
            QMessageBox.warning(self.parent, "Внимание", "Нельзя удалить последний столбец.")
            return

        layout.removeWidget(widget_to_remove)
        widget_to_remove.deleteLater()
        self._update_column_numbers(layout)
        self.parent.mapping_table.resizeRowToContents(row)

    def _update_column_numbers(self, layout):
        num_idx = 1
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item: continue
            w = item.widget()
            if not w: continue
            if w.objectName().startswith('col_widget_'):
                num_label = w.layout().itemAt(0).widget() if w.layout() else None
                if isinstance(num_label, QLabel):
                    num_label.setText(f"{num_idx}.")
                    num_idx += 1

    def _add_add_column_button(self, layout, row, table_name=None):
        add_btn_container = QWidget()
        add_btn_container.setObjectName(f"add_btn_container_{row}")
        add_btn_layout = QHBoxLayout(add_btn_container)
        add_btn_layout.setContentsMargins(0, 8, 0, 0)
        add_btn_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        add_col_btn = QPushButton("+ Добавить столбец")
        add_col_btn.setFixedSize(140, 28)
        add_col_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; border-radius: 6px; }")
        add_col_btn.clicked.connect(lambda checked=False, r=row: self.add_composite_column(r, table_name))
        add_btn_layout.addWidget(add_col_btn)
        layout.addWidget(add_btn_container)

    def add_composite_column(self, row, table_name=None):
        composite_widget = self.parent.mapping_table.cellWidget(row, 1)
        if not composite_widget: return
        layout = composite_widget.layout()
        if not layout: return
        
        add_btn_container = composite_widget.findChild(QWidget, f"add_btn_container_{row}")
        if not add_btn_container: return
        
        insert_idx = layout.indexOf(add_btn_container)
        tbl_name = table_name or getattr(self.parent, 'current_table_name', 'social_data')
        column_count = sum(1 for i in range(layout.count()) if layout.itemAt(i).widget() and layout.itemAt(i).widget().objectName().startswith('col_widget_'))
        
        col_info = {'column': '', 'separator': ', '}
        col_widget = self._create_composite_column_widget(row, column_count, col_info, tbl_name)
        col_widget.setObjectName(f"col_widget_{row}_{column_count}")
        layout.insertWidget(insert_idx, col_widget)
        
        self._update_column_numbers(layout)
        self.parent.mapping_table.resizeRowToContents(row)

    def add_composite_field_mapping(self, row):
        mapping_table = self.parent.mapping_table
        mapping_table.insertRow(row)
        var_combo = QComboBox()
        vars_list = getattr(self.parent, 'template_variables', [])
        var_combo.addItems(vars_list if vars_list else [])
        var_combo.setMinimumWidth(200)
        mapping_table.setCellWidget(row, 0, var_combo)

        composite_widget = QWidget()
        composite_layout = QVBoxLayout(composite_widget)
        composite_layout.setContentsMargins(5, 5, 5, 5)
        composite_layout.setSpacing(5)

        tbl_name = getattr(self.parent, 'current_table_name', 'social_data')
        col_info = {'column': '', 'separator': ', '}
        col_widget = self._create_composite_column_widget(row, 0, col_info, tbl_name)
        col_widget.setObjectName(f"col_widget_{row}_0")
        composite_layout.addWidget(col_widget)

        self._add_add_column_button(composite_layout, row, tbl_name)

        mapping_table.setCellWidget(row, 1, composite_widget)
        mapping_table.setCellWidget(row, 2, self._create_type_label("Составное"))
        mapping_table.resizeRowToContents(row)
        mapping_table.selectRow(row)

    def _create_type_label(self, text):
        type_label = QLabel(text)
        type_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 10px;" if text == "Составное" else "color: #666; font-size: 10px;")
        return type_label

    def get_composite_columns(self, composite_widget):
        """
        Извлекает список колонок и разделителей из виджета составного поля.
        """
        db_columns = []
        layout = composite_widget.layout()
        if not layout:
            return db_columns

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item: continue
            col_widget = item.widget()
            if not col_widget or not col_widget.layout(): continue

            col_combo = None
            sep_input = None
            for j in range(col_widget.layout().count()):
                w = col_widget.layout().itemAt(j).widget()
                if isinstance(w, QComboBox): col_combo = w
                elif isinstance(w, QLineEdit): sep_input = w

            if col_combo and sep_input:
                raw_data = col_combo.currentData()
                col_name = None
                if raw_data:
                    if "|" in str(raw_data):
                        _, col_name = str(raw_data).split("|", 1)
                        col_name = col_name.strip()
                    else:
                        col_name = str(raw_data).strip()
                elif col_combo.count() > 0:
                    col_name = col_combo.currentText().strip()

                separator = sep_input.text()
                if col_name:
                    db_columns.append({'column': col_name, 'separator': separator})
        return db_columns