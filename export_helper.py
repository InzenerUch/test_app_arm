"""
Модуль для выгрузки данных КРД в Excel
С поддержкой экспорта фотографий и конфигурации отчетов
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
from PyQt6.QtCore import QByteArray


class KrdExcelExporter:
    """Экспорт данных КРД в Excel с поддержкой конфигурации отчета"""
    
    AVAILABLE_FIELDS = {
        "social_data": {
            "title": "Социально-демографические данные",
            "fields": [
                ("krd_number", "№ КРД"),
                ("tab_number", "Табельный номер"),
                ("personal_number", "Личный номер"),
                ("category_name", "Категория военнослужащего"),
                ("rank_name", "Воинское звание"),
                ("surname", "Фамилия"),
                ("name", "Имя"),
                ("patronymic", "Отчество"),
                ("birth_date", "Дата рождения"),
                ("birth_place_town", "Населенный пункт места рождения"),
                ("birth_place_district", "Административный район места рождения"),
                ("birth_place_region", "Субъект (регион) места рождения"),
                ("birth_place_country", "Страна места рождения"),
                ("drafted_by_commissariat", "Наименование комиссариата"),
                ("draft_date", "Дата призыва"),
                ("povsk", "Наименование ПОВСК"),
                ("selection_date", "Дата отбора"),
                ("education", "Образование"),
                ("criminal_record", "Сведения о судимости"),
                ("social_media_account", "Аккаунт в социальных сетях"),
                ("bank_card_number", "Номер банковской карты"),
                ("passport_series", "Серия паспорта"),
                ("passport_number", "Номер паспорта"),
                ("passport_issue_date", "Дата выдачи паспорта"),
                ("passport_issued_by", "Кем выдан паспорт"),
                ("military_id_series", "Серия военного билета"),
                ("military_id_number", "Номер военного билета"),
                ("military_id_issue_date", "Дата выдачи военного билета"),
                ("military_id_issued_by", "Кем выдан военный билет"),
                ("appearance_features", "Особенности внешности"),
                ("personal_marks", "Личные приметы"),
                ("military_contacts", "Контакты в/с"),
                ("relatives_info", "Сведения о близких родственниках"),
            ]
        },
        "addresses": {
            "title": "Адреса проживания",
            "fields": [
                ("region", "Субъект РФ"),
                ("district", "Административный район"),
                ("town", "Населенный пункт"),
                ("street", "Улица"),
                ("house", "Дом"),
                ("building", "Корпус"),
                ("letter", "Литер"),
                ("apartment", "Квартира"),
                ("room", "Комната"),
                ("check_date", "Дата адресной проверки"),
                ("check_result", "Результат адресной проверки"),
            ]
        },
        "incoming_orders": {
            "title": "Входящие поручения на розыск",
            "fields": [
                ("initiator_full_name", "Инициатор розыска"),
                ("order_date", "Исходящая дата поручения"),
                ("order_number", "Исходящий номер поручения"),
                ("receipt_date", "Дата поступления в ВК"),
                ("receipt_number", "Входящий номер в ВК"),
                ("postal_index", "Индекс"),
                ("postal_region", "Субъект РФ"),
                ("postal_district", "Административный район"),
                ("postal_town", "Населенный пункт"),
                ("postal_street", "Улица"),
                ("postal_house", "Дом"),
                ("initiator_contacts", "Контакты источника"),
                ("our_response_date", "Дата ответа ВК"),
                ("our_response_number", "Исходящий номер ответа ВК"),
                ("military_unit_name", "Военное управление инициатора"),
            ]
        },
        "service_places": {
            "title": "Места службы",
            "fields": [
                ("place_name", "Наименование места службы"),
                ("military_unit_name", "Военное управление места службы"),
                ("garrison_name", "Гарнизон места службы"),
                ("position_name", "Воинская должность"),
                ("commanders", "Командиры (начальники)"),
                ("postal_index", "Индекс"),
                ("postal_region", "Субъект РФ"),
                ("postal_town", "Населенный пункт"),
                ("postal_street", "Улица"),
                ("postal_house", "Дом"),
                ("place_contacts", "Контакты места службы"),
            ]
        },
        "soch_episodes": {
            "title": "Сведения о СОЧ",
            "fields": [
                ("soch_date", "Дата СОЧ"),
                ("soch_location", "Место СОЧ"),
                ("order_date_number", "Дата и номер приказа о СОЧ"),
                ("witnesses", "Очевидцы СОЧ"),
                ("reasons", "Вероятные причины СОЧ"),
                ("weapon_info", "Сведения о наличии оружия"),
                ("clothing", "Во что был одет"),
                ("movement_options", "Варианты движения"),
                ("search_date", "Дата розыска"),
                ("found_by", "Кем разыскан"),
                ("notification_date", "Дата уведомления"),
                ("notification_number", "Номер уведомления"),
            ]
        },
        "outgoing_requests": {
            "title": "Исходящие запросы и поручения",
            "fields": [
                ("request_type_name", "Наименование запроса"),
                ("recipient_name", "Наименование адресата"),
                ("military_unit_name", "Военное управление адресата"),
                ("issue_date", "Исходящая дата"),
                ("issue_number", "Исходящий номер"),
                ("postal_index", "Индекс"),
                ("postal_region", "Субъект РФ"),
                ("postal_town", "Населенный пункт"),
                ("postal_street", "Улица"),
                ("postal_house", "Дом"),
                ("recipient_contacts", "Контакты"),
            ]
        }
    }
    
    def __init__(self, db_connection, krd_id=None, report_config=None):
        self.db = db_connection
        self.krd_id = krd_id
        self.wb = Workbook()
        self.report_config = report_config or self._get_default_config()
        
        self.header_font = Font(bold=True, size=11, color="FFFFFF")
        self.header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        self.section_font = Font(bold=True, size=12, color="000000")
        self.section_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        self.cell_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        self.header_alignment = Alignment(horizontal="center", vertical="center")
        
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        self.temp_image_files = []
        self.photo_width_px = 200
        self.photo_height_px = 270
    
    def _get_default_config(self):
        return {
            "sections": ["social_data", "addresses", "incoming_orders", 
                        "service_places", "soch_episodes", "outgoing_requests"],
            "fields": {}
        }
    
    def _cleanup_temp_files(self):
        for temp_file in self.temp_image_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"✗ Ошибка удаления временного файла {temp_file}: {e}")
        self.temp_image_files = []
    
    def _load_photo_from_db(self, field_name, krd_id=None):
        target_krd_id = krd_id if krd_id else self.krd_id
        
        try:
            query = QSqlQuery(self.db)
            query.prepare(f"""
                SELECT {field_name} 
                FROM krd.social_data 
                WHERE krd_id = :krd_id
                ORDER BY id DESC 
                LIMIT 1
            """)
            query.bindValue(":krd_id", target_krd_id)
            
            if not query.exec():
                return None
            
            if query.next():
                photo_data = query.value(0)
                
                if photo_data:
                    if hasattr(photo_data, 'data'):
                        return bytes(photo_data.data())
                    elif isinstance(photo_data, bytes):
                        return photo_data
                    elif isinstance(photo_data, bytearray):
                        return bytes(photo_data)
                    elif isinstance(photo_data, memoryview):
                        return bytes(photo_data)
                    else:
                        return bytes(photo_data)
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            print(f"✗ Ошибка загрузки фото {field_name}: {e}")
            return None
    
    def _create_temp_image_file(self, photo_bytes, suffix='.jpg', target_width=None, target_height=None):
        if not photo_bytes:
            return None
        
        try:
            img = PILImage.open(io.BytesIO(photo_bytes))
            
            if img.mode == 'RGBA':
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            if target_width and target_height:
                img = img.resize((target_width, target_height), PILImage.Resampling.LANCZOS)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            img.save(temp_file.name, quality=95)
            temp_file.close()
            
            self.temp_image_files.append(temp_file.name)
            return temp_file.name
            
        except Exception as e:
            print(f"✗ Ошибка создания временного файла: {e}")
            return None
    
    def export_to_excel(self, file_path):
        try:
            print(f"\n{'='*60}")
            print(f"📊 НАЧАЛО ЭКСПОРТА КРД-{self.krd_id}")
            print(f"{'='*60}")
            
            self.wb.remove(self.wb.active)
            ws = self.wb.create_sheet("Данные КРД")
            
            social_data = self._load_social_data()
            row = self._fill_social_data_section(ws, social_data, start_row=1)
            
            if "addresses" in self.report_config.get("sections", []):
                addresses = self._load_addresses()
                row = self._fill_addresses_section(ws, addresses, start_row=row)
            
            if "incoming_orders" in self.report_config.get("sections", []):
                incoming_orders = self._load_incoming_orders()
                row = self._fill_incoming_orders_section(ws, incoming_orders, start_row=row)
            
            if "service_places" in self.report_config.get("sections", []):
                service_places = self._load_service_places()
                row = self._fill_service_places_section(ws, service_places, start_row=row)
            
            if "soch_episodes" in self.report_config.get("sections", []):
                soch_episodes = self._load_soch_episodes()
                row = self._fill_soch_episodes_section(ws, soch_episodes, start_row=row)
            
            if "outgoing_requests" in self.report_config.get("sections", []):
                outgoing_requests = self._load_outgoing_requests()
                row = self._fill_outgoing_requests_section(ws, outgoing_requests, start_row=row)
            
            self._adjust_column_widths(ws)
            
            print(f"\n💾 СОХРАНЕНИЕ ФАЙЛА: {file_path}")
            self.wb.save(file_path)
            print(f"✓ Файл сохранён: {file_path}")
            
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
            self._cleanup_temp_files()
            raise
    
    def export_multiple_krd_to_excel(self, file_path, krd_ids=None):
        try:
            print(f"\n{'='*60}")
            print(f"📊 НАЧАЛО МАССОВОГО ЭКСПОРТА КРД (ОДИН ЛИСТ)")
            print(f"{'='*60}")
            
            if krd_ids is None:
                krd_ids = self.report_config.get("krd_ids", [])
            
            if not krd_ids:
                raise Exception("Не указан список КРД для экспорта")
            
            print(f"📋 Всего записей для экспорта: {len(krd_ids)}")
            
            self.wb.remove(self.wb.active)
            ws = self.wb.create_sheet("Отчет по КРД")
            
            row = self._fill_multiple_krd_to_single_sheet(ws, krd_ids)
            
            self._adjust_column_widths(ws)
            
            print(f"\n💾 СОХРАНЕНИЕ ФАЙЛА: {file_path}")
            self.wb.save(file_path)
            print(f"✓ Файл сохранён: {file_path}")
            
            self._cleanup_temp_files()
            
            print(f"\n{'='*60}")
            print(f"✅ МАССОВЫЙ ЭКСПОРТ ЗАВЕРШЁН УСПЕШНО")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"✗ ОШИБКА МАССОВОГО ЭКСПОРТА: {e}")
            print(f"{'='*60}\n")
            import traceback
            traceback.print_exc()
            self._cleanup_temp_files()
            raise
    
    def _fill_multiple_krd_to_single_sheet(self, ws, krd_ids):
        row = 1
        
        ws.merge_cells(f'A1:{get_column_letter(10)}1')
        cell = ws[f'A1']
        cell.value = "ОТЧЕТ ПО КАРТОЧКАМ РОЗЫСКА (КРД)"
        cell.font = Font(bold=True, size=14, color="FFFFFF")
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 2
        
        sections = self.report_config.get("sections", [])
        fields_config = self.report_config.get("fields", {})
        
        export_columns = []
        
        if "social_data" in sections:
            social_fields = fields_config.get("social_data", [])
            if social_fields:
                all_social_fields = dict(self.AVAILABLE_FIELDS["social_data"]["fields"])
                for field_key in social_fields:
                    if field_key in all_social_fields:
                        export_columns.append((field_key, all_social_fields[field_key]))
            else:
                export_columns.extend(self.AVAILABLE_FIELDS["social_data"]["fields"])
        
        for section in sections:
            if section != "social_data" and section in self.AVAILABLE_FIELDS:
                section_fields = fields_config.get(section, [])
                if section_fields:
                    all_section_fields = dict(self.AVAILABLE_FIELDS[section]["fields"])
                    for field_key in section_fields:
                        if field_key in all_section_fields:
                            export_columns.append((field_key, all_section_fields[field_key]))
                else:
                    export_columns.extend(self.AVAILABLE_FIELDS[section]["fields"])
        
        print(f"\n📋 Полей для экспорта: {len(export_columns)}")
        
        for col, (field_key, field_name) in enumerate(export_columns, 1):
            cell = ws.cell(row=row, column=col, value=field_name)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        print(f"\n📝 Экспорт данных...")
        for krd_id in krd_ids:
            print(f"  • Обработка КРД-{krd_id}...")
            
            data = self._load_all_data_for_krd(krd_id)
            
            print(f"    Загружено полей: {len(data)}")
            if 'krd_number' in data:
                print(f"    № КРД: {data['krd_number']}")
            if 'surname' in data:
                print(f"    Фамилия: {data['surname']}")
            
            for col, (field_key, field_name) in enumerate(export_columns, 1):
                value = self._get_field_value(data, field_key)
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            
            row += 1
        
        print(f"  ✓ Экспортировано {len(krd_ids)} записей")
        return row
    
    def _load_all_data_for_krd(self, krd_id):
        data = {}
        
        social_data = self._load_social_data_for_krd(krd_id)
        data.update(social_data)
        
        addresses = self._load_addresses_for_krd(krd_id)
        if addresses:
            data.update(addresses[0])
        
        incoming_orders = self._load_incoming_orders_for_krd(krd_id)
        if incoming_orders:
            data.update(incoming_orders[0])
        
        service_places = self._load_service_places_for_krd(krd_id)
        if service_places:
            data.update(service_places[0])
        
        soch_episodes = self._load_soch_episodes_for_krd(krd_id)
        if soch_episodes:
            data.update(soch_episodes[0])
        
        outgoing_requests = self._load_outgoing_requests_for_krd(krd_id)
        if outgoing_requests:
            data.update(outgoing_requests[0])
        
        return data
    
    def _get_field_value(self, data, field_key):
        value = data.get(field_key, '')
        
        if field_key.endswith('_date') and value:
            try:
                if hasattr(value, 'toString'):
                    return value.toString("dd.MM.yyyy")
                else:
                    return str(value)
            except:
                return str(value) if value else ''
        
        if value is None:
            return ''
        
        return value
    
    def export_to_single_sheet(self, ws):
        social_data = self._load_social_data()
        row = self._fill_social_data_section(ws, social_data, start_row=1)
        
        if "addresses" in self.report_config.get("sections", []):
            addresses = self._load_addresses()
            row = self._fill_addresses_section(ws, addresses, start_row=row)
        
        if "incoming_orders" in self.report_config.get("sections", []):
            incoming_orders = self._load_incoming_orders()
            row = self._fill_incoming_orders_section(ws, incoming_orders, start_row=row)
        
        if "service_places" in self.report_config.get("sections", []):
            service_places = self._load_service_places()
            row = self._fill_service_places_section(ws, service_places, start_row=row)
        
        if "soch_episodes" in self.report_config.get("sections", []):
            soch_episodes = self._load_soch_episodes()
            row = self._fill_soch_episodes_section(ws, soch_episodes, start_row=row)
        
        if "outgoing_requests" in self.report_config.get("sections", []):
            outgoing_requests = self._load_outgoing_requests()
            row = self._fill_outgoing_requests_section(ws, outgoing_requests, start_row=row)
        
        return True
    
    def _load_social_data(self):
        return self._load_social_data_for_krd(self.krd_id)
    
    def _load_social_data_for_krd(self, krd_id):
        """
        ИСПРАВЛЕНО: Убрана несуществующая колонка krd_number, используется kr.id
        """
        query_string = f"""
            SELECT 
                kr.id as krd_id,
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
            LEFT JOIN krd.krd kr ON s.krd_id = kr.id
            LEFT JOIN krd.categories c ON s.category_id = c.id
            LEFT JOIN krd.ranks r ON s.rank_id = r.id
            WHERE s.krd_id = {int(krd_id)}
            ORDER BY s.id DESC
            LIMIT 1
        """
        
        query = QSqlQuery(self.db)
        
        print(f"    📝 SQL запрос выполнен для КРД-{krd_id}")
        
        if not query.exec(query_string):
            print(f"    ⚠️ Ошибка SQL: {query.lastError().text()}")
            return {}
        
        if query.next():
            # === ИСПРАВЛЕНО: Формируем krd_number из ID ===
            krd_id_value = query.value('krd_id')
            krd_number = f"КРД-{krd_id_value}" if krd_id_value else ''
            
            return {
                'krd_id': krd_id_value or '',
                'krd_number': krd_number,  # Форматируем как "КРД-X"
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
        else:
            print(f"    ⚠️ Нет данных для КРД-{krd_id}")
            return {}
    
    def _load_addresses(self):
        return self._load_addresses_for_krd(self.krd_id)
    
    def _load_addresses_for_krd(self, krd_id):
        query_string = f"""
            SELECT 
                region, district, town, street, house, building, letter,
                apartment, room, check_date, check_result
            FROM krd.addresses
            WHERE krd_id = {int(krd_id)}
            ORDER BY id DESC
        """
        query = QSqlQuery(self.db)
        query.exec(query_string)
        
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
        return self._load_incoming_orders_for_krd(self.krd_id)
    
    def _load_incoming_orders_for_krd(self, krd_id):
        query_string = f"""
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
            WHERE i.krd_id = {int(krd_id)}
            ORDER BY i.receipt_date DESC
        """
        query = QSqlQuery(self.db)
        query.exec(query_string)
        
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
        return self._load_service_places_for_krd(self.krd_id)
    
    def _load_service_places_for_krd(self, krd_id):
        query_string = f"""
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
            WHERE s.krd_id = {int(krd_id)}
            ORDER BY s.id DESC
        """
        query = QSqlQuery(self.db)
        query.exec(query_string)
        
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
        return self._load_soch_episodes_for_krd(self.krd_id)
    
    def _load_soch_episodes_for_krd(self, krd_id):
        query_string = f"""
            SELECT 
                soch_date, soch_location, order_date_number, witnesses,
                reasons, weapon_info, clothing, movement_options, other_info,
                duty_officer_commissariat, duty_officer_omvd, investigation_info,
                prosecution_info, criminal_case_info, search_date, found_by,
                search_circumstances, notification_recipient, notification_date,
                notification_number
            FROM krd.soch_episodes
            WHERE krd_id = {int(krd_id)}
            ORDER BY soch_date DESC
        """
        query = QSqlQuery(self.db)
        query.exec(query_string)
        
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
        return self._load_outgoing_requests_for_krd(self.krd_id)
    
    def _load_outgoing_requests_for_krd(self, krd_id):
        query_string = f"""
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
            WHERE r.krd_id = {int(krd_id)}
            ORDER BY r.issue_date DESC
        """
        query = QSqlQuery(self.db)
        query.exec(query_string)
        
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
        if date_value:
            try:
                return date_value.toString("dd.MM.yyyy")
            except:
                return str(date_value)
        return ""
    
    def _fill_social_data_section(self, ws, data, start_row=1):
        row = start_row
        selected_fields = self.report_config.get("fields", {}).get("social_data", [])
        
        ws.merge_cells(f'A1:AC1')
        cell = ws[f'A1']
        cell.value = "СОЦИАЛЬНО-ДЕМОГРАФИЧЕСКИЕ ДАННЫЕ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        all_fields = self.AVAILABLE_FIELDS.get("social_data", {}).get("fields", [])
        
        if selected_fields:
            fields_to_export = [(k, v) for k, v in all_fields if k in selected_fields]
        else:
            fields_to_export = all_fields
        
        for col, (field_key, field_name) in enumerate(fields_to_export, 1):
            cell = ws.cell(row=row, column=col, value=field_name)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        for col, (field_key, field_name) in enumerate(fields_to_export, 1):
            value = data.get(field_key, '')
            if field_key.endswith('_date') and value:
                value = self._format_date(value)
            cell = ws.cell(row=row, column=col, value=value)
            cell.alignment = self.cell_alignment
            cell.border = self.thin_border
        
        row += 2
        return row
    
    def _fill_addresses_section(self, ws, addresses, start_row=1):
        row = start_row
        selected_fields = self.report_config.get("fields", {}).get("addresses", [])
        
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "АДРЕСА ПРОЖИВАНИЯ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        all_fields = self.AVAILABLE_FIELDS.get("addresses", {}).get("fields", [])
        
        if selected_fields:
            fields_to_export = [(k, v) for k, v in all_fields if k in selected_fields]
        else:
            fields_to_export = all_fields
        
        for col, (field_key, field_name) in enumerate(fields_to_export, 1):
            cell = ws.cell(row=row, column=col, value=field_name)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        for addr in addresses:
            for col, (field_key, field_name) in enumerate(fields_to_export, 1):
                value = addr.get(field_key, '')
                if field_key.endswith('_date') and value:
                    value = self._format_date(value)
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            row += 1
        
        return row
    
    def _fill_incoming_orders_section(self, ws, orders, start_row=1):
        row = start_row
        selected_fields = self.report_config.get("fields", {}).get("incoming_orders", [])
        
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "ВХОДЯЩИЕ ПОРУЧЕНИЯ НА РОЗЫСК"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        all_fields = self.AVAILABLE_FIELDS.get("incoming_orders", {}).get("fields", [])
        
        if selected_fields:
            fields_to_export = [(k, v) for k, v in all_fields if k in selected_fields]
        else:
            fields_to_export = all_fields
        
        for col, (field_key, field_name) in enumerate(fields_to_export, 1):
            cell = ws.cell(row=row, column=col, value=field_name)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        for order in orders:
            for col, (field_key, field_name) in enumerate(fields_to_export, 1):
                value = order.get(field_key, '')
                if field_key.endswith('_date') and value:
                    value = self._format_date(value)
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            row += 1
        
        return row
    
    def _fill_service_places_section(self, ws, places, start_row=1):
        row = start_row
        selected_fields = self.report_config.get("fields", {}).get("service_places", [])
        
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "МЕСТА СЛУЖБЫ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        all_fields = self.AVAILABLE_FIELDS.get("service_places", {}).get("fields", [])
        
        if selected_fields:
            fields_to_export = [(k, v) for k, v in all_fields if k in selected_fields]
        else:
            fields_to_export = all_fields
        
        for col, (field_key, field_name) in enumerate(fields_to_export, 1):
            cell = ws.cell(row=row, column=col, value=field_name)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        for place in places:
            for col, (field_key, field_name) in enumerate(fields_to_export, 1):
                value = place.get(field_key, '')
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            row += 1
        
        return row
    
    def _fill_soch_episodes_section(self, ws, episodes, start_row=1):
        row = start_row
        selected_fields = self.report_config.get("fields", {}).get("soch_episodes", [])
        
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "СВЕДЕНИЯ О СОЧ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        all_fields = self.AVAILABLE_FIELDS.get("soch_episodes", {}).get("fields", [])
        
        if selected_fields:
            fields_to_export = [(k, v) for k, v in all_fields if k in selected_fields]
        else:
            fields_to_export = all_fields
        
        for col, (field_key, field_name) in enumerate(fields_to_export, 1):
            cell = ws.cell(row=row, column=col, value=field_name)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        for episode in episodes:
            for col, (field_key, field_name) in enumerate(fields_to_export, 1):
                value = episode.get(field_key, '')
                if field_key.endswith('_date') and value:
                    value = self._format_date(value)
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            row += 1
        
        return row
    
    def _fill_outgoing_requests_section(self, ws, requests, start_row=1):
        row = start_row
        selected_fields = self.report_config.get("fields", {}).get("outgoing_requests", [])
        
        ws.merge_cells(f'A{row}:AC{row}')
        cell = ws[f'A{row}']
        cell.value = "ИСХОДЯЩИЕ ЗАПРОСЫ И ПОРУЧЕНИЯ"
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.header_alignment
        row += 1
        
        all_fields = self.AVAILABLE_FIELDS.get("outgoing_requests", {}).get("fields", [])
        
        if selected_fields:
            fields_to_export = [(k, v) for k, v in all_fields if k in selected_fields]
        else:
            fields_to_export = all_fields
        
        for col, (field_key, field_name) in enumerate(fields_to_export, 1):
            cell = ws.cell(row=row, column=col, value=field_name)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        row += 1
        
        for req in requests:
            for col, (field_key, field_name) in enumerate(fields_to_export, 1):
                value = req.get(field_key, '')
                if field_key.endswith('_date') and value:
                    value = self._format_date(value)
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = self.cell_alignment
                cell.border = self.thin_border
            row += 1
        
        return row
    
    def _adjust_column_widths(self, ws):
        for col_num in range(1, 50):
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