"""
app/modules/notifications/services/competition_notifications.py
─────────────────────────────────────────────────────────────
Competition notification handlers for team registration, payment, and placement.
"""
from typing import Optional
from decimal import Decimal
from fastapi import BackgroundTasks

from app.modules.notifications.services.base_notification_service import BaseNotificationService
from app.modules.notifications.repositories.notification_repository import NotificationRepository


class CompetitionNotificationService(BaseNotificationService):
    """Handles: team registration, fee payment, placement announcements."""

    def __init__(self, repo: NotificationRepository):
        super().__init__(repo)

    # ── Public API ────────────────────────────────────────────────────────

    def notify_team_registration(
        self,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        category: str,
        subcategory: Optional[str],
        background_tasks: BackgroundTasks,
    ) -> None:
        """Notify parent that student was registered for a competition team."""
        background_tasks.add_task(
            self._process_team_registration,
            student_id, team_id, team_name, competition_name, category, subcategory
        )

    def notify_competition_fee_paid(
        self,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        amount: Decimal,
        receipt_number: str,
        background_tasks: BackgroundTasks,
    ) -> None:
        """Notify parent that competition fee was paid."""
        background_tasks.add_task(
            self._process_fee_payment,
            student_id, team_id, team_name, competition_name, amount, receipt_number
        )

    def notify_placement_announcement(
        self,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        placement_rank: int,
        placement_label: Optional[str],
        background_tasks: BackgroundTasks,
    ) -> None:
        """Notify parent of team's competition placement/result."""
        background_tasks.add_task(
            self._process_placement,
            student_id, team_id, team_name, competition_name,
            placement_rank, placement_label
        )

    # ── Private Processors ─────────────────────────────────────────────────

    async def _process_team_registration(
        self,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        category: str,
        subcategory: Optional[str],
    ) -> None:
        """Process team registration notification."""
        template = self._repo.get_template_by_name("competition_team_registration")
        if not template or not template.is_active:
            return

        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "competition_team_registration",
            entity_id=team_id,
            entity_description=f"Team {team_name} registration"
        )

        # Get student name
        student_name = self._get_student_name(student_id)
        category_display = f"{category}{f' - {subcategory}' if subcategory else ''}"
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "team_name": team_name,
            "competition_name": competition_name,
            "category": category_display,
        }

        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)

    async def _process_fee_payment(
        self,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        amount: Decimal,
        receipt_number: str,
    ) -> None:
        """Process fee payment notification."""
        template = self._repo.get_template_by_name("competition_fee_payment")
        if not template or not template.is_active:
            return

        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "competition_fee_payment",
            entity_id=team_id,
            entity_description=f"Team {team_name} fee payment"
        )

        # Get student name
        student_name = self._get_student_name(student_id)
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "team_name": team_name,
            "competition_name": competition_name,
            "amount": str(amount),
            "receipt_number": receipt_number,
        }

        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)

    async def _process_placement(
        self,
        student_id: int,
        team_id: int,
        team_name: str,
        competition_name: str,
        placement_rank: int,
        placement_label: Optional[str],
    ) -> None:
        """Process placement announcement notification."""
        template = self._repo.get_template_by_name("competition_placement")
        if not template or not template.is_active:
            return

        # Get notification recipients with entity context for fallback alert
        recipients = self._resolve_notification_recipients(
            "competition_placement",
            entity_id=team_id,
            entity_description=f"Team {team_name} placement announcement"
        )

        # Get student name
        student_name = self._get_student_name(student_id)
        rank_display = placement_label if placement_label else f"{placement_rank}{self._get_ordinal_suffix(placement_rank)} place"
        
        variables = {
            "parent_name": "Admin",
            "student_name": student_name,
            "team_name": team_name,
            "competition_name": competition_name,
            "placement_rank": placement_rank,
            "placement_label": placement_label or "",
            "rank_display": rank_display,
        }

        # Send to all enabled recipients (admins + additional recipients)
        for email, recipient_id, recipient_type in recipients:
            await self._dispatch(template, "EMAIL", recipient_type, recipient_id, email, variables)

    def _get_ordinal_suffix(self, n: int) -> str:
        """Get ordinal suffix for number (st, nd, rd, th)."""
        if 11 <= n % 100 <= 13:
            return "th"
        return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
