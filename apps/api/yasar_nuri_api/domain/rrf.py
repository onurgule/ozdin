from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID


def reciprocal_rank_fusion(
    ranked_lists: list[list[UUID]],
    *,
    k: int = 60,
) -> list[tuple[UUID, float]]:
    scores: dict[UUID, float] = defaultdict(float)
    for lst in ranked_lists:
        for rank, cid in enumerate(lst, start=1):
            scores[cid] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def merge_unique_preserve_order(ids: Iterable[UUID]) -> list[UUID]:
    seen: set[UUID] = set()
    out: list[UUID] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out
