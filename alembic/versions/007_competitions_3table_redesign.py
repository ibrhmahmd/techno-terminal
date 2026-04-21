"""
007_competitions_3table_redesign.py

Competitions module redesign:
- Enable citext extension for case-insensitive text
- Add soft delete to competitions and teams
- Add edition_year to competitions
- Add category/subcategory citext columns to teams
- Add fee, placement columns to teams
- Create trim trigger for category/subcategory normalization
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import CITEXT

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006_add_employee_user_id'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Enable citext extension
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # 2. Add soft delete columns to competitions
    op.add_column('competitions', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('competitions', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_competitions_deleted_by',
        'competitions',
        'users',
        ['deleted_by'],
        ['id']
    )

    # 3. Add edition_year to competitions and migrate data
    op.add_column('competitions', sa.Column('edition_year', sa.Integer(), nullable=True))

    # Migrate edition string to edition_year
    op.execute("""
        UPDATE competitions
        SET edition_year = CAST(SUBSTRING(edition FROM '[0-9]+') AS INTEGER)
        WHERE edition ~ '[0-9]+'
    """)
    op.execute("""
        UPDATE competitions
        SET edition_year = EXTRACT(YEAR FROM COALESCE(competition_date, NOW()))
        WHERE edition_year IS NULL
    """)

    # Make edition_year NOT NULL
    op.alter_column('competitions', 'edition_year', nullable=False)

    # Add unique constraint on name + edition_year
    op.create_unique_constraint(
        'uq_competitions_name_edition_year',
        'competitions',
        ['name', 'edition_year']
    )

    # 4. Add new columns to teams table
    op.add_column('teams', sa.Column('competition_id', sa.Integer(), nullable=True))
    op.add_column('teams', sa.Column('category', CITEXT(), nullable=True))
    op.add_column('teams', sa.Column('subcategory', CITEXT(), nullable=True))
    op.add_column('teams', sa.Column('fee', sa.Numeric(10, 2), nullable=True))
    op.add_column('teams', sa.Column('placement_rank', sa.Integer(), nullable=True))
    op.add_column('teams', sa.Column('placement_label', sa.String(100), nullable=True))
    op.add_column('teams', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('teams', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('teams', sa.Column('deleted_by', sa.Integer(), nullable=True))

    # 5. Create foreign keys for teams
    op.create_foreign_key(
        'fk_teams_competition_id',
        'teams',
        'competitions',
        ['competition_id'],
        ['id']
    )
    op.create_foreign_key(
        'fk_teams_deleted_by',
        'teams',
        'users',
        ['deleted_by'],
        ['id']
    )

    # 6. Migrate teams data from old structure
    # Get competition_id from category_id
    op.execute("""
        UPDATE teams t
        SET competition_id = c.competition_id,
            category = c.category_name::citext,
            subcategory = NULL,
            fee = comp.fee_per_student
        FROM competition_categories c
        JOIN competitions comp ON c.competition_id = comp.id
        WHERE t.category_id = c.id
    """)

    # Make competition_id NOT NULL after migration
    op.alter_column('teams', 'competition_id', nullable=False)
    op.alter_column('teams', 'category', nullable=False)

    # 7. Create trim trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION normalize_team_fields()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.category := TRIM(NEW.category);
            NEW.subcategory := TRIM(NEW.subcategory);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # 8. Create trigger on teams table
    op.execute("""
        CREATE TRIGGER normalize_team_fields_trigger
        BEFORE INSERT OR UPDATE ON teams
        FOR EACH ROW EXECUTE FUNCTION normalize_team_fields()
    """)

    # 9. Create index on category/subcategory for performance
    op.create_index('ix_teams_category', 'teams', ['category'])
    op.create_index('ix_teams_competition_id', 'teams', ['competition_id'])


def downgrade():
    # Reverse order of operations

    # 9. Drop indexes
    op.drop_index('ix_teams_competition_id', table_name='teams')
    op.drop_index('ix_teams_category', table_name='teams')

    # 8. Drop trigger
    op.execute("DROP TRIGGER IF EXISTS normalize_team_fields_trigger ON teams")

    # 7. Drop function
    op.execute("DROP FUNCTION IF EXISTS normalize_team_fields()")

    # 6. Cannot restore old data structure, but can drop new columns
    op.drop_constraint('fk_teams_competition_id', 'teams', type_='foreignkey')
    op.drop_constraint('fk_teams_deleted_by', 'teams', type_='foreignkey')

    # 5. Drop new columns from teams
    op.drop_column('teams', 'deleted_by')
    op.drop_column('teams', 'deleted_at')
    op.drop_column('teams', 'notes')
    op.drop_column('teams', 'placement_label')
    op.drop_column('teams', 'placement_rank')
    op.drop_column('teams', 'fee')
    op.drop_column('teams', 'subcategory')
    op.drop_column('teams', 'category')
    op.drop_column('teams', 'competition_id')

    # 4. Drop edition_year and unique constraint
    op.drop_constraint('uq_competitions_name_edition_year', 'competitions', type_='unique')
    op.drop_column('competitions', 'edition_year')

    # 3. Drop soft delete columns from competitions
    op.drop_constraint('fk_competitions_deleted_by', 'competitions', type_='foreignkey')
    op.drop_column('competitions', 'deleted_by')
    op.drop_column('competitions', 'deleted_at')

    # 2. Note: We keep citext extension as it may be used elsewhere
