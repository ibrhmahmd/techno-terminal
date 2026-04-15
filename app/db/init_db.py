import os
from dotenv import load_dotenv

# Load env before importing engine
load_dotenv()

from sqlmodel import SQLModel, text
from app.db.connection import get_engine, get_session

# IMPORTANT: Import ALL SQLModels here so SQLModel.metadata recognizes them before create_all()
import app.modules.hr.hr_models
from app.modules.auth import User
import app.modules.crm.models.parent_models
import app.modules.crm.models.student_models
import app.modules.crm.models.link_models
import app.modules.academics.models.course_models
import app.modules.academics.models.group_models
import app.modules.academics.models.session_models
import app.modules.attendance.models.attendance_models
import app.modules.enrollments.models.enrollment_models
import app.modules.finance
import app.modules.competitions.models.competition_models
import app.modules.competitions.models.team_models

from app.db.seed import seed_admin_account

# ORM/table drift: older DBs may lack JSONB metadata columns referenced by views.
ENSURE_METADATA_COLUMNS_SQL = """
ALTER TABLE students ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE employees ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE groups ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE payments ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE teams ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
"""

RAW_VIEWS_SQL = """
CREATE OR REPLACE VIEW v_students AS
SELECT s.id,
    s.full_name,
    s.date_of_birth,
    EXTRACT(YEAR FROM AGE(s.date_of_birth))::INTEGER AS age,
    s.gender,
    s.phone AS student_phone,
    s.notes,
    s.is_active,
    s.created_at,
    s.updated_at,
    s.metadata,
    g.full_name AS primary_parent_name,
    g.phone_primary AS primary_parent_phone
FROM students s
    LEFT JOIN student_parents sg ON s.id = sg.student_id AND sg.is_primary = TRUE
    LEFT JOIN parents g ON sg.parent_id = g.id;

CREATE OR REPLACE VIEW v_enrollment_balance AS
SELECT e.id AS enrollment_id,
    e.student_id,
    e.group_id,
    e.level_number,
    e.amount_due,
    e.discount_applied,
    (e.amount_due - e.discount_applied) AS net_due,
    COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')), 0) - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0) AS total_paid,
    (COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type IN ('payment', 'charge')), 0) - COALESCE(SUM(p.amount) FILTER (WHERE p.transaction_type = 'refund'), 0)) - (e.amount_due - e.discount_applied) AS balance
FROM enrollments e
    LEFT JOIN payments p ON p.enrollment_id = e.id
GROUP BY e.id;

CREATE OR REPLACE VIEW v_enrollment_attendance AS
SELECT a.enrollment_id,
    COUNT(*) FILTER (WHERE a.status IN ('present', 'late')) AS sessions_attended,
    COUNT(*) FILTER (WHERE a.status = 'absent') AS sessions_missed
FROM attendance a
GROUP BY a.enrollment_id;

CREATE OR REPLACE VIEW v_siblings AS
SELECT sg1.student_id AS student_id,
    s1.full_name AS student_name,
    sg2.student_id AS sibling_id,
    s2.full_name AS sibling_name,
    sg1.parent_id
FROM student_parents sg1
    JOIN student_parents sg2 ON sg1.parent_id = sg2.parent_id AND sg1.student_id < sg2.student_id
    JOIN students s1 ON sg1.student_id = s1.id
    JOIN students s2 ON sg2.student_id = s2.id
WHERE s1.is_active = TRUE AND s2.is_active = TRUE;

CREATE OR REPLACE VIEW v_group_session_count AS
SELECT group_id,
    level_number,
    COUNT(*) FILTER (WHERE is_extra_session = FALSE) AS regular_sessions,
    COUNT(*) FILTER (WHERE is_extra_session = TRUE) AS extra_sessions,
    COUNT(*) AS total_sessions
FROM sessions
GROUP BY group_id, level_number;
"""


def _run_sql_statements(conn, sql_blob: str) -> None:
    for chunk in sql_blob.split(";"):
        chunk = chunk.strip()
        if chunk:
            conn.execute(text(chunk + ";"))


def apply_analytics_views() -> None:
    """
    Ensure JSONB metadata columns exist, then CREATE OR REPLACE analytics views
    (v_students, v_enrollment_balance, …). Idempotent — safe on every app start.
    """
    engine = get_engine()
    with engine.begin() as conn:
        _run_sql_statements(conn, ENSURE_METADATA_COLUMNS_SQL)
        _run_sql_statements(conn, RAW_VIEWS_SQL)


def init_db():
    engine = get_engine()
    
    print("Resetting database. Dropping all ORM tables...")
    # SQLModel.metadata.drop_all(engine)
    
    print("Creating tables dynamically from SQLModel decoupled definitions...")
    SQLModel.metadata.create_all(engine)
    
    print("Re-attaching native PostgreSQL Analytics Views...")
    apply_analytics_views()
        
    print("Executing Supabase Identity Seeder...")
    seed_admin_account()
    
    print("Complete! System architecture perfectly synchronized with Supabase.")

if __name__ == "__main__":
    init_db()
