import asyncio
import zoneinfo
import logging
from datetime import datetime
from typing import Callable

from app.db.uow import UnitOfWork, unit_of_work
from app.modules.tasks.services.task_service import TaskService

logger = logging.getLogger(__name__)

# Running at 00:05 Cairo time daily
SPAWN_HOUR = 0
SPAWN_MINUTE = 5


async def start_task_scheduler(make_service: Callable[[UnitOfWork], TaskService]) -> None:
    """
    Self-contained background task started at app lifespan.
    Checks every 60 seconds whether it's time to spawn recurring tasks.

    ``make_service`` builds a TaskService over the run's UnitOfWork; the composition root
    (create_app's lifespan) supplies it.
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

                    with unit_of_work() as uow:
                        spawned = make_service(uow).spawn_recurring_tasks(today)
                    logger.info(f"Recurring tasks spawner: spawned {spawned} child tasks.")
                    last_spawn_date = today
        except Exception as e:
            logger.exception(f"Error in recurring tasks scheduler: {e}")

        await asyncio.sleep(60)
