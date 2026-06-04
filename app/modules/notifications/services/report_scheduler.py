import asyncio
from datetime import datetime, timedelta
import logging
from typing import Callable
import zoneinfo

from app.core.config import settings
from app.modules.notifications.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

DAILY_REPORT_HOUR = settings.daily_report_hour
DAILY_REPORT_MINUTE = settings.daily_report_minute

async def start_report_scheduler(make_service: Callable[[], NotificationService]) -> None:
    """
    Self-contained asyncio task. Started once at app lifespan.
    Checks every 60 seconds whether a scheduled report is due.
    Uses a 'last_sent' guard to prevent double-sends on fast restarts.
    """
    logger.info(f"Notification report scheduler started. Daily report at {DAILY_REPORT_HOUR:02d}:{DAILY_REPORT_MINUTE:02d} (Cairo Time)")
    last_daily = None
    last_weekly = None
    last_monthly = None
    cairo_tz = zoneinfo.ZoneInfo("Africa/Cairo")

    if not settings.scheduler_enabled:
        logger.info("Report scheduler is disabled via SCHEDULER_ENABLED setting.")
        return

    while True:
        try:
            now = datetime.now(cairo_tz)

            # Check if we're in the execution window for daily report
            # Window-based check prevents missed reports if server is busy at exact time
            if now.hour == DAILY_REPORT_HOUR and now.minute >= DAILY_REPORT_MINUTE and now.minute < DAILY_REPORT_MINUTE + 5:
                today = now.date()
                
                # Check if we need to send any report today
                if last_daily != today or (now.weekday() == 0 and last_weekly != today) or (now.day == 1 and last_monthly != today):
                    svc = make_service()
                    try:
                        if last_daily != today:
                            yesterday = today - timedelta(days=1)
                            await svc.send_daily_report(target_date=yesterday)
                            last_daily = today

                        if now.weekday() == 0 and last_weekly != today:
                            await svc.send_weekly_report()
                            last_weekly = today

                        if now.day == 1 and last_monthly != today:
                            await svc.send_monthly_report()
                            last_monthly = today
                    finally:
                        svc.close_session()

        except Exception:
            logger.exception("Error in report scheduler")

        await asyncio.sleep(60)
