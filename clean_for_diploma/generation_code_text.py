import os
import re
import shutil
def clean_python_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        code = f.read()
    code = re.sub(r'
    code = re.sub(r'^\s*""".*?"""', '', code, flags=re.DOTALL | re.MULTILINE)
    code = re.sub(r"^\s*'''.*?'''", '', code, flags=re.DOTALL | re.MULTILINE)
    lines = [line.rstrip() for line in code.split('\n') if line.strip()]
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
SOURCE_DIR = '.'
TARGET_DIR = 'clean_for_diploma'
if os.path.exists(TARGET_DIR):
    shutil.rmtree(TARGET_DIR)
os.makedirs(TARGET_DIR)
for root, _, files in os.walk(SOURCE_DIR):
    for file in files:
        if file.endswith('.py'):
            src = os.path.join(root, file)
            if 'clean_code_for_diploma' in src or 'venv' in src or '__pycache__' in src:
                continue
            dst = os.path.join(TARGET_DIR, file)
            clean_python_file(src, dst)
            print(f'✅ Очищен: {file}')
print(f"\n📂 Готовые файлы сохранены в папке: {TARGET_DIR}")