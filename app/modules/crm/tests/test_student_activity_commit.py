"""Activity rows are committed together with the change they describe (#59).

soft_delete_student, restore_student and toggle_status used to commit first and
log afterwards; the request's UnitOfWork then rolled the activity row back, so
these actions never appeared in a student's history. Rolling back after the call
leaves only what was committed.
"""
import uuid

from sqlmodel import select

from app.modules.crm.models.activity_models import StudentActivityLog
from app.modules.crm.models.student_models import Student
from app.modules.crm.services.activity_service import StudentActivityService
from app.modules.crm.services.student_crud_service import StudentCrudService


def _student(uow) -> Student:
    s = Student(full_name=f"Act {uuid.uuid4().hex[:8]}", phone=f"010{uuid.uuid4().int % 10**8:08d}", status="active")
    uow.session.add(s)
    uow.commit()
    return s


def _committed_types(uow, student_id: int) -> list[str]:
    uow.rollback()  # discard anything flushed but not committed
    rows = uow.session.exec(select(StudentActivityLog).where(StudentActivityLog.student_id == student_id)).all()
    return sorted(r.activity_type for r in rows)


def _svc(uow) -> StudentCrudService:
    return StudentCrudService(uow, activity_svc=StudentActivityService(uow))


def test_soft_delete_and_restore_activities_are_committed(uow):
    student = _student(uow)
    svc = _svc(uow)

    assert svc.soft_delete_student(student.id, deleted_by=None) is True
    assert _committed_types(uow, student.id) == ["deletion"]

    assert svc.restore_student(student.id) is True
    assert _committed_types(uow, student.id) == ["deletion", "registration"]


def test_toggle_status_activity_is_committed(uow):
    student = _student(uow)

    _svc(uow).toggle_status(student.id)

    assert _committed_types(uow, student.id) == ["status_change"]
