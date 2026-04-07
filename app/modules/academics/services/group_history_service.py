"""
app/modules/academics/services/group_history_service.py
────────────────────────────────────────────────────
Service class for Group History and Lifecycle tracking.
"""
from app.db.connection import get_session
from app.modules.academics import repositories as repo


class GroupHistoryService:
    """Service for aggregating and retrieving group lifecycle history."""

    def get_full_lifecycle(self, group_id: int) -> dict:
        """
        Get complete lifecycle data for a group.
        
        Returns:
            Dict containing:
            - group_id, group_name, created_at
            - current_level, total_levels, completed_levels
            - levels_timeline: chronological level snapshots
            - course_assignments: course change history
        """
        with get_session() as session:
            return repo.get_full_group_lifecycle(session, group_id)

    def get_course_assignments(self, group_id: int) -> list[dict]:
        """Get chronological course assignment history."""
        with get_session() as session:
            records = repo.get_group_course_assignments(session, group_id)
            return [
                {
                    "course_id": r.course_id,
                    "assigned_at": r.assigned_at,
                    "removed_at": r.removed_at,
                    "assigned_by_user_id": r.assigned_by_user_id,
                    "notes": r.notes,
                }
                for r in records
            ]

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

    def get_enrollment_transitions(
        self, group_id: int, student_id: int | None = None
    ) -> list[dict]:
        """
        Get enrollment level transitions for a group.
        
        Args:
            group_id: Group to query
            student_id: Optional specific student filter
        
        Returns:
            List of transition records
        """
        with get_session() as session:
            records = repo.get_enrollment_transitions(session, group_id, student_id)
            return [
                {
                    "enrollment_id": r.enrollment_id,
                    "student_id": r.student_id,
                    "group_level_id": r.group_level_id,
                    "level_entered_at": r.level_entered_at,
                    "level_completed_at": r.level_completed_at,
                    "status": r.status,
                }
                for r in records
            ]

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

    def get_levels_timeline(self, group_id: int) -> list[dict]:
        """
        Get chronological timeline of group levels with enriched data.
        
        Returns:
            List of level snapshots with course and instructor names
        """
        with get_session() as session:
            levels = repo.get_group_levels_timeline(session, group_id)
            result = []
            for level in levels:
                course = session.get(repo.Course, level.course_id)
                instructor = None
                if level.instructor_id:
                    from app.modules.hr.hr_models import Employee
                    instructor = session.get(Employee, level.instructor_id)
                
                result.append({
                    "id": level.id,
                    "level_number": level.level_number,
                    "course_id": level.course_id,
                    "course_name": course.name if course else None,
                    "instructor_id": level.instructor_id,
                    "instructor_name": instructor.full_name if instructor else None,
                    "sessions_planned": level.sessions_planned,
                    "price_override": level.price_override,
                    "status": level.status,
                    "effective_from": level.effective_from,
                    "effective_to": level.effective_to,
                })
            return result
