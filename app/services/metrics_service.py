"""
Metrics service.

Computes three offline recommendation quality metrics:

1. Usage rate
   Fraction of active users who have at least one recorded interaction.
   Also reports total events, average events per engaged user, and a
   breakdown by event type.

2. Precision@k  (leave-one-out content-based evaluation)
   For each user with ≥ 2 distinct interacted items:
     - Hold out the most-recently-interacted item.
     - Recompute CB scores using only the remaining events as seeds.
     - Check whether the held-out item lands in the top-k ranking.
   precision@k = hits / evaluated_users

3. Top recommended items
   For each active user with events, score all candidate items through
   the content-based pipeline and count how many users' top-N list each
   item appears in.  Returns the N most-frequent items.

The SimilarityMatrix is built once per MetricsService instance, reusing
the registry artifact when available to avoid redundant TF-IDF fitting.
"""

import uuid
from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.ml.model_registry import get_registry
from app.ml.similarity import SimilarityMatrix
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.metrics import (
    MetricsSummary,
    PrecisionAtKMetrics,
    TopRecommendedItem,
    UsageRateMetrics,
)


def _build_seed_weights(
    events, allowed_ids: set[uuid.UUID]
) -> dict[uuid.UUID, float]:
    """Aggregate event weights for items that belong to allowed_ids."""
    seed: dict[uuid.UUID, float] = {}
    for event in events:
        if event.item_id in allowed_ids:
            seed[event.item_id] = seed.get(event.item_id, 0.0) + event.weight
    return seed


def _score_candidates(
    seed_weights: dict[uuid.UUID, float],
    similarity_matrix: SimilarityMatrix,
    n_items: int,
    exclude_ids: set[uuid.UUID],
) -> dict[uuid.UUID, float]:
    """
    Aggregate candidate scores from all seed items.
    candidate_score = Σ similarity(seed, candidate) × seed_weight
    """
    candidates: dict[uuid.UUID, float] = {}
    for seed_id, seed_score in seed_weights.items():
        for candidate_id, sim_score in similarity_matrix.get_similar(
            seed_id, top_n=n_items, exclude_ids=exclude_ids
        ):
            contribution = sim_score * seed_score
            if contribution > 0:
                candidates[candidate_id] = (
                    candidates.get(candidate_id, 0.0) + contribution
                )
    return candidates


class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.metrics_repo = MetricsRepository(db)
        self.rec_repo = RecommendationRepository(db)

        # Build (or reuse) the similarity matrix once for the whole request
        registry = get_registry()
        self._all_items = self.rec_repo.get_all_active_items()
        self._items_by_id = {item.id: item for item in self._all_items}

        if registry.content is not None:
            self._similarity_matrix: SimilarityMatrix | None = (
                registry.content.similarity_matrix
            )
        elif self._all_items:
            self._similarity_matrix = SimilarityMatrix(self._all_items)
        else:
            self._similarity_matrix = None

    # ------------------------------------------------------------------
    # Usage rate
    # ------------------------------------------------------------------

    def compute_usage_rate(self) -> UsageRateMetrics:
        total_active = self.metrics_repo.count_active_users()
        users_with_events = self.metrics_repo.get_active_users_with_events()
        engaged_count = len(users_with_events)
        total_events = self.metrics_repo.count_total_events()
        events_by_type = self.metrics_repo.count_events_by_type()

        usage_rate = round(engaged_count / total_active, 4) if total_active else 0.0
        avg_events = (
            round(total_events / engaged_count, 2) if engaged_count else 0.0
        )

        return UsageRateMetrics(
            total_active_users=total_active,
            users_with_interactions=engaged_count,
            usage_rate=usage_rate,
            total_events=total_events,
            avg_events_per_active_user=avg_events,
            events_by_type=events_by_type,
        )

    # ------------------------------------------------------------------
    # Top recommended items
    # ------------------------------------------------------------------

    def compute_top_recommended_items(
        self,
        top_n: int = 10,
        per_user_top_n: int = 10,
    ) -> list[TopRecommendedItem]:
        """
        Score candidates for every active user with events and tally how many
        users' top-per_user_top_n list each item appears in.
        """
        if not self._similarity_matrix or not self._all_items:
            return []

        n_items = len(self._all_items)
        users_with_events = self.metrics_repo.get_active_users_with_events()
        all_events = self.metrics_repo.get_all_events_ordered_by_user()

        user_events: dict[uuid.UUID, list] = defaultdict(list)
        for event in all_events:
            user_events[event.user_id].append(event)

        counter: Counter = Counter()

        for user in users_with_events:
            events = user_events.get(user.id, [])
            if not events:
                continue

            seen_ids: set[uuid.UUID] = {e.item_id for e in events}
            seed_weights = _build_seed_weights(events, seen_ids)
            if not seed_weights:
                continue

            candidates = _score_candidates(
                seed_weights, self._similarity_matrix, n_items, seen_ids
            )
            top_k = sorted(candidates, key=lambda x: candidates[x], reverse=True)[
                :per_user_top_n
            ]
            counter.update(top_k)

        result: list[TopRecommendedItem] = []
        for item_id, count in counter.most_common(top_n):
            item = self._items_by_id.get(item_id)
            if item:
                result.append(
                    TopRecommendedItem(
                        item_id=item_id,
                        title=item.title,
                        category=item.category,
                        recommendation_count=count,
                    )
                )
        return result

    # ------------------------------------------------------------------
    # Precision@k (leave-one-out)
    # ------------------------------------------------------------------

    def compute_precision_at_k(self, k: int = 10) -> PrecisionAtKMetrics:
        """
        Leave-one-out precision@k over the content-based pipeline.

        For each user with ≥ 2 distinct interacted items, the item from
        their most recent event is held out, CB scores are recomputed
        from remaining interactions, and we check whether the held-out
        item lands within the top-k ranked candidates.

        precision@k = hits / evaluated_users
        """
        if not self._similarity_matrix or not self._all_items:
            return PrecisionAtKMetrics(
                k=k, evaluated_users=0, hits=0, precision_at_k=0.0
            )

        n_items = len(self._all_items)
        all_events = self.metrics_repo.get_all_events_ordered_by_user()

        user_events: dict[uuid.UUID, list] = defaultdict(list)
        for event in all_events:
            user_events[event.user_id].append(event)

        hits = 0
        evaluated = 0

        for user_id, events in user_events.items():
            # Build ordered list of distinct items in chronological order
            seen_order: list[uuid.UUID] = []
            seen_set: set[uuid.UUID] = set()
            for e in events:
                if e.item_id not in seen_set:
                    seen_order.append(e.item_id)
                    seen_set.add(e.item_id)

            if len(seen_order) < 2:
                continue  # need at least 1 train item + 1 held-out item

            held_out_id = seen_order[-1]
            train_ids: set[uuid.UUID] = set(seen_order[:-1])

            seed_weights = _build_seed_weights(events, train_ids)
            if not seed_weights:
                continue

            candidates = _score_candidates(
                seed_weights, self._similarity_matrix, n_items, train_ids
            )
            top_k_ids = sorted(
                candidates, key=lambda x: candidates[x], reverse=True
            )[:k]

            evaluated += 1
            if held_out_id in top_k_ids:
                hits += 1

        precision = round(hits / evaluated, 4) if evaluated > 0 else 0.0
        return PrecisionAtKMetrics(
            k=k,
            evaluated_users=evaluated,
            hits=hits,
            precision_at_k=precision,
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self, top_n: int = 10, k: int = 10) -> MetricsSummary:
        return MetricsSummary(
            usage=self.compute_usage_rate(),
            precision_at_k=self.compute_precision_at_k(k=k),
            top_recommended_items=self.compute_top_recommended_items(top_n=top_n),
        )
