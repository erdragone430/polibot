from unittest.mock import MagicMock, patch

from polibot.retrieval.reranker import rerank
from polibot.retrieval.retriever import retrieve


def test_rerank_orders_candidates_by_score_desc():
    with patch("polibot.retrieval.reranker.get_reranker") as get_model:
        get_model.return_value.compute_score.return_value = [0.1, 0.9, 0.5]
        ranked = rerank("query", ["low", "high", "mid"], top_n=2)
    assert ranked == [(1, 0.9), (2, 0.5)]


def test_retrieve_fuses_then_reranks_to_top_k():
    fake_hit = MagicMock(payload={"text": "chunk text", "page": 3})
    fake_qdrant = MagicMock()
    fake_qdrant.query_points.return_value.points = [fake_hit]

    with (
        patch("polibot.retrieval.retriever.get_qdrant_client", return_value=fake_qdrant),
        patch(
            "polibot.retrieval.retriever.embed_texts",
            return_value=[{"dense": [0.1], "sparse": object()}],
        ),
        patch("polibot.retrieval.retriever.rerank", return_value=[(0, 0.87)]),
    ):
        results = retrieve("query", top_k=1)

    assert len(results) == 1
    assert results[0].node.get_content() == "chunk text"
    assert results[0].node.metadata["page"] == 3
    assert results[0].score == 0.87


if __name__ == "__main__":
    test_rerank_orders_candidates_by_score_desc()
    test_retrieve_fuses_then_reranks_to_top_k()
    print("ok")
