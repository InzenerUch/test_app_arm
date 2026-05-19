#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор продолжения раздела 2.4 "Проектирование базы данных"
Оформление согласно методическим указаниям (ГОСТ)
Исправлена ошибка WD_LINE_SPACING
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime


def setup_document():
    """Настройка документа согласно методичке"""
    doc = Document()
    
    # Настройка стиля Normal
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)
    font.color.rgb = RGBColor(0, 0, 0)
    
    # ✅ ИСПРАВЛЕНО: Используем Enum вместо float 1.5
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)
    
    # Отступ первой строки 1.25 см
    style.paragraph_format.first_line_indent = Cm(1.25)
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    # Настройка для кириллицы
    element = style.element.get_or_add_rPr()
    run_font = element.get_or_add_rFonts()
    run_font.set(qn('w:eastAsia'), 'Times New Roman')
    
    return doc


def add_heading(doc, text, level=1):
    """Добавление заголовка раздела"""
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(1.25)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    
    run = p.add_run(text)
    run.bold = True
    run.font.name = 'Times New Roman'
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)
    
    return p


def add_text(doc, text):
    """Добавление обычного текста"""
    p = doc.add_paragraph(text)
    p.paragraph_format.first_line_indent = Cm(1.25)
    return p


def add_list_item(doc, text, bullet=True):
    """Добавление элемента списка"""
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(1.25)
    
    if bullet:
        run = p.add_run('– ')
        run.bold = False
    else:
        run = p.add_run('   ')
        
    run_text = p.add_run(text)
    run_text.font.name = 'Times New Roman'
    run_text.font.size = Pt(14)
    
    return p


def set_cell_border(cell, **kwargs):
    """Установка границ для ячейки таблицы"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    
    tcBorders = tcPr.first_child_found_in('w:tcBorders')
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    
    for edge in ('start', 'left', 'top', 'bottom', 'end', 'right'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            
            for key in ['val', 'sz', 'space', 'color']:
                if key in edge_data:
                    element.set(qn(f'w:{key}'), str(edge_data[key]))


def create_formatted_table(doc, table_data, caption):
    """Создание таблицы с форматированием согласно ГОСТ"""
    # Добавляем подпись таблицы
    caption_para = doc.add_paragraph()
    caption_run = caption_para.add_run(caption)
    caption_run.bold = True
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_para.paragraph_format.space_after = Pt(6)
    
    # Создаем таблицу
    num_columns = len(table_data[0])
    table = doc.add_table(rows=1, cols=num_columns)
    table.style = 'Table Grid'
    table.autofit = False
    
    # Настраиваем ширину колонок
    for i, col in enumerate(table.columns):
        if i == 0:
            col.width = Cm(3.5)
        elif i == 1:
            col.width = Cm(3.0)
        elif i == 2:
            col.width = Cm(3.5)
        else:
            col.width = Cm(6.0)
    
    # Заполняем заголовок таблицы
    hdr_cells = table.rows[0].cells
    for i, heading in enumerate(table_data[0]):
        p = hdr_cells[i].paragraphs[0]
        run = p.add_run(heading)
        run.bold = True
        run.font.size = Pt(12)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        set_cell_border(hdr_cells[i], 
                       top={'val': 'single', 'sz': 4},
                       bottom={'val': 'single', 'sz': 4},
                       left={'val': 'single', 'sz': 4},
                       right={'val': 'single', 'sz': 4})
    
    # Заполняем данными
    for row_data in table_data[1:]:
        row_cells = table.add_row().cells
        for i, item in enumerate(row_data):
            p = row_cells[i].paragraphs[0]
            run = p.add_run(str(item))
            run.font.size = Pt(12)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i < 3 else WD_ALIGN_PARAGRAPH.LEFT
            
            set_cell_border(row_cells[i],
                           top={'val': 'single', 'sz': 4},
                           bottom={'val': 'single', 'sz': 4},
                           left={'val': 'single', 'sz': 4},
                           right={'val': 'single', 'sz': 4})
    
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    return table


def generate_section_continuation_docx():
    """Генерация продолжения раздела 2.4 в формате DOCX"""
    doc = setup_document()
    
    # Вводный текст
    add_text(doc, 
        "Помимо основных сущностей предметной области (КРД и связанные данные), "
        "информационная модель включает таблицы для управления процессами отчётности, "
        "персонализации интерфейса и контроля безопасности. Данные таблицы обеспечивают "
        "гибкость настройки системы под нужды конкретного сотрудника и соответствие "
        "требованиям аудита."
    )
    
    # --- Таблица 2.14: Шаблоны отчетов ---
    table_2_14_data = [
        ['Поле', 'Тип', 'Ограничения', 'Описание'],
        ['id', 'SERIAL', 'PK', 'Уникальный ID шаблона'],
        ['name', 'VARCHAR(255)', 'NOT NULL', 'Название шаблона'],
        ['template_type', 'VARCHAR(50)', "DEFAULT 'excel'", 'Тип экспорта'],
        ['config_json', 'JSONB', 'NOT NULL', 'Конфигурация полей отчета'],
        ['is_deleted', 'BOOLEAN', 'DEFAULT FALSE', 'Мягкое удаление'],
    ]
    create_formatted_table(doc, table_2_14_data, "Таблица 2.14 – Структура таблицы krd.report_templates")
    
    add_text(doc,
        "Таблица krd.report_templates хранит пользовательские конфигурации для массового "
        "экспорта данных. Ключевым элементом является поле config_json (тип JSONB), которое "
        "сохраняет структуру отчёта: список включенных секций и конкретных полей."
    )
    
    # --- Таблица 2.15: Сгенерированные документы ---
    table_2_15_data = [
        ['Поле', 'Тип', 'Ограничения', 'Описание'],
        ['id', 'SERIAL', 'PK', 'Уникальный ID записи'],
        ['krd_id', 'INTEGER', 'FK → krd.id', 'Ссылка на карточку розыска'],
        ['template_id', 'INTEGER', 'FK → report_templates', 'Использованный шаблон'],
        ['document_data', 'BYTEA', 'NULL', 'Бинарные данные файла (.docx/.xlsx)'],
        ['file_name', 'VARCHAR(255)', 'NULL', 'Имя файла'],
        ['generated_at', 'TIMESTAMP', 'DEFAULT NOW()', 'Дата генерации'],
    ]
    create_formatted_table(doc, table_2_15_data, "Таблица 2.15 – Структура таблицы krd.generated_documents")
    
    add_text(doc,
        "Таблица krd.generated_documents реализует функцию архивации созданных документов. "
        "Файлы хранятся в бинарном виде (BYTEA), что гарантирует атомарность транзакций "
        "и упрощает резервное копирование."
    )
    
    # --- Таблица 2.16: Настройки пользователя ---
    table_2_16_data = [
        ['Поле', 'Тип', 'Ограничения', 'Описание'],
        ['id', 'SERIAL', 'PK', 'Уникальный ID настроек'],
        ['user_id', 'INTEGER', 'FK → users.id', 'Привязка к пользователю'],
        ['theme_name', 'VARCHAR(50)', "DEFAULT 'light'", 'Название темы'],
        ['config_json', 'JSONB', 'NULL', 'JSON с параметрами UI (шрифт, цвета)'],
    ]
    create_formatted_table(doc, table_2_16_data, "Таблица 2.16 – Структура таблицы krd.user_settings")
    
    add_text(doc,
        "Таблица krd.user_settings отвечает за персонализацию рабочего места оператора. "
        "Поле config_json хранит сериализованные настройки интерфейса."
    )
    
    # --- Таблица 2.17: Пользовательские темы ---
    table_2_17_data = [
        ['Поле', 'Тип', 'Ограничения', 'Описание'],
        ['id', 'SERIAL', 'PK', 'Уникальный ID темы'],
        ['user_id', 'INTEGER', 'FK → users.id', 'Владелец темы'],
        ['theme_name', 'VARCHAR(100)', 'NOT NULL', 'Название темы'],
        ['config_json', 'JSONB', 'NOT NULL', 'Цветовая схема (HEX коды)'],
        ['is_active', 'BOOLEAN', 'DEFAULT FALSE', 'Активная тема сейчас'],
    ]
    create_formatted_table(doc, table_2_17_data, "Таблица 2.17 – Структура таблицы krd.user_themes")
    
    add_text(doc,
        "Таблица krd.user_themes позволяет создавать неограниченное количество визуальных "
        "тем оформления. Конфигурация цветов хранится в JSONB."
    )
    
    # --- Таблица 2.18: Сессии пользователей ---
    table_2_18_data = [
        ['Поле', 'Тип', 'Ограничения', 'Описание'],
        ['id', 'SERIAL', 'PK', 'Уникальный ID сессии'],
        ['user_id', 'INTEGER', 'FK → users.id', 'Владелец сессии'],
        ['login_time', 'TIMESTAMP', 'NOT NULL', 'Время входа'],
        ['logout_time', 'TIMESTAMP', 'NULL', 'Время выхода'],
        ['is_active', 'BOOLEAN', 'DEFAULT TRUE', 'Статус сессии'],
    ]
    create_formatted_table(doc, table_2_18_data, "Таблица 2.18 – Структура таблицы krd.user_sessions")
    
    add_text(doc,
        "Таблица krd.user_sessions используется для контроля безопасности. Она фиксирует "
        "каждое успешное вхождение в систему для выявления аномальной активности."
    )
    
    # Выводы по разделу
    add_heading(doc, "2.4.4 Выводы по проектированию базы данных", level=2)
    
    add_list_item(doc, 
        "Разработана полноценная реляционная схема krd, состоящая из 26 таблиц. "
        "Структура покрывает все требования ТЗ: от учёта персональных данных до гибкой "
        "настройки отчётности и интерфейса."
    )
    
    add_list_item(doc, 
        "Активное использование типа данных JSONB (в таблицах field_mappings, "
        "report_templates, user_settings) позволило реализовать гибкие конфигурации "
        "без изменения структуры БД (DDL-операций) при обновлении функционала."
    )
    
    add_list_item(doc, 
        "Реализован механизм мягкого удаления (is_deleted) для всех критичных таблиц. "
        "Это обеспечивает сохранность истории операций и возможность восстановления "
        "ошибочно удалённых записей администратором."
    )
    
    add_list_item(doc, 
        "Бинарные данные (фотографии, сканы документов, сгенерированные файлы) хранятся "
        "в полях типа BYTEA. Это упрощает процедуру резервного копирования и гарантирует "
        "атомарность хранения файла вместе с его метаданными."
    )
    
    add_list_item(doc, 
        "Спроектирована система аудита (audit_log) и контроля сессий (user_sessions), "
        "обеспечивающая соответствие требованиям информационной безопасности."
    )
    
    return doc


def main():
    """Основная функция"""
    doc = generate_section_continuation_docx()
    
    # Сохранение файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"section_2.4_schema_part2_{timestamp}.docx"
    
    doc.save(filename)
    
    print(f"✅ Раздел 2.4 (продолжение) сгенерирован и сохранён в файл: {filename}")
    print(f"\n{'='*70}")
    print("ИНСТРУКЦИЯ:")
    print('='*70)
    print("1. Откройте сгенерированный файл в Microsoft Word")
    print("2. Проверьте форматирование таблиц и текста")
    print("3. При необходимости добавьте перекрёстные ссылки")
    print("4. Вставьте этот раздел после описания основных таблиц (2.4.3)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()