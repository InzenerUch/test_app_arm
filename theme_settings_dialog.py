from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QColorDialog, QGroupBox, QMessageBox, QSpinBox, QFrame, QScrollArea,QWidget
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

class ThemeSettingsDialog(QDialog):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.tm = theme_manager
        self.setWindowTitle("🎨 Настройка темы оформления")
        self.resize(550, 600)  # ✅ Уменьшен базовый размер окна
        self.setMinimumSize(480, 450)
        self.setModal(True)
        
        # Цвета фона/текста
        self.bg_color = "#ffffff"
        self.text_color = "#000000"
        self.field_bg_color = "#f8f9fa"
        self.selection_bg_color = "#2196F3"
        
        # Цвета кнопок (фон)
        self.btn_save_color = "#4CAF50"
        self.btn_danger_color = "#f44336"
        self.btn_info_color = "#2196F3"
        self.btn_edit_color = "#FF9800"
        self.btn_normal_color = "#9E9E9E"
        
        # 🆕 Цвета текста кнопок
        self.btn_save_text = "#FFFFFF"
        self.btn_danger_text = "#FFFFFF"
        self.btn_info_text = "#FFFFFF"
        self.btn_edit_text = "#FFFFFF"
        self.btn_normal_text = "#FFFFFF"
        
        # 🆕 Цвет выделенного текста
        self.selection_text = "#FFFFFF"
        
        self.font_size = 12
        self.init_ui()
        self._load_current_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ─── 1. ОБЛАСТЬ ПРОКРУТКИ (все настройки) ───
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        content_widget = QWidget()
        lay = QVBoxLayout(content_widget)
        lay.setSpacing(15)
        lay.setContentsMargins(15, 15, 15, 15)

        # ─── 1.1. Основные цвета ───
        g1 = QGroupBox("🖼️ Основные цвета интерфейса")
        g1_layout = QGridLayout(g1)
        g1_layout.setHorizontalSpacing(15)
        self.bg_btn = self._make_color_btn("Фон окон:", self.bg_color)
        self.bg_btn.clicked.connect(lambda: self._pick_color("bg"))
        g1_layout.addWidget(QLabel("Фон окон:"), 0, 0); g1_layout.addWidget(self.bg_btn, 0, 1)
        self.txt_btn = self._make_color_btn("Цвет текста:", self.text_color)
        self.txt_btn.clicked.connect(lambda: self._pick_color("text"))
        g1_layout.addWidget(QLabel("Цвет текста:"), 1, 0); g1_layout.addWidget(self.txt_btn, 1, 1)
        lay.addWidget(g1)

        # ─── 1.2. Поля и выделение ───
        g2 = QGroupBox("📝 Поля ввода и выделение")
        g2_layout = QGridLayout(g2)
        g2_layout.setHorizontalSpacing(15)
        self.field_btn = self._make_color_btn("Фон полей:", self.field_bg_color)
        self.field_btn.clicked.connect(lambda: self._pick_color("field"))
        g2_layout.addWidget(QLabel("Фон полей:"), 0, 0); g2_layout.addWidget(self.field_btn, 0, 1)
        self.sel_btn = self._make_color_btn("Фон выделения:", self.selection_bg_color)
        self.sel_btn.clicked.connect(lambda: self._pick_color("selection"))
        g2_layout.addWidget(QLabel("Фон выделения:"), 1, 0); g2_layout.addWidget(self.sel_btn, 1, 1)
        lay.addWidget(g2)

        # ─── 1.3. Цвета кнопок (фон) ───
        g_btn_bg = QGroupBox("🎨 Цвета кнопок (фон)")
        g_btn_bg_layout = QGridLayout(g_btn_bg)
        g_btn_bg_layout.setHorizontalSpacing(15)
        g_btn_bg_layout.setVerticalSpacing(8)

        self.btn_save = self._make_color_btn("Сохранить (фон):", self.btn_save_color)
        self.btn_save.clicked.connect(lambda: self._pick_color("save"))
        g_btn_bg_layout.addWidget(QLabel("Сохранить (фон):"), 0, 0)
        g_btn_bg_layout.addWidget(self.btn_save, 0, 1)

        self.btn_danger = self._make_color_btn("Удалить (фон):", self.btn_danger_color)
        self.btn_danger.clicked.connect(lambda: self._pick_color("danger"))
        g_btn_bg_layout.addWidget(QLabel("Удалить (фон):"), 1, 0)
        g_btn_bg_layout.addWidget(self.btn_danger, 1, 1)

        self.btn_info = self._make_color_btn("Инфо (фон):", self.btn_info_color)
        self.btn_info.clicked.connect(lambda: self._pick_color("info"))
        g_btn_bg_layout.addWidget(QLabel("Инфо (фон):"), 2, 0)
        g_btn_bg_layout.addWidget(self.btn_info, 2, 1)

        self.btn_edit = self._make_color_btn("Редакт. (фон):", self.btn_edit_color)
        self.btn_edit.clicked.connect(lambda: self._pick_color("edit"))
        g_btn_bg_layout.addWidget(QLabel("Редакт. (фон):"), 3, 0)
        g_btn_bg_layout.addWidget(self.btn_edit, 3, 1)

        self.btn_normal = self._make_color_btn("Обычные (фон):", self.btn_normal_color)
        self.btn_normal.clicked.connect(lambda: self._pick_color("normal"))
        g_btn_bg_layout.addWidget(QLabel("Обычные (фон):"), 4, 0)
        g_btn_bg_layout.addWidget(self.btn_normal, 4, 1)
        lay.addWidget(g_btn_bg)

        # ─── 1.4. Цвета текста кнопок ───
        g3 = QGroupBox("🔤 Цвета текста на кнопках")
        g3_layout = QGridLayout(g3)
        g3_layout.setHorizontalSpacing(15)
        g3_layout.setVerticalSpacing(8)
        self.btn_save_txt = self._make_color_btn("Сохранить:", self.btn_save_text)
        self.btn_save_txt.clicked.connect(lambda: self._pick_color("save_text"))
        g3_layout.addWidget(QLabel("Сохранить (зел):"), 0, 0); g3_layout.addWidget(self.btn_save_txt, 0, 1)
        self.btn_danger_txt = self._make_color_btn("Удалить:", self.btn_danger_text)
        self.btn_danger_txt.clicked.connect(lambda: self._pick_color("danger_text"))
        g3_layout.addWidget(QLabel("Удалить (крас):"), 1, 0); g3_layout.addWidget(self.btn_danger_txt, 1, 1)
        self.btn_info_txt = self._make_color_btn("Инфо:", self.btn_info_text)
        self.btn_info_txt.clicked.connect(lambda: self._pick_color("info_text"))
        g3_layout.addWidget(QLabel("Инфо (син):"), 2, 0); g3_layout.addWidget(self.btn_info_txt, 2, 1)
        self.btn_edit_txt = self._make_color_btn("Редакт.:", self.btn_edit_text)
        self.btn_edit_txt.clicked.connect(lambda: self._pick_color("edit_text"))
        g3_layout.addWidget(QLabel("Редакт. (оранж):"), 3, 0); g3_layout.addWidget(self.btn_edit_txt, 3, 1)
        self.btn_normal_txt = self._make_color_btn("Обычные:", self.btn_normal_text)
        self.btn_normal_txt.clicked.connect(lambda: self._pick_color("normal_text"))
        g3_layout.addWidget(QLabel("Обычные (сер):"), 4, 0); g3_layout.addWidget(self.btn_normal_txt, 4, 1)
        lay.addWidget(g3)

        # ─── 1.5. Цвет выделенного текста ───
        g4 = QGroupBox("✨ Выделение текста")
        g4_layout = QHBoxLayout(g4)
        self.sel_text_btn = self._make_color_btn("Цвет текста при выделении:", self.selection_text)
        self.sel_text_btn.clicked.connect(lambda: self._pick_color("sel_text"))
        g4_layout.addWidget(QLabel("Текст в выделении:"), 0); g4_layout.addWidget(self.sel_text_btn, 1)
        lay.addWidget(g4)

        # ─── 1.6. Шрифт ───
        g_font = QGroupBox("🔤 Размер текста")
        g_font_layout = QHBoxLayout(g_font)
        g_font_layout.addWidget(QLabel("Размер шрифта:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 24)
        self.font_spin.setValue(self.font_size)
        self.font_spin.setSuffix(" px")
        g_font_layout.addWidget(self.font_spin)
        lay.addWidget(g_font)

        # Устанавливаем виджет в прокрутку
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # ─── 2. КНОПКИ (всегда видны внизу, БЕЗ прокрутки) ───
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        btns = QHBoxLayout()
        apply_btn = QPushButton("💾 Применить и сохранить")
        apply_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 12px 24px; font-weight: bold; font-size: 13px; border-radius: 5px;")
        apply_btn.clicked.connect(self.on_apply)
        reset_btn = QPushButton("🔄 Сбросить")
        reset_btn.setStyleSheet("background-color: #757575; color: white; padding: 12px 24px; font-weight: bold; border-radius: 5px;")
        reset_btn.clicked.connect(self.on_reset)
        btns.addWidget(apply_btn); btns.addWidget(reset_btn)
        main_layout.addLayout(btns)

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
                "edit": (self.btn_edit, "btn_edit_color"),
                "normal": (self.btn_normal, "btn_normal_color"),
                "save_text": (self.btn_save_txt, "btn_save_text"),
                "danger_text": (self.btn_danger_txt, "btn_danger_text"),
                "info_text": (self.btn_info_txt, "btn_info_text"),
                "edit_text": (self.btn_edit_txt, "btn_edit_text"),
                "normal_text": (self.btn_normal_txt, "btn_normal_text"),
                "sel_text": (self.sel_text_btn, "selection_text")
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
            self.btn_edit_color = current.get("button_edit_color", self.btn_edit_color)
            self.btn_normal_color = current.get("button_normal_color", self.btn_normal_color)
            
            self.btn_save_text = current.get("button_save_text", self.btn_save_text)
            self.btn_danger_text = current.get("button_danger_text", self.btn_danger_text)
            self.btn_info_text = current.get("button_info_text", self.btn_info_text)
            self.btn_edit_text = current.get("button_edit_text", self.btn_edit_text)
            self.btn_normal_text = current.get("button_normal_text", self.btn_normal_text)
            self.selection_text = current.get("selection_text", self.selection_text)
            
            self.font_size = current.get("font_size", self.font_size)
            
            # Обновление UI
            for btn, color in [(self.bg_btn, self.bg_color), (self.txt_btn, self.text_color),
                               (self.field_btn, self.field_bg_color), (self.sel_btn, self.selection_bg_color),
                               (self.btn_save, self.btn_save_color), (self.btn_danger, self.btn_danger_color),
                               (self.btn_info, self.btn_info_color), (self.btn_edit, self.btn_edit_color),
                               (self.btn_normal, self.btn_normal_color), (self.btn_save_txt, self.btn_save_text),
                               (self.btn_danger_txt, self.btn_danger_text), (self.btn_info_txt, self.btn_info_text),
                               (self.btn_edit_txt, self.btn_edit_text), (self.btn_normal_txt, self.btn_normal_text),
                               (self.sel_text_btn, self.selection_text)]:
                self._style_btn(btn, color)
            self.font_spin.setValue(self.font_size)

    def on_apply(self):
        self.tm.save_settings(
            bg_hex=self.bg_color, text_hex=self.text_color, field_bg_hex=self.field_bg_color,
            btn_save=self.btn_save_color, btn_danger=self.btn_danger_color, btn_info=self.btn_info_color,
            btn_edit=self.btn_edit_color, btn_normal=self.btn_normal_color,
            btn_save_text=self.btn_save_text, btn_danger_text=self.btn_danger_text,
            btn_info_text=self.btn_info_text, btn_edit_text=self.btn_edit_text, btn_normal_text=self.btn_normal_text,
            selection_text=self.selection_text, font_size=self.font_spin.value()
        )
        QMessageBox.information(self, "Успех", "Тема применена и сохранена в БД!")
        self.accept()

    def on_reset(self):
        self.bg_color = "#ffffff"; self.text_color = "#000000"; self.field_bg_color = "#f8f9fa"
        self.selection_bg_color = "#2196F3"
        self.btn_save_color = "#4CAF50"; self.btn_danger_color = "#f44336"; self.btn_info_color = "#2196F3"
        self.btn_edit_color = "#FF9800"; self.btn_normal_color = "#9E9E9E"
        self.btn_save_text = "#FFFFFF"; self.btn_danger_text = "#FFFFFF"; self.btn_info_text = "#FFFFFF"
        self.btn_edit_text = "#FFFFFF"; self.btn_normal_text = "#FFFFFF"; self.selection_text = "#FFFFFF"
        self.font_size = 12
        
        for btn, color in [(self.bg_btn, self.bg_color), (self.txt_btn, self.text_color),
                           (self.field_btn, self.field_bg_color), (self.sel_btn, self.selection_bg_color),
                           (self.btn_save, self.btn_save_color), (self.btn_danger, self.btn_danger_color),
                           (self.btn_info, self.btn_info_color), (self.btn_edit, self.btn_edit_color),
                           (self.btn_normal, self.btn_normal_color), (self.btn_save_txt, self.btn_save_text),
                           (self.btn_danger_txt, self.btn_danger_text), (self.btn_info_txt, self.btn_info_text),
                           (self.btn_edit_txt, self.btn_edit_text), (self.btn_normal_txt, self.btn_normal_text),
                           (self.sel_text_btn, self.selection_text)]:
            self._style_btn(btn, color)
        self.font_spin.setValue(self.font_size)
        
        self.tm.apply_colors(self.bg_color, self.text_color, self.field_bg_color,
                             self.btn_save_color, self.btn_danger_color, self.btn_info_color,
                             self.btn_edit_color, self.btn_normal_color,
                             self.btn_save_text, self.btn_danger_text, self.btn_info_text,
                             self.btn_edit_text, self.btn_normal_text, self.selection_text, self.font_size)
        self.accept()