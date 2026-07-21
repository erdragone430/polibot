import logging
import uuid
from pathlib import Path

from qdrant_client import models

from polibot.config import get_settings
from polibot.ingestion.captioning import caption_page_images
from polibot.ingestion.chunking import chunk_pages, read_pdf
from polibot.ingestion.embedding import embed_texts
from polibot.retrieval.qdrant_client import get_qdrant_client

logger = logging.getLogger(__name__)

DENSE_VECTOR_SIZE = 768


def ensure_collection() -> None:
    settings = get_settings()
    client = get_qdrant_client()
    if client.collection_exists(settings.qdrant_collection):
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config={
            "dense": models.VectorParams(size=DENSE_VECTOR_SIZE, distance=models.Distance.COSINE)
        },
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )
    # owner_id enforces the privacy filter (retriever.py), not just an optimization -
    # is_tenant=True so Qdrant lays out storage partitioned by it.
    client.create_payload_index(
        collection_name=settings.qdrant_collection,
        field_name="owner_id",
        field_schema=models.KeywordIndexParams(type=models.KeywordIndexType.KEYWORD, is_tenant=True),
    )
    for field_name in ("course", "topic", "access_scope"):
        client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name=field_name,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )


def ingest_pdf(
    path: str,
    course: str,
    topic: str | None = None,
    caption: bool = True,
    owner_id: str = "public",
    access_scope: str = "public",
    document_type: str = "lecture_note",
) -> int:
    """Read a slide-deck PDF, chunk (+ optionally caption) it, and upsert hybrid vectors into Qdrant."""
    topic = topic or Path(path).stem
    ensure_collection()

    pages = read_pdf(path)
    text_nodes = chunk_pages(pages, course=course, topic=topic)

    for node in text_nodes:
        node.metadata.update({
            "owner_id": owner_id,
            "access_scope": access_scope,
            "document_type": document_type,
        })

    texts = [node.get_content() for node in text_nodes]
    metadatas = [node.metadata for node in text_nodes]

    if caption:
        for page in pages:
            if page.images:
                logger.info(
                    "page %d/%d: captioning %d image(s)...",
                    page.number, len(pages), len(page.images),
                )
            for caption_text in caption_page_images(page):
                texts.append(caption_text)
                metadatas.append(
                    {
                        "course": course,
                        "topic": topic,
                        "page": page.number,
                        "slide": page.number,
                        "content_type": "image_caption",
                        "owner_id": owner_id,
                        "access_scope": access_scope,
                        "document_type": document_type,
                    }
                )

    if not texts:
        return 0

    embeddings = embed_texts(texts)
    points = [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector={"dense": embedding["dense"], "sparse": embedding["sparse"]},
            payload={**metadata, "text": text},
        )
        for text, metadata, embedding in zip(texts, metadatas, embeddings)
    ]

    client = get_qdrant_client()
    client.upsert(collection_name=get_settings().qdrant_collection, points=points)
    return len(points)
