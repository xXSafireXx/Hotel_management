from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QLineEdit,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from hotel_management.database.connector import DatabaseConnector

class GuestManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление гостями")
        self.init_ui()
        self.load_guests()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица гостей
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "ФИО", "Телефон"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить гостя")
        btn_add.setFixedHeight(40)
        btn_add.clicked.connect(self.show_add_guest_dialog)
        
        btn_edit = QPushButton("Редактировать")
        btn_edit.setFixedHeight(40)
        btn_edit.clicked.connect(self.edit_guest)
        
        btn_delete = QPushButton("Удалить")
        btn_delete.setFixedHeight(40)
        btn_delete.clicked.connect(self.delete_guest)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def create_phone_input(self):
        """Создает поле ввода телефона с маской"""
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("+7 (999) 123-45-67")
        
        # Устанавливаем валидатор для телефона
        regex = QRegularExpression(r"^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$")
        validator = QRegularExpressionValidator(regex)
        phone_input.setValidator(validator)
        
        # Устанавливаем маску ввода
        phone_input.setInputMask("+7 (999) 999-99-99;_")
        
        return phone_input

    def format_phone_number(self, phone):
        """Форматирует номер телефона для отображения"""
        if not phone:
            return ""
        
        # Удаляем все нецифровые символы
        digits = ''.join(filter(str.isdigit, phone))
        
        # Форматируем по маске, если достаточно цифр
        if len(digits) == 11 and digits.startswith('7'):
            return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        elif len(digits) == 11 and digits.startswith('8'):
            return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        
        return phone  # Возвращаем как есть, если не соответствует формату

    def show_add_guest_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить гостя")
        dialog.setFixedSize(400, 200)
        
        layout = QFormLayout()
        
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Иванов Иван Иванович")
        
        self.phone_input = self.create_phone_input()
        
        layout.addRow("ФИО:", self.full_name_input)
        layout.addRow("Телефон:", self.phone_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(lambda: self.add_guest(dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def add_guest(self, dialog):
        full_name = self.full_name_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not full_name:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО гостя")
            return
            
        # Проверяем корректность телефона
        if phone and len(phone.replace("_", "").replace(" ", "")) < 16:
            QMessageBox.warning(self, "Ошибка", "Введите корректный номер телефона")
            return
            
        db = DatabaseConnector()
        if db.connect():
            query = """
            INSERT INTO guests (full_name, phone_number)
            VALUES (%s, %s)
            RETURNING guest_id
            """
            result = db.execute_query(
                query,
                (full_name, phone if phone else None),
                fetch=True
            )
            
            if result:
                QMessageBox.information(
                    self, 
                    "Успех", 
                    f"Гость {full_name} добавлен\nID: {result[0][0]}"
                )
                self.load_guests()
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить гостя")
                
            db.disconnect()

    def edit_guest(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите гостя из списка")
            return
            
        guest_id = self.table.item(selected_row, 0).text()
        full_name = self.table.item(selected_row, 1).text()
        phone = self.table.item(selected_row, 2).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование гостя {full_name}")
        dialog.setFixedSize(400, 200)
        
        layout = QFormLayout()
        
        full_name_edit = QLineEdit(full_name)
        
        phone_edit = self.create_phone_input()
        phone_edit.setText(phone)
        
        layout.addRow("ФИО:", full_name_edit)
        layout.addRow("Телефон:", phone_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(lambda: self.update_guest(
            dialog, guest_id, 
            full_name_edit.text().strip(),
            phone_edit.text().strip()
        ))
        buttons.rejected.connect(dialog.reject)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def update_guest(self, dialog, guest_id, full_name, phone):
        if not full_name:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО гостя")
            return
            
        # Проверяем корректность телефона
        if phone and len(phone.replace("_", "").replace(" ", "")) < 16:
            QMessageBox.warning(self, "Ошибка", "Введите корректный номер телефона")
            return
            
        db = DatabaseConnector()
        if db.connect():
            query = """
            UPDATE guests 
            SET full_name = %s, 
                phone_number = %s
            WHERE guest_id = %s
            """
            success = db.execute_query(
                query,
                (full_name, phone if phone else None, guest_id)
            )
            
            if success:
                QMessageBox.information(self, "Успех", "Данные гостя обновлены")
                self.load_guests()
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить данные")
                
            db.disconnect()

    def load_guests(self):
        db = DatabaseConnector()
        if db.connect():
            query = "SELECT guest_id, full_name, phone_number FROM guests ORDER BY full_name"
            result = db.execute_query(query, fetch=True)
            
            if result:
                self.table.setRowCount(len(result))
                for row_idx, row in enumerate(result):
                    guest_id, full_name, phone = row
                    # Форматируем телефон для отображения
                    formatted_phone = self.format_phone_number(phone) if phone else ""
                    
                    self.table.setItem(row_idx, 0, QTableWidgetItem(str(guest_id)))
                    self.table.setItem(row_idx, 1, QTableWidgetItem(full_name))
                    self.table.setItem(row_idx, 2, QTableWidgetItem(formatted_phone))
            db.disconnect()

    def delete_guest(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите гостя из списка")
            return
            
        guest_id = self.table.item(selected_row, 0).text()
        full_name = self.table.item(selected_row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить гостя {full_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db = DatabaseConnector()
            if db.connect():
                # Проверяем, есть ли активные бронирования
                booking_check = db.execute_query(
                    "SELECT COUNT(*) FROM occupancy WHERE guest_id = %s AND check_out_date >= CURRENT_DATE",
                    (guest_id,),
                    fetch=True
                )
                
                if booking_check and booking_check[0][0] > 0:
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        "Нельзя удалить гостя с активными бронированиями"
                    )
                    db.disconnect()
                    return
                
                query = "DELETE FROM guests WHERE guest_id = %s"
                success = db.execute_query(query, (guest_id,))
                
                if success:
                    QMessageBox.information(self, "Успех", "Гость удален")
                    self.load_guests()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить гостя")
                    
                db.disconnect()