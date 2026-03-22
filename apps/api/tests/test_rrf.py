from uuid import UUID

from yasar_nuri_api.domain.rrf import reciprocal_rank_fusion

u1, u2, u3 = UUID(int=1), UUID(int=2), UUID(int=3)


def test_rrf_orders_by_fusion() -> None:
    merged = reciprocal_rank_fusion([[u1, u2], [u2, u3]], k=60)
    assert merged[0][0] == u2
