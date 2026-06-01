from datetime import datetime
from typing import Any, List, Optional
from sqlmodel import Session, select
from app.modules.academics.models import Course, Group
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.lifecycle.schemas import (
    MigrateEnrollmentsDTO,
    EnrollmentMigrationResult,
)
from app.shared.exceptions import NotFoundError


class EnrollmentLifecycleService:
    def __init__(self, notification_svc: Optional[Any] = None):
        self._notification_svc = notification_svc

    def migrate_enrollments_to_next_level(
        self,
        session: Session,
        data: MigrateEnrollmentsDTO
    ) -> EnrollmentMigrationResult:
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
            enrollment.updated_at = datetime.utcnow()
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
                enrolled_at=datetime.utcnow(),
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
