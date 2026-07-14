from llama_index.core.schema import NodeWithScore, TextNode
from qdrant_client import models

from polibot.config import get_settings
from polibot.ingestion.embedding import embed_texts
from polibot.retrieval.qdrant_client import get_qdrant_client
from polibot.retrieval.reranker import rerank

CANDIDATE_POOL_SIZE = 25


def retrieve(
    query: str,
    top_k: int = 5,
    candidate_pool_size: int = CANDIDATE_POOL_SIZE,
    owner_id: str | None = None,
    course_id: str | None = None,
) -> list[NodeWithScore]:
    settings = get_settings()
    client = get_qdrant_client()
    query_embedding = embed_texts([query])[0]

    # Synthesize filters
    conditions = []
    if course_id:
        conditions.append(
            models.FieldCondition(
                key="course",
                match=models.MatchValue(value=course_id),
            )
        )

    # Privacy filter: (access_scope == "public") OR (owner_id == owner_id)
    privacy_conditions = [
        models.FieldCondition(
            key="access_scope",
            match=models.MatchValue(value="public"),
        )
    ]
    if owner_id:
        privacy_conditions.append(
            models.FieldCondition(
                key="owner_id",
                match=models.MatchValue(value=owner_id),
            )
        )

    conditions.append(models.Filter(should=privacy_conditions))
    qdrant_filter = models.Filter(must=conditions)

    hits = client.query_points(
        collection_name=settings.qdrant_collection,
        prefetch=[
            models.Prefetch(
                query=query_embedding["dense"],
                using="dense",
                limit=candidate_pool_size,
                filter=qdrant_filter,
            ),
            models.Prefetch(
                query=query_embedding["sparse"],
                using="sparse",
                limit=candidate_pool_size,
                filter=qdrant_filter,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        query_filter=qdrant_filter,
        limit=candidate_pool_size,
    ).points

    if not hits:
        return []

    payloads = [hit.payload or {} for hit in hits]
    texts = [payload.get("text", "") for payload in payloads]

    results = []
    for index, score in rerank(query, texts, top_n=top_k):
        node = TextNode(text=texts[index], metadata=payloads[index])
        results.append(NodeWithScore(node=node, score=score))
    return results
