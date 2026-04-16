"""
004_add_competition_fee_column.py

Add fee_per_student column to competitions table.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003_add_course_stats_view'
branch_labels = None
depends_on = None


def upgrade():
    # Add fee_per_student column to competitions table
    op.add_column(
        'competitions',
        sa.Column('fee_per_student', sa.Float(), nullable=True, server_default='0.0')
    )


def downgrade():
    # Remove fee_per_student column
    op.drop_column('competitions', 'fee_per_student')
