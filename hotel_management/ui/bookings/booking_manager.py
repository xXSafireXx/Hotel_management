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
        self.initialize_user_interface()
        self.load_active_bookings()

    def initialize_user_interface(self):
        main_layout = QVBoxLayout()

        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(6)
        self.bookings_table.setHorizontalHeaderLabels(
            ["ID бронирования", "ФИО гостя", "Номер комнаты", 
             "Дата заезда", "Дата выезда", "Статус бронирования"]
        )
        self.bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.bookings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        buttons_layout = QHBoxLayout()
        
        self.new_booking_button = QPushButton("Создать новое бронирование")
        self.new_booking_button.clicked.connect(self.show_new_booking_dialog)
        
        self.cancel_booking_button = QPushButton("Отменить бронирование")
        self.cancel_booking_button.clicked.connect(self.cancel_current_booking)
        
        self.check_in_button = QPushButton("Зарегистрировать заселение")
        self.check_in_button.clicked.connect(self.register_guest_check_in)
        
        self.check_out_button = QPushButton("Оформить выселение")
        self.check_out_button.clicked.connect(self.process_guest_check_out)

        buttons_layout.addWidget(self.new_booking_button)
        buttons_layout.addWidget(self.cancel_booking_button)
        buttons_layout.addWidget(self.check_in_button)
        buttons_layout.addWidget(self.check_out_button)

        main_layout.addWidget(self.bookings_table)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def load_active_bookings(self):
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(
                self, 
                "Ограничение доступа", 
                "У вас недостаточно прав для просмотра информации о бронированиях"
            )
            return

        database_connection = DatabaseConnector()
        if not database_connection.connect():
            QMessageBox.warning(
                self, 
                "Ошибка подключения", 
                "Не удалось установить соединение с базой данных"
            )
            return

        try:
            active_bookings_query = """
            SELECT 
                occupancy.occupancy_id, 
                guests.full_name, 
                rooms.room_id, 
                occupancy.check_in_date, 
                occupancy.check_out_date, 
                occupancy.status
            FROM occupancy
            JOIN guests ON occupancy.guest_id = guests.guest_id
            JOIN rooms ON occupancy.room_id = rooms.room_id
            WHERE occupancy.status IN ('booked', 'checked_in')
            AND occupancy.check_out_date >= CURRENT_DATE
            ORDER BY occupancy.check_in_date
            """
            
            database_cursor = database_connection.connection.cursor()
            database_cursor.execute(active_bookings_query)
            active_bookings_data = database_cursor.fetchall()

            self.bookings_table.setRowCount(len(active_bookings_data))
            
            for row_index, booking_record in enumerate(active_bookings_data):
                for column_index in range(5):
                    table_item = QTableWidgetItem(str(booking_record[column_index]))
                    table_item.setFlags(table_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.bookings_table.setItem(row_index, column_index, table_item)
                
                status_display_text = self.translate_booking_status(booking_record[5])
                status_item = QTableWidgetItem(status_display_text)
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.bookings_table.setItem(row_index, 5, status_item)
            
            database_cursor.close()
        except Exception as database_error:
            QMessageBox.critical(
                self, 
                "Ошибка загрузки данных", 
                f"Произошла ошибка при загрузке бронирований: {str(database_error)}"
            )
        finally:
            database_connection.disconnect()

    def translate_booking_status(self, status_code):
        status_translations = {
            'booked': 'Забронирован',
            'checked_in': 'Гость заселен',
            'checked_out': 'Выселен',
            'cancelled': 'Отменен'
        }
        return status_translations.get(status_code, 'Неизвестный статус')

    def show_new_booking_dialog(self):
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(
                self, 
                "Ограничение доступа", 
                "У вас недостаточно прав для создания новых бронирований"
            )
            return

        booking_creation_dialog = QDialog(self)
        booking_creation_dialog.setWindowTitle("Создание нового бронирования")
        booking_creation_dialog.setFixedSize(500, 400)

        dialog_layout = QFormLayout()

        database_connection = DatabaseConnector()
        if not database_connection.connect():
            QMessageBox.warning(
                self, 
                "Ошибка подключения", 
                "Не удалось установить соединение с базой данных"
            )
            return

        try:
            database_cursor = database_connection.connection.cursor()
            
            database_cursor.execute("SELECT guest_id, full_name FROM guests ORDER BY full_name")
            available_guests = database_cursor.fetchall()

            database_cursor.execute("""
                SELECT rooms.room_id, rooms.floor, room_categories.name 
                FROM rooms
                JOIN room_categories ON rooms.category_id = room_categories.category_id
                WHERE rooms.room_id NOT IN (
                    SELECT room_id FROM occupancy 
                    WHERE status IN ('booked', 'checked_in')
                    AND check_out_date >= CURRENT_DATE
                )
                ORDER BY rooms.room_id
            """)
            available_rooms = database_cursor.fetchall()

            if not available_guests or not available_rooms:
                QMessageBox.warning(
                    self, 
                    "Недостаточно данных", 
                    "В системе нет доступных гостей или свободных номеров"
                )
                return

            self.guest_selection = QComboBox()
            for guest_id, guest_name in available_guests:
                self.guest_selection.addItem(guest_name, guest_id)

            self.room_selection = QComboBox()
            for room_id, floor_number, room_category in available_rooms:
                self.room_selection.addItem(
                    f"Номер {room_id} (Этаж {floor_number}, {room_category})", 
                    room_id
                )

            self.check_in_date_input = QDateEdit(QDate.currentDate())
            self.check_out_date_input = QDateEdit(QDate.currentDate().addDays(1))

            dialog_layout.addRow("Выберите гостя:", self.guest_selection)
            dialog_layout.addRow("Выберите номер:", self.room_selection)
            dialog_layout.addRow("Дата заезда:", self.check_in_date_input)
            dialog_layout.addRow("Дата выезда:", self.check_out_date_input)

            confirmation_buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | 
                QDialogButtonBox.StandardButton.Cancel
            )
            confirmation_buttons.accepted.connect(
                lambda: self.create_new_booking(booking_creation_dialog)
            )
            confirmation_buttons.rejected.connect(booking_creation_dialog.reject)

            dialog_layout.addRow(confirmation_buttons)
            booking_creation_dialog.setLayout(dialog_layout)
            booking_creation_dialog.exec()
        except Exception as dialog_error:
            QMessageBox.critical(
                self, 
                "Ошибка диалога", 
                f"Ошибка при отображении диалога: {str(dialog_error)}"
            )
        finally:
            database_cursor.close()
            database_connection.disconnect()

    def create_new_booking(self, dialog_window):
        selected_guest_id = self.guest_selection.currentData()
        selected_room_id = self.room_selection.currentData()
        check_in_date = self.check_in_date_input.date().toString("yyyy-MM-dd")
        check_out_date = self.check_out_date_input.date().toString("yyyy-MM-dd")

        if check_in_date >= check_out_date:
            QMessageBox.warning(
                self, 
                "Некорректные даты", 
                "Дата выезда должна быть позже даты заезда"
            )
            return

        database_connection = DatabaseConnector()
        if not database_connection.connect():
            QMessageBox.warning(
                self, 
                "Ошибка подключения", 
                "Не удалось установить соединение с базой данных"
            )
            return

        try:
            database_cursor = database_connection.connection.cursor()
            
            database_cursor.execute("""
                SELECT COUNT(*) 
                FROM occupancy 
                WHERE room_id = %s 
                AND status IN ('booked', 'checked_in')
                AND (
                    (check_in_date <= %s AND check_out_date >= %s) OR
                    (check_in_date <= %s AND check_out_date >= %s) OR
                    (check_in_date >= %s AND check_out_date <= %s)
                )
            """, (
                selected_room_id, 
                check_in_date, check_in_date,
                check_out_date, check_out_date,
                check_in_date, check_out_date
            ))
            
            if database_cursor.fetchone()[0] > 0:
                QMessageBox.warning(
                    self, 
                    "Номер занят", 
                    "Выбранный номер уже забронирован на указанные даты"
                )
                return

            database_cursor.execute("""
                INSERT INTO occupancy 
                (guest_id, room_id, check_in_date, check_out_date, status)
                VALUES (%s, %s, %s, %s, 'booked')
            """, (selected_guest_id, selected_room_id, check_in_date, check_out_date))

            database_connection.connection.commit()
            QMessageBox.information(
                self, 
                "Бронирование создано", 
                "Новое бронирование успешно зарегистрировано"
            )
            self.load_active_bookings()
            dialog_window.close()
        except Exception as creation_error:
            database_connection.connection.rollback()
            QMessageBox.critical(
                self, 
                "Ошибка создания", 
                f"Ошибка при создании бронирования: {str(creation_error)}"
            )
        finally:
            database_cursor.close()
            database_connection.disconnect()

    def cancel_current_booking(self):
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(
                self, 
                "Ограничение доступа", 
                "У вас недостаточно прав для отмены бронирований"
            )
            return

        selected_booking_row = self.bookings_table.currentRow()
        if selected_booking_row == -1:
            QMessageBox.warning(
                self, 
                "Не выбрано бронирование", 
                "Пожалуйста, выберите бронирование для отмены"
            )
            return

        booking_id = self.bookings_table.item(selected_booking_row, 0).text()
        guest_name = self.bookings_table.item(selected_booking_row, 1).text()

        confirmation_result = QMessageBox.question(
            self,
            "Подтверждение отмены",
            f"Вы действительно хотите отменить бронирование для {guest_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmation_result == QMessageBox.StandardButton.No:
            return

        database_connection = DatabaseConnector()
        if not database_connection.connect():
            QMessageBox.warning(
                self, 
                "Ошибка подключения", 
                "Не удалось установить соединение с базой данных"
            )
            return

        try:
            database_cursor = database_connection.connection.cursor()
            
            database_cursor.execute("""
                UPDATE occupancy 
                SET status = 'cancelled'
                WHERE occupancy_id = %s
                AND status IN ('booked', 'checked_in')
            """, (booking_id,))
            
            database_connection.connection.commit()
            QMessageBox.information(
                self, 
                "Бронирование отменено", 
                "Выбранное бронирование успешно отменено"
            )
            self.load_active_bookings()
        except Exception as cancellation_error:
            database_connection.connection.rollback()
            QMessageBox.critical(
                self, 
                "Ошибка отмены", 
                f"Ошибка при отмене бронирования: {str(cancellation_error)}"
            )
        finally:
            database_cursor.close()
            database_connection.disconnect()

    def register_guest_check_in(self):
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(
                self, 
                "Ограничение доступа", 
                "У вас недостаточно прав для регистрации заселений"
            )
            return

        selected_booking_row = self.bookings_table.currentRow()
        if selected_booking_row == -1:
            QMessageBox.warning(
                self, 
                "Не выбрано бронирование", 
                "Пожалуйста, выберите бронирование для регистрации заселения"
            )
            return

        booking_id = self.bookings_table.item(selected_booking_row, 0).text()
        guest_name = self.bookings_table.item(selected_booking_row, 1).text()

        database_connection = DatabaseConnector()
        if not database_connection.connect():
            QMessageBox.warning(
                self, 
                "Ошибка подключения", 
                "Не удалось установить соединение с базой данных"
            )
            return

        try:
            database_cursor = database_connection.connection.cursor()
            
            database_cursor.execute("""
                UPDATE occupancy 
                SET status = 'checked_in'
                WHERE occupancy_id = %s
                AND status = 'booked'
            """, (booking_id,))
            
            database_connection.connection.commit()
            QMessageBox.information(
                self, 
                "Заселение зарегистрировано", 
                f"Гость {guest_name} успешно зарегистрирован в системе"
            )
            self.load_active_bookings()
        except Exception as check_in_error:
            database_connection.connection.rollback()
            QMessageBox.critical(
                self, 
                "Ошибка регистрации", 
                f"Ошибка при регистрации заселения: {str(check_in_error)}"
            )
        finally:
            database_cursor.close()
            database_connection.disconnect()

    def process_guest_check_out(self):
        if self.parent and not self.parent.check_permission('manage_bookings'):
            QMessageBox.warning(
                self, 
                "Ограничение доступа", 
                "У вас недостаточно прав для оформления выселений"
            )
            return

        selected_booking_row = self.bookings_table.currentRow()
        if selected_booking_row == -1:
            QMessageBox.warning(
                self, 
                "Не выбрано бронирование", 
                "Пожалуйста, выберите бронирование для оформления выселения"
            )
            return

        booking_id = self.bookings_table.item(selected_booking_row, 0).text()
        room_id = self.bookings_table.item(selected_booking_row, 2).text()
        guest_name = self.bookings_table.item(selected_booking_row, 1).text()

        database_connection = DatabaseConnector()
        if not database_connection.connect():
            QMessageBox.warning(
                self, 
                "Ошибка подключения", 
                "Не удалось установить соединение с базой данных"
            )
            return

        try:
            database_cursor = database_connection.connection.cursor()
            
            database_cursor.execute("""
                SELECT check_in_date 
                FROM occupancy 
                WHERE occupancy_id = %s
            """, (booking_id,))
            check_in_date = database_cursor.fetchone()[0]
            
            current_date = QDate.currentDate()
            check_out_date = current_date.toString("yyyy-MM-dd")
            
            if check_out_date <= check_in_date.strftime("%Y-%m-%d"):
                check_out_date = current_date.addDays(1).toString("yyyy-MM-dd")
            
            database_cursor.execute("""
                UPDATE occupancy 
                SET 
                    status = 'checked_out',
                    check_out_date = %s
                WHERE occupancy_id = %s
                AND status = 'checked_in'
            """, (check_out_date, booking_id))
            
            database_cursor.execute("""
                INSERT INTO cleaning 
                (room_id, cleaning_date, completed)
                VALUES (%s, NOW(), FALSE)
            """, (room_id,))
            
            database_connection.connection.commit()
            QMessageBox.information(
                self, 
                "Выселение оформлено", 
                f"Гость {guest_name} успешно выселен из номера"
            )
            self.load_active_bookings()
        except Exception as check_out_error:
            database_connection.connection.rollback()
            QMessageBox.critical(
                self, 
                "Ошибка выселения", 
                f"Ошибка при оформлении выселения: {str(check_out_error)}"
            )
        finally:
            database_cursor.close()
            database_connection.disconnect()