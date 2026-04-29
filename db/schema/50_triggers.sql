-- =============================================================================
-- TRIGGERS
-- Database triggers for audit, validation, and automation
-- =============================================================================

-- =============================================================================
-- AUDIT TRIGGERS (Auto-update updated_at)
-- =============================================================================

-- Parents
DROP TRIGGER IF EXISTS trg_parents_updated_at ON parents;
CREATE TRIGGER trg_parents_updated_at
    BEFORE UPDATE ON parents
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Employees
DROP TRIGGER IF EXISTS trg_employees_updated_at ON employees;
CREATE TRIGGER trg_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Users
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Students
DROP TRIGGER IF EXISTS trg_students_updated_at ON students;
CREATE TRIGGER trg_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Courses
DROP TRIGGER IF EXISTS trg_courses_updated_at ON courses;
CREATE TRIGGER trg_courses_updated_at
    BEFORE UPDATE ON courses
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Groups
DROP TRIGGER IF EXISTS trg_groups_updated_at ON groups;
CREATE TRIGGER trg_groups_updated_at
    BEFORE UPDATE ON groups
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Group Levels
DROP TRIGGER IF EXISTS trg_group_levels_updated_at ON group_levels;
CREATE TRIGGER trg_group_levels_updated_at
    BEFORE UPDATE ON group_levels
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Sessions
DROP TRIGGER IF EXISTS trg_sessions_updated_at ON sessions;
CREATE TRIGGER trg_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Enrollments
DROP TRIGGER IF EXISTS trg_enrollments_updated_at ON enrollments;
CREATE TRIGGER trg_enrollments_updated_at
    BEFORE UPDATE ON enrollments
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Enrollment Level History
DROP TRIGGER IF EXISTS trg_enrollment_level_history_updated_at ON enrollment_level_history;
CREATE TRIGGER trg_enrollment_level_history_updated_at
    BEFORE UPDATE ON enrollment_level_history
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Receipts
DROP TRIGGER IF EXISTS trg_receipts_updated_at ON receipts;
CREATE TRIGGER trg_receipts_updated_at
    BEFORE UPDATE ON receipts
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Payments
DROP TRIGGER IF EXISTS trg_payments_updated_at ON payments;
CREATE TRIGGER trg_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Competitions
DROP TRIGGER IF EXISTS trg_competitions_updated_at ON competitions;
CREATE TRIGGER trg_competitions_updated_at
    BEFORE UPDATE ON competitions
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Teams
DROP TRIGGER IF EXISTS trg_teams_updated_at ON teams;
CREATE TRIGGER trg_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Competition Categories
DROP TRIGGER IF EXISTS trg_competition_categories_updated_at ON competition_categories;
CREATE TRIGGER trg_competition_categories_updated_at
    BEFORE UPDATE ON competition_categories
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Academic Categories
DROP TRIGGER IF EXISTS trg_academic_categories_updated_at ON academic_categories;
CREATE TRIGGER trg_academic_categories_updated_at
    BEFORE UPDATE ON academic_categories
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Academic Years
DROP TRIGGER IF EXISTS trg_academic_years_updated_at ON academic_years;
CREATE TRIGGER trg_academic_years_updated_at
    BEFORE UPDATE ON academic_years
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Receipt Templates
DROP TRIGGER IF EXISTS trg_receipt_templates_updated_at ON receipt_templates;
CREATE TRIGGER trg_receipt_templates_updated_at
    BEFORE UPDATE ON receipt_templates
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Group Course History
DROP TRIGGER IF EXISTS trg_group_course_history_updated_at ON group_course_history;
CREATE TRIGGER trg_group_course_history_updated_at
    BEFORE UPDATE ON group_course_history
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Group Competition Participation
DROP TRIGGER IF EXISTS trg_group_competition_participation_updated_at ON group_competition_participation;
CREATE TRIGGER trg_group_competition_participation_updated_at
    BEFORE UPDATE ON group_competition_participation
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Notification Templates
DROP TRIGGER IF EXISTS trg_notification_templates_updated_at ON notification_templates;
CREATE TRIGGER trg_notification_templates_updated_at
    BEFORE UPDATE ON notification_templates
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Notification Subscribers
DROP TRIGGER IF EXISTS trg_notification_subscribers_updated_at ON notification_subscribers;
CREATE TRIGGER trg_notification_subscribers_updated_at
    BEFORE UPDATE ON notification_subscribers
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- Admin Notification Settings
DROP TRIGGER IF EXISTS trg_admin_notification_settings_updated_at ON admin_notification_settings;
CREATE TRIGGER trg_admin_notification_settings_updated_at
    BEFORE UPDATE ON admin_notification_settings
    FOR EACH ROW
    EXECUTE FUNCTION tf_set_updated_at();

-- =============================================================================
-- BUSINESS LOGIC TRIGGERS
-- =============================================================================

-- Update waiting_since when student enters waiting status
DROP TRIGGER IF EXISTS trg_update_waiting_since ON students;
CREATE TRIGGER trg_update_waiting_since
    BEFORE UPDATE ON students
    FOR EACH ROW
    WHEN (NEW.status IS DISTINCT FROM OLD.status)
    EXECUTE FUNCTION update_waiting_since();

-- Normalize team category and subcategory fields
DROP TRIGGER IF EXISTS normalize_team_fields_trigger ON teams;
CREATE TRIGGER normalize_team_fields_trigger
    BEFORE INSERT OR UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION normalize_team_fields();

-- =============================================================================
-- NOTES
-- =============================================================================
-- 
-- Supabase-managed triggers (not included here):
-- - enforce_bucket_name_length_trigger (buckets table)
-- - protect_buckets_delete (buckets table)
-- - protect_objects_delete (objects table)
-- - update_objects_updated_at (objects table)
-- - tr_check_filters (subscription table)
--
-- These are auto-created by Supabase extensions and should not be modified.
--
