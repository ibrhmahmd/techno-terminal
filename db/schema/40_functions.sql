-- =============================================================================
-- FUNCTIONS
-- Custom PostgreSQL functions for triggers and business logic
-- =============================================================================

-- =============================================================================
-- AUDIT FUNCTIONS
-- =============================================================================

-- Function: Auto-update updated_at timestamp
-- Used by: Multiple tables via triggers
CREATE OR REPLACE FUNCTION tf_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION tf_set_updated_at() IS 'Trigger function to automatically update updated_at column';

-- =============================================================================
-- STUDENT STATUS FUNCTIONS
-- =============================================================================

-- Function: Auto-set waiting_since when status changes to waiting
CREATE OR REPLACE FUNCTION update_waiting_since()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'waiting' AND (OLD.status IS NULL OR OLD.status != 'waiting') THEN
        NEW.waiting_since = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_waiting_since() IS 'Trigger function to set waiting_since timestamp when student enters waiting status';

-- =============================================================================
-- TEAM DATA FUNCTIONS
-- =============================================================================

-- Function: Normalize team category and subcategory fields
CREATE OR REPLACE FUNCTION normalize_team_fields()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.category IS NOT NULL THEN
        NEW.category = LOWER(TRIM(NEW.category));
    END IF;
    IF NEW.subcategory IS NOT NULL THEN
        NEW.subcategory = LOWER(TRIM(NEW.subcategory));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION normalize_team_fields() IS 'Trigger function to normalize team category and subcategory (lowercase, trimmed)';

-- =============================================================================
-- RLS (ROW LEVEL SECURITY) FUNCTIONS
-- =============================================================================

-- Function: Auto-enable RLS on new tables (Supabase pattern)
-- Note: This is typically used with event triggers in Supabase
CREATE OR REPLACE FUNCTION rls_auto_enable()
RETURNS event_trigger AS $$
BEGIN
    -- This is a placeholder for Supabase's RLS auto-enable pattern
    -- Actual implementation depends on specific Supabase configuration
    NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION rls_auto_enable() IS 'Placeholder for Supabase RLS auto-enable trigger function';

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function: Generate receipt number
CREATE OR REPLACE FUNCTION generate_receipt_number()
RETURNS TEXT AS $$
DECLARE
    prefix TEXT := 'RCP';
    date_part TEXT;
    sequence_part TEXT;
    new_number TEXT;
BEGIN
    date_part := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
    sequence_part := LPAD(NEXTVAL('receipts_receipt_number_seq')::TEXT, 6, '0');
    new_number := prefix || '-' || date_part || '-' || sequence_part;
    RETURN new_number;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION generate_receipt_number() IS 'Generate a unique receipt number in format RCP-YYYYMMDD-######';

-- Function: Check if student has active enrollment in group
CREATE OR REPLACE FUNCTION has_active_enrollment(
    p_student_id INTEGER,
    p_group_id INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM enrollments 
        WHERE student_id = p_student_id 
          AND group_id = p_group_id 
          AND status = 'active'
          AND deleted_at IS NULL
    ) INTO v_exists;
    
    RETURN v_exists;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION has_active_enrollment(INTEGER, INTEGER) IS 'Check if student has an active enrollment in the specified group';
