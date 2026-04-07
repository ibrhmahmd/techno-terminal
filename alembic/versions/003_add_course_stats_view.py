"""
Add v_course_stats analytics view

Revision ID: 003
Revises: 002
Create Date: 2026-04-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the v_course_stats analytics view."""
    op.execute("""
        CREATE OR REPLACE VIEW v_course_stats AS
        SELECT
            c.id AS course_id,
            c.name AS course_name,
            COUNT(DISTINCT g.id) AS total_groups,
            COUNT(DISTINCT CASE WHEN g.status = 'active' THEN g.id END) AS active_groups,
            COUNT(DISTINCT CASE WHEN e.status IN ('active', 'completed', 'dropped') THEN e.student_id END) AS total_students_ever,
            COUNT(DISTINCT CASE WHEN e.status = 'active' THEN e.student_id END) AS active_students
        FROM courses c
        LEFT JOIN groups g ON g.course_id = c.id
        LEFT JOIN enrollments e ON e.group_id = g.id
        WHERE c.is_active = true
        GROUP BY c.id, c.name;
    """)


def downgrade() -> None:
    """Drop the v_course_stats view."""
    op.execute("DROP VIEW IF EXISTS v_course_stats;")
