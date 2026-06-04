import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.db.connection import get_engine
from sqlalchemy import text

engine = get_engine()
with engine.begin() as conn:
    with open('db/migrations/067_fix_notification_templates.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    conn.execute(text(sql))

print("Migration applied successfully.")
