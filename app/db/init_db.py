import os
from dotenv import load_dotenv

# Load env before importing engine
load_dotenv()

from sqlmodel import SQLModel, text
from app.db.connection import get_engine, get_session

# IMPORTANT: Import ALL SQLModels here so SQLModel.metadata recognizes them before create_all()
import app.modules.hr.models.employee_models
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

def _run_sql_statements(conn, sql_blob: str) -> None:
    """Execute a blob of SQL statements separated by semicolons.
    Uses sqlparse for safe splitting that handles semicolons in strings."""
    try:
        import sqlparse
        statements = sqlparse.split(sql_blob)
    except ImportError:
        # Fallback: naive split (safe for the current hardcoded view SQL)
        statements = [s.strip() for s in sql_blob.split(";")]

    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            conn.execute(text(stmt if stmt.endswith(";") else stmt + ";"))


def apply_analytics_views() -> None:
    """
    Ensure JSONB metadata columns exist, then CREATE OR REPLACE analytics views
    (v_students, v_enrollment_balance, …). Idempotent — safe on every app start.
    """
    import os
    engine = get_engine()
    
    # Read the actual schema file to guarantee sync
    views_path = os.path.join(os.path.dirname(__file__), "..", "..", "db", "schema", "30_views.sql")
    with open(views_path, "r", encoding="utf-8") as f:
        views_sql = f.read()
        
    with engine.begin() as conn:
        _run_sql_statements(conn, ENSURE_METADATA_COLUMNS_SQL)
        _run_sql_statements(conn, views_sql)


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
