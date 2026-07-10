"""
Apply migration 076 — BI Report Views
Run from repo root: python scratch/apply_076.py
"""
import os, sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL") or \
    "postgresql://postgres.srbppkcvrgioneitktdj:67OYU5HZeBYiVBs5@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

print("Applying migration 076_bi_report_views.sql ...")
with open("db/migrations/076_bi_report_views.sql", "r", encoding="utf-8") as f:
    sql = f.read()

# Split on semicolons and execute each statement so the verification SELECT
# result is consumed properly (psycopg2 doesn't buffer multiple result sets).
statements = [s.strip() for s in sql.split(";") if s.strip()]
errors = []
for i, stmt in enumerate(statements):
    try:
        cur.execute(stmt)
        # Consume any result set
        try:
            rows = cur.fetchall()
            if rows:
                cols = [d[0] for d in cur.description]
                for row in rows:
                    print("  ", dict(zip(cols, row)))
        except Exception:
            pass
    except Exception as e:
        print(f"  [WARN] Statement {i+1} failed: {e}")
        errors.append((i+1, str(e)))

cur.execute(
    "SELECT viewname FROM pg_views "
    "WHERE schemaname = 'public' AND viewname LIKE 'v_bi%' "
    "ORDER BY viewname"
)
views = [r[0] for r in cur.fetchall()]
print(f"\n[OK] {len(views)} BI views in database:")
for v in views:
    print(f"   {v}")

# Quick sanity: read KPI header
try:
    cur.execute("SELECT * FROM v_bi_kpi_header")
    row = dict(zip([d[0] for d in cur.description], cur.fetchone()))
    print("\nKPI Header snapshot:")
    for k, v in row.items():
        print(f"   {k}: {v}")
except Exception as e:
    print(f"\n[WARN] KPI header query failed: {e}")

if errors:
    print(f"\n[WARN] {len(errors)} statement(s) had errors:")
    for idx, msg in errors:
        print(f"   Statement {idx}: {msg}")

conn.close()
print("\nDone.")
