"""
Диалог для добавления/редактирования записи справочника
Вынесен в отдельный модуль для переиспользования
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtGui import QFont


class RecordEditDialog(QDialog):
    """Диалог для добавления/редактирования записи справочника"""
    
    def __init__(self, parent, table_name: str, config: dict, record_data: dict = None):
        super().__init__(parent)
        self.table_name = table_name
        self.config = config
        self.record_data = record_data or {}
        
        is_edit = record_data is not None
        self.setWindowTitle(f"{'✏️ Редактирование' if is_edit else '➕ Добавление'} записи")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self.inputs = {}
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Заголовок
        title_label = QLabel(f"{self.config['icon']} {self.config['title']}")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Поля ввода
        for col in self.config["editable_columns"]:
            field_layout = QHBoxLayout()
            
            label = QLabel(f"{col.replace('_', ' ').title()}:")
            label.setMinimumWidth(150)
            field_layout.addWidget(label)
            
            input_widget = QLineEdit()
            input_widget.setPlaceholderText(f"Введите {col}")
            
            # Заполняем существующими данными
            if col in self.record_data:
                input_widget.setText(str(self.record_data[col]) if self.record_data[col] else "")
            
            field_layout.addWidget(input_widget)
            self.inputs[col] = input_widget
            
            layout.addLayout(field_layout)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_data(self) -> dict:
        """Получение данных из формы"""
        data = {}
        for col, input_widget in self.inputs.items():
            value = input_widget.text().strip()
            
            # Проверка обязательных полей
            if col in self.config["required_columns"] and not value:
                raise ValueError(f"Поле '{col}' обязательно для заполнения")
            
            data[col] = value if value else None
        
        return data