import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    print("=== LIVE DATABASE SCHEMA INSPECTION ===")
    
    # 1. Unique Constraints on "students" table
    print("\n--- Constraints on 'students' table ---")
    res = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(c.oid)
        FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        WHERE t.relname = 'students';
    """))
    for row in res:
        print(f"Constraint: {row[0]} -> {row[1]}")
        
    # 2. Check if table 'student_credits' or others exist
    print("\n--- Check specific tables exist ---")
    tables_to_check = ['student_credits', 'enrollment_balance_history', 'student_balances', 'student_activity_log']
    for t in tables_to_check:
        res = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{t}');"))
        exists = res.scalar()
        print(f"Table '{t}' exists? {exists}")
        
    # 3. List all active triggers in the public schema
    print("\n--- Active Triggers ---")
    res = conn.execute(text("""
        SELECT tgname, relname, tgtype, pg_get_triggerdef(t.oid)
        FROM pg_trigger t
        JOIN pg_class c ON t.tgrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public' AND t.tgisinternal = false;
    """))
    for row in res:
        print(f"Trigger: {row[0]} on {row[1]} -> {row[3]}")
        
    # 4. View structure of 'students' table columns
    print("\n--- Columns in 'students' table ---")
    res = conn.execute(text("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'students'
        ORDER BY ordinal_position;
    """))
    for row in res:
        print(f"Column: {row[0]} | Type: {row[1]} | Nullable: {row[2]} | Default: {row[3]}")
