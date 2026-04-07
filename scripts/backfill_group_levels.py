"""
Backfill existing groups into group_levels table

Run this after applying migration 002_add_group_lifecycle_tables.py
Creates group_levels rows for all existing active/completed groups.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlmodel import select
from app.db.connection import get_session
from app.modules.academics.models import Group, GroupLevel, Course


def backfill_group_levels():
    """Create group_levels records for all existing groups."""
    with get_session() as session:
        # Get all groups that don't have a corresponding group_levels entry
        stmt = (
            select(Group)
            .outerjoin(
                GroupLevel,
                (Group.id == GroupLevel.group_id) & (GroupLevel.level_number == Group.level_number)
            )
            .where(GroupLevel.id.is_(None))
        )
        
        groups = session.exec(stmt).all()
        
        print(f"Found {len(groups)} groups to backfill into group_levels")
        
        for group in groups:
            # Get course to determine sessions_planned
            course = session.get(Course, group.course_id)
            sessions_planned = course.sessions_per_level if course else 12
            
            # Create group_levels snapshot
            level = GroupLevel(
                group_id=group.id,
                level_number=group.level_number,
                course_id=group.course_id,
                instructor_id=group.instructor_id,
                sessions_planned=sessions_planned,
                price_override=None,  # Use course default
                status="active" if group.status == "active" else "completed",
                effective_from=group.started_at or datetime.utcnow(),
                effective_to=None if group.status == "active" else datetime.utcnow(),
            )
            session.add(level)
            print(f"  Created level {group.level_number} for group '{group.name}' (ID: {group.id})")
        
        session.commit()
        print(f"\nSuccessfully backfilled {len(groups)} groups into group_levels table")


if __name__ == "__main__":
    backfill_group_levels()
