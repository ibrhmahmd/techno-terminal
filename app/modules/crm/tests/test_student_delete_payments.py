"""#243/#175: deleting a student keeps their payments; restore revives only legacy-cascaded ones."""
import uuid
from datetime import timedelta

from app.modules.crm.models.student_models import Student
from app.modules.crm.services.student_crud_service import StudentCrudService
from app.modules.enrollments.services.student_deletion_service import StudentDeletionService
from app.modules.finance.models import Payment, Receipt
from app.shared.datetime_utils import utc_now


def _student(uow) -> Student:
    s = Student(full_name=f"St {uuid.uuid4().hex[:8]}", phone=f"010{uuid.uuid4().int % 10**8:08d}", status="active")
    uow.session.add(s)
    uow.commit()
    return s


def _payment(uow, student_id, **kw) -> Payment:
    receipt = Receipt(payer_name="P", payment_method="cash", paid_at=utc_now(), created_at=utc_now())
    uow.session.add(receipt)
    uow.session.flush()
    p = Payment(receipt_id=receipt.id, student_id=student_id, amount=100.0,
                transaction_type="payment", payment_type="course_level", created_at=utc_now(), **kw)
    uow.session.add(p)
    uow.commit()
    return p


def _payment_deleted_at(uow, pid):
    uow.rollback()  # drops anything uncommitted; the savepoint keeps only what was committed
    p = uow.session.get(Payment, pid)
    uow.session.refresh(p)
    return p.deleted_at


def test_delete_keeps_payment_live(uow):
    student = _student(uow)
    pay = _payment(uow, student.id)

    assert StudentDeletionService(uow).delete_student(student.id, deleted_by=None) is True

    assert _payment_deleted_at(uow, pay.id) is None


def test_earlier_void_stays_voided_after_delete_and_restore(uow):
    student = _student(uow)
    voided_at = utc_now() - timedelta(days=3)
    pay = _payment(uow, student.id, deleted_at=voided_at)
    svc = StudentCrudService(uow)

    StudentDeletionService(uow).delete_student(student.id, deleted_by=None)
    svc.restore_student(student.id)

    assert _payment_deleted_at(uow, pay.id) == voided_at


def test_restore_revives_legacy_cascaded_payment(uow):
    student = _student(uow)
    pay = _payment(uow, student.id)
    stamp = utc_now()
    old_void = _payment(uow, student.id, deleted_at=stamp - timedelta(days=2))
    # Legacy state: the old cascade stamped the student and payment together.
    student.deleted_at = stamp
    pay.deleted_at = stamp + timedelta(milliseconds=5)
    uow.session.add_all([student, pay])
    uow.commit()

    assert StudentCrudService(uow).restore_student(student.id) is True

    assert _payment_deleted_at(uow, pay.id) is None
    assert _payment_deleted_at(uow, old_void.id) is not None
