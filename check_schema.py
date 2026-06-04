import sys; sys.path.insert(0, '.')
from app.db.connection import get_engine
from sqlalchemy import text
engine = get_engine()
with engine.connect() as conn:
    r = conn.execute(text(
        "SELECT column_name, data_type, column_default, is_nullable "
        "FROM information_schema.columns WHERE table_name='notification_templates' "
        "ORDER BY ordinal_position"
    ))
    for row in r:
        print(row)
