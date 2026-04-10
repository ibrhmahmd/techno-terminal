"""
app/modules/academics/services/group_lifecycle_service.py
─────────────────────────────────────────────────────────
Orchestration service for complex group workflows.
Coordinates GroupService, GroupLevelService, SessionService,
and EnrollmentMigrationService to perform atomic operations.
"""
from datetime import date
from typing import Optional

from app.db.connection import get_session
from app.modules.academics.models import Course, Group, CourseSession
from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.services.group_level_service import GroupLevelService
from app.modules.academics.services.session_service import SessionService
from app.modules.enrollments.services.enrollment_migration_service import (
    EnrollmentMigrationService,
)
from app.modules.academics.schemas.scheduling_dtos import (
    CreateGroupWithLevelDTO,
    CreateGroupDTO,
    CreateGroupLevelDTO,
    ProgressLevelDTO,
    MigrateEnrollmentsDTO,
    GroupCreationResult,
    LevelProgressionResult,
    GroupLevelResult,
)
from app.modules.academics.helpers.time_helpers import next_weekday
from app.shared.constants import DEFAULT_SESSIONS_PER_LEVEL


class GroupLifecycleService:
    """
    Orchestrates complex group workflows across multiple services.
    This is the high-level API that routers should call.
    """

    def __init__(
        self,
        group_level_service: Optional[GroupLevelService] = None,
        session_service: Optional[SessionService] = None,
        enrollment_migration_service: Optional[EnrollmentMigrationService] = None,
    ):
        self.level_svc = group_level_service or GroupLevelService()
        self.session_svc = session_service or SessionService()
        self.migration_svc = enrollment_migration_service or EnrollmentMigrationService()

    def create_group_with_first_level(
        self,
        data: CreateGroupWithLevelDTO
    ) -> GroupCreationResult:
        """
        Atomic operation to create a group with its first level and sessions.
        
        Process:
        1. Create group record
        2. Create Level 1 GroupLevel record
        3. Generate sessions for Level 1
        4. All in single transaction
        
        Args:
            data: Group creation parameters with level and session config
            
        Returns:
            GroupCreationResult with group, level, and session details
        """
        with get_session() as session:
            # Get course info
            course = session.get(Course, data.group_input.course_id)
            if not course:
                raise ValueError(f"Course {data.group_input.course_id} not found")
            
            sessions_per_level = data.sessions_per_level or course.sessions_per_level
            
            # Phase 1: Create group
            group = Group(
                name=self._generate_group_name(data.group_input, course.name),
                course_id=data.group_input.course_id,
                instructor_id=data.group_input.instructor_id,
                level_number=1,
                max_capacity=data.group_input.max_capacity,
                default_day=data.group_input.default_day,
                default_time_start=data.group_input.default_time_start,
                default_time_end=data.group_input.default_time_end,
                notes=data.group_input.notes,
                status="active",
            )
            session.add(group)
            session.flush()  # Get group.id without commit

            # Phase 2: Create Level 1
            level = GroupLevel(
                group_id=group.id,
                level_number=1,
                course_id=group.course_id,
                instructor_id=group.instructor_id,
                sessions_planned=sessions_per_level,
                price_override=None,  # Use course default
                status="active",
            )
            session.add(level)
            session.flush()  # Get level.id for session linking

            # Phase 3: Determine start date
            start_date = data.start_date
            if not start_date:
                start_date = (
                    next_weekday(date.today(), group.default_day)
                    if group.default_day else date.today()
                )

            # Phase 4: Generate sessions
            sessions = self._create_sessions_in_transaction(
                session=session,
                group_id=group.id,
                level_id=level.id,
                level_number=1,
                start_date=start_date,
                count=sessions_per_level,
                time_start=group.default_time_start,
                time_end=group.default_time_end,
                instructor_id=group.instructor_id,
            )

            session.commit()

            return GroupCreationResult(
                group_id=group.id,
                group_name=group.name,
                level_id=level.id,
                level_number=1,
                sessions_count=len(sessions),
                sessions=[self._serialize_session(s) for s in sessions],
            )

    def progress_to_next_level(
        self,
        data: ProgressLevelDTO
    ) -> LevelProgressionResult:
        """
        Atomic operation to progress a group to the next level.
        
        Process:
        1. Complete current level
        2. Create next level
        3. Generate sessions for next level
        4. Migrate enrollments (if enabled)
        5. Update group's level_number
        6. All in single transaction
        
        Args:
            data: Progression parameters including group_id and price override
            
        Returns:
            LevelProgressionResult with old/new level details and stats
        """
        from app.modules.academics import repositories as repo
        
        with get_session() as session:
            # Phase 1: Get current active level
            current_level = repo.get_current_group_level(session, data.group_id)
            if not current_level:
                raise ValueError(f"No active level found for group {data.group_id}")

            current_level_number = current_level.level_number
            new_level_number = current_level_number + 1

            # Phase 2: Check if next level already exists
            existing_next = repo.get_group_level_by_number(
                session, data.group_id, new_level_number
            )
            if existing_next:
                raise ValueError(
                    f"Level {new_level_number} already exists for group {data.group_id}"
                )

            # Phase 3: Complete current level
            repo.complete_group_level(session, data.group_id, current_level_number)

            # Phase 4: Get group and course for pricing
            group = session.get(Group, data.group_id)
            if not group:
                raise ValueError(f"Group {data.group_id} not found")
            
            course = session.get(Course, group.course_id)

            # Phase 5: Create new level
            new_level = GroupLevel(
                group_id=data.group_id,
                level_number=new_level_number,
                course_id=group.course_id,
                instructor_id=group.instructor_id,
                sessions_planned=DEFAULT_SESSIONS_PER_LEVEL,
                price_override=data.price_override,
                status="active",
            )
            session.add(new_level)
            session.flush()

            # Phase 6: Generate sessions for new level
            start_date = (
                next_weekday(date.today(), group.default_day)
                if group.default_day else date.today()
            )
            sessions = self._create_sessions_in_transaction(
                session=session,
                group_id=group.id,
                level_id=new_level.id,
                level_number=new_level_number,
                start_date=start_date,
                count=DEFAULT_SESSIONS_PER_LEVEL,
                time_start=group.default_time_start,
                time_end=group.default_time_end,
                instructor_id=group.instructor_id,
            )

            # Phase 7: Migrate enrollments (if enabled)
            enrollments_migrated = 0
            if data.auto_migrate_enrollments:
                migration_data = MigrateEnrollmentsDTO(
                    group_id=data.group_id,
                    from_level=current_level_number,
                    to_level=new_level_number,
                    price_override=data.price_override,
                    preserve_discounts=True,
                )
                migration_result = self.migration_svc.migrate_enrollments_to_next_level(
                    session, migration_data
                )
                enrollments_migrated = migration_result.count

            # Phase 8: Update group's level_number
            group.level_number = new_level_number
            session.add(group)

            session.commit()

            return LevelProgressionResult(
                old_level_number=current_level_number,
                new_level_number=new_level_number,
                new_level_id=new_level.id,
                sessions_created=len(sessions),
                enrollments_migrated=enrollments_migrated,
                message=f"Group progressed from level {current_level_number} to {new_level_number}. "
                       f"{len(sessions)} sessions created, {enrollments_migrated} enrollments migrated.",
            )

    def add_level_to_existing_group(
        self,
        data: CreateGroupLevelDTO
    ) -> GroupLevelResult:
        """
        Add a new level to an existing group with sessions.
        
        Args:
            data: Level creation parameters
            
        Returns:
            GroupLevelResult with level details and session count
        """
        from app.modules.academics import repositories as repo
        from app.shared.exceptions import BusinessRuleError
        
        with get_session() as session:
            # Validate group exists and is active
            group = session.get(Group, data.group_id)
            if not group:
                raise ValueError(f"Group {data.group_id} not found")
            if group.status != "active":
                raise BusinessRuleError(f"Group {data.group_id} is not active")

            # Check level doesn't exist
            existing = repo.get_group_level_by_number(
                session, data.group_id, data.level_number
            )
            if existing:
                raise ValueError(
                    f"Level {data.level_number} already exists for group {data.group_id}"
                )

            # Determine course and pricing
            course = session.get(Course, data.course_id or group.course_id)
            price_override = data.price_override
            if price_override is None or price_override == 0:
                price_override = None

            # Create level
            level = GroupLevel(
                group_id=data.group_id,
                level_number=data.level_number,
                course_id=data.course_id or group.course_id,
                instructor_id=data.instructor_id or group.instructor_id,
                sessions_planned=data.sessions_planned,
                price_override=price_override,
                status=data.status,
            )
            session.add(level)
            session.flush()

            # Generate sessions
            start_date = data.start_date
            if not start_date:
                start_date = (
                    next_weekday(date.today(), group.default_day)
                    if group.default_day else date.today()
                )

            sessions = self._create_sessions_in_transaction(
                session=session,
                group_id=group.id,
                level_id=level.id,
                level_number=data.level_number,
                start_date=start_date,
                count=data.sessions_planned,
                time_start=group.default_time_start,
                time_end=group.default_time_end,
                instructor_id=data.instructor_id or group.instructor_id,
            )

            # Update group's level_number to match the new level
            group.level_number = data.level_number
            session.add(group)

            session.commit()

            return GroupLevelResult(
                level_id=level.id,
                group_id=group.id,
                level_number=level.level_number,
                sessions_count=len(sessions),
                status=level.status,
            )

    def _generate_group_name(self, data: CreateGroupDTO, course_name: str) -> str:
        """Generate auto-name for a group."""
        from app.modules.academics.helpers.time_helpers import fmt_12h
        return f"{course_name} - {data.default_day} {fmt_12h(data.default_time_start)}"

    def _create_sessions_in_transaction(
        self,
        session,
        group_id: int,
        level_id: int,
        level_number: int,
        start_date: date,
        count: int,
        time_start,
        time_end,
        instructor_id: int,
    ) -> list[CourseSession]:
        """
        Create sessions within an existing transaction.
        Uses the session_service for the actual creation.
        """
        # Use the helper directly since we're already in a transaction
        from app.modules.academics.helpers.session_planning import create_sessions_in_session
        from app.shared.datetime_utils import utc_now
        from datetime import timedelta
        
        created: list[CourseSession] = []
        d = start_date
        for i in range(count):
            cs = CourseSession(
                group_id=group_id,
                group_level_id=level_id,
                level_number=level_number,
                session_number=i + 1,
                session_date=d,
                start_time=time_start,
                end_time=time_end,
                actual_instructor_id=instructor_id,
                is_extra_session=False,
                created_at=utc_now(),
            )
            session.add(cs)
            session.flush()
            created.append(cs)
            d += timedelta(weeks=1)
        
        return created

    def _serialize_session(self, session: CourseSession) -> dict:
        """Serialize a session for the result DTO."""
        return {
            "id": session.id,
            "session_number": session.session_number,
            "session_date": session.session_date.isoformat() if session.session_date else None,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "status": session.status,
        }
