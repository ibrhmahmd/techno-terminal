import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db.connection import get_engine
from sqlalchemy import text
import pprint

engine = get_engine()
with engine.connect() as conn:
    print("=== Students Constraints ===")
    res = conn.execute(text("""
        SELECT conname, pg_get_constraintdef(c.oid) 
        FROM pg_constraint c 
        JOIN pg_namespace n ON n.oid = c.connamespace 
        WHERE conrelid = 'students'::regclass;
    """)).mappings().all()
    pprint.pprint([dict(r) for r in res])

    print("=== Students Indexes ===")
    res = conn.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'students';
    """)).mappings().all()
    pprint.pprint([dict(r) for r in res])
