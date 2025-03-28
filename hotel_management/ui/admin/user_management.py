from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from hotel_management.database.connector import DatabaseConnector
from hotel_management.database.models import User, Role

class UserManagement(QWidget):
    def __init__(self, current_user_role):
        super().__init__()
        self.current_user_role = current_user_role
        self.setWindowTitle("Управление пользователями")
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица пользователей
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Логин", "Роль", "Статус", "Блокировка"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить пользователя")
        self.btn_add.clicked.connect(self.show_add_user_dialog)
        
        self.btn_change_pass = QPushButton("Изменить пароль")
        self.btn_change_pass.clicked.connect(self.show_change_password_dialog)
        
        self.btn_toggle = QPushButton("Блокировать/Разблокировать")
        self.btn_toggle.clicked.connect(self.toggle_user_status)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_change_pass)
        btn_layout.addWidget(self.btn_toggle)

        # Проверка прав доступа
        if not self.check_permission('all'):
            self.btn_add.setEnabled(False)
            self.btn_change_pass.setEnabled(False)
            self.btn_toggle.setEnabled(False)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def check_permission(self, permission):
        """Проверяет права текущего пользователя"""
        if self.current_user_role == 1:  # Администратор
            return True
        return permission in ROLES_CONFIG['roles'].get(self.current_user_role, {}).get('permissions', [])

    def load_users(self):
        db = DatabaseConnector()
        if db.connect():
            query = """
            SELECT u.user_id, u.username, r.name, 
                   CASE WHEN u.locked_until IS NULL OR u.locked_until < NOW() 
                   THEN 'Активен' ELSE 'Заблокирован' END,
                   COALESCE(TO_CHAR(u.locked_until, 'DD.MM.YYYY HH24:MI'), '-')
            FROM app_users u
            LEFT JOIN roles r ON u.role_id = r.role_id
            ORDER BY u.user_id
            """
            result = db.execute_query(query, fetch=True)
            
            if result:
                self.table.setRowCount(len(result))
                for row_idx, row in enumerate(result):
                    for col_idx, cell in enumerate(row):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell)))
            db.disconnect()

    def show_add_user_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить пользователя")
        dialog.setFixedSize(400, 300)
        
        layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pass_input = QLineEdit()
        self.confirm_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_combo = QComboBox()
        
        # Заполняем роли
        for role_id, name in Role.get_all():
            self.role_combo.addItem(name, role_id)
        
        layout.addRow("Логин:", self.username_input)
        layout.addRow("Пароль:", self.password_input)
        layout.addRow("Подтвердите пароль:", self.confirm_pass_input)
        layout.addRow("Роль:", self.role_combo)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.add_user(dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def add_user(self, dialog):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_pass = self.confirm_pass_input.text()
        role_id = self.role_combo.currentData()
        
        # Валидация
        if not username or not password or not confirm_pass:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
            
        if password != confirm_pass:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают")
            return
            
        is_valid, message = User.validate_password(password)
        if not is_valid:
            QMessageBox.warning(self, "Ошибка", message)
            return
            
        db = DatabaseConnector()
        if db.connect():
            query = """
            INSERT INTO app_users (username, password_hash, role_id)
            VALUES (%s, crypt(%s, gen_salt('bf')), %s)
            """
            success = db.execute_query(query, (username, password, role_id))
            
            if success:
                QMessageBox.information(self, "Успех", "Пользователь добавлен")
                self.load_users()
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить пользователя")
                
            db.disconnect()

    def show_change_password_dialog(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
            
        user_id = self.table.item(selected_row, 0).text()
        username = self.table.item(selected_row, 1).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Смена пароля для {username}")
        dialog.setFixedSize(400, 250)
        
        layout = QFormLayout()
        
        self.old_pass_input = QLineEdit()
        self.old_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass_input = QLineEdit()
        self.new_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_new_pass_input = QLineEdit()
        self.confirm_new_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addRow("Текущий пароль:", self.old_pass_input)
        layout.addRow("Новый пароль:", self.new_pass_input)
        layout.addRow("Подтвердите новый пароль:", self.confirm_new_pass_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.change_password(dialog, user_id))
        buttons.rejected.connect(dialog.reject)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def change_password(self, dialog, user_id):
        old_pass = self.old_pass_input.text()
        new_pass = self.new_pass_input.text()
        confirm_pass = self.confirm_new_pass_input.text()
        
        # Валидация
        if not old_pass or not new_pass or not confirm_pass:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
            
        if new_pass != confirm_pass:
            QMessageBox.warning(self, "Ошибка", "Новые пароли не совпадают")
            return
            
        is_valid, message = User.validate_password(new_pass)
        if not is_valid:
            QMessageBox.warning(self, "Ошибка", message)
            return
            
        db = DatabaseConnector()
        if db.connect():
            # Проверяем старый пароль
            check_query = """
            SELECT COUNT(*) FROM app_users 
            WHERE user_id = %s AND password_hash = crypt(%s, password_hash)
            """
            result = db.execute_query(check_query, (user_id, old_pass), fetch=True)
            
            if not result or result[0][0] == 0:
                QMessageBox.warning(self, "Ошибка", "Неверный текущий пароль")
                db.disconnect()
                return
                
            # Обновляем пароль
            update_query = """
            UPDATE app_users 
            SET password_hash = crypt(%s, gen_salt('bf'))
            WHERE user_id = %s
            """
            success = db.execute_query(update_query, (new_pass, user_id))
            
            if success:
                QMessageBox.information(self, "Успех", "Пароль изменен")
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось изменить пароль")
                
            db.disconnect()

    def toggle_user_status(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
            
        user_id = self.table.item(selected_row, 0).text()
        username = self.table.item(selected_row, 1).text()
        current_status = self.table.item(selected_row, 3).text()
        
        db = DatabaseConnector()
        if db.connect():
            if current_status == "Активен":
                # Блокируем
                query = """
                UPDATE app_users 
                SET locked_until = NOW() + INTERVAL '30 days' 
                WHERE user_id = %s
                """
                action = "заблокирован"
            else:
                # Разблокируем
                query = "UPDATE app_users SET locked_until = NULL WHERE user_id = %s"
                action = "разблокирован"
            
            success = db.execute_query(query, (user_id,))
            
            if success:
                QMessageBox.information(self, "Успех", f"Пользователь {username} {action}")
                self.load_users()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось изменить статус")
                
            db.disconnect()