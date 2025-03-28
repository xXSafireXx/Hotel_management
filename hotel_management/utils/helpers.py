from datetime import datetime

def format_date(value):
    return value.strftime('%d.%m.%Y') if value else ""