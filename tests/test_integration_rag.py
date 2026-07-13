import os
import uuid
from polibot.config import get_settings
from polibot.ingestion.embedding import embed_texts
from polibot.retrieval.qdrant_client import get_qdrant_client
from qdrant_client import models
from polibot.retrieval.retriever import retrieve
from polibot.material_generation.exercises import generate_exercise
from polibot.material_generation.lessons import generate_lesson

from polibot.ingestion.pipeline import ensure_collection

def test_full_rag_pipeline():
    settings = get_settings()

    # 1. Ingest Sample Material
    client = get_qdrant_client()
    # Ping Qdrant
    client.get_collections()
    ensure_collection()

    # Clean old test points
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="course", match=models.MatchValue(value="integration_course")
                    )
                ]
            )
        ),
    )

    texts = [
        "Newton's second law of motion states that F = ma.",
        "The integral of x^2 is x^3/3.",
    ]
    metadatas = [
        {"course": "integration_course", "topic": "physics", "page": 1, "slide": 1, "content_type": "text", "access_scope": "public"},
        {"course": "integration_course", "topic": "calculus", "page": 2, "slide": 1, "content_type": "text", "access_scope": "public"},
    ]

    embeddings = embed_texts(texts)
    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector={"dense": embedding["dense"], "sparse": embedding["sparse"]},
            payload={**metadata, "text": text},
        )
        for text, metadata, embedding in zip(texts, metadatas, embeddings)
    ]
    client.upsert(collection_name=settings.qdrant_collection, points=points)

    # 2. Retrieve Material
    results = retrieve("physics formula", top_k=1, course_id="integration_course")
    assert len(results) > 0, "Should retrieve the ingested physics text"
    assert "F = ma" in results[0].node.get_content()

    # 3. Generate Exercise (using RAG context if it uses the topic, though the topic is passed)
    # The generate_exercise function will search for topic="physics"
    exercise = generate_exercise("physics")
    assert exercise.statement is not None
    assert exercise.solution is not None

    # 4. Generate Lesson
    lesson = generate_lesson("calculus", min_slides=1, max_slides=2)
    assert lesson.topic is not None
    assert len(lesson.slides) >= 1

if __name__ == "__main__":
    print("Running RAG Integration test...")
    test_full_rag_pipeline()
    print("Done!")
