"""
app/modules/notifications/services/report_watchdog.py
──────────────────────────────────────────────────────
Guards against silently missed scheduled reports.

Runs daily just after the report-send window (default 08:15 Cairo) and queries
notification_logs for a SENT row of the daily_report template created today.
If the report was not generated/dispatched, emails all active additional
recipients subscribed to daily_report via GmailEmailDispatcher.

Intentionally reads the database (not Logfire) so it still fires when
telemetry or hosting pipelines are down — the failure mode it protects against.
Does not touch the template system or _dispatch; alert emails go straight to
Gmail over the same SMTP path used for all other notifications.
"""
import asyncio
from datetime import datetime, timezone
import logging
import zoneinfo

import logfire
from sqlmodel import Session

from app.core.config import settings
from app.db.connection import get_engine
from app.modules.notifications.dispatchers.email_dispatcher import GmailEmailDispatcher
from app.modules.notifications.repositories.admin_settings_repository import (
    AdminSettingsRepository,
)
from app.modules.notifications.repositories.notification_repository import (
    NotificationRepository,
)

logger = logging.getLogger(__name__)

CAIRO_TZ = zoneinfo.ZoneInfo("Africa/Cairo")
WATCHDOG_HOUR = settings.daily_report_hour
WATCHDOG_MINUTE = settings.daily_report_minute + 15


def _today_start_utc(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


async def _report_sent_today() -> bool:
    with Session(get_engine(), expire_on_commit=False) as session:
        repo = NotificationRepository(session)
        template = repo.get_template_by_name("daily_report")
        if not template:
            logger.warning("daily_report template not found; watchdog cannot verify")
            return True
        logs = repo.get_logs(
            template_id=template.id,
            status="SENT",
            start_date=_today_start_utc(datetime.now(CAIRO_TZ)),
            limit=1,
        )
        return bool(logs)


async def _send_alert(report_date: str) -> int:
    with Session(get_engine(), expire_on_commit=False) as session:
        recipients = AdminSettingsRepository(
            session
        ).get_active_additional_recipients(notification_type="daily_report")

    if not recipients:
        logger.warning("No active additional recipients for daily_report alert")
        return 0

    subject = f"Daily business report not generated - {report_date}"
    body = (
        "<h3>Daily business report was not sent today</h3>"
        f"<p>{report_date}: no <code>notification_logs</code> entry with status "
        "SENT was found for the <code>daily_report</code> template.</p>"
        "<p>Check the report scheduler (Logfire spans "
        "<code>report_scheduler_dispatch</code> / <code>report_scheduler_error</code>) "
        "or platform logs for the cause.</p>"
    )

    dispatcher = GmailEmailDispatcher()
    sent = 0
    for email, _label in recipients:
        ok, error = await dispatcher.send(email, body, subject=subject)
        if ok:
            sent += 1
        else:
            logger.error("Watchdog alert email failed to %s: %s", email, error)
    return sent


async def start_report_watchdog() -> None:
    """
    Self-contained asyncio task. Started once at app lifespan.
    Checks once per day inside a window right after the report-send window
    and alerts recipients when the daily report was not dispatched.
    """
    logger.info(
        "Report watchdog started. Daily check at %02d:%02d (Cairo Time)",
        WATCHDOG_HOUR,
        WATCHDOG_MINUTE,
    )
    logfire.log(
        "report_watchdog_started",
        check_window=f"{WATCHDOG_HOUR:02d}:{WATCHDOG_MINUTE:02d}",
        timezone="Africa/Cairo",
    )
    last_checked = None

    while True:
        try:
            now = datetime.now(CAIRO_TZ)
            in_window = (
                now.hour == WATCHDOG_HOUR
                and WATCHDOG_MINUTE <= now.minute < WATCHDOG_MINUTE + 5
            )
            if in_window and last_checked != now.date():
                sent = await _report_sent_today()
                alerted = 0
                if not sent:
                    alerted = await _send_alert(now.date().isoformat())
                    logfire.log(
                        "report_watchdog_alerted",
                        recipients=alerted,
                        report_date=now.date().isoformat(),
                    )
                last_checked = now.date()
                logfire.log(
                    "report_watchdog_check",
                    report_sent=sent,
                    report_date=now.date().isoformat(),
                )
        except Exception:
            logger.exception("Error in report watchdog")
            logfire.error("report_watchdog_error")

        await asyncio.sleep(60)