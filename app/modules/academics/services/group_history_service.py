"""
app/modules/academics/services/group_history_service.py
────────────────────────────────────────────────────
Service class for Group History and Lifecycle tracking.
"""
from app.db.connection import get_session
from app.modules.academics import repositories as repo


class GroupHistoryService:
    """Service for recording group lifecycle history (course changes, enrollment progression)."""

    def record_course_change(
        self,
        group_id: int,
        old_course_id: int | None,
        new_course_id: int,
        assigned_by_user_id: int | None = None,
        notes: str | None = None,
    ) -> None:
        """
        Record a course assignment change.
        
        Args:
            group_id: The group changing courses
            old_course_id: Previous course (None if initial assignment)
            new_course_id: New course being assigned
            assigned_by_user_id: User who made the change
            notes: Optional notes about the change
        """
        with get_session() as session:
            # Complete old course assignment if exists
            if old_course_id:
                repo.complete_course_assignment(session, group_id, old_course_id)
            
            # Record new assignment
            repo.record_course_assignment(
                session, group_id, new_course_id, assigned_by_user_id, notes
            )
            session.commit()

    def record_enrollment_progression(
        self,
        enrollment_id: int,
        old_level_id: int,
        new_level_id: int,
        student_id: int,
    ) -> None:
        """
        Record when a student progresses to a new level.
        
        Args:
            enrollment_id: The enrollment record
            old_level_id: Previous level (to mark as completed)
            new_level_id: New level (to record as active)
            student_id: Student being progressed
        """
        with get_session() as session:
            # Complete old level
            repo.complete_enrollment_level(session, enrollment_id, old_level_id)
            
            # Record new level entry
            repo.record_enrollment_level_transition(
                session, enrollment_id, new_level_id, student_id
            )
            session.commit()
