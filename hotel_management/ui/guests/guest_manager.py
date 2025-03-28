from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHeaderView,
                            QTableWidgetItem, QPushButton, QHBoxLayout,
                            QMessageBox, QDialog, QFormLayout, QLineEdit,
                            QDialogButtonBox)
from PyQt6.QtCore import Qt
from hotel_management.database.connector import DatabaseConnector

class GuestManager(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.load_guests()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица гостей с запретом редактирования
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "ФИО", "Телефон", "Возраст"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить гостя")
        self.btn_add.clicked.connect(self.show_add_dialog)
        self.btn_edit = QPushButton("Редактировать")
        self.btn_edit.clicked.connect(self.show_edit_dialog)
        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.clicked.connect(self.delete_guest)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_guests(self):
        """Загрузка списка гостей с проверкой прав"""
        if self.parent and not self.parent.check_permission('manage_guests'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для просмотра гостей")
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            query = "SELECT guest_id, full_name, phone_number, age FROM guests ORDER BY full_name"
            result = db.execute_query(query, fetch=True)

            if result:
                self.table.setRowCount(len(result))
                for row_idx, row in enumerate(result):
                    for col_idx, cell in enumerate(row):
                        item = QTableWidgetItem(str(cell) if cell else "")
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        self.table.setItem(row_idx, col_idx, item)
            else:
                self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке гостей: {str(e)}")
        finally:
            db.disconnect()

    def show_add_dialog(self):
        """Диалог добавления гостя"""
        if self.parent and not self.parent.check_permission('manage_guests'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для добавления гостей")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить гостя")
        dialog.setFixedSize(400, 300)

        layout = QFormLayout()

        self.full_name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.age_input = QLineEdit()

        layout.addRow("ФИО:", self.full_name_input)
        layout.addRow("Телефон:", self.phone_input)
        layout.addRow("Возраст:", self.age_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.add_guest(dialog))
        buttons.rejected.connect(dialog.reject)

        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def add_guest(self, dialog):
        """Добавление нового гостя через форму"""
        full_name = self.full_name_input.text().strip()
        phone = self.phone_input.text().strip()
        age = self.age_input.text().strip()

        if not full_name:
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно для заполнения")
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            query = "INSERT INTO guests (full_name, phone_number, age) VALUES (%s, %s, %s)"
            params = (
                full_name,
                phone if phone else None,
                int(age) if age.isdigit() else None
            )
            success = db.execute_query(query, params)

            if success:
                QMessageBox.information(self, "Успех", "Гость успешно добавлен")
                self.load_guests()
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить гостя")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Возраст должен быть числом")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении гостя: {str(e)}")
        finally:
            db.disconnect()

    def show_edit_dialog(self):
        """Диалог редактирования гостя"""
        if self.parent and not self.parent.check_permission('manage_guests'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для редактирования гостей")
            return

        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите гостя для редактирования")
            return

        guest_id = self.table.item(selected_row, 0).text()
        full_name = self.table.item(selected_row, 1).text()
        phone = self.table.item(selected_row, 2).text()
        age = self.table.item(selected_row, 3).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать гостя")
        dialog.setFixedSize(400, 300)

        layout = QFormLayout()

        self.edit_full_name = QLineEdit(full_name)
        self.edit_phone = QLineEdit(phone)
        self.edit_age = QLineEdit(age)

        layout.addRow("ФИО:", self.edit_full_name)
        layout.addRow("Телефон:", self.edit_phone)
        layout.addRow("Возраст:", self.edit_age)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.update_guest(dialog, guest_id))
        buttons.rejected.connect(dialog.reject)

        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def update_guest(self, dialog, guest_id):
        """Обновление данных гостя через форму"""
        full_name = self.edit_full_name.text().strip()
        phone = self.edit_phone.text().strip()
        age = self.edit_age.text().strip()

        if not full_name:
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно для заполнения")
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            query = """
            UPDATE guests 
            SET full_name = %s, phone_number = %s, age = %s 
            WHERE guest_id = %s
            """
            params = (
                full_name,
                phone if phone else None,
                int(age) if age.isdigit() else None,
                guest_id
            )
            success = db.execute_query(query, params)

            if success:
                QMessageBox.information(self, "Успех", "Данные гостя обновлены")
                self.load_guests()
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить данные гостя")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Возраст должен быть числом")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении гостя: {str(e)}")
        finally:
            db.disconnect()

    def delete_guest(self):
        """Удаление гостя с подтверждением"""
        if self.parent and not self.parent.check_permission('manage_guests'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для удаления гостей")
            return

        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите гостя для удаления")
            return

        guest_id = self.table.item(selected_row, 0).text()
        full_name = self.table.item(selected_row, 1).text()

        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            f"Вы уверены, что хотите удалить гостя {full_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            # Проверка на связанные бронирования
            check_query = "SELECT COUNT(*) FROM occupancy WHERE guest_id = %s"
            check_result = db.execute_query(check_query, (guest_id,), fetch=True)

            if check_result and check_result[0][0] > 0:
                QMessageBox.warning(self, "Ошибка", "Нельзя удалить гостя с активными бронированиями")
                return

            query = "DELETE FROM guests WHERE guest_id = %s"
            success = db.execute_query(query, (guest_id,))

            if success:
                QMessageBox.information(self, "Успех", "Гость успешно удален")
                self.load_guests()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить гостя")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении гостя: {str(e)}")
        finally:
            db.disconnect()