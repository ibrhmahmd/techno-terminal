"""#277: the discount carried to the next level is capped at the new amount due."""
from decimal import Decimal

from app.modules.enrollments.models.enrollment_models import Enrollment
from app.modules.enrollments.schemas.enrollment_lifecycle_schemas import MigrateEnrollmentsDTO
from app.modules.enrollments.services.enrollment_lifecycle_service import EnrollmentLifecycleService
from app.testing.db_helpers import (
    create_test_course,
    create_test_enrollment,
    create_test_group,
    create_test_student,
)


def _migrate(uow, price_override, old_discount, **kw):
    session = uow.session
    course = create_test_course(session)
    group = create_test_group(session, course.id)
    student = create_test_student(session)
    create_test_enrollment(
        session, student.id, group.id, amount_due=1000.0, discount_applied=old_discount
    )
    result = EnrollmentLifecycleService(uow).migrate_enrollments_to_next_level(
        MigrateEnrollmentsDTO(
            group_id=group.id, from_level=1, to_level=2, price_override=price_override, **kw
        )
    )
    return session.get(Enrollment, result.new_enrollment_ids[0])


def test_carried_discount_is_capped_at_new_amount_due(uow):
    new = _migrate(uow, Decimal("200"), 300.0)
    assert new.amount_due == 200.0
    assert new.discount_applied == 200.0


def test_discount_below_new_amount_due_is_carried_unchanged(uow):
    assert _migrate(uow, Decimal("500"), 300.0).discount_applied == 300.0


def test_discount_dropped_when_not_preserved(uow):
    assert _migrate(uow, Decimal("500"), 300.0, preserve_discounts=False).discount_applied == 0.0
