-- Migration 068: Update Waiting Since Trigger
-- Created: 2026-06-08
-- Purpose: Modify update_waiting_since() and trg_update_waiting_since to support BEFORE INSERT OR UPDATE on students.

CREATE OR REPLACE FUNCTION update_waiting_since()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status = 'waiting' THEN
            NEW.waiting_since = CURRENT_TIMESTAMP;
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.status = 'waiting' AND (OLD.status IS NULL OR OLD.status != 'waiting') THEN
            NEW.waiting_since = CURRENT_TIMESTAMP;
        ELSIF NEW.status != 'waiting' AND OLD.status = 'waiting' THEN
            NEW.waiting_since = NULL;
            NEW.waiting_priority = NULL;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_waiting_since ON students;
CREATE TRIGGER trg_update_waiting_since
    BEFORE INSERT OR UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_waiting_since();
