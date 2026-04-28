"""
KNN-based collaborative filtering.

Algorithm
─────────
1. Build the user-item InteractionMatrix from all events.
2. Fit a NearestNeighbors model (cosine metric, brute-force for sparse matrices).
3. For the target user, find the K most similar neighbours.
4. Aggregate neighbour interaction scores, weighted by neighbour similarity:
       item_score = Σ (neighbour_similarity × neighbour_weight_for_item)
5. Exclude items the target user has already interacted with.
6. Return ranked (item_id, score, neighbour_ids) tuples for the service layer.
"""

import uuid
from dataclasses import dataclass, field

import numpy as np
from sklearn.neighbors import NearestNeighbors

from app.ml.interaction_matrix import InteractionMatrix


@dataclass
class CFResult:
    item_id: uuid.UUID
    score: float
    similar_user_ids: list[uuid.UUID] = field(default_factory=list)


class KNNCollaborativeFilter:
    """
    Fits KNN over the user-item matrix and produces per-user recommendations.
    A new instance should be created per request (or cached with a TTL).
    """

    def __init__(self, matrix: InteractionMatrix, n_neighbors: int = 5) -> None:
        self.matrix = matrix
        self.n_neighbors = n_neighbors
        self._model: NearestNeighbors | None = None

        n_users = matrix.matrix.shape[0]
        if n_users > 1:
            k = min(n_neighbors + 1, n_users)  # +1 because the user itself is included
            self._model = NearestNeighbors(
                n_neighbors=k,
                metric="cosine",
                algorithm="brute",
            )
            self._model.fit(matrix.matrix)

    def recommend(
        self,
        user_id: uuid.UUID,
        top_n: int = 10,
    ) -> list[CFResult]:
        if self._model is None:
            return []

        user_idx = self.matrix.user_index.get(user_id)
        if user_idx is None:
            return []

        user_vector = self.matrix.matrix[user_idx]
        distances, indices = self._model.kneighbors(user_vector)

        # distances are cosine distances → similarity = 1 - distance
        distances = distances.flatten()
        indices = indices.flatten()

        already_seen = self.matrix.get_interacted_item_ids(user_id)

        # Accumulate weighted item scores from neighbours
        item_scores: dict[int, float] = {}
        item_contributors: dict[int, list[uuid.UUID]] = {}

        for dist, neighbour_idx in zip(distances, indices):
            if neighbour_idx == user_idx:
                continue  # skip the user themselves

            similarity = max(0.0, 1.0 - float(dist))
            if similarity == 0.0:
                continue

            neighbour_id = self.matrix.user_ids[neighbour_idx]
            neighbour_vec = np.asarray(
                self.matrix.matrix[neighbour_idx].todense()
            ).flatten()

            for item_col, weight in enumerate(neighbour_vec):
                if weight == 0.0:
                    continue
                item_id = self.matrix.item_ids[item_col]
                if item_id in already_seen:
                    continue

                contribution = similarity * float(weight)
                item_scores[item_col] = item_scores.get(item_col, 0.0) + contribution
                item_contributors.setdefault(item_col, []).append(neighbour_id)

        results: list[CFResult] = [
            CFResult(
                item_id=self.matrix.item_ids[col],
                score=round(score, 4),
                similar_user_ids=item_contributors.get(col, []),
            )
            for col, score in item_scores.items()
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_n]
