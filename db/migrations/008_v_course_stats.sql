-- Migration: 008_v_course_stats.sql
-- Sprint 7 (B5/D3) — Course aggregate view
-- Adds v_course_stats: group counts + distinct student counts per course
-- Safe to run multiple times (CREATE OR REPLACE VIEW)

CREATE OR REPLACE VIEW v_course_stats AS
SELECT
    c.id                                                                    AS course_id,
    c.name                                                                  AS course_name,
    COUNT(DISTINCT g.id)                                                    AS total_groups,
    COUNT(DISTINCT g.id) FILTER (WHERE g.status = 'active')                AS active_groups,
    COUNT(DISTINCT e.student_id)                                            AS total_students_ever,
    COUNT(DISTINCT e.student_id) FILTER (WHERE e.status = 'active')        AS active_students
FROM courses c
LEFT JOIN groups g ON g.course_id = c.id
LEFT JOIN enrollments e ON e.group_id = g.id
GROUP BY c.id, c.name;
