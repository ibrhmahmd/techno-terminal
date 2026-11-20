"""E2E purge, academics part (#218): the finance use case calls this through the facade."""
from app.db.uow import UnitOfWork
from app.modules.academics.repositories.e2e_purge_repository import AcademicsE2EPurgeRepository
from app.modules.academics.schemas.e2e_purge import AcademicsE2ESeedDTO
from app.shared.e2e_purge import PurgeCountsDTO


class AcademicsE2EPurgeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._repo = AcademicsE2EPurgeRepository(uow.session)

    def find_seed(self, prefix: str) -> AcademicsE2ESeedDTO:
        r = self._repo
        course_ids = r.find_course_ids(prefix)
        group_ids = r.find_group_ids(prefix, course_ids)
        return AcademicsE2ESeedDTO(
            course_ids=course_ids,
            group_ids=group_ids,
            session_ids=r.find_session_ids(group_ids),
            level_ids=r.find_level_ids(group_ids, course_ids),
        )

    def purge(self, seed: AcademicsE2ESeedDTO) -> PurgeCountsDTO:
        """Call after attendance, enrollments and level history that point at these rows are gone."""
        r = self._repo
        return PurgeCountsDTO(counts={
            "sessions": r.delete_sessions(seed.group_ids),
            "group_course_history": r.delete_course_history(seed.group_ids, seed.course_ids),
            "group_levels": r.delete_levels(seed.level_ids),
            "groups": r.delete_groups(seed.group_ids),
            "courses": r.delete_courses(seed.course_ids),
        })
