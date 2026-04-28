"""
User-item interaction matrix builder.

Constructs a sparse weighted matrix where:
  - rows  = users
  - cols  = items
  - value = aggregated event weight for that (user, item) pair

Aggregation uses the maximum weight seen for a given (user, item) pair
rather than a sum, so a user who views AND completes an item gets the
completion weight (3) rather than view+click+complete (1+2+3=6), which
would unfairly inflate that pair versus others.
"""

import uuid

import numpy as np
from scipy.sparse import csr_matrix

from app.models.user_event import UserEvent


class InteractionMatrix:
    """
    Sparse (n_users × n_items) matrix of aggregated interaction weights.
    Exposes index maps for downstream KNN and hybrid layers.
    """

    def __init__(
        self,
        events: list[UserEvent],
        user_ids: list[uuid.UUID],
        item_ids: list[uuid.UUID],
    ) -> None:
        self.user_ids: list[uuid.UUID] = user_ids
        self.item_ids: list[uuid.UUID] = item_ids
        self.user_index: dict[uuid.UUID, int] = {
            uid: i for i, uid in enumerate(user_ids)
        }
        self.item_index: dict[uuid.UUID, int] = {
            iid: i for i, iid in enumerate(item_ids)
        }

        # Aggregate: keep the maximum weight per (user, item) pair
        agg: dict[tuple[int, int], float] = {}
        for event in events:
            u = self.user_index.get(event.user_id)
            i = self.item_index.get(event.item_id)
            if u is None or i is None:
                continue
            key = (u, i)
            agg[key] = max(agg.get(key, 0.0), float(event.weight))

        if agg:
            rows, cols = zip(*agg.keys())
            data = list(agg.values())
        else:
            rows, cols, data = [], [], []

        self.matrix: csr_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(user_ids), len(item_ids)),
            dtype=np.float32,
        )

    def get_user_vector(self, user_id: uuid.UUID) -> np.ndarray | None:
        """Return the dense interaction row for a user, or None if unknown."""
        idx = self.user_index.get(user_id)
        if idx is None:
            return None
        return np.asarray(self.matrix[idx].todense()).flatten()

    def get_interacted_item_ids(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        """Return the set of item IDs the user has interacted with."""
        vec = self.get_user_vector(user_id)
        if vec is None:
            return set()
        return {self.item_ids[i] for i, w in enumerate(vec) if w > 0}
