from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
    QLabel, QColorDialog, QGroupBox, QMessageBox, QSpinBox
)
from PyQt6.QtGui import QColor

class ThemeSettingsDialog(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.tm = theme_manager
        self.setWindowTitle("🎨 Настройка темы оформления")
        self.resize(540, 520)
        self.setModal(True)
        
        # Значения по умолчанию
        self.bg_color = "#ffffff"
        self.text_color = "#000000"
        self.field_bg_color = "#f8f9fa"
        self.btn_primary = "#4CAF50"
        self.btn_danger = "#f44336"
        self.btn_info = "#2196F3"
        self.font_size = 12
        
        self.init_ui()
        self._load_current_settings()

    def _load_current_settings(self):
        """Предзагрузка текущих настроек из ThemeManager"""
        current = self.tm.get_current_settings()
        if current.get("theme_name") == "custom":
            self.bg_color = current.get("bg_color", self.bg_color)
            self.text_color = current.get("text_color", self.text_color)
            self.field_bg_color = current.get("field_bg_color", self.field_bg_color)
            self.btn_primary = current.get("button_primary_color", self.btn_primary)
            self.btn_danger = current.get("button_danger_color", self.btn_danger)
            self.btn_info = current.get("button_info_color", self.btn_info)
            self.font_size = current.get("font_size", self.font_size)
            
            # Обновляем UI под загруженные значения
            self._style_btn(self.bg_btn, self.bg_color)
            self._style_btn(self.txt_btn, self.text_color)
            self._style_btn(self.field_btn, self.field_bg_color)
            self._style_btn(self.btn_prim, self.btn_primary)
            self._style_btn(self.btn_dang, self.btn_danger)
            self._style_btn(self.btn_inf, self.btn_info)
            self.font_spin.setValue(self.font_size)

    def init_ui(self):
        lay = QVBoxLayout(self)
        
        # Группа 1: Основные цвета
        g1 = QGroupBox("🖼️ Основные цвета")
        g1_lay = QGridLayout(g1)
        self.bg_btn = self._make_color_btn("Фон окна:", self.bg_color)
        self.bg_btn.clicked.connect(lambda: self._pick_color("bg"))
        g1_lay.addWidget(QLabel("Фон окна:"), 0, 0); g1_lay.addWidget(self.bg_btn, 0, 1)
        self.txt_btn = self._make_color_btn("Цвет текста:", self.text_color)
        self.txt_btn.clicked.connect(lambda: self._pick_color("text"))
        g1_lay.addWidget(QLabel("Цвет текста:"), 1, 0); g1_lay.addWidget(self.txt_btn, 1, 1)
        lay.addWidget(g1)
        
        # Группа 2: Поля ввода
        g2 = QGroupBox("📝 Поля ввода")
        g2_lay = QGridLayout(g2)
        self.field_btn = self._make_color_btn("Фон полей:", self.field_bg_color)
        self.field_btn.clicked.connect(lambda: self._pick_color("field"))
        g2_lay.addWidget(QLabel("Фон полей ввода:"), 0, 0); g2_lay.addWidget(self.field_btn, 0, 1)
        lay.addWidget(g2)
        
        # Группа 3: Кнопки
        g3 = QGroupBox("🔘 Кнопки действий")
        g3_lay = QGridLayout(g3)
        self.btn_prim = self._make_color_btn("Сохранить (зел):", self.btn_primary)
        self.btn_prim.clicked.connect(lambda: self._pick_color("btn_prim"))
        g3_lay.addWidget(QLabel("Основные (сохранить):"), 0, 0); g3_lay.addWidget(self.btn_prim, 0, 1)
        self.btn_dang = self._make_color_btn("Удалить (крас):", self.btn_danger)
        self.btn_dang.clicked.connect(lambda: self._pick_color("btn_dang"))
        g3_lay.addWidget(QLabel("Опасные (удалить):"), 1, 0); g3_lay.addWidget(self.btn_dang, 1, 1)
        self.btn_inf = self._make_color_btn("Инфо (син):", self.btn_info)
        self.btn_inf.clicked.connect(lambda: self._pick_color("btn_inf"))
        g3_lay.addWidget(QLabel("Информация (синие):"), 2, 0); g3_lay.addWidget(self.btn_inf, 2, 1)
        lay.addWidget(g3)

        # Группа 4: Размер текста (НОВОЕ)
        g_font = QGroupBox("🔤 Размер текста")
        g_font_lay = QHBoxLayout(g_font)
        g_font_lay.addWidget(QLabel("Размер шрифта:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 24)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setSuffix(" px")
        self.font_spin.setSingleStep(1)
        g_font_lay.addWidget(self.font_spin)
        lay.addWidget(g_font)
        
        # Кнопки
        btns = QHBoxLayout()
        apply_btn = QPushButton("💾 Применить и сохранить")
        apply_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        apply_btn.clicked.connect(self.on_apply)
        reset_btn = QPushButton("🔄 Сбросить")
        reset_btn.clicked.connect(self.on_reset)
        btns.addWidget(apply_btn); btns.addWidget(reset_btn)
        lay.addLayout(btns)

    def _make_color_btn(self, text, color):
        btn = QPushButton(text)
        btn.setMinimumHeight(42)
        self._style_btn(btn, color)
        return btn

    def _style_btn(self, btn, color):
        contrast = "white" if QColor(color).lightness() < 140 else "black"
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: {contrast}; border: 1px solid #ccc; border-radius: 5px; padding: 6px; }}
        """)

    def _pick_color(self, target):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_c = color.name()
            map_dict = {
                "bg": (self.bg_btn, "bg_color"),
                "text": (self.txt_btn, "text_color"),
                "field": (self.field_btn, "field_bg_color"),
                "btn_prim": (self.btn_prim, "btn_primary"),
                "btn_dang": (self.btn_dang, "btn_danger"),
                "btn_inf": (self.btn_inf, "btn_info"),
            }
            if target in map_dict:
                btn, attr = map_dict[target]
                setattr(self, attr, hex_c)
                self._style_btn(btn, hex_c)

    def on_apply(self):
        self.tm.save_settings(
            bg_hex=self.bg_color, text_hex=self.text_color,
            field_bg_hex=self.field_bg_color,
            btn_prim=self.btn_primary, btn_dang=self.btn_danger, btn_info=self.btn_info,
            font_size=self.font_spin.value()
        )
        QMessageBox.information(self, "Успех", "Тема применена и сохранена в БД!")
        self.accept()

    def on_reset(self):
        self.bg_color = "#ffffff"
        self.text_color = "#000000"
        self.field_bg_color = "#f8f9fa"
        self.btn_primary = "#4CAF50"
        self.btn_danger = "#f44336"
        self.btn_info = "#2196F3"
        self.font_size = 12
        
        self.tm.apply_colors(
            self.bg_color, self.text_color, self.field_bg_color,
            self.btn_primary, self.btn_danger, self.btn_info,
            font_size=self.font_size
        )
        self.accept()