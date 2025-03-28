from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget,
                            QPushButton,QTableWidgetItem, QHeaderView)
from database.connector import DatabaseConnector
from database.queries import RoomQueries

class RoomManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление номерами")
        self.init_ui()
        self.load_rooms()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Этаж", "Категория", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_rooms(self):
        db = DatabaseConnector()
        if db.connect():
            result = db.execute_query(RoomQueries.GET_ALL, fetch=True)
            if result:
                self.table.setRowCount(len(result))
                for row_idx, row in enumerate(result):
                    for col_idx, cell in enumerate(row):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell)))
            db.disconnect()