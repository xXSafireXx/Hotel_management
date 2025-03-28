from datetime import datetime
from hotel_management.database.connector import DatabaseConnector
from hotel_management.config import SECURITY_CONFIG, PERMISSIONS
import re

class User:
    def __init__(self, user_id, username, role_id, is_active=True, locked_until=None):
        """
        Инициализация объекта пользователя
        :param user_id: ID пользователя
        :param username: Логин
        :param role_id: ID роли (1-Админ, 2-Менеджер, 3-Горничная, 4-Портье)
        :param is_active: Активен ли аккаунт
        :param locked_until: Время блокировки
        """
        self.user_id = user_id
        self.username = username
        self.role_id = role_id
        self.is_active = is_active
        self.locked_until = locked_until
        self.permissions = self._get_permissions()

    def _get_permissions(self):
        """Получает список прав доступа для роли пользователя"""
        role_map = {
            1: 'admin',
            2: 'manager',
            3: 'maid',
            4: 'receptionist'
        }
        role_name = role_map.get(self.role_id, '')
        return PERMISSIONS.get(role_name, [])

    @classmethod
    def authenticate(cls, username, password):
        """
        Аутентификация пользователя
        :param username: Логин
        :param password: Пароль
        :return: Объект User или None
        """
        db = DatabaseConnector()
        if not db.connect():
            return None
            
        try:
            query = """
            SELECT u.user_id, u.username, u.role_id, 
                   (u.locked_until IS NULL OR u.locked_until < NOW()) as is_active,
                   u.locked_until
            FROM app_users u
            WHERE u.username = %s AND u.password_hash = crypt(%s, u.password_hash)
            """
            result = db.execute_query(query, (username, password), fetch=True)
            
            if result and result[0][3]:  # Проверка is_active
                return cls(*result[0][:3], result[0][3], result[0][4])
            return None
        finally:
            db.disconnect()

    @staticmethod
    def validate_password(password):
        """
        Проверка сложности пароля
        :param password: Пароль для проверки
        :return: (bool, str) - (Валиден, Сообщение об ошибке)
        """
        config = SECURITY_CONFIG['password_requirements']
        errors = []
        
        # Проверка длины пароля
        if len(password) < SECURITY_CONFIG['password_min_length']:
            errors.append(f"Пароль должен содержать минимум {SECURITY_CONFIG['password_min_length']} символов")
        
        # Проверка на заглавные буквы
        if config['require_upper'] and not re.search(r'[A-ZА-Я]', password):
            errors.append("Пароль должен содержать хотя бы одну заглавную букву")
        
        # Проверка на цифры
        if config['require_digit'] and not re.search(r'\d', password):
            errors.append("Пароль должен содержать хотя бы одну цифру")
        
        # Проверка на спецсимволы
        if config['require_special'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Пароль должен содержать хотя бы один специальный символ")
        
        return (True, "") if not errors else (False, "; ".join(errors))

class Role:
    @staticmethod
    def get_all():
        """Получает список всех ролей из БД"""
        db = DatabaseConnector()
        if not db.connect():
            return []
            
        try:
            query = "SELECT role_id, name FROM roles ORDER BY role_id"
            result = db.execute_query(query, fetch=True)
            return result if result else []
        finally:
            db.disconnect()

    @staticmethod
    def get_name(role_id):
        """Получает название роли по ID"""
        db = DatabaseConnector()
        if not db.connect():
            return "Неизвестная роль"
            
        try:
            query = "SELECT name FROM roles WHERE role_id = %s"
            result = db.execute_query(query, (role_id,), fetch=True)
            return result[0][0] if result else "Неизвестная роль"
        finally:
            db.disconnect()