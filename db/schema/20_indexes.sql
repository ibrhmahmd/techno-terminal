-- =============================================================================
-- INDEXES (SYNCED FROM LIVE DB)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Indexes for table admin_notification_settings
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_admin_settings_admin_id ON public.admin_notification_settings USING btree (admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_settings_type ON public.admin_notification_settings USING btree (notification_type);

-- -----------------------------------------------------------------------------
-- Indexes for table attendance
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_attendance_enrollment ON public.attendance USING btree (enrollment_id);
CREATE INDEX IF NOT EXISTS idx_attendance_session ON public.attendance USING btree (session_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON public.attendance USING btree (student_id);

-- -----------------------------------------------------------------------------
-- Indexes for table audit_logs
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_created ON public.audit_logs USING btree (event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created ON public.audit_logs USING btree (user_id, created_at DESC);

-- -----------------------------------------------------------------------------
-- Indexes for table competitions
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_competitions_edition_year ON public.competitions USING btree (edition_year);
CREATE UNIQUE INDEX IF NOT EXISTS uq_competitions_name_edition_year ON public.competitions USING btree (name, edition_year);

-- -----------------------------------------------------------------------------
-- Indexes for table employees
-- -----------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS uq_employees_email ON public.employees USING btree (email);
CREATE UNIQUE INDEX IF NOT EXISTS uq_employees_national_id ON public.employees USING btree (national_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_employees_phone ON public.employees USING btree (phone);
CREATE UNIQUE INDEX IF NOT EXISTS uq_employees_user_id ON public.employees USING btree (user_id);

-- -----------------------------------------------------------------------------
-- Indexes for table enrollment_level_history
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_enrollment ON public.enrollment_level_history USING btree (enrollment_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_level ON public.enrollment_level_history USING btree (group_level_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_level_history_student ON public.enrollment_level_history USING btree (student_id);

-- -----------------------------------------------------------------------------
-- Indexes for table enrollments
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_enrollments_active ON public.enrollments USING btree (status) WHERE (status = 'active'::text);
CREATE UNIQUE INDEX IF NOT EXISTS idx_enrollments_active_unique ON public.enrollments USING btree (student_id, group_id) WHERE (status = 'active'::text);
CREATE INDEX IF NOT EXISTS idx_enrollments_group ON public.enrollments USING btree (group_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_group_level_active ON public.enrollments USING btree (group_id, level_number, status) WHERE (status = 'active'::text);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON public.enrollments USING btree (student_id);

-- -----------------------------------------------------------------------------
-- Indexes for table group_course_history
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_group_course_history_assigned ON public.group_course_history USING btree (assigned_at);
CREATE INDEX IF NOT EXISTS idx_group_course_history_course ON public.group_course_history USING btree (course_id);
CREATE INDEX IF NOT EXISTS idx_group_course_history_group ON public.group_course_history USING btree (group_id);

-- -----------------------------------------------------------------------------
-- Indexes for table group_levels
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_group_levels_effective ON public.group_levels USING btree (effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_group_levels_group ON public.group_levels USING btree (group_id);
CREATE INDEX IF NOT EXISTS idx_group_levels_group_number ON public.group_levels USING btree (group_id, level_number);
CREATE INDEX IF NOT EXISTS idx_group_levels_status ON public.group_levels USING btree (status);

-- -----------------------------------------------------------------------------
-- Indexes for table groups
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_groups_active ON public.groups USING btree (status) WHERE (status = 'active'::text);
CREATE INDEX IF NOT EXISTS idx_groups_course ON public.groups USING btree (course_id);
CREATE INDEX IF NOT EXISTS idx_groups_instructor ON public.groups USING btree (instructor_id);

-- -----------------------------------------------------------------------------
-- Indexes for table notification_additional_recipients
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_additional_recipients_active ON public.notification_additional_recipients USING btree (is_active);
CREATE INDEX IF NOT EXISTS idx_additional_recipients_admin_id ON public.notification_additional_recipients USING btree (admin_id);
CREATE INDEX IF NOT EXISTS idx_additional_recipients_email ON public.notification_additional_recipients USING btree (email);

-- -----------------------------------------------------------------------------
-- Indexes for table notification_logs
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at ON public.notification_logs USING btree (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_logs_recipient ON public.notification_logs USING btree (recipient_type, recipient_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON public.notification_logs USING btree (status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_template ON public.notification_logs USING btree (template_id);

-- -----------------------------------------------------------------------------
-- Indexes for table parents
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_parents_phone ON public.parents USING btree (phone_primary) WHERE (phone_primary IS NOT NULL);

-- -----------------------------------------------------------------------------
-- Indexes for table payments
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_payments_active ON public.payments USING btree (id) WHERE (deleted_at IS NULL);
CREATE INDEX IF NOT EXISTS idx_payments_deleted ON public.payments USING btree (deleted_at) WHERE (deleted_at IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_payments_enrollment ON public.payments USING btree (enrollment_id);
CREATE INDEX IF NOT EXISTS idx_payments_original_payment_id ON public.payments USING btree (original_payment_id);
CREATE INDEX IF NOT EXISTS idx_payments_receipt ON public.payments USING btree (receipt_id);
CREATE INDEX IF NOT EXISTS idx_payments_student ON public.payments USING btree (student_id);

-- -----------------------------------------------------------------------------
-- Indexes for table receipts
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_receipts_paid_at ON public.receipts USING btree (paid_at DESC);
CREATE INDEX IF NOT EXISTS idx_receipts_template ON public.receipts USING btree (receipt_template);

-- -----------------------------------------------------------------------------
-- Indexes for table sessions
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sessions_date ON public.sessions USING btree (session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_group ON public.sessions USING btree (group_id);
CREATE INDEX IF NOT EXISTS idx_sessions_group_level ON public.sessions USING btree (group_id, level_number);
CREATE INDEX IF NOT EXISTS idx_sessions_group_level_id ON public.sessions USING btree (group_level_id);

-- -----------------------------------------------------------------------------
-- Indexes for table student_activity_log
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON public.student_activity_log USING btree (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_meta ON public.student_activity_log USING gin (meta);
CREATE INDEX IF NOT EXISTS idx_activity_log_metadata ON public.student_activity_log USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_activity_log_performed_by ON public.student_activity_log USING btree (performed_by);
CREATE INDEX IF NOT EXISTS idx_activity_log_reference ON public.student_activity_log USING btree (reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_student_time ON public.student_activity_log USING btree (student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_type_time ON public.student_activity_log USING btree (activity_type, created_at DESC);

-- -----------------------------------------------------------------------------
-- Indexes for table student_parents
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_student_parents_parent ON public.student_parents USING btree (parent_id);
CREATE INDEX IF NOT EXISTS idx_student_parents_student ON public.student_parents USING btree (student_id);

-- -----------------------------------------------------------------------------
-- Indexes for table students
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_students_deleted ON public.students USING btree (deleted_at) WHERE (deleted_at IS NOT NULL);
CREATE INDEX IF NOT EXISTS idx_students_name ON public.students USING btree (full_name);
CREATE INDEX IF NOT EXISTS idx_students_status ON public.students USING btree (status);
CREATE INDEX IF NOT EXISTS idx_students_waiting ON public.students USING btree (status) WHERE (status = 'waiting'::student_status);

-- -----------------------------------------------------------------------------
-- Indexes for table team_members
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_team_members_amount_paid ON public.team_members USING btree (amount_paid);
CREATE INDEX IF NOT EXISTS idx_team_members_student ON public.team_members USING btree (student_id);
CREATE INDEX IF NOT EXISTS idx_team_members_student_id ON public.team_members USING btree (student_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON public.team_members USING btree (team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON public.team_members USING btree (team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team_student ON public.team_members USING btree (team_id, student_id);

-- -----------------------------------------------------------------------------
-- Indexes for table teams
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_teams_category ON public.teams USING btree (category_id);
CREATE INDEX IF NOT EXISTS idx_teams_coach_id ON public.teams USING btree (coach_id);
CREATE INDEX IF NOT EXISTS idx_teams_competition_category ON public.teams USING btree (competition_id, category);
CREATE INDEX IF NOT EXISTS idx_teams_competition_id ON public.teams USING btree (competition_id);
CREATE INDEX IF NOT EXISTS idx_teams_deleted ON public.teams USING btree (is_deleted) WHERE (is_deleted = true);
CREATE INDEX IF NOT EXISTS idx_teams_subcategory ON public.teams USING btree (subcategory);

-- -----------------------------------------------------------------------------
-- Indexes for table users
-- -----------------------------------------------------------------------------
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_supabase_uid ON public.users USING btree (supabase_uid);

