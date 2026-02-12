"""
Модуль для вкладки формирования запроса в миграционную службу
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QGroupBox, QFileDialog, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtGui import QFont
import os
from datetime import datetime


class MigrationRequestTab(QWidget):
    """
    Вкладка для формирования запроса в миграционную службу
    """
    
    def __init__(self, krd_id, db_connection):
        """
        Инициализация вкладки запроса в миграционную службу
        
        Args:
            krd_id (int): ID КРД
            db_connection: соединение с базой данных
        """
        super().__init__()
        self.krd_id = krd_id
        self.db = db_connection
        
        self.init_ui()
        self.load_person_data()
    
    def init_ui(self):
        """
        Инициализация пользовательского интерфейса
        """
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Формирование запроса в миграционную службу")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Создаем область прокрутки для текста запроса
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Создаем виджет для содержимого области прокрутки
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Текст запроса
        self.request_text = QTextEdit()
        self.request_text.setMinimumHeight(500)
        content_layout.addWidget(self.request_text)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        generate_button = QPushButton("Сформировать запрос")
        generate_button.clicked.connect(self.generate_request)
        button_layout.addWidget(generate_button)
        
        save_button = QPushButton("Сохранить запрос")
        save_button.clicked.connect(self.save_request)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_person_data(self):
        """
        Загрузка данных о военнослужащем из базы данных
        """
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                s.surname, s.name, s.patronymic, s.birth_date, s.birth_place_town,
                s.tab_number, s.personal_number, s.passport_series, s.passport_number,
                s.passport_issue_date, s.passport_issued_by, s.education
            FROM krd.social_data s
            WHERE s.krd_id = ?
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        if query.next():
            self.person_data = {
                'surname': query.value('surname') or '',
                'name': query.value('name') or '',
                'patronymic': query.value('patronymic') or '',
                'birth_date': query.value('birth_date'),
                'birth_place_town': query.value('birth_place_town') or '',
                'tab_number': query.value('tab_number') or '',
                'personal_number': query.value('personal_number') or '',
                'passport_series': query.value('passport_series') or '',
                'passport_number': query.value('passport_number') or '',
                'passport_issue_date': query.value('passport_issue_date'),
                'passport_issued_by': query.value('passport_issued_by') or ''
            }
        else:
            self.person_data = {}
    
    def generate_request(self):
        """
        Генерация текста запроса с подстановкой данных военнослужащего
        """
        if not self.person_data:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить данные военнослужащего")
            return
        
        # Формирование текста запроса с подстановкой данных
        request_text = f"""Начальнику отдела по вопросам миграции
УМВД России г. Абакан
О.В. Джумашевой
655017, Республика Хакасия, г. Абакан, 
ул. Чертыгашева, д. 104,
8 390 223 74 95

Военной комендатурой (гарнизона, 3 разряда) (г. Абакан) проводятся разыскные мероприятия в отношении военнослужащего по контракту войсковой части 42038 рядового {self.person_data['surname']} {self.person_data['name']} {self.person_data['patronymic']}, {self.format_date(self.person_data['birth_date'])} года рождения, уроженца {self.person_data['birth_place_town']}, зарегистрированного (проживающего) по адресу: Красноярский край, г. Минусинск, ул. Народная, д. 62Г, кв. 5, паспорт {self.person_data['passport_series']} {self.person_data['passport_number']}, выданный {self.format_date(self.person_data['passport_issue_date'])} {self.person_data['passport_issued_by']}.

Руководствуясь, положениями межведомственного приказа от 24 октября 2023 года № 92/1/12533/113/22505/1/15-МВС «О мерах по активизации розыска лиц, совершивших преступления против порядка пребывания на военной службе» прошу Вас оказать содействие в розыске указанного военнослужащего, для чего поставить последнего на сторожевой контроль, а также сообщить в адрес военной комендатуры актуальные сведения о его регистрации по месту жительства, месте пребывания, паспортные данные.

В случае установления местонахождения военнослужащего поршу сообщить в военную комендатуру (гарнизона, 3 разряда) (г. Абакан).

Ответ прошу направить по адресу: 655011, г. Абакан, ул. Аскизская, д. 240А, военная комендатура (гарнизона, 3 разряда) (г. Абакан). 
Телефон для связи (факс) 8 (390) 235-58-77.

Временно исполняющий обязанности
военного коменданта военной комендатуры
(гарнизона, 3 разряда) (г. Абакан)
лейтенант юстиции
И.Кувандыков"""
        
        self.request_text.setPlainText(request_text)
    
    def format_date(self, date_value):
        """
        Форматирование даты для отображения
        """
        if date_value is None:
            return ""
        
        if isinstance(date_value, str):
            # Если дата в формате строки, преобразуем её
            try:
                date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return date_obj.strftime("%d.%m.%Y")
            except:
                return date_value
        elif hasattr(date_value, 'toString'):
            # Если это объект QDate
            return date_value.toString("dd.MM.yyyy")
        else:
            return str(date_value)
    
    def save_request(self):
        """
        Сохранение запроса в файл
        """
        if not self.request_text.toPlainText():
            QMessageBox.warning(self, "Ошибка", "Сначала сформируйте запрос")
            return
        
        # Открываем диалог сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить запрос",
            f"Запрос_миграция_{self.krd_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.request_text.toPlainText())
                
                QMessageBox.information(self, "Успех", f"Запрос сохранен в файл:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении файла:\n{str(e)}")