"""
Standalone model training script.

Usage:
    python -m scripts.train

Trains both the content-based and collaborative filtering models using
all active data in the database, then saves the artifacts to the
directory specified by MODEL_DIR in settings (default: models/).

Prerequisites:
    - DATABASE_URL is configured in .env
    - The database has been migrated (alembic upgrade head)
    - Seed data has been loaded (python -m scripts.seed)
"""

import logging
import sys
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.ml.model_store import save_collaborative_model, save_content_model
from app.ml.trainer import ModelTrainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_training() -> None:
    model_dir = Path(settings.MODEL_DIR)
    db = SessionLocal()
    try:
        trainer = ModelTrainer(db)

        logger.info("Training content-based model...")
        content = trainer.train_content_model()
        save_content_model(content, model_dir)
        logger.info("Content model ready: %d items.", content.item_count)

        logger.info("Training collaborative filtering model...")
        collaborative = trainer.train_collaborative_model()
        save_collaborative_model(collaborative, model_dir)
        logger.info(
            "Collaborative model ready: %d users / %d items.",
            collaborative.user_count,
            collaborative.item_count,
        )

        logger.info("All models saved to: %s", model_dir.resolve())
    except ValueError as exc:
        logger.error("Training aborted: %s", exc)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_training()
