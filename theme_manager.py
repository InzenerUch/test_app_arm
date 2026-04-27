from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QColor
from PyQt6.QtSql import QSqlQuery
import json

class ThemeManager:
    def __init__(self, db_connection, user_id):
        self.db = db_connection
        self.user_id = int(user_id) if user_id is not None else None
        print(f"🎨 [ThemeManager] Инициализирован для user_id={self.user_id}")

    def get_current_settings(self) -> dict:
        """Возвращает текущие сохранённые настройки для предзагрузки в диалог"""
        return self._load_settings()

    def load_and_apply(self):
        if self.user_id is None:
            self._apply_default()
            return

        print(f"📂 [Theme] Загрузка настроек для пользователя {self.user_id}...")
        settings = self._load_settings()
        print(f"📦 [Theme] Данные из БД: {settings}")

        if settings and settings.get("theme_name") == "custom":
            print("✨ [Theme] Применяем кастомную тему через QSS...")
            self.apply_colors(
                bg_hex=settings.get("bg_color", "#ffffff"),
                text_hex=settings.get("text_color", "#000000"),
                field_bg_hex=settings.get("field_bg_color"),
                btn_prim=settings.get("button_primary_color", "#4CAF50"),
                btn_dang=settings.get("button_danger_color", "#f44336"),
                btn_info=settings.get("button_info_color", "#2196F3"),
                font_size=settings.get("font_size", 12)
            )
        else:
            self._apply_default()

    def apply_colors(self, bg_hex: str, text_hex: str, 
                     field_bg_hex: str = None,
                     btn_prim: str = "#4CAF50",
                     btn_dang: str = "#f44336",
                     btn_info: str = "#2196F3",
                     font_size: int = 12):
        """Применение темы через глобальный QSS с поддержкой размера шрифта"""
        bg = QColor(bg_hex or "#ffffff")
        txt = QColor(text_hex or "#000000")
        field_bg = QColor(field_bg_hex or bg_hex or "#ffffff")
        alt_bg = bg.lighter(115).name()
        field_bg_darker = field_bg.darker(102).name()

        qss = f"""
        /* === ОСНОВНЫЕ ЭЛЕМЕНТЫ === */
        QWidget {{ 
            background-color: {bg_hex}; 
            color: {text_hex}; 
            font-size: {font_size}px; 
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }}
        
        QMainWindow, QDialog {{ background-color: {bg_hex}; }}
        
        /* === ТАБЛИЦЫ И СПИСКИ === */
        QTableView, QTableWidget, QTreeView, QTreeWidget, QListWidget, QListView {{
            background-color: {bg_hex};
            alternate-background-color: {alt_bg};
            color: {text_hex};
            gridline-color: {txt.darker(150).name()};
            border: 1px solid {txt.darker(200).name()};
            selection-background-color: {btn_info};
            selection-color: white;
            font-size: {font_size}px;
        }}
        
        QTableView::item:selected, QTableWidget::item:selected, 
        QListWidget::item:selected, QListView::item:selected {{
            background-color: {btn_info}; color: white;
        }}
        
        /* === ПОЛЯ ВВОДА === */
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, 
        QDoubleSpinBox, QDateEdit, QDateTimeEdit, QTimeEdit {{
            background-color: {field_bg_darker};
            color: {text_hex};
            border: 1px solid {txt.darker(180).name()};
            border-radius: 4px;
            padding: 6px 8px;
            font-size: {font_size}px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
            border: 2px solid {btn_info};
            background-color: {field_bg_hex or bg_hex};
        }}
        
        /* === КОМБОБОКСЫ === */
        QComboBox {{
            background-color: {field_bg_darker}; color: {text_hex};
            border: 1px solid {txt.darker(180).name()}; border-radius: 4px; padding: 5px 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {field_bg_hex or bg_hex}; color: {text_hex};
            selection-background-color: {btn_info}; selection-color: white;
        }}
        
        /* === КНОПКИ === */
        QPushButton {{
            background-color: {btn_prim}; color: white; border: none;
            border-radius: 5px; padding: 8px 16px; font-weight: bold;
            font-size: {font_size}px; min-width: 80px;
        }}
        QPushButton:hover {{ background-color: {QColor(btn_prim).darker(110).name()}; }}
        QPushButton:pressed {{ background-color: {QColor(btn_prim).darker(120).name()}; }}
        QPushButton:disabled {{ background-color: {txt.darker(150).name()}; color: {bg.lighter(150).name()}; }}
        
        QPushButton[danger="true"] {{ background-color: {btn_dang}; }}
        QPushButton[danger="true"]:hover {{ background-color: {QColor(btn_dang).darker(110).name()}; }}
        
        QPushButton[info="true"] {{ background-color: {btn_info}; }}
        QPushButton[info="true"]:hover {{ background-color: {QColor(btn_info).darker(110).name()}; }}
        
        QPushButton[secondary="true"] {{ background-color: {bg.darker(115).name()}; color: {text_hex}; border: 1px solid {txt.darker(180).name()}; }}
        
        /* === МЕНЮ, ПАНЕЛИ, ЗАГОЛОВКИ === */
        QMenuBar {{ background-color: {bg.darker(105).name()}; color: {text_hex}; padding: 4px; }}
        QMenuBar::item:selected {{ background-color: {btn_info}; color: white; }}
        QMenu {{ background-color: {bg_hex}; border: 1px solid {txt.darker(180).name()}; border-radius: 5px; padding: 5px; }}
        QMenu::item {{ padding: 8px 25px; border-radius: 3px; font-size: {font_size}px; }}
        QMenu::item:selected {{ background-color: {btn_info}; color: white; }}
        
        QToolBar {{ background-color: {bg.darker(105).name()}; border-bottom: 1px solid {txt.darker(180).name()}; }}
        QToolBar QLabel {{ color: {text_hex}; padding: 4px; font-size: {font_size}px; }}
        
        QHeaderView::section {{
            background-color: {bg.darker(115).name()}; color: {text_hex};
            padding: 8px; border: 1px solid {txt.darker(180).name()};
            font-weight: bold; font-size: {font_size}px;
        }}
        
        QGroupBox {{
            border: 1px solid {txt.darker(180).name()}; border-radius: 8px;
            margin-top: 12px; padding-top: 12px; font-weight: bold; font-size: {font_size}px;
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 8px; color: {text_hex}; }}
        
        QTabBar::tab {{
            background-color: {bg.darker(110).name()}; color: {text_hex};
            padding: 8px 16px; border: 1px solid {txt.darker(180).name()};
            border-top-left-radius: 5px; border-top-right-radius: 5px;
            margin-right: 2px; font-size: {font_size}px;
        }}
        QTabBar::tab:selected {{ background-color: {bg_hex}; border-bottom: 1px solid {bg_hex}; }}
        
        QStatusBar {{ background-color: {bg.darker(110).name()}; color: {text_hex}; font-size: {font_size}px; }}
        QToolTip {{ background-color: {bg.darker(115).name()}; color: {text_hex}; font-size: {font_size}px; }}
        """
        
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)
            app.setStyle(QStyleFactory.create("Fusion"))
            print(f"✅ [Theme] QSS тема применена (шрифт: {font_size}px)")
        else:
            print("❌ [Theme] QApplication.instance() вернул None.")

    def save_settings(self, bg_hex: str, text_hex: str, 
                      field_bg_hex: str = None,
                      btn_prim: str = "#4CAF50",
                      btn_dang: str = "#f44336",
                      btn_info: str = "#2196F3",
                      font_size: int = 12):
        config = {
            "theme_name": "custom",
            "bg_color": bg_hex, "text_color": text_hex,
            "field_bg_color": field_bg_hex or bg_hex,
            "button_primary_color": btn_prim,
            "button_danger_color": btn_dang,
            "button_info_color": btn_info,
            "font_size": font_size
        }
        query = QSqlQuery(self.db)
        query.prepare("""
            INSERT INTO krd.user_settings (user_id, theme_name, config_json, created_at, updated_at)
            VALUES (:uid, 'custom', :config, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET
                theme_name = 'custom', config_json = EXCLUDED.config_json, updated_at = CURRENT_TIMESTAMP
        """)
        query.bindValue(":uid", self.user_id)
        query.bindValue(":config", json.dumps(config, ensure_ascii=False))
        
        if query.exec():
            print("✅ [Theme] Настройки сохранены в БД")
            self.apply_colors(bg_hex, text_hex, field_bg_hex, btn_prim, btn_dang, btn_info, font_size)
        else:
            print(f"❌ [Theme] Ошибка БД: {query.lastError().text()}")

    def _load_settings(self) -> dict:
        query = QSqlQuery(self.db)
        query.prepare("SELECT config_json FROM krd.user_settings WHERE user_id = ?")
        query.addBindValue(self.user_id)
        if query.exec() and query.next():
            raw = query.value(0)
            return json.loads(raw) if raw else {}
        return {}

    def _apply_default(self):
        app = QApplication.instance()
        if app:
            app.setStyleSheet("")
            app.setStyle(QStyleFactory.create("Fusion"))