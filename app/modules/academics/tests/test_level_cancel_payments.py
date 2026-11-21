"""#280: a level with live payments cannot be cancelled; a soft-deleted payment does not block it."""
import pytest

from app.modules.academics.models.group_level_models import GroupLevel
from app.modules.academics.models.group_models import Group
from app.modules.academics.services.group_level_service import GroupLevelService
from app.modules.enrollments.models.enrollment_models import Enrollment
from app.shared.datetime_utils import utc_now
from app.shared.exceptions import BusinessRuleError
from app.testing.db_helpers import (
    create_test_course,
    create_test_enrollment,
    create_test_group,
    create_test_group_level,
    create_test_payment,
    create_test_receipt,
    create_test_student,
)


def _two_level_group(session):
    course = create_test_course(session)
    group = create_test_group(session, course.id, level_number=2)
    prev = create_test_group_level(session, group.id, 1, course.id, status="completed")
    cur = create_test_group_level(session, group.id, 2, course.id)
    student = create_test_student(session)
    enr = create_test_enrollment(session, student.id, group.id, level_number=2, amount_due=500.0)
    return group, prev, cur, student, enr


def test_cancel_refused_when_level_has_a_live_payment(uow):
    session = uow.session
    group, prev, cur, student, enr = _two_level_group(session)
    receipt = create_test_receipt(session)
    create_test_payment(session, receipt.id, student.id, 100.0, enrollment_id=enr.id)

    with pytest.raises(BusinessRuleError, match="Refund"):
        GroupLevelService(uow).cancel_level(group.id, 2, reason="x")

    session.expire_all()
    assert session.get(GroupLevel, cur.id).status == "active"
    assert session.get(GroupLevel, prev.id).status == "completed"
    assert session.get(Group, group.id).level_number == 2
    assert session.get(Enrollment, enr.id).status == "active"


def test_cancel_allowed_when_only_payment_is_soft_deleted(uow):
    session = uow.session
    group, _prev, cur, student, enr = _two_level_group(session)
    receipt = create_test_receipt(session)
    payment = create_test_payment(session, receipt.id, student.id, 100.0, enrollment_id=enr.id)
    payment.deleted_at = utc_now()
    session.add(payment)
    session.commit()

    GroupLevelService(uow).cancel_level(group.id, 2)

    session.expire_all()
    assert session.get(GroupLevel, cur.id).status == "cancelled"
