# Конфигурация базы данных
DB_CONFIG = {
    'dbname': 'Hotel',
    'user': 'postgres',
    'password': '43512',  # Замените на ваш пароль
    'host': 'localhost',
    'port': '5432',
    'connect_timeout': 5
}

# Настройки безопасности
SECURITY_CONFIG = {
    'max_login_attempts': 3,          # Максимальное количество попыток входа
    'lock_time_minutes': 30,          # Время блокировки в минутах
    'password_min_length': 8,         # Минимальная длина пароля
    'password_requirements': {
        'require_upper': True,        # Требовать заглавные буквы
        'require_digit': True,        # Требовать цифры
        'require_special': True       # Требовать спецсимволы
    }
}

# Права доступа для ролей
PERMISSIONS = {
    'admin': ['all'],                 # Полный доступ
    'manager': ['manage_bookings', 'manage_guests', 'view_reports'],
    'maid': ['manage_cleaning'],
    'receptionist': ['check_in_out', 'view_guests']
}