"""
In-memory model registry.

Holds the pre-trained model artifacts loaded at application startup.
Services check this registry before falling back to on-demand training,
avoiding the cost of re-computing the TF-IDF matrix and KNN model on
every request.

Typical lifecycle
─────────────────
1. ``load_into_registry()`` is called once inside the FastAPI lifespan hook.
2. ``ContentBasedService`` and ``CollaborativeService`` call ``get_registry()``
   and use the cached artifacts if available.
3. If model files are absent (first run before training), services fall back
   to building the models from the database on each request.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ml.trainer import CollaborativeModel, ContentModel


@dataclass
class ModelRegistry:
    content: ContentModel | None = None
    collaborative: CollaborativeModel | None = None


_registry: ModelRegistry = ModelRegistry()


def get_registry() -> ModelRegistry:
    """Return the application-wide model registry singleton."""
    return _registry


def load_into_registry(model_dir: str) -> None:
    """
    Load persisted models from disk into the in-memory registry.

    Missing model files are silently skipped — services will fall back
    to on-demand training for that model type.
    """
    from pathlib import Path

    from app.ml.model_store import load_collaborative_model, load_content_model

    path = Path(model_dir)
    _registry.content = load_content_model(path)
    _registry.collaborative = load_collaborative_model(path)
