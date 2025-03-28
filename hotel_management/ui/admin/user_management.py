from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QHeaderView,
                            QMessageBox, QDialog, QFormLayout, QLineEdit,
                            QComboBox, QDialogButtonBox)
from PyQt6.QtCore import Qt
from hotel_management.database.connector import DatabaseConnector
from hotel_management.database.models import User, Role

class UserManagement(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Логин", "Роль", "Статус", "Блокировка"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

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

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_users(self):
        """Загрузка списка пользователей из БД"""
        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к БД")
            return
            
        try:
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
            else:
                QMessageBox.information(self, "Информация", "Нет данных о пользователях")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки пользователей: {str(e)}")
        finally:
            db.disconnect()

    def show_add_user_dialog(self):
        """Показывает диалог добавления пользователя"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить пользователя")
        dialog.setFixedSize(400, 300)
        
        layout = QFormLayout()
        
        self.dialog_username = QLineEdit()
        self.dialog_password = QLineEdit()
        self.dialog_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.dialog_confirm_pass = QLineEdit()
        self.dialog_confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.dialog_role_combo = QComboBox()
        
        # Заполнение комбобокса ролями
        roles = Role.get_all()
        for role_id, name in roles:
            self.dialog_role_combo.addItem(name, role_id)
        
        layout.addRow("Логин:", self.dialog_username)
        layout.addRow("Пароль:", self.dialog_password)
        layout.addRow("Подтвердите пароль:", self.dialog_confirm_pass)
        layout.addRow("Роль:", self.dialog_role_combo)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.add_user(dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def add_user(self, dialog):
        """Добавляет нового пользователя"""
        username = self.dialog_username.text().strip()
        password = self.dialog_password.text()
        confirm_pass = self.dialog_confirm_pass.text()
        role_id = self.dialog_role_combo.currentData()
        
        # Валидация ввода
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
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к БД")
            return
            
        try:
            # Проверка существования пользователя
            check_query = "SELECT COUNT(*) FROM app_users WHERE username = %s"
            check_result = db.execute_query(check_query, (username,), fetch=True)
            
            if check_result and check_result[0][0] > 0:
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует")
                return
                
            # Добавление пользователя
            query = """
            INSERT INTO app_users (username, password_hash, role_id)
            VALUES (%s, crypt(%s, gen_salt('bf')), %s)
            """
            success = db.execute_query(query, (username, password, role_id))
            
            if success:
                QMessageBox.information(self, "Успех", "Пользователь успешно добавлен")
                self.load_users()
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить пользователя")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении пользователя: {str(e)}")
        finally:
            db.disconnect()

    def show_change_password_dialog(self):
        """Показывает диалог смены пароля"""
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
        
        self.change_old_pass = QLineEdit()
        self.change_old_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.change_new_pass = QLineEdit()
        self.change_new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.change_confirm_pass = QLineEdit()
        self.change_confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addRow("Текущий пароль:", self.change_old_pass)
        layout.addRow("Новый пароль:", self.change_new_pass)
        layout.addRow("Подтвердите пароль:", self.change_confirm_pass)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.change_password(dialog, user_id))
        buttons.rejected.connect(dialog.reject)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def change_password(self, dialog, user_id):
        """Изменяет пароль пользователя"""
        old_pass = self.change_old_pass.text()
        new_pass = self.change_new_pass.text()
        confirm_pass = self.change_confirm_pass.text()
        
        # Валидация ввода
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
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к БД")
            return
            
        try:
            # Проверка текущего пароля
            check_query = """
            SELECT COUNT(*) FROM app_users 
            WHERE user_id = %s AND password_hash = crypt(%s, password_hash)
            """
            check_result = db.execute_query(check_query, (user_id, old_pass), fetch=True)
            
            if not check_result or check_result[0][0] == 0:
                QMessageBox.warning(self, "Ошибка", "Неверный текущий пароль")
                return
                
            # Обновление пароля
            update_query = """
            UPDATE app_users 
            SET password_hash = crypt(%s, gen_salt('bf'))
            WHERE user_id = %s
            """
            success = db.execute_query(update_query, (new_pass, user_id))
            
            if success:
                QMessageBox.information(self, "Успех", "Пароль успешно изменен")
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось изменить пароль")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении пароля: {str(e)}")
        finally:
            db.disconnect()

    def toggle_user_status(self):
        """Блокирует/разблокирует пользователя"""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя")
            return
            
        user_id = self.table.item(selected_row, 0).text()
        username = self.table.item(selected_row, 1).text()
        current_status = self.table.item(selected_row, 3).text()
        
        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к БД")
            return
            
        try:
            if current_status == "Активен":
                # Блокировка пользователя
                query = """
                UPDATE app_users 
                SET locked_until = NOW() + INTERVAL '30 days' 
                WHERE user_id = %s
                """
                action = "заблокирован"
            else:
                # Разблокировка пользователя
                query = "UPDATE app_users SET locked_until = NULL WHERE user_id = %s"
                action = "разблокирован"
            
            success = db.execute_query(query, (user_id,))
            
            if success:
                QMessageBox.information(self, "Успех", f"Пользователь {username} {action}")
                self.load_users()
            else:
                QMessageBox.warning(self, "Ошибка", f"Не удалось {action} пользователя")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении статуса: {str(e)}")
        finally:
            db.disconnect()