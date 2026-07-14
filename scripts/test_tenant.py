import uuid
from polibot.ingestion.pipeline import ensure_collection
from polibot.retrieval.qdrant_client import get_qdrant_client
from polibot.retrieval.retriever import retrieve
from polibot.ingestion.embedding import embed_texts
from qdrant_client import models
from polibot.config import get_settings


def run_test():
    print("--- Running Multi-Tenant RAG Isolation Test ---")
    settings = get_settings()

    client = get_qdrant_client()
    # Ping Qdrant
    client.get_collections()
    ensure_collection()
    print("Connected to active local Qdrant server.")

    print("Ingesting test points...")
    # Clean old test points first (by filtering on the test course name)
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="course", match=models.MatchValue(value="tenant_test_course")
                    )
                ]
            )
        ),
    )

    texts = [
        "Public Course Slide: The derivative represents the instantaneous rate of change.",
        "Student A Private Notes: Remember to study the boundary values for the derivative exam.",
        "Student B Private Notes: Calculus homework solutions for problem 3 on integration.",
    ]
    metadatas = [
        {
            "course": "tenant_test_course",
            "topic": "calculus",
            "page": 1,
            "slide": 1,
            "content_type": "text",
            "access_scope": "public",
            "owner_id": "public",
            "document_type": "lecture_note",
        },
        {
            "course": "tenant_test_course",
            "topic": "calculus",
            "page": 2,
            "slide": 2,
            "content_type": "text",
            "access_scope": "private",
            "owner_id": "student_a",
            "document_type": "user_upload",
        },
        {
            "course": "tenant_test_course",
            "topic": "calculus",
            "page": 3,
            "slide": 3,
            "content_type": "text",
            "access_scope": "private",
            "owner_id": "student_b",
            "document_type": "user_upload",
        },
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
    print("Ingestion complete.")

    # Query as Student A
    print("\n[Querying as Student A (should retrieve public + student_a notes)]")
    results_a = retrieve(
        "derivative calculus notes",
        top_k=5,
        owner_id="student_a",
        course_id="tenant_test_course",
    )
    for i, r in enumerate(results_a, 1):
        print(
            f"  {i}. [Owner: {r.node.metadata.get('owner_id')}] text: '{r.node.get_content()[:80]}...'"
        )

    assert any(
        r.node.metadata.get("owner_id") == "student_a" for r in results_a
    ), "Student A should see their private notes!"
    assert all(
        r.node.metadata.get("owner_id") != "student_b" for r in results_a
    ), "Student A should NOT see Student B's private notes!"

    # Query as Student B
    print("\n[Querying as Student B (should retrieve public + student_b notes)]")
    results_b = retrieve(
        "calculus homework",
        top_k=5,
        owner_id="student_b",
        course_id="tenant_test_course",
    )
    for i, r in enumerate(results_b, 1):
        print(
            f"  {i}. [Owner: {r.node.metadata.get('owner_id')}] text: '{r.node.get_content()[:80]}...'"
        )

    assert any(
        r.node.metadata.get("owner_id") == "student_b" for r in results_b
    ), "Student B should see their private notes!"
    assert all(
        r.node.metadata.get("owner_id") != "student_a" for r in results_b
    ), "Student B should NOT see Student A's private notes!"

    # Query anonymously (no owner_id)
    print("\n[Querying anonymously (should retrieve only public slides)]")
    results_anon = retrieve(
        "derivative calculus homework",
        top_k=5,
        owner_id=None,
        course_id="tenant_test_course",
    )
    for i, r in enumerate(results_anon, 1):
        print(
            f"  {i}. [Owner: {r.node.metadata.get('owner_id')}] text: '{r.node.get_content()[:80]}...'"
        )

    assert all(
        r.node.metadata.get("access_scope") == "public" for r in results_anon
    ), "Anonymous query should only see public materials!"

    print("\n>>> MULTI-TENANT ISOLATION TEST PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    run_test()
