from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import pyqtSignal
from hotel_management.database.models import User

class LoginWindow(QWidget):
    login_success = pyqtSignal(int, int)  # Сигнал успешной авторизации (user_id, role_id)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setFixedSize(400, 300)
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса входа"""
        layout = QVBoxLayout()
        
        # Поля ввода
        self.username_input = QLineEdit(placeholderText="Логин")
        self.password_input = QLineEdit(placeholderText="Пароль", echoMode=QLineEdit.EchoMode.Password)
        
        # Кнопка входа
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.authenticate)
        
        # Добавление элементов на форму
        layout.addWidget(QLabel("Система управления отелем"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_btn)
        
        self.setLayout(layout)
        
    def authenticate(self):
        """Аутентификация пользователя"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Проверка заполнения полей
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
            
        # Попытка аутентификации
        user = User.authenticate(username, password)
        
        if user:
            if user.is_active:
                self.login_success.emit(user.user_id, user.role_id)
                self.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Ваш аккаунт заблокирован")
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные учетные данные")