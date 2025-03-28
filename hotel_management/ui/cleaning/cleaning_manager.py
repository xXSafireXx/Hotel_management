from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHeaderView,
                            QTableWidgetItem, QPushButton, QHBoxLayout,
                            QMessageBox)
from PyQt6.QtCore import Qt
from hotel_management.database.connector import DatabaseConnector

class CleaningManager(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.load_cleaning_tasks()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица уборки с запретом редактирования
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Номер", "Этаж", "Категория", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.clicked.connect(self.load_cleaning_tasks)
        self.btn_mark_cleaned = QPushButton("Отметить убранным")
        self.btn_mark_cleaned.clicked.connect(self.mark_as_cleaned)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_mark_cleaned)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_cleaning_tasks(self):
        """Загрузка задач уборки с проверкой прав"""
        if self.parent and not self.parent.check_permission('manage_cleaning'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для просмотра уборки")
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            query = """
            SELECT r.room_id, r.room_id, r.floor, c.name, s.name
            FROM rooms r
            JOIN room_categories c ON r.category_id = c.category_id
            JOIN statuses s ON r.status_id = s.status_id
            WHERE r.status_id = 2
            ORDER BY r.room_id
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
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.disconnect()

    def mark_as_cleaned(self):
        """Отметка номера как убранного с проверкой прав"""
        if self.parent and not self.parent.check_permission('manage_cleaning'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для отметки уборки")
            return

        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите номер для отметки")
            return

        room_id = self.table.item(selected_row, 0).text()

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            # Обновление статуса номера
            update_room_query = "UPDATE rooms SET status_id = 1 WHERE room_id = %s"
            success = db.execute_query(update_room_query, (room_id,))

            if success:
                # Добавление записи об уборке
                insert_query = """
                INSERT INTO cleaning (room_id, status_id, cleaning_date)
                VALUES (%s, 1, NOW())
                """
                db.execute_query(insert_query, (room_id,))

                QMessageBox.information(self, "Успех", "Номер успешно отмечен как убранный")
                self.load_cleaning_tasks()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить статус номера")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении статуса: {str(e)}")
        finally:
            db.disconnect()