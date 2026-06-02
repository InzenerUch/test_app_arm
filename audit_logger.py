"""
Модуль для аудита действий пользователей
Адаптирован под структуру krd.audit_log без хранения diff-значений (old/new).
"""

from PyQt6.QtSql import QSqlQuery


class AuditLogger:
    """Класс для логирования действий пользователей"""
    
    def __init__(self, db_connection, user_info):
        """
        Args:
            db_connection: активное QSqlDatabase соединение
            user_info (dict): {'id': int, 'username': str}
        """
        self.db = db_connection
        self.user_info = user_info
    
    def log_action(self, action_type, table_name, record_id=None, krd_id=None, description=None):
        """Базовый метод записи события в журнал аудита"""
        try:
            query = QSqlQuery(self.db)
            query.prepare("""
                INSERT INTO krd.audit_log 
                (user_id, username, action_type, table_name, record_id, krd_id, description)
                VALUES (:uid, :uname, :atype, :tname, :rid, :kid, :desc)
            """)
            query.bindValue(":uid", self.user_info.get('id'))
            query.bindValue(":uname", self.user_info.get('username'))
            query.bindValue(":atype", action_type)
            query.bindValue(":tname", table_name)
            query.bindValue(":rid", record_id)
            query.bindValue(":kid", krd_id)
            query.bindValue(":desc", description)
            
            if not query.exec():
                print(f"⚠️ Ошибка логирования: {query.lastError().text()}")
                
        except Exception as e:
            print(f"⚠️ Критическая ошибка в логгере аудита: {e}")

    # ========================
    # МЕТОДЫ АУДИТА КРД
    # ========================
    def log_krd_create(self, krd_id, data=None):
        self.log_action('CREATE', 'krd', krd_id, krd_id, f'Создана новая карточка розыска КРД-{krd_id}')
    
    def log_krd_update(self, krd_id, old_data=None, new_data=None):
        # Параметры old_data/new_data оставлены для обратной совместимости вызовов, но игнорируются
        self.log_action('UPDATE', 'krd', krd_id, krd_id, f'Обновлена карточка розыска КРД-{krd_id}')
    
    def log_krd_delete(self, krd_id, data=None):
        self.log_action('DELETE', 'krd', krd_id, krd_id, f'Удалена карточка розыска КРД-{krd_id}')
    
    def log_krd_view(self, krd_id):
        self.log_action('VIEW', 'krd', krd_id, krd_id, f'Просмотрена карточка розыска КРД-{krd_id}')
    
    def log_krd_restore(self, krd_id):
        self.log_action('RESTORE', 'krd', krd_id, krd_id, f'Восстановлена карточка розыска КРД-{krd_id}')

    # ========================
    # МЕТОДЫ АУДИТА ШАБЛОНОВ И МАППИНГОВ
    # ========================
    def log_template_create(self, template_id, template_name, description=None, file_size=None):
        self.log_action('TEMPLATE_CREATE', 'document_templates', template_id, None,
                        f'Создан шаблон "{template_name}"')
    
    def log_template_update(self, template_id, old_name=None, new_name=None, old_desc=None, new_desc=None):
        self.log_action('TEMPLATE_UPDATE', 'document_templates', template_id, None,
                        f'Обновлен шаблон документа ID={template_id}')
    
    def log_template_delete(self, template_id, template_name):
        self.log_action('TEMPLATE_DELETE', 'document_templates', template_id, None,
                        f'Удален шаблон "{template_name}"')

    def log_mapping_create(self, template_id, field_name, db_column, table_name):
        self.log_action('MAPPING_CREATE', 'field_mappings', None, None,
                        f'Добавлено сопоставление "{field_name}" → {table_name}.{db_column}')
    
    def log_mapping_delete(self, field_name, db_column):
        self.log_action('MAPPING_DELETE', 'field_mappings', None, None,
                        f'Удалено сопоставление "{field_name}" → {db_column}')
    
    def log_mapping_update(self, old_field, new_field, old_column, new_column):
        self.log_action('MAPPING_UPDATE', 'field_mappings', None, None,
                        f'Изменено сопоставление: "{old_field}" → "{new_field}"')

    # ========================
    # МЕТОДЫ АУДИТА ДОКУМЕНТОВ И ЭКСПОРТА
    # ========================
    def log_document_generate(self, krd_id, template_name):
        self.log_action('DOCUMENT_GENERATE', 'outgoing_requests', None, krd_id,
                        f'Сгенерирован документ по шаблону "{template_name}" для КРД-{krd_id}')
    
    def log_document_save(self, krd_id, filename):
        self.log_action('DOCUMENT_SAVE', 'outgoing_requests', None, krd_id,
                        f'Сохранен документ "{filename}" для КРД-{krd_id}')
    
    def log_export(self, krd_id, export_type, filename):
        self.log_action('EXPORT', 'krd', None, krd_id,
                        f'Экспорт данных КРД-{krd_id} в {export_type} → {filename}')

    # ========================
    # МЕТОДЫ АУДИТА СЕССИЙ
    # ========================
    def log_user_login(self):
        self.log_action('LOGIN', 'users', self.user_info.get('id'), None,
                        f'Пользователь {self.user_info.get("username")} вошел в систему')
    
    def log_user_logout(self):
        self.log_action('LOGOUT', 'users', self.user_info.get('id'), None,
                        f'Пользователь {self.user_info.get("username")} вышел из системы')