"""
Виджет для управления составными полями
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, 
    QPushButton, QLabel, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import json
import traceback


class CompositeFieldWidget:
    """Управление интерфейсом составных полей"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def create_composite_field_row(self, row, field_name, db_columns_json, table_name, mapping_table):
        """Создание строки для составного сопоставления"""
        print(f"📝 CompositeFieldWidget.create_composite_field_row(row={row}, field={field_name})")
        
        try:
            # ✅ ВАЖНО: Сначала вставляем строку в таблицу!
            mapping_table.insertRow(row)
            print(f"   ✅ Строка {row} вставлена в таблицу")
            
            # 1. Переменная из шаблона
            var_combo = QComboBox()
            var_combo.addItems(self.parent.template_variables)
            var_combo.setCurrentText(field_name)
            
            # 2. Контейнер для составных столбцов
            composite_widget = QWidget()
            composite_layout = QVBoxLayout(composite_widget)
            composite_layout.setContentsMargins(5, 5, 5, 5)
            composite_layout.setSpacing(5)
            
            db_columns = json.loads(db_columns_json) if isinstance(db_columns_json, str) else db_columns_json
            if not db_columns:
                db_columns = [{'column': '', 'separator': ', '}]
            
            print(f"   Столбцов в JSON: {len(db_columns)}")
            
            for idx, col_info in enumerate(db_columns):
                col_widget = self._create_composite_column_widget(row, idx, col_info, table_name)
                composite_layout.addWidget(col_widget)
            
            # 3. Кнопка добавления столбца
            self._add_add_column_button(composite_layout, row)
            
            # 4. Установка виджетов в таблицу
            mapping_table.setCellWidget(row, 0, var_combo)
            mapping_table.setCellWidget(row, 1, composite_widget)
            mapping_table.setCellWidget(row, 2, self._create_type_label("Составное"))
            mapping_table.resizeRowToContents(row)
            
            # ✅ ПРОВЕРКА: что было создано
            var_w = mapping_table.cellWidget(row, 0)
            col_w = mapping_table.cellWidget(row, 1)
            type_w = mapping_table.cellWidget(row, 2)
            
            if var_w and col_w and type_w:
                print(f"✅ Строка создана успешно")
                print(f"   var_combo: {var_w.currentText()}")
                print(f"   composite_widget: {col_w}")
                print(f"   type_label: {type_w.text()}")
            else:
                print(f"❌ ОШИБКА: виджеты не созданы!")
                print(f"   var_w={var_w}, col_w={col_w}, type_w={type_w}")
            
        except Exception as e:
            print(f"❌ Ошибка создания строки: {e}")
            traceback.print_exc()
    
    def _create_composite_column_widget(self, row, idx, col_info, table_name):
        """Создание виджета одного столбца в составном поле"""
        col_widget = QWidget()
        col_layout = QHBoxLayout(col_widget)
        col_layout.setContentsMargins(8, 5, 8, 5)
        col_layout.setSpacing(8)
        
        # Номер столбца
        num_label = QLabel(f"{idx + 1}.")
        num_label.setStyleSheet("font-weight: bold; color: #2196F3; min-width: 20px;")
        num_label.setObjectName(f"num_{row}_{idx}")
        col_layout.addWidget(num_label)
        
        # Выбор столбца БД
        col_combo = QComboBox()
        col_combo.setMinimumWidth(150)
        if table_name in self.parent.db_columns:
            col_combo.addItems(self.parent.db_columns[table_name])
        col_combo.setCurrentText(col_info.get('column', ''))
        col_combo.setObjectName(f"col_{row}_{idx}")
        col_layout.addWidget(col_combo, 2)
        
        # Разделитель
        sep_label = QLabel("Разделитель:")
        sep_label.setStyleSheet("color: #666; font-size: 10px;")
        col_layout.addWidget(sep_label)
        
        sep_input = QLineEdit()
        sep_input.setText(col_info.get('separator', ', '))
        sep_input.setFixedWidth(70)
        sep_input.setObjectName(f"sep_{row}_{idx}")
        sep_input.setStyleSheet("QLineEdit { border: 1px solid #ddd; border-radius: 3px; padding: 2px; }")
        col_layout.addWidget(sep_input)
        
        # Кнопка удаления
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(26, 26)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border-radius: 13px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        
        remove_btn.clicked.connect(
            lambda checked=False, r=row, i=idx, w=col_widget: self._remove_composite_column(r, i, w)
        )
        col_layout.addWidget(remove_btn)
        
        return col_widget
    
    def _remove_composite_column(self, row, idx, widget_to_remove):
        """Удаление столбца из составного поля"""
        print(f"🗑️ Удаление столбца #{idx + 1} из строки {row}")
        
        composite_widget = self.parent.mapping_table.cellWidget(row, 1)
        if not composite_widget:
            print("❌ Ошибка: composite_widget не найден")
            return
        
        layout = composite_widget.layout()
        if not layout:
            print("❌ Ошибка: layout не найден")
            return
        
        if layout.count() <= 2:
            QMessageBox.warning(self.parent, "Внимание", "Нельзя удалить последний столбец.")
            return
        
        layout.removeWidget(widget_to_remove)
        widget_to_remove.deleteLater()
        self._update_column_numbers(layout)
        self.parent.mapping_table.resizeRowToContents(row)
        print(f"✅ Столбец #{idx + 1} удален")
    
    def _update_column_numbers(self, layout):
        """Обновление номеров всех столбцов"""
        for i in range(layout.count() - 1):
            widget = layout.itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                col_layout = widget.layout()
                if col_layout and col_layout.count() > 0:
                    num_label = col_layout.itemAt(0).widget()
                    if isinstance(num_label, QLabel):
                        num_label.setText(f"{i + 1}.")
    
    def _add_add_column_button(self, layout, row):
        """Добавление кнопки добавления столбца"""
        add_btn_container = QWidget()
        add_btn_layout = QHBoxLayout(add_btn_container)
        add_btn_layout.setContentsMargins(0, 8, 0, 0)
        
        # ✅ ИСПРАВЛЕНО: PyQt6 синтаксис для QSizePolicy
        add_btn_layout.addSpacerItem(QSpacerItem(40, 20, 
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Minimum
        ))
        
        add_col_btn = QPushButton("+ Добавить столбец")
        add_col_btn.setFixedSize(140, 28)
        add_col_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """)
        add_col_btn.clicked.connect(lambda checked=False, r=row: self.add_composite_column(r))
        add_btn_layout.addWidget(add_col_btn)
        
        layout.addWidget(add_btn_container)
        layout.addStretch()
    
    def add_composite_column(self, row):
        """Добавление нового столбца в составное сопоставление"""
        print(f"➕ Добавление столбца в строку {row}")
        
        composite_widget = self.parent.mapping_table.cellWidget(row, 1)
        if not composite_widget:
            print("❌ Ошибка: composite_widget не найден")
            return
        
        layout = composite_widget.layout()
        if not layout:
            print("❌ Ошибка: layout не найден")
            return
        
        idx = layout.count() - 2 if layout.count() >= 2 else 0
        col_info = {'column': '', 'separator': ', '}
        col_widget = self._create_composite_column_widget(row, idx, col_info, self.parent.current_table_name)
        
        button_container = layout.itemAt(layout.count() - 2).widget() if layout.count() >= 2 else None
        if button_container:
            layout.insertWidget(layout.count() - 2, col_widget)
        else:
            layout.addWidget(col_widget)
        
        self._update_column_numbers(layout)
        self.parent.mapping_table.resizeRowToContents(row)
        print(f"✅ Столбец добавлен")
    
    def add_composite_field_mapping(self, row):
        """Добавление составного сопоставления"""
        print(f"📝 CompositeFieldWidget.add_composite_field_mapping(row={row})")
        
        mapping_table = self.parent.mapping_table
        
        # ✅ ВАЖНО: Сначала вставляем строку в таблицу!
        mapping_table.insertRow(row)
        print(f"   ✅ Строка {row} вставлена в таблицу")
        
        # Переменная из шаблона
        var_combo = QComboBox()
        var_combo.addItems(self.parent.template_variables)
        mapping_table.setCellWidget(row, 0, var_combo)
        
        # Контейнер для составных столбцов
        composite_widget = QWidget()
        composite_layout = QVBoxLayout(composite_widget)
        composite_layout.setContentsMargins(5, 5, 5, 5)
        composite_layout.setSpacing(5)
        
        # Добавляем первый столбец
        col_info = {'column': '', 'separator': ', '}
        col_widget = self._create_composite_column_widget(row, 0, col_info, self.parent.current_table_name)
        composite_layout.addWidget(col_widget)
        
        # Кнопка добавления столбца
        self._add_add_column_button(composite_layout, row)
        
        mapping_table.setCellWidget(row, 1, composite_widget)
        mapping_table.setCellWidget(row, 2, self._create_type_label("Составное"))
        mapping_table.resizeRowToContents(row)
        mapping_table.selectRow(row)
        
        print(f"✅ Составное поле добавлено")
    
    def _create_type_label(self, text):
        """Создание метки типа сопоставления"""
        type_label = QLabel(text)
        type_label.setStyleSheet(
            "color: #4CAF50; font-weight: bold; font-size: 10px;" if text == "Составное" 
            else "color: #666; font-size: 10px;"
        )
        return type_label
    
    def get_composite_columns(self, composite_widget):
        """Получение списка составных столбцов из виджета"""
        print(f"🔍 get_composite_columns()")
        
        db_columns = []
        layout = composite_widget.layout()
        
        if not layout:
            print("   ⚠️ layout не найден")
            return db_columns
        
        print(f"   Элементов в layout: {layout.count()}")
        
        for i in range(layout.count() - 1):
            col_widget = layout.itemAt(i).widget()
            if not col_widget:
                print(f"   [{i}] ⚠️ col_widget не найден")
                continue
            
            col_layout = col_widget.layout()
            if not col_layout:
                print(f"   [{i}] ⚠️ col_layout не найден")
                continue
            
            print(f"   [{i}] Элементов в col_layout: {col_layout.count()}")
            
            col_combo = None
            sep_input = None
            
            for j in range(col_layout.count()):
                item = col_layout.itemAt(j)
                if item:
                    widget = item.widget()
                    if isinstance(widget, QComboBox):
                        col_combo = widget
                        print(f"       [{j}] QComboBox: {widget.currentText() if widget else 'None'}")
                    elif isinstance(widget, QLineEdit):
                        sep_input = widget
                        print(f"       [{j}] QLineEdit: {widget.text() if widget else 'None'}")
            
            if col_combo and sep_input:
                column_name = col_combo.currentText().strip()
                separator = sep_input.text()
                print(f"   [{i}] ✅ {column_name} (sep: '{separator}')")
                if column_name:
                    db_columns.append({'column': column_name, 'separator': separator})
            else:
                print(f"   [{i}] ⚠️ col_combo={col_combo}, sep_input={sep_input}")
        
        print(f"   ✅ Возвращено {len(db_columns)} столбцов")
        return db_columns