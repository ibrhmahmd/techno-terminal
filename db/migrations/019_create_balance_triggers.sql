-- Migration 019: Create Balance Update Triggers
-- Created: 2026-04-08
-- Purpose: Automate balance updates on payment/enrollment changes

-- Function to update student balance
CREATE OR REPLACE FUNCTION update_student_balance()
RETURNS TRIGGER AS $$
DECLARE
    v_student_id INTEGER;
    v_total_due DECIMAL(10,2);
    v_total_discounts DECIMAL(10,2);
    v_total_paid DECIMAL(10,2);
    v_net_balance DECIMAL(10,2);
BEGIN
    -- Determine which student to update
    IF TG_OP = 'DELETE' THEN
        v_student_id := OLD.student_id;
    ELSE
        v_student_id := NEW.student_id;
    END IF;
    
    -- Calculate totals from enrollments
    SELECT 
        COALESCE(SUM(e.amount_due), 0),
        COALESCE(SUM(e.discount_applied), 0)
    INTO v_total_due, v_total_discounts
    FROM enrollments e
    WHERE e.student_id = v_student_id
      AND e.status IN ('active', 'completed');
    
    -- Calculate total paid (through payment allocations)
    SELECT COALESCE(SUM(pa.allocated_amount), 0)
    INTO v_total_paid
    FROM payment_allocations pa
    JOIN payments p ON pa.payment_id = p.id
    WHERE p.student_id = v_student_id;
    
    -- Calculate net balance (negative = debt, positive = credit)
    v_net_balance := v_total_paid - (v_total_due - v_total_discounts);
    
    -- Update or insert student balance
    INSERT INTO student_balances (
        student_id, 
        total_amount_due, 
        total_discounts, 
        total_paid, 
        net_balance, 
        last_updated
    )
    VALUES (
        v_student_id, 
        v_total_due, 
        v_total_discounts, 
        v_total_paid, 
        v_net_balance, 
        NOW()
    )
    ON CONFLICT (student_id) 
    DO UPDATE SET
        total_amount_due = EXCLUDED.total_amount_due,
        total_discounts = EXCLUDED.total_discounts,
        total_paid = EXCLUDED.total_paid,
        net_balance = EXCLUDED.net_balance,
        last_updated = NOW();
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger on payments table
DROP TRIGGER IF EXISTS trg_update_balance_on_payment ON payments;
CREATE TRIGGER trg_update_balance_on_payment
    AFTER INSERT OR UPDATE OR DELETE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_student_balance();

-- Function to handle enrollment changes
CREATE OR REPLACE FUNCTION update_balance_on_enrollment_change()
RETURNS TRIGGER AS $$
DECLARE
    v_student_id INTEGER;
BEGIN
    -- Determine student ID
    IF TG_OP = 'DELETE' THEN
        v_student_id := OLD.student_id;
    ELSE
        v_student_id := NEW.student_id;
    END IF;
    
    -- Recalculate and update balance
    INSERT INTO student_balances (
        student_id, 
        total_amount_due, 
        total_discounts, 
        total_paid, 
        net_balance, 
        last_updated
    )
    SELECT 
        v_student_id,
        COALESCE(SUM(e.amount_due), 0),
        COALESCE(SUM(e.discount_applied), 0),
        COALESCE(SUM(pa.allocated_amount), 0),
        COALESCE(SUM(pa.allocated_amount), 0) - COALESCE(SUM(e.amount_due - e.discount_applied), 0),
        NOW()
    FROM enrollments e
    LEFT JOIN payment_allocations pa ON pa.enrollment_id = e.id
    WHERE e.student_id = v_student_id AND e.status IN ('active', 'completed')
    ON CONFLICT (student_id) 
    DO UPDATE SET
        total_amount_due = EXCLUDED.total_amount_due,
        total_discounts = EXCLUDED.total_discounts,
        total_paid = EXCLUDED.total_paid,
        net_balance = EXCLUDED.net_balance,
        last_updated = NOW();
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger on enrollments table
DROP TRIGGER IF EXISTS trg_update_balance_on_enrollment ON enrollments;
CREATE TRIGGER trg_update_balance_on_enrollment
    AFTER INSERT OR UPDATE OR DELETE ON enrollments
    FOR EACH ROW
    EXECUTE FUNCTION update_balance_on_enrollment_change();
