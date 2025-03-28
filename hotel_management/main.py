import sys
from PyQt6.QtWidgets import QApplication
from ui.auth.login_window import LoginWindow

class HotelApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = LoginWindow()
        self.login_window.login_success.connect(self.on_login_success)

    def on_login_success(self, user_id, role_id):
        from ui.admin.admin_dashboard import AdminDashboard
        self.main_window = AdminDashboard(user_id, role_id)
        self.main_window.show()
        self.login_window.close()

    def run(self):
        self.login_window.show()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = HotelApp()
    app.run()