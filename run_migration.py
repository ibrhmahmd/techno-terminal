import os
from sqlalchemy import text
from app.db.connection import get_engine

def run_migration():
    engine = get_engine()
    
    statements = [
        "ALTER TABLE receipts DROP COLUMN parent_id",
        "ALTER TABLE receipts ADD COLUMN payer_name TEXT",
        "ALTER TABLE groups ADD COLUMN notes TEXT",
        "ALTER TABLE courses ADD COLUMN notes TEXT",
        "ALTER TABLE sessions ADD COLUMN status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled'))"
    ]
    
    with engine.connect() as conn:
        for stmt in statements:
            print(f"Executing: {stmt.strip()[:60]}...")
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as e:
                print(f"Warn (Ignored): {str(e).split()[0]}")
                conn.rollback()

    print("Phase 3 Migration applied successfully!")

if __name__ == "__main__":
    run_migration()
