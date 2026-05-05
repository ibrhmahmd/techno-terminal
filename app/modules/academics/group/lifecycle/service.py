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
from app.modules.academics.models.group_level_models import GroupLevel, GroupCourseHistory
from app.modules.academics.group.level.service import GroupLevelService
from app.modules.academics.session.service import SessionService
from app.modules.enrollments.services.enrollment_migration_service import (
    EnrollmentMigrationService,
)
from app.modules.hr.models import Employee
import app.modules.academics.group.level.repository as repo
from app.shared.exceptions import BusinessRuleError
from app.modules.academics.group.lifecycle.schemas import (
    CreateGroupWithLevelDTO,
    CreateGroupLevelDTO,
    ProgressLevelDTO,
    MigrateEnrollmentsDTO,
    
    GroupCreationResult,
    LevelProgressionResult,
    GroupLevelResult,
    SessionSummaryDTO,
)
from app.modules.academics.group.core.schemas import ScheduleGroupInput as CreateGroupDTO
from app.modules.academics.helpers.time_helpers import next_weekday
from app.modules.academics.constants import GROUP_STATUS_ACTIVE
from app.modules.academics.constants import DEFAULT_SESSIONS_PER_LEVEL
from app.shared.datetime_utils import utc_now


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
            
            sessions_per_level = course.sessions_per_level
            
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
            from app.shared.audit_utils import apply_create_audit
            apply_create_audit(group)
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
            apply_create_audit(level)
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
            from app.modules.academics.helpers.session_planning import create_sessions_in_session
            
            sessions = create_sessions_in_session(
                session=session,
                group=group,
                sessions_count=sessions_per_level,
                start_date=start_date,
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
        with get_session() as session:
            # Phase 1: Get current active level
            current_level = repo.get_current_group_level(session, data.group_id)
            if not current_level:
                raise ValueError(f"No active level found for group {data.group_id}")

            current_level_number = current_level.level_number
            # Use target_level if provided, otherwise default to next sequential level
            new_level_number = data.target_level or (current_level_number + 1)

            # Validate: target level must be greater than current level
            if new_level_number <= current_level_number:
                raise ValueError(
                    f"Target level {new_level_number} must be greater than current level {current_level_number}"
                )

            # Phase 2: Check if target level already exists
            existing_next = repo.get_group_level_by_number(
                session, data.group_id, new_level_number
            )
            if existing_next:
                raise ValueError(
                    f"Level {new_level_number} already exists for group {data.group_id}"
                )

            # Phase 3: Complete current level (if enabled)
            if data.complete_current_level:
                repo.complete_group_level(session, data.group_id, current_level_number)

            # Phase 4: Get group and handle course override
            group = session.get(Group, data.group_id)
            if not group:
                raise ValueError(f"Group {data.group_id} not found")

            old_course_id = group.course_id
            new_course_id = data.course_id or group.course_id

            # Validate course override if provided
            if data.course_id:
                new_course = session.get(Course, data.course_id)
                if not new_course:
                    raise ValueError(f"Course {data.course_id} not found")
                # Update group's course_id
                group.course_id = data.course_id
                # Log course change in history
                history_record = GroupCourseHistory(
                    group_id=data.group_id,
                    course_id=old_course_id,
                    notes=f"Course changed from {old_course_id} to {data.course_id} during level progression",
                    assigned_at=utc_now(),
                )
                session.add(history_record)

            # Handle instructor override
            if data.instructor_id:
                # Validate instructor exists (employees table)
                instructor = session.get(Employee, data.instructor_id)
                if not instructor:
                    raise ValueError(f"Instructor {data.instructor_id} not found")
                # Update group's instructor_id
                group.instructor_id = data.instructor_id

            # Get course for pricing (may be new course if overridden)
            course = session.get(Course, new_course_id)
            if not course:
                raise ValueError(f"Course {new_course_id} not found")

            # Phase 5: Create new level
            new_level = GroupLevel(
                group_id=data.group_id,
                level_number=new_level_number,
                course_id=group.course_id,
                instructor_id=group.instructor_id,
                sessions_planned=course.sessions_per_level,
                price_override=data.price_override,
                status="active",
            )
            apply_create_audit(new_level)
            session.add(new_level)
            session.flush()

            # Phase 6: Generate sessions for new level
            from app.modules.academics.helpers.session_planning import create_sessions_in_session
            
            sessions = create_sessions_in_session(
                session=session,
                group=group,
                sessions_count=course.sessions_per_level,
                start_date=data.session_start_date or (
                    next_weekday(date.today(), group.default_day) if group.default_day else date.today()
                ),
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
                
                # Trigger level progression notification via activity logging
                from app.modules.enrollments.models.enrollment_models import Enrollment
                from app.modules.crm.repositories.activity_repository import ActivityRepository
                from sqlmodel import select
                
                if migration_result.new_enrollment_ids:
                    activity_repo = ActivityRepository(session)
                    stmt_enr = select(Enrollment).where(Enrollment.id.in_(migration_result.new_enrollment_ids))
                    new_enrollments = session.exec(stmt_enr).all()
                    
                    for enrollment in new_enrollments:
                        activity_repo.create_activity_log(
                            student_id=enrollment.student_id,
                            activity_type="academic",
                            activity_subtype="level_started",
                            reference_type="enrollment",
                            reference_id=enrollment.id,
                            description=f"Progressed to Level {new_level_number} in Group {group.name}",
                            metadata={"notes": f"Automatic progression from Level {current_level_number} to {new_level_number}"},
                            performed_by=None
                        )

            # Phase 8: Update group's level_number and optional name
            group.level_number = new_level_number
            if data.group_name:
                group.name = data.group_name.strip()
            from app.shared.audit_utils import apply_update_audit
            apply_update_audit(group)
            session.add(group)

            session.commit()

            # Build appropriate message based on what was done
            action_desc = "progressed" if data.complete_current_level else "added"
            migration_desc = f", {enrollments_migrated} enrollments migrated" if data.auto_migrate_enrollments else ", no enrollments migrated"
            name_desc = ", name updated" if data.group_name else ""
            course_desc = f", course changed to {new_course_id}" if data.course_id else ""
            instructor_desc = ", instructor updated" if data.instructor_id else ""

            return LevelProgressionResult(
                old_level_number=current_level_number,
                new_level_number=new_level_number,
                new_level_id=new_level.id,
                sessions_created=len(sessions),
                enrollments_migrated=enrollments_migrated,
                message=f"Group {action_desc} from level {current_level_number} to {new_level_number}. "
                       f"{len(sessions)} sessions created{migration_desc}{name_desc}{course_desc}{instructor_desc}.",
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
        with get_session() as session:
            # Validate group exists and is active
            group = session.get(Group, data.group_id)
            if not group:
                raise ValueError(f"Group {data.group_id} not found")
            if group.status != GROUP_STATUS_ACTIVE:
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
            from app.shared.audit_utils import apply_create_audit
            apply_create_audit(level)
            session.add(level)
            session.flush()

            # Generate sessions
            from app.modules.academics.helpers.session_planning import create_sessions_in_session
            
            sessions = create_sessions_in_session(
                session=session,
                group=group,
                sessions_count=data.sessions_planned,
                start_date=data.start_date or (
                    next_weekday(date.today(), group.default_day) if group.default_day else date.today()
                ),
            )

            # Update group's level_number to match the new level
            group.level_number = data.level_number
            from app.shared.audit_utils import apply_update_audit
            apply_update_audit(group)
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


    def _serialize_session(self, session: CourseSession) -> SessionSummaryDTO:
        """Serialize a session for the result DTO."""
        return SessionSummaryDTO(
            id=session.id,
            session_number=session.session_number,
            session_date=session.session_date.isoformat() if session.session_date else None,
            start_time=session.start_time.isoformat() if session.start_time else None,
            end_time=session.end_time.isoformat() if session.end_time else None,
            status=session.status,
        )
