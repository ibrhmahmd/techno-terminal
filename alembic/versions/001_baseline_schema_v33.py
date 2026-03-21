"""Baseline schema v3.3 — DDL applied via db/schema.sql

Revision ID: 001_baseline_v33
Revises:
Create Date: 2026-03-21

Greenfield: run `psql -f db/schema.sql` then `alembic stamp 001_baseline_v33`.
Future revisions should contain incremental op.* changes.
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "001_baseline_v33"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
