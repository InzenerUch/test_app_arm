from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

def create_architecture_section():
    """Создание раздела о проектировании архитектуры АРМ"""
    doc = Document()
    
    # Настройка стилей
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)
    
    # Добавление заголовка раздела
    heading = doc.add_heading('2.2 Архитектура программного продукта', level=2)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()  # Пустая строка
    
    # Основной текст
    text1 = """Проектирование архитектуры автоматизированного рабочего места (АРМ) сотрудника отдела дознания осуществлялось с учётом требований к отказоустойчивости, информационной безопасности, масштабируемости и удобства сопровождения. В качестве базовой парадигмы выбрана трёхуровневая клиент-серверная архитектура с адаптацией паттерна Model-View-Controller (MVC). Данное решение обеспечивает строгое разделение ответственности между слоями, минимизирует связность компонентов и упрощает независимое тестирование каждого модуля системы."""
    
    p1 = doc.add_paragraph(text1)
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p1.paragraph_format.first_line_indent = Cm(1.25)
    p1.paragraph_format.line_spacing = 1.5
    
    doc.add_paragraph()  # Пустая строка
    
    # Рисунок 2.2 - Схема архитектуры
    doc.add_paragraph('Рисунок 2.2 – Схема архитектуры приложения (клиент → логика → БД)', style='Caption')
    doc.add_paragraph()
    
    # Здесь можно добавить изображение архитектуры
    # if os.path.exists('architecture_diagram.png'):
    #     doc.add_picture('architecture_diagram.png', width=Inches(6))
    #     doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    # Текст про трёхуровневую архитектуру
    text2 = """Трёхуровневая архитектура является стандартом де-факто для корпоративных информационных систем, обрабатывающих конфиденциальные данные. В рамках проекта архитектура разделена на три изолированных логических уровня: уровень представления (Presentation Layer), уровень бизнес-логики (Business Logic Layer) и уровень данных (Data Access Layer). Взаимодействие между уровнями осуществляется через строго определённые интерфейсы, что исключает риски несанкционированного доступа и SQL-инъекций."""
    
    p2 = doc.add_paragraph(text2)
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p2.paragraph_format.first_line_indent = Cm(1.25)
    p2.paragraph_format.line_spacing = 1.5
    
    doc.add_paragraph()
    
    text3 = """Уровень представления реализован на базе фреймворка PyQt6 и инкапсулирует графический интерфейс пользователя, включая визуализацию данных, мгновенную валидацию ввода и обработку событий. Уровень бизнес-логики содержит алгоритмы генерации документов, экспорта в Excel, автодополнения полей и ведения журнала аудита. Уровень данных реализован на базе PostgreSQL 16 и отвечает за персистентное хранение, ACID-транзакции и криптографическую защиту."""
    
    p3 = doc.add_paragraph(text3)
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p3.paragraph_format.first_line_indent = Cm(1.25)
    p3.paragraph_format.line_spacing = 1.5
    
    doc.add_paragraph()
    
    text4 = """Адаптация MVC в PyQt6 учитывает особенности Qt-SQL модулей. В роли Model выступают классы QSqlQueryModel и QSqlTableModel, обеспечивающие ленивую загрузку данных и автоматическую синхронизацию состояний. Представление (View) использует стандартные компоненты PyQt6: QTableView для списков, QTabWidget для навигации, QDialog для модальных окон. Контроллеры инкапсулированы в классах диалогов, обрабатывают события, валидируют данные и управляют транзакциями."""
    
    p4 = doc.add_paragraph(text4)
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p4.paragraph_format.first_line_indent = Cm(1.25)
    p4.paragraph_format.line_spacing = 1.5
    
    doc.add_paragraph()
    
    text5 = """Информационная модель данных, лежащая в основе архитектуры системы, формализована в нотации IDEF1X. Диаграммы отображают трансформацию процессов обработки карточек розыска (КРД) при переходе от ручного учёта к автоматизированному рабочему месту."""
    
    p5 = doc.add_paragraph(text5)
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p5.paragraph_format.first_line_indent = Cm(1.25)
    p5.paragraph_format.line_spacing = 1.5
    
    doc.add_paragraph()
    
    # Диаграмма вариантов использования
    doc.add_paragraph('Рисунок 2.5 – Диаграмма вариантов использования системы', style='Caption')
    doc.add_paragraph()
    
    # Вставка диаграммы вариантов использования
    if os.path.exists('use_case_diagram.png'):
        doc.add_picture('use_case_diagram.png', width=Inches(6.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    text6 = """Диаграмма вариантов использования (Рисунок 2.5) определяет границы системы и роли пользователей. Основной актор «Пользователь» (Дознаватель) взаимодействует с системой для ведения карточек розыска (КРД), работы с адресами проживания, местами прохождения службы, входящими поручениями и эпизодами СОЧ, а также создания отчётов. Актор «Администратор» обладает расширенными функциональными возможностями: управление пользователями системы (добавление, редактирование, активация, удаление), просмотр журнала аудита действий пользователей, работа с удалёнными записями (просмотр и восстановление). Все операции начинаются с авторизации в системе и включают настройку интерфейса программы."""
    
    p6 = doc.add_paragraph(text6)
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p6.paragraph_format.first_line_indent = Cm(1.25)
    p6.paragraph_format.line_spacing = 1.5
    
    doc.add_paragraph()
    
    # Диаграмма активностей
    doc.add_paragraph('Рисунок 2.6 – Диаграмма активностей создания и сохранения КРД', style='Caption')
    doc.add_paragraph()
    
    # if os.path.exists('activity_diagram.png'):
    #     doc.add_picture('activity_diagram.png', width=Inches(6))
    #     doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    text7 = """Диаграмма активностей (Рисунок 2.6) визуализирует алгоритм создания и сохранения новой карточки розыска. Процесс начинается с ввода данных в интерфейс, после чего система выполняет автоматическую проверку обязательных полей и соответствие форматов регулярным выражениям. В случае ошибок транзакция отклоняется, пользователю выводится структурированное сообщение. При успешной валидации данные записываются в БД в рамках единой транзакции BEGIN TRANSACTION, одновременно создаётся запись в таблице audit_log с типом действия CREATE и фиксацией новых значений. Транзакция завершается командой COMMIT, что гарантирует атомарность и отсутствие «висячих» состояний в базе данных."""
    
    p7 = doc.add_paragraph(text7)
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p7.paragraph_format.first_line_indent = Cm(1.25)
    p7.paragraph_format.line_spacing = 1.5
    
    doc.add_paragraph()
    
    # Диаграмма последовательности
    doc.add_paragraph('Рисунок 2.7 – Диаграмма последовательности сохранения данных', style='Caption')
    doc.add_paragraph()
    
    # if os.path.exists('sequence_diagram.png'):
    #     doc.add_picture('sequence_diagram.png', width=Inches(6))
    #     doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()
    
    text8 = """Диаграмма последовательности (Рисунок 2.7) детализирует временное взаимодействие слоёв MVC при сохранении записи. Пользователь инициирует действие в UI (View), которое передаёт событие Контроллеру. Контроллер выполняет бизнес-логику валидации и формирует подготовленный SQL-запрос (PREPARE), передавая параметры через bindValue для предотвращения SQL-инъекций. СУБД выполняет INSERT внутри транзакции и возвращает сгенерированный id. После успешного сохранения контроллер вызывает метод логгера аудита и отправляет UI подтверждение об успешном завершении. При возникновении ошибки на любом этапе вызывается ROLLBACK, интерфейс остаётся в стабильном состоянии, а пользователю выводится сообщение с кодом исключения СУБД."""
    
    p8 = doc.add_paragraph(text8)
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p8.paragraph_format.first_line_indent = Cm(1.25)
    p8.paragraph_format.line_spacing = 1.5
    
    doc.add_paragraph()
    
    # Заключительный абзац
    text9 = """Таким образом, спроектированная архитектура обеспечивает высокую модульность, безопасность данных и прозрачность процессуальных действий. Использование трёхуровневой модели, паттерна MVC и стандартизированных диаграмм UML/IDEF1X позволяет эффективно сопровождать систему, масштабировать её компоненты и гарантировать соответствие требованиям ФЗ-152 «О персональных данных» и приказам ФСТЭК РФ по защите информации в изолированных информационных системах."""
    
    p9 = doc.add_paragraph(text9)
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p9.paragraph_format.first_line_indent = Cm(1.25)
    p9.paragraph_format.line_spacing = 1.5
    
    # Сохранение документа
    doc.save('section_2_2_architecture.docx')
    print("Документ section_2_2_architecture.docx успешно создан!")

if __name__ == "__main__":
    create_architecture_section()