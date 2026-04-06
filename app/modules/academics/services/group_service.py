"""
app/modules/academics/services/group_service.py
────────────────────────────────────────────────
Service class for Group-related business logic.
"""
from datetime import date
from app.db.connection import get_session
from app.shared.audit_utils import apply_update_audit
from app.shared.exceptions import NotFoundError
from app.modules.academics.models import Course, Group
from app.modules.academics.models import CourseSession
from app.modules.academics.schemas import ScheduleGroupInput, UpdateGroupDTO, EnrichedGroupDTO
from app.modules.academics.helpers.time_helpers import fmt_12h, next_weekday, validate_times
from app.modules.academics.helpers.session_planning import create_sessions_in_session
from app.modules.academics import repositories as repo


class GroupService:
    def schedule_group(self, data: ScheduleGroupInput) -> tuple[Group, list[CourseSession]]:
        """
        Creates a group, auto-generates its name, validates time window (11AM-9PM),
        and immediately generates the first level sessions starting from today.
        Returns (group, sessions).
        ATOMIC — group + sessions commit together or not at all.
        """
        validate_times(data.default_time_start, data.default_time_end)

        with get_session() as session:                          # ← ONE session
            course = session.get(Course, data.course_id)
            if not course:
                raise NotFoundError(f"Course with ID {data.course_id} not found.")

            auto_name = (
                f"{data.default_day} "
                f"{fmt_12h(data.default_time_start)} - {course.name}"
            )
            group = Group(
                name=auto_name,
                course_id=data.course_id,
                instructor_id=data.instructor_id,
                level_number=1,
                max_capacity=data.max_capacity,
                default_day=data.default_day,
                default_time_start=data.default_time_start,
                default_time_end=data.default_time_end,
            )
            session.add(group)
            session.flush()                                     # get group.id without commit

            start_date = (
                next_weekday(date.today(), data.default_day)
                if data.default_day else date.today()
            )
            sessions = create_sessions_in_session(            # ← SAME session
                session, group.id, 1, start_date,
                course.sessions_per_level,
                data.default_time_start, data.default_time_end,
                group.instructor_id,
            )
            return group, sessions
        # ← SINGLE COMMIT — group + sessions or nothing

    def get_groups_by_course(self, course_id: int) -> list[Group]:
        with get_session() as session:
            return list(repo.list_groups_by_course(session, course_id))

    def get_all_active_groups(self, include_inactive: bool = False) -> list[Group]:
        with get_session() as session:
            return list(repo.list_all_active_groups(session, include_inactive))

    def get_all_active_groups_enriched(self) -> list[EnrichedGroupDTO]:
        """Returns groups with instructor_name and course_name joined for display."""
        with get_session() as session:
            return repo.get_enriched_groups(session)

    def get_todays_groups_enriched(self) -> list[EnrichedGroupDTO]:
        """Returns active groups that have at least one session scheduled for today."""
        with get_session() as session:
            return repo.get_enriched_groups_by_date(session, date.today().isoformat())

    def get_group_by_id(self, group_id: int) -> Group | None:
        with get_session() as session:
            return repo.get_group_by_id(session, group_id)

    def get_enriched_group_by_id(self , group: Group) -> EnrichedGroupDTO:
        with get_session() as session:
            return repo.get_enriched_group_by_id(session, group.id)
            
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

    def search_groups(
        self,
        query: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Group], int]:
        """Search groups by name with optional status filter."""
        with get_session() as session:
            results, total = repo.search_groups(session, query, status, skip, limit)
            return list(results), total

    def get_groups_by_type(
        self,
        group_type: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Group], int]:
        """Get groups filtered by type."""
        with get_session() as session:
            results, total = repo.get_groups_by_type(session, group_type, status, skip, limit)
            return list(results), total

    def get_groups_by_course(
        self,
        course_id: int,
        include_inactive: bool = False,
        level_number: int | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[Group], int]:
        """Get all groups for a specific course."""
        with get_session() as session:
            results, total = repo.get_groups_by_course(
                session, course_id, include_inactive, level_number, skip, limit
            )
            return list(results), total
