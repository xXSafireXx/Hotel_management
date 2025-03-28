class RoomQueries:
    GET_ALL = """
    SELECT r.room_id, r.floor, rc.name, s.name 
    FROM rooms r
    JOIN room_categories rc ON r.category_id = rc.category_id
    JOIN statuses s ON r.status_id = s.status_id
    """

class GuestQueries:
    GET_ALL = "SELECT guest_id, full_name, phone_number FROM guests"
    
class BookingQueries:
    GET_ACTIVE = """
    SELECT o.occupancy_id, g.full_name, r.room_id, o.check_in_date, o.check_out_date
    FROM occupancy o
    JOIN guests g ON o.guest_id = g.guest_id
    JOIN rooms r ON o.room_id = r.room_id
    WHERE o.check_out_date >= CURRENT_DATE
    """

class CleaningQueries:
    GET_PENDING = """
    SELECT c.cleaning_id, r.room_id, s.name 
    FROM cleaning c
    JOIN rooms r ON c.room_id = r.room_id
    JOIN statuses s ON c.status_id = s.status_id
    WHERE s.name = 'Требует уборки'
    """
class RoleQueries:
    GET_ALL = "SELECT role_id, name FROM roles ORDER BY role_id"
    CREATE = "INSERT INTO roles (name) VALUES (%s) RETURNING role_id"