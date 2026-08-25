"""
app/observability/scheduler.py
──────────────────────────────
Background task runner for the business metrics collector.
Integrates with FastAPI lifespan.
"""
import asyncio
import logging

from .business_metrics import get_collector

logger = logging.getLogger(__name__)

_collector_task: asyncio.Task | None = None


async def run_metrics_collector(interval_seconds: int = 60) -> asyncio.Task:
    """
    Start the business metrics collector as a background task.
    
    Returns the task so it can be cancelled on shutdown.
    """
    global _collector_task
    collector = get_collector()
    _collector_task = asyncio.create_task(collector.run_forever(interval_seconds))
    logger.info("Business metrics collector task started")
    return _collector_task


async def stop_metrics_collector() -> None:
    """Stop the business metrics collector gracefully."""
    global _collector_task
    if _collector_task is not None:
        _collector_task.cancel()
        try:
            await asyncio.wait_for(_collector_task, timeout=10.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            logger.warning("Metrics collector task did not stop cleanly")
        _collector_task = None
        logger.info("Business metrics collector task stopped")