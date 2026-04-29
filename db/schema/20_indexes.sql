-- =============================================================================
-- INDEXES
-- Performance indexes for all tables
-- Organized by table for easy maintenance
-- =============================================================================

-- =============================================================================
-- CORE TABLES INDEXES
-- =============================================================================

-- Parents
CREATE INDEX IF NOT EXISTS idx_parents_phone ON parents(phone_primary)
    WHERE phone_primary IS NOT NULL;

-- Employees
CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(is_active)
    WHERE is_active = TRUE;

-- Users
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_supabase_uid ON users(supabase_uid);

-- =============================================================================
-- CRM TABLES INDEXES
-- =============================================================================

-- Students
CREATE INDEX IF NOT EXISTS idx_students_active ON students(status)
    WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_students_deleted ON students(deleted_at)
    WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_students_name ON students(full_name);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
CREATE INDEX IF NOT EXISTS idx_students_waiting ON students(status)
    WHERE status = 'waiting';

-- Student Parents
CREATE INDEX IF NOT EXISTS idx_student_parents_student ON student_parents(student_id);
CREATE INDEX IF NOT EXISTS idx_student_parents_parent ON student_parents(parent_id);

-- Student Activity Log
CREATE INDEX IF NOT EXISTS idx_activity_log_student_time ON student_activity_log(student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_type_time ON student_activity_log(activity_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON student_activity_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_performed_by ON student_activity_log(performed_by);
CREATE INDEX IF NOT EXISTS idx_activity_log_reference ON student_activity_log(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_meta ON student_activity_log(meta) WHERE meta IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activity_log_metadata ON student_activity_log(metadata) WHERE metadata IS NOT NULL;

-- =============================================================================
-- ACADEMICS TABLES INDEXES
-- =============================================================================

-- Courses
CREATE INDEX IF NOT EXISTS idx_courses_active ON courses(is_active)
    WHERE is_active = TRUE;

-- Groups
CREATE INDEX IF NOT EXISTS idx_groups_course ON groups(course_id);
CREATE INDEX IF NOT EXISTS idx_groups_instructor ON groups(instructor_id);
CREATE INDEX IF NOT EXISTS idx_groups_active ON groups(status)
    WHERE status = 'active';

-- Group Levels
CREATE INDEX IF NOT EXISTS idx_group_levels_effective ON group_levels(effective_from, effective_until);
CREATE INDEX IF NOT EXISTS idx_group_levels_status ON group_levels(status);

-- Group Course History
CREATE INDEX IF NOT EXISTS idx_group_course_history_group ON group_course_history(group_id);
CREATE INDEX IF NOT EXISTS idx_group_course_history_course ON group_course_history(course_id);
CREATE INDEX IF NOT EXISTS idx_group_course_history_assigned ON group_course_history(assigned_at);

-- Sessions
CREATE INDEX IF NOT EXISTS idx_sessions_group ON sessions(group_id);
CREATE INDEX IF NOT EXISTS idx_sessions_group_level ON sessions(group_id, level_number);
CREATE INDEX IF NOT EXISTS idx_sessions_group_level_id ON sessions(group_level_id)
    WHERE group_level_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);

-- =============================================================================
-- ENROLLMENTS TABLES INDEXES
-- =============================================================================

-- Enrollments
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_group ON enrollments(group_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_active ON enrollments(status)
    WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_enrollments_active_unique ON enrollments(student_id, group_id)
    WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_enrollments_group_level_active ON enrollments(group_id, level_number, status)
    WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_enrollments_deleted ON enrollments(deleted_at)
    WHERE deleted_at IS NOT NULL;

-- Enrollment Level History
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_enrollment ON enrollment_level_history(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_student ON enrollment_level_history(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_level ON enrollment_level_history(group_level_id)
    WHERE group_level_id IS NOT NULL;

-- Attendance
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance(session_id);
CREATE INDEX IF NOT EXISTS idx_attendance_enrollment ON attendance(enrollment_id);

-- =============================================================================
-- FINANCE TABLES INDEXES
-- =============================================================================

-- Receipts
CREATE INDEX IF NOT EXISTS idx_receipts_paid_at ON receipts(paid_at DESC);
CREATE INDEX IF NOT EXISTS idx_receipts_template ON receipts(receipt_template)
    WHERE receipt_template IS NOT NULL;

-- Payments
CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id);
CREATE INDEX IF NOT EXISTS idx_payments_receipt ON payments(receipt_id);
CREATE INDEX IF NOT EXISTS idx_payments_enrollment ON payments(enrollment_id)
    WHERE enrollment_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payments_deleted ON payments(deleted_at)
    WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_payments_type ON payments(transaction_type);

-- =============================================================================
-- COMPETITIONS TABLES INDEXES
-- =============================================================================

-- Competitions
CREATE INDEX IF NOT EXISTS idx_competitions_deleted_at ON competitions(deleted_at)
    WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_competitions_edition_year ON competitions(edition_year);
CREATE INDEX IF NOT EXISTS idx_competitions_active ON competitions(is_active, deleted_at)
    WHERE is_active = TRUE AND deleted_at IS NULL;

-- Competition Categories
CREATE INDEX IF NOT EXISTS idx_comp_categories_comp ON competition_categories(competition_id);

-- Teams
CREATE INDEX IF NOT EXISTS idx_teams_category ON teams(category_id);
CREATE INDEX IF NOT EXISTS idx_teams_competition_id ON teams(category_id);
CREATE INDEX IF NOT EXISTS idx_teams_competition_category ON teams(category_id);
CREATE INDEX IF NOT EXISTS idx_teams_subcategory ON teams(subcategory)
    WHERE subcategory IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_teams_deleted ON teams(is_deleted)
    WHERE is_deleted = TRUE;
CREATE INDEX IF NOT EXISTS idx_teams_deleted_at ON teams(deleted_at)
    WHERE deleted_at IS NOT NULL;

-- Team Members
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_student ON team_members(student_id);

-- Group Competition Participation
CREATE INDEX IF NOT EXISTS idx_group_competition_participation_group ON group_competition_participation(group_id);
CREATE INDEX IF NOT EXISTS idx_group_competition_participation_team ON group_competition_participation(team_id);
CREATE INDEX IF NOT EXISTS idx_group_competition_participation_competition ON group_competition_participation(competition_id);
CREATE INDEX IF NOT EXISTS idx_group_competition_participation_active ON group_competition_participation(is_active)
    WHERE is_active = TRUE;

-- =============================================================================
-- NOTIFICATIONS TABLES INDEXES
-- =============================================================================

-- Notification Logs
CREATE INDEX IF NOT EXISTS idx_notification_logs_recipient ON notification_logs(recipient_type, recipient_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_created ON notification_logs(created_at DESC);

-- Notification Subscribers
CREATE INDEX IF NOT EXISTS idx_notification_subscribers_user ON notification_subscribers(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_subscribers_type ON notification_subscribers(notification_type);

-- Notification Additional Recipients
CREATE INDEX IF NOT EXISTS idx_notification_recipients_reference ON notification_additional_recipients(reference_type, reference_id);

-- Admin Notification Settings
CREATE INDEX IF NOT EXISTS idx_admin_settings_admin_id ON admin_notification_settings(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_settings_type ON admin_notification_settings(notification_type);
