"""
Модуль для аудита действий пользователей
"""

from PyQt6.QtSql import QSqlQuery
import json


class AuditLogger:
    """
    Класс для логирования действий пользователей
    """
    
    def __init__(self, db_connection, user_info):
        """
        Инициализация логгера
        
        Args:
            db_connection: соединение с базой данных
            user_info (dict): информация о текущем пользователе
        """
        self.db = db_connection
        self.user_info = user_info
    
    def log_action(self, action_type, table_name, record_id=None, krd_id=None, 
                   old_values=None, new_values=None, description=None):
        """
        Логирование действия пользователя
        
        Args:
            action_type (str): тип действия (CREATE, UPDATE, DELETE, VIEW и т.д.)
            table_name (str): название таблицы
            record_id (int, optional): ID записи
            krd_id (int, optional): ID КРД
            old_values (dict, optional): старые значения
            new_values (dict, optional): новые значения
            description (str, optional): описание действия
        """
        try:
            query = QSqlQuery(self.db)
            query.prepare("""
                INSERT INTO krd.audit_log 
                (user_id, username, action_type, table_name, record_id, krd_id, 
                 old_values, new_values, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
            
            # Преобразуем словари в JSON
            old_json = json.dumps(old_values, ensure_ascii=False) if old_values else None
            new_json = json.dumps(new_values, ensure_ascii=False) if new_values else None
            
            query.addBindValue(self.user_info.get('id'))
            query.addBindValue(self.user_info.get('username'))
            query.addBindValue(action_type)
            query.addBindValue(table_name)
            query.addBindValue(record_id if record_id else None)
            query.addBindValue(krd_id if krd_id else None)
            query.addBindValue(old_json)
            query.addBindValue(new_json)
            query.addBindValue(description)
            
            if not query.exec():
                print(f"⚠️ Ошибка логирования: {query.lastError().text()}")
        
        except Exception as e:
            print(f"⚠️ Ошибка в логгере аудита: {e}")
    
    # ========================
    # МЕТОДЫ АУДИТА КРД
    # ========================
    
    def log_krd_create(self, krd_id, data):
        """Логирование создания КРД"""
        self.log_action(
            action_type='CREATE',
            table_name='krd',
            record_id=krd_id,
            krd_id=krd_id,
            new_values=data,
            description=f'Создана новая карточка розыска КРД-{krd_id}'
        )
    
    def log_krd_update(self, krd_id, old_data, new_data):
        """Логирование обновления КРД"""
        # Находим измененные поля
        changed_fields = {}
        for key in new_:
            if key in old_data and old_data[key] != new_data[key]:
                changed_fields[key] = {
                    'old': old_data[key],
                    'new': new_data[key]
                }
        
        self.log_action(
            action_type='UPDATE',
            table_name='krd',
            record_id=krd_id,
            krd_id=krd_id,
            old_values=old_data,
            new_values=new_data,
            description=f'Обновлена карточка розыска КРД-{krd_id}. Изменено полей: {len(changed_fields)}'
        )
    
    def log_krd_delete(self, krd_id, data):
        """Логирование удаления КРД"""
        self.log_action(
            action_type='DELETE',
            table_name='krd',
            record_id=krd_id,
            krd_id=krd_id,
            old_values=data,
            description=f'Удалена карточка розыска КРД-{krd_id}'
        )
    
    def log_krd_view(self, krd_id):
        """Логирование просмотра КРД"""
        self.log_action(
            action_type='VIEW',
            table_name='krd',
            record_id=krd_id,
            krd_id=krd_id,
            description=f'Просмотрена карточка розыска КРД-{krd_id}'
        )
    
    def log_krd_restore(self, krd_id):
        """Логирование восстановления КРД"""
        self.log_action(
            action_type='RESTORE',
            table_name='krd',
            record_id=krd_id,
            krd_id=krd_id,
            description=f'Восстановлена карточка розыска КРД-{krd_id}'
        )
    
    # ========================
    # МЕТОДЫ АУДИТА ШАБЛОНОВ
    # ========================
    
    def log_template_create(self, template_id, template_name, description, file_size):
        """Логирование создания шаблона документа"""
        self.log_action(
            action_type='TEMPLATE_CREATE',
            table_name='document_templates',
            record_id=template_id,
            new_values={
                'name': template_name,
                'description': description,
                'file_size': file_size
            },
            description=f'Создан шаблон документа "{template_name}" ({file_size} байт)'
        )
    
    def log_template_update(self, template_id, old_name, new_name, old_description, new_description):
        """Логирование обновления шаблона документа"""
        self.log_action(
            action_type='TEMPLATE_UPDATE',
            table_name='document_templates',
            record_id=template_id,
            old_values={
                'name': old_name,
                'description': old_description
            },
            new_values={
                'name': new_name,
                'description': new_description
            },
            description=f'Обновлен шаблон документа "{old_name}" → "{new_name}"'
        )
    
    def log_template_delete(self, template_id, template_name):
        """Логирование удаления шаблона документа"""
        self.log_action(
            action_type='TEMPLATE_DELETE',
            table_name='document_templates',
            record_id=template_id,
            old_values={'name': template_name},
            description=f'Удален шаблон документа "{template_name}"'
        )
    
    def log_template_view(self, template_id, template_name):
        """Логирование просмотра шаблона"""
        self.log_action(
            action_type='TEMPLATE_VIEW',
            table_name='document_templates',
            record_id=template_id,
            description=f'Просмотрен шаблон документа "{template_name}"'
        )
    
    def log_mapping_create(self, template_id, field_name, db_column, table_name):
        """Логирование создания сопоставления поля"""
        self.log_action(
            action_type='MAPPING_CREATE',
            table_name='field_mappings',
            new_values={
                'template_id': template_id,
                'field_name': field_name,
                'db_column': db_column,
                'table_name': table_name
            },
            description=f'Добавлено сопоставление "{{{{{field_name}}}}}" → {table_name}.{db_column}'
        )
    
    def log_mapping_delete(self, field_name, db_column):
        """Логирование удаления сопоставления поля"""
        self.log_action(
            action_type='MAPPING_DELETE',
            table_name='field_mappings',
            old_values={
                'field_name': field_name,
                'db_column': db_column
            },
            description=f'Удалено сопоставление "{{{{{field_name}}}}}" → {db_column}'
        )
    
    def log_mapping_update(self, old_field, new_field, old_column, new_column):
        """Логирование обновления сопоставления поля"""
        self.log_action(
            action_type='MAPPING_UPDATE',
            table_name='field_mappings',
            old_values={
                'field_name': old_field,
                'db_column': old_column
            },
            new_values={
                'field_name': new_field,
                'db_column': new_column
            },
            description=f'Обновлено сопоставление "{{{{{old_field}}}}}" → "{{{{{new_field}}}}}"'
        )
    
    # ========================
    # МЕТОДЫ АУДИТА ДОКУМЕНТОВ
    # ========================
    
    def log_document_generate(self, krd_id, template_name):
        """Логирование генерации документа"""
        self.log_action(
            action_type='DOCUMENT_GENERATE',
            table_name='documents',
            krd_id=krd_id,
            new_values={'template_name': template_name},
            description=f'Сгенерирован документ по шаблону "{template_name}" для КРД-{krd_id}'
        )
    
    def log_document_save(self, krd_id, filename):
        """Логирование сохранения документа"""
        self.log_action(
            action_type='DOCUMENT_SAVE',
            table_name='documents',
            krd_id=krd_id,
            new_values={'filename': filename},
            description=f'Сохранен документ "{filename}" для КРД-{krd_id}'
        )
    
    # ========================
    # МЕТОДЫ АУДИТА ПОЛЬЗОВАТЕЛЕЙ
    # ========================
    
    def log_user_login(self):
        """Логирование входа пользователя"""
        self.log_action(
            action_type='LOGIN',
            table_name='users',
            record_id=self.user_info.get('id'),
            description=f'Пользователь {self.user_info.get("username")} вошел в систему'
        )
    
    def log_user_logout(self):
        """Логирование выхода пользователя"""
        self.log_action(
            action_type='LOGOUT',
            table_name='users',
            record_id=self.user_info.get('id'),
            description=f'Пользователь {self.user_info.get("username")} вышел из системы'
        )
    
    # ========================
    # МЕТОДЫ АУДИТА ЭКСПОРТА
    # ========================
    
    def log_export(self, krd_id, export_type, filename):
        """Логирование экспорта данных"""
        self.log_action(
            action_type='EXPORT',
            table_name='krd',
            krd_id=krd_id,
            new_values={
                'export_type': export_type,
                'filename': filename
            },
            description=f'Экспортированы данные КРД-{krd_id} в формате {export_type}'
        )