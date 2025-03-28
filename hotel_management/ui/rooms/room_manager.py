from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHeaderView,
                            QTableWidgetItem, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from hotel_management.database.connector import DatabaseConnector

class RoomManager(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.load_rooms()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица номеров с запретом редактирования
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Этаж", "Категория", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Кнопка обновления
        self.btn_refresh = QPushButton("Обновить список")
        self.btn_refresh.clicked.connect(self.load_rooms)

        layout.addWidget(self.table)
        layout.addWidget(self.btn_refresh)
        self.setLayout(layout)

    def load_rooms(self):
        """Загрузка данных о номерах из БД с проверкой прав"""
        if self.parent and not self.parent.check_permission('manage_rooms'):
            QMessageBox.warning(self, "Ошибка доступа", "Недостаточно прав для просмотра номеров")
            return

        db = DatabaseConnector()
        if not db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к базе данных")
            return

        try:
            query = """
            SELECT r.room_id, r.floor, c.name, s.name
            FROM rooms r
            JOIN room_categories c ON r.category_id = c.category_id
            JOIN statuses s ON r.status_id = s.status_id
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
                QMessageBox.information(self, "Информация", "Нет данных о номерах")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")
        finally:
            db.disconnect()