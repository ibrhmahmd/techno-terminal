"""
app/modules/academics/group/core/service.py
──────────────────────────────────────
Service class for Group Core business logic.
"""
from app.db.connection import get_session
from app.shared.audit_utils import apply_update_audit
from app.shared.exceptions import NotFoundError
from app.modules.academics.models import Group
from app.modules.academics.group.core.schemas import ScheduleGroupInput, UpdateGroupDTO
import app.modules.academics.group.core.repository as repo
import app.modules.academics.course.repository as course_repo
from app.modules.hr.models import Employee


class GroupCoreService:
    def schedule_group(self, data: ScheduleGroupInput) -> Group:
        """Schedules a new standalone group."""
        from app.modules.academics.helpers.time_helpers import fmt_12h
        with get_session() as session:
            # Validate FKs
            course = course_repo.get_course_by_id(session, data.course_id)
            if not course:
                raise NotFoundError(f"Course {data.course_id} not found.")

            instructor = session.get(Employee, data.instructor_id)
            if not instructor:
                raise NotFoundError(f"Instructor {data.instructor_id} not found.")

            auto_name = f"{course.name} - {data.default_day} {fmt_12h(data.default_time_start)}"

            group = Group(
                name=auto_name,
                course_id=data.course_id,
                instructor_id=data.instructor_id,
                level_number=1,
                default_day=data.default_day,
                default_time_start=data.default_time_start,
                default_time_end=data.default_time_end,
                max_capacity=data.max_capacity,
                notes=data.notes,
            )
            from app.shared.audit_utils import apply_create_audit
            apply_create_audit(group)
            return repo.create_group(session, group)

    def update_group(self, group_id: int, data: UpdateGroupDTO) -> Group:
        with get_session() as session:
            group = repo.get_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            for k, v in data.model_dump(exclude_unset=True).items():
                if hasattr(group, k) and k != "id":
                    setattr(group, k, v)
            apply_update_audit(group)
            session.add(group)
            session.commit()
            session.refresh(group)
            return group

    def get_group_by_id(self, group_id: int) -> Group | None:
        with get_session() as session:
            group = repo.get_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            return group
            
    def update_group_status(self, group_id: int, status: str) -> Group:
        with get_session() as session:
            group = repo.update_group_status(session, group_id, status)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            session.commit()
            session.refresh(group)
            return group

    def archive_group(self, group_id: int) -> Group:
        """
        Archive a group. The group has finished its lifecycle and is kept for
        historical reference. Enrollments remain — status becomes 'archived'.
        """
        from app.modules.academics.constants import GROUP_STATUS_COMPLETED
        with get_session() as session:
            group = repo.get_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            group.status = GROUP_STATUS_COMPLETED
            apply_update_audit(group)
            session.add(group)
            session.commit()
            session.refresh(group)
            return group

    def deactivate_group(self, group_id: int) -> Group:
        """
        Deactivate a group. Different from archiving — the group is suspended
        (e.g. on hold, no new sessions). Status becomes 'inactive'.
        """
        from app.modules.academics.constants import GROUP_STATUS_INACTIVE
        with get_session() as session:
            group = repo.get_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
            group.status = GROUP_STATUS_INACTIVE
            apply_update_audit(group)
            session.add(group)
            session.commit()
            session.refresh(group)
            return group
