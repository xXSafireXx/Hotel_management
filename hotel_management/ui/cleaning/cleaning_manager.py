# Файл: cleaning_manager.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHeaderView,
                            QTableWidgetItem, QPushButton, QHBoxLayout,
                            QMessageBox, QComboBox, QLabel)
from PyQt6.QtCore import Qt
from datetime import datetime
from hotel_management.database.connector import DatabaseConnector

class CleaningManager(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.db = DatabaseConnector()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Секция добавления комнаты на уборку
        self.add_layout = QHBoxLayout()
        self.room_combo = QComboBox()
        self.add_layout.addWidget(QLabel("Добавить комнату:"))
        self.add_layout.addWidget(self.room_combo)
        
        self.btn_add = QPushButton("Добавить на уборку")
        self.btn_add.clicked.connect(self.add_to_cleaning)
        self.add_layout.addWidget(self.btn_add)
        
        self.layout.addLayout(self.add_layout)

        # Таблица комнат, требующих уборки
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Номер", "Этаж", "Категория"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Кнопки управления
        self.btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.clicked.connect(self.load_data)
        self.btn_mark_cleaned = QPushButton("Отметить убранным")
        self.btn_mark_cleaned.clicked.connect(self.mark_as_cleaned)

        self.btn_layout.addWidget(self.btn_refresh)
        self.btn_layout.addWidget(self.btn_mark_cleaned)

        self.layout.addWidget(self.table)
        self.layout.addLayout(self.btn_layout)
        self.setLayout(self.layout)

    def load_data(self):
        """Загрузка всех данных"""
        self.load_available_rooms()
        self.load_cleaning_tasks()

    def load_available_rooms(self):
        """Загрузка свободных комнат"""
        if not self.db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к БД")
            return

        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT r.room_id, r.floor, c.name 
                FROM rooms r
                JOIN room_categories c ON r.category_id = c.category_id
                WHERE r.status_id = 1
                ORDER BY r.room_id
            """)
            rooms = cursor.fetchall()
            cursor.close()

            self.room_combo.clear()
            for room_id, floor, category in rooms:
                self.room_combo.addItem(f"№{room_id} ({floor} этаж, {category})", room_id)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки комнат: {str(e)}")
        finally:
            self.db.disconnect()

    def load_cleaning_tasks(self):
        """Загрузка задач уборки"""
        if not self.db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к БД")
            return

        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                SELECT r.room_id, r.floor, c.name
                FROM cleaning cl
                JOIN rooms r ON cl.room_id = r.room_id
                JOIN room_categories c ON r.category_id = c.category_id
                WHERE cl.completed = FALSE
                ORDER BY r.room_id
            """)
            tasks = cursor.fetchall()
            cursor.close()

            self.table.setRowCount(len(tasks))
            for row, (room_id, floor, category) in enumerate(tasks):
                self.table.setItem(row, 0, QTableWidgetItem(str(room_id)))
                self.table.setItem(row, 1, QTableWidgetItem(str(room_id)))
                self.table.setItem(row, 2, QTableWidgetItem(str(floor)))
                self.table.setItem(row, 3, QTableWidgetItem(category))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки уборки: {str(e)}")
        finally:
            self.db.disconnect()

    def add_to_cleaning(self):
        """Добавление комнаты на уборку"""
        room_id = self.room_combo.currentData()
        if not room_id:
            QMessageBox.warning(self, "Ошибка", "Выберите комнату")
            return

        if not self.db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к БД")
            return

        try:
            cursor = self.db.connection.cursor()
            current_time = datetime.now()
            
            # 1. Добавляем запись в таблицу уборки
            cursor.execute("""
                INSERT INTO cleaning 
                (cleaning_id, room_id, status_id, staff_id, cleaning_date, completed, requested_at, cleaned_at)
                VALUES (
                    nextval('cleaning_cleaning_id_seq'),
                    %s, 
                    2,  -- status_id для "Требует уборки"
                    NULL,
                    %s,
                    FALSE,
                    %s,
                    NULL
                )
            """, (room_id, current_time, current_time))
            
            # 2. Обновляем статус комнаты на "Требует уборки" (2)
            cursor.execute("""
                UPDATE rooms
                SET status_id = 2
                WHERE room_id = %s
            """, (room_id,))
            
            self.db.connection.commit()
            cursor.close()
            
            QMessageBox.information(self, "Успех", "Комната добавлена на уборку")
            self.load_data()

        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка добавления: {str(e)}")
        finally:
            self.db.disconnect()

    def mark_as_cleaned(self):
        """Пометить комнату как убранную"""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите комнату")
            return

        room_id = self.table.item(selected_row, 0).text()

        if not self.db.connect():
            QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к БД")
            return

        try:
            cursor = self.db.connection.cursor()
            current_time = datetime.now()
            
            # 1. Обновляем запись уборки
            cursor.execute("""
                UPDATE cleaning 
                SET 
                    status_id = 1,  -- status_id для "Свободен"
                    cleaning_date = %s,
                    completed = TRUE, 
                    cleaned_at = %s
                WHERE room_id = %s AND completed = FALSE
            """, (current_time, current_time, room_id))
            
            # 2. Обновляем статус комнаты на "Свободен" (1)
            cursor.execute("""
                UPDATE rooms
                SET status_id = 1
                WHERE room_id = %s
            """, (room_id,))
            
            self.db.connection.commit()
            cursor.close()
            
            QMessageBox.information(self, "Успех", "Комната отмечена как убранная")
            self.load_data()

        except Exception as e:
            self.db.connection.rollback()
            QMessageBox.critical(self, "Ошибка", f"Ошибка отметки: {str(e)}")
        finally:
            self.db.disconnect()