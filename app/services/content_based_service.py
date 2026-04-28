"""
Content-based recommendation service.

Algorithm
─────────
1. Load all active items from DB and build a SimilarityMatrix.
2. Collect the user's interaction history, grouped by item.
3. For each interacted item, compute a weighted seed score:
       seed_score(item) = sum(event.weight for event in item_events)
4. For each candidate item (not yet seen by the user), aggregate
   similarity scores against every seed item, weighted by seed_score:
       candidate_score = sum(
           similarity(seed, candidate) * seed_score(seed)
           for seed in user_history
       )
5. Sort candidates by aggregated score descending.
6. Attach explainability: find the single seed item with the highest
   contribution and surface it as the "reason".
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.ml.model_registry import get_registry
from app.ml.similarity import SimilarityMatrix
from app.models.item import Item
from app.repositories.recommendation_repository import RecommendationRepository


@dataclass
class RecommendationResult:
    item_id: uuid.UUID
    score: float
    reason: str
    category: str


def _build_seed_weights(events) -> dict[uuid.UUID, float]:
    """
    Aggregate event weights per item the user has interacted with.
    Higher-weight events (complete > click > view) dominate the seed.
    """
    seed: dict[uuid.UUID, float] = {}
    for event in events:
        seed[event.item_id] = seed.get(event.item_id, 0.0) + event.weight
    return seed


class ContentBasedService:
    def __init__(self, db: Session) -> None:
        self.repo = RecommendationRepository(db)

    def recommend(
        self,
        user_id: uuid.UUID,
        top_n: int = 10,
        category: str | None = None,
    ) -> list[RecommendationResult]:
        registry = get_registry()

        all_items = self.repo.get_all_active_items()
        if not all_items:
            return []

        items_by_id: dict[uuid.UUID, Item] = {item.id: item for item in all_items}

        if registry.content is not None:
            similarity_matrix = registry.content.similarity_matrix
        else:
            similarity_matrix = SimilarityMatrix(all_items)

        user_events = self.repo.get_user_events(user_id)
        if not user_events:
            return []

        seed_weights = _build_seed_weights(user_events)
        seen_ids: set[uuid.UUID] = set(seed_weights.keys())

        # candidate_id → {score, best_reason_seed_id, best_contribution}
        candidates: dict[uuid.UUID, dict] = {}

        for seed_id, seed_score in seed_weights.items():
            similars = similarity_matrix.get_similar(
                seed_id,
                top_n=len(all_items),
                exclude_ids=seen_ids,
            )
            for candidate_id, sim_score in similars:
                contribution = sim_score * seed_score
                if contribution == 0.0:
                    continue

                if candidate_id not in candidates:
                    candidates[candidate_id] = {
                        "score": 0.0,
                        "best_seed_id": seed_id,
                        "best_contribution": 0.0,
                    }

                candidates[candidate_id]["score"] += contribution
                if contribution > candidates[candidate_id]["best_contribution"]:
                    candidates[candidate_id]["best_contribution"] = contribution
                    candidates[candidate_id]["best_seed_id"] = seed_id

        results: list[RecommendationResult] = []
        for candidate_id, data in candidates.items():
            item = items_by_id.get(candidate_id)
            if not item:
                continue

            # Category filter applied after scoring to avoid biasing the matrix
            if category and item.category != category:
                continue

            best_seed = items_by_id.get(data["best_seed_id"])
            reason = (
                f"Similar to '{best_seed.title}' that you interacted with"
                if best_seed
                else "Based on your activity"
            )

            results.append(
                RecommendationResult(
                    item_id=candidate_id,
                    score=round(data["score"], 4),
                    reason=reason,
                    category=item.category,
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_n]
