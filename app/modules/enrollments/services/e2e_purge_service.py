"""E2E purge, enrollments part (#218): the finance use case calls this through the facade."""
from app.db.uow import UnitOfWork
from app.modules.enrollments.repositories.e2e_purge_repository import EnrollmentsE2EPurgeRepository
from app.shared.e2e_purge import PurgeCountsDTO


class EnrollmentsE2EPurgeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._repo = EnrollmentsE2EPurgeRepository(uow.session)

    def find_enrollment_ids(self, student_ids: list[int], group_ids: list[int]) -> list[int]:
        return self._repo.find_enrollment_ids(student_ids, group_ids)

    def purge(
        self, enrollment_ids: list[int], student_ids: list[int], level_ids: list[int]
    ) -> PurgeCountsDTO:
        """Call after attendance (and payments) pointing at these enrollments are gone."""
        return PurgeCountsDTO(counts={
            "enrollment_level_history": self._repo.delete_level_history(
                enrollment_ids, student_ids, level_ids
            ),
            "enrollments": self._repo.delete_enrollments(enrollment_ids),
        })
