from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QHeaderView, QPushButton, QDateEdit, QLabel,
    QTableWidgetItem, QMessageBox, QComboBox,
    QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import QDate
from hotel_management.database.connector import DatabaseConnector

class BookingManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление бронированиями")
        self.init_ui()
        self.load_bookings()

    def init_ui(self):
        layout = QVBoxLayout()

        # Фильтры
        filter_layout = QHBoxLayout()
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_to = QDateEdit(QDate.currentDate().addDays(30))
        btn_filter = QPushButton("Фильтровать")
        btn_filter.clicked.connect(self.load_bookings)
        
        filter_layout.addWidget(QLabel("С:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("По:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(btn_filter)

        # Таблица бронирований
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Гость", "Номер", "Заезд", "Выезд", "Статус"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить бронь")
        btn_add.clicked.connect(self.show_add_booking_dialog)
        btn_remove = QPushButton("Отменить бронь")
        btn_remove.clicked.connect(self.cancel_booking)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)

        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_bookings(self):
        db = DatabaseConnector()
        if db.connect():
            query = """
            SELECT o.occupancy_id, g.full_name, r.room_id, 
                   o.check_in_date, o.check_out_date, s.name
            FROM occupancy o
            JOIN guests g ON o.guest_id = g.guest_id
            JOIN rooms r ON o.room_id = r.room_id
            JOIN statuses s ON r.status_id = s.status_id
            WHERE o.check_in_date BETWEEN %s AND %s
            ORDER BY o.check_in_date
            """
            result = db.execute_query(
                query,
                (
                    self.date_from.date().toPyDate(),
                    self.date_to.date().toPyDate()
                ),
                fetch=True
            )
            
            if result:
                self.table.setRowCount(len(result))
                for row_idx, row in enumerate(result):
                    for col_idx, cell in enumerate(row):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell)))
            db.disconnect()

    def show_add_booking_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Новое бронирование")
        dialog.setFixedSize(600, 300)
        
        layout = QFormLayout()
        
        # Выбор гостя
        self.guest_combo = QComboBox()
        self.load_guests()
        
        # Выбор номера
        self.room_combo = QComboBox()
        self.load_available_rooms()
        
        # Даты бронирования
        self.check_in = QDateEdit(QDate.currentDate())
        self.check_out = QDateEdit(QDate.currentDate().addDays(1))
        
        layout.addRow("Гость:", self.guest_combo)
        layout.addRow("Номер:", self.room_combo)
        layout.addRow("Дата заезда:", self.check_in)
        layout.addRow("Дата выезда:", self.check_out)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.add_booking(dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addRow(buttons)
        dialog.setLayout(layout)
        dialog.exec()

    def load_guests(self):
        """Загружает список всех гостей с проверкой на None"""
        db = DatabaseConnector()
        if db.connect():
            try:
                # Получаем всех гостей, включая тех у кого нет телефона
                result = db.execute_query(
                    "SELECT guest_id, full_name, phone_number FROM guests ORDER BY full_name",
                    fetch=True
                )
                
                self.guest_combo.clear()
                
                if result:
                    for guest_id, full_name, phone in result:
                        # Форматируем отображение с учетом отсутствия телефона
                        phone_display = phone if phone else "телефон не указан"
                        display_text = f"{full_name} (ID: {guest_id}, Тел: {phone_display})"
                        self.guest_combo.addItem(display_text, guest_id)
            except Exception as e:
                print(f"Ошибка при загрузке гостей: {e}")
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список гостей")
            finally:
                db.disconnect()

    def load_available_rooms(self):
        """Загружает список доступных номеров"""
        db = DatabaseConnector()
        if db.connect():
            try:
                result = db.execute_query(
                    "SELECT room_id FROM rooms WHERE status_id = 1 ORDER BY room_id",
                    fetch=True
                )
                self.room_combo.clear()
                if result:
                    for row in result:
                        self.room_combo.addItem(f"Номер {row[0]}", row[0])
            except Exception as e:
                print(f"Ошибка при загрузке номеров: {e}")
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список номеров")
            finally:
                db.disconnect()

    def add_booking(self, dialog):
        """Добавляет новое бронирование"""
        guest_id = self.guest_combo.currentData()
        room_id = self.room_combo.currentData()
        check_in = self.check_in.date().toPyDate()
        check_out = self.check_out.date().toPyDate()
        
        # Валидация данных
        if not guest_id:
            QMessageBox.warning(self, "Ошибка", "Выберите гостя")
            return
            
        if not room_id:
            QMessageBox.warning(self, "Ошибка", "Выберите номер")
            return
            
        if check_in >= check_out:
            QMessageBox.warning(self, "Ошибка", "Дата выезда должна быть позже даты заезда")
            return
            
        db = DatabaseConnector()
        if db.connect():
            try:
                # Проверяем доступность номера
                check_query = """
                SELECT COUNT(*) FROM occupancy 
                WHERE room_id = %s AND (
                    (check_in_date <= %s AND check_out_date >= %s) OR
                    (check_in_date <= %s AND check_out_date >= %s) OR
                    (check_in_date >= %s AND check_out_date <= %s)
                )
                """
                result = db.execute_query(
                    check_query,
                    (room_id, check_in, check_in, check_out, check_out, check_in, check_out),
                    fetch=True
                )
                
                if result and result[0][0] > 0:
                    QMessageBox.warning(self, "Ошибка", "Номер уже занят на выбранные даты")
                    return
                    
                # Добавляем бронирование
                insert_query = """
                INSERT INTO occupancy (guest_id, room_id, check_in_date, check_out_date)
                VALUES (%s, %s, %s, %s)
                """
                success = db.execute_query(
                    insert_query,
                    (guest_id, room_id, check_in, check_out)
                )
                
                if success:
                    # Обновляем статус номера
                    db.execute_query(
                        "UPDATE rooms SET status_id = 4 WHERE room_id = %s",
                        (room_id,)
                    )
                    QMessageBox.information(self, "Успех", "Бронирование добавлено")
                    self.load_bookings()
                    dialog.close()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить бронирование")
            except Exception as e:
                print(f"Ошибка при добавлении бронирования: {e}")
                QMessageBox.warning(self, "Ошибка", f"Произошла ошибка: {str(e)}")
            finally:
                db.disconnect()

    def cancel_booking(self):
        """Отменяет выбранное бронирование"""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите бронирование для отмены")
            return
            
        booking_id = self.table.item(selected_row, 0).text()
        room_id = self.table.item(selected_row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите отменить это бронирование?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db = DatabaseConnector()
            if db.connect():
                try:
                    # Удаляем бронирование
                    delete_query = "DELETE FROM occupancy WHERE occupancy_id = %s"
                    success = db.execute_query(delete_query, (booking_id,))
                    
                    if success:
                        # Возвращаем номер в доступные
                        db.execute_query(
                            "UPDATE rooms SET status_id = 1 WHERE room_id = %s",
                            (room_id,)
                        )
                        QMessageBox.information(self, "Успех", "Бронирование отменено")
                        self.load_bookings()
                    else:
                        QMessageBox.warning(self, "Ошибка", "Не удалось отменить бронирование")
                except Exception as e:
                    print(f"Ошибка при отмене бронирования: {e}")
                    QMessageBox.warning(self, "Ошибка", f"Произошла ошибка: {str(e)}")
                finally:
                    db.disconnect()