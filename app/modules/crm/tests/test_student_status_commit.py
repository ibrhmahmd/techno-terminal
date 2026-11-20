"""#237: status changes are committed."""
import uuid

from app.modules.crm.models.student_models import Student
from app.modules.crm.services.student_crud_service import StudentCrudService
from app.modules.crm.models import StudentStatus


def _student(uow) -> Student:
    s = Student(full_name=f"St {uuid.uuid4().hex[:8]}", phone=f"010{uuid.uuid4().int % 10**8:08d}", status="active")
    uow.session.add(s)
    uow.commit()
    return s


def test_update_status_is_committed(uow):
    student = _student(uow)

    StudentCrudService(uow).update_status(student.id, StudentStatus.INACTIVE)

    uow.rollback()  # without commit() the change is lost here
    assert uow.session.get(Student, student.id).status == StudentStatus.INACTIVE


def test_status_endpoint_commits(client_with_uow, mock_admin_headers, override_auth, uow):
    student = _student(uow)

    resp = client_with_uow.patch(f"/api/v1/crm/students/{student.id}/status",
                                 headers=mock_admin_headers, json={"status": "inactive"})

    assert resp.status_code == 200
    uow.rollback()  # what get_uow does to uncommitted work
    assert uow.session.get(Student, student.id).status == StudentStatus.INACTIVE


