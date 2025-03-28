from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, 
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from hotel_management.database.models import User
from hotel_management.utils.auth import AuthManager

class LoginWindow(QWidget):
    login_success = pyqtSignal(int, int)  # user_id, role_id

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setFixedSize(400, 300)
        self.auth_manager = AuthManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit(placeholderText="Логин")
        self.password_input = QLineEdit(
            placeholderText="Пароль", 
            echoMode=QLineEdit.EchoMode.Password
        )
        login_btn = QPushButton("Войти", clicked=self.authenticate)

        layout.addWidget(QLabel("Система управления отелем"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)
        self.setLayout(layout)

    def authenticate(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return

        if self.auth_manager.is_account_locked(username):
            QMessageBox.warning(self, "Ошибка", "Аккаунт временно заблокирован")
            return

        user = User.authenticate(username, password)
        
        if user:
            self.login_success.emit(user.user_id, user.role_id)
            self.close()
        else:
            self.auth_manager.record_failed_attempt(username)
            QMessageBox.warning(self, "Ошибка", "Неверные учетные данные")