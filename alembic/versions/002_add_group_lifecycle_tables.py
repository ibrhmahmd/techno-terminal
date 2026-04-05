"""
Add group_levels, group_course_history, group_competition_participation tables

Revision ID: 002
Revises: 001
Create Date: 2026-04-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create group_levels table
    op.create_table(
        'group_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('level_number', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('instructor_id', sa.Integer(), nullable=True),
        sa.Column('sessions_planned', sa.Integer(), server_default='12'),
        sa.Column('price_override', sa.Numeric(10, 2), nullable=True),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('effective_from', sa.DateTime(), nullable=False),
        sa.Column('effective_to', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['instructor_id'], ['employees.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'level_number')
    )
    op.create_index('idx_group_levels_group_id', 'group_levels', ['group_id'])
    op.create_index('idx_group_levels_status', 'group_levels', ['status'])
    
    # Create group_course_history table
    op.create_table(
        'group_course_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('removed_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_by_user_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_group_course_history_group_id', 'group_course_history', ['group_id'])
    
    # Create group_competition_participation table
    op.create_table(
        'group_competition_participation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('competition_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('entered_at', sa.DateTime(), nullable=False),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('final_placement', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id']),
        sa.ForeignKeyConstraint(['competition_id'], ['competitions.id']),
        sa.ForeignKeyConstraint(['category_id'], ['competition_categories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'team_id', 'competition_id')
    )
    op.create_index('idx_gcp_group_id', 'group_competition_participation', ['group_id'])
    op.create_index('idx_gcp_team_id', 'group_competition_participation', ['team_id'])
    op.create_index('idx_gcp_active', 'group_competition_participation', ['is_active'])
    
    # Create enrollment_level_history table
    op.create_table(
        'enrollment_level_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('group_level_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('level_entered_at', sa.DateTime(), nullable=False),
        sa.Column('level_completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id']),
        sa.ForeignKeyConstraint(['group_level_id'], ['group_levels.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_enrollment_level_history_enrollment', 'enrollment_level_history', ['enrollment_id'])
    op.create_index('idx_enrollment_level_history_student', 'enrollment_level_history', ['student_id'])
    op.create_index('idx_enrollment_level_history_level', 'enrollment_level_history', ['group_level_id'])


def downgrade() -> None:
    op.drop_index('idx_enrollment_level_history_level', table_name='enrollment_level_history')
    op.drop_index('idx_enrollment_level_history_student', table_name='enrollment_level_history')
    op.drop_index('idx_enrollment_level_history_enrollment', table_name='enrollment_level_history')
    op.drop_table('enrollment_level_history')
    
    op.drop_index('idx_gcp_active', table_name='group_competition_participation')
    op.drop_index('idx_gcp_team_id', table_name='group_competition_participation')
    op.drop_index('idx_gcp_group_id', table_name='group_competition_participation')
    op.drop_table('group_competition_participation')
    
    op.drop_index('idx_group_course_history_group_id', table_name='group_course_history')
    op.drop_table('group_course_history')
    
    op.drop_index('idx_group_levels_status', table_name='group_levels')
    op.drop_index('idx_group_levels_group_id', table_name='group_levels')
    op.drop_table('group_levels')
