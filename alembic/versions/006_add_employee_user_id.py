"""
006_add_employee_user_id.py

Add user_id column to employees table for linking to users.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005_add_group_level_id_to_sessions'
branch_labels = None
depends_on = None


def upgrade():
    # Add user_id column to employees table
    op.add_column(
        'employees',
        sa.Column('user_id', sa.Integer(), nullable=True)
    )
    # Create unique constraint and foreign key
    op.create_unique_constraint(
        'uq_employees_user_id',
        'employees',
        ['user_id']
    )
    op.create_foreign_key(
        'fk_employees_user_id',
        'employees',
        'users',
        ['user_id'],
        ['id']
    )


def downgrade():
    # Remove user_id column
    op.drop_constraint('fk_employees_user_id', 'employees', type_='foreignkey')
    op.drop_constraint('uq_employees_user_id', 'employees', type_='unique')
    op.drop_column('employees', 'user_id')