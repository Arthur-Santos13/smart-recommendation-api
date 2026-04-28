"""
Model training pipeline.

Orchestrates the preprocessing and fitting steps for both the
content-based and collaborative filtering models, returning
typed artifacts that can be persisted to disk or held in memory.

Preprocessing conventions
─────────────────────────
Content model
  - Only active items are included (soft-deleted items are excluded).
  - Tags are repeated 3× in the text corpus to boost their TF weight
    (handled inside SimilarityMatrix → build_tfidf_matrix).

Collaborative model
  - Only active users and active items are included.
  - Interaction weights use max-aggregation per (user, item) pair to
    prevent repeated event types from inflating a single pair's score.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ml.collaborative_filter import KNNCollaborativeFilter
from app.ml.interaction_matrix import InteractionMatrix
from app.ml.similarity import SimilarityMatrix
from app.repositories.recommendation_repository import RecommendationRepository


@dataclass
class ContentModel:
    """Trained content-based model artifact."""

    similarity_matrix: SimilarityMatrix
    item_count: int
    trained_at: datetime


@dataclass
class CollaborativeModel:
    """Trained collaborative filtering artifact."""

    interaction_matrix: InteractionMatrix
    knn_filter: KNNCollaborativeFilter
    user_count: int
    item_count: int
    trained_at: datetime


@dataclass
class TrainedModels:
    """Container for both trained model artifacts."""

    content: ContentModel
    collaborative: CollaborativeModel


class ModelTrainer:
    """
    Loads data from the database and trains both recommendation models.

    Raises ``ValueError`` if there is insufficient data to train a model
    (e.g. empty catalogue or no users).
    """

    def __init__(self, db: Session) -> None:
        self.repo = RecommendationRepository(db)

    def train_content_model(self) -> ContentModel:
        """Fit TF-IDF vectorizer and compute the item-item similarity matrix."""
        items = self.repo.get_all_active_items()
        if not items:
            raise ValueError("No active items available for content model training.")

        similarity_matrix = SimilarityMatrix(items)

        return ContentModel(
            similarity_matrix=similarity_matrix,
            item_count=len(items),
            trained_at=datetime.now(timezone.utc),
        )

    def train_collaborative_model(self, n_neighbors: int = 5) -> CollaborativeModel:
        """Build the user-item interaction matrix and fit the KNN model."""
        users = self.repo.get_all_active_users()
        items = self.repo.get_all_active_items()
        events = self.repo.get_all_events()

        if not users or not items:
            raise ValueError(
                "Insufficient data for collaborative model training "
                f"(users={len(users)}, items={len(items)})."
            )

        user_ids = [u.id for u in users]
        item_ids = [i.id for i in items]

        interaction_matrix = InteractionMatrix(
            events=events,
            user_ids=user_ids,
            item_ids=item_ids,
        )
        knn_filter = KNNCollaborativeFilter(
            matrix=interaction_matrix,
            n_neighbors=n_neighbors,
        )

        return CollaborativeModel(
            interaction_matrix=interaction_matrix,
            knn_filter=knn_filter,
            user_count=len(users),
            item_count=len(items),
            trained_at=datetime.now(timezone.utc),
        )

    def train_all(self, n_neighbors: int = 5) -> TrainedModels:
        """Train both models and return them together."""
        return TrainedModels(
            content=self.train_content_model(),
            collaborative=self.train_collaborative_model(n_neighbors=n_neighbors),
        )
