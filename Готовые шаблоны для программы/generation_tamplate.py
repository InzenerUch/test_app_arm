"""
Генератор диаграммы жизненного цикла АРМ
Период: Осень 2025 — Май 2026
"""

from graphviz import Digraph
import os


def create_lifecycle_diagram_2025_2026():
    """
    Создание диаграммы итеративно-инкрементной модели ЖЦ
    Период: Ноябрь 2025 — Май 2026
    """
    
    # Создаём граф
    dot = Digraph(
        comment='Жизненный цикл АРМ Сотрудника дознания 2025-2026',
        format='png',
        engine='dot',
        graph_attr={
            'rankdir': 'LR',  # Left to Right
            'fontsize': '14',
            'fontname': 'Arial',
            'bgcolor': 'white',
            'compound': 'true',
            'dpi': '300',
            'label': '📊 ИТЕРАТИВНО-ИНКРЕМЕНТНАЯ МОДЕЛЬ ЖИЗНЕННОГО ЦИКЛА\nПериод реализации: Ноябрь 2025 — Май 2026',
            'labelloc': 't',
            'labelfontsize': '16',
            'labelfontcolor': '#003366'
        },
        node_attr={
            'shape': 'box',
            'style': 'filled,rounded',
            'fontname': 'Arial',
            'fontsize': '10',
            'penwidth': '2'
        },
        edge_attr={
            'fontname': 'Arial',
            'fontsize': '9',
            'penwidth': '2'
        }
    )
    
    # ==================== ИТЕРАЦИЯ 1 ====================
    with dot.subgraph(name='cluster_iter1') as c:
        c.attr(label='🔵 ИТЕРАЦИЯ 1\nНоябрь — Декабрь 2025',
               style='filled',
               color='#E3F2FD',
               fontsize='12',
               fontname='Arial Bold',
               pencolor='#1976D2',
               penwidth='3')
        
        c.node('iter1_analysis', '📋 Анализ\nтребований',
               fillcolor='#BBDEFB',
               shape='parallelogram')
        
        c.node('iter1_design', '🏗️ Проектирование\nБД + UI',
               fillcolor='#90CAF9',
               shape='box')
        
        c.node('iter1_auth', '🔐 Модуль\nавторизации',
               fillcolor='#64B5F6',
               shape='box')
        
        c.node('iter1_crud', '✏️ CRUD КРД\n(базовый)',
               fillcolor='#42A5F5',
               shape='box')
        
        c.node('iter1_result', '✅ Ядро системы\n(работоспособное)',
               fillcolor='#2196F3',
               shape='folder',
               fontcolor='white')
    
    # ==================== ИТЕРАЦИЯ 2 ====================
    with dot.subgraph(name='cluster_iter2') as c:
        c.attr(label='🟢 ИТЕРАЦИЯ 2\nДекабрь 2025 — Январь 2026',
               style='filled',
               color='#E8F5E9',
               fontsize='12',
               fontname='Arial Bold',
               pencolor='#388E3C',
               penwidth='3')
        
        c.node('iter2_addresses', '🏠 Адреса\nпроживания',
               fillcolor='#C8E6C9',
               shape='box')
        
        c.node('iter2_service', '🎖️ Места\nслужбы',
               fillcolor='#A5D6A7',
               shape='box')
        
        c.node('iter2_incoming', '📬 Входящие\nпоручения',
               fillcolor='#81C784',
               shape='box')
        
        c.node('iter2_soch', '⚠️ Эпизоды\nСОЧ',
               fillcolor='#66BB6A',
               shape='box')
        
        c.node('iter2_autocomplete', '⚡ Авто-\nдополнение',
               fillcolor='#4CAF50',
               shape='box')
        
        c.node('iter2_result', '✅ Расширенная\nкарточка КРД',
               fillcolor='#388E3C',
               shape='folder',
               fontcolor='white')
    
    # ==================== ИТЕРАЦИЯ 3 ====================
    with dot.subgraph(name='cluster_iter3') as c:
        c.attr(label='🟡 ИТЕРАЦИЯ 3\nЯнварь — Февраль 2026',
               style='filled',
               color='#FFF8E1',
               fontsize='12',
               fontname='Arial Bold',
               pencolor='#F57C00',
               penwidth='3')
        
        c.node('iter3_templates', '📄 Шаблоны\nдокументов',
               fillcolor='#FFE0B2',
               shape='box')
        
        c.node('iter3_mapping', '🔗 Динамический\nмаппинг',
               fillcolor='#FFCC80',
               shape='box')
        
        c.node('iter3_jsonb', '📦 JSONB\nсоставные поля',
               fillcolor='#FFB74D',
               shape='box')
        
        c.node('iter3_bytea', '💾 BYTEA\nхранение файлов',
               fillcolor='#FFA726',
               shape='cylinder')
        
        c.node('iter3_result', '✅ Генератор\nдокументов .docx',
               fillcolor='#F57C00',
               shape='folder',
               fontcolor='white')
    
    # ==================== ИТЕРАЦИЯ 4 ====================
    with dot.subgraph(name='cluster_iter4') as c:
        c.attr(label='🟠 ИТЕРАЦИЯ 4\nФевраль — Март 2026',
               style='filled',
               color='#FFEBEE',
               fontsize='12',
               fontname='Arial Bold',
               pencolor='#D32F2F',
               penwidth='3')
        
        c.node('iter4_excel', '📊 Экспорт\nExcel',
               fillcolor='#FFCDD2',
               shape='box')
        
        c.node('iter4_audit', '🔍 Система\nаудита',
               fillcolor='#EF9A9A',
               shape='box')
        
        c.node('iter4_softdelete', '🗑️ Мягкое\nудаление',
               fillcolor='#E57373',
               shape='box')
        
        c.node('iter4_admin', '⚙️ Админ-\nпанель',
               fillcolor='#EF5350',
               shape='box')
        
        c.node('iter4_result', '✅ Полная\nфункциональность',
               fillcolor='#F44336',
               shape='folder',
               fontcolor='white')
    
    # ==================== ИТЕРАЦИЯ 5 ====================
    with dot.subgraph(name='cluster_iter5') as c:
        c.attr(label='🟣 ИТЕРАЦИЯ 5\nАпрель — Май 2026',
               style='filled',
               color='#F3E5F5',
               fontsize='12',
               fontname='Arial Bold',
               pencolor='#7B1FA2',
               penwidth='3')
        
        c.node('iter5_testing', '🧪 Комплексное\nтестирование',
               fillcolor='#E1BEE7',
               shape='hexagon')
        
        c.node('iter5_docs', '📚 Докумен-\nтация',
               fillcolor='#CE93D8',
               shape='note')
        
        c.node('iter5_security', '🔒 Security-\nтестирование',
               fillcolor='#BA68C8',
               shape='box')
        
        c.node('iter5_deploy', '🚀 Развёрты-\nвание',
               fillcolor='#AB47BC',
               shape='box')
        
        c.node('iter5_result', '✅ ГОТОВЫЙ ПП\n(внедрение)',
               fillcolor='#8E24AA',
               shape='folder',
               fontcolor='white',
               fontsize='11')
    
    # ==================== СВЯЗИ МЕЖДУ ИТЕРАЦИЯМИ ====================
    
    # Итерация 1
    dot.edge('iter1_analysis', 'iter1_design', '1-2 нед')
    dot.edge('iter1_design', 'iter1_auth', '3-4 нед')
    dot.edge('iter1_auth', 'iter1_crud', '5-6 нед')
    dot.edge('iter1_crud', 'iter1_result', '7-8 нед')
    
    # Переход между итерациями
    dot.edge('iter1_result', 'iter2_addresses',
             label='🔄 Инкремент 1',
             style='dashed',
             color='#666666',
             penwidth='2')
    
    # Итерация 2
    dot.edge('iter2_addresses', 'iter2_service', '1-2 нед')
    dot.edge('iter2_service', 'iter2_incoming', '3-4 нед')
    dot.edge('iter2_incoming', 'iter2_soch', '5-6 нед')
    dot.edge('iter2_soch', 'iter2_autocomplete', '7 нед')
    dot.edge('iter2_autocomplete', 'iter2_result', '8 нед')
    
    # Переход между итерациями
    dot.edge('iter2_result', 'iter3_templates',
             label='🔄 Инкремент 2',
             style='dashed',
             color='#666666',
             penwidth='2')
    
    # Итерация 3
    dot.edge('iter3_templates', 'iter3_mapping', '1-2 нед')
    dot.edge('iter3_mapping', 'iter3_jsonb', '3 нед')
    dot.edge('iter3_jsonb', 'iter3_bytea', '4 нед')
    dot.edge('iter3_bytea', 'iter3_result', '5-6 нед')
    
    # Переход между итерациями
    dot.edge('iter3_result', 'iter4_excel',
             label='🔄 Инкремент 3',
             style='dashed',
             color='#666666',
             penwidth='2')
    
    # Итерация 4
    dot.edge('iter4_excel', 'iter4_audit', '1-2 нед')
    dot.edge('iter4_audit', 'iter4_softdelete', '3 нед')
    dot.edge('iter4_softdelete', 'iter4_admin', '4 нед')
    dot.edge('iter4_admin', 'iter4_result', '5-6 нед')
    
    # Переход между итерациями
    dot.edge('iter4_result', 'iter5_testing',
             label='🔄 Инкремент 4',
             style='dashed',
             color='#666666',
             penwidth='2')
    
    # Итерация 5
    dot.edge('iter5_testing', 'iter5_docs', '1-2 нед')
    dot.edge('iter5_docs', 'iter5_security', '3-4 нед')
    dot.edge('iter5_security', 'iter5_deploy', '5-6 нед')
    dot.edge('iter5_deploy', 'iter5_result', '7-8 нед')
    
    # ==================== ВРЕМЕННАЯ ШКАЛА ====================
    
    with dot.subgraph(name='cluster_timeline') as c:
        c.attr(label='📅 ВРЕМЕННАЯ ШКАЛА',
               style='filled',
               color='#FAFAFA',
               fontsize='11',
               fontname='Arial Bold',
               pencolor='#999999',
               penwidth='2')
        
        c.node('timeline_nov', 'Ноябрь\n2025',
               shape='plaintext',
               fontcolor='#1976D2')
        
        c.node('timeline_dec', 'Декабрь\n2025',
               shape='plaintext',
               fontcolor='#388E3C')
        
        c.node('timeline_jan', 'Январь\n2026',
               shape='plaintext',
               fontcolor='#F57C00')
        
        c.node('timeline_feb', 'Февраль\n2026',
               shape='plaintext',
               fontcolor='#F44336')
        
        c.node('timeline_mar', 'Март\n2026',
               shape='plaintext',
               fontcolor='#F44336')
        
        c.node('timeline_apr', 'Апрель\n2026',
               shape='plaintext',
               fontcolor='#8E24AA')
        
        c.node('timeline_may', 'Май\n2026',
               shape='plaintext',
               fontcolor='#8E24AA')
        
        # Связи временной шкалы
        dot.edge('timeline_nov', 'timeline_dec', style='dotted')
        dot.edge('timeline_dec', 'timeline_jan', style='dotted')
        dot.edge('timeline_jan', 'timeline_feb', style='dotted')
        dot.edge('timeline_feb', 'timeline_mar', style='dotted')
        dot.edge('timeline_mar', 'timeline_apr', style='dotted')
        dot.edge('timeline_apr', 'timeline_may', style='dotted')
    
    # ==================== ЛЕГЕНДА ====================
    
    with dot.subgraph(name='cluster_legend') as c:
        c.attr(label='📋 ЛЕГЕНДА',
               style='filled',
               color='#F5F5F5',
               fontsize='10',
               fontname='Arial Bold',
               pencolor='#999999')
        
        c.node('legend_shape', '▢ Этап разработки',
               shape='plaintext',
               fontname='Arial')
        
        c.node('legend_parallelogram', '⧄ Анализ/Проектирование',
               shape='plaintext',
               fontname='Arial')
        
        c.node('legend_hexagon', '⬡ Тестирование',
               shape='plaintext',
               fontname='Arial')
        
        c.node('legend_cylinder', '🛢️ База данных',
               shape='plaintext',
               fontname='Arial')
        
        c.node('legend_folder', '📁 Результат итерации',
               shape='plaintext',
               fontname='Arial')
        
        c.node('legend_arrow', '➡️ Последовательность',
               shape='plaintext',
               fontname='Arial')
        
        c.node('legend_dashed', '⇢ Инкремент',
               shape='plaintext',
               fontname='Arial')
    
    # Сохраняем диаграмму
    output_path = dot.render('lifecycle_diagram_2025_2026',
                             directory='.',
                             cleanup=True)
    
    print(f"✅ Диаграмма жизненного цикла сохранена: {output_path}")
    print(f"📁 Формат: PNG (300 DPI)")
    print(f"📊 Количество узлов: {len(dot.body)}")
    print(f"📅 Период: Ноябрь 2025 — Май 2026 (7 месяцев)")
    
    return output_path


def create_gantt_chart():
    """
    Создание упрощённой диаграммы Ганта для презентации
    """
    
    dot = Digraph(
        comment='Диаграмма Ганта АРМ 2025-2026',
        format='png',
        engine='dot',
        graph_attr={
            'rankdir': 'TB',
            'fontsize': '14',
            'fontname': 'Arial',
            'bgcolor': 'white',
            'dpi': '300',
            'label': '📅 ДИАГРАММА ГАНТА\nПериод реализации: Ноябрь 2025 — Май 2026',
            'labelloc': 't',
            'labelfontsize': '16',
            'labelfontcolor': '#003366'
        },
        node_attr={
            'shape': 'box',
            'style': 'filled,rounded',
            'fontname': 'Arial',
            'fontsize': '10',
            'penwidth': '2'
        }
    )
    
    # Месяцы
    months = [
        ('nov2025', 'Ноябрь\n2025', '#E3F2FD'),
        ('dec2025', 'Декабрь\n2025', '#E8F5E9'),
        ('jan2026', 'Январь\n2026', '#FFF8E1'),
        ('feb2026', 'Февраль\n2026', '#FFEBEE'),
        ('mar2026', 'Март\n2026', '#FFEBEE'),
        ('apr2026', 'Апрель\n2026', '#F3E5F5'),
        ('may2026', 'Май\n2026', '#F3E5F5')
    ]
    
    # Создаём узлы месяцев
    for node_id, label, color in months:
        dot.node(node_id, label, fillcolor=color, penwidth='3')
    
    # Задачи по итерациям
    tasks = [
        ('Итерация 1\n(Ядро системы)', ['nov2025', 'dec2025'], '#2196F3'),
        ('Итерация 2\n(Связанные сущности)', ['dec2025', 'jan2026'], '#4CAF50'),
        ('Итерация 3\n(Генератор документов)', ['jan2026', 'feb2026'], '#FF9800'),
        ('Итерация 4\n(Отчёты + Аудит)', ['feb2026', 'mar2026'], '#F44336'),
        ('Итерация 5\n(Тестирование + Внедрение)', ['apr2026', 'may2026'], '#9C27B0')
    ]
    
    # Создаём узлы задач
    for i, (task_name, month_ids, color) in enumerate(tasks):
        task_id = f'task{i}'
        dot.node(task_id, task_name, fillcolor=color, fontcolor='white', 
                 fontsize='11', penwidth='3')
        
        # Связываем задачи с месяцами
        for month_id in month_ids:
            dot.edge(task_id, month_id, style='dotted', color=color)
    
    # Связи между месяцами
    for i in range(len(months) - 1):
        dot.edge(months[i][0], months[i+1][0], style='solid')
    
    output_path = dot.render('gantt_chart_2025_2026',
                             directory='.',
                             cleanup=True)
    
    print(f"✅ Диаграмма Ганта сохранена: {output_path}")
    
    return output_path


if __name__ == "__main__":
    print("🎨 Генерация диаграмм жизненного цикла...\n")
    print("=" * 60)
    
    # Создаём подробную диаграмму
    create_lifecycle_diagram_2025_2026()
    
    # Создаём диаграмму Ганта
    create_gantt_chart()
    
    print("=" * 60)
    print("\n✅ Все диаграммы сгенерированы!")
    print("📂 Файлы:")
    print("   • lifecycle_diagram_2025_2026.png (подробная)")
    print("   • gantt_chart_2025_2026.png (диаграмма Ганта)")
    print("\n📅 Период: Ноябрь 2025 — Май 2026 (7 месяцев)")
    print("🔄 Модель: Итеративно-инкрементная (5 итераций)")
    print("=" * 60)