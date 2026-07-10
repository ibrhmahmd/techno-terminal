"""
Apply migration 075 — Finance Monitoring Views
Run from the repo root: python scratch/apply_075.py
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL") or \
    "postgresql://postgres.srbppkcvrgioneitktdj:67OYU5HZeBYiVBs5@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

print("Applying migration 075_finance_views.sql ...")
with open("db/migrations/075_finance_views.sql", "r", encoding="utf-8") as f:
    sql = f.read()

cur.execute(sql)
cur.fetchall()   # consume the verification SELECT result

cur.execute(
    "SELECT viewname FROM pg_views "
    "WHERE schemaname = 'public' AND viewname LIKE 'v_finance%' "
    "ORDER BY viewname"
)
views = [r[0] for r in cur.fetchall()]
print(f"\n[OK] {len(views)} finance views created:")
for v in views:
    print(f"   {v}")

# Quick sanity check on summary view
cur.execute("SELECT * FROM v_finance_summary")
row = dict(zip([d[0] for d in cur.description], cur.fetchone()))
print("\nFinance Summary snapshot:")
for k, v in row.items():
    print(f"   {k}: {v}")

conn.close()
print("\nDone.")
