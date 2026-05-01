"""
Periodic model retraining job.

This module contains the job function invoked by APScheduler on each
scheduled run. It trains both the content-based and collaborative
filtering models from the current database state, persists the artifacts
to disk, and refreshes the in-memory model registry so that subsequent
requests immediately use the updated models — with no application restart.

Design decisions
────────────────
- A fresh DB session is opened for each run and closed in a ``finally``
  block to avoid connection leaks between scheduled executions.
- Training errors are caught and logged rather than propagated, so a
  transient DB issue during one run does not stop the scheduler.
- The registry is updated atomically (both models at once or neither)
  only when training fully succeeds, preventing a half-updated state.
"""

import logging
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.ml.model_registry import get_registry
from app.ml.model_store import save_collaborative_model, save_content_model
from app.ml.trainer import ModelTrainer

logger = logging.getLogger(__name__)


def retrain_models() -> None:
    """
    Train both ML models, persist them to disk, and refresh the registry.

    Intended to be called by APScheduler on a configurable interval.
    Safe to call manually from the admin endpoint.
    """
    logger.info("Scheduled retraining started.")
    model_dir = Path(settings.MODEL_DIR)
    db = SessionLocal()
    try:
        trainer = ModelTrainer(db)
        content = trainer.train_content_model()
        collaborative = trainer.train_collaborative_model()

        save_content_model(content, model_dir)
        save_collaborative_model(collaborative, model_dir)

        registry = get_registry()
        registry.content = content
        registry.collaborative = collaborative

        logger.info(
            "Retraining complete — content: %d items, collaborative: %d users / %d items.",
            content.item_count,
            collaborative.user_count,
            collaborative.item_count,
        )
    except ValueError as exc:
        logger.warning("Retraining skipped — insufficient data: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("Retraining failed with unexpected error: %s", exc, exc_info=True)
    finally:
        db.close()
