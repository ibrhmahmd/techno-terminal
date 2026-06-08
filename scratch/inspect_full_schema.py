import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    print("=== LIVE TABLES AND COLUMNS ===")
    res = conn.execute(text("""
        SELECT table_name, column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name IN (
            SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        )
        ORDER BY table_name, ordinal_position;
    """))
    
    current_table = None
    for row in res:
        table, col, dtype, nullable, default = row
        if table != current_table:
            print(f"\nTABLE: {table}")
            current_table = table
        print(f"  - {col} ({dtype}) | Nullable: {nullable} | Default: {default}")
        
    print("\n=== LIVE VIEWS ===")
    res = conn.execute(text("""
        SELECT table_name, view_definition
        FROM information_schema.views
        WHERE table_schema = 'public';
    """))
    for row in res:
        print(f"VIEW: {row[0]}")
