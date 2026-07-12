import asyncio
import zoneinfo
import logging
from datetime import datetime, date
from typing import Callable

from app.modules.tasks.service import TaskService

logger = logging.getLogger(__name__)

# Running at 00:05 Cairo time daily
SPAWN_HOUR = 0
SPAWN_MINUTE = 5


async def start_task_scheduler(make_service: Callable[[], TaskService]) -> None:
    """
    Self-contained background task started at app lifespan.
    Checks every 60 seconds whether it's time to spawn recurring tasks.
    """
    logger.info("Recurring tasks spawner scheduler started.")
    last_spawn_date = None
    cairo_tz = zoneinfo.ZoneInfo("Africa/Cairo")

    while True:
        try:
            now = datetime.now(cairo_tz)
            
            if now.hour == SPAWN_HOUR and now.minute >= SPAWN_MINUTE and now.minute < SPAWN_MINUTE + 5:
                today = now.date()
                if last_spawn_date != today:
                    logger.info(f"Running daily recurring tasks spawner for target date {today}")
                    
                    # Instantiate service using fresh session
                    service = make_service()
                    try:
                        spawned = service.spawn_recurring_tasks(today)
                        logger.info(f"Recurring tasks spawner: spawned {spawned} child tasks.")
                        last_spawn_date = today
                    finally:
                        # Close the session on UoW
                        service._uow._session.close()
        except Exception as e:
            logger.exception(f"Error in recurring tasks scheduler: {e}")

        await asyncio.sleep(60)
