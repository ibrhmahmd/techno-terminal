"""
app/modules/academics/services/group_service.py
──────────────────────────────────────
Service class for Group Core business logic.
"""
from app.db.uow import UnitOfWork
from app.shared.audit_utils import apply_update_audit
from app.shared.exceptions import NotFoundError
from app.modules.academics.models import Group
from app.modules.academics.schemas.group_schemas import ScheduleGroupInput, UpdateGroupDTO
from app.modules.academics.repositories.group_repository import GroupRepository
from app.modules.academics.repositories.course_repository import CourseRepository
from app.modules.hr.models import Employee


class GroupCoreService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._repo = GroupRepository(uow.session)
        self._course_repo = CourseRepository(uow.session)

    def schedule_group(self, data: ScheduleGroupInput) -> Group:
        """Schedules a new standalone group."""
        from app.shared.time_helpers import fmt_12h
        # Validate FKs
        course = self._course_repo.get_course_by_id(data.course_id)
        if not course:
            raise NotFoundError(f"Course {data.course_id} not found.")

        instructor = self._uow.session.get(Employee, data.instructor_id)
        if not instructor:
            raise NotFoundError(f"Instructor {data.instructor_id} not found.")

        auto_name = f"{course.name} - {data.schedule.day} {fmt_12h(data.schedule.time_start)}"

        group = Group(
            name=auto_name,
            course_id=data.course_id,
            instructor_id=data.instructor_id,
            level_number=1,
            default_day=data.schedule.day,
            default_time_start=data.schedule.time_start,
            default_time_end=data.schedule.time_end,
            max_capacity=data.max_capacity,
            notes=data.notes,
        )
        from app.shared.audit_utils import apply_create_audit
        apply_create_audit(group)
        return self._repo.create_group(group)

    def update_group(self, group_id: int, data: UpdateGroupDTO) -> Group:
        group = self._repo.get_group_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(group, k) and k != "id":
                setattr(group, k, v)
        apply_update_audit(group)
        self._uow.session.add(group)
        self._uow.commit()
        self._uow.session.refresh(group)
        return group

    def get_group_by_id(self, group_id: int) -> Group | None:
        group = self._repo.get_group_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        return group

    def update_group_status(self, group_id: int, status: str) -> Group:
        group = self._repo.update_group_status(group_id, status)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        self._uow.commit()
        self._uow.session.refresh(group)
        return group

    def archive_group(self, group_id: int) -> Group:
        """
        Archive a group. The group has finished its lifecycle and is kept for
        historical reference. Enrollments remain — status becomes 'archived'.
        """
        from app.modules.academics.constants import GROUP_STATUS_COMPLETED
        group = self._repo.get_group_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        group.status = GROUP_STATUS_COMPLETED
        apply_update_audit(group)
        self._uow.session.add(group)
        self._uow.commit()
        self._uow.session.refresh(group)
        return group

    def deactivate_group(self, group_id: int) -> Group:
        """
        Deactivate a group. Different from archiving — the group is suspended
        (e.g. on hold, no new sessions). Status becomes 'inactive'.
        """
        from app.modules.academics.constants import GROUP_STATUS_INACTIVE
        group = self._repo.get_group_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found.")
        group.status = GROUP_STATUS_INACTIVE
        apply_update_audit(group)
        self._uow.session.add(group)
        self._uow.commit()
        self._uow.session.refresh(group)
        return group