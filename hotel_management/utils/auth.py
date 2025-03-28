from datetime import datetime, timedelta
from hotel_management.config import SECURITY_CONFIG
from hotel_management.database.connector import DatabaseConnector

class AuthManager:
    def __init__(self):
        self.max_attempts = SECURITY_CONFIG['max_login_attempts']
        self.lock_time = timedelta(minutes=SECURITY_CONFIG['lock_time_minutes'])

    def record_failed_attempt(self, username):
        """Записывает неудачную попытку входа и блокирует аккаунт при необходимости"""
        db = DatabaseConnector()
        if db.connect():
            try:
                # Увеличиваем счетчик неудачных попыток
                db.execute_query(
                    "UPDATE app_users SET failed_attempts = failed_attempts + 1 WHERE username = %s",
                    (username,)
                )

                # Проверяем, нужно ли блокировать
                result = db.execute_query(
                    "SELECT failed_attempts FROM app_users WHERE username = %s",
                    (username,), fetch=True
                )

                if result and result[0][0] >= self.max_attempts:
                    self.lock_account(username)
            finally:
                db.disconnect()

    def lock_account(self, username):
        """Блокирует аккаунт на указанное время"""
        db = DatabaseConnector()
        if db.connect():
            try:
                lock_until = datetime.now() + self.lock_time
                db.execute_query(
                    "UPDATE app_users SET locked_until = %s WHERE username = %s",
                    (lock_until, username)
                )
            finally:
                db.disconnect()

    def is_account_locked(self, username):
        """Проверяет, заблокирован ли аккаунт"""
        db = DatabaseConnector()
        if db.connect():
            try:
                result = db.execute_query(
                    "SELECT locked_until > NOW() FROM app_users WHERE username = %s",
                    (username,), fetch=True
                )
                return result[0][0] if result else False
            finally:
                db.disconnect()
        return False