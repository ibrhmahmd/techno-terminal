"""Enrollment money/lifecycle rules: transfer carry-over (#238), discount bounds (#256), drop/transfer guards (#247).

Runs on the rollback-only ``uow`` fixture: nothing is left behind.
"""

import pytest
from sqlalchemy import text

from app.modules.enrollments.schemas.enrollment_schemas import (
    EnrollStudentInput,
    TransferStudentInput,
    UpdateEnrollmentInput,
)
from app.modules.enrollments.services.enrollment_service import EnrollmentService
from app.modules.enrollments.tests.fakes import FakeEnrollmentNotifier
from app.shared.exceptions import BusinessRuleError, ConflictError
from app.testing.db_helpers import (
    create_test_course,
    create_test_enrollment,
    create_test_group,
    create_test_payment,
    create_test_receipt,
    create_test_student,
)


@pytest.fixture
def world(uow):
    s = uow.session
    course = create_test_course(s)
    g1 = create_test_group(s, course.id)
    g2 = create_test_group(s, course.id)
    student = create_test_student(s)
    notifier = FakeEnrollmentNotifier()
    svc = EnrollmentService(uow, notifier=notifier)
    return s, svc, notifier, student, g1, g2


def _pay(s, student_id, enrollment_id, amount):
    receipt = create_test_receipt(s)
    create_test_payment(s, receipt.id, student_id, amount, enrollment_id=enrollment_id)


def _unpaid_rows(s, student_id):
    return s.execute(
        text("SELECT 1 FROM v_unpaid_enrollments WHERE student_id = :sid"), {"sid": student_id}
    ).all()


# -- #238 transfer carries only the unpaid remainder --------------------------


def test_transfer_fully_paid_owes_nothing(world):
    s, svc, _, student, g1, g2 = world
    src = create_test_enrollment(s, student.id, g1.id, amount_due=1000.0)
    _pay(s, student.id, src.id, 1000.0)

    new = svc.transfer_student(TransferStudentInput(from_enrollment_id=src.id, to_group_id=g2.id))

    assert new.amount_due == 0
    assert new.discount_applied == 0
    assert new.amount_remaining == 0
    assert _unpaid_rows(s, student.id) == []


def test_transfer_partial_payment_carries_remainder(world):
    s, svc, _, student, g1, g2 = world
    src = create_test_enrollment(s, student.id, g1.id, amount_due=1000.0)
    _pay(s, student.id, src.id, 400.0)

    new = svc.transfer_student(TransferStudentInput(from_enrollment_id=src.id, to_group_id=g2.id))

    assert new.amount_due == 600.0
    assert new.discount_applied == 0


def test_transfer_with_discount_carries_net_remainder(world):
    s, svc, _, student, g1, g2 = world
    src = create_test_enrollment(s, student.id, g1.id, amount_due=1000.0, discount_applied=100.0)
    _pay(s, student.id, src.id, 300.0)

    new = svc.transfer_student(TransferStudentInput(from_enrollment_id=src.id, to_group_id=g2.id))

    assert new.amount_due == 600.0
    assert new.discount_applied == 0


# -- #247 transfer/drop guards -------------------------------------------------


def test_transfer_into_group_already_active_is_conflict(world):
    s, svc, _, student, g1, g2 = world
    src = create_test_enrollment(s, student.id, g1.id, amount_due=500.0)
    create_test_enrollment(s, student.id, g2.id, amount_due=500.0)

    with pytest.raises(ConflictError):
        svc.transfer_student(TransferStudentInput(from_enrollment_id=src.id, to_group_id=g2.id))


@pytest.mark.parametrize("status", ["completed", "transferred", "dropped"])
def test_drop_non_active_is_rejected_without_notification(world, status):
    s, svc, notifier, student, g1, _ = world
    enr = create_test_enrollment(s, student.id, g1.id, status=status)

    with pytest.raises(BusinessRuleError):
        svc.drop_enrollment(enr.id)

    assert notifier.calls == []
    assert enr.status == status


# -- #256 discount bounds ------------------------------------------------------


def test_enroll_discount_above_amount_due_rejected(world):
    _, svc, _, student, g1, _ = world
    with pytest.raises(BusinessRuleError):
        svc.enroll_student(
            EnrollStudentInput(student_id=student.id, group_id=g1.id, amount_due=1000.0, discount=1500.0)
        )


def test_update_discount_above_amount_due_rejected(world):
    s, svc, _, student, g1, _ = world
    enr = create_test_enrollment(s, student.id, g1.id, amount_due=1000.0, discount_applied=100.0)
    with pytest.raises(BusinessRuleError):
        svc.update_enrollment(enr.id, UpdateEnrollmentInput(discount_applied=1500.0))
    # Lowering the amount below the existing discount is the same violation.
    with pytest.raises(BusinessRuleError):
        svc.update_enrollment(enr.id, UpdateEnrollmentInput(amount_due=50.0))


def test_sibling_discount_above_amount_due_rejected(world):
    s, svc, _, student, g1, _ = world
    enr = create_test_enrollment(s, student.id, g1.id, amount_due=1000.0)
    with pytest.raises(BusinessRuleError):
        svc.apply_sibling_discount(enr.id, 1500.0)


def test_negative_discount_is_422_on_all_three_paths(client_with_uow, override_auth, mock_admin_headers, world):
    s, _, _, student, g1, _ = world
    enr = create_test_enrollment(s, student.id, g1.id, amount_due=1000.0)
    c, h = client_with_uow, mock_admin_headers

    assert c.post(
        "/api/v1/enrollments",
        headers=h,
        json={"student_id": student.id, "group_id": g1.id, "amount_due": 1000, "discount": -5},
    ).status_code == 422
    assert c.patch(f"/api/v1/enrollments/{enr.id}", headers=h, json={"discount_applied": -5}).status_code == 422
    assert c.post(f"/api/v1/enrollments/{enr.id}/discount?discount_amount=-5", headers=h).status_code == 422


def test_discount_above_amount_due_is_409_over_http(client_with_uow, override_auth, mock_admin_headers, world):
    s, _, _, student, g1, _ = world
    enr = create_test_enrollment(s, student.id, g1.id, amount_due=1000.0)
    r = client_with_uow.post(
        f"/api/v1/enrollments/{enr.id}/discount?discount_amount=1500", headers=mock_admin_headers
    )
    assert r.status_code == 409
