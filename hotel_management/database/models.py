from datetime import datetime
from hotel_management.database.connector import DatabaseConnector
from hotel_management.config import SECURITY_CONFIG, ROLES_CONFIG
import re

class User:
    def __init__(self, user_id, username, role_id, is_active=True, locked_until=None):
        self.user_id = user_id
        self.username = username
        self.role_id = role_id if role_id is not None else ROLES_CONFIG['default_role']
        self.is_active = is_active
        self.locked_until = locked_until
        self.permissions = ROLES_CONFIG['roles'].get(self.role_id, {}).get('permissions', [])

    @classmethod
    def authenticate(cls, username, password):
        db = DatabaseConnector()
        if not db.connect():
            return None
            
        # Сначала пробуем проверить через crypt()
        query = """
        SELECT user_id, username, role_id, 
               (locked_until IS NULL OR locked_until < NOW()) as is_active,
               locked_until
        FROM app_users 
        WHERE username = %s AND password_hash = crypt(%s, password_hash)
        """
        result = db.execute_query(query, (username, password), fetch=True)
        
        # Если не сработало, проверяем открытый пароль (для совместимости)
        if not result:
            query = """
            SELECT user_id, username, role_id, 
                   (locked_until IS NULL OR locked_until < NOW()) as is_active,
                   locked_until
            FROM app_users 
            WHERE username = %s AND password_hash = %s
            """
            result = db.execute_query(query, (username, password), fetch=True)
            
            # Если нашли по открытому паролю - хешируем его
            if result:
                update_query = """
                UPDATE app_users 
                SET password_hash = crypt(%s, gen_salt('bf'))
                WHERE user_id = %s
                """
                db.execute_query(update_query, (password, result[0][0]))
        
        db.disconnect()
        
        if result and result[0][3]:  # Проверка is_active
            return cls(*result[0][:3], result[0][3], result[0][4])
        return None

    @staticmethod
    def validate_password(password):
        """Проверка сложности пароля"""
        config = SECURITY_CONFIG['password_requirements']
        errors = []
        
        if len(password) < config['min_length']:
            errors.append(f"Пароль должен содержать минимум {config['min_length']} символов")
        
        if config['require_upper'] and not re.search(r'[A-ZА-Я]', password):
            errors.append("Пароль должен содержать хотя бы одну заглавную букву")
        
        if config['require_digit'] and not re.search(r'\d', password):
            errors.append("Пароль должен содержать хотя бы одну цифру")
        
        if config['require_special'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Пароль должен содержать хотя бы один специальный символ")
        
        return (True, "") if not errors else (False, "; ".join(errors))

class Role:
    @staticmethod
    def get_all():
        """Возвращает список всех ролей"""
        return [(role_id, data['name']) for role_id, data in ROLES_CONFIG['roles'].items()]