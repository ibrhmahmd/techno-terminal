"""
005_add_group_level_id_to_sessions.py

Add group_level_id column to sessions table to establish
referential integrity between sessions and group levels.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004_add_competition_fee_column'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add group_level_id column (nullable for migration safety)
    op.add_column(
        'sessions',
        sa.Column(
            'group_level_id',
            sa.Integer(),
            sa.ForeignKey('group_levels.id', ondelete='SET NULL'),
            nullable=True
        )
    )
    
    # 2. Create index for performance
    op.create_index(
        'idx_sessions_group_level_id',
        'sessions',
        ['group_level_id']
    )
    
    # 3. Backfill existing sessions by joining on (group_id, level_number)
    op.execute("""
        UPDATE sessions s
        SET group_level_id = gl.id
        FROM group_levels gl
        WHERE s.group_id = gl.group_id 
          AND s.level_number = gl.level_number
          AND s.group_level_id IS NULL
    """)


def downgrade():
    # 1. Drop index
    op.drop_index('idx_sessions_group_level_id', table_name='sessions')
    
    # 2. Drop column
    op.drop_column('sessions', 'group_level_id')
