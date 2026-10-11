"""Read-side queries for competition fee payments/refunds (reads any model, ADR-0004)."""
from typing import Optional

from sqlmodel import Session, select

from app.modules.competitions.models import Competition, Team, TeamMember
from app.modules.crm.models.parent_models import Parent


class CompetitionFeeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_team(self, team_id: int) -> Optional[Team]:
        return self._session.get(Team, team_id)

    def get_team_member(self, team_id: int, student_id: int) -> Optional[TeamMember]:
        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id, TeamMember.student_id == student_id
        )
        return self._session.exec(stmt).first()

    def get_team_member_by_id(self, member_id: int) -> Optional[TeamMember]:
        return self._session.get(TeamMember, member_id)

    def get_competition(self, competition_id: int) -> Optional[Competition]:
        return self._session.get(Competition, competition_id)

    def get_parent(self, parent_id: int) -> Optional[Parent]:
        return self._session.get(Parent, parent_id)

    def get_member_of_student(self, student_id: int) -> Optional[TeamMember]:
        stmt = select(TeamMember).where(TeamMember.student_id == student_id)
        return self._session.exec(stmt).first()
