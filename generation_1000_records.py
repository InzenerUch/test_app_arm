import psycopg2
import random
from datetime import datetime, timedelta

# Параметры подключения (взяты из вашего project_code_context.txt)
DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "dbname": "krd_system",
    "user": "arm_user",
    "password": "ArmUserSecurePass2026!"
}

# Массивы для генерации реалистичных данных
SURNAMES = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Соколов', 'Михайлов', 'Новиков']
NAMES = ['Александр', 'Дмитрий', 'Максим', 'Сергей', 'Андрей', 'Алексей', 'Артём', 'Илья', 'Кирилл', 'Михаил']
PATRONYMICS = ['Александрович', 'Дмитриевич', 'Максимович', 'Сергеевич', 'Андреевич', 'Алексеевич', 'Иванович', 'Петрович']
REGIONS = ['Московская область', 'Свердловская область', 'Новосибирская область', 'Краснодарский край', 'Ростовская область']
TOWNS = ['Москва', 'Екатеринбург', 'Новосибирск', 'Краснодар', 'Ростов-на-Дону']
STREETS = ['ул. Ленина', 'пр. Мира', 'ул. Советская', 'ул. Гагарина', 'пер. Тихий', 'б-р Победы']

def seed_reference_data(cur):
    """Добавляет базовые записи в справочники, если они пустые, чтобы избежать ошибок FK"""
    tables_to_seed = {
        "krd.statuses": [("В розыске",), ("Разыскан",), ("Приостановлен",)],
        "krd.categories": [("Солдаты срочной службы",), ("Контрактники",), ("Офицеры",), ("Курсанты",)],
        "krd.ranks": [("Рядовой",), ("Ефрейтор",), ("Сержант",), ("Лейтенант",), ("Капитан",)],
        "krd.military_units": [("ЦВО",), ("ЮВО",), ("ЗВО",), ("ВДВ",)],
        "krd.garrisons": [("г. Москва",), ("г. Екатеринбург",), ("г. Краснодар",)],
        "krd.positions": [("Стрелок",), ("Водитель",), ("Командир отделения",), ("Начальник штаба",)]
    }
    
    for table, values in tables_to_seed.items():
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        if cur.fetchone()[0] == 0:
            # Используем ON CONFLICT DO NOTHING на случай, если имя уже есть (для таблиц с UNIQUE)
            # Но для простоты здесь используем обычный INSERT, так как мы проверили COUNT(*) == 0
            cols = ", ".join(["name"] * len(values[0])) # Обычно это просто 'name'
            placeholders = ", ".join(["%s"] * len(values[0]))
            query = f"INSERT INTO {table} (name) VALUES ({placeholders})"
            for val in values:
                cur.execute(query, val)
    print("✅ Справочные данные проверены и при необходимости заполнены.")

def get_valid_ids(cur):
    """Получает списки реальных ID из справочников, чтобы не нарушать FK"""
    ids = {}
    for table in ['statuses', 'categories', 'ranks', 'military_units', 'garrisons', 'positions']:
        cur.execute(f"SELECT id FROM krd.{table}")
        ids[table] = [row[0] for row in cur.fetchall()]
        
        # Если вдруг таблица всё равно пуста, добавим заглушку, чтобы random.choice не упал
        if not ids[table]:
            cur.execute(f"INSERT INTO krd.{table} (name) VALUES ('Не указано') RETURNING id")
            ids[table] = [cur.fetchone()[0]]
            
    return ids

def generate_krd_records(num_records=1000):
    print("🔌 Подключение к базе данных...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    try:
        print("⚙️ Подготовка справочников...")
        seed_reference_data(cur)
        valid_ids = get_valid_ids(cur)
        conn.commit()
        
        print(f"🚀 Начало генерации {num_records} записей КРД...")
        
        for i in range(1, num_records + 1):
            # 1. Создаем основную запись КРД
            cur.execute("""
                INSERT INTO krd.krd (status_id, is_deleted, is_locked) 
                VALUES (%s, %s, %s) RETURNING id
            """, (random.choice(valid_ids['statuses']), False, random.random() > 0.9))
            krd_id = cur.fetchone()[0]
            
            # 2. Социально-демографические данные (ИСПОЛЬЗУЕМ РЕАЛЬНЫЕ ID!)
            birth_date = datetime.now() - timedelta(days=random.randint(5000, 15000))
            cur.execute("""
                INSERT INTO krd.social_data (
                    krd_id, surname, name, patronymic, birth_date, 
                    birth_place_town, birth_place_region, personal_number, rank_id, category_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                krd_id,
                random.choice(SURNAMES),
                random.choice(NAMES),
                random.choice(PATRONYMICS),
                birth_date,
                random.choice(TOWNS),
                random.choice(REGIONS),
                f"П{random.randint(100000, 999999)}",
                random.choice(valid_ids['ranks']),       # <-- Реальный ID
                random.choice(valid_ids['categories'])   # <-- Реальный ID
            ))
            
            # 3. Адрес проживания
            cur.execute("""
                INSERT INTO krd.addresses (
                    krd_id, region, district, town, street, house, apartment, postal_index, is_deleted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                krd_id,
                random.choice(REGIONS),
                'Центральный район',
                random.choice(TOWNS),
                random.choice(STREETS),
                str(random.randint(1, 150)),
                str(random.randint(1, 200)),
                f"{random.randint(100000, 999999)}",
                False
            ))
            
            # 4. Место службы
            unit_num = f"в/ч {random.randint(10000, 99999)}"
            cur.execute("""
                INSERT INTO krd.service_places (
                    krd_id, place_name, military_unit_id, garrison_id, position_id, military_unit_number, is_deleted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                krd_id,
                unit_num,
                random.choice(valid_ids['military_units']), # <-- Реальный ID
                random.choice(valid_ids['garrisons']),      # <-- Реальный ID
                random.choice(valid_ids['positions']),      # <-- Реальный ID
                unit_num,
                False
            ))
            service_place_id = cur.fetchone()[0]
            
            # 5. Обновляем КРД ссылкой на место службы
            cur.execute("""
                UPDATE krd.krd SET last_service_place_id = %s WHERE id = %s
            """, (service_place_id, krd_id))
            
            # Коммитим каждые 100 записей для экономии памяти и отображения прогресса
            if i % 100 == 0:
                conn.commit()
                print(f"   ✅ Создано {i} из {num_records} записей...")
                
        # Финальный коммит
        conn.commit()
        print(f"\n🎉 УСПЕХ! Успешно создано {num_records} полных записей КРД со всеми связанными данными.")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ОШИБКА: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    generate_krd_records(1000)