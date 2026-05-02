"""
Hybrid recommendation merger.

Combines scored results from two sources (content-based and collaborative)
using a configurable weighted strategy:

    final_score(item) = (cb_weight × cb_score) + (cf_weight × cf_score)

Where cb_weight + cf_weight = 1.0 (enforced at call site).

Scores from each source are min-max normalised before merging so that
the two pipelines operate on a common [0, 1] scale regardless of their
internal magnitude differences.

Explainability:
    - Item present in both sources → reason from the higher-weighted source
    - Item present in one source only → reason from that source
    - Source tag appended: "(content)" or "(collaborative)" or "(hybrid)"
"""

import uuid
from dataclasses import dataclass

from app.services.content_based_service import RecommendationResult


def _normalise(results: list[RecommendationResult]) -> list[RecommendationResult]:
    """Min-max normalise scores to [0, 1]."""
    if not results:
        return results
    min_s = min(r.score for r in results)
    max_s = max(r.score for r in results)
    if max_s == min_s:
        return [
            RecommendationResult(
                item_id=r.item_id, score=1.0, reason=r.reason, category=r.category, title=r.title
            )
            for r in results
        ]
    return [
        RecommendationResult(
            item_id=r.item_id,
            score=round((r.score - min_s) / (max_s - min_s), 4),
            reason=r.reason,
            category=r.category,
            title=r.title,
        )
        for r in results
    ]


def merge_recommendations(
    cb_results: list[RecommendationResult],
    cf_results: list[RecommendationResult],
    cb_weight: float = 0.7,
    cf_weight: float = 0.3,
    top_n: int = 10,
    category: str | None = None,
) -> list[RecommendationResult]:
    """
    Merge content-based and collaborative results into a single ranked list.

    Parameters
    ----------
    cb_results : scored results from ContentBasedService
    cf_results : scored results from CollaborativeService
    cb_weight  : weight applied to content-based scores (default 0.70)
    cf_weight  : weight applied to collaborative scores (default 0.30)
    top_n      : maximum items to return
    category   : optional post-merge category filter
    """
    cb_norm = _normalise(cb_results)
    cf_norm = _normalise(cf_results)

    cb_map: dict[uuid.UUID, RecommendationResult] = {r.item_id: r for r in cb_norm}
    cf_map: dict[uuid.UUID, RecommendationResult] = {r.item_id: r for r in cf_norm}

    all_item_ids: set[uuid.UUID] = set(cb_map) | set(cf_map)
    merged: list[RecommendationResult] = []

    for item_id in all_item_ids:
        cb = cb_map.get(item_id)
        cf = cf_map.get(item_id)

        cb_score = cb.score if cb else 0.0
        cf_score = cf.score if cf else 0.0
        final_score = round(cb_weight * cb_score + cf_weight * cf_score, 4)

        # Determine reason and source tag
        if cb and cf:
            # Both signals — use the reason from the dominant source
            if cb_weight >= cf_weight:
                base_reason = cb.reason
            else:
                base_reason = cf.reason
            source_tag = "hybrid"
        elif cb:
            base_reason = cb.reason
            source_tag = "content"
        else:
            base_reason = cf.reason  # type: ignore[union-attr]
            source_tag = "collaborative"

        reason = f"{base_reason} ({source_tag})"
        category_val = (cb or cf).category  # type: ignore[union-attr]

        if category and category_val != category:
            continue

        merged.append(
            RecommendationResult(
                item_id=item_id,
                score=final_score,
                reason=reason,
                category=category_val,
                title=(cb or cf).title,  # type: ignore[union-attr]
            )
        )

    merged.sort(key=lambda r: r.score, reverse=True)
    top = merged[:top_n]
    # Re-normalise the final merged list so the best item is always 1.0.
    # Without this, a CB-only item is capped at cb_weight (e.g. 0.70) and a
    # CF-only item at cf_weight (e.g. 0.30), making scores artifacts of the
    # blending weights rather than a meaningful match percentage.
    return _normalise(top)
