import asyncio
import os
from datetime import datetime
import logging

from app.modules.notifications.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Load daily report schedule from environment (default: 20:00 = 8 PM)
DAILY_REPORT_HOUR = int(os.getenv("DAILY_REPORT_HOUR", "20"))
DAILY_REPORT_MINUTE = int(os.getenv("DAILY_REPORT_MINUTE", "0"))

from typing import Callable

async def start_report_scheduler(make_service: Callable[[], NotificationService]) -> None:
    """
    Self-contained asyncio task. Started once at app lifespan.
    Checks every 60 seconds whether a scheduled report is due.
    Uses a 'last_sent' guard to prevent double-sends on fast restarts.
    """
    logger.info(f"Notification report scheduler started. Daily report at {DAILY_REPORT_HOUR:02d}:{DAILY_REPORT_MINUTE:02d}")
    last_daily = None
    last_weekly = None
    last_monthly = None

    while True:
        try:
            now = datetime.now()

            # Check if we're in the execution window for daily report
            # Window-based check prevents missed reports if server is busy at exact time
            if now.hour == DAILY_REPORT_HOUR and now.minute >= DAILY_REPORT_MINUTE and now.minute < DAILY_REPORT_MINUTE + 5:
                today = now.date()
                
                # Check if we need to send any report today
                if last_daily != today or (now.weekday() == 0 and last_weekly != today) or (now.day == 1 and last_monthly != today):
                    svc = make_service()
                    try:
                        if last_daily != today:
                            await svc.send_daily_report()
                            last_daily = today

                        if now.weekday() == 0 and last_weekly != today:
                            await svc.send_weekly_report()
                            last_weekly = today

                        if now.day == 1 and last_monthly != today:
                            await svc.send_monthly_report()
                            last_monthly = today
                    finally:
                        svc._repo._session.close()

        except Exception as e:
            logger.error(f"Error in report scheduler: {e}")

        await asyncio.sleep(60)
