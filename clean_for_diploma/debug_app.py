import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtSql import QSqlDatabase
from login_window import LoginWindow
from main_window import MainWindow
def main():
    app = QApplication(sys.argv)
    db = QSqlDatabase.addDatabase("QPSQL")
    db.setHostName("localhost")
    db.setDatabaseName("krd_system")
    db.setUserName("arm_user")
    db.setPassword("ArmUserSecurePass2026!")
    if not db.open():
        QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к базе данных:\n{db.lastError().text()}")
        sys.exit(1)
    print("Подключение к базе данных успешно")
    login_window = LoginWindow(db)
    main_window = None
    def open_main_window(user_info):
        nonlocal main_window
        try:
            print(f"Попытка создания главного окна для пользователя: {user_info}")
            main_window = MainWindow(user_info, db)
            print("Главное окно создано, показываем...")
            main_window.show()
            print("Главное окно показано")
            login_window.close()
            print("Окно авторизации закрыто")
        except Exception as e:
            print(f"Ошибка при создании главного окна: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(None, "Ошибка", f"Ошибка при открытии главного окна:\n{str(e)}\n{traceback.format_exc()}")
    login_window.login_successful.connect(open_main_window)
    login_window.show()
    print("Окно авторизации показано")
    sys.exit(app.exec())
if __name__ == "__main__":
    main()