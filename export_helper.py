"""
Модуль для выгрузки данных КРД в Excel
С поддержкой экспорта фотографий
"""

from PyQt6.QtSql import QSqlQuery
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell
from openpyxl.drawing.image import Image as OpenPyXLImage
from datetime import datetime
import tempfile
import os
import io
from PIL import Image as PILImage


class KrdExcelExporter:
    """Экспорт данных КРД в Excel"""
    
    def __init__(self, db_connection, krd_id):
        self.db = db_connection
        self.krd_id = krd_id
        self.wb = Workbook()
        
        # Стили для форматирования
        self.header_font = Font(bold=True, size=11, color="FFFFFF")
        self.header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        self.section_font = Font(bold=True, size=12, color="000000")
        self.section_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        self.cell_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        self.header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Границы
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Временные файлы для изображений
        self.temp_image_files = []
        
        # Размеры для фотографий (в пикселях)
        self.photo_width_px = 200
        self.photo_height_px = 270
    
    def _cleanup_temp_files(self):
        """Удаление временных файлов изображений"""
        for temp_file in self.temp_image_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"✓ Удалён временный файл: {temp_file}")
            except Exception as e:
                print(f"✗ Ошибка удаления временного файла {temp_file}: {e}")
        self.temp_image_files = []
    
    def _load_photo_from_db(self, field_name):
        """
        Загрузка фотографии из базы данных
        Returns: bytes или None
        """
        try:
            query = QSqlQuery(self.db)
            query.prepare(f"""
                SELECT {field_name} 
                FROM krd.social_data 
                WHERE krd_id = ?
                ORDER BY id DESC 
                LIMIT 1
            """)
            query.addBindValue(self.krd_id)
            
            if not query.exec():
                print(f"✗ Ошибка запроса для {field_name}: {query.lastError().text()}")
                return None
            
            if query.next():
                photo_data = query.value(0)
                print(f"📷 {field_name}: тип={type(photo_data)}, размер={len(photo_data) if photo_data else 0} байт")
                
                if photo_data:
                    if hasattr(photo_data, 'data'):  # QByteArray
                        return bytes(photo_data.data())
                    elif isinstance(photo_data, bytes):
                        return photo_data
                    elif isinstance(photo_data, bytearray):
                        return bytes(photo_data)
                    elif isinstance(photo_data, memoryview):
                        return bytes(photo_data)
                    else:
                        print(f"⚠️ Неизвестный тип данных фото: {type(photo_data)}")
                        return bytes(photo_data)
                else:
                    print(f"⚠️ Фото {field_name} отсутствует в БД (NULL)")
                    return None
            else:
                print(f"⚠️ Запись КРД-{self.krd_id} не найдена в social_data")
                return None
                
        except Exception as e:
            print(f"✗ Ошибка загрузки фото {field_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_temp_image_file(self, photo_bytes, suffix='.jpg', target_width=None, target_height=None):
        """
        Создание временного файла для изображения с масштабированием
        Returns: путь к файлу или None
        """
        if not photo_bytes:
            print("⚠️ Пустые байты изображения")
            return None
        
        try:
            print(f"📷 Создание временного файла из {len(photo_bytes)} байт...")
            
            # Открываем изображение через PIL для проверки и масштабирования
            img = PILImage.open(io.BytesIO(photo_bytes))
            print(f"✓ Изображение открыто: формат={img.format}, размер={img.size}, режим={img.mode}")
            
            # === ИСПРАВЛЕНО: Конвертируем RGBA в RGB для JPEG ===
            if img.mode == 'RGBA':
                # Создаём белый фон для прозрачных областей
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                # Накладываем изображение на фон
                background.paste(img, mask=img.split()[3])  # 3 - альфа-канал
                img = background
                print(f"✓ Конвертировано RGBA → RGB с белым фоном")
            elif img.mode != 'RGB':
                # Другие режимы (P, LA и т.д.)
                img = img.convert('RGB')
                print(f"✓ Конвертировано {img.mode} → RGB")
            
            # Масштабируем если указаны размеры
            if target_width and target_height:
                img = img.resize((target_width, target_height), PILImage.Resampling.LANCZOS)
                print(f"✓ Изображение масштабировано до {target_width}x{target_height}")
            
            # Создаём временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            img.save(temp_file.name, quality=95)
            temp_file.close()
            
            self.temp_image_files.append(temp_file.name)
            print(f"✓ Временный файл создан: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f"✗ Ошибка создания временного файла изображения: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_image_to_cell(self, ws, image_path, row, col, row_height=100, col_width=30):
        """
        Добавление изображения в ячейку Excel с правильным размером
        """
        if not image_path or not os.path.exists(image_path):
            print(f"✗ Изображение не найдено: {image_path}")
            return False
        
        try:
            print(f"📷 Добавление изображения {image_path} в ячейку {get_column_letter(col)}{row}")
            
            # Создаём объект изображения openpyxl
            img = OpenPyXLImage(image_path)
            
            # Получаем реальные размеры изображения
            original_width, original_height = img.width, img.height
            
            # Вычисляем пропорции для масштабирования
            max_width = col_width * 7  # Примерная ширина в пикселях
            max_height = row_height * 1.5  # Примерная высота в пикселях
            
            # Масштабируем с сохранением пропорций
            ratio = min(max_width / original_width, max_height / original_height)
            img.width = original_width * ratio
            img.height = original_height * ratio
            
            # Якорь ячейки (начальная позиция)
            anchor_cell = f'{get_column_letter(col)}{row}'
            
            # Добавляем изображение на лист
            ws.add_image(img, anchor_cell)
            
            # Настраиваем размеры ячейки для изображения
            ws.row_dimensions[row].height = row_height
            ws.column_dimensions[get_column_letter(col)].width = col_width
            
            print(f"✓ Изображение добавлено в {anchor_cell} (размер: {img.width:.0f}x{img.height:.0f})")
            return True
            
        except Exception as e:
            print(f"✗ Ошибка добавления изображения: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _fill_social_data_section(self, ws, data, photos, start_row=1):
        """Заполнение раздела социально-демографических данных с фотографиями"""
        row = start_row
        
        # Заголовок раздела
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "СОЦИАЛЬНО-ДЕМОГРАФИЧЕСКИЕ ДАННЫЕ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        # Заголовки колонок (33 колонки)
        headers = [
            "№ КРД", "табельный номер", "личный номер", "категория военнослужащего",
            "воинское звание", "фамилия", "имя", "отчество", "дата рождения",
            "населенный пункт места рождения", "административный район места рождения",
            "субъект (регион) места рождения", "страна места рождения",
            "Наименование комиссариата", "Дата призыва", "Наименование ПОВСК",
            "Дата отбора", "Образование", "Сведения о судимости",
            "Аккаунт в социальных сетях", "Номер банковской карты",
            "Серия паспорта", "Номер паспорта", "Дата выдачи паспорта",
            "Кем выдан паспорт", "Серия военного билета", "Номер военного билета",
            "Дата выдачи военного билета", "Кем выдан военный билет",
            "Особенности внешности", "Личные приметы", "Контакты в/с",
            "Сведения о близких родственниках"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        # Данные
        values = [
            data.get('krd_number', ''),
            data.get('tab_number', ''),
            data.get('personal_number', ''),
            data.get('category_name', ''),
            data.get('rank_name', ''),
            data.get('surname', ''),
            data.get('name', ''),
            data.get('patronymic', ''),
            self._format_date(data.get('birth_date')),
            data.get('birth_place_town', ''),
            data.get('birth_place_district', ''),
            data.get('birth_place_region', ''),
            data.get('birth_place_country', ''),
            data.get('drafted_by_commissariat', ''),
            self._format_date(data.get('draft_date')),
            data.get('povsk', ''),
            self._format_date(data.get('selection_date')),
            data.get('education', ''),
            data.get('criminal_record', ''),
            data.get('social_media_account', ''),
            data.get('bank_card_number', ''),
            data.get('passport_series', ''),
            data.get('passport_number', ''),
            self._format_date(data.get('passport_issue_date')),
            data.get('passport_issued_by', ''),
            data.get('military_id_series', ''),
            data.get('military_id_number', ''),
            self._format_date(data.get('military_id_issue_date')),
            data.get('military_id_issued_by', ''),
            data.get('appearance_features', ''),
            data.get('personal_marks', ''),
            data.get('military_contacts', ''),
            data.get('relatives_info', '')
        ]
        
        for col, value in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.alignment = self.cell_alignment
            cell.border = self.thin_border
        
        row += 2  # Пропускаем строку для данных
        
        # === СЕКЦИЯ С ФОТОГРАФИЯМИ ===
        # Заголовок для фотографий
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "ФОТОГРАФИИ ВОЕННОСЛУЖАЩЕГО"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        # Заголовки для 4 фотографий (каждая занимает 8 колонок)
        photo_labels = [
            ('civilian', 'Фото в гражданской одежде'),
            ('military_headgear', 'Фото в военной форме\nс головным убором'),
            ('military_no_headgear', 'Фото в военной форме\nбез головного убора'),
            ('distinctive_marks', 'Фото отличительных примет')
        ]
        
        # Создаём заголовки для фото
        for i, (photo_key, label) in enumerate(photo_labels):
            start_col = i * 8 + 1
            end_col = start_col + 7
            ws.merge_cells(f'{get_column_letter(start_col)}{row}:{get_column_letter(end_col)}{row}')
            cell = ws[f'{get_column_letter(start_col)}{row}']
            cell.value = label
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = self.thin_border
        
        row += 1
        
        # === ВСТАВЛЯЕМ ФОТОГРАФИИ ===
        photo_row = row
        for i, (photo_key, label) in enumerate(photo_labels):
            start_col = i * 8 + 1
            
            if photos.get(photo_key):
                # Вставляем фото
                self._add_image_to_cell(
                    ws, 
                    photos[photo_key], 
                    row=photo_row, 
                    col=start_col,
                    row_height=80,   # Высота строки для фото
                    col_width=12     # Ширина колонки для фото
                )
            else:
                # Если фото нет, пишем текст
                end_col = start_col + 7
                ws.merge_cells(f'{get_column_letter(start_col)}{photo_row}:{get_column_letter(end_col)}{photo_row}')
                cell = ws[f'{get_column_letter(start_col)}{photo_row}']
                cell.value = "Фото отсутствует"
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = self.thin_border
        
        # Устанавливаем высоту строк для фотографий
        ws.row_dimensions[photo_row].height = 80
        
        row = photo_row + 2  # Пропускаем 2 строки после фото
        
        return row
    
    def export_to_excel(self, file_path):
        """Экспорт всех данных КРД в Excel файл"""
        try:
            print(f"\n{'='*60}")
            print(f"📊 НАЧАЛО ЭКСПОРТА КРД-{self.krd_id}")
            print(f"{'='*60}")
            
            # Удаляем стандартный лист
            self.wb.remove(self.wb.active)
            
            # Создаём основной лист с данными
            ws = self.wb.create_sheet("Данные КРД")
            
            # Загружаем все данные
            social_data = self._load_social_data()
            addresses = self._load_addresses()
            incoming_orders = self._load_incoming_orders()
            service_places = self._load_service_places()
            soch_episodes = self._load_soch_episodes()
            outgoing_requests = self._load_outgoing_requests()
            
            # Загружаем фотографии
            print(f"\n📷 ЗАГРУЗКА ФОТОГРАФИЙ...")
            photos = self._load_photos()
            
            # Заполняем лист данными
            row = self._fill_social_data_section(ws, social_data, photos, start_row=1)
            row = self._fill_addresses_section(ws, addresses, start_row=row)
            row = self._fill_incoming_orders_section(ws, incoming_orders, start_row=row)
            row = self._fill_service_places_section(ws, service_places, start_row=row)
            row = self._fill_soch_episodes_section(ws, soch_episodes, start_row=row)
            row = self._fill_outgoing_requests_section(ws, outgoing_requests, start_row=row)
            
            # Настройка ширины колонок
            self._adjust_column_widths(ws)
            
            # === ВАЖНО: Сохраняем файл ПЕРЕД очисткой временных файлов ===
            print(f"\n💾 СОХРАНЕНИЕ ФАЙЛА: {file_path}")
            self.wb.save(file_path)
            print(f"✓ Файл сохранён: {file_path}")
            
            # === ТОЛЬКО ПОСЛЕ СОХРАНЕНИЯ очищаем временные файлы ===
            print(f"\n🧹 ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ...")
            self._cleanup_temp_files()
            
            print(f"\n{'='*60}")
            print(f"✅ ЭКСПОРТ ЗАВЕРШЁН УСПЕШНО")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"✗ ОШИБКА ЭКСПОРТА: {e}")
            print(f"{'='*60}\n")
            import traceback
            traceback.print_exc()
            # Даже при ошибке очищаем временные файлы
            self._cleanup_temp_files()
            raise
    
    def export_to_single_sheet(self, ws):
        """Экспорт данных одной КРД на один лист"""
        try:
            row = 1
            
            # Заголовок
            ws.merge_cells(f'A1:AC1')
            cell = ws[f'A1']
            cell.value = f"КАРТОЧКА РОЗЫСКА №{self.krd_id}"
            cell.font = Font(bold=True, size=16)
            cell.alignment = self.header_alignment
            row += 1
            
            # Загружаем все данные
            social_data = self._load_social_data()
            addresses = self._load_addresses()
            incoming_orders = self._load_incoming_orders()
            service_places = self._load_service_places()
            soch_episodes = self._load_soch_episodes()
            outgoing_requests = self._load_outgoing_requests()
            
            # Загружаем фотографии
            photos = self._load_photos()
            
            # Заполняем лист данными
            row = self._fill_social_data_section(ws, social_data, photos, start_row=row)
            row = self._fill_addresses_section(ws, addresses, start_row=row)
            row = self._fill_incoming_orders_section(ws, incoming_orders, start_row=row)
            row = self._fill_service_places_section(ws, service_places, start_row=row)
            row = self._fill_soch_episodes_section(ws, soch_episodes, start_row=row)
            row = self._fill_outgoing_requests_section(ws, outgoing_requests, start_row=row)
            
            # Настройка ширины колонок
            self._adjust_column_widths(ws)
            
            return True
            
        except Exception as e:
            print(f"Ошибка экспорта на лист: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _load_photos(self):
        """Загрузка всех фотографий из базы данных с масштабированием"""
        photos = {
            'civilian': None,
            'military_headgear': None,
            'military_no_headgear': None,
            'distinctive_marks': None
        }
        
        # Загружаем каждое фото
        photo_fields = {
            'civilian': 'photo_civilian',
            'military_headgear': 'photo_military_headgear',
            'military_no_headgear': 'photo_military_no_headgear',
            'distinctive_marks': 'photo_distinctive_marks'
        }
        
        print(f"\n📷 Загрузка фотографий для КРД-{self.krd_id}:")
        for photo_key, field_name in photo_fields.items():
            print(f"  • {photo_key} ({field_name})...")
            photo_bytes = self._load_photo_from_db(field_name)
            if photo_bytes:
                # Масштабируем изображение под размер ячейки
                temp_file = self._create_temp_image_file(
                    photo_bytes, 
                    target_width=self.photo_width_px,
                    target_height=self.photo_height_px
                )
                if temp_file:
                    photos[photo_key] = temp_file
                    print(f"    ✓ Загружено: {temp_file} ({len(photo_bytes)} байт)")
                else:
                    print(f"    ✗ Не удалось создать временный файл")
            else:
                print(f"    ⚠️ Фото отсутствует в БД")
        
        return photos
    
    def _load_social_data(self):
        """Загрузка социально-демографических данных"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                k.id as krd_id,
                k.krd_number,
                s.tab_number,
                s.personal_number,
                c.name as category_name,
                r.name as rank_name,
                s.surname,
                s.name,
                s.patronymic,
                s.birth_date,
                s.birth_place_town,
                s.birth_place_district,
                s.birth_place_region,
                s.birth_place_country,
                s.drafted_by_commissariat,
                s.draft_date,
                s.povsk,
                s.selection_date,
                s.education,
                s.criminal_record,
                s.social_media_account,
                s.bank_card_number,
                s.passport_series,
                s.passport_number,
                s.passport_issue_date,
                s.passport_issued_by,
                s.military_id_series,
                s.military_id_number,
                s.military_id_issue_date,
                s.military_id_issued_by,
                s.appearance_features,
                s.personal_marks,
                s.federal_search_info,
                s.military_contacts,
                s.relatives_info
            FROM krd.social_data s
            LEFT JOIN krd.krd ON s.krd_id = krd.id
            LEFT JOIN krd.categories c ON s.category_id = c.id
            LEFT JOIN krd.ranks r ON s.rank_id = r.id
            WHERE s.krd_id = ?
            ORDER BY s.id DESC
            LIMIT 1
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        if query.next():
            return {
                'krd_number': query.value('krd_number') or '',
                'tab_number': query.value('tab_number') or '',
                'personal_number': query.value('personal_number') or '',
                'category_name': query.value('category_name') or '',
                'rank_name': query.value('rank_name') or '',
                'surname': query.value('surname') or '',
                'name': query.value('name') or '',
                'patronymic': query.value('patronymic') or '',
                'birth_date': query.value('birth_date'),
                'birth_place_town': query.value('birth_place_town') or '',
                'birth_place_district': query.value('birth_place_district') or '',
                'birth_place_region': query.value('birth_place_region') or '',
                'birth_place_country': query.value('birth_place_country') or '',
                'drafted_by_commissariat': query.value('drafted_by_commissariat') or '',
                'draft_date': query.value('draft_date'),
                'povsk': query.value('povsk') or '',
                'selection_date': query.value('selection_date'),
                'education': query.value('education') or '',
                'criminal_record': query.value('criminal_record') or '',
                'social_media_account': query.value('social_media_account') or '',
                'bank_card_number': query.value('bank_card_number') or '',
                'passport_series': query.value('passport_series') or '',
                'passport_number': query.value('passport_number') or '',
                'passport_issue_date': query.value('passport_issue_date'),
                'passport_issued_by': query.value('passport_issued_by') or '',
                'military_id_series': query.value('military_id_series') or '',
                'military_id_number': query.value('military_id_number') or '',
                'military_id_issue_date': query.value('military_id_issue_date'),
                'military_id_issued_by': query.value('military_id_issued_by') or '',
                'appearance_features': query.value('appearance_features') or '',
                'personal_marks': query.value('personal_marks') or '',
                'federal_search_info': query.value('federal_search_info') or '',
                'military_contacts': query.value('military_contacts') or '',
                'relatives_info': query.value('relatives_info') or ''
            }
        return {}
    
    def _load_addresses(self):
        """Загрузка адресов проживания"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                region, district, town, street, house, building, letter,
                apartment, room, check_date, check_result
            FROM krd.addresses
            WHERE krd_id = ?
            ORDER BY id DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        addresses = []
        while query.next():
            addresses.append({
                'region': query.value('region') or '',
                'district': query.value('district') or '',
                'town': query.value('town') or '',
                'street': query.value('street') or '',
                'house': query.value('house') or '',
                'building': query.value('building') or '',
                'letter': query.value('letter') or '',
                'apartment': query.value('apartment') or '',
                'room': query.value('room') or '',
                'check_date': query.value('check_date'),
                'check_result': query.value('check_result') or ''
            })
        return addresses
    
    def _load_incoming_orders(self):
        """Загрузка входящих поручений"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                i.initiator_full_name, i.order_date, i.order_number,
                i.receipt_date, i.receipt_number, i.postal_index,
                i.postal_region, i.postal_district, i.postal_town,
                i.postal_street, i.postal_house, i.postal_building,
                i.postal_letter, i.postal_apartment, i.postal_room,
                i.initiator_contacts, i.our_response_date,
                i.our_response_number, m.name as military_unit_name
            FROM krd.incoming_orders i
            LEFT JOIN krd.military_units m ON i.military_unit_id = m.id
            WHERE i.krd_id = ?
            ORDER BY i.receipt_date DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        orders = []
        while query.next():
            orders.append({
                'initiator_full_name': query.value('initiator_full_name') or '',
                'order_date': query.value('order_date'),
                'order_number': query.value('order_number') or '',
                'receipt_date': query.value('receipt_date'),
                'receipt_number': query.value('receipt_number') or '',
                'postal_index': query.value('postal_index') or '',
                'postal_region': query.value('postal_region') or '',
                'postal_district': query.value('postal_district') or '',
                'postal_town': query.value('postal_town') or '',
                'postal_street': query.value('postal_street') or '',
                'postal_house': query.value('postal_house') or '',
                'postal_building': query.value('postal_building') or '',
                'postal_letter': query.value('postal_letter') or '',
                'postal_apartment': query.value('postal_apartment') or '',
                'postal_room': query.value('postal_room') or '',
                'initiator_contacts': query.value('initiator_contacts') or '',
                'our_response_date': query.value('our_response_date'),
                'our_response_number': query.value('our_response_number') or '',
                'military_unit_name': query.value('military_unit_name') or ''
            })
        return orders
    
    def _load_service_places(self):
        """Загрузка мест службы"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                s.place_name, m.name as military_unit_name,
                g.name as garrison_name, p.name as position_name,
                s.commanders, s.postal_index, s.postal_region,
                s.postal_district, s.postal_town, s.postal_street,
                s.postal_house, s.postal_building, s.postal_letter,
                s.postal_apartment, s.postal_room, s.place_contacts
            FROM krd.service_places s
            LEFT JOIN krd.military_units m ON s.military_unit_id = m.id
            LEFT JOIN krd.garrisons g ON s.garrison_id = g.id
            LEFT JOIN krd.positions p ON s.position_id = p.id
            WHERE s.krd_id = ?
            ORDER BY s.id DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        places = []
        while query.next():
            places.append({
                'place_name': query.value('place_name') or '',
                'military_unit_name': query.value('military_unit_name') or '',
                'garrison_name': query.value('garrison_name') or '',
                'position_name': query.value('position_name') or '',
                'commanders': query.value('commanders') or '',
                'postal_index': query.value('postal_index') or '',
                'postal_region': query.value('postal_region') or '',
                'postal_district': query.value('postal_district') or '',
                'postal_town': query.value('postal_town') or '',
                'postal_street': query.value('postal_street') or '',
                'postal_house': query.value('postal_house') or '',
                'postal_building': query.value('postal_building') or '',
                'postal_letter': query.value('postal_letter') or '',
                'postal_apartment': query.value('postal_apartment') or '',
                'postal_room': query.value('postal_room') or '',
                'place_contacts': query.value('place_contacts') or ''
            })
        return places
    
    def _load_soch_episodes(self):
        """Загрузка эпизодов СОЧ"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                soch_date, soch_location, order_date_number, witnesses,
                reasons, weapon_info, clothing, movement_options, other_info,
                duty_officer_commissariat, duty_officer_omvd, investigation_info,
                prosecution_info, criminal_case_info, search_date, found_by,
                search_circumstances, notification_recipient, notification_date,
                notification_number
            FROM krd.soch_episodes
            WHERE krd_id = ?
            ORDER BY soch_date DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        episodes = []
        while query.next():
            episodes.append({
                'soch_date': query.value('soch_date'),
                'soch_location': query.value('soch_location') or '',
                'order_date_number': query.value('order_date_number') or '',
                'witnesses': query.value('witnesses') or '',
                'reasons': query.value('reasons') or '',
                'weapon_info': query.value('weapon_info') or '',
                'clothing': query.value('clothing') or '',
                'movement_options': query.value('movement_options') or '',
                'other_info': query.value('other_info') or '',
                'duty_officer_commissariat': query.value('duty_officer_commissariat') or '',
                'duty_officer_omvd': query.value('duty_officer_omvd') or '',
                'investigation_info': query.value('investigation_info') or '',
                'prosecution_info': query.value('prosecution_info') or '',
                'criminal_case_info': query.value('criminal_case_info') or '',
                'search_date': query.value('search_date'),
                'found_by': query.value('found_by') or '',
                'search_circumstances': query.value('search_circumstances') or '',
                'notification_recipient': query.value('notification_recipient') or '',
                'notification_date': query.value('notification_date'),
                'notification_number': query.value('notification_number') or ''
            })
        return episodes
    
    def _load_outgoing_requests(self):
        """Загрузка исходящих запросов"""
        query = QSqlQuery(self.db)
        query.prepare("""
            SELECT 
                r.recipient_name, r.issue_date, r.issue_number,
                r.postal_index, r.postal_region, r.postal_district,
                r.postal_town, r.postal_street, r.postal_house,
                r.postal_building, r.postal_letter, r.postal_apartment,
                r.postal_room, r.recipient_contacts, r.request_text,
                r.signed_by_position, m.name as military_unit_name,
                t.name as request_type_name
            FROM krd.outgoing_requests r
            LEFT JOIN krd.military_units m ON r.military_unit_id = m.id
            LEFT JOIN krd.request_types t ON r.request_type_id = t.id
            WHERE r.krd_id = ?
            ORDER BY r.issue_date DESC
        """)
        query.addBindValue(self.krd_id)
        query.exec()
        
        requests = []
        while query.next():
            requests.append({
                'recipient_name': query.value('recipient_name') or '',
                'issue_date': query.value('issue_date'),
                'issue_number': query.value('issue_number') or '',
                'postal_index': query.value('postal_index') or '',
                'postal_region': query.value('postal_region') or '',
                'postal_district': query.value('postal_district') or '',
                'postal_town': query.value('postal_town') or '',
                'postal_street': query.value('postal_street') or '',
                'postal_house': query.value('postal_house') or '',
                'postal_building': query.value('postal_building') or '',
                'postal_letter': query.value('postal_letter') or '',
                'postal_apartment': query.value('postal_apartment') or '',
                'postal_room': query.value('postal_room') or '',
                'recipient_contacts': query.value('recipient_contacts') or '',
                'request_text': query.value('request_text') or '',
                'signed_by_position': query.value('signed_by_position') or '',
                'military_unit_name': query.value('military_unit_name') or '',
                'request_type_name': query.value('request_type_name') or ''
            })
        return requests
    
    def _format_date(self, date_value):
        """Форматирование даты"""
        if date_value:
            try:
                return date_value.toString("dd.MM.yyyy")
            except:
                return str(date_value)
        return ""
    
    
    def _fill_addresses_section(self, ws, addresses, start_row=1):
        """Заполнение раздела адресов проживания"""
        row = start_row
        
        # Заголовок раздела
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "АДРЕСА ПРОЖИВАНИЯ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        # Заголовки колонок
        headers = [
            "Субъект РФ", "Административный район", "Населенный пункт",
            "Улица", "Дом", "Корпус", "Литер", "Квартира", "Комната",
            "Дата адресной проверки", "Результат адресной проверки"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        # Данные
        for addr in addresses:
            values = [
                addr.get('region', ''),
                addr.get('district', ''),
                addr.get('town', ''),
                addr.get('street', ''),
                addr.get('house', ''),
                addr.get('building', ''),
                addr.get('letter', ''),
                addr.get('apartment', ''),
                addr.get('room', ''),
                self._format_date(addr.get('check_date')),
                addr.get('check_result', '')
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            
            row += 1
        
        return row
    
    def _fill_incoming_orders_section(self, ws, orders, start_row=1):
        """Заполнение раздела входящих поручений"""
        row = start_row
        
        # Заголовок раздела
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "ВХОДЯЩИЕ ПОРУЧЕНИЯ НА РОЗЫСК"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        # Заголовки колонок
        headers = [
            "Инициатор розыска", "Полное наименование инициатора розыска",
            "Военное управление инициатора розыска", "Исходящая дата поручения",
            "Исходящий номер поручения", "Дата поступления в ВК",
            "Входящий номер в ВК", "Индекс", "Субъект РФ",
            "Административный район", "Населенный пункт", "Улица",
            "Дом", "Корпус", "Литер", "Квартира", "Комната",
            "Контакты источника", "Дата ответа ВК", "Исходящий номер ответа ВК"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        # Данные
        for order in orders:
            values = [
                order.get('initiator_full_name', ''),
                order.get('initiator_full_name', ''),
                order.get('military_unit_name', ''),
                self._format_date(order.get('order_date')),
                order.get('order_number', ''),
                self._format_date(order.get('receipt_date')),
                order.get('receipt_number', ''),
                order.get('postal_index', ''),
                order.get('postal_region', ''),
                order.get('postal_district', ''),
                order.get('postal_town', ''),
                order.get('postal_street', ''),
                order.get('postal_house', ''),
                order.get('postal_building', ''),
                order.get('postal_letter', ''),
                order.get('postal_apartment', ''),
                order.get('postal_room', ''),
                order.get('initiator_contacts', ''),
                self._format_date(order.get('our_response_date')),
                order.get('our_response_number', '')
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            
            row += 1
        
        return row
    
    def _fill_service_places_section(self, ws, places, start_row=1):
        """Заполнение раздела мест службы"""
        row = start_row
        
        # Заголовок раздела
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "МЕСТА СЛУЖБЫ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        # Заголовки колонок
        headers = [
            "Наименование места службы", "Военное управление места службы",
            "Гарнизон места службы", "Воинская должность",
            "Командиры (начальники) (воинское звание, ФИО, контакты)",
            "Индекс", "Субъект РФ", "Административный район",
            "Населенный пункт", "Улица", "Дом", "Корпус", "Литер",
            "Квартира", "Комната", "Контакты места службы"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        # Данные
        for place in places:
            values = [
                place.get('place_name', ''),
                place.get('military_unit_name', ''),
                place.get('garrison_name', ''),
                place.get('position_name', ''),
                place.get('commanders', ''),
                place.get('postal_index', ''),
                place.get('postal_region', ''),
                place.get('postal_district', ''),
                place.get('postal_town', ''),
                place.get('postal_street', ''),
                place.get('postal_house', ''),
                place.get('postal_building', ''),
                place.get('postal_letter', ''),
                place.get('postal_apartment', ''),
                place.get('postal_room', ''),
                place.get('place_contacts', '')
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            
            row += 1
        
        return row
    
    def _fill_soch_episodes_section(self, ws, episodes, start_row=1):
        """Заполнение раздела сведений о СОЧ"""
        row = start_row
        
        # Заголовок раздела
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "СВЕДЕНИЯ О СОЧ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        # Заголовки колонок
        headers = [
            "Дата СОЧ", "Место СОЧ", "Дата и номер приказа о СОЧ",
            "Очевидцы СОЧ", "Вероятные причины СОЧ",
            "Сведения о наличии оружия", "Во что был одет",
            "Варианты движения", "Другая значимая информация",
            "Контакт дежурного по ВК", "Контакт дежурного по ОМВД",
            "Сведения о проверке", "Сведения о прокуратуре",
            "Сведения об уголовном деле", "Дата розыска",
            "Обстоятельства розыска", "Кем разыскан",
            "Дата уведомления", "Номер уведомления", "Адресат уведомления"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        # Данные
        for episode in episodes:
            values = [
                self._format_date(episode.get('soch_date')),
                episode.get('soch_location', ''),
                episode.get('order_date_number', ''),
                episode.get('witnesses', ''),
                episode.get('reasons', ''),
                episode.get('weapon_info', ''),
                episode.get('clothing', ''),
                episode.get('movement_options', ''),
                episode.get('other_info', ''),
                episode.get('duty_officer_commissariat', ''),
                episode.get('duty_officer_omvd', ''),
                episode.get('investigation_info', ''),
                episode.get('prosecution_info', ''),
                episode.get('criminal_case_info', ''),
                self._format_date(episode.get('search_date')),
                episode.get('search_circumstances', ''),
                episode.get('found_by', ''),
                self._format_date(episode.get('notification_date')),
                episode.get('notification_number', ''),
                episode.get('notification_recipient', '')
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            
            row += 1
        
        return row
    
    def _fill_outgoing_requests_section(self, ws, requests, start_row=1):
        """Заполнение раздела исходящих запросов"""
        row = start_row
        
        # Заголовок раздела
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "ИСХОДЯЩИЕ ЗАПРОСЫ И ПОРУЧЕНИЯ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        # Заголовки колонок
        headers = [
            "Наименование запроса", "Наименование адресата",
            "Военное управление адресата", "Исходящая дата",
            "Исходящий номер", "Индекс", "Субъект РФ",
            "Административный район", "Населенный пункт",
            "Улица", "Дом", "Корпус", "Литер", "Квартира",
            "Комната", "Контакты"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        # Данные
        for req in requests:
            values = [
                req.get('request_type_name', ''),
                req.get('recipient_name', ''),
                req.get('military_unit_name', ''),
                self._format_date(req.get('issue_date')),
                req.get('issue_number', ''),
                req.get('postal_index', ''),
                req.get('postal_region', ''),
                req.get('postal_district', ''),
                req.get('postal_town', ''),
                req.get('postal_street', ''),
                req.get('postal_house', ''),
                req.get('postal_building', ''),
                req.get('postal_letter', ''),
                req.get('postal_apartment', ''),
                req.get('postal_room', ''),
                req.get('recipient_contacts', '')
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            
            row += 1
        
        return row
    
    def _adjust_column_widths(self, ws):
        """Настройка ширины колонок"""
        for col_num in range(1, 30):
            max_length = 0
            column_letter = get_column_letter(col_num)
            
            for row_num in range(1, ws.max_row + 1):
                cell = ws.cell(row=row_num, column=col_num)
                
                if not isinstance(cell, MergedCell):
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width