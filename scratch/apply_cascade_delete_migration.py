import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db.connection import get_engine
from sqlalchemy import text

# Load migration sql
migration_path = 'db/migrations/069_fix_student_activity_log_cascade.sql'
with open(migration_path, 'r', encoding='utf-8') as f:
    sql_content = f.read()

engine = get_engine()
with engine.connect() as conn:
    print("Applying migration 069...")
    conn.execute(text(sql_content))
    conn.commit()
    print("Migration 069 applied successfully!")
