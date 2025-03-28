from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit,
                            QPushButton, QLabel, QMessageBox)
from database.connector import DatabaseConnector

class ChangePasswordWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Смена пароля")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.old_pass = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.new_pass = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        self.confirm_pass = QLineEdit(echoMode=QLineEdit.EchoMode.Password)
        btn_submit = QPushButton("Изменить")

        layout.addWidget(QLabel("Старый пароль:"))
        layout.addWidget(self.old_pass)
        layout.addWidget(QLabel("Новый пароль:"))
        layout.addWidget(self.new_pass)
        layout.addWidget(QLabel("Подтвердите пароль:"))
        layout.addWidget(self.confirm_pass)
        layout.addWidget(btn_submit)
        self.setLayout(layout)