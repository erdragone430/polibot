from polibot.ingestion.chunking import Page, chunk_pages
from polibot.ingestion.embedding import embed_texts

def test_chunk_pages_tags_each_chunk_with_its_own_page():
    pages = [
        Page(number=1, text="Intro to loops. " * 5),
        Page(number=2, text="Recursion basics. " * 5),
    ]
    nodes = chunk_pages(pages, course="CS101", topic="algorithms", chunk_size=100, chunk_overlap=5)
    assert nodes
    assert {node.metadata["page"] for node in nodes} == {1, 2}

def test_embed_texts_combines_ollama_dense_and_fastembed_sparse_live():
    # Calling the live models (nomic-embed-text for dense, Qdrant/bm25 for sparse)
    results = embed_texts(["hello world"])

    assert len(results) == 1
    assert "dense" in results[0]
    assert "sparse" in results[0]
    # DENSE_VECTOR_SIZE config says 768 for nomic-embed-text
    assert len(results[0]["dense"]) == 768
    assert hasattr(results[0]["sparse"], "indices")
    assert hasattr(results[0]["sparse"], "values")

if __name__ == "__main__":
    test_chunk_pages_tags_each_chunk_with_its_own_page()
    test_embed_texts_combines_ollama_dense_and_fastembed_sparse_live()
    print("ok")
