"""E2E purge, competitions part (#218): the finance use case calls this through the facade."""
from app.db.uow import UnitOfWork
from app.modules.competitions.repositories.e2e_purge_repository import CompetitionsE2EPurgeRepository
from app.modules.competitions.schemas.e2e_purge import CompetitionsE2ESeedDTO
from app.shared.e2e_purge import PurgeCountsDTO


class CompetitionsE2EPurgeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._repo = CompetitionsE2EPurgeRepository(uow.session)

    def find_seed(self, prefix: str, student_ids: list[int]) -> CompetitionsE2ESeedDTO:
        r = self._repo
        competition_ids = r.find_competition_ids(prefix)
        team_ids = r.find_team_ids(prefix, competition_ids)
        return CompetitionsE2ESeedDTO(
            competition_ids=competition_ids,
            team_ids=team_ids,
            team_member_ids=r.find_team_member_ids(team_ids, student_ids),
        )

    def purge(self, seed: CompetitionsE2ESeedDTO) -> PurgeCountsDTO:
        """Call after payments pointing at these team members are gone."""
        r = self._repo
        return PurgeCountsDTO(counts={
            "team_members": r.delete_team_members(seed.team_member_ids),
            "teams": r.delete_teams(seed.team_ids),
            "competitions": r.delete_competitions(seed.competition_ids),
        })
