"""
Hybrid recommendation service.

Orchestrates ContentBasedService and CollaborativeService, then
merges their results via the weighted hybrid_merger.

Default balance: 70% content-based / 30% collaborative.
The caller can override both weights through the endpoint query params,
enabling A/B testing of different blending strategies.

Cold-start handling:
    - No interaction history → falls back to content-based only (score=1.0 per item)
    - Insufficient users for KNN → falls back to content-based only
"""

import uuid

from sqlalchemy.orm import Session

from app.ml.hybrid_merger import merge_recommendations
from app.services.collaborative_service import CollaborativeService
from app.services.content_based_service import ContentBasedService, RecommendationResult


class HybridService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def recommend(
        self,
        user_id: uuid.UUID,
        top_n: int = 10,
        category: str | None = None,
        cb_weight: float = 0.7,
        cf_weight: float = 0.3,
        n_neighbors: int = 5,
    ) -> list[RecommendationResult]:
        # Fetch a larger pool from each source so the merger has enough
        # candidates after deduplication and optional category filtering
        pool = max(top_n * 3, 30)

        cb_results = ContentBasedService(self.db).recommend(
            user_id=user_id,
            top_n=pool,
            category=category,
        )

        cf_results = CollaborativeService(self.db, n_neighbors=n_neighbors).recommend(
            user_id=user_id,
            top_n=pool,
            category=category,
        )

        # Cold-start: no collaborative signal → pure content-based
        if not cf_results:
            for r in cb_results:
                r.reason = f"{r.reason} (content)"
            return cb_results[:top_n]

        # Cold-start: no content signal → pure collaborative
        if not cb_results:
            for r in cf_results:
                r.reason = f"{r.reason} (collaborative)"
            return cf_results[:top_n]

        return merge_recommendations(
            cb_results=cb_results,
            cf_results=cf_results,
            cb_weight=cb_weight,
            cf_weight=cf_weight,
            top_n=top_n,
            category=category,
        )
