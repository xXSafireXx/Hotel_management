-- Триггер для автоматического обновления статуса номера при бронировании
CREATE OR REPLACE FUNCTION update_room_status_on_booking()
RETURNS TRIGGER AS $$
BEGIN
    -- При создании брони
    IF TG_OP = 'INSERT' THEN
        UPDATE rooms 
        SET status_id = (SELECT status_id FROM statuses WHERE name = 'Занят')
        WHERE room_id = NEW.room_id;
    
    -- При отмене брони
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE rooms 
        SET status_id = (SELECT status_id FROM statuses WHERE name = 'Требует уборки')
        WHERE room_id = OLD.room_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_booking_change
AFTER INSERT OR DELETE ON occupancy
FOR EACH ROW EXECUTE FUNCTION update_room_status_on_booking();

-- Триггер для автоматической отметки уборки
CREATE OR REPLACE FUNCTION mark_room_cleaned()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE rooms
    SET status_id = (SELECT status_id FROM statuses WHERE name = 'Свободен')
    WHERE room_id = NEW.room_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_cleaning_complete
AFTER INSERT ON cleaning
FOR EACH ROW EXECUTE FUNCTION mark_room_cleaned();