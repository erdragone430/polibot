import uuid
from qdrant_client import models
from polibot.config import get_settings
from polibot.ingestion.embedding import embed_texts
from polibot.ingestion.pipeline import ensure_collection
from polibot.retrieval.qdrant_client import get_qdrant_client
from polibot.retrieval.reranker import rerank
from polibot.retrieval.retriever import retrieve

def test_rerank_orders_candidates_by_score_desc_live():
    # Will use the live BAAI/bge-reranker-v2-m3 model
    ranked = rerank("what is a cat?", ["A car is a vehicle.", "A cat is an animal.", "A dog barks."], top_n=2)
    assert len(ranked) == 2
    # The second text ("A cat is an animal.") should be ranked highest (index 1)
    assert ranked[0][0] == 1

def test_retrieve_fuses_then_reranks_to_top_k_live():
    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection()

    test_course = "test_retrieval_course"
    
    # Clean previous runs
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(must=[models.FieldCondition(key="course", match=models.MatchValue(value=test_course))])
        )
    )

    texts = ["Apples are red.", "Bananas are yellow.", "The speed of light is fast."]
    embeddings = embed_texts(texts)
    points = []
    for t, emb in zip(texts, embeddings):
        points.append(models.PointStruct(
            id=str(uuid.uuid4()),
            vector={"dense": emb["dense"], "sparse": emb["sparse"]},
            payload={"text": t, "course": test_course, "access_scope": "public", "owner_id": "public"}
        ))
    client.upsert(collection_name=settings.qdrant_collection, points=points)

    results = retrieve("fruit that is yellow", top_k=1, course_id=test_course)
    assert len(results) == 1
    assert "Bananas are yellow." in results[0].node.get_content()

if __name__ == "__main__":
    test_rerank_orders_candidates_by_score_desc_live()
    test_retrieve_fuses_then_reranks_to_top_k_live()
    print("ok")
