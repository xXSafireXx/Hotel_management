from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QHeaderView,
    QPushButton, QComboBox, QHBoxLayout, QMessageBox,
    QTableWidgetItem, QLabel
)
from hotel_management.database.connector import DatabaseConnector

class CleaningManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление уборкой")
        self.init_ui()
        self.load_tasks()

    def init_ui(self):
        layout = QVBoxLayout()

        # Фильтры
        filter_layout = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все", "Требует уборки", "В процессе", "Завершено"])
        btn_filter = QPushButton("Фильтровать", clicked=self.load_tasks)
        
        filter_layout.addWidget(QLabel("Статус:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(btn_filter)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Номер", "Этаж", "Статус", "Дата уборки"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить задачу")
        btn_complete = QPushButton("Отметить выполненной")
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_complete)

        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_tasks(self):
        db = DatabaseConnector()
        if db.connect():
            query = """
            SELECT c.cleaning_id, r.room_id, r.floor, s.name, c.cleaning_date
            FROM cleaning c
            JOIN rooms r ON c.room_id = r.room_id
            JOIN statuses s ON c.status_id = s.status_id
            """
            
            if self.status_filter.currentText() != "Все":
                query += f" WHERE s.name = '{self.status_filter.currentText()}'"
            
            result = db.execute_query(query, fetch=True)
            
            if result:
                self.table.setRowCount(len(result))
                for row_idx, row in enumerate(result):
                    for col_idx, cell in enumerate(row):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell)))
            db.disconnect() 