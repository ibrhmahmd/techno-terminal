import sys
import os
import re
from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:34373839@localhost:5432/techno"

schema_files = [
    "db/schema/00_extensions.sql",
    "db/schema/01_enums.sql",
    "db/schema/02_tables_core.sql",
    "db/schema/03_tables_crm.sql",
    "db/schema/04_tables_academics.sql",
    "db/schema/05_tables_enrollments.sql",
    "db/schema/06_tables_finance.sql",
    "db/schema/07_tables_competitions.sql",
    "db/schema/08_tables_notifications.sql",
    "db/schema/09_tables_history.sql",
    "db/schema/10_tables_supabase.sql",
    "db/schema/20_indexes.sql",
    "db/schema/30_views.sql",
    "db/schema/40_functions.sql",
    "db/schema/50_triggers.sql",
    "db/schema/60_constraints.sql",
    "db/schema/90_seed_data.sql",
]

engine = create_engine(db_url)

def split_sql_statements(sql_text):
    statements = []
    current_statement = []
    in_dollar_quote = False
    dollar_tag = None
    
    tag_pattern = re.compile(r'\$[a-zA-Z0-9_]*\$')
    
    lines = sql_text.split("\n")
    for line in lines:
        pos = 0
        while pos < len(line):
            if not in_dollar_quote:
                match = tag_pattern.search(line, pos)
                if match:
                    dollar_tag = match.group(0)
                    in_dollar_quote = True
                    pos = match.end()
                else:
                    break
            else:
                idx = line.find(dollar_tag, pos)
                if idx != -1:
                    in_dollar_quote = False
                    pos = idx + len(dollar_tag)
                    dollar_tag = None
                else:
                    break
                    
        current_statement.append(line)
        
        if not in_dollar_quote and line.rstrip().endswith(";"):
            statements.append("\n".join(current_statement))
            current_statement = []
            
    if current_statement:
        stmt = "\n".join(current_statement).strip()
        if stmt:
            statements.append(stmt)
            
    return [s.strip() for s in statements if s.strip()]

def clean_statement(stmt):
    cleaned_lines = []
    for line in stmt.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("--"):
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()

print(f"Connecting to local database: {db_url}")
with engine.connect() as conn:
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")
    
    print("Dropping public schema to start clean...")
    conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
    conn.execute(text("CREATE SCHEMA public;"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
    
    for sql_file in schema_files:
        print(f"Applying {sql_file}...")
        if not os.path.exists(sql_file):
            print(f"Warning: file {sql_file} does not exist. Skipping.")
            continue
            
        with open(sql_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        statements = split_sql_statements(content)
        
        for raw_stmt in statements:
            stmt = clean_statement(raw_stmt)
            if not stmt:
                continue
            try:
                conn.execute(text(stmt))
            except Exception as e:
                print(f"ERROR executing statement in {sql_file}:")
                print(stmt)
                print(f"Error details: {e}")
                sys.exit(1)

print("All schema files applied successfully to the local database!")
