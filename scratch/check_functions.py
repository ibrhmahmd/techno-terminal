import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    res = conn.execute(text("""
        SELECT p.proname, pg_get_functiondef(p.oid)
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' 
          AND p.prokind = 'f';
    """))
    for row in res:
        print(f"FUNCTION: {row[0]}")
        print(row[1])
        print("-" * 40)
