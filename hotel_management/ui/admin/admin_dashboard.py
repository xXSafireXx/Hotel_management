from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PyQt6.QtGui import QIcon
from hotel_management.ui.rooms.room_manager import RoomManager
from hotel_management.ui.guests.guest_manager import GuestManager
from hotel_management.ui.bookings.booking_manager import BookingManager
from hotel_management.ui.cleaning.cleaning_manager import CleaningManager
from hotel_management.ui.admin.user_management import UserManagement
from hotel_management.config import ROLES_CONFIG

class AdminDashboard(QMainWindow):
    def __init__(self, user_id, role_id):
        super().__init__()
        self.user_id = user_id
        self.role_id = role_id
        self.setWindowTitle(f"Отель Grand Plaza - {ROLES_CONFIG['roles'][role_id]['name']}")
        self.setMinimumSize(1200, 800)
        self.setWindowIcon(QIcon('hotel_icon.ico'))
        self.init_ui()
        
    def init_ui(self):
        tabs = QTabWidget()
        
        # Создаем только доступные вкладки
        if self.check_permission('all') or self.check_permission('manage_rooms'):
            self.room_manager = RoomManager(self.role_id)
            tabs.addTab(self.room_manager, "Номера")
        
        if self.check_permission('all') or self.check_permission('manage_guests'):
            self.guest_manager = GuestManager(self.role_id)
            tabs.addTab(self.guest_manager, "Гости")
        
        if self.check_permission('all') or self.check_permission('manage_bookings'):
            self.booking_manager = BookingManager(self.role_id)
            tabs.addTab(self.booking_manager, "Бронирования")
        
        if self.check_permission('all') or self.check_permission('manage_cleaning'):
            self.cleaning_manager = CleaningManager(self.role_id)
            tabs.addTab(self.cleaning_manager, "Уборка")
        
        if self.check_permission('all'):
            self.user_manager = UserManagement(self.role_id)
            tabs.addTab(self.user_manager, "Пользователи")
        
        self.setCentralWidget(tabs)
        
        # Статус бар
        status_bar = QStatusBar()
        status_bar.showMessage(f"Вы вошли как {ROLES_CONFIG['roles'][self.role_id]['name']} (ID: {self.user_id})")
        self.setStatusBar(status_bar)

    def check_permission(self, permission):
        """Проверяет права текущего пользователя"""
        if self.role_id == 1:  # Администратор
            return True
        return permission in ROLES_CONFIG['roles'].get(self.role_id, {}).get('permissions', [])