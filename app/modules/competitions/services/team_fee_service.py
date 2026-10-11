"""Fee writes on team members, exposed through the competitions facade.

Finance owns the payment/refund workflows (ADR-0006), but ``team_members`` is a
competitions table, so finance records fee amounts through this service
(ADR-0004) over its own Unit of Work.
"""
from app.db.uow import UnitOfWork
from app.modules.competitions.repositories.team_repository import TeamRepository


class TeamFeeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._teams = TeamRepository(uow.session)

    def record_payment(self, team_member_id: int, amount: float) -> None:
        """Increment ``amount_paid`` for a team member (no commit)."""
        self._teams.record_payment(team_member_id, amount)
