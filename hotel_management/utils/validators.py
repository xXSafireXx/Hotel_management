from PyQt6.QtWidgets import QMessageBox
import re

class Validators:
    @staticmethod
    def validate_phone(phone):
        return re.match(r'^\+?[0-9\s\-]{10,15}$', phone.strip())

    @staticmethod
    def validate_date_range(start_date, end_date):
        return start_date <= end_date if start_date and end_date else False

    @staticmethod
    def show_error(parent, title, message):
        QMessageBox.critical(parent, title, message)