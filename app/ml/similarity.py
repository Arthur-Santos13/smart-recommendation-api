"""
Cosine similarity matrix for item-item content similarity.

The matrix is computed once over the full item catalogue and cached
in-process. It is invalidated and recomputed whenever the caller
requests a fresh build (e.g. after new items are inserted).
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import spmatrix

from app.models.item import Item
from app.ml.vectorizer import build_tfidf_matrix


class SimilarityMatrix:
    """
    Holds the item-item cosine similarity matrix together with an
    index map from item UUID → row position so callers never depend
    on insertion order.
    """

    def __init__(self, items: list[Item]) -> None:
        self.item_ids: list = [item.id for item in items]
        self.index: dict = {item_id: idx for idx, item_id in enumerate(self.item_ids)}

        _, tfidf_matrix = build_tfidf_matrix(items)
        # Compute dense similarity — acceptable for catalogue sizes up to ~50k items
        self._matrix: np.ndarray = cosine_similarity(tfidf_matrix)

    def get_similar(
        self,
        item_id,
        top_n: int = 10,
        exclude_ids: set | None = None,
    ) -> list[tuple]:
        """
        Return top_n most similar items to item_id (excluding itself and
        any ids in exclude_ids).

        Returns list of (similar_item_id, score) sorted by score descending.
        """
        if item_id not in self.index:
            return []

        row_idx = self.index[item_id]
        scores = self._matrix[row_idx]

        exclude = exclude_ids or set()
        exclude.add(item_id)

        results: list[tuple] = []
        for idx, score in enumerate(scores):
            candidate_id = self.item_ids[idx]
            if candidate_id in exclude:
                continue
            results.append((candidate_id, float(score)))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def score(self, item_id_a, item_id_b) -> float:
        """Return the similarity score between two items."""
        if item_id_a not in self.index or item_id_b not in self.index:
            return 0.0
        a = self.index[item_id_a]
        b = self.index[item_id_b]
        return float(self._matrix[a][b])
