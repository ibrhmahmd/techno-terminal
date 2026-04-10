"""
app/modules/enrollments/services/enrollment_migration_service.py
──────────────────────────────────────────────────────────────
Service for handling enrollment transitions between group levels.
Manages the migration of active enrollments when groups progress.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlmodel import Session, select

from app.db.connection import get_session
from app.modules.academics.models import Course, Group
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.academics.schemas.scheduling_dtos import (
    MigrateEnrollmentsDTO,
    EnrollmentMigrationResult,
)


class EnrollmentMigrationService:
    """
    Handles enrollment migrations between levels.
    Responsible for completing old enrollments and creating new ones.
    """

    def migrate_enrollments_to_next_level(
        self,
        session: Session,
        data: MigrateEnrollmentsDTO
    ) -> EnrollmentMigrationResult:
        """
        Migrate active enrollments from one level to the next.
        
        Process:
        1. Find all active enrollments for the source level
        2. Mark old enrollments as 'completed'
        3. Create new enrollments for the target level
        4. Preserve discounts from original enrollments
        5. Calculate new amount_due based on course/override
        
        Args:
            session: Database session (managed by caller)
            data: Migration parameters including group_id, from_level, to_level
            
        Returns:
            EnrollmentMigrationResult with counts and IDs
        """
        # Get the group for course info
        group = session.get(Group, data.group_id)
        if not group:
            raise ValueError(f"Group {data.group_id} not found")
        
        # Get course for pricing
        course = session.get(Course, group.course_id)
        if not course:
            raise ValueError(f"Course {group.course_id} not found")
        
        # Find active enrollments for the source level
        stmt = select(Enrollment).where(
            Enrollment.group_id == data.group_id,
            Enrollment.level_number == data.from_level,
            Enrollment.status == "active"
        )
        active_enrollments = list(session.exec(stmt).all())
        
        migrated_ids: List[int] = []
        new_enrollment_ids: List[int] = []
        total_amount_due = 0.0
        
        for enrollment in active_enrollments:
            # Mark old enrollment as completed
            enrollment.status = "completed"
            enrollment.completed_at = datetime.utcnow()
            session.add(enrollment)
            migrated_ids.append(enrollment.id)
            
            # Determine price for new level
            if data.price_override is not None:
                new_amount_due = float(data.price_override)
            else:
                new_amount_due = float(course.price_per_level) if course.price_per_level else 0.0
            
            total_amount_due += new_amount_due
            
            # Create new enrollment for next level
            discount = enrollment.discount_applied if data.preserve_discounts else 0.0
            
            new_enrollment = Enrollment(
                student_id=enrollment.student_id,
                group_id=data.group_id,
                level_number=data.to_level,
                amount_due=new_amount_due,
                discount_applied=discount,
                status="active",
                enrolled_at=datetime.utcnow(),
            )
            session.add(new_enrollment)
            session.flush()  # Get the new enrollment ID
            new_enrollment_ids.append(new_enrollment.id)
        
        return EnrollmentMigrationResult(
            count=len(active_enrollments),
            old_level=data.from_level,
            new_level=data.to_level,
            migrated_enrollment_ids=migrated_ids,
            new_enrollment_ids=new_enrollment_ids,
            total_amount_due=total_amount_due,
        )

    def complete_level_enrollments(
        self,
        session: Session,
        group_id: int,
        level_number: int,
        completion_notes: Optional[str] = None
    ) -> List[int]:
        """
        Mark all active enrollments for a level as completed.
        Used when a level is completed but NOT progressing (e.g., group disbanding).
        
        Args:
            session: Database session
            group_id: The group ID
            level_number: Level to complete
            completion_notes: Optional notes about completion
            
        Returns:
            List of completed enrollment IDs
        """
        stmt = select(Enrollment).where(
            Enrollment.group_id == group_id,
            Enrollment.level_number == level_number,
            Enrollment.status == "active"
        )
        enrollments = list(session.exec(stmt).all())
        
        completed_ids: List[int] = []
        for enrollment in enrollments:
            enrollment.status = "completed"
            enrollment.completed_at = datetime.utcnow()
            # Store notes in metadata if needed
            if completion_notes:
                if enrollment.enrollment_metadata is None:
                    enrollment.enrollment_metadata = {}
                enrollment.enrollment_metadata["completion_notes"] = completion_notes
            session.add(enrollment)
            completed_ids.append(enrollment.id)
        
        return completed_ids

    def get_active_enrollments_for_level(
        self,
        group_id: int,
        level_number: int
    ) -> List[Enrollment]:
        """
        Get all active enrollments for a specific group level.
        
        Args:
            group_id: The group ID
            level_number: The level number
            
        Returns:
            List of active Enrollment records
        """
        with get_session() as session:
            stmt = select(Enrollment).where(
                Enrollment.group_id == group_id,
                Enrollment.level_number == level_number,
                Enrollment.status == "active"
            )
            return list(session.exec(stmt).all())

    def validate_migration_prerequisites(
        self,
        session: Session,
        group_id: int,
        from_level: int,
        to_level: int
    ) -> tuple[bool, str]:
        """
        Validate that enrollment migration can proceed.
        
        Checks:
        - Group exists and is active
        - Source level exists and is active or completed
        - Target level exists and is active
        - There are enrollments to migrate
        
        Returns:
            (is_valid, error_message)
        """
        from app.modules.academics.models import GroupLevel
        
        # Check group exists
        group = session.get(Group, group_id)
        if not group:
            return False, f"Group {group_id} not found"
        
        if group.status != "active":
            return False, f"Group {group_id} is not active (status: {group.status})"
        
        # Check source level
        source_level_stmt = select(GroupLevel).where(
            GroupLevel.group_id == group_id,
            GroupLevel.level_number == from_level
        )
        source_level = session.exec(source_level_stmt).first()
        if not source_level:
            return False, f"Source level {from_level} not found for group {group_id}"
        
        # Check target level
        target_level_stmt = select(GroupLevel).where(
            GroupLevel.group_id == group_id,
            GroupLevel.level_number == to_level
        )
        target_level = session.exec(target_level_stmt).first()
        if not target_level:
            return False, f"Target level {to_level} not found for group {group_id}"
        
        if target_level.status != "active":
            return False, f"Target level {to_level} is not active (status: {target_level.status})"
        
        # Check for enrollments to migrate
        enrollment_stmt = select(Enrollment).where(
            Enrollment.group_id == group_id,
            Enrollment.level_number == from_level,
            Enrollment.status == "active"
        )
        enrollments = list(session.exec(enrollment_stmt).all())
        if not enrollments:
            return False, f"No active enrollments found for level {from_level}"
        
        return True, f"OK - {len(enrollments)} enrollments ready to migrate"
