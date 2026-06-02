import re

# Имя вашего файла с "грязным" кодом (сохраните docx как txt)
input_filename = 'code_raw.txt'
# Имя файла для результата
output_filename = 'code_clean.txt'

try:
    with open(input_filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Регулярное выражение для удаления заголовков файлов
    # Ищет блоки вида: ==================\n📄 FILE: ...\n==================
    pattern = r'={10,}\n📄 FILE: .*?\n={10,}\n'
    
    # Удаляем заголовки
    clean_content = re.sub(pattern, '', content)

    # Разбиваем на строки и убираем пустые
    lines = [line for line in clean_content.split('\n') if line.strip()]

    # Сохраняем результат
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ Готово! Файл сохранен как '{output_filename}'")
    print(f"📊 Общее количество строк кода: {len(lines)}")

except FileNotFoundError:
    print(f"❌ Ошибка: Файл '{input_filename}' не найден.")
    print("Пожалуйста, сохраните содержимое вашего Word-файла как текстовый файл (.txt)")