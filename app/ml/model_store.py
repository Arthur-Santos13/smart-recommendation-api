"""
Joblib-based model persistence.

Provides save/load helpers for content and collaborative model artifacts.
The caller is responsible for ensuring the model directory exists and
that the application has write permissions to it.
"""

import logging
from pathlib import Path

import joblib

from app.ml.trainer import CollaborativeModel, ContentModel

logger = logging.getLogger(__name__)

_CONTENT_FILE = "content_model.joblib"
_COLLABORATIVE_FILE = "collaborative_model.joblib"


def save_content_model(model: ContentModel, model_dir: Path) -> None:
    """Serialize the content model artifact to disk using joblib compress=3."""
    model_dir.mkdir(parents=True, exist_ok=True)
    path = model_dir / _CONTENT_FILE
    joblib.dump(model, path, compress=3)
    logger.info("Content model saved → %s", path)


def load_content_model(model_dir: Path) -> ContentModel | None:
    """Deserialize the content model from disk. Returns None if the file is missing."""
    path = model_dir / _CONTENT_FILE
    if not path.exists():
        logger.warning("Content model not found at %s — will rebuild on demand.", path)
        return None
    model: ContentModel = joblib.load(path)
    logger.info(
        "Content model loaded ← %s (trained_at=%s, items=%d)",
        path,
        model.trained_at,
        model.item_count,
    )
    return model


def save_collaborative_model(model: CollaborativeModel, model_dir: Path) -> None:
    """Serialize the collaborative model artifact to disk using joblib compress=3."""
    model_dir.mkdir(parents=True, exist_ok=True)
    path = model_dir / _COLLABORATIVE_FILE
    joblib.dump(model, path, compress=3)
    logger.info("Collaborative model saved → %s", path)


def load_collaborative_model(model_dir: Path) -> CollaborativeModel | None:
    """Deserialize the collaborative model from disk. Returns None if the file is missing."""
    path = model_dir / _COLLABORATIVE_FILE
    if not path.exists():
        logger.warning(
            "Collaborative model not found at %s — will rebuild on demand.", path
        )
        return None
    model: CollaborativeModel = joblib.load(path)
    logger.info(
        "Collaborative model loaded ← %s (trained_at=%s, users=%d, items=%d)",
        path,
        model.trained_at,
        model.user_count,
        model.item_count,
    )
    return model
