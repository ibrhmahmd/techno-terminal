import psycopg2
import os

DATABASE_URL = "postgresql://postgres.srbppkcvrgioneitktdj:67OYU5HZeBYiVBs5@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()

with open("db/migrations/074_audit_views.sql", "r", encoding="utf-8") as f:
    sql = f.read()

cur.execute(sql)
cur.execute("SELECT viewname FROM pg_views WHERE schemaname = 'public' AND viewname LIKE 'v_audit%' ORDER BY viewname")
views = [r[0] for r in cur.fetchall()]
print("Views created:", views)

conn.close()
