"""
Модуль для главного окна приложения
Содержит класс MainWindow для отображения данных КРД и информации о пользователе
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QGroupBox,
    QGridLayout, QMenuBar, QStatusBar, QToolBar,QTableView,QPushButton,QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel, QSqlQuery,QSqlTableModel
from PyQt6.QtGui import QAction, QFont
from add_krd_window import AddKrdWindow


class MainWindow(QMainWindow):
    """
    Главное окно приложения
    Отображает данные КРД и информацию о вошедшем пользователе
    """
    
    def __init__(self, user_info, db_connection):
        """
        Инициализация главного окна
        
        Args:
            user_info (dict): информация о пользователе, полученная из окна авторизации
            db_connection: соединение с базой данных
        """
        super().__init__()
        self.user_info = user_info
        self.db = db_connection
        
        # Установка основных параметров окна
        self.setWindowTitle("АРМ Сотрудника дознания - Главное окно")
        self.setGeometry(100, 100, 1200, 800)  # x, y, ширина, высота
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Загрузка данных
        self.load_krd_data()
    
    def init_ui(self):
        """
        Инициализация пользовательского интерфейса
        """
        # Создание меню
        self.create_menu_bar()
        
        # Создание тулбара
        self.create_toolbar()
        
        # Создание статусбара
        self.create_status_bar()
        
        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной макет
        main_layout = QVBoxLayout(central_widget)
        
        # Группа с информацией о пользователе
        user_info_group = self.create_user_info_section()
        main_layout.addWidget(user_info_group)
        
        # Разделитель
        separator = self.create_separator()
        main_layout.addWidget(separator)
        
        # Группа с данными КРД
        krd_data_group = self.create_krd_data_section()
        main_layout.addWidget(krd_data_group)
    
    def create_menu_bar(self):
        """
        Создание строки меню
        """
        menu_bar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menu_bar.addMenu("Файл")
        
        # Действие "Выход"
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Справка"
        help_menu = menu_bar.addMenu("Справка")
        
        # Действие "О программе"
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """
        Создание панели инструментов
        """
        toolbar = self.addToolBar("Основная панель")

        # Добавляем действия на тулбар
        refresh_action = QAction("Обновить", self)
        refresh_action.triggered.connect(self.load_krd_data)
        toolbar.addAction(refresh_action)

        # Добавляем действие "Добавить КРД"
        add_krd_action = QAction("Добавить КРД", self)
        add_krd_action.triggered.connect(self.open_krd_add_window)
        toolbar.addAction(add_krd_action)
        
        # Добавляем действие "Управление пользователями" (только для администраторов)
        if self.user_info.get('role') == 'admin':
            user_mgmt_action = QAction("Управление пользователями", self)
            user_mgmt_action.triggered.connect(self.open_user_management)
            toolbar.addAction(user_mgmt_action)
    
    def create_status_bar(self):
        """
        Создание строки состояния
        """
        status_bar = self.statusBar()
        status_bar.showMessage(f"Пользователь: {self.user_info['username']} | Роль: {self.user_info['role']}")
    
    def create_user_info_section(self):
        """
        Создание секции с информацией о пользователе
        """
        group_box = QGroupBox("Информация о пользователе")
        layout = QGridLayout()
        
        # Метки для отображения информации о пользователе
        username_label = QLabel(f"<b>Имя пользователя:</b> {self.user_info.get('username', 'N/A')}")
        full_name_label = QLabel(f"<b>ФИО:</b> {self.user_info.get('full_name', 'N/A')}")
        role_label = QLabel(f"<b>Роль:</b> {self.user_info.get('role', 'N/A')}")
        
        # Устанавливаем жирный шрифт для значений
        font = QFont()
        font.setBold(True)
        full_name_label.setFont(font)
        
        # Добавляем метки в макет
        layout.addWidget(username_label, 0, 0)
        layout.addWidget(full_name_label, 0, 1)
        layout.addWidget(role_label, 1, 0, 1, 2)  # Занимает 2 колонки
        
        group_box.setLayout(layout)
        return group_box
    
    def create_separator(self):
        """
        Создание разделителя между секциями
        """
        separator = QWidget()
        separator.setFixedHeight(10)
        return separator
    
    def create_krd_data_section(self):
        """
        Создание секции с данными КРД
        """
        group_box = QGroupBox("Данные КРД")
        layout = QVBoxLayout()
        #   Создаем модель данных для таблицы krd 
        self.table_model_krd = QSqlQueryModel()
        self.query_table_krd = """SELECT 
            k.id AS "ID",
            CONCAT('КРД-', k.id) AS "Номер КРД",  -- Генерируем номер КРД на основе ID
            s.surname AS "Фамилия",
            s.name AS "Имя", 
            s.patronymic AS "Отчество",
            st.name AS "Статус",
            k.last_service_place_id AS "ID последнего места службы"
        FROM krd.krd k
        LEFT JOIN krd.social_data s ON k.id = s.krd_id
        LEFT JOIN krd.statuses st ON k.status_id = st.id
        ORDER BY k.id DESC
        LIMIT 100"""
        self.table_model_krd.setQuery(self.query_table_krd,self.db)
        
        # Создаем таблицу для отображения данных КРД
        self.krd_table_view = QTableView()
        self.krd_table_view.setModel(self.table_model_krd)
        self.krd_table_view.setAlternatingRowColors(True)
        header = self.krd_table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.krd_table_view.doubleClicked.connect(self.on_krd_double_clicked)
        
        layout.addWidget(self.krd_table_view)
        group_box.setLayout(layout)
        
        return group_box
    
    def open_krd_add_window(self):
        krd_add_window = AddKrdWindow(self.db)

        if krd_add_window.exec() == QDialog.DialogCode.Accepted:
            self.load_krd_data()
    
    def open_user_management(self):
        """
        Открытие окна управления пользователями (только для администраторов)
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        from admin_user_management_tab import AdminUserManagementTab
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление пользователями")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Добавляем вкладку управления пользователями
        user_mgmt_tab = AdminUserManagementTab(self.db)
        layout.addWidget(user_mgmt_tab)
        
        # Кнопки OK и Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def on_krd_double_clicked(self, index):
        """
        Обработка двойного клика по строке в таблице КРД
        """
        # Получаем ID КРД из первой колонки (предполагается, что ID находится в первой колонке)
        krd_id = self.table_model_krd.data(self.table_model_krd.index(index.row(), 0))

        if krd_id:
            # Открываем окно деталей КРД
            from krd_details_window import KrdDetailsWindow  # импортируем класс
            details_window = KrdDetailsWindow(int(krd_id), self.db)

            if details_window.exec() == QDialog.DialogCode.Accepted:
                # Обновляем данные в таблице после сохранения
                self.load_krd_data()

    def load_krd_data(self):
       self.table_model_krd.setQuery(self.query_table_krd,self.db)
    
    def show_about_dialog(self):
        """
        Показ диалога "О программе"
        """
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "О программе",
            "АРМ Сотрудника дознания\n\n"
            "Главное окно приложения\n"
            f"Пользователь: {self.user_info.get('username', 'N/A')}\n"
            f"Роль: {self.user_info.get('role', 'N/A')}"
        )


def main():
    """
    Тестовая функция для демонстрации главного окна
    """
    app = QApplication(sys.argv)
    
    # Подключение к базе данных (для тестирования)
    db = QSqlDatabase.addDatabase("QPSQL")
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")
    
    if not db.open():
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных:\n{db.lastError().text()}")
        sys.exit(1)
    
    # Тестовые данные пользователя (обычно передаются из окна авторизации)
    user_info = {
        'id': 1,
        'username': 'test_user',
        'full_name': 'Иванов Иван Иванович',
        'role': 'Сотрудник'
    }
    
    # Создание и показ главного окна
    main_window = MainWindow(user_info, db)
    main_window.show()
    
    sys.exit(app.exec())


from PyQt6.QtWidgets import QAbstractItemView  # Импорт для использования в методе

if __name__ == "__main__":
    main()