"""Fee writes on team members, exposed through the competitions facade.

Finance owns the payment/refund workflows (ADR-0006), but ``team_members`` is a
competitions table, so finance records fee amounts through this service
(ADR-0004) over its own Unit of Work.
"""
from app.db.uow import UnitOfWork
import app.modules.competitions.repositories.team_repository as team_repo


class TeamFeeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def record_payment(self, team_member_id: int, amount: float) -> None:
        """Increment ``amount_paid`` for a team member (no commit)."""
        team_repo.record_payment(self._uow.session, team_member_id, amount)
