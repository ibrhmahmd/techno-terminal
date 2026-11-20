"""Hard deletes of E2E test data in crm's own tables (#218). Staging only."""
from sqlalchemy import delete, or_, select
from sqlmodel import Session

from app.modules.crm.models import Parent, Student, StudentParent
from app.modules.crm.models.activity_models import StudentActivityLog


class CrmE2EPurgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_student_ids(self, prefix: str) -> list[int]:
        stmt = select(Student.id).where(Student.full_name.startswith(prefix, autoescape=True))
        return list(self._session.execute(stmt).scalars())

    def find_parent_ids(self, prefix: str) -> list[int]:
        stmt = select(Parent.id).where(Parent.full_name.startswith(prefix, autoescape=True))
        return list(self._session.execute(stmt).scalars())

    def delete_activity_log(self, student_ids: list[int]) -> int:
        return self._session.execute(
            delete(StudentActivityLog).where(StudentActivityLog.student_id.in_(student_ids))
        ).rowcount

    def delete_links(self, student_ids: list[int], parent_ids: list[int]) -> int:
        return self._session.execute(
            delete(StudentParent).where(
                or_(StudentParent.student_id.in_(student_ids), StudentParent.parent_id.in_(parent_ids))
            )
        ).rowcount

    def delete_students(self, student_ids: list[int]) -> int:
        return self._session.execute(delete(Student).where(Student.id.in_(student_ids))).rowcount

    def delete_parents(self, parent_ids: list[int]) -> int:
        return self._session.execute(delete(Parent).where(Parent.id.in_(parent_ids))).rowcount
