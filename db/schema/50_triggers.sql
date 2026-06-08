-- =============================================================================
-- TRIGGERS (SYNCED FROM LIVE DB)
-- =============================================================================

DROP TRIGGER IF EXISTS trg_update_waiting_since ON students;
CREATE TRIGGER trg_update_waiting_since BEFORE INSERT OR UPDATE ON public.students FOR EACH ROW EXECUTE FUNCTION update_waiting_since();

DROP TRIGGER IF EXISTS trg_parents_updated_at ON parents;
CREATE TRIGGER trg_parents_updated_at BEFORE UPDATE ON public.parents FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_employees_updated_at ON employees;
CREATE TRIGGER trg_employees_updated_at BEFORE UPDATE ON public.employees FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_students_updated_at ON students;
CREATE TRIGGER trg_students_updated_at BEFORE UPDATE ON public.students FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_courses_updated_at ON courses;
CREATE TRIGGER trg_courses_updated_at BEFORE UPDATE ON public.courses FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_groups_updated_at ON groups;
CREATE TRIGGER trg_groups_updated_at BEFORE UPDATE ON public.groups FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_enrollments_updated_at ON enrollments;
CREATE TRIGGER trg_enrollments_updated_at BEFORE UPDATE ON public.enrollments FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_group_levels_updated_at ON group_levels;
CREATE TRIGGER trg_group_levels_updated_at BEFORE UPDATE ON public.group_levels FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

DROP TRIGGER IF EXISTS trg_enrollment_level_history_updated_at ON enrollment_level_history;
CREATE TRIGGER trg_enrollment_level_history_updated_at BEFORE UPDATE ON public.enrollment_level_history FOR EACH ROW EXECUTE FUNCTION tf_set_updated_at();

DROP TRIGGER IF EXISTS normalize_team_fields_trigger ON teams;
CREATE TRIGGER normalize_team_fields_trigger BEFORE INSERT OR UPDATE ON public.teams FOR EACH ROW EXECUTE FUNCTION normalize_team_fields();

