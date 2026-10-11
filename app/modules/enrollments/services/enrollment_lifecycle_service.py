from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any, List, Optional
from sqlmodel import select
from app.db.uow import UnitOfWork
from app.modules.academics.models import Course, Group
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.schemas.enrollment_lifecycle_schemas import (
    MigrateEnrollmentsDTO,
    EnrollmentMigrationResult,
    LevelProgressionResult,
)
from app.shared.exceptions import NotFoundError
from app.shared.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.modules.academics import ProgressLevelDTO


class EnrollmentLifecycleService:
    def __init__(self, uow: UnitOfWork, notification_svc: Optional[Any] = None):
        self._uow = uow
        self._notification_svc = notification_svc

    def progress_group_level(
        self,
        data: ProgressLevelDTO,
    ) -> LevelProgressionResult:
        """
        Progress a group to its next level, migrating enrolments in one transaction.

        Asks academics (via its facade) to create the next level and sessions,
        then migrates the active enrolments to that level. Both steps share one
        session and commit once, so a failure in either step rolls back both.
        """
        from app.modules.academics import GroupLifecycleService
        from app.modules.crm import StudentActivityService

        session = self._uow.session
        created = GroupLifecycleService(self._uow).create_next_level(data)

        enrollments_migrated = 0
        if data.auto_migrate_enrollments:
            migration_data = MigrateEnrollmentsDTO(
                group_id=created.group_id,
                from_level=created.old_level_number,
                to_level=created.new_level_number,
                price_override=data.price_override,
                preserve_discounts=True,
            )
            migration_result = self.migrate_enrollments_to_next_level(
                migration_data
            )
            enrollments_migrated = migration_result.count

            if migration_result.new_enrollment_ids:
                activity_svc = StudentActivityService(self._uow)
                stmt = select(Enrollment).where(
                    Enrollment.id.in_(migration_result.new_enrollment_ids)
                )
                for enrollment in session.exec(stmt).all():
                    activity_svc.log_activity(
                        student_id=enrollment.student_id,
                        activity_type="academic",
                        activity_subtype="level_started",
                        reference_type="enrollment",
                        reference_id=enrollment.id,
                        description=(
                            f"Progressed to Level {created.new_level_number} "
                            f"in Group {created.group_name}"
                        ),
                        metadata={
                            "notes": (
                                f"Automatic progression from Level "
                                f"{created.old_level_number} to {created.new_level_number}"
                            )
                        },
                        performed_by=None,
                    )

        self._uow.commit()

        action_desc = "progressed" if data.complete_current_level else "added"
        migration_desc = (
            f", {enrollments_migrated} enrollments migrated"
            if data.auto_migrate_enrollments
            else ", no enrollments migrated"
        )
        name_desc = ", name updated" if data.group_name else ""
        course_desc = f", course changed to {data.course_id}" if data.course_id else ""
        instructor_desc = ", instructor updated" if data.instructor_id else ""

        return LevelProgressionResult(
            old_level_number=created.old_level_number,
            new_level_number=created.new_level_number,
            new_level_id=created.new_level_id,
            sessions_created=created.sessions_created,
            enrollments_migrated=enrollments_migrated,
            message=f"Group {action_desc} from level {created.old_level_number} to {created.new_level_number}. "
                   f"{created.sessions_created} sessions created{migration_desc}{name_desc}{course_desc}{instructor_desc}.",
        )

    def migrate_enrollments_to_next_level(
        self,
        data: MigrateEnrollmentsDTO
    ) -> EnrollmentMigrationResult:
        session = self._uow.session
        group = session.get(Group, data.group_id)
        if not group:
            raise NotFoundError(f"Group {data.group_id} not found")

        course = session.get(Course, group.course_id)
        if not course:
            raise NotFoundError(f"Course {group.course_id} not found")

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
            enrollment.status = "completed"
            enrollment.updated_at = utc_now()
            session.add(enrollment)
            migrated_ids.append(enrollment.id)

            if data.price_override is not None:
                new_amount_due = float(data.price_override)
            else:
                new_amount_due = float(course.price_per_level) if course.price_per_level else 0.0

            total_amount_due += new_amount_due

            discount = enrollment.discount_applied if data.preserve_discounts else 0.0

            new_enrollment = Enrollment(
                student_id=enrollment.student_id,
                group_id=data.group_id,
                level_number=data.to_level,
                amount_due=new_amount_due,
                discount_applied=discount,
                status="active",
                enrolled_at=date.today(),
            )
            session.add(new_enrollment)
            session.flush()
            new_enrollment_ids.append(new_enrollment.id)

        return EnrollmentMigrationResult(
            count=len(active_enrollments),
            old_level=data.from_level,
            new_level=data.to_level,
            migrated_enrollment_ids=migrated_ids,
            new_enrollment_ids=new_enrollment_ids,
            total_amount_due=total_amount_due,
        )
