from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QPushButton,
                            QHeaderView, QInputDialog, QLineEdit, QDoubleSpinBox)
from database.connector import DatabaseConnector

class ServiceManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление услугами")
        self.init_ui()
        self.load_services()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица услуг
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Цена"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Форма добавления
        self.service_name = QLineEdit(placeholderText="Название услуги")
        self.service_price = QDoubleSpinBox()
        self.service_price.setPrefix("₽ ")
        self.service_price.setMaximum(100000)
        
        self.btn_add = QPushButton("Добавить услугу", clicked=self.add_service)
        self.btn_remove = QPushButton("Удалить услугу", clicked=self.remove_service)

        layout.addWidget(self.table)
        layout.addWidget(QLabel("Новая услуга:"))
        layout.addWidget(self.service_name)
        layout.addWidget(self.service_price)
        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_remove)
        self.setLayout(layout)

    def load_services(self):
        db = DatabaseConnector()
        if db.connect():
            services = db.execute_query(
                "SELECT service_id, name, price FROM services ORDER BY service_id",
                fetch=True
            )
            if services:
                self.table.setRowCount(len(services))
                for row_idx, row in enumerate(services):
                    for col_idx, cell in enumerate(row):
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(cell)))
            db.disconnect()

    def add_service(self):
        name = self.service_name.text().strip()
        price = self.service_price.value()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название услуги")
            return

        db = DatabaseConnector()
        if db.connect():
            db.execute_query(
                "INSERT INTO services (name, price) VALUES (%s, %s)",
                (name, price)
            )
            db.disconnect()
            self.load_services()
            self.service_name.clear()
            self.service_price.setValue(0)

    def remove_service(self):
        selected = self.table.currentRow()
        if selected >= 0:
            service_id = self.table.item(selected, 0).text()
            db = DatabaseConnector()
            if db.connect():
                db.execute_query(
                    "DELETE FROM services WHERE service_id = %s",
                    (service_id,)
                )
                db.disconnect()
                self.load_services()