"""E2E purge, crm part (#218): the finance use case calls this through the facade."""
from app.db.uow import UnitOfWork
from app.modules.crm.repositories.e2e_purge_repository import CrmE2EPurgeRepository
from app.modules.crm.schemas.e2e_purge import CrmE2ESeedDTO
from app.shared.e2e_purge import PurgeCountsDTO


class CrmE2EPurgeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._repo = CrmE2EPurgeRepository(uow.session)

    def find_seed(self, prefix: str) -> CrmE2ESeedDTO:
        return CrmE2ESeedDTO(
            student_ids=self._repo.find_student_ids(prefix),
            parent_ids=self._repo.find_parent_ids(prefix),
        )

    def purge(self, seed: CrmE2ESeedDTO) -> PurgeCountsDTO:
        """Delete the seed students and parents. Call after every table that points at a student."""
        r = self._repo
        return PurgeCountsDTO(counts={
            "student_activity_log": r.delete_activity_log(seed.student_ids),
            "student_parents": r.delete_links(seed.student_ids, seed.parent_ids),
            "students": r.delete_students(seed.student_ids),
            "parents": r.delete_parents(seed.parent_ids),
        })
