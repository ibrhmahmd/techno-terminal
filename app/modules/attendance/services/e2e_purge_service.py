"""E2E purge, attendance part (#218): the finance use case calls this through the facade."""
from app.db.uow import UnitOfWork
from app.modules.attendance.repositories.e2e_purge_repository import AttendanceE2EPurgeRepository
from app.shared.e2e_purge import PurgeCountsDTO


class AttendanceE2EPurgeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._repo = AttendanceE2EPurgeRepository(uow.session)

    def purge(self, student_ids: list[int], session_ids: list[int], enrollment_ids: list[int]) -> PurgeCountsDTO:
        return PurgeCountsDTO(counts={
            "attendance": self._repo.delete_for(student_ids, session_ids, enrollment_ids),
        })
