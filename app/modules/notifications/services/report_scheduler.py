import asyncio
from datetime import datetime
import logging

from app.modules.notifications.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

async def start_report_scheduler(notification_service: NotificationService) -> None:
    """
    Self-contained asyncio task. Started once at app lifespan.
    Checks every 60 seconds whether a scheduled report is due.
    Uses a 'last_sent' guard to prevent double-sends on fast restarts.
    """
    logger.info("Notification report scheduler started.")
    last_daily = None
    last_weekly = None
    last_monthly = None

    while True:
        try:
            now = datetime.now()

            # Default execution window is 08:00-08:05 local server time.
            # Window-based check prevents missed reports if server is busy at exact 08:00:00.
            if now.hour == 8 and now.minute < 5:
                today = now.date()
                if last_daily != today:
                    await notification_service.send_daily_report()
                    last_daily = today

                if now.weekday() == 0 and last_weekly != today:
                    await notification_service.send_weekly_report()
                    last_weekly = today

                if now.day == 1 and last_monthly != today:
                    await notification_service.send_monthly_report()
                    last_monthly = today
        except Exception as e:
            logger.error(f"Error in report scheduler: {e}")

        await asyncio.sleep(60)
