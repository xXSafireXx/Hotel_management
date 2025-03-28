DB_CONFIG = {
    'dbname': 'Hotel',
    'user': 'postgres',
    'password': '43512',
    'host': 'localhost',
    'port': '5432',
    'connect_timeout': 5
}

SECURITY_CONFIG = {
    'max_login_attempts': 3,
    'lock_time_minutes': 30,
    'password_min_length': 8,
    'password_requirements': {
        'min_length': 8,
        'require_upper': True,
        'require_digit': True,
        'require_special': True
    }
}

ROLES_CONFIG = {
    'roles': {
        1: {'name': 'Администратор', 'permissions': ['all']},
        2: {'name': 'Менеджер', 'permissions': ['manage_bookings', 'manage_guests', 'view_reports']},
        3: {'name': 'Персонал', 'permissions': ['manage_cleaning', 'view_schedule']},
        4: {'name': 'Бухгалтер', 'permissions': ['view_reports', 'manage_payments']}
    },
    'default_role': 2
}