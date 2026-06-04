from sqlalchemy import create_engine, text
import os

engine = create_engine(os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/techno_terminal"))
with engine.connect() as conn:
    res = conn.execute(text("SELECT id, receipt_number, paid_at FROM receipts ORDER BY paid_at DESC LIMIT 10"))
    for row in res:
        print(row)
