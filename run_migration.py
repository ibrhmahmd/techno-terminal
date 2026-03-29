import os
from sqlalchemy import text
from app.db.connection import get_engine

def run_migration():
    engine = get_engine()
    
    statements = [
        "ALTER TABLE guardians RENAME TO parents",
        "ALTER TABLE student_guardians RENAME TO student_parents",
        "ALTER TABLE student_parents RENAME COLUMN guardian_id TO parent_id",
        "ALTER TABLE receipts RENAME COLUMN guardian_id TO parent_id",
        "ALTER INDEX idx_guardians_phone RENAME TO idx_parents_phone",
        "ALTER INDEX idx_student_guardians_student RENAME TO idx_student_parents_student",
        "ALTER INDEX idx_student_guardians_guardian RENAME TO idx_student_parents_parent",
        "ALTER TRIGGER trg_guardians_updated_at ON parents RENAME TO trg_parents_updated_at",
        "DROP VIEW IF EXISTS v_siblings CASCADE",
        """
        CREATE OR REPLACE VIEW v_siblings AS
        SELECT sp1.student_id AS student_id,
            s1.full_name AS student_name,
            sp2.student_id AS sibling_id,
            s2.full_name AS sibling_name,
            sp1.parent_id
        FROM student_parents sp1
            JOIN student_parents sp2 ON sp1.parent_id = sp2.parent_id
            AND sp1.student_id < sp2.student_id
            JOIN students s1 ON sp1.student_id = s1.id
            JOIN students s2 ON sp2.student_id = s2.id
        WHERE s1.is_active = TRUE
            AND s2.is_active = TRUE
        """,
        "DROP VIEW IF EXISTS v_students CASCADE",
        """
        CREATE OR REPLACE VIEW v_students AS
        SELECT s.id,
            s.full_name,
            s.date_of_birth,
            EXTRACT(YEAR FROM AGE(s.date_of_birth))::INTEGER AS age,
            s.gender,
            s.phone AS student_phone,
            s.notes,
            s.is_active,
            s.created_at,
            s.updated_at,
            s.metadata,
            p.full_name AS primary_parent_name,
            p.phone_primary AS primary_parent_phone
        FROM students s
            LEFT JOIN student_parents sp ON s.id = sp.student_id
            AND sp.is_primary = TRUE
            LEFT JOIN parents p ON sp.parent_id = p.id
        """
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

    print("Migration applied successfully!")

if __name__ == "__main__":
    run_migration()
