import sys
from PyQt6.QtWidgets import QApplication
from hotel_management.ui.auth.login_window import LoginWindow
from hotel_management.ui.admin.admin_dashboard import AdminDashboard

class MainApp:
    def __init__(self):
        """Инициализация главного приложения"""
        self.app = QApplication(sys.argv)
        self.login_window = LoginWindow()
        self.login_window.login_success.connect(self.on_login_success)
        self.login_window.show()
        
    def on_login_success(self, user_id, role_id):
        """Обработчик успешного входа"""
        self.main_window = AdminDashboard(user_id, role_id)
        self.main_window.show()
        self.login_window.close()
        
    def run(self):
        """Запуск приложения"""
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = MainApp()
    app.run()