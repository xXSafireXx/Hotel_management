import psycopg2
from psycopg2 import OperationalError
from hotel_management.config import DB_CONFIG

class DatabaseConnector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        try:
            if self.connection is None or self.connection.closed:
                self.connection = psycopg2.connect(**DB_CONFIG)
            return True
        except OperationalError as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return False

    def disconnect(self):
        if self.connection and not self.connection.closed:
            self.connection.close()
        self.connection = None

    def execute_query(self, query, params=None, fetch=False):
        try:
            if not self.connect():
                return None if fetch else False
                
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    return cursor.fetchall()
                self.connection.commit()
                return True
                
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            print(f"Ошибка выполнения запроса: {e}")
            return None if fetch else False