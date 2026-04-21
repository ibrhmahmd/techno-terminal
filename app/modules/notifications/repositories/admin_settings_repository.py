"""
app/modules/notifications/repositories/admin_settings_repository.py
─────────────────────────────────────────────────────────────────
Repository for admin notification settings and additional recipients.
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy import text
from sqlmodel import Session, select

from app.modules.auth.models.auth_models import User


class AdminSettingsRepository:
    """Data access for admin notification settings."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Admin Notification Settings ─────────────────────────────────────

    def get_admin_settings(self, admin_id: int) -> List[dict]:
        """Get all notification settings for an admin."""
        stmt = select(
            # We need to use raw SQL or SA Core here since we haven't created the model class
            # Using text() for now
        )
        result = self._session.exec(
            text(f"""SELECT notification_type, is_enabled, channel 
                FROM admin_notification_settings 
                WHERE admin_id = {admin_id}""")
        ).all()
        return [
            {"notification_type": r[0], "is_enabled": r[1], "channel": r[2]}
            for r in result
        ]

    def get_setting(self, admin_id: int, notification_type: str) -> Optional[dict]:
        """Get specific setting for an admin."""
        result = self._session.exec(
            text(f"""SELECT notification_type, is_enabled, channel 
                FROM admin_notification_settings 
                WHERE admin_id = {admin_id} AND notification_type = '{notification_type}'""")
        ).first()
        if result:
            return {"notification_type": result[0], "is_enabled": result[1], "channel": result[2]}
        return None

    def upsert_setting(
        self, admin_id: int, notification_type: str, is_enabled: bool, channel: str = "EMAIL"
    ) -> None:
        """Create or update a setting."""
        existing = self.get_setting(admin_id, notification_type)
        if existing:
            self._session.exec(
                text(f"""UPDATE admin_notification_settings 
                    SET is_enabled = {is_enabled}, channel = '{channel}', updated_at = NOW()
                    WHERE admin_id = {admin_id} AND notification_type = '{notification_type}'""")
            )
        else:
            self._session.exec(
                text(f"""INSERT INTO admin_notification_settings 
                    (admin_id, notification_type, is_enabled, channel)
                    VALUES ({admin_id}, '{notification_type}', {is_enabled}, '{channel}')""")
            )
        self._session.commit()

    def initialize_default_settings(self, admin_id: int) -> None:
        """Create default settings for a new admin (all enabled)."""
        notification_types = [
            "enrollment_created", "enrollment_completed", "enrollment_dropped",
            "enrollment_transferred", "level_progression",
            "payment_received", "payment_reminder",
            "daily_report", "weekly_report", "monthly_report",
            "competition_team_registration", "competition_fee_payment", "competition_placement"
        ]
        for notif_type in notification_types:
            existing = self.get_setting(admin_id, notif_type)
            if not existing:
                self.upsert_setting(admin_id, notif_type, True, "EMAIL")

    def get_enabled_admins_for_notification(self, notification_type: str) -> List[tuple[int, str]]:
        """Get list of (admin_id, email) for admins who have this notification enabled.
        
        NOTE: Currently returns empty list - all notifications go through
        notification_additional_recipients table only.
        """
        # Return empty list - we don't use User/Employee emails anymore
        # All recipients are managed through notification_additional_recipients
        return []

    # ── Additional Recipients ────────────────────────────────────────────

    def get_additional_recipients(self, admin_id: int = None) -> List[dict]:
        """Get all additional recipients (global - ignores admin_id)."""
        result = self._session.exec(
            text("""SELECT id, email, label, notification_types, is_active
                FROM notification_additional_recipients""")
        ).all()
        return [
            {
                "id": r[0], "email": r[1], "label": r[2],
                "notification_types": r[3], "is_active": r[4]
            }
            for r in result
        ]

    def get_recipient(self, recipient_id: int) -> Optional[dict]:
        """Get specific recipient."""
        result = self._session.exec(
            text(f"""SELECT id, email, label, notification_types, is_active
                FROM notification_additional_recipients
                WHERE id = {recipient_id}""")
        ).first()
        if result:
            return {
                "id": result[0], "email": result[1], "label": result[2],
                "notification_types": result[3], "is_active": result[4]
            }
        return None

    def add_recipient(
        self, admin_id: int, email: str, label: Optional[str] = None,
        notification_types: Optional[List[str]] = None
    ) -> int:
        """Add new recipient. Returns recipient ID."""
        types_str = "NULL" if notification_types is None else f"ARRAY{notification_types}"
        label_str = "NULL" if label is None else f"'{label}'"
        
        result = self._session.exec(
            text(f"""INSERT INTO notification_additional_recipients 
                (admin_id, email, label, notification_types)
                VALUES ({admin_id}, '{email}', {label_str}, {types_str})
                RETURNING id""")
        ).first()
        self._session.commit()
        return result[0] if result else 0

    def update_recipient(
        self, recipient_id: int, email: Optional[str] = None,
        label: Optional[str] = None, notification_types: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update recipient. Returns True if found."""
        updates = []
        if email is not None:
            updates.append(f"email = '{email}'")
        if label is not None:
            updates.append(f"label = '{label}'" if label else "label = NULL")
        if notification_types is not None:
            updates.append(f"notification_types = ARRAY{notification_types}" if notification_types else "notification_types = NULL")
        if is_active is not None:
            updates.append(f"is_active = {is_active}")
        
        if not updates:
            return False
            
        updates.append("updated_at = NOW()")
        
        self._session.exec(
            text(f"""UPDATE notification_additional_recipients
                SET {', '.join(updates)}
                WHERE id = {recipient_id}""")
        )
        self._session.commit()
        return True

    def delete_recipient(self, recipient_id: int) -> bool:
        """Delete recipient. Returns True if found."""
        result = self._session.exec(
            text(f"DELETE FROM notification_additional_recipients WHERE id = {recipient_id}")
        )
        self._session.commit()
        return result.rowcount > 0

    def get_active_additional_recipients(
        self, admin_id: int = None, notification_type: str = None
    ) -> List[tuple[str, Optional[str]]]:
        """Get (email, label) for active recipients who should receive this notification (global)."""
        # Both parameters ignored - returns all global active recipients for the notification type
        result = self._session.exec(
            text(f"""SELECT email, label
                FROM notification_additional_recipients
                WHERE is_active = true
                AND (notification_types IS NULL OR '{notification_type}' = ANY(notification_types))""")
        ).all()
        return [(r[0], r[1]) for r in result]
