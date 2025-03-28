from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PyQt6.QtGui import QIcon
from hotel_management.ui.rooms.room_manager import RoomManager
from hotel_management.ui.guests.guest_manager import GuestManager
from hotel_management.ui.bookings.booking_manager import BookingManager
from hotel_management.ui.cleaning.cleaning_manager import CleaningManager
from hotel_management.ui.admin.user_management import UserManagement
from hotel_management.database.models import Role
from hotel_management.database.connector import DatabaseConnector

class AdminDashboard(QMainWindow):
    def __init__(self, user_id, role_id):
        super().__init__()
        self.user_id = user_id
        self.role_id = role_id
        self.setWindowTitle(f"Отель Grand Plaza - {Role.get_name(role_id)}")
        self.setMinimumSize(1200, 800)
        self.setWindowIcon(QIcon('hotel_icon.ico'))
        self.init_ui()
        
    def init_ui(self):
        tabs = QTabWidget()
        
        # Вкладка управления номерами
        if self.check_permission('all') or self.check_permission('manage_rooms'):
            self.room_manager = RoomManager(self)
            tabs.addTab(self.room_manager, "Номера")
        
        # Вкладка управления гостями
        if self.check_permission('all') or self.check_permission('manage_guests'):
            self.guest_manager = GuestManager(self)
            tabs.addTab(self.guest_manager, "Гости")
        
        # Вкладка управления бронированиями
        if self.check_permission('all') or self.check_permission('manage_bookings'):
            self.booking_manager = BookingManager(self)
            tabs.addTab(self.booking_manager, "Бронирования")
        
        # Вкладка управления уборкой
        if self.check_permission('all') or self.check_permission('manage_cleaning'):
            self.cleaning_manager = CleaningManager(self)
            tabs.addTab(self.cleaning_manager, "Уборка")
        
        # Вкладка управления пользователями (только для админа)
        if self.check_permission('all'):
            self.user_manager = UserManagement(self)
            tabs.addTab(self.user_manager, "Пользователи")
        
        self.setCentralWidget(tabs)
        
        # Статус бар с информацией о пользователе
        status_bar = QStatusBar()
        status_bar.showMessage(f"Вы вошли как {Role.get_name(self.role_id)} (ID: {self.user_id})")
        self.setStatusBar(status_bar)

    def check_permission(self, permission):
        """Проверяет наличие прав у пользователя"""
        if self.role_id == 1:  # Администратор имеет все права
            return True
            
        db = DatabaseConnector()
        if not db.connect():
            return False
            
        try:
            query = """
            SELECT EXISTS (
                SELECT 1 FROM roles 
                WHERE role_id = %s AND %s = ANY(permissions)
            """
            result = db.execute_query(query, (self.role_id, permission), fetch=True)
            return result[0][0] if result else False
        except Exception as e:
            print(f"Ошибка проверки прав: {e}")
            return False
        finally:
            db.disconnect()