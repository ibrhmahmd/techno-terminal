import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    res = conn.execute(text("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'teams' AND table_schema = 'public';
    """))
    for row in res:
        print(row)
        
    print("\n--- All custom types in public schema ---")
    res = conn.execute(text("""
        SELECT t.typname, t.typtype
        FROM pg_type t
        JOIN pg_namespace n ON t.typnamespace = n.oid
        WHERE n.nspname = 'public';
    """))
    for row in res:
        print(row)
