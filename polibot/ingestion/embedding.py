from functools import lru_cache

import ollama
from fastembed import SparseTextEmbedding
from qdrant_client import models

from polibot.config import get_settings


@lru_cache
def get_sparse_model() -> SparseTextEmbedding:
    return SparseTextEmbedding(model_name=get_settings().sparse_model_name)


def embed_texts(texts: list[str]) -> list[dict]:
    """Dense (bge-m3 via Ollama) + sparse (fastembed BM25) embeddings for hybrid search."""
    settings = get_settings()
    client = ollama.Client(host=settings.ollama_base_url)
    dense_vectors = client.embed(model=settings.ollama_embedding_model, input=texts)["embeddings"]

    sparse_vectors = get_sparse_model().embed(texts)

    return [
        {
            "dense": list(dense),
            "sparse": models.SparseVector(
                indices=sparse.indices.tolist(), values=sparse.values.tolist()
            ),
        }
        for dense, sparse in zip(dense_vectors, sparse_vectors)
    ]
