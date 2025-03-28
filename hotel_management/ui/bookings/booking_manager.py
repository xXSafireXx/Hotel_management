from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHeaderView,
                            QTableWidgetItem, QPushButton, QHBoxLayout,
                            QMessageBox, QDialog, QFormLayout, QComboBox,
                            QDateEdit, QDialogButtonBox)
from PyQt6.QtCore import QDate, Qt
from hotel_management.database.connector import DatabaseConnector

class BookingManager(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.load_bookings()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица бронирований с запретом редактирования
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Гость", "Номер", "Заезд", "Выезд", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_new = QPushButton("Новое бронирование")
        self.btn_new.clicked.connect(self.show_new_booking_dialog)
        self.btn_cancel = QPushButton("Отменить бронь")
        self.btn_cancel.clicked.connect(self.cancel_booking)
        self.btn_check_in = QPushButton("Заселить")
        self.btn_check_in.clicked.connect(self.check_in_guest)
        self.btn_check_out = QPushButton("Выселить")
        self.btn_check_out.clicked.connect(self.check_out_guest)

        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_check_in)
        btn_layout.addWidget(self.btn_check_out)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_bookings(self):
        """Загрузка бронирований с проверкой прав"""
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для просмотра бронирований")
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            query = """
            SELECT b.occupancy_id, g.full_name, r.room_id, 
                   b.check_in_date, b.check_out_date, s.name
            FROM occupancy b
            JOIN guests g ON b.guest_id = g.guest_id
            JOIN rooms r ON b.room_id = r.room_id
            JOIN statuses s ON r.status_id = s.status_id
            ORDER BY b.check_in_date
            """
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
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке бронирований: {str(e)}")
        finally:
            db.disconnect()

    def show_new_booking_dialog(self):
        """Диалог создания нового бронирования"""
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для создания бронирований")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Новое бронирование")
        dialog.setFixedSize(500, 400)

        layout = QFormLayout()

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            # Загрузка данных для формы
            guests_query = "SELECT guest_id, full_name FROM guests ORDER BY full_name"
            guests = db.execute_query(guests_query, fetch=True)

            rooms_query = """
            SELECT r.room_id, r.floor, c.name 
            FROM rooms r
            JOIN room_categories c ON r.category_id = c.category_id
            WHERE r.status_id = 1
            ORDER BY r.room_id
            """
            rooms = db.execute_query(rooms_query, fetch=True)

            if not guests or not rooms:
                QMessageBox.warning(self, "Ошибка", "Нет доступных гостей или номеров")
                return

            self.guest_combo = QComboBox()
            for guest_id, full_name in guests:
                self.guest_combo.addItem(full_name, guest_id)

            self.room_combo = QComboBox()
            for room_id, floor, category in rooms:
                self.room_combo.addItem(f"{room_id} (Этаж {floor}, {category})", room_id)

            self.check_in_date = QDateEdit(QDate.currentDate())
            self.check_out_date = QDateEdit(QDate.currentDate().addDays(1))

            layout.addRow("Гость:", self.guest_combo)
            layout.addRow("Номер:", self.room_combo)
            layout.addRow("Дата заезда:", self.check_in_date)
            layout.addRow("Дата выезда:", self.check_out_date)

            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(lambda: self.create_booking(dialog))
            buttons.rejected.connect(dialog.reject)

            layout.addRow(buttons)
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.disconnect()

    def create_booking(self, dialog):
        """Создание нового бронирования через форму"""
        guest_id = self.guest_combo.currentData()
        room_id = self.room_combo.currentData()
        check_in = self.check_in_date.date().toString("yyyy-MM-dd")
        check_out = self.check_out_date.date().toString("yyyy-MM-dd")

        if check_in >= check_out:
            QMessageBox.warning(self, "Ошибка", "Дата выезда должна быть позже даты заезда")
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            # Проверка доступности номера
            availability_query = """
            SELECT COUNT(*) FROM occupancy 
            WHERE room_id = %s AND (
                (check_in_date <= %s AND check_out_date >= %s) OR
                (check_in_date <= %s AND check_out_date >= %s) OR
                (check_in_date >= %s AND check_out_date <= %s)
            )
            """
            availability_result = db.execute_query(
                availability_query, 
                (room_id, check_in, check_in, check_out, check_out, check_in, check_out),
                fetch=True
            )

            if availability_result and availability_result[0][0] > 0:
                QMessageBox.warning(self, "Ошибка", "Номер уже занят на выбранные даты")
                return

            # Создание бронирования
            query = """
            INSERT INTO occupancy (guest_id, room_id, check_in_date, check_out_date)
            VALUES (%s, %s, %s, %s)
            """
            success = db.execute_query(query, (guest_id, room_id, check_in, check_out))

            if success:
                # Обновление статуса номера
                update_room_query = "UPDATE rooms SET status_id = 3 WHERE room_id = %s"
                db.execute_query(update_room_query, (room_id,))

                QMessageBox.information(self, "Успех", "Бронирование успешно создано")
                self.load_bookings()
                dialog.close()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось создать бронирование")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании бронирования: {str(e)}")
        finally:
            db.disconnect()

    def cancel_booking(self):
        """Отмена бронирования с подтверждением"""
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для отмены бронирований")
            return

        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите бронирование для отмены")
            return

        booking_id = self.table.item(selected_row, 0).text()
        room_id = self.table.item(selected_row, 2).text()
        guest_name = self.table.item(selected_row, 1).text()

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите отменить бронирование для {guest_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            # Удаление бронирования
            query = "DELETE FROM occupancy WHERE occupancy_id = %s"
            success = db.execute_query(query, (booking_id,))

            if success:
                # Обновление статуса номера
                update_room_query = "UPDATE rooms SET status_id = 1 WHERE room_id = %s"
                db.execute_query(update_room_query, (room_id,))

                QMessageBox.information(self, "Успех", "Бронирование успешно отменено")
                self.load_bookings()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось отменить бронирование")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отмене бронирования: {str(e)}")
        finally:
            db.disconnect()

    def check_in_guest(self):
        """Заселение гостя с проверкой прав"""
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для заселения гостей")
            return

        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите бронирование для заселения")
            return

        booking_id = self.table.item(selected_row, 0).text()
        room_id = self.table.item(selected_row, 2).text()
        guest_name = self.table.item(selected_row, 1).text()

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            # Обновление статуса номера
            update_room_query = "UPDATE rooms SET status_id = 4 WHERE room_id = %s"
            success = db.execute_query(update_room_query, (room_id,))

            if success:
                QMessageBox.information(self, "Успех", f"Гость {guest_name} успешно заселен")
                self.load_bookings()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось заселить гостя")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при заселении гостя: {str(e)}")
        finally:
            db.disconnect()

    def check_out_guest(self):
        """Выселение гостя с проверкой прав"""
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для выселения гостей")
            return

        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите бронирование для выселения")
            return

        booking_id = self.table.item(selected_row, 0).text()
        room_id = self.table.item(selected_row, 2).text()
        guest_name = self.table.item(selected_row, 1).text()

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            # Обновление статуса номера
            update_room_query = "UPDATE rooms SET status_id = 2 WHERE room_id = %s"
            success = db.execute_query(update_room_query, (room_id,))

            if success:
                # Добавление записи об уборке
                cleaning_query = """
                INSERT INTO cleaning (room_id, status_id, cleaning_date)
                VALUES (%s, 1, NOW())
                """
                db.execute_query(cleaning_query, (room_id,))

                QMessageBox.information(self, "Успех", f"Гость {guest_name} успешно выселен")
                self.load_bookings()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось выселить гостя")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выселении гостя: {str(e)}")
        finally:
            db.disconnect()