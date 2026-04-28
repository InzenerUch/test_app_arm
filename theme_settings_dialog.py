from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QColorDialog, QGroupBox, QMessageBox, QSpinBox, QFrame
)
from PyQt6.QtGui import QColor

class ThemeSettingsDialog(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.tm = theme_manager
        self.setWindowTitle("🎨 Настройка темы оформления")
        self.resize(680, 800)
        self.setModal(True)
        
        # Текущие значения (по умолчанию)
        self.bg_color = "#ffffff"
        self.text_color = "#000000"
        self.field_bg_color = "#f8f9fa"
        self.selection_bg_color = "#2196F3"
        
        # Кнопки
        self.btn_save_color = "#4CAF50"
        self.btn_danger_color = "#f44336"
        self.btn_info_color = "#2196F3"
        self.btn_edit_color = "#FF9800"    # 🔹 НОВОЕ
        self.btn_normal_color = "#9E9E9E"  # 🔹 НОВОЕ
        
        self.font_size = 12
        
        self.init_ui()
        self._load_current_settings()

    def init_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(15)
        lay.setContentsMargins(20, 20, 20, 20)

        # ─── Группа 1: Основные цвета ───
        g1 = QGroupBox("🖼️ Основные цвета интерфейса")
        g1_layout = QGridLayout(g1)
        g1_layout.setHorizontalSpacing(15)
        g1_layout.setVerticalSpacing(12)
        self.bg_btn = self._make_color_btn("Фон окон:", self.bg_color)
        self.bg_btn.clicked.connect(lambda: self._pick_color("bg"))
        g1_layout.addWidget(QLabel("Фон окон:"), 0, 0); g1_layout.addWidget(self.bg_btn, 0, 1)
        self.txt_btn = self._make_color_btn("Цвет текста:", self.text_color)
        self.txt_btn.clicked.connect(lambda: self._pick_color("text"))
        g1_layout.addWidget(QLabel("Цвет текста:"), 1, 0); g1_layout.addWidget(self.txt_btn, 1, 1)
        lay.addWidget(g1)

        # ─── Группа 2: Поля ввода ───
        g2 = QGroupBox("📝 Поля ввода")
        g2_layout = QGridLayout(g2)
        g2_layout.setHorizontalSpacing(15)
        self.field_btn = self._make_color_btn("Фон полей:", self.field_bg_color)
        self.field_btn.clicked.connect(lambda: self._pick_color("field"))
        g2_layout.addWidget(QLabel("Фон полей ввода:"), 0, 0); g2_layout.addWidget(self.field_btn, 0, 1)
        lay.addWidget(g2)

        # ─── Группа 3: Цвет выделения ───
        g_sel = QGroupBox("✨ Выделение")
        g_sel_layout = QGridLayout(g_sel)
        self.sel_btn = self._make_color_btn("Фон выделения:", self.selection_bg_color)
        self.sel_btn.clicked.connect(lambda: self._pick_color("selection"))
        g_sel_layout.addWidget(QLabel("Фон выделения:"), 0, 0); g_sel_layout.addWidget(self.sel_btn, 0, 1)
        lay.addWidget(g_sel)

        # ─── Группа 4: Кнопки действий ───
        g3 = QGroupBox("🔘 Кнопки действий")
        g3_layout = QGridLayout(g3)
        g3_layout.setHorizontalSpacing(15)
        g3_layout.setVerticalSpacing(10)
        
        self.btn_save = self._make_color_btn("Сохранить (зел):", self.btn_save_color)
        self.btn_save.clicked.connect(lambda: self._pick_color("save"))
        g3_layout.addWidget(QLabel("Сохранение:"), 0, 0); g3_layout.addWidget(self.btn_save, 0, 1)
        
        self.btn_danger = self._make_color_btn("Удалить (крас):", self.btn_danger_color)
        self.btn_danger.clicked.connect(lambda: self._pick_color("danger"))
        g3_layout.addWidget(QLabel("Удаление/Отмена:"), 1, 0); g3_layout.addWidget(self.btn_danger, 1, 1)
        
        self.btn_info = self._make_color_btn("Инфо (син):", self.btn_info_color)
        self.btn_info.clicked.connect(lambda: self._pick_color("info"))
        g3_layout.addWidget(QLabel("Информация:"), 2, 0); g3_layout.addWidget(self.btn_info, 2, 1)
        
        # 🔹 НОВЫЕ ПОЛЯ
        self.btn_edit = self._make_color_btn("Редакт./Открыть (оранж):", self.btn_edit_color)
        self.btn_edit.clicked.connect(lambda: self._pick_color("edit"))
        g3_layout.addWidget(QLabel("Редактирование/Открытие:"), 3, 0); g3_layout.addWidget(self.btn_edit, 3, 1)
        
        self.btn_normal = self._make_color_btn("Обычные (сер):", self.btn_normal_color)
        self.btn_normal.clicked.connect(lambda: self._pick_color("normal"))
        g3_layout.addWidget(QLabel("Обычные кнопки:"), 4, 0); g3_layout.addWidget(self.btn_normal, 4, 1)
        
        lay.addWidget(g3)

        # ─── Группа 5: Размер шрифта ───
        g_font = QGroupBox("🔤 Размер текста")
        g_font_layout = QHBoxLayout(g_font)
        g_font_layout.addWidget(QLabel("Размер шрифта:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 24)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setSuffix(" px")
        self.font_spin.setSingleStep(1)
        g_font_layout.addWidget(self.font_spin)
        lay.addWidget(g_font)

        # ─── Разделитель и кнопки ───
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        lay.addWidget(line)
        
        btns = QHBoxLayout()
        apply_btn = QPushButton("💾 Применить и сохранить")
        apply_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 12px 24px; font-weight: bold; font-size: 13px; border-radius: 5px;")
        apply_btn.clicked.connect(self.on_apply)
        reset_btn = QPushButton("🔄 Сбросить")
        reset_btn.setStyleSheet("background-color: #757575; color: white; padding: 12px 24px; font-weight: bold; border-radius: 5px;")
        reset_btn.clicked.connect(self.on_reset)
        btns.addWidget(apply_btn); btns.addWidget(reset_btn)
        lay.addLayout(btns)

    def _make_color_btn(self, text, color):
        btn = QPushButton(text)
        btn.setMinimumHeight(44)
        btn.setMinimumWidth(200)
        self._style_btn(btn, color)
        return btn

    def _style_btn(self, btn, color):
        contrast = "white" if QColor(color).lightness() < 140 else "black"
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: {contrast}; border: 1px solid #aaa; border-radius: 5px; padding: 6px; }}
        """)

    def _pick_color(self, target):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_c = color.name()
            map_dict = {
                "bg": (self.bg_btn, "bg_color"),
                "text": (self.txt_btn, "text_color"),
                "field": (self.field_btn, "field_bg_color"),
                "selection": (self.sel_btn, "selection_bg_color"),
                "save": (self.btn_save, "btn_save_color"),
                "danger": (self.btn_danger, "btn_danger_color"),
                "info": (self.btn_info, "btn_info_color"),
                "edit": (self.btn_edit, "btn_edit_color"),      # 🔹 НОВОЕ
                "normal": (self.btn_normal, "btn_normal_color") # 🔹 НОВОЕ
            }
            if target in map_dict:
                btn, attr = map_dict[target]
                setattr(self, attr, hex_c)
                self._style_btn(btn, hex_c)

    def _load_current_settings(self):
        current = self.tm.get_current_settings()
        if current.get("theme_name") == "custom":
            self.bg_color = current.get("bg_color", self.bg_color)
            self.text_color = current.get("text_color", self.text_color)
            self.field_bg_color = current.get("field_bg_color", self.field_bg_color)
            self.selection_bg_color = current.get("selection_bg_color", self.selection_bg_color)
            self.btn_save_color = current.get("button_save_color", self.btn_save_color)
            self.btn_danger_color = current.get("button_danger_color", self.btn_danger_color)
            self.btn_info_color = current.get("button_info_color", self.btn_info_color)
            self.btn_edit_color = current.get("button_edit_color", self.btn_edit_color)      # 🔹 НОВОЕ
            self.btn_normal_color = current.get("button_normal_color", self.btn_normal_color)# 🔹 НОВОЕ
            self.font_size = current.get("font_size", self.font_size)
            
            self._style_btn(self.bg_btn, self.bg_color)
            self._style_btn(self.txt_btn, self.text_color)
            self._style_btn(self.field_btn, self.field_bg_color)
            self._style_btn(self.sel_btn, self.selection_bg_color)
            self._style_btn(self.btn_save, self.btn_save_color)
            self._style_btn(self.btn_danger, self.btn_danger_color)
            self._style_btn(self.btn_info, self.btn_info_color)
            self._style_btn(self.btn_edit, self.btn_edit_color)      # 🔹 НОВОЕ
            self._style_btn(self.btn_normal, self.btn_normal_color)  # 🔹 НОВОЕ
            self.font_spin.setValue(self.font_size)

    def on_apply(self):
        self.tm.save_settings(
            bg_hex=self.bg_color, text_hex=self.text_color,
            field_bg_hex=self.field_bg_color,
            btn_save=self.btn_save_color, btn_danger=self.btn_danger_color, btn_info=self.btn_info_color,
            btn_edit=self.btn_edit_color, btn_normal=self.btn_normal_color, # 🔹 НОВОЕ
            font_size=self.font_spin.value()
        )
        QMessageBox.information(self, "Успех", "Тема применена и сохранена в БД!")
        self.accept()

    def on_reset(self):
        self.bg_color = "#ffffff"
        self.text_color = "#000000"
        self.field_bg_color = "#f8f9fa"
        self.selection_bg_color = "#2196F3"
        self.btn_save_color = "#4CAF50"
        self.btn_danger_color = "#f44336"
        self.btn_info_color = "#2196F3"
        self.btn_edit_color = "#FF9800"      # 🔹 НОВОЕ
        self.btn_normal_color = "#9E9E9E"    # 🔹 НОВОЕ
        self.font_size = 12
        
        self._style_btn(self.bg_btn, self.bg_color)
        self._style_btn(self.txt_btn, self.text_color)
        self._style_btn(self.field_btn, self.field_bg_color)
        self._style_btn(self.sel_btn, self.selection_bg_color)
        self._style_btn(self.btn_save, self.btn_save_color)
        self._style_btn(self.btn_danger, self.btn_danger_color)
        self._style_btn(self.btn_info, self.btn_info_color)
        self._style_btn(self.btn_edit, self.btn_edit_color)      # 🔹 НОВОЕ
        self._style_btn(self.btn_normal, self.btn_normal_color)  # 🔹 НОВОЕ
        self.font_spin.setValue(self.font_size)
        
        self.tm.apply_colors(
            self.bg_color, self.text_color, self.field_bg_color,
            self.btn_save_color, self.btn_danger_color, self.btn_info_color,
            self.btn_edit_color, self.btn_normal_color, self.font_size
        )
        self.accept()