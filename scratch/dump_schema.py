import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with open("scratch/schema_dump_output.txt", "w", encoding="utf-8") as f:
    with engine.connect() as conn:
        f.write("=== ENUMS ===\n")
        res = conn.execute(text("""
            SELECT t.typname, e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            ORDER BY t.typname, e.enumsortorder;
        """))
        enums = {}
        for row in res:
            enums.setdefault(row[0], []).append(row[1])
        for name, labels in enums.items():
            f.write(f"CREATE TYPE {name} AS ENUM ({', '.join(f"'{l}'" for l in labels)});\n")

        f.write("\n=== TABLES ===\n")
        res_tables = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        tables = [r[0] for r in res_tables]
        
        for t in tables:
            f.write(f"\nTABLE: {t}\n")
            res_cols = conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{t}'
                ORDER BY ordinal_position;
            """))
            for col in res_cols:
                name, dtype, nullable, default = col
                null_str = "NULL" if nullable == "YES" else "NOT NULL"
                def_str = f"DEFAULT {default}" if default else ""
                f.write(f"  {name} {dtype} {null_str} {def_str}\n")
                
            # Get constraints for this table
            res_con = conn.execute(text(f"""
                SELECT conname, pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_class r ON c.conrelid = r.oid
                JOIN pg_catalog.pg_namespace n ON n.oid = c.connamespace
                WHERE r.relname = '{t}' AND n.nspname = 'public';
            """))
            for con in res_con:
                f.write(f"  CONSTRAINT {con[0]} {con[1]}\n")

        f.write("\n=== VIEWS ===\n")
        res_views = conn.execute(text("""
            SELECT table_name, view_definition
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        for row in res_views:
            f.write(f"\nVIEW: {row[0]}\n")
            f.write(row[1] + "\n")

        f.write("\n=== TRIGGERS ===\n")
        res_trig = conn.execute(text("""
            SELECT tgname, pg_get_triggerdef(t.oid)
            FROM pg_trigger t
            JOIN pg_class c ON t.tgrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public' AND t.tgisinternal = false
            ORDER BY tgname;
        """))
        for row in res_trig:
            f.write(f"TRIGGER: {row[0]}\n")
            f.write(f"  {row[1]}\n")
