import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from app.db.connection import get_engine
from sqlalchemy import text
import pprint

engine = get_engine()
with engine.connect() as conn:
    print("=== Additional Recipients ===")
    res = conn.execute(text('SELECT * FROM notification_additional_recipients')).mappings().all()
    pprint.pprint([dict(r) for r in res])
    
    print("\n=== Admin Notification Settings ===")
    res = conn.execute(text('SELECT * FROM admin_notification_settings')).mappings().all()
    pprint.pprint([dict(r) for r in res])
