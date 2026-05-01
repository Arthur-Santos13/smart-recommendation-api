"""
APScheduler configuration and lifecycle helpers.

The scheduler runs inside the same process as the FastAPI application,
using a background thread pool executor so it never blocks the async
event loop.

Scheduler is started inside the FastAPI ``lifespan`` hook and shut down
gracefully on application exit, ensuring in-flight jobs are not
interrupted.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.jobs.retrain_job import retrain_models

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """Return the application-wide scheduler instance."""
    if _scheduler is None:
        raise RuntimeError("Scheduler has not been initialised — call start_scheduler() first.")
    return _scheduler


def start_scheduler() -> BackgroundScheduler:
    """
    Create and start the background scheduler with the retraining job.

    The retraining interval is controlled by ``RETRAIN_INTERVAL_HOURS``
    in settings (default: 6 hours).  Set to 0 to disable automatic
    retraining while still allowing manual triggers via the admin endpoint.
    """
    global _scheduler  # noqa: PLW0603
    _scheduler = BackgroundScheduler(timezone="UTC")

    if settings.RETRAIN_INTERVAL_HOURS > 0:
        _scheduler.add_job(
            retrain_models,
            trigger=IntervalTrigger(hours=settings.RETRAIN_INTERVAL_HOURS),
            id="retrain_models",
            name="Periodic model retraining",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        logger.info(
            "Retraining job scheduled every %d hour(s).",
            settings.RETRAIN_INTERVAL_HOURS,
        )
    else:
        logger.info(
            "RETRAIN_INTERVAL_HOURS=0 — automatic retraining disabled; "
            "use POST /api/v1/admin/retrain to trigger manually."
        )

    _scheduler.start()
    logger.info("Background scheduler started.")
    return _scheduler


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler, waiting for running jobs to finish."""
    global _scheduler  # noqa: PLW0603
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=True)
        logger.info("Background scheduler stopped.")
        _scheduler = None
