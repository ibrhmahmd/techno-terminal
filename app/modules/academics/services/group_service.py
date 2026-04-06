"""
app/modules/academics/services/group_service.py
────────────────────────────────────────────────
Service class for Group-related business logic.
"""
from datetime import date
from decimal import Decimal
from app.db.connection import get_session
from app.shared.audit_utils import apply_update_audit
from app.shared.exceptions import NotFoundError, BusinessRuleError
from app.modules.academics.models import Course, Group
from app.modules.academics.models import CourseSession
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.schemas import (
    ScheduleGroupInput, UpdateGroupDTO, EnrichedGroupDTO,
    ScheduleGroupLevelInput, ProgressGroupLevelInput, ProgressGroupLevelResult,
)
from app.modules.academics.helpers.time_helpers import fmt_12h, next_weekday, validate_times
from app.modules.academics.helpers.session_planning import create_sessions_in_session
from app.modules.academics import repositories as repo
from app.shared.constants import DEFAULT_SESSIONS_PER_LEVEL


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

    def schedule_group_level(
        self, data: ScheduleGroupLevelInput
    ) -> tuple[GroupLevel, list[CourseSession]]:
        """
        Schedule a new level for an existing group.
        Creates GroupLevel record and generates sessions.
        ATOMIC — all operations in one transaction.
        """
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from sqlmodel import select

        with get_session() as session:
            # 1. Validate group exists and is active
            group = session.get(Group, data.group_id)
            if not group:
                raise NotFoundError(f"Group {data.group_id} not found.")
            if group.status != "active":
                raise BusinessRuleError(f"Group {data.group_id} is not active (status: {group.status})")

            # 2. Check if level already exists
            existing_level = repo.get_group_level_by_number(
                session, data.group_id, data.level_number
            )
            if existing_level:
                raise BusinessRuleError(
                    f"Level {data.level_number} already exists for group {data.group_id}"
                )

            # 3. Get course for pricing
            course = session.get(Course, group.course_id)
            if not course:
                raise NotFoundError(f"Course {group.course_id} for group not found.")

            # 4. Determine price (use course default if override is None or 0)
            price_override = data.price_override
            if price_override is None or price_override == 0:
                price_override = None  # Will use course default

            # 5. Determine instructor (use override or group's default)
            instructor_id = data.instructor_id or group.instructor_id

            # 6. Create GroupLevel record
            level = GroupLevel(
                group_id=data.group_id,
                level_number=data.level_number,
                course_id=group.course_id,
                instructor_id=instructor_id,
                sessions_planned=DEFAULT_SESSIONS_PER_LEVEL,
                price_override=price_override,
                status="active",
            )
            session.add(level)
            session.flush()

            # 7. Determine start date
            start_date = data.start_date
            if not start_date:
                start_date = (
                    next_weekday(date.today(), group.default_day)
                    if group.default_day else date.today()
                )

            # 8. Create sessions for this level
            sessions = create_sessions_in_session(
                session,
                group.id,
                data.level_number,
                start_date,
                DEFAULT_SESSIONS_PER_LEVEL,
                group.default_time_start,
                group.default_time_end,
                instructor_id,
            )

            # 9. Update group's level_number to match the new level
            group.level_number = data.level_number
            session.add(group)

            session.commit()
            return level, sessions

    def progress_group_level(
        self, data: ProgressGroupLevelInput
    ) -> ProgressGroupLevelResult:
        """
        Progress a group from current level to next level.
        Creates new GroupLevel, generates sessions, migrates enrollments.
        ATOMIC — all operations in one transaction.
        """
        from app.modules.enrollments.models.enrollment_models import Enrollment
        from sqlmodel import select
        from datetime import datetime

        with get_session() as session:
            # 1. Validate group exists
            group = session.get(Group, data.group_id)
            if not group:
                raise NotFoundError(f"Group {data.group_id} not found.")

            # 2. Get current active level
            current_level = repo.get_current_group_level(session, data.group_id)
            if not current_level:
                raise BusinessRuleError(f"No active level found for group {data.group_id}")

            current_level_number = current_level.level_number
            new_level_number = current_level_number + 1

            # 3. Check if next level already exists
            existing_next = repo.get_group_level_by_number(
                session, data.group_id, new_level_number
            )
            if existing_next:
                raise BusinessRuleError(
                    f"Level {new_level_number} already exists for group {data.group_id}"
                )

            # 4. Complete the current level
            repo.complete_group_level(session, data.group_id, current_level_number)

            # 5. Get course for pricing
            course = session.get(Course, group.course_id)
            if not course:
                raise NotFoundError(f"Course {group.course_id} for group not found.")

            # 6. Determine price for new level
            price_override = data.price_override
            if price_override is None or price_override == 0:
                price_override = None

            # 7. Create new GroupLevel
            new_level = GroupLevel(
                group_id=data.group_id,
                level_number=new_level_number,
                course_id=group.course_id,
                instructor_id=group.instructor_id,
                sessions_planned=DEFAULT_SESSIONS_PER_LEVEL,
                price_override=price_override,
                status="active",
            )
            session.add(new_level)
            session.flush()

            # 8. Create sessions for new level
            start_date = (
                next_weekday(date.today(), group.default_day)
                if group.default_day else date.today()
            )
            sessions = create_sessions_in_session(
                session,
                group.id,
                new_level_number,
                start_date,
                DEFAULT_SESSIONS_PER_LEVEL,
                group.default_time_start,
                group.default_time_end,
                group.instructor_id,
            )

            # 9. Migrate enrollments from old level to new level
            # Get active enrollments for current level
            stmt = select(Enrollment).where(
                Enrollment.group_id == data.group_id,
                Enrollment.level_number == current_level_number,
                Enrollment.status == "active"
            )
            active_enrollments = list(session.exec(stmt).all())

            enrollments_migrated = 0
            for enrollment in active_enrollments:
                # Mark old enrollment as completed
                enrollment.status = "completed"
                enrollment.completed_at = datetime.utcnow()
                session.add(enrollment)

                # Create new enrollment for next level
                new_amount_due = float(price_override) if price_override else float(course.price_per_level)
                
                new_enrollment = Enrollment(
                    student_id=enrollment.student_id,
                    group_id=data.group_id,
                    level_number=new_level_number,
                    amount_due=new_amount_due,
                    discount_applied=enrollment.discount_applied,  # Carry over discount
                    status="active",
                )
                session.add(new_enrollment)
                enrollments_migrated += 1

            # 10. Update group's level_number
            group.level_number = new_level_number
            session.add(group)

            session.commit()

            return ProgressGroupLevelResult(
                old_level_number=current_level_number,
                new_level_number=new_level_number,
                enrollments_migrated=enrollments_migrated,
                sessions_created=len(sessions),
                message=f"Group progressed from level {current_level_number} to {new_level_number}. "
                       f"{enrollments_migrated} enrollments migrated, {len(sessions)} sessions created."
            )

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

    def get_enriched_group_by_id(self, group_id: int) -> EnrichedGroupDTO | None:
        with get_session() as session:
            return repo.get_enriched_group_by_id(session, group_id)
            
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

    def delete_group_by_id(self, group_id: int) -> Group:
        """Delete a group by ID."""
        with get_session() as session:
            group = repo.delete_group_by_id(session, group_id)
            if not group:
                raise NotFoundError(f"Group {group_id} not found.")
                
            return group