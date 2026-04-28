"""
Collaborative filtering recommendation service.

Wraps KNNCollaborativeFilter with DB data loading and
adds explanation strings for the API response.
"""

import uuid

from sqlalchemy.orm import Session

from app.ml.collaborative_filter import KNNCollaborativeFilter
from app.ml.interaction_matrix import InteractionMatrix
from app.repositories.recommendation_repository import RecommendationRepository
from app.services.content_based_service import RecommendationResult


class CollaborativeService:
    def __init__(self, db: Session, n_neighbors: int = 5) -> None:
        self.repo = RecommendationRepository(db)
        self.n_neighbors = n_neighbors

    def recommend(
        self,
        user_id: uuid.UUID,
        top_n: int = 10,
        category: str | None = None,
    ) -> list[RecommendationResult]:
        all_users = self.repo.get_all_active_users()
        all_items = self.repo.get_all_active_items()
        all_events = self.repo.get_all_events()

        if not all_users or not all_items or not all_events:
            return []

        user_ids = [u.id for u in all_users]
        item_ids = [i.id for i in all_items]
        items_by_id = {i.id: i for i in all_items}

        matrix = InteractionMatrix(
            events=all_events,
            user_ids=user_ids,
            item_ids=item_ids,
        )
        knn = KNNCollaborativeFilter(matrix=matrix, n_neighbors=self.n_neighbors)
        cf_results = knn.recommend(user_id=user_id, top_n=top_n * 2)

        results: list[RecommendationResult] = []
        for cf in cf_results:
            item = items_by_id.get(cf.item_id)
            if not item:
                continue
            if category and item.category != category:
                continue

            reason = "Users similar to you also interacted with this item"

            results.append(
                RecommendationResult(
                    item_id=cf.item_id,
                    score=cf.score,
                    reason=reason,
                    category=item.category,
                )
            )

        return results[:top_n]
