"""Hard deletes of E2E test data in competitions' own tables (#218). Staging only."""
from sqlalchemy import delete, or_, select
from sqlmodel import Session

from app.modules.competitions.models.competition_models import Competition
from app.modules.competitions.models.team_models import Team, TeamMember


class CompetitionsE2EPurgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _ids(self, stmt) -> list[int]:
        return list(self._session.execute(stmt).scalars())

    def find_competition_ids(self, prefix: str) -> list[int]:
        return self._ids(select(Competition.id).where(Competition.name.startswith(prefix, autoescape=True)))

    def find_team_ids(self, prefix: str, competition_ids: list[int]) -> list[int]:
        return self._ids(select(Team.id).where(or_(
            Team.team_name.startswith(prefix, autoescape=True), Team.competition_id.in_(competition_ids),
        )))

    def find_team_member_ids(self, team_ids: list[int], student_ids: list[int]) -> list[int]:
        return self._ids(select(TeamMember.id).where(or_(
            TeamMember.team_id.in_(team_ids), TeamMember.student_id.in_(student_ids),
        )))

    def delete_team_members(self, team_member_ids: list[int]) -> int:
        return self._session.execute(
            delete(TeamMember).where(TeamMember.id.in_(team_member_ids))
        ).rowcount

    def delete_teams(self, team_ids: list[int]) -> int:
        return self._session.execute(delete(Team).where(Team.id.in_(team_ids))).rowcount

    def delete_competitions(self, competition_ids: list[int]) -> int:
        return self._session.execute(
            delete(Competition).where(Competition.id.in_(competition_ids))
        ).rowcount
